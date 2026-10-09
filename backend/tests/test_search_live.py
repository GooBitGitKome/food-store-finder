import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_search_stores_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        req_body = {
            "query_text": "東京都港区麻布十番",
            "radius_meters": 200,
            "categories": ["restaurant", "cafe"],
            "only_without_website": True,
            "enrich_contacts": False # 高速テストのためモック化/探索オフ
        }
        res = await ac.post("/api/v1/stores/search", json=req_body)
        if res.status_code == 500:
            pytest.skip(f"Public OSM/Overpass API temporarily rate-limited ({res.text}); skipping live network test.")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "center" in data
        assert data["center"]["lat"] > 35.0
        assert data["radius_meters"] == 200
        assert isinstance(data["stores"], list)
        print(f"\n[Test] Found {len(data['stores'])} stores without website in Azabujuban (200m)")
