import re
import urllib.parse
from typing import Optional, Tuple, List, Dict
import httpx
from bs4 import BeautifulSoup
from app.core.config import settings

# 有効なメールアドレスの抽出パターン
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

# 除外すべきドメイン・キーワード（ポータルやシステムメール、画像拡張子の誤認識など）
EXCLUDED_EMAIL_DOMAINS = [
    "tabelog.com", "gnavi.co.jp", "hotpepper.jp", "retty.me",
    "ubereats.com", "demae-can.com", "tripadvisor.jp", "tripadvisor.com",
    "google.com", "google.co.jp", "yahoo.co.jp", "apple.com",
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "w3.org", "sentry.io", "example.com", "schema.org"
]

EXCLUDED_LOCAL_PARTS = [
    "noreply", "no-reply", "mailer-daemon", "postmaster",
    "admin", "support", "contact-form", "privacy"
]

EXCLUDED_EXTENSIONS = [
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js"
]

def clean_email(email_str: str) -> Optional[str]:
    """メールアドレスをクレンジングし、除外ルールに合致しないか判定する"""
    if not email_str:
        return None
    email_str = email_str.strip().lower()
    
    # 拡張子の誤検知除外 (例: icon.png@2x)
    for ext in EXCLUDED_EXTENSIONS:
        if ext in email_str:
            return None
            
    if "@" not in email_str:
        return None
        
    local_part, domain = email_str.split("@", 1)
    
    # ドメインチェック
    for d in EXCLUDED_EMAIL_DOMAINS:
        if domain == d or domain.endswith("." + d):
            return None
            
    # ローカルパートチェック
    for l in EXCLUDED_LOCAL_PARTS:
        if local_part == l:
            return None
            
    return email_str

async def search_email_online(store_name: str, area_hint: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    店舗名とエリアを元に公開Web探索を行い、メールアドレスを発掘する
    戻り値: (email, source_url, confidence)
    """
    if not store_name:
        return None, None, "NONE"

    # DuckDuckGo HTML検索用クエリ (例: "炭火焼肉 たろう" "港区" email OR mail OR "@")
    query = f'"{store_name}" "{area_hint}" (email OR mail OR "@")'
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # 検索スニペットとリンクを解析
                results = soup.select(".result")
                for res in results[:5]:
                    snippet_elem = res.select_one(".result__snippet")
                    url_elem = res.select_one(".result__url")
                    snippet = snippet_elem.get_text() if snippet_elem else ""
                    source_url = url_elem.get_text().strip() if url_elem else ""

                    # メールアドレスの抽出
                    matches = EMAIL_REGEX.findall(snippet)
                    for m in matches:
                        valid = clean_email(m)
                        if valid:
                            return valid, ("https://" + source_url if not source_url.startswith("http") else source_url), "HIGH"
    except Exception as e:
        print(f"[ContactMiner] Online search error for {store_name}: {e}")

    return None, None, "NONE"

async def enrich_store_contacts(
    name: str,
    address: str,
    tags: Dict[str, str],
    allow_online_search: bool = True
) -> Dict[str, Optional[str]]:
    """
    OSMタグおよびオンライン探索を統合し、連絡先情報を最大限補完する
    """
    # 1. OSMタグ内の直接記載メール
    tag_email = tags.get("email") or tags.get("contact:email")
    if tag_email:
        cleaned = clean_email(tag_email)
        if cleaned:
            return {
                "email": cleaned,
                "email_source_url": "OpenStreetMap Tags",
                "email_confidence": "HIGH"
            }

    # 2. オンライン探索
    if allow_online_search and name and name != "名称未設定":
        email, source_url, confidence = await search_email_online(name, address)
        if email:
            return {
                "email": email,
                "email_source_url": source_url,
                "email_confidence": confidence
            }

    return {
        "email": None,
        "email_source_url": None,
        "email_confidence": "NONE"
    }
