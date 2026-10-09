from fastapi import APIRouter, HTTPException, Query, Response
from typing import List, Optional
from app.models.store import SearchRequest, SearchResponse, SearchCenter, GeocodeResponse, StoreModel
from app.services.geo import resolve_address
from app.services.store_discovery import discover_stores
from app.services.csv_export import generate_stores_csv

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "food-store-finder-api"}

@router.get("/stores/geocode", response_model=GeocodeResponse)
async def geocode(query: str = Query(..., description="地名または住所")):
    res = await resolve_address(query)
    if not res:
        raise HTTPException(status_code=404, detail=f"住所 '{query}' を特定できませんでした。")
    lat, lon, display_name = res
    return GeocodeResponse(query=query, lat=lat, lon=lon, display_name=display_name)

from app.services.overture_discovery import discover_stores_overture

@router.post("/stores/search", response_model=SearchResponse)
async def search_stores(req: SearchRequest):
    lat = req.lat
    lon = req.lon
    display_name = req.query_text or "指定地点"

    # 地名指定がある場合、座標が未設定ならジオコーディング
    if (lat is None or lon is None) and req.query_text:
        res = await resolve_address(req.query_text)
        if not res:
            raise HTTPException(status_code=404, detail=f"指定された地名 '{req.query_text}' が見つかりませんでした。")
        lat, lon, display_name = res
    elif lat is None or lon is None:
        raise HTTPException(status_code=400, detail="地名(query_text)または中心座標(lat, lon)のいずれかを指定してください。")

    used_source = req.data_source or "overture"
    try:
        if used_source == "overture":
            try:
                stores, total, without_web, with_contact = await discover_stores_overture(
                    lat=lat,
                    lon=lon,
                    radius_meters=req.radius_meters,
                    categories=req.categories,
                    only_without_website=req.only_without_website,
                    enrich_contacts=req.enrich_contacts
                )
            except Exception as overture_err:
                print(f"[Warning] Overture Maps query failed ({overture_err}); falling back to OSM...")
                stores, total, without_web, with_contact = await discover_stores(
                    lat=lat,
                    lon=lon,
                    radius_meters=req.radius_meters,
                    categories=req.categories,
                    only_without_website=req.only_without_website,
                    enrich_contacts=req.enrich_contacts
                )
                used_source = "osm (fallback)"
        else:
            stores, total, without_web, with_contact = await discover_stores(
                lat=lat,
                lon=lon,
                radius_meters=req.radius_meters,
                categories=req.categories,
                only_without_website=req.only_without_website,
                enrich_contacts=req.enrich_contacts
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"店舗データ取得中にエラーが発生しました: {str(e)}")

    return SearchResponse(
        status="success",
        data_source=used_source,
        center=SearchCenter(lat=lat, lon=lon, display_name=display_name),
        radius_meters=req.radius_meters,
        total_found=total,
        without_website_count=without_web,
        with_contact_count=with_contact,
        stores=stores
    )

@router.post("/stores/export-csv")
async def export_csv(stores: List[StoreModel]):
    """店舗リストを受け取り、即時ダウンロード用のCSVを返す"""
    csv_content = generate_stores_csv(stores)
    return Response(
        content=csv_content.encode('utf-8'),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="food_stores_without_website.csv"'
        }
    )
