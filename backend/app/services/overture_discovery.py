import math
import duckdb
import asyncio
from typing import List, Tuple, Dict, Any, Optional
from app.models.store import StoreModel
from app.services.website_judger import judge_website_status, extract_domain
from app.services.store_discovery import build_google_maps_url, is_public_building
from app.services.contact_miner import enrich_store_contacts

OVERTURE_S3_PATH = "s3://overturemaps-us-west-2/release/2026-09-23.1/theme=places/type=place/*"

OVERTURE_CATEGORY_LABELS: Dict[str, str] = {
    "restaurant": "レストラン",
    "japanese_restaurant": "日本料理・和食",
    "sushi_restaurant": "寿司店",
    "ramen_restaurant": "ラーメン店",
    "soba_restaurant": "蕎麦店",
    "udon_restaurant": "うどん店",
    "izakaya": "居酒屋",
    "yakitori_restaurant": "焼き鳥",
    "yakiniku_restaurant": "焼肉店",
    "chinese_restaurant": "中華料理",
    "italian_restaurant": "イタリア料理",
    "french_restaurant": "フランス料理",
    "korean_restaurant": "韓国料理",
    "thai_restaurant": "タイ料理",
    "indian_restaurant": "インド料理",
    "cafe": "カフェ",
    "coffee_shop": "喫茶店・コーヒー",
    "bar": "バー",
    "pub": "パブ",
    "bakery": "ベーカリー・パン屋",
    "pastry_shop": "洋菓子・スイーツ",
    "confectionery": "和菓子・菓子店",
    "deli": "惣菜・デリ",
    "fast_food": "ファストフード",
    "meal_takeaway": "テイクアウト",
    "butcher": "精肉店",
    "seafood_market": "鮮魚店",
}

def format_overture_category(basic_cat: Optional[str], tax_cat: Optional[str]) -> str:
    """Overtureカテゴリをわかりやすい日本語に変換"""
    if tax_cat and tax_cat in OVERTURE_CATEGORY_LABELS:
        return OVERTURE_CATEGORY_LABELS[tax_cat]
    if basic_cat and basic_cat in OVERTURE_CATEGORY_LABELS:
        return OVERTURE_CATEGORY_LABELS[basic_cat]
    raw = tax_cat or basic_cat or "飲食店"
    return OVERTURE_CATEGORY_LABELS.get(raw, raw.replace("_", " "))

def determine_overture_genre(basic_cat: Optional[str], tax_cat: Optional[str]) -> str:
    """Overtureカテゴリから大分類ジャンル (restaurant/cafe/food/public_building) を判定"""
    combined = f"{basic_cat or ''} {tax_cat or ''}".lower()
    if any(k in combined for k in ["cafe", "coffee", "bar", "pub", "tea"]):
        return "cafe"
    if any(k in combined for k in ["bakery", "pastry", "confectionery", "deli", "sweet", "butcher", "seafood"]):
        return "food"
    if any(k in combined for k in ["public", "government", "community", "townhall", "civic"]):
        return "public_building"
    return "restaurant"

def calculate_bbox(lat: float, lon: float, radius_meters: int) -> Tuple[float, float, float, float]:
    """緯度経度と探索半径(m)から Bounding Box (min_lon, max_lon, min_lat, max_lat) を算出"""
    lat_delta = radius_meters / 111000.0
    lon_delta = radius_meters / (111000.0 * math.cos(math.radians(lat)))
    return (
        round(lon - lon_delta, 6),
        round(lon + lon_delta, 6),
        round(lat - lat_delta, 6),
        round(lat + lat_delta, 6)
    )

def query_overture_places_sync(
    min_lon: float,
    max_lon: float,
    min_lat: float,
    max_lat: float,
    categories: List[str]
) -> List[Dict[str, Any]]:
    """DuckDBを使用してS3上のOverture Places GeoParquetからデータを直接ストリーミング抽出"""
    conn = duckdb.connect()
    try:
        conn.execute("INSTALL httpfs; LOAD httpfs;")
        conn.execute("SET s3_region = 'us-west-2';")

        cat_conditions = []
        if "restaurant" in categories:
            cat_conditions.extend([
                "basic_category IN ('restaurant', 'meal_takeaway', 'meal_delivery', 'fast_food')",
                "taxonomy.primary LIKE '%restaurant%'"
            ])
        if "cafe" in categories:
            cat_conditions.extend([
                "basic_category IN ('cafe', 'bar', 'pub')",
                "taxonomy.primary LIKE '%cafe%'",
                "taxonomy.primary LIKE '%bar%'",
                "taxonomy.primary LIKE '%coffee%'"
            ])
        if "food" in categories:
            cat_conditions.extend([
                "basic_category IN ('bakery', 'confectionery', 'deli')",
                "taxonomy.primary LIKE '%bakery%'",
                "taxonomy.primary LIKE '%pastry%'",
                "taxonomy.primary LIKE '%food%'"
            ])
        if "public_building" in categories:
            cat_conditions.extend([
                "basic_category LIKE '%public%'",
                "taxonomy.primary LIKE '%community%'",
                "taxonomy.primary LIKE '%townhall%'"
            ])

        if not cat_conditions:
            cat_conditions = [
                "basic_category IN ('restaurant', 'cafe', 'bar', 'bakery', 'meal_takeaway')",
                "taxonomy.primary LIKE '%restaurant%'",
                "taxonomy.primary LIKE '%cafe%'"
            ]

        where_cat_clause = " OR ".join(cat_conditions)

        sql = f"""
        SELECT 
            id,
            names.primary AS name,
            basic_category,
            taxonomy.primary AS taxonomy_cat,
            websites,
            socials,
            phones,
            emails,
            brand.names.primary AS brand_name,
            addresses[1].freeform AS address,
            addresses[1].locality AS locality,
            bbox.xmin AS lon,
            bbox.ymin AS lat
        FROM read_parquet('{OVERTURE_S3_PATH}', hive_partitioning=1)
        WHERE bbox.xmin >= {min_lon} AND bbox.xmax <= {max_lon}
          AND bbox.ymin >= {min_lat} AND bbox.ymax <= {max_lat}
          AND ({where_cat_clause})
        LIMIT 300;
        """

        cursor = conn.execute(sql)
        cols = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()

async def discover_stores_overture(
    lat: float,
    lon: float,
    radius_meters: int,
    categories: List[str],
    only_without_website: bool = True,
    enrich_contacts: bool = True,
    max_enrich_count: int = 15
) -> Tuple[List[StoreModel], int, int, int]:
    """
    Overture Maps Placesから店舗を探索し、自前HP有無判定・連絡先補完を行ったリストを返却する
    """
    min_lon, max_lon, min_lat, max_lat = calculate_bbox(lat, lon, radius_meters)

    # I/O負荷の高いDuckDBクエリを別スレッドで非同期実行
    raw_records = await asyncio.to_thread(
        query_overture_places_sync, min_lon, max_lon, min_lat, max_lat, categories
    )

    total_found = len(raw_records)
    stores: List[StoreModel] = []
    seen_ids = set()

    for item in raw_records:
        rec_id = item.get("id") or ""
        if rec_id in seen_ids:
            continue
        seen_ids.add(rec_id)

        name = item.get("name") or item.get("brand_name") or "名称未設定"
        basic_cat = item.get("basic_category")
        tax_cat = item.get("taxonomy_cat")

        category_label = format_overture_category(basic_cat, tax_cat)
        genre = determine_overture_genre(basic_cat, tax_cat)

        # 公共建築物の除外 (categoriesに指定がない場合)
        if genre == "public_building" and "public_building" not in categories:
            continue

        raw_websites = item.get("websites") or []
        raw_socials = item.get("socials") or []
        raw_phones = item.get("phones") or []
        raw_emails = item.get("emails") or []

        # 住所の整形
        address = item.get("address") or item.get("locality") or ""

        # 自前HPの判定
        tags_for_judge = {
            "name": name,
            "brand": item.get("brand_name") or "",
        }
        if raw_websites:
            tags_for_judge["website"] = raw_websites[0]

        has_own, primary_url, portal_urls, sns_urls = judge_website_status(tags_for_judge)

        # OvertureネイティブのSNSやWebサイトを追加マージ
        for w in raw_websites:
            w_dom = extract_domain(w)
            if any(p in w_dom for p in ["tabelog.com", "gnavi.co.jp", "hotpepper.jp", "retty.me", "ubereats.com"]):
                if w not in portal_urls:
                    portal_urls.append(w)
            elif any(s in w_dom for s in ["facebook.com", "instagram.com", "x.com", "twitter.com", "line.me"]):
                if w not in sns_urls:
                    sns_urls.append(w)

        for soc in raw_socials:
            if soc and soc not in sns_urls:
                sns_urls.append(soc)

        # 自前Webサイト無しの店舗のみ抽出
        if only_without_website and has_own:
            continue

        phone = raw_phones[0] if raw_phones else None
        email = raw_emails[0] if raw_emails else None
        email_conf = "HIGH" if email else "NONE"

        el_lat = float(item.get("lat") or lat)
        el_lon = float(item.get("lon") or lon)
        gmaps_url = build_google_maps_url(name, address, el_lat, el_lon)

        store = StoreModel(
            id=f"overture_{rec_id}",
            name=name,
            category=category_label,
            genre=genre,
            lat=el_lat,
            lon=el_lon,
            address=address,
            phone=phone,
            has_own_website=has_own,
            raw_website=primary_url,
            portal_urls=portal_urls,
            sns_urls=sns_urls,
            email=email,
            email_source_url=primary_url,
            email_confidence=email_conf,
            google_maps_url=gmaps_url,
            additional_info={"overture_id": rec_id, "basic_category": basic_cat}
        )
        stores.append(store)

    without_website_count = len(stores)

    # メールアドレス未取得店舗に対してWeb補完
    if enrich_contacts:
        tasks = []
        for i, st in enumerate(stores):
            if not st.email and i < max_enrich_count:
                tasks.append(enrich_store_contacts(st.name, st.address, {}, allow_online_search=True))
            else:
                tasks.append(asyncio.sleep(0, result=None))

        enrich_results = await asyncio.gather(*tasks, return_exceptions=True)
        for st, res in zip(stores, enrich_results):
            if isinstance(res, dict) and res.get("email"):
                st.email = res.get("email")
                st.email_source_url = res.get("email_source_url")
                st.email_confidence = res.get("email_confidence", "NONE")

    with_contact_count = sum(1 for s in stores if s.email or s.phone or len(s.sns_urls) > 0)

    return stores, total_found, without_website_count, with_contact_count
