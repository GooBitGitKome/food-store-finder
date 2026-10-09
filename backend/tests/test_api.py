import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"

@pytest.mark.asyncio
async def test_export_csv_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        sample_stores = [
            {
                "id": "node_999",
                "name": "テストカフェ",
                "category": "カフェ",
                "lat": 35.6895,
                "lon": 139.6917,
                "address": "東京都新宿区西新宿1-1",
                "phone": "03-9999-9999",
                "has_own_website": False,
                "raw_website": None,
                "portal_urls": [],
                "sns_urls": [],
                "email": "cafe@test.jp",
                "email_source_url": "https://test.jp",
                "email_confidence": "HIGH",
                "additional_info": {}
            }
        ]
        res = await ac.post("/api/v1/stores/export-csv", json=sample_stores)
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]
        text = res.content.decode("utf-8")
        assert "テストカフェ" in text
        assert "cafe@test.jp" in text

def test_search_request_radius_100km():
    from app.models.store import SearchRequest
    # 100km (100,000m) がバリデーションエラーなく受理されることを検証
    req = SearchRequest(lat=35.0, lon=139.0, radius_meters=100000)
    assert req.radius_meters == 100000

