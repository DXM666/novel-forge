# 从Git跟踪中移除.env文件的脚本
# 如果.env文件已经被提交到Git，使用此脚本移除跟踪

Write-Host "🔧 从Git跟踪中移除敏感配置文件" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Yellow

# 检查是否在Git仓库中
if (-not (Test-Path ".git")) {
    Write-Host "❌ 当前目录不是Git仓库" -ForegroundColor Red
    exit 1
}

# 要移除的敏感文件列表
$sensitiveFiles = @(
    "backend/.env",
    "frontend/.env",
    ".env"
)

$removedFiles = @()

foreach ($file in $sensitiveFiles) {
    # 检查文件是否被Git跟踪
    $isTracked = git ls-files --error-unmatch $file 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "🔍 发现被跟踪的敏感文件: $file" -ForegroundColor Yellow
        
        # 从Git索引中移除文件，但保留本地文件
        git rm --cached $file
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 已从Git跟踪中移除: $file" -ForegroundColor Green
            $removedFiles += $file
        } else {
            Write-Host "❌ 移除失败: $file" -ForegroundColor Red
        }
    }
}

if ($removedFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "📝 已移除的文件:" -ForegroundColor Cyan
    foreach ($file in $removedFiles) {
        Write-Host "   - $file" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "⚠️  重要提醒:" -ForegroundColor Yellow
    Write-Host "1. 这些文件仍然存在于本地，只是不再被Git跟踪"
    Write-Host "2. 请提交这次更改以确保.env文件不再被跟踪："
    Write-Host "   git add .gitignore"
    Write-Host "   git commit -m 'Remove sensitive .env files from Git tracking'"
    Write-Host "3. 如果这些文件包含敏感信息，考虑轮换API密钥"
    
} else {
    Write-Host "✅ 没有发现被Git跟踪的敏感文件" -ForegroundColor Green
}

Write-Host ""
Write-Host "🔒 安全检查完成！" -ForegroundColor Green
