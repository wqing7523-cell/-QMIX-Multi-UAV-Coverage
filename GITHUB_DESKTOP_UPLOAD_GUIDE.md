# GitHub Desktop 上传代码指南

## 步骤说明

### 方法一：添加现有本地仓库（推荐）

1. **在 GitHub Desktop 中，点击右下角的按钮：**
   - 点击 **"Add an Existing Repository from your local drive..."**（添加现有本地仓库）

2. **选择项目文件夹：**
   - 点击 **"Choose..."** 按钮
   - 浏览并选择文件夹：`C:\Users\44358\Desktop\uav-qmix`
   - 点击 **"Add repository"**

3. **如果提示 "This directory does not appear to be a Git repository"：**
   - 点击 **"create a repository"** 链接
   - 填写信息：
     - Name: `uav-qmix`（或保持默认）
     - Description: `QMIX-Based Multi-UAV Cooperative Coverage Path Planning`
     - 勾选 **"Initialize this repository with a README"**（如果还没有 README）
   - 点击 **"Create Repository"**

4. **查看更改：**
   - 左侧会显示所有要提交的文件
   - 在左下角输入提交信息，例如：`Initial commit: QMIX-based multi-UAV cooperative coverage path planning`

5. **提交更改：**
   - 点击左下角的 **"Commit to main"** 按钮

6. **发布到 GitHub：**
   - 点击右上角的 **"Publish repository"** 按钮
   - 或者如果已经连接，点击 **"Push origin"** 按钮
   - 如果提示选择仓库，选择：`wqing7523-cell/QMIX-Multi-UAV-Coverage`
   - 确保选择 **"Keep this code private"** 是**未勾选**状态（保持公开）
   - 点击 **"Publish Repository"**

### 方法二：先克隆再复制文件（如果方法一不行）

1. **克隆仓库：**
   - 在 GitHub Desktop 中，点击底部的 **"Clone wqing7523-cell/QMIX-Multi-UAV-Coverage"** 按钮
   - 选择保存位置（例如：`C:\Users\44358\Desktop\QMIX-Multi-UAV-Coverage`）
   - 点击 **"Clone"**

2. **复制文件：**
   - 将 `C:\Users\44358\Desktop\uav-qmix` 中的所有文件复制到克隆的文件夹中
   - 注意：不要复制 `.git` 文件夹（如果存在）

3. **提交并推送：**
   - 在 GitHub Desktop 中，您会看到所有新文件
   - 输入提交信息并点击 **"Commit to main"**
   - 点击 **"Push origin"** 上传

## 注意事项

- ✅ 确保 `.gitignore` 文件已存在，会自动排除不需要的文件
- ✅ 大文件（如模型文件、日志）会被自动排除
- ✅ 如果某些文件不想上传，可以取消勾选后再提交

## 完成后

上传完成后，访问以下链接查看您的仓库：
**https://github.com/wqing7523-cell/QMIX-Multi-UAV-Coverage**
