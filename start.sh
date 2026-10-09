#!/usr/bin/env bash
set -e

# カレントディレクトリをプロジェクトルートに設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export UV_LINK_MODE=copy
MODE="${1:-all}"

echo "=================================================="
echo " Food Store Finder 起動スクリプト (uv 対応)"
echo "=================================================="

case "$MODE" in
  backend)
    echo ">> バックエンド (FastAPI) を uv で起動します (Port: 8000)..."
    uv run --package food-store-finder-backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ;;
  frontend)
    echo ">> フロントエンド (Next.js) を起動します (Port: 3000)..."
    cd frontend && npm run dev
    ;;
  test)
    echo ">> テストスイートを uv で実行します..."
    uv run --package food-store-finder-backend --group dev pytest -v backend/tests
    ;;
  *)
    echo "使用方法: ./start.sh [backend | frontend | test]"
    echo ""
    echo "例:"
    echo "  ./start.sh backend   # バックエンドのみ起動"
    echo "  ./start.sh frontend  # フロントエンドのみ起動"
    echo "  ./start.sh test      # テストを実行"
    echo ""
    echo "※バックグラウンドで両方を同時起動したい場合:"
    echo "  nohup uv run --package food-store-finder-backend uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &"
    echo "  (cd frontend && nohup npm run dev > frontend.log 2>&1 &)"
    ;;
esac
