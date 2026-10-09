# Food Store Finder (自前Webサイトなし飲食店検索＆連絡先収集システム)

自社公式Webサイト（ホームページ）を保有していない飲食店・食品店を地図上のPinや指定半径、または地名から抽出し、E-mailアドレスをはじめとする各種連絡先（SNS、電話番号、住所）を一覧化してCSV出力するフルスタックWebアプリケーションです。

---

## 🌐 公開デモサイト

以下のリンクより、デモサイトを直接ブラウザでお試しいただけます：

👉 **[https://food-store-finder.pages.dev/](https://food-store-finder.pages.dev/)**

- **フロントエンド**: Cloudflare Pages
- **バックエンド API**: Google Cloud Run (`asia-northeast1`)

---

## 主な機能

1. **柔軟な範囲指定 & 現在地取得**:
   - 地名・住所入力による自動ジオコーディング（例: 「東京都港区麻布十番」）
   - ブラウザの位置情報（Geolocation API）を利用した**現在地ワンクリック取得**
   - Leaflet地図上のPinドラッグ＆クリック配置、探索半径スライダー（100m 〜 最大100km対応）
2. **ジャンル分類 & リアルタイムフィルタリング**:
   - **検索条件指定**: 飲食店・レストラン、カフェ・喫茶、食品・ベーカリー・専門店などのジャンルを事前選択可能
   - **テーブル即時切り替え**: 取得後も「すべて / 飲食店 / カフェ / 食品・ベーカリー」タブでワンクリック絞り込み
   - 各店舗にジャンル別の色分けバッジ（🍽️ 飲食店 / ☕ カフェ / 🥖 食品）を表示
3. **Google Maps 別ページ誘導 (API課金ゼロ)**:
   - 一覧テーブル各行に目立つ **「Google Map ↗」誘導ボタン** を配置
   - 店舗名リンクおよび地図上のピンポップアップ内にもGoogleマップリンクを設置
   - Google Maps APIキーを使わない公式Universal URLスキームにより、完全無料でGoogleマップの店舗詳細・クチコミ・外観写真へ誘導
4. **自社Webサイト有無判定**:
   - 食べログ、ぐるなび、ホットペッパー、UberEatsなどのグルメポータルやSNSのみの店舗を「自社HPなし」と正確に判定。
   - 独自ドメインを持つチェーン店・店舗は自動除外可能。
5. **連絡先ハイブリッド補完**:
   - 自社HPを持たない店舗に対して、OSMタグや公開Web探索からメールアドレスを発掘。
   - メール未公開の小規模店でも、電話番号、住所、SNSアカウント（Instagram等）、ポータルURLで最大限補完。
6. **Excel対応 CSVエクスポート**:
   - 大分類ジャンル、Google Maps URLを含めた、日本語Excelで文字化けしない UTF-8 (BOM付き) 形式で出力。

---

## アーキテクチャ構成 & 配置ファイル一覧

```
food-store-finder/
├── pyproject.toml              # uv ワークスペース定義 (ルート)
├── Makefile                    # make コマンドによる簡易起動
├── start.sh                    # uv 対応ワンストップ起動スクリプト
├── README.md                   # 本ドキュメント
│
├── backend/                    # Python FastAPI バックエンド
│   ├── pyproject.toml          # uv / PEP 621 プロジェクト設定 & 依存関係
│   ├── uv.lock                 # uv ロックファイル (再現性保証)
│   ├── requirements.txt        # pip 互換用要件定義
│   ├── pytest.ini              # テスト設定
│   ├── app/
│   │   ├── main.py             # FastAPI エントリポイント
│   │   ├── core/config.py      # 設定 (Overpass, Nominatim, UA等)
│   │   ├── models/store.py     # Pydantic モデル定義
│   │   ├── services/
│   │   │   ├── geo.py          # ジオコーディング (Nominatim)
│   │   │   ├── website_judger.py # 自前HP判定 (ポータル/SNSドメイン判別)
│   │   │   ├── store_discovery.py # Overpass API 連携探索
│   │   │   ├── contact_miner.py # メール/SNSハイブリッド深層探索
│   │   │   └── csv_export.py   # BOM付きCSV生成
│   │   └── api/routes.py       # REST API ルーティング
│   └── tests/                  # Pytest 自動テストスイート (全13件)
│
├── frontend/                   # Next.js 14 フロントエンド
│   ├── package.json            # npm パッケージ定義
│   ├── tsconfig.json           # TypeScript 設定
│   └── src/
│       ├── app/page.tsx        # メインダッシュボード画面
│       └── components/
│           ├── MapComponent.tsx # Leaflet 地図 UI (Pin/半径/マーカー)
│           └── StoreTable.tsx   # 店舗一覧・フィルタ・CSVエクスポート
│
└── docs/adr/                   # アーキテクチャ決定記録 (ADR)
    ├── ADR-0001-technology-stack.md
    └── ADR-0002-osm-hybrid-data-source.md
```

---

## UV を使用したクイックスタート

Pythonパッケージマネージャー **`uv`** を使用して即座に起動・テストできます。

### 1. 依存関係の同期
プロジェクトルートで以下を実行します：
```bash
uv sync
```
（または `make install`）

### 2. バックエンドの起動 (Port: 8000)
```bash
# スクリプト利用
./start.sh backend

# または make 利用
make backend

# または uv 直接実行
uv run --package food-store-finder-backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API仕様書 (Swagger UI): `http://localhost:8000/docs`

### 3. フロントエンドの起動 (Port: 3000)
```bash
# スクリプト利用
./start.sh frontend

# または make 利用
make frontend

# または npm 直接実行
cd frontend && npm run dev
```
Web UI: `http://localhost:3000`

### 4. テストの実行
```bash
# スクリプト利用 (推奨)
./start.sh test

# または make 利用
make test

# または uv 直接実行
uv run --with pytest --with pytest-asyncio pytest -v backend/tests
```
# food-store-finder
