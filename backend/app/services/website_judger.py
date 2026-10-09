import urllib.parse
from typing import Tuple, List, Dict, Optional

# 一般的なグルメポータルおよび口コミサイト・デリバリー・地図
PORTAL_DOMAINS = [
    "tabelog.com",
    "gnavi.co.jp",
    "hotpepper.jp",
    "retty.me",
    "hitosara.com",
    "ubereats.com",
    "demae-can.com",
    "tripadvisor.jp",
    "tripadvisor.com",
    "ekiten.jp",
    "itp.ne.jp",       # タウンページ
    "navitime.co.jp",
    "mapion.co.jp",
    "google.com",
    "google.co.jp",
    "maps.google.com",
    "foursquare.com",
    "yelp.com",
    "loco.yahoo.co.jp",
    "dancyu.jp",
    "sarah30.com",
    "chouseisan.com"
]

# SNSプラットフォーム
SNS_DOMAINS = [
    "instagram.com",
    "facebook.com",
    "fb.com",
    "twitter.com",
    "x.com",
    "line.me",
    "page.line.me",
    "tiktok.com",
    "threads.net"
]

# 公式Webサイトを保有する著名な大手飲食チェーン・コンビニ・ブランド
# (OSMで個別のwebsiteタグが抜けていても大手チェーンは除外対象とする)
KNOWN_CHAIN_KEYWORDS = [
    "マクドナルド", "mcdonald", "スターバックス", "starbucks", "ドミノ・ピザ", "ドミノピザ", "domino",
    "ピザハット", "pizzahut", "ケンタッキー", "kfc", "サブウェイ", "subway",
    "吉野家", "すき家", "松屋", "なか卯", "かつや", "からやま",
    "モスバーガー", "mos burger", "ロッテリア", "lotteria", "フレッシュネスバーガー",
    "サイゼリヤ", "ガスト", "バーミヤン", "ジョナサン", "デニーズ", "denny's", "ロイヤルホスト",
    "大戸屋", "やよい軒", "CoCo壱番屋", "coco壱", "日高屋", "幸楽苑", "一蘭", "一風堂",
    "丸亀製麺", "はなまるうどん", "スシロー", "くら寿司", "はま寿司", "かっぱ寿司",
    "ドトール", "doutor", "タリーズ", "tully", "サンマルク", "saint marc", "コメダ珈琲", "komeda",
    "エクセルシオール", "プロント", "pronto", "星乃珈琲", "上島珈琲", "ミスタードーナツ", "mister donut",
    "サーティワン", "baskin", "銀だこ", "築地銀だこ", "リンガーハット", "ringer hut",
    "餃子の王将", "大阪王将", "牛角", "安楽亭", "温野菜", "しゃぶ葉", "しゃぶしゃぶ温野菜",
    "鳥貴族", "塚田農場", "庄や", "魚民", "白木屋", "笑笑", "千年の宴", "養老乃瀧", "hub",
    "セブン-イレブン", "セブンイレブン", "ファミリーマート", "ローソン", "ミニストップ", "デイリーヤマザキ",
    "まいばすけっと", "成城石井", "カルディ", "kaldi"
]

def extract_domain(url: str) -> str:
    """URLからドメイン部分（小文字、ポート・www除去）を抽出する"""
    if not url:
        return ""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        if ":" in netloc:
            netloc = netloc.split(":")[0]
        return netloc
    except Exception:
        return ""

def is_known_chain(tags: Dict[str, str]) -> bool:
    """Wikidataタグやブランド・店舗名から大手チェーン店かどうかを判定"""
    # 1. Wikidata / Wikipedia タグ（著名企業・ブランドの証）
    wikidata_keys = ["brand:wikidata", "operator:wikidata", "brand:wikipedia", "operator:wikipedia"]
    if any(k in tags and tags[k].strip() for k in wikidata_keys):
        return True

    # 2. ブランド名・店舗名でのシグネチャ照合
    name = (tags.get("name") or "").lower()
    brand = (tags.get("brand") or tags.get("brand:ja") or tags.get("brand:en") or "").lower()
    operator = (tags.get("operator") or "").lower()

    text_to_check = f"{name} {brand} {operator}"
    for kw in KNOWN_CHAIN_KEYWORDS:
        if kw.lower() in text_to_check:
            return True

    return False

def judge_website_status(tags: Dict[str, str]) -> Tuple[bool, Optional[str], List[str], List[str]]:
    """
    OSMのタグ群から自前Webサイトの有無を判定する。
    戻り値: (has_own_website: bool, primary_url: Optional[str], portal_urls: List[str], sns_urls: List[str])
    """
    portal_urls: List[str] = []
    sns_urls: List[str] = []
    candidate_urls: List[str] = []

    # 1. tagsからURL候補を網羅的に収集
    url_keys = [
        "website", "contact:website", "url", "website:ja", "website:en",
        "url:official", "contact:url", "contact:web", "brand:website", "operator:website"
    ]
    for k in url_keys:
        if k in tags and tags[k]:
            val = tags[k].strip()
            if val and val not in candidate_urls:
                candidate_urls.append(val)

    # SNS個別タグの収集
    if "contact:instagram" in tags:
        ig_val = tags["contact:instagram"].strip()
        ig_url = ig_val if ig_val.startswith("http") else f"https://www.instagram.com/{ig_val.lstrip('@')}/"
        sns_urls.append(ig_url)
    if "contact:facebook" in tags:
        fb_val = tags["contact:facebook"].strip()
        fb_url = fb_val if fb_val.startswith("http") else f"https://www.facebook.com/{fb_val}"
        sns_urls.append(fb_url)
    if "contact:twitter" in tags or "contact:x" in tags:
        x_val = (tags.get("contact:twitter") or tags.get("contact:x", "")).strip()
        x_url = x_val if x_val.startswith("http") else f"https://x.com/{x_val.lstrip('@')}"
        sns_urls.append(x_url)
    if "contact:line" in tags:
        line_val = tags["contact:line"].strip()
        line_url = line_val if line_val.startswith("http") else f"https://line.me/R/ti/p/{line_val}"
        sns_urls.append(line_url)

    # 2. 大手チェーン店判定 (URLタグが欠損していても公式HPありと判定)
    if is_known_chain(tags):
        primary = candidate_urls[0] if candidate_urls else "https://chain-brand.detected/"
        return True, primary, portal_urls, list(dict.fromkeys(sns_urls))

    if not candidate_urls:
        # 登録URL自体が存在せず、チェーン店でもない -> 自前HPなし
        return False, None, portal_urls, list(dict.fromkeys(sns_urls))

    primary_url = candidate_urls[0]
    domain = extract_domain(primary_url)

    # 3. ドメイン判定
    is_portal = any(p_domain in domain for p_domain in PORTAL_DOMAINS)
    is_sns = any(s_domain in domain for s_domain in SNS_DOMAINS)

    if is_portal:
        portal_urls.append(primary_url)
        return False, primary_url, list(dict.fromkeys(portal_urls)), list(dict.fromkeys(sns_urls))
    elif is_sns:
        sns_urls.append(primary_url)
        return False, primary_url, list(dict.fromkeys(portal_urls)), list(dict.fromkeys(sns_urls))
    else:
        # 独自ドメインと推定 -> 自前HPあり
        return True, primary_url, list(dict.fromkeys(portal_urls)), list(dict.fromkeys(sns_urls))
