# GitHub Issues Killer

![GitHub Issues Killer](https://img.shields.io/badge/Tool-GitHub%20Issues%20Killer-blue)
![Python](https://img.shields.io/badge/Language-Python-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

一个自动监控和删除 GitHub 仓库中可疑 Issues 的命令行工具。

## 功能特点

- 🔍 **自动监控**：定期检查指定仓库中的 Issues
- 🚫 **彻底删除**：使用 GitHub GraphQL API 完全删除可疑 Issues
- 🔑 **关键词检测**：通过自定义关键词识别恶意 Issues
- 🔄 **多仓库支持**：同时监控多个 GitHub 仓库
- ⚙️ **配置持久化**：自动保存配置，无需重复设置

## 安装要求

- Python 3.6+
- requests 库

## 安装方法

**通过本地/服务器运行：**

1. 在本地或者服务器运行 `issues_killer.py` 文件
2. 完成配置流程
3. 等待程序自动运行 (可以用screen进行进程管理)

**通过Github Actions自动运行：**

1. Fork 或克隆此仓库
2. 确保你的仓库中包含 `issues_killer_actions.py` 和 `.github/workflows/issues_killer.yml` 文件
3. 在你的仓库中，访问 Settings > Secrets and variables > Actions
   点击 "New repository secret"
   名称填写 `PERSONAL_ACCESS_TOKEN`
   值填写创建的包含正确权限的 Token

4. 工作流文件位于 .github/workflows/issues_killer.yml
   你可以修改 cron 表达式来设置不同的执行频率:

如果要修改执行频率：
每小时执行: cron: '0 * * * *'
每天执行: cron: '0 2 * * *' (UTC时间2:00，约等于北京时间10:00)
每周执行: cron: '0 2 * * 1' (每周一)

修改要监控的仓库:
yamlREPOS_TO_MONITOR: ${{ github.event_name == 'workflow_dispatch' && github.event.inputs.repos || 'your-username/your-repo' }}


**通过Github Actions手动触发：**

1. 访问仓库的 Actions 标签页
2. 点击 "GitHub Issues Killer" 工作流
3. 点击 "Run workflow" 按钮手动触发执行

### 初次设置

首次运行会引导你完成以下配置步骤:

1. **GitHub Token 设置**: 
   - 需要提供具有 `Issues` 和 `Metadata` 权限的 Personal Access Token
   - 获取方式: [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)

2. **可疑关键词设置**:
   - 除了默认关键词还可以添加自定义关键词

3. **监控仓库选择**:
   - 自动获取你的仓库列表
   - 可以选择监控所有仓库或特定仓库

4. **检查频率设置**:
   - 设置监控间隔时间 (默认60秒)

## 工作原理

1. 程序定期检查指定仓库中的未关闭 Issues
2. 检查每个 Issue 的标题和内容是否包含可疑关键词
3. 对于可疑 Issues，使用 GitHub GraphQL API 获取其 node_id 并完全删除