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

1. 在本地或者服务器运行 `issues_killer.py` 文件
2. 完成配置流程

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