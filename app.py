from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import re
import csv
import io
import time
from datetime import datetime
from typing import Tuple, Optional

app = Flask(__name__)
CORS(app)

# ==================== КОНФИГ ====================
MASTER_KEY = "deeptrek_fjnrndhfrb2947472992gdvsbdh"

# BIGBASE (ОСНОВНОЙ)
BIGBASE_KEY = "8JsPp38dXVdQI5OAXxQlwgQRNvhcDD2Q"
BIGBASE_URL = "https://bigbase.top/api/search"

# ANYSCAN (duckdns)
ANYSCAN_TOKEN = "oxYKwwEN2kvMyG7advJ3DQ"
ANYSCAN_URL = "https://anyscan.duckdns.org/api/v1/search"

# JITLER
JITLER_TOKEN = "kcWgDpRlesD30v6SvqeLOejO"
JITLER_URL = "https://api.jitler.top"

# VK
VK_TOKEN = "0af157510af157510af15751aa0a89e69600af10af157516a0bc15996e74fe2b440998c"
VK_API = "https://api.vk.com/method/users.get"

# ABUSEIPDB
ABUSEIPDB_KEY = "58878ed65228db88eddfda4983bce5d19d425ddf81f427857b3f59f11aecc34f127862a1cc7d4581"
ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"

# OFDATA
OFDATA_KEY = "KBnpz1CHKNngFXxK"
OFDATA_URL = "https://api.ofdata.ru/v2/search"

# SNUSBASE
SNUSBASE_KEY = "sbmeovhou6ecsn9fd9wcwnwwvsvwnc"
SNUSBASE_URL = "https://api.snusbase.com/data/search"

# CERERA (если будет баланс)
CERERA_TOKEN = "ca_4oOeTcjU0dYTU_O6yl1Spg5s2JzseZEzVr2_dYL7rmI"
CERERA_URL = "https://cerera.cc/api"

# ==================== LEAKOSINT (ВРЕМЕННО ОТКЛЮЧЁН) ====================
# LEAKOSINT_TOKEN = "76572095882:app:WRfKwOvV"
# LEAKOSINT_URL = "https://leakosintapi.com/"

# ==================== ФУНКЦИЯ СКРЫТИЯ ====================
def sanitize_response(data):
    """Скрывает логин и токен в ответе"""
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
                sanitize_response(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        sanitize_response(item)
    return data

# ==================== ОПРЕДЕЛЕНИЕ ТИПА ====================
def detect_type(query: str) -> Tuple[str, Optional[str]]:
    query = query.strip()
    if not query:
        return "unknown", None
    
    # Email
    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', query):
        return "email", query.lower()
    
    # IP
    ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    if re.match(ip_pattern, query):
        return "ip", query
    
    # Телефон
    phone_clean = re.sub(r'[\s()+-]', '', query)
    if re.match(r'^(7|8|9)\d{10}$', phone_clean):
        if phone_clean.startswith('8'):
            phone_clean = '7' + phone_clean[1:]
        elif phone_clean.startswith('9'):
            phone_clean = '7' + phone_clean
        return "phone", phone_clean
    
    # VK
    if query.lower().startswith('id') and query[2:].isdigit():
        return "vk", query[2:]
    
    # Автономер
    auto_clean = re.sub(r'\s+', '', query.upper())
    auto_patterns = [
        r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$',
        r'^[АВЕКМНОРСТУХ]{2}\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$',
    ]
    for pattern in auto_patterns:
        if re.match(pattern, auto_clean):
            return "auto", auto_clean
    
    # ИНН
    if re.match(r'^\d{10}$', query) or re.match(r'^\d{12}$', query):
        return "inn", query
    
    # СНИЛС
    snils_clean = re.sub(r'[\s-]', '', query)
    if re.match(r'^\d{11}$', snils_clean):
        return "snils", snils_clean
    
    # Паспорт
    passport_clean = re.sub(r'[\s-]', '', query)
    if re.match(r'^\d{4}\d{6}$', passport_clean):
        return "passport", passport_clean
    
    # ФИО
    if re.search(r'[а-яА-Я]', query):
        words = query.split()
        if len(words) >= 2:
            return "fio", query
    
    return "username", query

def check_api_key():
    return request.headers.get('X-API-Key') == MASTER_KEY

# ==================== BIGBASE (ОСНОВНОЙ) ====================
def search_bigbase(query, search_type):
    headers = {
        "Authorization": BIGBASE_KEY,
        "Content-Type": "application/json"
    }
    data = {"search": query}
    if search_type:
        data["type"] = search_type
    
    try:
        r = requests.post(BIGBASE_URL, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            result = r.json()
            result = sanitize_response(result)
            return {"source": "bigbase", "data": result}
        elif r.status_code == 402:
            return {"source": "bigbase", "error": "Недостаточно средств"}
        elif r.status_code == 403:
            return {"source": "bigbase", "error": "Неверный ключ"}
        else:
            return {"source": "bigbase", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "bigbase", "error": str(e)}

# ==================== ОСТАЛЬНЫЕ ИСТОЧНИКИ ====================
def search_anyscan(query, search_type):
    type_map = {"phone": "phone", "email": "email", "fio": "name", "inn": "inn", "snils": "snils", "passport": "passport"}
    if search_type not in type_map:
        return {"source": "anyscan", "error": "Тип не поддерживается"}
    headers = {"Authorization": f"Bearer {ANYSCAN_TOKEN}", "Content-Type": "application/json"}
    data = {"type": type_map[search_type], "q": query, "limit": 100}
    try:
        r = requests.post(ANYSCAN_URL, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            return {"source": "anyscan", "data": r.json()}
        return {"source": "anyscan", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "anyscan", "error": str(e)}

def search_jitler(query, search_type):
    type_map = {"phone": "number", "telegram_username": "sherlock", "telegram_id": "sherlock", "vk": "vks"}
    if search_type not in type_map:
        return {"source": "jitler", "error": "Тип не поддерживается"}
    headers = {"Authorization": f"Bearer {JITLER_TOKEN}", "Content-Type": "application/json"}
    data = {"type": type_map[search_type], "query": query, "page": 1}
    try:
        r = requests.post(f"{JITLER_URL}/search", headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            return {"source": "jitler", "data": r.json()}
        return {"source": "jitler", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "jitler", "error": str(e)}

def search_vk(query):
    params = {"access_token": VK_TOKEN, "v": "5.131", "user_ids": query, "fields": "first_name,last_name,status,sex,country"}
    try:
        r = requests.get(VK_API, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if "response" in data and data["response"]:
                return {"source": "vk", "data": data["response"]}
        return {"source": "vk", "error": "Пользователь не найден"}
    except Exception as e:
        return {"source": "vk", "error": str(e)}

def search_abuseipdb(ip):
    headers = {"Key": ABUSEIPDB_KEY, "Accept": "application/json"}
    params = {"ipAddress": ip, "maxAgeInDays": 90}
    try:
        r = requests.get(ABUSEIPDB_URL, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", {})
            return {"source": "abuseipdb", "data": {"ip": data.get("ipAddress"), "country": data.get("countryCode"), "isp": data.get("isp"), "confidence": data.get("abuseConfidenceScore"), "reports": data.get("totalReports")}}
        return {"source": "abuseipdb", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "abuseipdb", "error": str(e)}

def search_ofdata(query, search_type):
    if search_type not in ["inn", "ogrn", "fio", "company"]:
        return {"source": "ofdata", "error": "Тип не поддерживается"}
    by = search_type if search_type in ["inn", "ogrn"] else "name"
    obj = "org" if search_type in ["inn", "ogrn", "company"] else "ent"
    url = f"{OFDATA_URL}?key={OFDATA_KEY}&by={by}&obj={obj}&query={query}&limit=10"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("data", {}).get("Записи"):
                return {"source": "ofdata", "data": data}
            return {"source": "ofdata", "error": "Ничего не найдено"}
        return {"source": "ofdata", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "ofdata", "error": str(e)}

def search_snusbase(query, search_type):
    if search_type not in ["email", "fio", "ip"]:
        return {"source": "snusbase", "error": "Тип не поддерживается"}
    snus_type = "ip" if search_type == "ip" else search_type
    if search_type == "fio":
        snus_type = "username"
    payload = {"terms": [query], "types": [snus_type], "wildcard": False}
    headers = {"Auth": SNUSBASE_KEY, "Content-Type": "application/json"}
    try:
        r = requests.post(SNUSBASE_URL, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return {"source": "snusbase", "data": r.json()}
        return {"source": "snusbase", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "snusbase", "error": str(e)}

def search_cerera(query, search_type):
    valid_types = ["phone", "fio", "email", "vk", "inn", "snils", "passport", "auto", "vin", "ip"]
    if search_type not in valid_types:
        return {"source": "cerera", "error": "Тип не поддерживается"}
    params = {"token": CERERA_TOKEN, "type": search_type, "q": query}
    try:
        r = requests.get(CERERA_URL, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "success":
                return {"source": "cerera", "data": data.get("data"), "balance": data.get("remaining_balance")}
            return {"source": "cerera", "error": data.get("error", "Неизвестная ошибка")}
        return {"source": "cerera", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "cerera", "error": str(e)}

# ==================== LEAKOSINT (ВРЕМЕННО ОТКЛЮЧЁН) ====================
# def search_leakosint(query, limit=100, lang="ru"):
#     data = {
#         "token": LEAKOSINT_TOKEN,
#         "request": query,
#         "limit": limit,
#         "lang": lang
#     }
#     try:
#         r = requests.post(LEAKOSINT_URL, json=data, timeout=30)
#         if r.status_code == 200:
#             result = r.json()
#             if "Error code" in result:
#                 return {"source": "leakosint", "error": f"{result.get('Error code')}: {result.get('Message', '')}"}
#             return {"source": "leakosint", "data": result}
#         return {"source": "leakosint", "error": f"HTTP {r.status_code}"}
#     except Exception as e:
#         return {"source": "leakosint", "error": str(e)}

# ==================== ПОИСК ====================
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
    
    # BIGBASE (ОСНОВНОЙ)
    if search_type in ["phone", "email", "fio", "auto", "inn", "passport", "ip"]:
        try:
            result["sources"].append(search_bigbase(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "bigbase", "error": str(e)})
    
    # ANYSCAN
    if search_type in ["phone", "email", "fio", "inn", "snils", "passport"]:
        try:
            result["sources"].append(search_anyscan(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "anyscan", "error": str(e)})
    
    # JITLER
    if search_type in ["phone", "vk", "telegram_username", "telegram_id"]:
        try:
            result["sources"].append(search_jitler(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "jitler", "error": str(e)})
    
    # VK
    if search_type == "vk":
        try:
            result["sources"].append(search_vk(query))
        except Exception as e:
            result["sources"].append({"source": "vk", "error": str(e)})
    
    # ABUSEIPDB
    if search_type == "ip":
        try:
            result["sources"].append(search_abuseipdb(query))
        except Exception as e:
            result["sources"].append({"source": "abuseipdb", "error": str(e)})
    
    # OFDATA
    if search_type in ["inn", "ogrn", "fio", "company"]:
        try:
            result["sources"].append(search_ofdata(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "ofdata", "error": str(e)})
    
    # SNUSBASE
    if search_type in ["email", "fio", "ip"]:
        try:
            result["sources"].append(search_snusbase(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "snusbase", "error": str(e)})
    
    # CERERA
    if search_type in ["phone", "email", "fio", "vk", "inn", "snils", "passport", "auto", "vin", "ip"]:
        try:
            result["sources"].append(search_cerera(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "cerera", "error": str(e)})
    
    # LEAKOSINT (ВРЕМЕННО ОТКЛЮЧЁН)
    # if search_type in ["phone", "email", "fio", "username", "vk", "inn", "snils", "passport", "auto"]:
    #     try:
    #         result["sources"].append(search_leakosint(query))
    #     except Exception as e:
    #         result["sources"].append({"source": "leakosint", "error": str(e)})
    
    return jsonify(result)

# ==================== TEMPMAIL ====================
@app.route('/tempmail/generate', methods=['GET'])
def tempmail_generate():
    if not check_api_key():
        return jsonify({"error": "Неверный API-ключ"}), 403
    try:
        r = requests.get("https://api.tempmail.lol/generate", timeout=10)
        if r.status_code == 200:
            return jsonify(r.json())
        return jsonify({"error": f"HTTP {r.status_code}"}), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tempmail/check/<token>', methods=['GET'])
def tempmail_check(token):
    if not check_api_key():
        return jsonify({"error": "Неверный API-ключ"}), 403
    try:
        r = requests.get(f"https://api.tempmail.lol/messages/{token}", timeout=10)
        if r.status_code == 200:
            return jsonify(r.json())
        return jsonify({"error": f"HTTP {r.status_code}"}), r.status_code
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
        "version": "10.0",
        "description": "OSINT-агрегатор",
        "author": "@kmyfg",
        "sources": [
            "BigBase",
            "AnyScan",
            "Jitler",
            "VK",
            "AbuseIPDB",
            "OFDATA",
            "Snusbase",
            "Cerera"
        ],
        "note": "LeakOSINT временно отключён"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
