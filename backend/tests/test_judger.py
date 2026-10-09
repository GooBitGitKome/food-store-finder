import pytest
from app.services.website_judger import judge_website_status, extract_domain

def test_extract_domain():
    assert extract_domain("https://tabelog.com/tokyo/A1303/A130301/13000001/") == "tabelog.com"
    assert extract_domain("http://www.instagram.com/my_restaurant") == "instagram.com"
    assert extract_domain("my-restaurant.jp:8080/home") == "my-restaurant.jp"
    assert extract_domain("") == ""

def test_judge_no_website():
    tags = {
        "name": "居酒屋 たぬき",
        "amenity": "pub"
    }
    has_own, primary, portals, sns = judge_website_status(tags)
    assert has_own is False
    assert primary is None
    assert portals == []
    assert sns == []

def test_judge_portal_only():
    tags = {
        "name": "炭火焼 太郎",
        "website": "https://tabelog.com/tokyo/A1303/A130301/13012345/"
    }
    has_own, primary, portals, sns = judge_website_status(tags)
    assert has_own is False
    assert primary == "https://tabelog.com/tokyo/A1303/A130301/13012345/"
    assert "https://tabelog.com/tokyo/A1303/A130301/13012345/" in portals

def test_judge_sns_only():
    tags = {
        "name": "路地裏カフェ",
        "website": "https://www.instagram.com/rojiura_cafe/",
        "contact:facebook": "rojiuracafe"
    }
    has_own, primary, portals, sns = judge_website_status(tags)
    assert has_own is False
    assert "https://www.instagram.com/rojiura_cafe/" in sns
    assert any("facebook.com" in s for s in sns)

def test_judge_own_domain():
    tags = {
        "name": "本格割烹 まつもと",
        "website": "https://kappo-matsumoto.tokyo/about"
    }
    has_own, primary, portals, sns = judge_website_status(tags)
    assert has_own is True
    assert primary == "https://kappo-matsumoto.tokyo/about"
    assert portals == []

def test_judge_chain_brand():
    # websiteタグが無くても大手チェーンはHPありと判定される
    tags = {
        "name": "マクドナルド 麻布十番店",
        "amenity": "fast_food"
    }
    has_own, primary, portals, sns = judge_website_status(tags)
    assert has_own is True

def test_judge_wikidata_chain():
    tags = {
        "name": "カフェ・ローカル",
        "brand:wikidata": "Q123456"
    }
    has_own, primary, portals, sns = judge_website_status(tags)
    assert has_own is True

def test_is_public_building_and_genre():
    from app.services.store_discovery import is_public_building, determine_genre

    # amenity=public_building
    tags_public = {"amenity": "public_building", "name": "麻布区民センター"}
    assert is_public_building(tags_public) is True
    assert determine_genre(tags_public) == "public_building"

    # building=public
    tags_building = {"building": "public", "amenity": "restaurant", "name": "市役所食堂"}
    assert is_public_building(tags_building) is True
    assert determine_genre(tags_building) == "public_building"

    # office=government
    tags_gov = {"office": "government", "name": "出張所"}
    assert is_public_building(tags_gov) is True
    assert determine_genre(tags_gov) == "public_building"

    # 通常のレストラン
    tags_normal = {"amenity": "restaurant", "name": "純喫茶・定食屋"}
    assert is_public_building(tags_normal) is False
    assert determine_genre(tags_normal) == "restaurant"

