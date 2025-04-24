import requests
import time
import sys
import os
from datetime import datetime
import json
import threading
import re

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# 配置文件路径
CONFIG_FILE = 'github_monitor_config.json'

def clear_screen():
    """清除屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = f"""{Colors.BLUE}
  _____                           _    _ _ _          
 |_   _|                         | |  (_) | |          
   | |  ___ ___ _   _  ___  ___  | | ___| | | ___ _ __ 
   | | / __/ __| | | |/ _ \/ __| | |/ / | | |/ _ \ '__|
  _| |_\__ \__ \ |_| |  __/\__ \ |   <| | | |  __/ |   
 |_____|___/___/\__,_|\___||___/ |_|\_\_|_|_|\___|_|   {Colors.ENDC}
    """
    print(banner)

def validate_token(token, headers):
    """验证GitHub Token是否有效"""
    try:
        response = requests.get('https://api.github.com/user', headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"{Colors.GREEN}✓ Token有效！用户名: {user_data['login']}{Colors.ENDC}")
            return True, user_data['login']
        else:
            print(f"{Colors.FAIL}✗ Token无效或权限不足。错误代码: {response.status_code}{Colors.ENDC}")
            return False, None
    except Exception as e:
        print(f"{Colors.FAIL}✗ 验证Token时出错: {e}{Colors.ENDC}")
        return False, None

def get_user_repos(headers, username):
    """获取用户的仓库列表"""
    try:
        repos = []
        page = 1
        while True:
            response = requests.get(f'https://api.github.com/users/{username}/repos?page={page}&per_page=100', headers=headers)
            if response.status_code != 200 or not response.json():
                break
            repos.extend(response.json())
            page += 1
        
        return [(repo['name'], repo['full_name']) for repo in repos]
    except Exception as e:
        print(f"{Colors.FAIL}获取仓库列表时出错: {e}{Colors.ENDC}")
        return []

def setup_config():
    """设置配置信息"""
    clear_screen()
    print_banner()
    
    config = {}
    
    # 1. 获取Token
    print(f"{Colors.HEADER}[步骤 1/4] GitHub Personal Access Token 设置{Colors.ENDC}")
    print("请提供具有以下权限的GitHub Token: 'Issues', 'Metadata'")
    print("获取Token: https://github.com/settings/tokens\n")
    
    token = input("请输入GitHub Token: ").strip()
    if not token:
        print(f"{Colors.FAIL}需要提供有效的Token才能继续。{Colors.ENDC}")
        sys.exit(1)
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    is_valid, username = validate_token(token, headers)
    if not is_valid:
        print(f"{Colors.FAIL}请检查Token并重试。{Colors.ENDC}")
        sys.exit(1)
    
    config['token'] = token
    config['username'] = username
    
    # 2. 设置关键词
    clear_screen()
    print_banner()
    print(f"{Colors.HEADER}[步骤 2/4] 可疑关键词设置{Colors.ENDC}")
    print("添加可以识别恶意Issues的关键词 (每行输入一个关键词, 输入空行完成)")
    
    suspicious_keywords = ["spam", "恶意", "虚假", "suspicious", "Star", "star", "异常增长"]
    
    print("当前关键词:")
    for kw in suspicious_keywords:
        print(f" - {kw}")
    
    while True:
        keyword = input("\n添加新关键词 (直接回车跳过): ").strip()
        if not keyword:
            break
        if keyword not in suspicious_keywords:
            suspicious_keywords.append(keyword)
            print(f"{Colors.GREEN}已添加: {keyword}{Colors.ENDC}")
    
    config['suspicious_keywords'] = suspicious_keywords
    
    # 3. 选择监控的仓库
    clear_screen()
    print_banner()
    print(f"{Colors.HEADER}[步骤 3/4] 选择监控仓库{Colors.ENDC}")
    print("正在获取你的仓库列表...")
    
    repos = get_user_repos(headers, username)
    if not repos:
        print(f"{Colors.WARNING}未找到仓库或获取仓库列表失败。{Colors.ENDC}")
        manual_repo = input("请手动输入仓库名称 (例如: myrepo): ").strip()
        if manual_repo:
            repos = [(manual_repo, f"{username}/{manual_repo}")]
    
    selected_repos = []
    
    print(f"\n找到 {len(repos)} 个仓库:")
    for i, (repo_name, full_name) in enumerate(repos, 1):
        print(f"{i}. {repo_name}")
    
    print("\n选择要监控的仓库 (输入序号, 多个序号用逗号分隔, 输入'all'监控所有)")
    selection = input("选择: ").strip().lower()
    
    if selection == 'all':
        selected_repos = [full_name for _, full_name in repos]
        print(f"{Colors.GREEN}已选择所有仓库进行监控{Colors.ENDC}")
    else:
        try:
            indices = [int(idx.strip()) for idx in selection.split(',') if idx.strip()]
            for idx in indices:
                if 1 <= idx <= len(repos):
                    selected_repos.append(repos[idx-1][1])
                    print(f"{Colors.GREEN}已选择: {repos[idx-1][0]}{Colors.ENDC}")
            
            if not selected_repos:
                print(f"{Colors.WARNING}未选择任何仓库，默认监控第一个仓库{Colors.ENDC}")
                if repos:
                    selected_repos.append(repos[0][1])
                    print(f"{Colors.GREEN}已选择: {repos[0][0]}{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.WARNING}输入无效，默认监控第一个仓库{Colors.ENDC}")
            if repos:
                selected_repos.append(repos[0][1])
                print(f"{Colors.GREEN}已选择: {repos[0][0]}{Colors.ENDC}")
    
    config['monitored_repos'] = selected_repos
    
    # 4. 设置检查间隔
    clear_screen()
    print_banner()
    print(f"{Colors.HEADER}[步骤 4/4] 检查频率设置{Colors.ENDC}")
    print("设置检查GitHub Issues的时间间隔 (单位: 秒)")
    
    try:
        interval = input("间隔时间 (默认60秒): ").strip()
        interval = int(interval) if interval else 60
        if interval < 30:
            print(f"{Colors.WARNING}警告: 间隔太短可能导致API频率限制。设置为最小值30秒。{Colors.ENDC}")
            interval = 30
    except ValueError:
        print(f"{Colors.WARNING}输入无效，使用默认值60秒{Colors.ENDC}")
        interval = 60
    
    config['check_interval'] = interval
    
    # 保存配置
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Colors.GREEN}配置已保存到 {CONFIG_FILE}{Colors.ENDC}")
    return config

def load_config():
    """加载配置"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        else:
            return setup_config()
    except Exception as e:
        print(f"{Colors.FAIL}加载配置文件失败: {e}{Colors.ENDC}")
        return setup_config()

def get_open_issues(repo_full_name, headers):
    """获取仓库的未关闭issues"""
    url = f"https://api.github.com/repos/{repo_full_name}/issues?state=open"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"{Colors.FAIL}获取仓库 {repo_full_name} 的issues失败: {response.status_code}{Colors.ENDC}")
        return []

def is_suspicious(issue, suspicious_keywords):
    """检查issue是否可疑"""
    # 检查标题和内容中是否包含可疑关键词
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
        print(f"{Colors.FAIL}获取issue信息失败: {response.status_code}{Colors.ENDC}")
        return None

def delete_issue(node_id, headers):
    """完全删除指定的issue (使用GraphQL API)"""
    graphql_endpoint = "https://api.github.com/graphql"
    graphql_headers = {
        "Authorization": f"bearer {headers['Authorization'].split(' ')[1]}",
        "Content-Type": "application/json"
    }
    
    # GraphQL mutation来删除issue
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
            print(f"{Colors.FAIL}删除失败: {result['errors']}{Colors.ENDC}")
            return False
        return True
    else:
        print(f"{Colors.FAIL}API请求失败: {response.status_code}{Colors.ENDC}")
        return False

def monitor_repositories(config):
    """监控仓库"""
    token = config['token']
    suspicious_keywords = config['suspicious_keywords']
    monitored_repos = config['monitored_repos']
    check_interval = config['check_interval']
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    processed_issues = set()  # 已处理的issue集合
    
    while True:
        try:
            clear_screen()
            print_banner()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{Colors.BOLD}[{now}] 开始检查可疑issues...{Colors.ENDC}")
            print(f"监控仓库: {', '.join(monitored_repos)}")
            print(f"检查间隔: {check_interval}秒")
            print("-" * 60)
            
            for repo_full_name in monitored_repos:
                print(f"\n正在检查仓库: {repo_full_name}")
                issues = get_open_issues(repo_full_name, headers)
                
                for issue in issues:
                    issue_number = issue["number"]
                    issue_id = f"{repo_full_name}#{issue_number}"
                    
                    # 如果已经处理过此issue，则跳过
                    if issue_id in processed_issues:
                        continue
                    
                    is_sus, keyword = is_suspicious(issue, suspicious_keywords)
                    if is_sus:
                        print(f"{Colors.WARNING}发现可疑issue {issue_id}: {issue['title']}{Colors.ENDC}")
                        print(f"{Colors.WARNING}匹配关键词: {keyword}{Colors.ENDC}")
                        
                        # 获取issue的node_id
                        node_id = get_issue_node_id(repo_full_name, issue_number, headers)
                        
                        if node_id:
                            # 删除issue
                            if delete_issue(node_id, headers):
                                print(f"{Colors.GREEN}已成功删除issue {issue_id}{Colors.ENDC}")
                                processed_issues.add(issue_id)
                            else:
                                print(f"{Colors.FAIL}删除issue {issue_id}失败{Colors.ENDC}")
                        else:
                            print(f"{Colors.FAIL}获取issue {issue_id}的node_id失败{Colors.ENDC}")
            
            print(f"\n{Colors.GREEN}检查完成! 下次检查将在{check_interval}秒后进行...{Colors.ENDC}")
            
            # 等待指定时间
            for i in range(check_interval, 0, -1):
                if i % 10 == 0 or i <= 5:  # 每10秒更新一次，或倒计时最后5秒
                    sys.stdout.write(f"\r{Colors.BLUE}等待下次检查: {i}秒{Colors.ENDC}")
                    sys.stdout.flush()
                time.sleep(1)
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.BOLD}程序已停止{Colors.ENDC}")
            break
        except Exception as e:
            print(f"\n{Colors.FAIL}发生错误: {e}{Colors.ENDC}")
            print("将在10秒后重试...")
            time.sleep(10)

def main_menu():
    """主菜单"""
    while True:
        clear_screen()
        print_banner()
        
        print(f"{Colors.HEADER}主菜单:{Colors.ENDC}")
        print("1. 开始监控")
        print("2. 重新配置")
        print("3. 查看当前配置")
        print("4. 退出程序")
        
        choice = input("\n请选择: ").strip()
        
        if choice == '1':
            config = load_config()
            monitor_repositories(config)
        elif choice == '2':
            setup_config()
        elif choice == '3':
            config = load_config()
            clear_screen()
            print_banner()
            print(f"{Colors.HEADER}当前配置:{Colors.ENDC}")
            print(f"用户名: {config.get('username', 'N/A')}")
            print(f"监控仓库: {', '.join(config.get('monitored_repos', []))}")
            print(f"可疑关键词: {', '.join(config.get('suspicious_keywords', []))}")
            print(f"检查间隔: {config.get('check_interval', 60)}秒")
            input("\n按Enter键返回主菜单...")
        elif choice == '4':
            print("\n感谢使用，再见!")
            sys.exit(0)
        else:
            print(f"{Colors.WARNING}无效选择，请重试{Colors.ENDC}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n程序已停止")
        sys.exit(0)