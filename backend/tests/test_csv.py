import pytest
from app.models.store import StoreModel
from app.services.csv_export import generate_stores_csv

def test_generate_stores_csv():
    stores = [
        StoreModel(
            id="node_12345",
            name="居酒屋 たぬき",
            category="居酒屋 (飲食店)",
            lat=35.6580,
            lon=139.7016,
            address="東京都渋谷区道玄坂1-2-3",
            phone="03-1234-5678",
            has_own_website=False,
            email="tanuki@example-izakaya.jp",
            email_source_url="https://www.instagram.com/tanuki/",
            email_confidence="HIGH",
            portal_urls=["https://tabelog.com/tokyo/A1303/A130301/13000000/"],
            sns_urls=["https://www.instagram.com/tanuki/"]
        )
    ]
    
    csv_str = generate_stores_csv(stores)
    
    # BOM付きチェック
    assert csv_str.startswith('\ufeff')
    # ヘッダーチェック
    assert "店舗名,大分類ジャンル,業態カテゴリ,GoogleマップURL,住所,電話番号,メールアドレス" in csv_str
    # レコードチェック
    assert "居酒屋 たぬき" in csv_str
    assert "レストラン・飲食店" in csv_str
    assert "https://www.google.com/maps" in csv_str
    assert "03-1234-5678" in csv_str
    assert "tanuki@example-izakaya.jp" in csv_str
    assert "なし" in csv_str  # 自前HP有無
