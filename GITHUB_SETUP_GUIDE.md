# GitHub 仓库创建指南

本指南将帮助您将项目上传到 GitHub 并创建公开仓库。

## 第一步：注册 GitHub 账号（如果还没有）

1. 访问 https://github.com
2. 点击右上角 "Sign up" 注册账号
3. 填写用户名、邮箱和密码
4. 验证邮箱

## 第二步：在 GitHub 上创建新仓库

### 方法一：通过网页创建（推荐新手）

1. 登录 GitHub 后，点击右上角的 **"+"** 按钮
2. 选择 **"New repository"**
3. 填写仓库信息：
   - **Repository name**: `uav-qmix-coverage` （或您喜欢的名称）
   - **Description**: `QMIX-Based Multi-UAV Cooperative Coverage Path Planning`
   - **Visibility**: 选择 **Public**（公开，便于论文引用）
   - **不要**勾选 "Add a README file"（因为您本地已有）
   - **不要**勾选 "Add .gitignore"（我们将创建）
   - **不要**选择 License（可选，稍后添加）
4. 点击 **"Create repository"**

### 方法二：使用 GitHub Desktop（图形界面，更简单）

1. 下载安装 GitHub Desktop: https://desktop.github.com/
2. 登录您的 GitHub 账号
3. 点击 "File" → "New Repository"
4. 填写仓库信息并创建

## 第三步：准备本地项目文件

### 3.1 创建 .gitignore 文件

在项目根目录创建 `.gitignore` 文件，排除不需要上传的文件：

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Jupyter Notebook
.ipynb_checkpoints

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# 实验数据（大文件，可选）
experiments/logs/
experiments/checkpoints/
*.pth
*.pt
*.h5

# 系统文件
.DS_Store
Thumbs.db

# 临时文件
*.log
*.tmp
*.bak
*.backup

# 论文相关（可选，如果不想上传）
*.docx
*.doc
*.wps
paper_*.md
paper_*.tex
submissions/
Download*/

# 个人文件
*.pdf（如果不想上传PDF）
```

### 3.2 更新 README.md（可选）

确保 README.md 包含：
- 项目简介
- 安装说明
- 使用方法
- 实验结果
- 引用信息

## 第四步：上传代码到 GitHub

### 方法一：使用 Git 命令行（推荐）

在项目根目录打开 PowerShell 或命令提示符，执行：

```powershell
# 1. 初始化 Git 仓库
git init

# 2. 添加所有文件（.gitignore 会自动排除不需要的文件）
git add .

# 3. 提交文件
git commit -m "Initial commit: QMIX-based multi-UAV coverage path planning"

# 4. 连接到 GitHub 仓库（替换 YOUR_USERNAME 和 REPO_NAME）
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# 5. 上传到 GitHub
git branch -M main
git push -u origin main
```

**注意**：执行第 4 步时，需要：
- 将 `YOUR_USERNAME` 替换为您的 GitHub 用户名
- 将 `REPO_NAME` 替换为您创建的仓库名称

### 方法二：使用 GitHub Desktop

1. 打开 GitHub Desktop
2. 点击 "File" → "Add Local Repository"
3. 选择项目文件夹
4. 点击 "Publish repository"
5. 填写仓库信息并发布

## 第五步：获取仓库链接

上传完成后，您的仓库链接格式为：
```
https://github.com/YOUR_USERNAME/REPO_NAME
```

例如：
```
https://github.com/zhangsan/uav-qmix-coverage
```

## 第六步：更新论文中的链接

将论文 LaTeX 文件中的占位符链接替换为您的实际仓库链接。

## 常见问题

### Q: 如何更新代码？
A: 使用以下命令：
```powershell
git add .
git commit -m "描述您的更改"
git push
```

### Q: 如何添加 LICENSE？
A: 
1. 在 GitHub 仓库页面点击 "Add file" → "Create new file"
2. 文件名输入 `LICENSE`
3. GitHub 会自动提示选择许可证类型（推荐 MIT 或 Apache 2.0）

### Q: 如何添加项目描述和标签？
A: 在仓库主页点击 "Settings" → 可以添加描述、主题标签等

### Q: 如何创建 Release（发布版本）？
A: 
1. 在仓库页面点击 "Releases"
2. 点击 "Create a new release"
3. 填写版本号和描述

## 需要帮助？

如果遇到问题，可以：
1. 查看 GitHub 官方文档：https://docs.github.com
2. 搜索相关教程视频
3. 联系我获取进一步帮助
