import requests
import time
import sys
import os
import json
import datetime
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("Issues Killer")

def validate_token(token):
    """验证GitHub Token是否有效"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get('https://api.github.com/user', headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            logger.info(f"✓ Token有效！用户名: {user_data['login']}")
            return True, user_data['login'], headers
        else:
            logger.error(f"✗ Token无效或权限不足。错误代码: {response.status_code}")
            return False, None, None
    except Exception as e:
        logger.error(f"✗ 验证Token时出错: {e}")
        return False, None, None

def get_user_repos(headers, username, repo_filter=None):
    """获取用户的仓库列表，可选择过滤特定仓库"""
    try:
        repos = []
        page = 1
        while True:
            response = requests.get(f'https://api.github.com/users/{username}/repos?page={page}&per_page=100', headers=headers)
            if response.status_code != 200 or not response.json():
                break
            repos.extend(response.json())
            page += 1
        
        full_names = [repo['full_name'] for repo in repos]
        
        # 如果有指定要监控的仓库，就过滤
        if repo_filter:
            repo_list = [r.strip() for r in repo_filter.split(',')]
            return [name for name in full_names if name in repo_list]
        return full_names
        
    except Exception as e:
        logger.error(f"获取仓库列表时出错: {e}")
        return []

def get_open_issues(repo_full_name, headers):
    """获取仓库的未关闭issues"""
    url = f"https://api.github.com/repos/{repo_full_name}/issues?state=open"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"获取仓库 {repo_full_name} 的issues失败: {response.status_code}")
        return []

def is_suspicious(issue, suspicious_keywords):
    """检查issue是否可疑"""
    title = issue.get("title", "").lower()
    body = issue.get("body", "").lower() if issue.get("body") else ""
    
    for keyword in suspicious_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in title.lower() or keyword_lower in body:
            return True, keyword
    
    return False, None

def get_issue_node_id(repo_full_name, issue_number, headers):
    """获取issue的node_id (GraphQL ID)"""
    owner, repo = repo_full_name.split('/')
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        issue_data = response.json()
        return issue_data.get("node_id")
    else:
        logger.error(f"获取issue信息失败: {response.status_code}")
        return None

def delete_issue(node_id, token):
    """完全删除指定的issue (使用GraphQL API)"""
    graphql_endpoint = "https://api.github.com/graphql"
    graphql_headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json"
    }
    
    mutation = """
    mutation {
      deleteIssue(input: {issueId: "%s"}) {
        clientMutationId
      }
    }
    """ % node_id
    
    response = requests.post(
        graphql_endpoint,
        headers=graphql_headers,
        json={"query": mutation}
    )
    
    if response.status_code == 200:
        result = response.json()
        if "errors" in result:
            logger.error(f"删除失败: {result['errors']}")
            return False
        return True
    else:
        logger.error(f"API请求失败: {response.status_code}")
        return False

def main():
    """主函数"""
    # 从环境变量获取配置
    token = os.environ.get("GITHUB_TOKEN")
    repo_filter = os.environ.get("REPOS_TO_MONITOR")  # 格式: "owner/repo1,owner/repo2"
    keywords_str = os.environ.get("SUSPICIOUS_KEYWORDS", 
                                "spam,恶意,虚假,suspicious,Star,star,异常增长")
    
    suspicious_keywords = [kw.strip() for kw in keywords_str.split(',')]
    
    if not token:
        logger.error("未提供GitHub Token (GITHUB_TOKEN环境变量)")
        sys.exit(1)
    
    # 验证Token
    is_valid, username, headers = validate_token(token)
    if not is_valid:
        logger.error("Token无效，无法继续。")
        sys.exit(1)
    
    # 获取仓库列表
    logger.info("正在获取仓库列表...")
    repos = get_user_repos(headers, username, repo_filter)
    
    if not repos:
        logger.error("未找到可监控的仓库。")
        sys.exit(1)
    
    logger.info(f"将监控以下仓库: {', '.join(repos)}")
    logger.info(f"关键词列表: {', '.join(suspicious_keywords)}")
    
    processed_issues = set()  # 已处理的issue集合
    issues_found = False
    
    # 开始检查issues
    logger.info("开始检查可疑issues...")
    
    for repo_full_name in repos:
        logger.info(f"检查仓库: {repo_full_name}")
        issues = get_open_issues(repo_full_name, headers)
        
        for issue in issues:
            issue_number = issue["number"]
            issue_id = f"{repo_full_name}#{issue_number}"
            
            # 如果已经处理过此issue，则跳过
            if issue_id in processed_issues:
                continue
            
            is_sus, keyword = is_suspicious(issue, suspicious_keywords)
            if is_sus:
                issues_found = True
                logger.warning(f"发现可疑issue {issue_id}: {issue['title']}")
                logger.warning(f"匹配关键词: {keyword}")
                
                # 获取issue的node_id
                node_id = get_issue_node_id(repo_full_name, issue_number, headers)
                
                if node_id:
                    # 删除issue
                    if delete_issue(node_id, token):
                        logger.info(f"已成功删除issue {issue_id}")
                        processed_issues.add(issue_id)
                    else:
                        logger.error(f"删除issue {issue_id}失败")
                else:
                    logger.error(f"获取issue {issue_id}的node_id失败")
    
    if not issues_found:
        logger.info("未发现可疑issues。")
    
    logger.info("检查完成！")

if __name__ == "__main__":
    try:
        logger.info("GitHub Issues Killer (GitHub Actions版) 开始运行...")
        main()
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        sys.exit(1)