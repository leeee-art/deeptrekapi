from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import re
import socket
import csv
import io
import whois
import dns.resolver
import base64
from datetime import datetime
from typing import Tuple, Optional
from urllib.parse import unquote, quote

app = Flask(__name__)
CORS(app)

MASTER_KEY = 'deeptrek_fjnrndhfrb2947472992gdvsbdh'

# ==================== DEPSEARCH ====================
DEPSEARCH_URL   = "https://api.depsearch.sbs"
DEPSEARCH_TOKEN = "py6cpozEd9XYNZaDvsUqu0sYMtCPb5hQ"

# ==================== GLOOM (заменяет BigBase + DepSearch) ====================
GLOOM_URL = "https://gloomapi.bothost.tech/search"
GLOOM_TOKEN = "plut_kCYREkorsBmPb7xoW4pEws2Thw8qHU0L0wxgo4xTPzs"

# ==================== INFINITY ====================
INFINITY_TOKEN_1 = 'Bjm928HUcvsw923ZMBX19gd110FWSZgd'
INFINITY_TOKEN_2 = 'QoNm98UeMLIqNjZ198snm98AdGvhqA88'
INFINITY_URL = 'https://infinity-search.fun/find.php'

# ==================== WHITE SEARCH ====================
WHITESEARCH_KEY = 'WS-PUBLIC-9X7K-2M4P'
WHITESEARCH_URL = 'https://api.whitesearch.workers.dev/api'

# ==================== JITLER ====================
JITLER_TOKEN = 'n7C9rwJgka8uREoMusjSx52L'
JITLER_URL = 'https://api.jitler.top/search'

# ==================== NIGHT SEARCH ====================
NIGHTSEARCH_KEY = 'sk_adf1c3969235df867481065a015ad3aba4217251ec50dace7efaff645c1ac005'
NIGHTSEARCH_URL = 'https://nightsearch.life/api/search'

# ==================== HUNTER.HOW ====================
HUNTERHOW_API_KEY = 'd43597d5bc6033a21ba389e034080628fe2ecffd'
HUNTERHOW_URL = 'https://api.hunter.how/search'

# ==================== HUNTER.IO ====================
HUNTER_API_KEY = 'd43597d5bc6033a21ba389e034080628fe2ecffd'
HUNTER_URL = 'https://api.hunter.io/v2'

# ==================== NUMVERIFY ====================
NUMVERIFY_API_KEY = '45b6ab2f9ee0cf8acb0880d5dfe5ec5c'
NUMVERIFY_URL = 'http://apilayer.net/api/validate'

# ==================== LEAKCHECK ====================
LEAKCHECK_KEY = 'd36864926b6e998846d9eb9499e0f2e6546a9541'
LEAKCHECK_URL = 'https://leakcheck.io/api/v2/query'

# ==================== SNUSBASE ====================
SNUSBASE_KEY = 'sb5029dec66mht55m78fx8bsw6tm8a'
SNUSBASE_URL = 'https://api.snusbase.com/v3/search'

# ==================== VERIPHONE ====================
VERIPHONE_KEY = 'A9A2A88762854D45888BA49E8F98509C'
VERIPHONE_URL = 'https://api.veriphone.io/v2/verify'

# ==================== IPGEO ====================
IPGEO_KEY = '73d99145d2e948779263360bfeb67ecc'
IPGEO_URL = 'https://api.ipgeolocation.io/ipgeo'

# ==================== OFDATA ====================
OFDATA_KEY = 'KBnpz1CHKNngFXxK'
OFDATA_URL = 'https://api.ofdata.ru/v2/search'

# ==================== OMKAR ====================
OMKAR_API_KEY = 'ok_ad50fb80682eff950d34e7a9b3a77c8c'

# ==================== VK ====================
VK_TOKEN = 'vk1.a.WX465fcyCl3FoFXysIyBPjQYn4D4Cgz3SJAmX7mxXvQBMUzTjzkaZfA0Tt-FBRDuA4WYq7tvbO3TaqZbvdl3oAva367V8KP4AQUFI1kC3I8UnT687rM12Bv-d-Ax9FnXAeOTxMp8MTBUwqQ_6kH-1LAQIT7fgdzWaawG3CEOhe6Q5VSuzTrDFF0iWIrUAXIwT22_uN6XzH25tZCegI-AWQ'

# ==================== INTELX ====================
INTELX_API_KEY = '9df816e5-f2a1-4b3c-8d7e-6f5a4b3c2d1e'
INTELX_HOST = '2.intelx.io'

infinity_tokens = [INFINITY_TOKEN_1, INFINITY_TOKEN_2]
infinity_idx = 0

def get_infinity_token():
    global infinity_idx
    token = infinity_tokens[infinity_idx]
    infinity_idx = (infinity_idx + 1) % len(infinity_tokens)
    return token

# ==================== DEPSEARCH ====================
def search_depsearch(query, search_type):
    type_map = {
        "phone":    "phone",
        "email":    "email",
        "fio":      "fio",
        "vk":       "vk",
        "vkid":     "vk",
        "tiktok":   "tiktok",
        "ip":       "ip",
        "snils":    "snils",
        "inn":      "inn",
        "addr":     "addr",
        "username": "nick",
        "nick":     "nick",
        "pass":     "pass",
        "auto":     "auto",
        "vin":      "vin",
    }
    if search_type not in type_map:
        return {"source": "depsearch", "error": f"Тип {search_type} не поддерживается"}

    enc = quote(query, safe=":")
    candidates = [
        f"/quest={enc}&token={DEPSEARCH_TOKEN}&lang=ru",
        f"/?quest={enc}&token={DEPSEARCH_TOKEN}&lang=ru",
        f"/search?quest={enc}&token={DEPSEARCH_TOKEN}&lang=ru",
    ]
    last_err = None
    for path in candidates:
        try:
            r = requests.get(
                DEPSEARCH_URL + path,
                timeout=60,
                headers={"User-Agent": "DeepTrek/26.0"},
            )
            if r.status_code == 404:
                continue
            if r.status_code == 200:
                try:
                    data = r.json()
                except Exception:
                    return {"source": "depsearch",
                            "error": f"Не JSON: {r.text[:120]}"}
                if (not data.get("results")
                        and not data.get("phone_info")
                        and not data.get("ip_info")):
                    return {"source": "depsearch", "error": "Ничего не найдено"}
                return {"source": "depsearch", "data": data}
            if r.status_code == 429:
                return {"source": "depsearch", "error": "Лимит запросов"}
            if r.status_code in (401, 403):
                return {"source": "depsearch", "error": "Токен недействителен"}
            return {"source": "depsearch", "error": f"HTTP {r.status_code}"}
        except Exception as e:
            last_err = e
    return {"source": "depsearch",
            "error": str(last_err) if last_err else "Нет рабочего endpoint"}

# ==================== GLOOM ====================
def search_gloom(query, search_type):
    type_map = {
        "phone": "phone", "email": "email", "fio": "fio", "vk": "vk",
        "telegram": "telegram", "telegram_id": "telegram",
        "telegram_username": "telegram", "username": "username",
        "ip": "ip", "passport": "passport", "inn": "inn",
        "snils": "snils", "card": "card",
    }
    if search_type not in type_map:
        return {"source": "gloom", "error": f"Тип {search_type} не поддерживается"}
    try:
        headers = {
            "Authorization": f"Bearer {GLOOM_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {type_map[search_type]: query}
        r = requests.post(GLOOM_URL, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            if not data.get("success"):
                return {"source": "gloom", "error": "Ничего не найдено"}
            return {"source": "gloom", "data": data}
        elif r.status_code == 401:
            return {"source": "gloom", "error": "Неверный токен"}
        elif r.status_code == 422:
            return {"source": "gloom", "error": "Формат запроса неверен"}
        elif r.status_code == 429:
            return {"source": "gloom", "error": "Лимит запросов"}
        else:
            return {"source": "gloom", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "gloom", "error": str(e)}

# ==================== INFINITY ====================
def search_infinity(query, search_type):
    token = get_infinity_token()
    if search_type not in ["phone", "email", "fio"]:
        return {"source": "infinity", "error": "Тип не поддерживается"}
    try:
        params = {"token": token, search_type: query}
        r = requests.get(INFINITY_URL, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data.get("results"):
                return {"source": "infinity",
                        "data": {"total": len(data["results"]),
                                 "results": data["results"][:20]}}
            return {"source": "infinity", "error": "Ничего не найдено"}
        return {"source": "infinity", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "infinity", "error": str(e)}

# ==================== WHITE SEARCH ====================
def search_white_search(query, search_type):
    type_map = {
        "phone": "/search/phone", "email": "/search/email",
        "telegram": "/search/telegram", "telegram_id": "/search/telegram",
        "telegram_username": "/search/telegram", "vk": "/search/vk",
        "fio": "/search/fio", "ip": "/search/ip", "snils": "/search/snils",
        "inn": "/search/inn", "passport": "/search/passport",
        "auto": "/search/grz", "vin": "/search/vin"
    }
    if search_type not in type_map:
        return {"source": "white_search", "error": f"Тип {search_type} не поддерживается"}
    try:
        endpoint = type_map[search_type]
        url = f"{WHITESEARCH_URL}{endpoint}"
        headers = {"X-API-Key": WHITESEARCH_KEY}
        if search_type in ["phone", "email", "fio", "ip", "snils", "inn", "passport"]:
            params = {search_type: query}
        elif search_type in ["telegram", "telegram_id", "telegram_username"]:
            params = {"id": query}
        elif search_type == "vk":
            params = {"id": query}
        elif search_type == "auto":
            params = {"grz": query}
        elif search_type == "vin":
            params = {"vin": query}
        else:
            params = {"q": query}
        r = requests.get(url, params=params, headers=headers, timeout=60)
        if r.status_code == 200:
            data = r.json()
            if data.get("success") and data.get("data"):
                results_data = data.get("data", [])
                if isinstance(results_data, dict) and results_data.get("message") == "Not found":
                    return {"source": "white_search", "error": "Ничего не найдено"}
                return {"source": "white_search",
                        "data": {
                            "total": len(results_data) if isinstance(results_data, list) else 1,
                            "results": results_data if isinstance(results_data, list) else [results_data]
                        }}
            return {"source": "white_search", "error": "Ничего не найдено"}
        elif r.status_code == 429:
            return {"source": "white_search", "error": "Дневной лимит исчерпан"}
        return {"source": "white_search", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "white_search", "error": str(e)}

# ==================== JITLER ====================
def search_jitler(query, search_type):
    if search_type not in ["phone", "telegram", "telegram_id", "telegram_username", "vk"]:
        return {"source": "jitler", "error": "Jitler поддерживает только phone, telegram, vk"}
    type_map = {"phone": "number", "telegram": "sherlock",
                "telegram_id": "sherlock", "telegram_username": "sherlock", "vk": "vks"}
    try:
        headers = {"Authorization": f"Bearer {JITLER_TOKEN}",
                   "Content-Type": "application/json"}
        payload = {"type": type_map[search_type], "query": query, "page": 1}
        r = requests.post(JITLER_URL, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            return {"source": "jitler", "data": data.get("response", {})}
        return {"source": "jitler", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "jitler", "error": str(e)}

# ==================== NIGHT SEARCH ====================
def search_nightsearch(query, search_type):
    type_map = {
        "phone": "phone", "email": "email", "fio": "fio",
        "passport": "passport", "inn": "inn", "snils": "snils",
        "vk": "vk", "telegram": "telegram", "telegram_id": "telegram",
        "telegram_username": "telegram", "auto": "auto", "vin": "vin",
        "ip": "ip", "ogrn": "ogrn", "username": "username",
        "domain": "domain", "card": "card", "bank": "card",
    }
    if search_type not in type_map:
        return {"source": "nightsearch", "error": f"Night Search не поддерживает тип {search_type}"}
    try:
        headers = {"X-API-Key": NIGHTSEARCH_KEY,
                   "Content-Type": "application/json; charset=utf-8"}
        if search_type == "phone":
            query = re.sub(r'\D', '', query)
        payload = {"query": query, "search_type": type_map[search_type]}
        r = requests.post(NIGHTSEARCH_URL, headers=headers, json=payload, timeout=120)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if not results:
                return {"source": "nightsearch", "error": "Ничего не найдено"}
            return {"source": "nightsearch", "data": {"total": len(results), "results": results}}
        elif r.status_code == 500:
            return {"source": "nightsearch", "error": "Night Search внутренняя ошибка (500)"}
        elif r.status_code == 401:
            return {"source": "nightsearch", "error": "Неверный API ключ"}
        elif r.status_code == 429:
            return {"source": "nightsearch", "error": "Лимит запросов исчерпан"}
        else:
            return {"source": "nightsearch", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "nightsearch", "error": str(e)}

# ==================== HUNTER.HOW ====================
def search_hunterhow(query, search_type):
    if search_type not in ["ip", "domain"]:
        return {"source": "hunterhow", "error": "Hunter.how поддерживает ip, domain"}
    try:
        q = f'ip="{query}"' if search_type == "ip" else f'domain="{query}"'
        encoded_query = base64.urlsafe_b64encode(q.encode("utf-8")).decode('ascii')
        params = {
            "api-key": HUNTERHOW_API_KEY,
            "query": encoded_query, "page": 1, "page_size": 10,
            "start_time": "2024-01-01", "end_time": "2026-12-31",
            "fields": "ip,port,domain,protocol,transport_protocol,web_title,country,province,city,url,asn,as_org,as_name,status_code,cert,os,header,header_server,banner,product,updated_at,body"
        }
        r = requests.get(HUNTERHOW_URL, params=params, timeout=60)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 200:
                results = data.get("data", {})
                items = results.get("list", [])
                return {"source": "hunterhow",
                        "data": {"total": results.get("total", len(items)),
                                 "results": items[:20]}}
            return {"source": "hunterhow", "error": data.get("message", "Ошибка")}
        elif r.status_code == 401:
            return {"source": "hunterhow", "error": "Неверный API ключ"}
        elif r.status_code == 429:
            return {"source": "hunterhow", "error": "Лимит запросов"}
        return {"source": "hunterhow", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "hunterhow", "error": str(e)}

# ==================== HUNTER.IO ====================
def search_hunter(query, search_type):
    if search_type not in ["domain", "company", "email"]:
        return {"source": "hunter", "error": "Hunter поддерживает domain, company, email"}
    try:
        if search_type == "domain":
            params = {"domain": query, "api_key": HUNTER_API_KEY, "limit": 50}
            r = requests.get(f"{HUNTER_URL}/domain-search", params=params, timeout=60)
            if r.status_code == 200:
                data = r.json()
                emails = data.get("data", {}).get("emails", [])
                return {"source": "hunter",
                        "data": {
                            "domain": query,
                            "total_emails": len(emails),
                            "emails": [{
                                "email": e.get("value"), "type": e.get("type"),
                                "first_name": e.get("first_name"),
                                "last_name": e.get("last_name"),
                                "position": e.get("position"),
                                "department": e.get("department"),
                                "confidence": e.get("confidence")
                            } for e in emails[:20]]
                        }}
        elif search_type == "email":
            params = {"email": query, "api_key": HUNTER_API_KEY}
            r = requests.get(f"{HUNTER_URL}/email-verifier", params=params, timeout=60)
            if r.status_code == 200:
                data = r.json()
                return {"source": "hunter", "data": data.get("data", {})}
        return {"source": "hunter", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "hunter", "error": str(e)}

# ==================== NUMVERIFY ====================
def search_numverify(phone):
    try:
        phone_clean = re.sub(r'\D', '', phone)
        params = {"access_key": NUMVERIFY_API_KEY, "number": phone_clean, "format": 1}
        r = requests.get(NUMVERIFY_URL, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data.get("valid"):
                return {"source": "numverify",
                        "data": {"valid": data.get("valid"),
                                 "number": data.get("international_format"),
                                 "local_format": data.get("local_format"),
                                 "country": data.get("country_name"),
                                 "country_code": data.get("country_code"),
                                 "location": data.get("location"),
                                 "carrier": data.get("carrier"),
                                 "line_type": data.get("line_type")}}
            return {"source": "numverify", "error": "Номер невалиден"}
        return {"source": "numverify", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "numverify", "error": str(e)}

# ==================== LEAKCHECK ====================
def search_leakcheck(query, search_type="email"):
    try:
        r = requests.get(LEAKCHECK_URL,
                         params={"key": LEAKCHECK_KEY, "check": query},
                         timeout=30)
        if r.status_code == 200:
            return {"source": "leakcheck", "data": r.json()}
        return {"source": "leakcheck", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "leakcheck", "error": str(e)}

# ==================== SNUSBASE ====================
def search_snusbase(query, search_type):
    if search_type not in ["email", "fio", "ip"]:
        return {"source": "snusbase", "error": "Тип не поддерживается"}
    try:
        snus_type = "ip" if search_type == "ip" else search_type
        if search_type == "fio":
            snus_type = "username"
        payload = {"terms": [query], "types": [snus_type], "wildcard": False}
        headers = {"Auth": SNUSBASE_KEY, "Content-Type": "application/json"}
        r = requests.post(SNUSBASE_URL, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            return {"source": "snusbase", "data": r.json()}
        return {"source": "snusbase", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "snusbase", "error": str(e)}

# ==================== VERIPHONE ====================
def search_veriphone(phone):
    try:
        phone_clean = re.sub(r'\D', '', phone)
        r = requests.get(VERIPHONE_URL,
                         params={"phone": phone_clean, "key": VERIPHONE_KEY},
                         timeout=30)
        if r.status_code == 200:
            data = r.json()
            return {"source": "veriphone",
                    "data": {"valid": data.get("phone_valid", False),
                             "country": data.get("country_name"),
                             "region": data.get("phone_region"),
                             "carrier": data.get("carrier")}}
        return {"source": "veriphone", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "veriphone", "error": str(e)}

# ==================== IPGEO ====================
def search_ipgeo(ip):
    try:
        r = requests.get(IPGEO_URL,
                         params={"apiKey": IPGEO_KEY, "ip": ip}, timeout=30)
        if r.status_code == 200:
            return {"source": "ipgeo", "data": r.json()}
        return {"source": "ipgeo", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "ipgeo", "error": str(e)}

# ==================== OFDATA ====================
def search_ofdata(query, search_type):
    if search_type not in ["inn", "ogrn", "fio", "company"]:
        return {"source": "ofdata", "error": "Тип не поддерживается"}
    try:
        by = search_type if search_type in ["inn", "ogrn"] else "name"
        obj = "org" if search_type in ["inn", "ogrn", "company"] else "ent"
        url = f"{OFDATA_URL}?key={OFDATA_KEY}&by={by}&obj={obj}&query={query}&limit=10"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data.get("data", {}).get("Записи"):
                return {"source": "ofdata", "data": data}
            return {"source": "ofdata", "error": "Ничего не найдено"}
        return {"source": "ofdata", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "ofdata", "error": str(e)}

# ==================== OMKAR PHONE ====================
def search_omkar_phone(phone):
    try:
        r = requests.get("https://carrier-lookup-api.omkar.cloud/lookup",
                         params={"phone": phone},
                         headers={"API-Key": OMKAR_API_KEY}, timeout=30)
        if r.status_code == 200:
            return {"source": "omkar_phone", "data": r.json()}
        return {"source": "omkar_phone", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "omkar_phone", "error": str(e)}

# ==================== OMKAR EMAIL ====================
def search_omkar_email(email):
    try:
        r = requests.get("https://email-verification-api.omkar.cloud/verify",
                         params={"email": email},
                         headers={"API-Key": OMKAR_API_KEY}, timeout=30)
        if r.status_code == 200:
            return {"source": "omkar_email", "data": r.json()}
        return {"source": "omkar_email", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "omkar_email", "error": str(e)}

# ==================== OMKAR REVIEWS ====================
def search_omkar_reviews(query):
    try:
        r = requests.get("https://travel-data-api.omkar.cloud/travel/reviews",
                         params={"query": query},
                         headers={"API-Key": OMKAR_API_KEY}, timeout=60)
        if r.status_code == 200:
            data = r.json()
            results = []
            for review in data.get('results', [])[:20]:
                results.append({
                    "title": review.get('title'),
                    "rating": review.get('rating'),
                    "text": review.get('text')[:500] if review.get('text') else None,
                    "date": review.get('published_at_date'),
                    "author": review.get('reviewer', {}).get('name'),
                    "link": review.get('review_link')
                })
            return {"source": "omkar_reviews",
                    "data": {"query": query,
                             "total": data.get('count', 0),
                             "reviews": results}}
        return {"source": "omkar_reviews", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "omkar_reviews", "error": str(e)}

# ==================== VK ====================
def search_vk(user_id):
    try:
        params = {"access_token": VK_TOKEN, "user_ids": user_id, "v": "5.131",
                  "fields": "first_name,last_name,domain,followers_count,is_closed,sex,bdate,city,country,photo_max_orig,status"}
        r = requests.get("https://api.vk.com/method/users.get",
                         params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if "error" in data:
                return {"source": "vk", "error": data["error"].get("error_msg", "VK error")}
            if "response" in data and data["response"]:
                user = data["response"][0]
                return {"source": "vk",
                        "data": {"id": user.get("id"),
                                 "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                                 "domain": user.get("domain"),
                                 "followers": user.get("followers_count"),
                                 "is_closed": user.get("is_closed", False),
                                 "bdate": user.get("bdate"),
                                 "city": user.get("city", {}).get("title"),
                                 "country": user.get("country", {}).get("title"),
                                 "photo": user.get("photo_max_orig"),
                                 "status": user.get("status")}}
        return {"source": "vk", "error": "Пользователь не найден"}
    except Exception as e:
        return {"source": "vk", "error": str(e)}

# ==================== INTELX ====================
def search_intelx(phone):
    phone_clean = re.sub(r'\D', '', phone)
    if len(phone_clean) < 8:
        return {"source": "intelx", "error": "Номер слишком короткий"}
    url = f"https://data.intelx.io/saverudata/db2/dbpn/{phone_clean[:2]}/{phone_clean[2:4]}/{phone_clean[4:6]}/{phone_clean[6:8]}.csv"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"},
                         timeout=30, verify=False)
        if r.status_code == 200:
            csv_data = list(csv.reader(io.StringIO(r.text)))
            if len(csv_data) > 1:
                headers = csv_data[0]
                results = []
                for row in csv_data[1:]:
                    row_text = ' '.join(row)
                    if phone_clean in row_text:
                        result = {}
                        for i, val in enumerate(row):
                            if i < len(headers) and val:
                                result[headers[i]] = val
                        results.append(result)
                if results:
                    return {"source": "intelx",
                            "data": {"total": len(results),
                                     "results": results[:20]}}
                return {"source": "intelx", "error": "Номер не найден"}
            return {"source": "intelx", "error": "CSV пустой"}
        return {"source": "intelx", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "intelx", "error": str(e)}

# ==================== WHATSAPP ====================
def search_whatsapp(phone):
    phone_clean = re.sub(r'\D', '', phone)
    if phone_clean.startswith('8'):
        phone_clean = '7' + phone_clean[1:]
    elif not phone_clean.startswith('7'):
        phone_clean = '7' + phone_clean
    try:
        r = requests.get(f"https://wa.me/{phone_clean}", timeout=30, allow_redirects=True)
        if r.status_code == 200:
            return {"source": "whatsapp",
                    "data": {"exists": "not on WhatsApp" not in r.text,
                             "phone": phone_clean}}
        return {"source": "whatsapp", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "whatsapp", "error": str(e)}

# ==================== ODNOKLASSNIKI ====================
def search_odnoklassniki(phone):
    phone_clean = re.sub(r'\D', '', phone)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        params = {"st.mode": "Users", "st.query": phone_clean}
        r = requests.get("https://ok.ru/search", headers=headers, params=params, timeout=30)
        if r.status_code == 200:
            match = re.search(r'num-found["\s]*:["\s]*(\d+)', r.text)
            exists = match and int(match.group(1)) > 0
            return {"source": "odnoklassniki",
                    "data": {"exists": exists, "phone": phone_clean}}
        return {"source": "odnoklassniki", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "odnoklassniki", "error": str(e)}

# ==================== TELEGRAM ====================
def search_telegram(username):
    username = username.replace("@", "").strip()
    try:
        r = requests.get(f"https://t.me/{username}", timeout=30)
        if r.status_code == 200:
            exists = "is not available" not in r.text
            return {"source": "telegram",
                    "data": {"exists": exists, "username": username}}
        return {"source": "telegram", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "telegram", "error": str(e)}

# ==================== TIKTOK ====================
def search_tiktok(username):
    username = username.replace('@', '').strip()
    url = f"https://www.tiktok.com/@{username}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            followers_match = re.search(r'"followerCount":(\d+)', r.text)
            followers = int(followers_match.group(1)) if followers_match else 0
            name_match = re.search(r'"nickname":"([^"]+)"', r.text)
            name = name_match.group(1) if name_match else username
            return {"source": "tiktok",
                    "data": {"username": username, "name": name, "followers": followers}}
        return {"source": "tiktok", "error": "Пользователь не найден"}
    except Exception as e:
        return {"source": "tiktok", "error": str(e)}

# ==================== BIN ====================
def search_bin(bin_number):
    bin_number = bin_number[:6]
    try:
        r = requests.get(f"https://lookup.binlist.net/{bin_number}",
                         headers={'Accept-Version': '3'}, timeout=30)
        if r.status_code == 200:
            data = r.json()
            return {"source": "bin",
                    "data": {"bin": bin_number,
                             "bank": data.get('bank', {}).get('name'),
                             "country": data.get('country', {}).get('name'),
                             "brand": data.get('scheme'),
                             "type": data.get('type')}}
        return {"source": "bin", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "bin", "error": str(e)}

# ==================== WHOIS ====================
def search_whois(domain):
    try:
        w = whois.whois(domain)
        return {"source": "whois",
                "data": {"domain": domain,
                         "registrar": str(w.registrar) if w.registrar else None,
                         "creation_date": str(w.creation_date) if w.creation_date else None,
                         "expiration_date": str(w.expiration_date) if w.expiration_date else None,
                         "name_servers": w.name_servers,
                         "status": w.status}}
    except Exception as e:
        return {"source": "whois", "error": str(e)}

# ==================== DNS ====================
def search_dns(domain):
    records = {}
    try:
        for record_type in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                records[record_type] = [str(r) for r in answers]
            except Exception:
                records[record_type] = []
        return {"source": "dns", "data": {"domain": domain, "records": records}}
    except Exception as e:
        return {"source": "dns", "error": str(e)}

# ==================== SUBDOMAINS ====================
def search_subdomains(domain):
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            data = r.json()
            subdomains = set()
            for entry in data:
                name = entry.get('name_value', '')
                if name:
                    for sub in name.split('\n'):
                        if domain in sub:
                            subdomains.add(sub.strip())
            return {"source": "subdomains",
                    "data": {"domain": domain,
                             "subdomains": list(subdomains)[:50]}}
        return {"source": "subdomains", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "subdomains", "error": str(e)}

# ==================== HEADERS ====================
def search_headers(url):
    if not url.startswith('http'):
        url = 'https://' + url
    try:
        r = requests.get(url, timeout=30,
                         headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        return {"source": "headers",
                "data": {"url": url, "status_code": r.status_code,
                         "server": r.headers.get('Server'),
                         "content_type": r.headers.get('Content-Type'),
                         "headers": dict(r.headers)}}
    except Exception as e:
        return {"source": "headers", "error": str(e)}

# ==================== SOCIAL LINKS ====================
def search_social_links(phone):
    phone_clean = ''.join(filter(str.isdigit, phone))
    return {"source": "social_links",
            "data": {
                "vk": f"https://vk.com/search?c[q]={phone_clean}&c[section]=people",
                "whatsapp": f"https://wa.me/{phone_clean}",
                "telegram": f"https://t.me/{phone_clean}",
                "instagram": f"https://www.instagram.com/{phone_clean}",
                "facebook": f"https://www.facebook.com/search/top?q={phone_clean}",
                "tiktok": f"https://www.tiktok.com/search?q={phone_clean}",
                "twitter": f"https://twitter.com/search?q={phone_clean}",
                "ok": f"https://ok.ru/search?q={phone_clean}",
                "viber": f"viber://add?number={phone_clean}",
                "yandex": f"https://yandex.ru/search/?text={phone_clean}",
                "google": f"https://www.google.com/search?q={phone_clean}"
            }}

# ==================== DORKS ====================
def search_dorks(phone):
    phone_clean = ''.join(filter(str.isdigit, phone))
    if phone_clean.startswith('8'):
        phone_clean = '7' + phone_clean[1:]
    dorks = [
        f'"{phone_clean}"',
        f'"{phone_clean}" filetype:pdf',
        f'"{phone_clean}" site:vk.com',
        f'"{phone_clean}" site:avito.ru',
        f'"{phone_clean}" site:ok.ru',
        f'"{phone_clean}" "ИНН"',
        f'"{phone_clean}" "паспорт"',
        f'"{phone_clean}" "адрес"'
    ]
    return {"source": "dorks",
            "data": {"phone": phone_clean,
                     "dorks": [f"https://www.google.com/search?q={quote(d)}" for d in dorks]}}

# ==================== DETECT TYPE ====================
def detect_type(query: str) -> Tuple[str, Optional[str]]:
    query = query.strip()
    if not query:
        return "unknown", None

    auto_clean = re.sub(r'\s+', '', query.upper())
    auto_patterns = [
        r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$',
        r'^[АВЕКМНОРСТУХ]{2}\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$',
        r'^[A-Z]\d{3}[A-Z]{2}\d{2,3}$'
    ]
    for pattern in auto_patterns:
        if re.match(pattern, auto_clean):
            return "auto", auto_clean

    vin_clean = re.sub(r'\s+', '', query.upper())
    if re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin_clean):
        return "vin", vin_clean

    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', query):
        return "email", query.lower()

    ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    if re.match(ip_pattern, query):
        return "ip", query

    phone_clean = re.sub(r'[\s()+-]', '', query)
    if re.match(r'^(7|8|9)\d{10}$', phone_clean):
        if phone_clean.startswith('8'):
            phone_clean = '7' + phone_clean[1:]
        elif phone_clean.startswith('9'):
            phone_clean = '7' + phone_clean
        return "phone", phone_clean

    if query.lower().startswith('id') and query[2:].isdigit():
        return "vkid", query[2:]

    if query.lower().startswith('tt:'):
        return "tiktok", query[3:]

    if query.lower().startswith('nick:'):
        return "nick", query[5:]

    if query.lower().startswith('pass:'):
        return "pass", query[5:]

    if query.lower().startswith('addr:') or query.lower().startswith('адрес:'):
        return "addr", query.split(":", 1)[1].strip()

    if re.match(r'^\d{10}$', query) or re.match(r'^\d{12}$', query):
        return "inn", query

    snils_clean = re.sub(r'[\s-]', '', query)
    if re.match(r'^\d{11}$', snils_clean):
        return "snils", snils_clean

    passport_clean = re.sub(r'[\s-]', '', query)
    if re.match(r'^\d{4}\d{6}$', passport_clean):
        return "passport", passport_clean

    if re.search(r'[а-яА-Я]', query):
        words = query.split()
        if len(words) >= 2:
            return "fio", query

    if re.match(r'^\d{13}$', query):
        return "ogrn", query

    return "username", query


def check_api_key():
    return request.headers.get('X-API-Key') == MASTER_KEY


# ==================== /search ====================
@app.route('/search', methods=['POST'])
def search():
    if not check_api_key():
        return jsonify({"error": "Неверный API-ключ"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Нет данных"}), 400

    query = data.get('query', '').strip()
    if not query:
        return jsonify({"error": "Пустой запрос"}), 400

    search_type = data.get('type')
    if not search_type:
        search_type, normalized_query = detect_type(query)
        if normalized_query:
            query = normalized_query

    result = {
        "query": query,
        "type": search_type,
        "timestamp": datetime.now().isoformat(),
        "sources": []
    }

    # DEPSEARCH
    if search_type in ["phone", "email", "fio", "vk", "vkid", "tiktok",
                       "ip", "snils", "inn", "addr", "username", "nick",
                       "pass", "auto", "vin"]:
        result["sources"].append(search_depsearch(query, search_type))

    # GLOOM
    if search_type in ["phone", "email", "fio", "vk", "telegram", "telegram_id",
                       "telegram_username", "username", "ip", "passport",
                       "inn", "snils", "card"]:
        result["sources"].append(search_gloom(query, search_type))

    # INFINITY
    if search_type in ["phone", "email", "fio"]:
        result["sources"].append(search_infinity(query, search_type))

    # WHITE SEARCH
    if search_type in ["phone", "email", "fio", "telegram", "telegram_id",
                       "telegram_username", "vk", "ip", "snils", "inn",
                       "passport", "auto", "vin"]:
        result["sources"].append(search_white_search(query, search_type))

    # JITLER
    if search_type in ["phone", "telegram", "telegram_id", "telegram_username", "vk"]:
        result["sources"].append(search_jitler(query, search_type))

    # NIGHT SEARCH
    if search_type in ["phone", "email", "fio", "passport", "inn", "snils",
                       "vk", "telegram", "telegram_id", "telegram_username",
                       "auto", "vin", "ip", "ogrn", "username", "domain",
                       "card", "bank"]:
        result["sources"].append(search_nightsearch(query, search_type))

    # HUNTER.HOW
    if search_type in ["ip", "domain"]:
        result["sources"].append(search_hunterhow(query, search_type))

    # HUNTER.IO
    if search_type in ["domain", "company", "email"]:
        result["sources"].append(search_hunter(query, search_type))

    # NUMVERIFY
    if search_type == "phone":
        result["sources"].append(search_numverify(query))

    # LEAKCHECK
    if search_type in ["email", "phone"]:
        result["sources"].append(search_leakcheck(query, search_type))

    # SNUSBASE
    if search_type in ["email", "fio", "ip"]:
        result["sources"].append(search_snusbase(query, search_type))

    # VERIPHONE
    if search_type == "phone":
        result["sources"].append(search_veriphone(query))

    # IPGEO
    if search_type == "ip":
        result["sources"].append(search_ipgeo(query))

    # OFDATA
    if search_type in ["inn", "ogrn", "fio", "company"]:
        result["sources"].append(search_ofdata(query, search_type))

    # OMKAR PHONE
    if search_type == "phone":
        result["sources"].append(search_omkar_phone(query))

    # OMKAR EMAIL
    if search_type == "email":
        result["sources"].append(search_omkar_email(query))

    # OMKAR REVIEWS
    if search_type in ["fio", "phone", "username"]:
        result["sources"].append(search_omkar_reviews(query))

    # VK
    if search_type in ["vk", "vkid"]:
        result["sources"].append(search_vk(query))

    # INTELX
    if search_type == "phone":
        result["sources"].append(search_intelx(query))

    # WHATSAPP
    if search_type == "phone":
        result["sources"].append(search_whatsapp(query))

    # ODNOKLASSNIKI
    if search_type == "phone":
        result["sources"].append(search_odnoklassniki(query))

    # TELEGRAM
    if search_type == "username":
        result["sources"].append(search_telegram(query))

    # TIKTOK
    if search_type == "tiktok":
        result["sources"].append(search_tiktok(query))

    # BIN
    if re.match(r'^\d{6,8}$', query):
        result["sources"].append(search_bin(query))

    # WHOIS
    if search_type == "domain":
        result["sources"].append(search_whois(query))

    # DNS
    if search_type == "domain":
        result["sources"].append(search_dns(query))

    # SUBDOMAINS
    if search_type == "domain":
        result["sources"].append(search_subdomains(query))

    # HEADERS
    if search_type == "domain":
        result["sources"].append(search_headers(query))

    # SOCIAL LINKS
    if search_type == "phone":
        result["sources"].append(search_social_links(query))

    # DORKS
    if search_type == "phone":
        result["sources"].append(search_dorks(query))

    return jsonify(result)


# ==================== /health ====================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})


# ==================== / ====================
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "name": "DeepTrek API",
        "version": "26.1",
        "sources": [
            "DepSearch",
            "Gloom (заменяет BigBase + DepSearch)",
            "Infinity (2 ключа)",
            "White Search",
            "Jitler",
            "Night Search",
            "Hunter.how",
            "Hunter.io",
            "Numverify",
            "LeakCheck",
            "Snusbase",
            "Veriphone",
            "IpGeo",
            "OFDATA",
            "Omkar Phone",
            "Omkar Email",
            "Omkar Reviews",
            "VK API",
            "IntelX",
            "WhatsApp",
            "Odnoklassniki",
            "Telegram",
            "TikTok",
            "BIN",
            "WHOIS",
            "DNS",
            "Subdomains",
            "Headers",
            "Social Links",
            "Google Dorks"
        ],
        "total_sources": 30
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)