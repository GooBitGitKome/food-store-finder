# Google Cloud Run 最適化 Python 3.12 Dockerfile
FROM python:3.12-slim

# 標準出力・エラー出力を即時フラッシュ（Google Cloud Loggingでリアルタイム確認可能）
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# 最小限のシステムパッケージ（SSL証明書、curl）のインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 高速パッケージマネージャー uv を利用して依存関係をインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 依存定義ファイルをコピーしてDockerレイヤーキャッシュを活用
COPY pyproject.toml requirements.txt /app/

# プロダクション依存パッケージをシステム環境に直接インストール
RUN uv pip install --system --no-cache -r requirements.txt

# アプリケーションソースコードをコピー
COPY app /app/app

# Cloud Run のデフォルトポート
EXPOSE 8080

# Cloud Runから注入される $PORT 環境変数を展開して起動
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
