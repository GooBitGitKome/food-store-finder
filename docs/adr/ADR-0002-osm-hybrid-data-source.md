# ADR-0002: OpenStreetMap (Overpass API) + ハイブリッド探索方式の採用

## ステータス
Accepted (承認済)

## コンテキスト
店舗母集団の取得において、Google Places APIは網羅性が高い一方で以下の課題がある：
1. 従量課金が発生し、広範囲や多数の店舗を検索した際のコストが大きい。
2. Google利用規約（ToS）により、Place ID以外の店舗属性データを自社DBに永続キャッシュしたりCSVとして一括エクスポートすることに厳格な制約が存在する。

## 決定事項
1. **店舗母集団の抽出**: OpenStreetMap (OSM) の Overpass API を採用。
   - `amenity` (restaurant, cafe, fast_food, bar, pub) および `shop` (bakery, confectionery, deli, butcher, seafood 等) を検索対象とする。
   - 地名からの座標解決には Nominatim API を利用。
2. **自前Webサイト有無判定**:
   - OSMタグ内の `website`, `contact:website` を検査。
   - URLが未登録、またはポータルサイト（食べログ、ぐるなび、ホットペッパー、UberEats等）やSNS（Instagram等）のみの場合は「自前Webサイトなし」と判定。
3. **連絡先情報補完（ハイブリッド探索）**:
   - メールアドレスが見つからない場合、電話番号・住所・SNSアカウント等を代替・補完情報としてCSVに記録する。
   - 深層探索として、店舗名＋電話番号・地域名をキーにしたWeb公開情報からのメールアドレス・SNSリンク抽出を試みる。

## 結果・影響
- **メリット**:
  - API利用コストゼロで完全オープンなデータを自由に出力・CSVエクスポート可能（ODbLライセンスの帰属表示のみで対応可能）。
  - Google Places APIのToSリスクを回避できる。
- **トレードオフ**:
  - 一部の地方地域や開店直後の店舗でOSMのカバレッジに偏りがある可能性がある（今後のスプリントで他オープンソースデータソースの併用も検討可能）。
