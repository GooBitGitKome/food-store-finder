import httpx
from typing import Optional, Tuple
from app.core.config import settings

async def resolve_address(query: str) -> Optional[Tuple[float, float, str]]:
    """
    Nominatim APIを利用して地名・住所から緯度、経度、表示住所文字列を解決する
    """
    if not query or not query.strip():
        return None
        
    url = settings.NOMINATIM_API_URL
    params = {
        "q": query.strip(),
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": settings.USER_AGENT
    }
    
    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
        try:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    first = data[0]
                    lat = float(first["lat"])
                    lon = float(first["lon"])
                    display_name = first.get("display_name", query)
                    return lat, lon, display_name
        except Exception as e:
            # エラー時はNoneを返し呼び出し元でフォールバック
            print(f"[GeoService] Nominatim resolution error for '{query}': {e}")
            
    return None
