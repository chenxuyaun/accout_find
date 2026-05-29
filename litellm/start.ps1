# =============================================================================
# LiteLLM Proxy 安全启动脚本 (Windows PowerShell)
#
# 功能：
#   1. 检查 .env 文件中的密钥是否已从默认值更换
#   2. 若使用默认密钥则阻止启动（生产安全）
#   3. 通过检查后启动 Docker Compose 服务
#
# 用法：
#   .\start.ps1           # 安全检查 + 启动
#   .\start.ps1 -Dev      # 跳过安全检查（仅开发环境）
# =============================================================================

param(
    [switch]$Dev
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "============================================"
Write-Host "  LiteLLM Proxy 启动前检查"
Write-Host "============================================"

if ($Dev) {
    Write-Host "[INFO] 开发模式：跳过密钥安全检查"
} else {
    # 运行安全检查脚本
    python3 check_keys.py --strict
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "启动被阻止：请先更换 .env 中的默认密钥。"
        Write-Host "开发环境可使用 -Dev 跳过检查："
        Write-Host "  .\start.ps1 -Dev"
        exit 1
    }
}

# 检查 .env 文件存在
if (-not (Test-Path ".env")) {
    Write-Host "[ERROR] 未找到 .env 文件，请从 .env.example 复制："
    Write-Host "  copy .env.example .env"
    exit 1
}

# 启动 Docker Compose 服务
Write-Host "[INFO] 启动 LiteLLM Proxy 服务..."
docker-compose up -d

# 等待服务就绪
Write-Host "[INFO] 等待服务就绪..."
Start-Sleep -Seconds 5

# 健康检查
try {
    $response = Invoke-WebRequest -Uri "http://localhost:4000/health" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] LiteLLM Proxy 启动成功！"
        Write-Host "  管理 UI: http://localhost:4000"
        Write-Host "  API:     http://localhost:4000/health"
    }
} catch {
    Write-Host "[WARNING] 服务已启动但健康检查未通过，请稍后重试或查看日志："
    Write-Host "  docker-compose logs -f litellm"
}
