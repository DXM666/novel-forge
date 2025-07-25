# NovelForge 环境配置设置脚本
# 用于快速设置开发环境的环境变量

Write-Host "🚀 NovelForge 环境配置设置" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# 检查是否存在 .env 文件
$envFile = "backend\.env"
$envExampleFile = "backend\.env.example"

if (Test-Path $envFile) {
    Write-Host "⚠️  发现已存在的 .env 文件" -ForegroundColor Yellow
    $overwrite = Read-Host "是否要覆盖现有配置？(y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "❌ 操作已取消" -ForegroundColor Red
        exit 1
    }
}

# 复制模板文件
if (Test-Path $envExampleFile) {
    Copy-Item $envExampleFile $envFile
    Write-Host "✅ 已从模板创建 .env 文件" -ForegroundColor Green
} else {
    Write-Host "❌ 找不到 .env.example 模板文件" -ForegroundColor Red
    exit 1
}

# 生成随机密钥
function Generate-RandomKey {
    param([int]$Length = 32)
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    $key = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $key += $chars[(Get-Random -Maximum $chars.Length)]
    }
    return $key
}

# 更新配置文件
$secretKey = Generate-RandomKey -Length 64
$jwtKey = Generate-RandomKey -Length 32

Write-Host "🔐 正在生成安全密钥..." -ForegroundColor Cyan

# 读取并更新 .env 文件
$content = Get-Content $envFile
$content = $content -replace "SECRET_KEY=your_secret_key_here", "SECRET_KEY=$secretKey"
$content = $content -replace "JWT_SECRET_KEY=your_jwt_secret_key_here", "JWT_SECRET_KEY=$jwtKey"

# 写回文件
$content | Set-Content $envFile

Write-Host "✅ 已生成安全密钥" -ForegroundColor Green

# 提示用户需要手动配置的项目
Write-Host ""
Write-Host "📝 请手动配置以下项目：" -ForegroundColor Yellow
Write-Host "1. OPENAI_API_KEY - 你的 OpenAI API 密钥"
Write-Host "2. DATABASE_PASSWORD - 数据库密码"
Write-Host "3. REDIS_PASSWORD - Redis 密码（如果需要）"
Write-Host ""
Write-Host "📂 配置文件位置: $envFile" -ForegroundColor Cyan
Write-Host "📖 详细说明请查看: docs\security_configuration.md" -ForegroundColor Cyan

# 检查 .gitignore
if (Select-String -Path ".gitignore" -Pattern "backend/\.env" -Quiet) {
    Write-Host "✅ .env 文件已在 .gitignore 中，不会被提交到 Git" -ForegroundColor Green
} else {
    Write-Host "⚠️  警告：.env 文件可能没有被 .gitignore 忽略！" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 环境配置设置完成！" -ForegroundColor Green
Write-Host "请编辑 $envFile 文件，填入你的实际配置值。" -ForegroundColor White
