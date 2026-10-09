import asyncio
import httpx
import urllib.parse
from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.models.store import StoreModel
from app.services.website_judger import judge_website_status
from app.services.contact_miner import enrich_store_contacts

CATEGORY_MAP = {
    "restaurant": 'node["amenity"~"restaurant|fast_food|food_court"]["amenity"!="public_building"]["building"!="public"]["building"!="public_building"](around:{radius}, {lat}, {lon}); way["amenity"~"restaurant|fast_food|food_court"]["amenity"!="public_building"]["building"!="public"]["building"!="public_building"](around:{radius}, {lat}, {lon});',
    "cafe": 'node["amenity"~"cafe|bar|pub"]["amenity"!="public_building"](around:{radius}, {lat}, {lon}); way["amenity"~"cafe|bar|pub"]["amenity"!="public_building"](around:{radius}, {lat}, {lon});',
    "food": 'node["shop"~"bakery|confectionery|pastry|deli|butcher|seafood"](around:{radius}, {lat}, {lon}); way["shop"~"bakery|confectionery|pastry|deli|butcher|seafood"](around:{radius}, {lat}, {lon});',
    "public_building": 'node["amenity"~"public_building|townhall|community_centre"](around:{radius}, {lat}, {lon}); way["amenity"~"public_building|townhall|community_centre"](around:{radius}, {lat}, {lon});'
}

PUBLIC_BUILDING_AMENITIES = {
    "public_building", "townhall", "community_centre", "social_facility",
    "courthouse", "police", "fire_station", "post_office", "library",
    "civic", "government", "embassy"
}

PUBLIC_BUILDING_TAG_VALUES = {
    "public", "public_building", "civic", "government"
}

def is_public_building(tags: Dict[str, str]) -> bool:
    """公共建築物・公的機関・行政施設かどうかを判定"""
    amenity = tags.get("amenity", "").lower()
    building = tags.get("building", "").lower()
    office = tags.get("office", "").lower()
    
    if amenity in PUBLIC_BUILDING_AMENITIES:
        return True
    if building in PUBLIC_BUILDING_TAG_VALUES:
        return True
    if office in ["government", "administrative", "public"]:
        return True
    return False

def format_address(tags: Dict[str, str]) -> str:
    """OSMの住所系タグから1つの日本語住所文字列を組み立てる"""
    if "addr:full" in tags:
        return tags["addr:full"]
    parts = []
    for k in ["addr:province", "addr:city", "addr:suburb", "addr:neighbourhood", "addr:quarter", "addr:street", "addr:block_number", "addr:housenumber"]:
        if k in tags and tags[k]:
            parts.append(tags[k])
    if parts:
        return "".join(parts)
    return ""

def determine_genre(tags: Dict[str, str]) -> str:
    """OSMタグから大分類ジャンル (restaurant / cafe / food / public_building / other) を判定"""
    if is_public_building(tags):
        return "public_building"

    amenity = tags.get("amenity", "")
    shop = tags.get("shop", "")
    if amenity in ["cafe", "bar", "pub"]:
        return "cafe"
    if shop:
        return "food"
    if amenity in ["restaurant", "fast_food", "food_court"] or "cuisine" in tags:
        return "restaurant"
    return "other"

def build_google_maps_url(name: str, address: str, lat: float, lon: float) -> str:
    """Google Mapsで店舗・場所を開くURL (API料金不要のWebリンク)"""
    search_query = f"{name} {address}".strip()
    if search_query and name != "名称未設定":
        return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(search_query)}"
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"

def format_category(tags: Dict[str, str]) -> str:
    """業態のわかりやすい日本語表示"""
    if is_public_building(tags):
        return "公共施設・公的建築物"
    if "cuisine" in tags:
        return f"{tags.get('cuisine')} (飲食店)"
    if "amenity" in tags:
        am = tags["amenity"]
        labels = {
            "restaurant": "レストラン", "cafe": "カフェ", "fast_food": "ファストフード",
            "bar": "バー", "pub": "パブ", "food_court": "フードコート",
            "public_building": "公共施設・公的建築物"
        }
        return labels.get(am, am)
    if "shop" in tags:
        sh = tags["shop"]
        labels = {"bakery": "ベーカリー・パン屋", "confectionery": "和菓子・洋菓子", "pastry": "ペストリー", "deli": "総菜屋", "butcher": "精肉店", "seafood": "鮮魚店"}
        return labels.get(sh, sh)
    return "飲食店・食品店"

async def fetch_stores_from_overpass(
    lat: float,
    lon: float,
    radius_meters: int,
    categories: List[str]
) -> List[Dict[str, Any]]:
    """Overpass APIにクエリを送信し、生の要素リストを取得する"""
    query_parts = []
    for cat in categories:
        if cat in CATEGORY_MAP:
            query_parts.append(CATEGORY_MAP[cat].format(radius=radius_meters, lat=lat, lon=lon))
            
    if not query_parts:
        # デフォルトは全カテゴリ
        for q in CATEGORY_MAP.values():
            query_parts.append(q.format(radius=radius_meters, lat=lat, lon=lon))

    op_timeout = 90 if radius_meters >= 30000 else (50 if radius_meters >= 10000 else 25)
    overpass_query = f"""
    [out:json][timeout:{op_timeout}];
    (
      {"".join(query_parts)}
    );
    out center tags;
    """

    headers = {
        "User-Agent": settings.USER_AGENT
    }

    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
        resp = await client.post(
            settings.OVERPASS_API_URL,
            content=overpass_query.encode("utf-8"),
            headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("elements", [])

async def discover_stores(
    lat: float,
    lon: float,
    radius_meters: int,
    categories: List[str],
    only_without_website: bool = True,
    enrich_contacts: bool = True,
    max_enrich_count: int = 15
) -> Tuple[List[StoreModel], int, int, int]:
    """
    店舗を探索し、自社HP有無の判定と連絡先補完を行ったリストを返却する
    """
    elements = await fetch_stores_from_overpass(lat, lon, radius_meters, categories)
    
    raw_stores: List[StoreModel] = []
    seen_ids = set()

    for el in elements:
        osm_id = f"{el.get('type')}_{el.get('id')}"
        if osm_id in seen_ids:
            continue
        seen_ids.add(osm_id)

        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:ja") or tags.get("brand") or "名称未設定"
        
        # 緯度経度の抽出 (node or way center)
        el_lat = el.get("lat") or (el.get("center", {}).get("lat") if "center" in el else None)
        el_lon = el.get("lon") or (el.get("center", {}).get("lon") if "center" in el else None)
        if el_lat is None or el_lon is None:
            continue

        category = format_category(tags)
        genre = determine_genre(tags)

        # 公共建築物 (public_building) の除外
        # 検索カテゴリに明示的に "public_building" が含まれていない場合、飲食店リストから確実に除外
        if is_public_building(tags) and "public_building" not in categories:
            continue

        address = format_address(tags)
        phone = tags.get("phone") or tags.get("contact:phone")
        gmaps_url = build_google_maps_url(name, address, float(el_lat), float(el_lon))

        # 抽出された店舗名を判定用tagsに反映
        eval_tags = dict(tags)
        eval_tags["name"] = name
        has_own_website, primary_url, portal_urls, sns_urls = judge_website_status(eval_tags)

        # フィルタリング: 自社Webサイト無しの店舗のみ抽出
        if only_without_website and has_own_website:
            continue

        store = StoreModel(
            id=osm_id,
            name=name,
            category=category,
            genre=genre,
            lat=float(el_lat),
            lon=float(el_lon),
            address=address,
            phone=phone,
            has_own_website=has_own_website,
            raw_website=primary_url,
            portal_urls=portal_urls,
            sns_urls=sns_urls,
            google_maps_url=gmaps_url,
            additional_info={"tags": tags}
        )
        raw_stores.append(store)

    total_found = len(elements)
    without_website_count = len(raw_stores)

    # 連絡先のハイブリッド補完（メール探索 & SNS等）
    # レートリミットとパフォーマンスを考慮し上位N件にオンライン探索を適用
    if enrich_contacts:
        tasks = []
        for i, st in enumerate(raw_stores):
            allow_online = (i < max_enrich_count)
            tags = st.additional_info.get("tags", {})
            tasks.append(enrich_store_contacts(st.name, st.address, tags, allow_online_search=allow_online))
            
        enrich_results = await asyncio.gather(*tasks, return_exceptions=True)
        for st, res in zip(raw_stores, enrich_results):
            if isinstance(res, dict):
                st.email = res.get("email")
                st.email_source_url = res.get("email_source_url")
                st.email_confidence = res.get("email_confidence", "NONE")

    with_contact_count = sum(1 for s in raw_stores if s.email or s.phone or len(s.sns_urls) > 0)

    return raw_stores, total_found, without_website_count, with_contact_count
