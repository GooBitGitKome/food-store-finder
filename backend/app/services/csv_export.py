import csv
import io
from typing import List
from app.models.store import StoreModel

def generate_stores_csv(stores: List[StoreModel]) -> str:
    """
    店舗リストをBOM付きUTF-8のCSV文字列に変換する。
    Excelで直接開いた場合にも文字化けしないよう \ufeff を付与。
    """
    output = io.StringIO()
    # UTF-8 BOM
    output.write('\ufeff')
    
    fieldnames = [
        "店舗名",
        "大分類ジャンル",
        "業態カテゴリ",
        "GoogleマップURL",
        "住所",
        "電話番号",
        "メールアドレス",
        "メール取得元",
        "メール信頼度",
        "SNSリンク",
        "ポータルURL",
        "自前HP有無",
        "緯度",
        "経度",
        "ID"
    ]
    
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(fieldnames)
    
    genre_labels = {
        "restaurant": "レストラン・飲食店",
        "cafe": "カフェ・喫茶・バー",
        "food": "食品・ベーカリー・専門店",
        "public_building": "公共施設・公的機関"
    }

    for s in stores:
        genre_display = genre_labels.get(s.genre or "", s.genre or "飲食店")
        gmaps = s.google_maps_url or f"https://www.google.com/maps/search/?api=1&query={s.lat},{s.lon}"
        writer.writerow([
            s.name,
            genre_display,
            s.category,
            gmaps,
            s.address,
            s.phone or "",
            s.email or "",
            s.email_source_url or "",
            s.email_confidence or "",
            "; ".join(s.sns_urls),
            "; ".join(s.portal_urls),
            "あり" if s.has_own_website else "なし",
            str(s.lat),
            str(s.lon),
            s.id
        ])
        
    return output.getvalue()
