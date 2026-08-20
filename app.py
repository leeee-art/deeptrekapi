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
import os
from datetime import datetime
from typing import Tuple, Optional
from urllib.parse import unquote, quote
from funstat_api import FunstatClient

app = Flask(__name__)
CORS(app)

MASTER_KEY = 'deeptrek_fjnrndhfrb2947472992gdvsbdh'

BIGBASE_KEY_1 = 'hS9I51yASMt5yGj8S9k1jbbN6HmA38xA'
BIGBASE_KEY_2 = 'IWTtHHz1lg_5XbYNHBWjiAtPiRrzpESM'
BIGBASE_URL = 'https://bigbase.top/api/search'

INFINITY_TOKEN_1 = 'Bjm928HUcvsw923ZMBX19gd110FWSZgd'
INFINITY_TOKEN_2 = 'QoNm98UeMLIqNjZ198snm98AdGvhqA88'
INFINITY_URL = 'https://infinity-search.fun/find.php'

WHITESEARCH_KEY = 'WS-PUBLIC-9X7K-2M4P'
WHITESEARCH_URL = 'https://api.whitesearch.workers.dev/api'

JITLER_TOKEN = '7M8wfVQlszWnbaaINN2ig7iA'
JITLER_URL = 'https://api.jitler.top/search'

NIGHTSEARCH_KEY = 'sk_66beac29ce86f915b184a9ddde7aecbfc6177ab265cf5c1f579ce53219422234'
NIGHTSEARCH_URL = 'https://nightsearch.life/api/search'

HUNTERHOW_API_KEY = 'd43597d5bc6033a21ba389e034080628fe2ecffd'
HUNTERHOW_URL = 'https://api.hunter.how/search'

HUNTER_API_KEY = 'd43597d5bc6033a21ba389e034080628fe2ecffd'
HUNTER_URL = 'https://api.hunter.io/v2'

NUMVERIFY_API_KEY = '45b6ab2f9ee0cf8acb0880d5dfe5ec5c'
NUMVERIFY_URL = 'http://apilayer.net/api/validate'

LEAKCHECK_KEY = '49535f49545f5245414c4c595f4150495f4b4559'
LEAKCHECK_URL = 'https://leakcheck.net/api/public'

SNUSBASE_KEY = 'sb5029dec66mht55m78fx8bsw6tm8a'
SNUSBASE_URL = 'https://api.snusbase.com/v3/search'

FUNSTAT_TOKEN = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiIyMDMzMDI5NDc1IiwianRpIjoiODJmMjlmNzQtYmJlMi00ZGUwLWEwZDQtN2EzMDJhMWE5MDViIiwiZXhwIjoxODAxMDA4MzM4fQ.Mba4aX85YAMcaMLfhUBzXtCoNmEujfMe-6sGBbp3kT-T2SiLM_Ho0BBAFAQ8_C6Gz06PH9mAYhfBvlLSjb4oVd1Fm_vmb8MC-wuObU3qgfGrYdGzVF3ntJHv-LdNELq-jsqvQOY3jq9meso9dUoyj5SviDQWL6cvnRQ03kpHWxA'

VERIPHONE_KEY = 'A9A2A88762854D45888BA49E8F98509C'
VERIPHONE_URL = 'https://api.veriphone.io/v2/verify'

IPGEO_KEY = '73d99145d2e948779263360bfeb67ecc'
IPGEO_URL = 'https://api.ipgeolocation.io/ipgeo'

OFDATA_KEY = 'KBnpz1CHKNngFXxK'
OFDATA_URL = 'https://api.ofdata.ru/v2/search'

OMKAR_API_KEY = 'ok_ad50fb80682eff950d34e7a9b3a77c8c'

VK_TOKEN = 'vk1.a.WX465fcyCl3FoFXysIyBPjQYn4D4Cgz3SJAmX7mxXvQBMUzTjzkaZfA0Tt-FBRDuA4WYq7tvbO3TaqZbvdl3oAva367V8KP4AQUFI1kC3I8UnT687rM12Bv-d-Ax9FnXAeOTxMp8MTBUwqQ_6kH-1LAQIT7fgdzWaawG3CEOhe6Q5VSuzTrDFF0iWIrUAXIwT22_uN6XzH25tZCegI-AWQ'

SMSC_LOGIN = 'kirahacker333'
SMSC_PASSWORD = 'Zangar5050'

bigbase_keys = [BIGBASE_KEY_1, BIGBASE_KEY_2]
bigbase_idx = 0
infinity_tokens = [INFINITY_TOKEN_1, INFINITY_TOKEN_2]
infinity_idx = 0

def get_bigbase_key():
    global bigbase_idx
    key = bigbase_keys[bigbase_idx]
    bigbase_idx = (bigbase_idx + 1) % len(bigbase_keys)
    return key

def get_infinity_token():
    global infinity_idx
    token = infinity_tokens[infinity_idx]
    infinity_idx = (infinity_idx + 1) % len(infinity_tokens)
    return token

def sanitize_bigbase(data):
    if isinstance(data, dict):
        for key, value in list(data.items()):
            if key == "user" and isinstance(value, dict):
                if "login" in value:
                    value["login"] = "***"
                if "api_token" in value:
                    value["api_token"] = "***"
                if "referral_url" in value:
                    value["referral_url"] = "***"
            elif key == "login":
                data[key] = "***"
            elif key == "api_token":
                data[key] = "***"
            elif key == "referral_url":
                data[key] = "***"
            elif isinstance(value, dict):
                sanitize_bigbase(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        sanitize_bigbase(item)
    return data

def search_bigbase(query, search_type):
    key = get_bigbase_key()
    try:
        headers = {"Authorization": key, "Content-Type": "application/json"}
        data = {"search": query, "page": 0}
        r = requests.post(BIGBASE_URL, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            result = r.json()
            if result.get("error"):
                return {"source": "bigbase", "error": result["error"]}
            result = sanitize_bigbase(result)
            if result.get("records") and result.get("count_result", 0) == 0:
                result["count_result"] = len(result["records"])
            return {"source": "bigbase", "data": result}
        return {"source": "bigbase", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "bigbase", "error": str(e)}

def search_infinity(query, search_type):
    token = get_infinity_token()
    if search_type not in ["phone", "email", "fio"]:
        return {"source": "infinity", "error": "Тип не поддерживается"}
    try:
        params = {"token": token, search_type: query}
        r = requests.get(INFINITY_URL, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("results"):
                return {"source": "infinity", "data": {"total": len(data["results"]), "results": data["results"][:20]}}
            return {"source": "infinity", "error": "Ничего не найдено"}
        return {"source": "infinity", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "infinity", "error": str(e)}

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
        r = requests.get(url, params=params, headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data.get("success") and data.get("data"):
                results_data = data.get("data", [])
                if isinstance(results_data, dict) and results_data.get("message") == "Not found":
                    return {"source": "white_search", "error": "Ничего не найдено"}
                return {"source": "white_search", "data": {"total": len(results_data) if isinstance(results_data, list) else 1, "results": results_data if isinstance(results_data, list) else [results_data]}}
            return {"source": "white_search", "error": "Ничего не найдено"}
        elif r.status_code == 429:
            return {"source": "white_search", "error": "Дневной лимит исчерпан"}
        return {"source": "white_search", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "white_search", "error": str(e)}

def search_jitler(query, search_type):
    if search_type not in ["phone", "telegram", "telegram_id", "telegram_username", "vk"]:
        return {"source": "jitler", "error": "Jitler поддерживает только phone, telegram, vk"}
    type_map = {"phone": "number", "telegram": "sherlock", "telegram_id": "sherlock", "telegram_username": "sherlock", "vk": "vks"}
    try:
        headers = {"Authorization": f"Bearer {JITLER_TOKEN}", "Content-Type": "application/json"}
        payload = {"type": type_map[search_type], "query": query, "page": 1}
        r = requests.post(JITLER_URL, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            data = r.json()
            return {"source": "jitler", "data": data.get("response", {})}
        return {"source": "jitler", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "jitler", "error": str(e)}

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
        headers = {"X-API-Key": NIGHTSEARCH_KEY, "Content-Type": "application/json; charset=utf-8"}
        if search_type == "phone":
            query = re.sub(r'\D', '', query)
        payload = {"query": query, "search_type": type_map[search_type]}
        r = requests.post(NIGHTSEARCH_URL, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            data = r.json()
            return {"source": "nightsearch", "data": data}
        elif r.status_code == 401:
            return {"source": "nightsearch", "error": "Неверный API ключ"}
        elif r.status_code == 429:
            return {"source": "nightsearch", "error": "Лимит запросов исчерпан"}
        else:
            return {"source": "nightsearch", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "nightsearch", "error": str(e)}

def search_hunterhow(query, search_type):
    if search_type not in ["ip", "domain"]:
        return {"source": "hunterhow", "error": "Hunter.how поддерживает ip, domain"}
    try:
        if search_type == "ip":
            q = f'ip="{query}"'
        else:
            q = f'domain="{query}"'
        encoded_query = base64.urlsafe_b64encode(q.encode("utf-8")).decode('ascii')
        params = {
            "api-key": HUNTERHOW_API_KEY,
            "query": encoded_query,
            "page": 1,
            "page_size": 10,
            "start_time": "2024-01-01",
            "end_time": "2026-12-31",
            "fields": "ip,port,domain,protocol,transport_protocol,web_title,country,province,city,url,asn,as_org,as_name,status_code,cert,os,header,header_server,banner,product,updated_at,body"
        }
        r = requests.get(HUNTERHOW_URL, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 200:
                results = data.get("data", {})
                items = results.get("list", [])
                return {"source": "hunterhow", "data": {"total": results.get("total", len(items)), "results": items[:20]}}
            return {"source": "hunterhow", "error": data.get("message", "Ошибка")}
        elif r.status_code == 401:
            return {"source": "hunterhow", "error": "Неверный API ключ"}
        elif r.status_code == 429:
            return {"source": "hunterhow", "error": "Лимит запросов"}
        return {"source": "hunterhow", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "hunterhow", "error": str(e)}

def search_hunter(query, search_type):
    if search_type not in ["domain", "company", "email"]:
        return {"source": "hunter", "error": "Hunter поддерживает domain, company, email"}
    try:
        if search_type == "domain":
            params = {"domain": query, "api_key": HUNTER_API_KEY, "limit": 50}
            r = requests.get(f"{HUNTER_URL}/domain-search", params=params, timeout=30)
            if r.status_code == 200:
                data = r.json()
                emails = data.get("data", {}).get("emails", [])
                return {"source": "hunter", "data": {"domain": query, "total_emails": len(emails), "emails": [{"email": e.get("value"), "type": e.get("type"), "first_name": e.get("first_name"), "last_name": e.get("last_name"), "position": e.get("position"), "department": e.get("department"), "confidence": e.get("confidence")} for e in emails[:20]]}}
        elif search_type == "email":
            params = {"email": query, "api_key": HUNTER_API_KEY}
            r = requests.get(f"{HUNTER_URL}/email-verifier", params=params, timeout=30)
            if r.status_code == 200:
                data = r.json()
                return {"source": "hunter", "data": data.get("data", {})}
        return {"source": "hunter", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "hunter", "error": str(e)}

def search_numverify(phone):
    try:
        phone_clean = re.sub(r'\D', '', phone)
        params = {"access_key": NUMVERIFY_API_KEY, "number": phone_clean, "format": 1}
        r = requests.get(NUMVERIFY_URL, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("valid"):
                return {"source": "numverify", "data": {"valid": data.get("valid"), "number": data.get("international_format"), "local_format": data.get("local_format"), "country": data.get("country_name"), "country_code": data.get("country_code"), "location": data.get("location"), "carrier": data.get("carrier"), "line_type": data.get("line_type")}}
            return {"source": "numverify", "error": "Номер невалиден"}
        return {"source": "numverify", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "numverify", "error": str(e)}

def search_leakcheck(query, search_type="email"):
    try:
        r = requests.get(LEAKCHECK_URL, params={"key": LEAKCHECK_KEY, "check": query}, timeout=10)
        if r.status_code == 200:
            return {"source": "leakcheck", "data": r.json()}
        return {"source": "leakcheck", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "leakcheck", "error": str(e)}

def search_snusbase(query, search_type):
    if search_type not in ["email", "fio", "ip"]:
        return {"source": "snusbase", "error": "Тип не поддерживается"}
    try:
        snus_type = "ip" if search_type == "ip" else search_type
        if search_type == "fio":
            snus_type = "username"
        payload = {"terms": [query], "types": [snus_type], "wildcard": False}
        headers = {"Auth": SNUSBASE_KEY, "Content-Type": "application/json"}
        r = requests.post(SNUSBASE_URL, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return {"source": "snusbase", "data": r.json()}
        return {"source": "snusbase", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "snusbase", "error": str(e)}

def search_funstat(query, search_type):
    if search_type not in ["telegram", "telegram_id"]:
        return {"source": "funstat", "error": "Funstat поддерживает только поиск по Telegram ID"}
    if not query.isdigit():
        return {"source": "funstat", "error": "Funstat ищет только по числовому ID"}
    try:
        client = FunstatClient(FUNSTAT_TOKEN)
        stats = client.stats_min(int(query))
        if stats.success:
            data = stats.data
            return {"source": "funstat", "data": {"id": data.id, "first_name": data.first_name, "last_name": data.last_name, "is_bot": data.is_bot, "is_active": data.is_active, "first_msg_date": data.first_msg_date, "last_msg_date": data.last_msg_date, "total_msg_count": data.total_msg_count, "msg_in_groups_count": data.msg_in_groups_count, "adm_in_groups": data.adm_in_groups, "total_groups": data.total_groups, "usernames_count": data.usernames_count, "names_count": data.names_count}}
        return {"source": "funstat", "error": "Пользователь не найден"}
    except Exception as e:
        return {"source": "funstat", "error": str(e)}

def search_veriphone(phone):
    try:
        phone_clean = re.sub(r'\D', '', phone)
        r = requests.get(VERIPHONE_URL, params={"phone": phone_clean, "key": VERIPHONE_KEY}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {"source": "veriphone", "data": {"valid": data.get("phone_valid", False), "country": data.get("country_name"), "region": data.get("phone_region"), "carrier": data.get("carrier")}}
        return {"source": "veriphone", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "veriphone", "error": str(e)}

def search_ipgeo(ip):
    try:
        r = requests.get(IPGEO_URL, params={"apiKey": IPGEO_KEY, "ip": ip}, timeout=10)
        if r.status_code == 200:
            return {"source": "ipgeo", "data": r.json()}
        return {"source": "ipgeo", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "ipgeo", "error": str(e)}

def search_ofdata(query, search_type):
    if search_type not in ["inn", "ogrn", "fio", "company"]:
        return {"source": "ofdata", "error": "Тип не поддерживается"}
    try:
        by = search_type if search_type in ["inn", "ogrn"] else "name"
        obj = "org" if search_type in ["inn", "ogrn", "company"] else "ent"
        url = f"{OFDATA_URL}?key={OFDATA_KEY}&by={by}&obj={obj}&query={query}&limit=10"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("data", {}).get("Записи"):
                return {"source": "ofdata", "data": data}
            return {"source": "ofdata", "error": "Ничего не найдено"}
        return {"source": "ofdata", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "ofdata", "error": str(e)}

def search_omkar_phone(phone):
    try:
        url = "https://carrier-lookup-api.omkar.cloud/lookup"
        params = {"phone": phone}
        headers = {"API-Key": OMKAR_API_KEY}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return {"source": "omkar_phone", "data": r.json()}
        return {"source": "omkar_phone", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "omkar_phone", "error": str(e)}

def search_omkar_email(email):
    try:
        url = "https://email-verification-api.omkar.cloud/verify"
        params = {"email": email}
        headers = {"API-Key": OMKAR_API_KEY}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return {"source": "omkar_email", "data": r.json()}
        return {"source": "omkar_email", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "omkar_email", "error": str(e)}

def search_omkar_reviews(query):
    try:
        url = "https://travel-data-api.omkar.cloud/travel/reviews"
        r = requests.get(url, params={"query": query}, headers={"API-Key": OMKAR_API_KEY}, timeout=30)
        if r.status_code == 200:
            data = r.json()
            results = []
            for review in data.get('results', [])[:20]:
                results.append({"title": review.get('title'), "rating": review.get('rating'), "text": review.get('text')[:500] if review.get('text') else None, "date": review.get('published_at_date'), "author": review.get('reviewer', {}).get('name'), "link": review.get('review_link')})
            return {"source": "omkar_reviews", "data": {"query": query, "total": data.get('count', 0), "reviews": results}}
        return {"source": "omkar_reviews", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "omkar_reviews", "error": str(e)}

def search_vk(user_id):
    try:
        url = "https://api.vk.com/method/users.get"
        params = {"access_token": VK_TOKEN, "user_ids": user_id, "v": "5.131", "fields": "first_name,last_name,domain,followers_count,is_closed,sex,bdate,city,country,photo_max_orig,status"}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if "response" in data and data["response"]:
                user = data["response"][0]
                return {"source": "vk", "data": {"id": user.get("id"), "name": f"{user.get('first_name', '')} {user.get('last_name', '')}", "domain": user.get("domain"), "followers": user.get("followers_count"), "is_closed": user.get("is_closed", False), "bdate": user.get("bdate"), "city": user.get("city", {}).get("title"), "country": user.get("country", {}).get("title"), "photo": user.get("photo_max_orig"), "status": user.get("status")}}
        return {"source": "vk", "error": "Пользователь не найден"}
    except Exception as e:
        return {"source": "vk", "error": str(e)}

def search_intelx(phone):
    phone_clean = re.sub(r'\D', '', phone)
    if len(phone_clean) < 8:
        return {"source": "intelx", "error": "Номер слишком короткий"}
    url = f"https://data.intelx.io/saverudata/db2/dbpn/{phone_clean[:2]}/{phone_clean[2:4]}/{phone_clean[4:6]}/{phone_clean[6:8]}.csv"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, verify=False)
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
                    return {"source": "intelx", "data": {"total": len(results), "results": results[:20]}}
                return {"source": "intelx", "error": "Номер не найден"}
            return {"source": "intelx", "error": "CSV пустой"}
        return {"source": "intelx", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "intelx", "error": str(e)}

def search_whatsapp(phone):
    phone_clean = re.sub(r'\D', '', phone)
    if phone_clean.startswith('8'):
        phone_clean = '7' + phone_clean[1:]
    elif not phone_clean.startswith('7'):
        phone_clean = '7' + phone_clean
    try:
        r = requests.get(f"https://wa.me/{phone_clean}", timeout=10, allow_redirects=True)
        if r.status_code == 200:
            return {"source": "whatsapp", "data": {"exists": "not on WhatsApp" not in r.text, "phone": phone_clean}}
        return {"source": "whatsapp", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "whatsapp", "error": str(e)}

def search_odnoklassniki(phone):
    phone_clean = re.sub(r'\D', '', phone)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        url = "https://ok.ru/search"
        params = {"st.mode": "Users", "st.query": phone_clean}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            match = re.search(r'num-found["\s]*:["\s]*(\d+)', r.text)
            exists = match and int(match.group(1)) > 0
            return {"source": "odnoklassniki", "data": {"exists": exists, "phone": phone_clean}}
        return {"source": "odnoklassniki", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "odnoklassniki", "error": str(e)}

def search_telegram(username):
    username = username.replace("@", "").strip()
    try:
        r = requests.get(f"https://t.me/{username}", timeout=10)
        if r.status_code == 200:
            exists = "is not available" not in r.text
            return {"source": "telegram", "data": {"exists": exists, "username": username}}
        return {"source": "telegram", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "telegram", "error": str(e)}

def search_tiktok(username):
    username = username.replace('@', '').strip()
    url = f"https://www.tiktok.com/@{username}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            followers_match = re.search(r'"followerCount":(\d+)', r.text)
            followers = int(followers_match.group(1)) if followers_match else 0
            name_match = re.search(r'"nickname":"([^"]+)"', r.text)
            name = name_match.group(1) if name_match else username
            return {"source": "tiktok", "data": {"username": username, "name": name, "followers": followers}}
        return {"source": "tiktok", "error": "Пользователь не найден"}
    except Exception as e:
        return {"source": "tiktok", "error": str(e)}

def search_bin(bin_number):
    bin_number = bin_number[:6]
    try:
        r = requests.get(f"https://lookup.binlist.net/{bin_number}", headers={'Accept-Version': '3'}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {"source": "bin", "data": {"bin": bin_number, "bank": data.get('bank', {}).get('name'), "country": data.get('country', {}).get('name'), "brand": data.get('scheme'), "type": data.get('type')}}
        return {"source": "bin", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "bin", "error": str(e)}

def search_whois(domain):
    try:
        w = whois.whois(domain)
        return {"source": "whois", "data": {"domain": domain, "registrar": str(w.registrar) if w.registrar else None, "creation_date": str(w.creation_date) if w.creation_date else None, "expiration_date": str(w.expiration_date) if w.expiration_date else None, "name_servers": w.name_servers, "status": w.status}}
    except Exception as e:
        return {"source": "whois", "error": str(e)}

def search_dns(domain):
    records = {}
    try:
        for record_type in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                records[record_type] = [str(r) for r in answers]
            except:
                records[record_type] = []
        return {"source": "dns", "data": {"domain": domain, "records": records}}
    except Exception as e:
        return {"source": "dns", "error": str(e)}

def search_subdomains(domain):
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            subdomains = set()
            for entry in data:
                name = entry.get('name_value', '')
                if name:
                    for sub in name.split('\n'):
                        if domain in sub:
                            subdomains.add(sub.strip())
            return {"source": "subdomains", "data": {"domain": domain, "subdomains": list(subdomains)[:50]}}
        return {"source": "subdomains", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "subdomains", "error": str(e)}

def search_headers(url):
    if not url.startswith('http'):
        url = 'https://' + url
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        return {"source": "headers", "data": {"url": url, "status_code": r.status_code, "server": r.headers.get('Server'), "content_type": r.headers.get('Content-Type'), "headers": dict(r.headers)}}
    except Exception as e:
        return {"source": "headers", "error": str(e)}

def search_social_links(phone):
    phone_clean = ''.join(filter(str.isdigit, phone))
    return {"source": "social_links", "data": {"vk": f"https://vk.com/search?c[q]={phone_clean}&c[section]=people", "whatsapp": f"https://wa.me/{phone_clean}", "telegram": f"https://t.me/{phone_clean}", "instagram": f"https://www.instagram.com/{phone_clean}", "facebook": f"https://www.facebook.com/search/top?q={phone_clean}", "tiktok": f"https://www.tiktok.com/search?q={phone_clean}", "twitter": f"https://twitter.com/search?q={phone_clean}", "ok": f"https://ok.ru/search?q={phone_clean}", "viber": f"viber://add?number={phone_clean}", "yandex": f"https://yandex.ru/search/?text={phone_clean}", "google": f"https://www.google.com/search?q={phone_clean}"}}

def search_dorks(phone):
    phone_clean = ''.join(filter(str.isdigit, phone))
    if phone_clean.startswith('8'):
        phone_clean = '7' + phone_clean[1:]
    dorks = [f'"{phone_clean}"', f'"{phone_clean}" filetype:pdf', f'"{phone_clean}" site:vk.com', f'"{phone_clean}" site:avito.ru', f'"{phone_clean}" site:ok.ru', f'"{phone_clean}" "ИНН"', f'"{phone_clean}" "паспорт"', f'"{phone_clean}" "адрес"']
    return {"source": "dorks", "data": {"phone": phone_clean, "dorks": [f"https://www.google.com/search?q={quote(d)}" for d in dorks]}}

def detect_type(query: str) -> Tuple[str, Optional[str]]:
    query = query.strip()
    if not query:
        return "unknown", None

    auto_clean = re.sub(r'\s+', '', query.upper())
    auto_patterns = [r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$', r'^[АВЕКМНОРСТУХ]{2}\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$', r'^[A-Z]\d{3}[A-Z]{2}\d{2,3}$']
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
        return "vk", query[2:]

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

    result = {"query": query, "type": search_type, "timestamp": datetime.now().isoformat(), "sources": []}

    if search_type in ["phone", "email", "fio", "auto", "inn", "passport", "ip"]:
        result["sources"].append(search_bigbase(query, search_type))

    if search_type in ["phone", "email", "fio"]:
        result["sources"].append(search_infinity(query, search_type))

    if search_type in ["phone", "email", "fio", "telegram", "telegram_id", "telegram_username", "vk", "ip", "snils", "inn", "passport", "auto", "vin"]:
        result["sources"].append(search_white_search(query, search_type))

    if search_type in ["phone", "telegram", "telegram_id", "telegram_username", "vk"]:
        result["sources"].append(search_jitler(query, search_type))

    if search_type in ["phone", "email", "fio", "passport", "inn", "snils", "vk", "telegram", "telegram_id", "telegram_username", "auto", "vin", "ip", "ogrn", "username", "domain", "card", "bank"]:
        result["sources"].append(search_nightsearch(query, search_type))

    if search_type in ["ip", "domain"]:
        result["sources"].append(search_hunterhow(query, search_type))

    if search_type in ["domain", "company", "email"]:
        result["sources"].append(search_hunter(query, search_type))

    if search_type == "phone":
        result["sources"].append(search_numverify(query))

    if search_type in ["email", "phone"]:
        result["sources"].append(search_leakcheck(query, search_type))

    if search_type in ["email", "fio", "ip"]:
        result["sources"].append(search_snusbase(query, search_type))

    if search_type in ["telegram", "telegram_id"] and query.isdigit():
        result["sources"].append(search_funstat(query, search_type))

    if search_type == "phone":
        result["sources"].append(search_veriphone(query))

    if search_type == "ip":
        result["sources"].append(search_ipgeo(query))

    if search_type in ["inn", "ogrn", "fio", "company"]:
        result["sources"].append(search_ofdata(query, search_type))

    if search_type == "phone":
        result["sources"].append(search_omkar_phone(query))

    if search_type == "email":
        result["sources"].append(search_omkar_email(query))

    if search_type in ["fio", "phone", "username"]:
        result["sources"].append(search_omkar_reviews(query))

    if search_type == "vk":
        result["sources"].append(search_vk(query))

    if search_type == "phone":
        result["sources"].append(search_intelx(query))

    if search_type == "phone":
        result["sources"].append(search_whatsapp(query))

    if search_type == "phone":
        result["sources"].append(search_odnoklassniki(query))

    if search_type == "username":
        result["sources"].append(search_telegram(query))

    if search_type == "username":
        result["sources"].append(search_tiktok(query))

    if re.match(r'^\d{6,8}$', query):
        result["sources"].append(search_bin(query))

    if search_type == "domain":
        result["sources"].append(search_whois(query))

    if search_type == "domain":
        result["sources"].append(search_dns(query))

    if search_type == "domain":
        result["sources"].append(search_subdomains(query))

    if search_type == "domain":
        result["sources"].append(search_headers(query))

    if search_type == "phone":
        result["sources"].append(search_social_links(query))

    if search_type == "phone":
        result["sources"].append(search_dorks(query))

    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "name": "DeepTrek API",
        "version": "24.0",
        "sources": [
            "BigBase (2 ключа)", "Infinity (2 ключа)", "White Search",
            "Jitler", "Night Search", "Hunter.how", "Hunter.io",
            "Numverify", "LeakCheck", "Snusbase", "Funstat",
            "Veriphone", "IpGeo", "OFDATA", "Omkar Phone",
            "Omkar Email", "Omkar Reviews", "VK API",
            "IntelX", "WhatsApp", "Odnoklassniki", "Telegram",
            "TikTok", "BIN", "WHOIS", "DNS", "Subdomains",
            "Headers", "Social Links", "Google Dorks"
        ],
        "total_sources": 30
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)