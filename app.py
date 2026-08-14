from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import re
import time
import csv
import io
from datetime import datetime
from typing import Tuple, Optional
from funstat_api import FunstatClient

app = Flask(__name__)
CORS(app)

# ==================== КОНФИГ ====================
MASTER_KEY = "deeptrek_fjnrndhfrb2947472992gdvsbdh"

# ==================== ВСЕ КЛЮЧИ ====================

# VK
VK_TOKEN = "0af157510af157510af15751aa0a89e69600af10af157516a0bc15996e74fe2b440998c"
VK_API = "https://api.vk.com/method/users.get"

# SNUSBASE
SNUSBASE_KEY = "sbmeovhou6ecsn9fd9wcwnwwvsvwnc"
SNUSBASE_URL = "https://api.snusbase.com/data/search"

# PROXYCHECK
PROXYCHECK_KEY = "9fcd3e6622f96a780f0908ce414bb16360d3779d8253f484f319e02cc5c25065"
PROXYCHECK_URL = "https://proxycheck.io/v2/"

# ABUSEIPDB
ABUSEIPDB_KEY = "58878ed65228db88eddfda4983bce5d19d425ddf81f427857b3f59f11aecc34f127862a1cc7d4581"
ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"

# HUDSON ROCK
HUDSON_IP_URL = "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-ip"
HUDSON_USERNAME_URL = "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-username"
HUDSON_EMAIL_URL = "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-email"

# PROXYNOVA
PROXYNOVA_URL = "https://api.proxynova.com/comb"

# WHOIS
WHOIS_URL = "https://www.whois.com/whois"

# IP2LOCATION
IP2LOCATION_KEY = "965108E0429BB3E9329066D8D015564C"
IP2LOCATION_URL = "https://api.ip2location.io"

# BIGBASE
BIGBASE_KEY = "8JsPp38dXVdQI5OAXxQlwgQRNvhcDD2Q"
BIGBASE_URL = "https://bigbase.top/api/search"

# JITLER
JITLER_TOKEN = "kcWgDpRlesD30v6SvqeLOejO"
JITLER_URL = "https://api.jitler.top"

# INFINITY
INFINITY_TOKEN = "Bjm928HUcvsw923ZMBX19gd110FWSZgd"
INFINITY_URL = "https://infinity-search.fun/find.php"

# WHITE SEARCH
WHITE_SEARCH_KEY = "WS-PUBLIC-9X7K-2M4P"
WHITE_SEARCH_URL = "https://api.whitesearch.workers.dev/api"

# FUNSTAT
FUNSTAT_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiI4NDkwNjcxMTE3IiwianRpIjoiYzk0MjAwNDktYTNhNi00ZjgwLTkwZjItYzAxOTllNWQ3ZjdlIiwiZXhwIjoxODExNDQwNTkzfQ.ZtAs0h5SnD-INsbBALHO9L6u7Owzb8oZeOQQdM5trWkG-5W5S2sWAzTRXVMNaZOrYXsGOekr4bARBFYVudASyC2tTx7HmJqHivn0gzdeUXvi3V-L6_YGWg87QSbfr-qEtqp2OJwolSgudgeNuMEn3AGpSM1Cb8N99oRDX5pFEiQ"

# OFDATA
OFDATA_KEY = "KBnpz1CHKNngFXxK"
OFDATA_URL = "https://api.ofdata.ru/v2/search"

# SMSC
SMSC_LOGIN = "kirahacker333"
SMSC_PASSWORD = "Zangar5050"
SMSC_URL = "https://smsc.ru/sys/info.php"

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

# ==================== ОПРЕДЕЛЕНИЕ ТИПА ====================
def detect_type(query: str) -> Tuple[str, Optional[str]]:
    query = query.strip()
    if not query:
        return "unknown", None
    
    # ГРЗ (госномер) — СНАЧАЛА, ЧТОБЫ НЕ ПЕРЕПУТАТЬ С ДРУГИМИ ТИПАМИ
    # Форматы: А999АА99, А999АА199, АА999АА99 и т.д.
    auto_clean = re.sub(r'\s+', '', query.upper())
    auto_patterns = [
        r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$',
        r'^[АВЕКМНОРСТУХ]{2}\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$',
        r'^[A-Z]\d{3}[A-Z]{2}\d{2,3}$',  # Латиница для грузин/армян
    ]
    for pattern in auto_patterns:
        if re.match(pattern, auto_clean):
            return "auto", auto_clean
    
    # VIN (17 символов, буквы+цифры, без I/O/Q)
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
    
    return "username", query

def check_api_key():
    return request.headers.get('X-API-Key') == MASTER_KEY

# ==================== ПОИСКОВЫЕ ФУНКЦИИ ====================

# ===== WHITE SEARCH =====
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
        return {"source": "white_search", "error": "Тип не поддерживается"}
    
    try:
        endpoint = type_map[search_type]
        url = f"{WHITE_SEARCH_URL}{endpoint}"
        headers = {"X-API-Key": WHITE_SEARCH_KEY}
        
        params = {}
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
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
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
        elif response.status_code == 429:
            return {"source": "white_search", "error": "Дневной лимит исчерпан"}
        return {"source": "white_search", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"source": "white_search", "error": str(e)}

# ===== INFINITY =====
def search_infinity(query, search_type):
    if search_type not in ["phone", "email", "fio", "auto"]:
        return {"source": "infinity", "error": "Тип не поддерживается"}
    try:
        params = {"token": INFINITY_TOKEN, search_type: query}
        r = requests.get(INFINITY_URL, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("results"):
                return {"source": "infinity", "data": {"total": len(data["results"]), "results": data["results"][:20]}}
            return {"source": "infinity", "error": "Ничего не найдено"}
        return {"source": "infinity", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "infinity", "error": str(e)}

# ===== BIGBASE =====
def search_bigbase(query, search_type):
    type_map = {
        "phone": "phone",
        "email": "email",
        "fio": "fio",
        "auto": "auto",
        "inn": "inn",
        "passport": "passport",
        "ip": "ip",
        "vin": "vin"
    }
    if search_type not in type_map:
        return {"source": "bigbase", "error": "Тип не поддерживается"}
    try:
        headers = {"Authorization": BIGBASE_KEY, "Content-Type": "application/json"}
        data = {"search": query, "type": type_map[search_type], "page": 1}
        r = requests.post(BIGBASE_URL, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            result = r.json()
            result = sanitize_bigbase(result)
            return {"source": "bigbase", "data": result}
        return {"source": "bigbase", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "bigbase", "error": str(e)}

# ===== JITLER =====
def search_jitler(query, search_type):
    if search_type not in ["telegram", "telegram_id", "telegram_username"]:
        return {"source": "jitler", "error": "Jitler поддерживает только поиск по Telegram"}
    try:
        headers = {"Authorization": f"Bearer {JITLER_TOKEN}", "Content-Type": "application/json"}
        payload = {"type": "sherlock", "query": query, "page": 1}
        r = requests.post(f"{JITLER_URL}/search", headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            data = r.json()
            response = data.get("response", {})
            return {"source": "jitler", "data": {"telegram": response.get("telegram", []), "phonebooks": response.get("phonebooks", []), "profiles": response.get("profiles", {}), "raw": response.get("raw", ""), "counts": response.get("counts", {})}}
        return {"source": "jitler", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "jitler", "error": str(e)}

def search_jitler_phone(query):
    try:
        headers = {"Authorization": f"Bearer {JITLER_TOKEN}", "Content-Type": "application/json"}
        payload = {"type": "number", "query": query, "page": 1}
        r = requests.post(f"{JITLER_URL}/search", headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return {"source": "jitler_phone", "data": r.json().get("response", {})}
        return {"source": "jitler_phone", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "jitler_phone", "error": str(e)}

# ===== INTELX =====
def search_intelx_phone(phone):
    try:
        phone_clean = re.sub(r'\D', '', phone)
        if len(phone_clean) < 8:
            return {"source": "intelx", "error": "Номер слишком короткий"}
        url = f'https://data.intelx.io/saverudata/db2/dbpn/{phone_clean[:2]}/{phone_clean[2:4]}/{phone_clean[4:6]}/{phone_clean[6:8]}.csv'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            csv_data = list(csv.reader(io.StringIO(response.text)))
            if len(csv_data) > 1:
                headers_row = csv_data[0]
                results = []
                for row in csv_data[1:]:
                    row_text = ' '.join(row)
                    if phone_clean in row_text:
                        result = {}
                        for idx, value in enumerate(row):
                            if idx < len(headers_row) and value:
                                result[headers_row[idx]] = value
                        results.append(result)
                if results:
                    return {"source": "intelx", "data": {"total": len(results), "results": results[:20]}}
                return {"source": "intelx", "error": "Номер не найден"}
            return {"source": "intelx", "error": "CSV пустой"}
        return {"source": "intelx", "error": f"Данных нет (HTTP {response.status_code})"}
    except Exception as e:
        return {"source": "intelx", "error": str(e)}

# ===== VK =====
def search_vk(query):
    try:
        params = {"access_token": VK_TOKEN, "v": "5.131", "user_ids": query, "fields": "first_name,last_name,status,sex,country"}
        r = requests.get(VK_API, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if "response" in data and data["response"]:
                return {"source": "vk", "data": data["response"]}
        return {"source": "vk", "error": "Пользователь не найден"}
    except Exception as e:
        return {"source": "vk", "error": str(e)}

# ===== SNUSBASE =====
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

# ===== ABUSEIPDB =====
def search_abuseipdb(ip):
    try:
        headers = {"Key": ABUSEIPDB_KEY, "Accept": "application/json"}
        params = {"ipAddress": ip, "maxAgeInDays": 90}
        r = requests.get(ABUSEIPDB_URL, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", {})
            return {"source": "abuseipdb", "data": {"ip": data.get("ipAddress"), "country": data.get("countryCode"), "isp": data.get("isp"), "confidence": data.get("abuseConfidenceScore"), "reports": data.get("totalReports")}}
        return {"source": "abuseipdb", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "abuseipdb", "error": str(e)}

# ===== PROXYCHECK =====
def search_proxycheck(ip):
    try:
        r = requests.get(f"{PROXYCHECK_URL}{ip}", params={"key": PROXYCHECK_KEY}, timeout=10)
        if r.status_code == 200:
            return {"source": "proxycheck", "data": r.json()}
        return {"source": "proxycheck", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "proxycheck", "error": str(e)}

# ===== HUDSON ROCK =====
def search_hudson_ip(ip):
    try:
        r = requests.get(HUDSON_IP_URL, params={"ip": ip}, timeout=15)
        if r.status_code == 200:
            return {"source": "hudson_ip", "data": r.json()}
        return {"source": "hudson_ip", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "hudson_ip", "error": str(e)}

def search_hudson_username(username):
    try:
        r = requests.get(HUDSON_USERNAME_URL, params={"username": username}, timeout=15)
        if r.status_code == 200:
            return {"source": "hudson_username", "data": r.json()}
        return {"source": "hudson_username", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "hudson_username", "error": str(e)}

def search_hudson_email(email):
    try:
        r = requests.get(HUDSON_EMAIL_URL, params={"email": email}, timeout=15)
        if r.status_code == 200:
            return {"source": "hudson_email", "data": r.json()}
        return {"source": "hudson_email", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "hudson_email", "error": str(e)}

# ===== PROXYNOVA =====
def search_proxynova(query):
    try:
        r = requests.get(PROXYNOVA_URL, params={"query": query, "start": 0, "limit": 100}, timeout=15)
        if r.status_code == 200:
            return {"source": "proxynova", "data": r.json()}
        return {"source": "proxynova", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "proxynova", "error": str(e)}

# ===== IP2LOCATION =====
def search_ip2location(ip):
    try:
        r = requests.get(IP2LOCATION_URL, params={"key": IP2LOCATION_KEY, "ip": ip}, timeout=10)
        if r.status_code == 200:
            return {"source": "ip2location", "data": r.json()}
        return {"source": "ip2location", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "ip2location", "error": str(e)}

# ===== WHOIS =====
def search_whois(ip):
    try:
        r = requests.get(f"{WHOIS_URL}/{ip}", timeout=15)
        if r.status_code == 200:
            return {"source": "whois", "data": r.text[:500]}
        return {"source": "whois", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "whois", "error": str(e)}

# ===== OFDATA =====
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

# ===== FUNSTAT =====
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

# ===== SMSC =====
def search_smsc():
    try:
        r = requests.get(SMSC_URL, params={"login": SMSC_LOGIN, "psw": SMSC_PASSWORD}, timeout=10)
        if r.status_code == 200:
            return {"source": "smsc", "data": r.text}
        return {"source": "smsc", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "smsc", "error": str(e)}

# ==================== ГЛАВНЫЙ ЭНДПОИНТ ====================
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
    
    # ===== WHITE SEARCH (ВКЛЮЧАЕТ ГРЗ И VIN) =====
    if search_type in ["phone", "email", "fio", "telegram", "telegram_id", "telegram_username", "vk", "ip", "snils", "inn", "passport", "auto", "vin"]:
        try:
            result["sources"].append(search_white_search(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "white_search", "error": str(e)})
    
    # ===== INFINITY (ПОДДЕРЖИВАЕТ ГРЗ) =====
    if search_type in ["phone", "email", "fio", "auto"]:
        try:
            result["sources"].append(search_infinity(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "infinity", "error": str(e)})
    
    # ===== BIGBASE (ПОДДЕРЖИВАЕТ ГРЗ И VIN) =====
    if search_type in ["phone", "email", "fio", "auto", "inn", "passport", "ip", "vin"]:
        try:
            result["sources"].append(search_bigbase(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "bigbase", "error": str(e)})
    
    # ===== JITLER =====
    if search_type in ["telegram", "telegram_id", "telegram_username"]:
        try:
            result["sources"].append(search_jitler(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "jitler", "error": str(e)})
    if search_type == "phone":
        try:
            result["sources"].append(search_jitler_phone(query))
        except Exception as e:
            result["sources"].append({"source": "jitler_phone", "error": str(e)})
    
    # ===== INTELX =====
    if search_type == "phone":
        try:
            result["sources"].append(search_intelx_phone(query))
        except Exception as e:
            result["sources"].append({"source": "intelx", "error": str(e)})
    
    # ===== VK =====
    if search_type == "vk":
        try:
            result["sources"].append(search_vk(query))
        except Exception as e:
            result["sources"].append({"source": "vk", "error": str(e)})
    
    # ===== SNUSBASE =====
    if search_type in ["email", "fio", "ip"]:
        try:
            result["sources"].append(search_snusbase(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "snusbase", "error": str(e)})
    
    # ===== ABUSEIPDB =====
    if search_type == "ip":
        try:
            result["sources"].append(search_abuseipdb(query))
        except Exception as e:
            result["sources"].append({"source": "abuseipdb", "error": str(e)})
    
    # ===== PROXYCHECK =====
    if search_type == "ip":
        try:
            result["sources"].append(search_proxycheck(query))
        except Exception as e:
            result["sources"].append({"source": "proxycheck", "error": str(e)})
    
    # ===== HUDSON ROCK =====
    if search_type == "ip":
        try:
            result["sources"].append(search_hudson_ip(query))
        except Exception as e:
            result["sources"].append({"source": "hudson_ip", "error": str(e)})
    if search_type == "username":
        try:
            result["sources"].append(search_hudson_username(query))
        except Exception as e:
            result["sources"].append({"source": "hudson_username", "error": str(e)})
    if search_type == "email":
        try:
            result["sources"].append(search_hudson_email(query))
        except Exception as e:
            result["sources"].append({"source": "hudson_email", "error": str(e)})
    
    # ===== PROXYNOVA =====
    if search_type in ["email", "fio", "username"]:
        try:
            result["sources"].append(search_proxynova(query))
        except Exception as e:
            result["sources"].append({"source": "proxynova", "error": str(e)})
    
    # ===== IP2LOCATION =====
    if search_type == "ip":
        try:
            result["sources"].append(search_ip2location(query))
        except Exception as e:
            result["sources"].append({"source": "ip2location", "error": str(e)})
    
    # ===== WHOIS =====
    if search_type == "ip":
        try:
            result["sources"].append(search_whois(query))
        except Exception as e:
            result["sources"].append({"source": "whois", "error": str(e)})
    
    # ===== OFDATA =====
    if search_type in ["inn", "ogrn", "fio", "company"]:
        try:
            result["sources"].append(search_ofdata(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "ofdata", "error": str(e)})
    
    # ===== FUNSTAT =====
    if search_type in ["telegram", "telegram_id"] and query.isdigit():
        try:
            result["sources"].append(search_funstat(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "funstat", "error": str(e)})
    
    return jsonify(result)

# ==================== TEMPMAIL ====================
@app.route('/tempmail/generate', methods=['GET'])
def tempmail_generate():
    if not check_api_key():
        return jsonify({"error": "Неверный API-ключ"}), 403
    try:
        r = requests.get("https://api.tempmail.lol/generate", timeout=10)
        return jsonify(r.json()) if r.status_code == 200 else jsonify({"error": f"HTTP {r.status_code}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tempmail/check/<token>', methods=['GET'])
def tempmail_check(token):
    if not check_api_key():
        return jsonify({"error": "Неверный API-ключ"}), 403
    try:
        r = requests.get(f"https://api.tempmail.lol/messages/{token}", timeout=10)
        return jsonify(r.json()) if r.status_code == 200 else jsonify({"error": f"HTTP {r.status_code}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== HEALTH ====================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "name": "DeepTrek API",
        "version": "14.0",
        "description": "OSINT-агрегатор со всеми рабочими источниками, включая ГРЗ и VIN",
        "author": "@kmyfg",
        "sources": [
            "White Search (ГРЗ, VIN, телефон, email, ФИО, Telegram, VK, IP, СНИЛС, ИНН)",
            "Infinity (ГРЗ, телефон, email, ФИО)",
            "BigBase (ГРЗ, VIN, телефон, email, ФИО, ИНН, паспорт, IP)",
            "Jitler, IntelX, VK, Snusbase, AbuseIPDB, Proxycheck, Hudson Rock, Proxynova, IP2Location, Whois, OFDATA, Funstat, SMSC"
        ],
        "total_sources": 16,
        "search_types": [
            "phone", "email", "fio", "telegram", "telegram_id", "telegram_username",
            "vk", "ip", "snils", "inn", "passport", "auto (ГРЗ)", "vin"
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
