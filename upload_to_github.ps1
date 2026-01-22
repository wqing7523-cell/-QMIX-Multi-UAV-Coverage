# PowerShell script to upload code to GitHub repository
# Repository: https://github.com/wqing7523-cell/QMIX-Multi-UAV-Coverage

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading code to GitHub repository" -ForegroundColor Cyan
Write-Host "Repository: wqing7523-cell/QMIX-Multi-UAV-Coverage" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "Git is installed: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Git is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Navigate to project directory
$projectDir = "C:\Users\44358\Desktop\uav-qmix"
Set-Location $projectDir
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Green
Write-Host ""

# Check if .git exists
if (Test-Path ".git") {
    Write-Host "Git repository already initialized" -ForegroundColor Green
} else {
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    git init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to initialize Git repository" -ForegroundColor Red
        exit 1
    }
}

# Add remote if not exists
Write-Host "Checking remote repository..." -ForegroundColor Yellow
$remoteExists = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Adding remote repository..." -ForegroundColor Yellow
    git remote add origin https://github.com/wqing7523-cell/QMIX-Multi-UAV-Coverage.git
    Write-Host "Remote added successfully" -ForegroundColor Green
} else {
    Write-Host "Remote already exists: $remoteExists" -ForegroundColor Green
}

# Add all files
Write-Host ""
Write-Host "Adding files to Git..." -ForegroundColor Yellow
git add .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to add files" -ForegroundColor Red
    exit 1
}

# Check if there are changes to commit
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "No changes to commit. All files are up to date." -ForegroundColor Yellow
} else {
    Write-Host "Files to be committed:" -ForegroundColor Cyan
    git status --short
    Write-Host ""
    
    # Commit changes
    Write-Host "Committing changes..." -ForegroundColor Yellow
    git commit -m "Initial commit: QMIX-based multi-UAV cooperative coverage path planning"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to commit changes" -ForegroundColor Red
        exit 1
    }
    Write-Host "Changes committed successfully" -ForegroundColor Green
}

# Push to GitHub
Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "Note: You may be prompted to enter your GitHub credentials" -ForegroundColor Yellow
Write-Host ""

# Set default branch to main
git branch -M main 2>$null

# Push to origin
git push -u origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Error: Failed to push to GitHub" -ForegroundColor Red
    Write-Host "Possible reasons:" -ForegroundColor Yellow
    Write-Host "1. Authentication failed - you may need to use a Personal Access Token" -ForegroundColor Yellow
    Write-Host "2. Network connection issue" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternative: Use GitHub Desktop to upload files" -ForegroundColor Cyan
    Write-Host "Or follow the manual steps in QUICK_START_GITHUB.md" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Success! Code uploaded to GitHub" -ForegroundColor Green
Write-Host "Repository: https://github.com/wqing7523-cell/QMIX-Multi-UAV-Coverage" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
