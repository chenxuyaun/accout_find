#!/usr/bin/env bash
# =============================================================================
# LiteLLM Proxy 安全启动脚本
#
# 功能：
#   1. 检查 .env 文件中的密钥是否已从默认值更换
#   2. 若使用默认密钥则阻止启动（生产安全）
#   3. 通过检查后启动 Docker Compose 服务
#
# 用法：
#   chmod +x start.sh
#   ./start.sh           # 安全检查 + 启动
#   ./start.sh --dev     # 跳过安全检查（仅开发环境）
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  LiteLLM Proxy 启动前检查"
echo "============================================"

# 开发模式跳过安全检查
if [ "${1:-}" = "--dev" ]; then
    echo "[INFO] 开发模式：跳过密钥安全检查"
else
    # 运行安全检查脚本
    if python3 check_keys.py --strict; then
        echo ""
    else
        echo ""
        echo "启动被阻止：请先更换 .env 中的默认密钥。"
        echo "开发环境可使用 --dev 跳过检查："
        echo "  ./start.sh --dev"
        exit 1
    fi
fi

# 检查 .env 文件存在
if [ ! -f .env ]; then
    echo "[ERROR] 未找到 .env 文件，请从 .env.example 复制："
    echo "  cp .env.example .env"
    exit 1
fi

# 启动 Docker Compose 服务
echo "[INFO] 启动 LiteLLM Proxy 服务..."
docker-compose up -d

# 等待服务就绪
echo "[INFO] 等待服务就绪..."
sleep 5

# 健康检查
if curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/health | grep -q "200"; then
    echo "[OK] LiteLLM Proxy 启动成功！"
    echo "  管理 UI: http://localhost:4000"
    echo "  API:     http://localhost:4000/health"
else
    echo "[WARNING] 服务已启动但健康检查未通过，请稍后重试或查看日志："
    echo "  docker-compose logs -f litellm"
fi
