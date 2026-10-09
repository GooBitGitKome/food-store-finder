.PHONY: help install backend frontend test

help:
	@echo "利用可能なコマンド:"
	@echo "  make install    - uv と npm で全依存関係をセットアップ"
	@echo "  make backend    - uv で FastAPI サーバーを起動 (Port 8000)"
	@echo "  make frontend   - Next.js サーバーを起動 (Port 3000)"
	@echo "  make test       - uv でテストスイートを実行"

install:
	uv sync --all-packages --all-extras
	cd frontend && npm install

backend:
	uv run --package food-store-finder-backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm run dev

test:
	uv run --package food-store-finder-backend --group dev pytest -v backend/tests
