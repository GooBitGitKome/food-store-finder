# ADR-0001: 技術スタック選定 (Next.js + FastAPI + Leaflet)

## ステータス
Accepted (承認済)

## コンテキスト
自社Webサイトを持たない飲食店・食品店を地図上のPinおよび指定半径、または地名から抽出し、メールアドレス等の連絡先を探索してCSV保存するシステムを開発する。
ユーザーの直感的な地図操作（Pin設置・半径サークル描画）と、非同期でのデータ収集・スクレイピング・メール抽出ロジックを両立させる必要がある。

## 決定事項
以下の技術スタックを採用する。
1. **フロントエンド**: Next.js (App Router, React, TypeScript), Tailwind CSS, Leaflet (react-leaflet)
2. **バックエンド**: Python 3.14, FastAPI, Pydantic, httpx, BeautifulSoup4
3. **ストレージ**: SQLite (スプリント0〜2での軽量モック/キャッシュ)
4. **テストツール**: Pytest, pytest-asyncio

## 結果・影響
- **メリット**:
  - Pythonのスクレイピング・正規化ライブラリ資産（BeautifulSoup, regex, httpx）をフル活用可能。
  - Leafletによるオープンソースな地図UI構築により、商用マップAPIの地図タイル課金を回避。
  - FastAPIにより型安全で非同期I/Oに最適化されたREST APIを迅速に提供可能。
- **トレードオフ**:
  - フロントエンドとバックエンドの2つのランタイムを管理する必要がある（Docker Compose等で標準化）。
