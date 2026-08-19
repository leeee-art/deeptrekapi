from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import re
import time
import csv
import io
import os
from datetime import datetime
from typing import Tuple, Optional
from funstat_api import FunstatClient

app = Flask(__name__)
CORS(app)

# ==================== КОНФИГ ====================
MASTER_KEY = os.environ.get('MASTER_KEY', 'deeptrek_fjnrndhfrb2947472992gdvsbdh')

# ==================== ВСЕ РАБОЧИЕ КЛЮЧИ ====================

# BIGBASE (3 КЛЮЧА)
BIGBASE_KEY_1 = os.environ.get('BIGBASE_KEY_1', 'yhIkVgFWlT4ldeiauETMCFGkla7-VYtH')
BIGBASE_KEY_2 = os.environ.get('BIGBASE_KEY_2', 'IWTtHHz1lg_5XbYNHBWjiAtPiRrzpESM')
BIGBASE_KEY_3 = os.environ.get('BIGBASE_KEY_3', 'M9djfI8W3l-ozvCNsxPuLGONicsvgvnM')
BIGBASE_URL = os.environ.get('BIGBASE_URL', 'https://bigbase.top/api/search')

# DEPSEARCH
DEPSEARCH_TOKEN = os.environ.get('DEPSEARCH_TOKEN', 'OsMTcjyHTRtfABnWA4V3d12SYKVIYE8z')
DEPSEARCH_URL = os.environ.get('DEPSEARCH_URL', 'https://api.depsearch.sbs/quest')

# INFINITY (2 КЛЮЧА)
INFINITY_TOKEN_1 = os.environ.get('INFINITY_TOKEN_1', 'Bjm928HUcvsw923ZMBX19gd110FWSZgd')
INFINITY_TOKEN_2 = os.environ.get('INFINITY_TOKEN_2', 'QoNm98UeMLIqNjZ198snm98AdGvhqA88')
INFINITY_URL = os.environ.get('INFINITY_URL', 'https://infinity-search.fun/find.php')

# WHITE SEARCH
WHITESEARCH_KEY = os.environ.get('WHITESEARCH_KEY', 'WS-PUBLIC-9X7K-2M4P')
WHITESEARCH_URL = os.environ.get('WHITESEARCH_URL', 'https://api.whitesearch.workers.dev/api')

# JITLER
JITLER_TOKEN = os.environ.get('JITLER_TOKEN', '7M8wfVQlszWnbaaINN2ig7iA')
JITLER_URL = os.environ.get('JITLER_URL', 'https://api.jitler.top/search')

# LEAKCHECK
LEAKCHECK_KEY = os.environ.get('LEAKCHECK_KEY', '49535f49545f5245414c4c595f4150495f4b4559')
LEAKCHECK_URL = os.environ.get('LEAKCHECK_URL', 'https://leakcheck.net/api/public')

# SNUSBASE
SNUSBASE_KEY = os.environ.get('SNUSBASE_KEY', 'sb5029dec66mht55m78fx8bsw6tm8a')
SNUSBASE_URL = os.environ.get('SNUSBASE_URL', 'https://api.snusbase.com/v3/search')

# LEAKOSINT
LEAKOSINT_TOKEN = os.environ.get('LEAKOSINT_TOKEN', '8602726148:KHqZhmJC')
LEAKOSINT_URL = os.environ.get('LEAKOSINT_URL', 'https://leakosintapi.com/')

# FUNSTAT
FUNSTAT_TOKEN = os.environ.get('FUNSTAT_TOKEN', 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiIyMDMzMDI5NDc1IiwianRpIjoiODJmMjlmNzQtYmJlMi00ZGUwLWEwZDQtN2EzMDJhMWE5MDViIiwiZXhwIjoxODAxMDA4MzM4fQ.Mba4aX85YAMcaMLfhUBzXtCoNmEujfMe-6sGBbp3kT-T2SiLM_Ho0BBAFAQ8_C6Gz06PH9mAYhfBvlLSjb4oVd1Fm_vmb8MC-wuObU3qgfGrYdGzVF3ntJHv-LdNELq-jsqvQOY3jq9meso9dUoyj5SviDQWL6cvnRQ03kpHWxA')

# VERIPHONE
VERIPHONE_KEY = os.environ.get('VERIPHONE_KEY', 'D997B34B302B4A06B3AB815312852E51')
VERIPHONE_URL = os.environ.get('VERIPHONE_URL', 'https://api.veriphone.io/v2/verify')

# IPGEO
IPGEO_KEY = os.environ.get('IPGEO_KEY', '73d99145d2e948779263360bfeb67ecc')
IPGEO_URL = os.environ.get('IPGEO_URL', 'https://api.ipgeolocation.io/ipgeo')

# OFDATA
OFDATA_KEY = os.environ.get('OFDATA_KEY', 'KBnpz1CHKNngFXxK')
OFDATA_URL = os.environ.get('OFDATA_URL', 'https://api.ofdata.ru/v2/search')

# SMSC
SMSC_LOGIN = os.environ.get('SMSC_LOGIN', 'kirahacker333')
SMSC_PASSWORD = os.environ.get('SMSC_PASSWORD', 'Zangar5050')
SMSC_URL = os.environ.get('SMSC_URL', 'https://smsc.ru/sys/info.php')

# ==================== ПАРСЕРЫ ====================

# INTELX
INTELX_URL = os.environ.get('INTELX_URL', 'https://data.intelx.io/saverudata/')

# GETSCAM
GETSCAM_URL = os.environ.get('GETSCAM_URL', 'https://getscam.com')

# REVIEWS SITE
REVIEWS_URL = os.environ.get('REVIEWS_URL', 'https://xn---7-elctgilofd3b.xn--p1ai')

# GITHUB
GITHUB_URL = os.environ.get('GITHUB_URL', 'https://api.github.com/users')

# INSTAGRAM
INSTAGRAM_URL = os.environ.get('INSTAGRAM_URL', 'https://www.instagram.com')

# BINLIST
BINLIST_URL = os.environ.get('BINLIST_URL', 'https://lookup.binlist.net')

# MAC VENDORS
MACVENDORS_URL = os.environ.get('MACVENDORS_URL', 'https://api.macvendors.com')

# MINECRAFT
MINECRAFT_URL = os.environ.get('MINECRAFT_URL', 'https://api.mojang.com/users/profiles/minecraft')

# DOMAIN WHOIS
DOMAINWHOIS_URL = os.environ.get('DOMAINWHOIS_URL', 'https://api.hackertarget.com/whois/')

# DNS LOOKUP
DNSLOOKUP_URL = os.environ.get('DNSLOOKUP_URL', 'https://api.hackertarget.com/dnslookup/')

# ==================== РОТАТОРЫ ====================
bigbase_keys = [BIGBASE_KEY_1, BIGBASE_KEY_2, BIGBASE_KEY_3]
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

# ==================== ХРАНИЛИЩЕ ИСТОРИИ ====================
user_history = {}
MAX_HISTORY = 30

def get_history(user_id):
    if user_id not in user_history:
        user_history[user_id] = []
    return user_history[user_id]

def add_to_history(user_id, role, content):
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY:
        history.pop(0)

def clear_history(user_id):
    user_history[user_id] = []

# ==================== ФУНКЦИЯ СКРЫТИЯ ====================
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

# ==================== ПОИСКОВЫЕ ФУНКЦИИ ====================

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

def search_depsearch(query, search_type):
    type_map = {"phone": "phone", "email": "email", "fio": "name", "vk": "vk", "telegram": "telegram"}
    if search_type not in type_map:
        return {"source": "depsearch", "error": "Тип не поддерживается"}
    try:
        params = {"quest": query, "type": type_map[search_type], "token": DEPSEARCH_TOKEN}
        r = requests.get(DEPSEARCH_URL, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if "error" not in data:
                results = data.get("results", [])
                return {"source": "depsearch", "data": {"total": len(results), "results": results[:20]}}
            return {"source": "depsearch", "error": data.get("error")}
        return {"source": "depsearch", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "depsearch", "error": str(e)}

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
        "phone": "/search/phone",
        "email": "/search/email",
        "telegram": "/search/telegram",
        "telegram_id": "/search/telegram",
        "telegram_username": "/search/telegram",
        "vk": "/search/vk",
        "fio": "/search/fio",
        "ip": "/search/ip",
        "snils": "/search/snils",
        "inn": "/search/inn",
        "passport": "/search/passport",
        "auto": "/search/grz",
        "vin": "/search/vin"
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
                return {
                    "source": "white_search",
                    "data": {
                        "total": len(results_data) if isinstance(results_data, list) else 1,
                        "results": results_data if isinstance(results_data, list) else [results_data]
                    }
                }
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

def search_leakosint(query, limit=100):
    try:
        payload = {"token": LEAKOSINT_TOKEN, "request": query, "limit": limit, "lang": "ru"}
        r = requests.post(LEAKOSINT_URL, json=payload, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if "Error code" in data:
                return {"source": "leakosint", "error": data.get("Error code")}
            return {"source": "leakosint", "data": data}
        return {"source": "leakosint", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "leakosint", "error": str(e)}

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
            return {"source": "funstat", "data": {
                "id": data.id,
                "first_name": data.first_name,
                "last_name": data.last_name,
                "is_bot": data.is_bot,
                "is_active": data.is_active,
                "first_msg_date": data.first_msg_date,
                "last_msg_date": data.last_msg_date,
                "total_msg_count": data.total_msg_count,
                "msg_in_groups_count": data.msg_in_groups_count,
                "adm_in_groups": data.adm_in_groups,
                "total_groups": data.total_groups,
                "usernames_count": data.usernames_count,
                "names_count": data.names_count
            }}
        return {"source": "funstat", "error": "Пользователь не найден"}
    except Exception as e:
        return {"source": "funstat", "error": str(e)}

def search_veriphone(phone):
    try:
        r = requests.get(VERIPHONE_URL, params={"phone": phone, "key": VERIPHONE_KEY}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {"source": "veriphone", "data": {
                "valid": data.get("phone_valid", False),
                "country": data.get("country_name"),
                "region": data.get("phone_region"),
                "carrier": data.get("carrier")
            }}
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

def search_smsc():
    try:
        r = requests.get(SMSC_URL, params={"login": SMSC_LOGIN, "psw": SMSC_PASSWORD}, timeout=10)
        if r.status_code == 200:
            return {"source": "smsc", "data": r.text}
        return {"source": "smsc", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "smsc", "error": str(e)}

# ==================== ПАРСЕРЫ ====================

def search_intelx(phone):
    phone_clean = re.sub(r'\D', '', phone)
    if len(phone_clean) < 8:
        return {"source": "intelx", "error": "Номер слишком короткий"}
    url = f"{INTELX_URL}db2/dbpn/{phone_clean[:2]}/{phone_clean[2:4]}/{phone_clean[4:6]}/{phone_clean[6:8]}.csv"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
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

def search_getscam(query):
    try:
        r = requests.get(f"{GETSCAM_URL}/{query}", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            return {"source": "getscam", "data": r.text[:500]}
        return {"source": "getscam", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "getscam", "error": str(e)}

def search_reviews(query):
    try:
        r = requests.get(f"{REVIEWS_URL}/{query}", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            return {"source": "reviews", "data": r.text[:500]}
        return {"source": "reviews", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "reviews", "error": str(e)}

def search_github(username):
    try:
        r = requests.get(f"{GITHUB_URL}/{username}", timeout=10)
        if r.status_code == 200:
            return {"source": "github", "data": r.json()}
        return {"source": "github", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "github", "error": str(e)}

def search_instagram(username):
    try:
        r = requests.get(f"{INSTAGRAM_URL}/{username}/?__a=1", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            return {"source": "instagram", "data": r.text[:500]}
        return {"source": "instagram", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "instagram", "error": str(e)}

def search_binlist(bin):
    try:
        r = requests.get(f"{BINLIST_URL}/{bin}", timeout=10)
        if r.status_code == 200:
            return {"source": "binlist", "data": r.json()}
        return {"source": "binlist", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "binlist", "error": str(e)}

def search_macvendors(mac):
    try:
        r = requests.get(f"{MACVENDORS_URL}/{mac}", timeout=10)
        if r.status_code == 200:
            return {"source": "macvendors", "data": r.text.strip()}
        return {"source": "macvendors", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "macvendors", "error": str(e)}

def search_minecraft(username):
    try:
        r = requests.get(f"{MINECRAFT_URL}/{username}", timeout=10)
        if r.status_code == 200:
            return {"source": "minecraft", "data": r.json()}
        return {"source": "minecraft", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "minecraft", "error": str(e)}

def search_domainwhois(domain):
    try:
        r = requests.get(DOMAINWHOIS_URL, params={"q": domain}, timeout=10)
        if r.status_code == 200:
            return {"source": "domainwhois", "data": r.text}
        return {"source": "domainwhois", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "domainwhois", "error": str(e)}

def search_dnslookup(domain):
    try:
        r = requests.get(DNSLOOKUP_URL, params={"q": domain}, timeout=10)
        if r.status_code == 200:
            return {"source": "dnslookup", "data": r.text}
        return {"source": "dnslookup", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "dnslookup", "error": str(e)}

# ==================== ОПРЕДЕЛЕНИЕ ТИПА ====================
def detect_type(query: str) -> Tuple[str, Optional[str]]:
    query = query.strip()
    if not query:
        return "unknown", None

    auto_clean = re.sub(r'\s+', '', query.upper())
    auto_patterns = [
        r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$',
        r'^[АВЕКМНОРСТУХ]{2}\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$',
        r'^[A-Z]\d{3}[A-Z]{2}\d{2,3}$',
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

# ============================================
# ГЛАВНЫЙ ЭНДПОИНТ ПОИСКА
# ============================================
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

    # BIGBASE
    if search_type in ["phone", "email", "fio", "auto", "inn", "passport", "ip"]:
        try:
            result["sources"].append(search_bigbase(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "bigbase", "error": str(e)})

    # DEPSEARCH
    if search_type in ["phone", "email", "fio", "vk", "telegram"]:
        try:
            result["sources"].append(search_depsearch(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "depsearch", "error": str(e)})

    # INFINITY
    if search_type in ["phone", "email", "fio"]:
        try:
            result["sources"].append(search_infinity(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "infinity", "error": str(e)})

    # WHITE SEARCH
    if search_type in ["phone", "email", "fio", "telegram", "telegram_id", "telegram_username", "vk", "ip", "snils", "inn", "passport", "auto", "vin"]:
        try:
            result["sources"].append(search_white_search(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "white_search", "error": str(e)})

    # JITLER
    if search_type in ["phone", "telegram", "telegram_id", "telegram_username", "vk"]:
        try:
            result["sources"].append(search_jitler(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "jitler", "error": str(e)})

    # LEAKCHECK
    if search_type in ["email", "phone"]:
        try:
            result["sources"].append(search_leakcheck(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "leakcheck", "error": str(e)})

    # SNUSBASE
    if search_type in ["email", "fio", "ip"]:
        try:
            result["sources"].append(search_snusbase(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "snusbase", "error": str(e)})

    # LEAKOSINT
    try:
        result["sources"].append(search_leakosint(query))
    except Exception as e:
        result["sources"].append({"source": "leakosint", "error": str(e)})

    # FUNSTAT
    if search_type in ["telegram", "telegram_id"] and query.isdigit():
        try:
            result["sources"].append(search_funstat(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "funstat", "error": str(e)})

    # VERIPHONE
    if search_type == "phone":
        try:
            result["sources"].append(search_veriphone(query))
        except Exception as e:
            result["sources"].append({"source": "veriphone", "error": str(e)})

    # IPGEO
    if search_type == "ip":
        try:
            result["sources"].append(search_ipgeo(query))
        except Exception as e:
            result["sources"].append({"source": "ipgeo", "error": str(e)})

    # OFDATA
    if search_type in ["inn", "ogrn", "fio", "company"]:
        try:
            result["sources"].append(search_ofdata(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "ofdata", "error": str(e)})

    # INTELX (ПАРСЕР)
    if search_type == "phone":
        try:
            result["sources"].append(search_intelx(query))
        except Exception as e:
            result["sources"].append({"source": "intelx", "error": str(e)})

    # GETSCAM (ПАРСЕР)
    if search_type == "phone":
        try:
            result["sources"].append(search_getscam(query))
        except Exception as e:
            result["sources"].append({"source": "getscam", "error": str(e)})

    # REVIEWS (ПАРСЕР)
    if search_type == "phone":
        try:
            result["sources"].append(search_reviews(query))
        except Exception as e:
            result["sources"].append({"source": "reviews", "error": str(e)})

    # GITHUB (ПАРСЕР)
    if search_type == "username":
        try:
            result["sources"].append(search_github(query))
        except Exception as e:
            result["sources"].append({"source": "github", "error": str(e)})

    # INSTAGRAM (ПАРСЕР)
    if search_type == "username":
        try:
            result["sources"].append(search_instagram(query))
        except Exception as e:
            result["sources"].append({"source": "instagram", "error": str(e)})

    # BINLIST (ПАРСЕР)
    if re.match(r'^\d{6,8}$', query):
        try:
            result["sources"].append(search_binlist(query))
        except Exception as e:
            result["sources"].append({"source": "binlist", "error": str(e)})

    # MAC VENDORS (ПАРСЕР)
    if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', query):
        try:
            result["sources"].append(search_macvendors(query))
        except Exception as e:
            result["sources"].append({"source": "macvendors", "error": str(e)})

    # MINECRAFT (ПАРСЕР)
    if search_type == "username":
        try:
            result["sources"].append(search_minecraft(query))
        except Exception as e:
            result["sources"].append({"source": "minecraft", "error": str(e)})

    # DOMAIN WHOIS (ПАРСЕР)
    if search_type == "domain":
        try:
            result["sources"].append(search_domainwhois(query))
        except Exception as e:
            result["sources"].append({"source": "domainwhois", "error": str(e)})

    # DNS LOOKUP (ПАРСЕР)
    if search_type == "domain":
        try:
            result["sources"].append(search_dnslookup(query))
        except Exception as e:
            result["sources"].append({"source": "dnslookup", "error": str(e)})

    return jsonify(result)

# ============================================
# HEALTH
# ============================================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

# ============================================
# ROOT
# ============================================
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "name": "DeepTrek API",
        "version": "22.0",
        "description": "OSINT-агрегатор со всеми парсерами",
        "author": "@kmyfg",
        "sources": [
            "BigBase (3 ключа)",
            "DepSearch",
            "Infinity (2 ключа)",
            "White Search",
            "Jitler",
            "LeakCheck",
            "Snusbase",
            "LeakOSINT",
            "Funstat",
            "Veriphone",
            "IpGeo",
            "OFDATA",
            "SMSC",
            "IntelX (парсер)",
            "GetScam (парсер)",
            "Reviews (парсер)",
            "GitHub (парсер)",
            "Instagram (парсер)",
            "BinList (парсер)",
            "MAC Vendors (парсер)",
            "Minecraft (парсер)",
            "Domain WHOIS (парсер)",
            "DNS Lookup (парсер)"
        ],
        "total_sources": 23
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)