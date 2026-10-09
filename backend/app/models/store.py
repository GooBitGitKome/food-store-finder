from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class StoreModel(BaseModel):
    id: str = Field(description="店舗識別子 (OSM ID等)")
    name: str = Field(description="店舗名")
    category: str = Field(default="飲食店", description="業態カテゴリ")
    lat: float = Field(description="緯度")
    lon: float = Field(description="経度")
    address: str = Field(default="", description="住所")
    phone: Optional[str] = Field(default=None, description="電話番号")
    has_own_website: bool = Field(default=False, description="自前公式HP保有フラグ")
    raw_website: Optional[str] = Field(default=None, description="登録元URL")
    portal_urls: List[str] = Field(default_factory=list, description="確認されたポータルURL")
    sns_urls: List[str] = Field(default_factory=list, description="確認されたSNSリンク")
    email: Optional[str] = Field(default=None, description="検出されたメールアドレス")
    email_source_url: Optional[str] = Field(default=None, description="メール取得元URL")
    email_confidence: Optional[str] = Field(default="NONE", description="信頼度: HIGH/MEDIUM/LOW/NONE")
    genre: Optional[str] = Field(default="restaurant", description="大分類ジャンル (restaurant/cafe/food等)")
    google_maps_url: Optional[str] = Field(default=None, description="Google Maps詳細・検索URL")
    additional_info: Dict[str, Any] = Field(default_factory=dict, description="補足情報(営業時間等)")

class SearchRequest(BaseModel):
    query_text: Optional[str] = Field(default=None, description="地名または住所 (例: 東京都港区麻布十番)")
    lat: Optional[float] = Field(default=None, description="中心緯度")
    lon: Optional[float] = Field(default=None, description="中心経度")
    radius_meters: int = Field(default=500, ge=100, le=100000, description="検索半径(メートル: 100〜100000)")
    categories: List[str] = Field(default=["restaurant", "cafe", "food"], description="検索カテゴリ")
    only_without_website: bool = Field(default=True, description="自前HPなし店舗のみを抽出")
    enrich_contacts: bool = Field(default=True, description="ハイブリッドメール・SNS深層探索を実行")
    data_source: Optional[str] = Field(default="overture", description="データソース (overture / osm)")

class SearchCenter(BaseModel):
    lat: float
    lon: float
    display_name: str

class SearchResponse(BaseModel):
    status: str = "success"
    data_source: str = "overture"
    center: SearchCenter
    radius_meters: int
    total_found: int
    without_website_count: int
    with_contact_count: int
    stores: List[StoreModel]

class GeocodeResponse(BaseModel):
    query: str
    lat: float
    lon: float
    display_name: str
