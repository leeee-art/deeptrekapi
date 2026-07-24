from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import re
import time
from datetime import datetime
from funstat_api import FunstatClient

app = Flask(__name__)
CORS(app)

# ==================== КОНФИГ ====================
MASTER_KEY = "deeptrek_fjnrndhfrb2947472992gdvsbdh"

BIGBASE_KEY = "3y-Wbcx_NZrmoli2CnNXveZNSIozuGDW"
BIGBASE_BACKUP_KEY = "UUfh4i4J1WaMdeERFqzLOOPfBoQqZ9UB"
BIGBASE_URL = "https://bigbase.top/api/search"

ANYSCAN_TOKEN = "oxYKwwEN2kvMyG7advJ3DQ"
ANYSCAN_URL = "https://anyscan.duckdns.org/api/v1/search"

JITLER_TOKEN = "kcWgDpRlesD30v6SvqeLOejO"
JITLER_URL = "https://api.jitler.top"

VK_TOKEN = "0af157510af157510af15751aa0a89e69600af10af157516a0bc15996e74fe2b440998c"
VK_API = "https://api.vk.com/method/users.get"

ABUSEIPDB_KEY = "58878ed65228db88eddfda4983bce5d19d425ddf81f427857b3f59f11aecc34f127862a1cc7d4581"
ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"

FUNSTAT_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiI4NDkwNjcxMTE3IiwianRpIjoiYzk0MjAwNDktYTNhNi00ZjgwLTkwZjItYzAxOTllNWQ3ZjdlIiwiZXhwIjoxODExNDQwNTkzfQ.ZtAs0h5SnD-INsbBALHO9L6u7Owzb8oZeOQQdM5trWkG-5W5S2sWAzTRXVMNaZOrYXsGOekr4bARBFYVudASyC2tTx7HmJqHivn0gzdeUXvi3V-L6_YGWg87QSbfr-qEtqp2OJwolSgudgeNuMEn3AGpSM1Cb8N99oRDX5pFEiQ"

OFDATA_KEY = "KBnpz1CHKNngFXxK"
OFDATA_URL = "https://api.ofdata.ru/v2/search"

SNUSBASE_KEY = "sbmeovhou6ecsn9fd9wcwnwwvsvwnc"
SNUSBASE_URL = "https://api.snusbase.com/data/search"

LEAKOSINT_TOKEN = ""
LEAKOSINT_URL = "https://leakosint.com/api/v1/search"

def check_api_key():
    return request.headers.get('X-API-Key') == MASTER_KEY

# ==================== ОПРЕДЕЛЕНИЕ ТИПА ====================
def detect_type(query):
    query = query.strip()
    
    if re.match(r'^\d{4}\s?\d{6}$', query):
        return "passport"
    if re.search(r'@', query):
        return "email"
    if re.match(r'^[78]\d{10}$', re.sub(r'\D', '', query)):
        return "phone"
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', query):
        return "ip"
    if re.match(r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$', query, re.IGNORECASE):
        return "auto"
    if re.match(r'^\d{10}$|^\d{12}$', query):
        return "inn"
    if re.match(r'^\d{13}$|^\d{15}$', query):
        return "ogrn"
    if re.match(r'^\d{11}$', re.sub(r'\D', '', query)):
        return "snils"
    if query.startswith('@'):
        return "username"
    if query.lower().startswith('id') and query[2:].isdigit():
        return "vk"
    if re.search(r'[а-яА-Я]', query):
        if len(query.split()) >= 2:
            return "fio"
        else:
            return "company"
    return "username"

# ==================== BIGBASE ====================
def search_bigbase(query, search_type):
    keys = [BIGBASE_KEY, BIGBASE_BACKUP_KEY]
    
    for key in keys:
        headers = {
            "Authorization": key,
            "Content-Type": "application/json"
        }
        data = {"search": query, "page": 1}
        
        try:
            r = requests.post(BIGBASE_URL, headers=headers, json=data, timeout=30)
            if r.status_code == 200:
                return {"source": "bigbase", "data": r.json()}
            elif r.status_code in [402, 403]:
                continue
            else:
                return {"source": "bigbase", "error": f"HTTP {r.status_code}"}
        except:
            continue
    
    return {"source": "bigbase", "error": "Все ключи BigBase недоступны"}

# ==================== ANYSCAN ====================
def search_anyscan(query, search_type):
    type_map = {
        "phone": "phone",
        "email": "email",
        "fio": "name",
        "inn": "inn",
        "snils": "snils",
        "passport": "passport"
    }
    
    if search_type not in type_map:
        return {"source": "anyscan", "error": "Тип не поддерживается"}
    
    headers = {
        "Authorization": f"Bearer {ANYSCAN_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "type": type_map[search_type],
        "q": query,
        "limit": 100
    }
    
    try:
        r = requests.post(ANYSCAN_URL, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            return {"source": "anyscan", "data": r.json()}
        else:
            return {"source": "anyscan", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "anyscan", "error": str(e)}

# ==================== JITLER ====================
def search_jitler(query, search_type):
    type_map = {
        "phone": "number",
        "telegram": "sherlock",
        "vk": "vks"
    }
    
    if search_type not in type_map:
        return {"source": "jitler", "error": "Тип не поддерживается"}
    
    headers = {
        "Authorization": f"Bearer {JITLER_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "type": type_map[search_type],
        "query": query,
        "page": 1
    }
    
    try:
        r = requests.post(f"{JITLER_URL}/search", headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            return {"source": "jitler", "data": r.json()}
        else:
            return {"source": "jitler", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "jitler", "error": str(e)}

# ==================== VK ====================
def search_vk(query):
    params = {
        "access_token": VK_TOKEN,
        "v": "5.131",
        "user_ids": query,
        "fields": "first_name,last_name,status,sex,country"
    }
    
    try:
        r = requests.get(VK_API, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if "response" in data and data["response"]:
                return {"source": "vk", "data": data["response"]}
        return {"source": "vk", "error": "Пользователь не найден"}
    except Exception as e:
        return {"source": "vk", "error": str(e)}

# ==================== ABUSEIPDB ====================
def search_abuseipdb(ip):
    headers = {"Key": ABUSEIPDB_KEY, "Accept": "application/json"}
    params = {"ipAddress": ip, "maxAgeInDays": 90}
    
    try:
        r = requests.get(ABUSEIPDB_URL, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", {})
            return {
                "source": "abuseipdb",
                "data": {
                    "ip": data.get("ipAddress"),
                    "country": data.get("countryCode"),
                    "isp": data.get("isp"),
                    "confidence": data.get("abuseConfidenceScore"),
                    "reports": data.get("totalReports")
                }
            }
        else:
            return {"source": "abuseipdb", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "abuseipdb", "error": str(e)}

# ==================== FUNSTAT ====================
def search_funstat(query):
    if not query.isdigit():
        return {"source": "funstat", "error": "Funstat ищет только по числовому ID"}
    
    try:
        fs = FunstatClient(FUNSTAT_TOKEN)
        stats = fs.stats_min(int(query))
        
        if stats.success:
            data = stats.data
            return {
                "source": "funstat",
                "data": {
                    "id": data.id,
                    "first_name": data.first_name,
                    "last_name": data.last_name,
                    "is_bot": data.is_bot,
                    "is_active": data.is_active,
                    "total_msg_count": data.total_msg_count,
                    "total_groups": data.total_groups
                }
            }
        else:
            return {"source": "funstat", "error": "Пользователь не найден"}
    except Exception as e:
        return {"source": "funstat", "error": str(e)}

# ==================== OFDATA ====================
def search_ofdata(query, search_type):
    if search_type not in ["inn", "ogrn", "fio", "company"]:
        return {"source": "ofdata", "error": "Тип не поддерживается"}
    
    if search_type in ["inn", "ogrn"]:
        by = search_type
        obj = "org"
    elif search_type == "fio":
        by = "name"
        obj = "ent"
    else:
        by = "name"
        obj = "org"
    
    url = f"{OFDATA_URL}?key={OFDATA_KEY}&by={by}&obj={obj}&query={query}&limit=10"
    
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("data", {}).get("Записи"):
                return {"source": "ofdata", "data": data}
            else:
                return {"source": "ofdata", "error": "Ничего не найдено"}
        else:
            return {"source": "ofdata", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "ofdata", "error": str(e)}

# ==================== SNUSBASE ====================
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
        else:
            return {"source": "snusbase", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "snusbase", "error": str(e)}

# ==================== LEAKOSINT ====================
def search_leakosint(query, search_type):
    if not LEAKOSINT_TOKEN:
        return {"source": "leakosint", "error": "Нет ключа"}
    
    type_map = {
        "phone": "phone",
        "email": "email",
        "fio": "name",
        "inn": "inn",
        "snils": "snils",
        "passport": "passport",
        "ip": "ip"
    }
    
    if search_type not in type_map:
        return {"source": "leakosint", "error": "Тип не поддерживается"}
    
    headers = {
        "Authorization": f"Bearer {LEAKOSINT_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "type": type_map[search_type],
        "query": query,
        "limit": 50
    }
    
    try:
        r = requests.post(LEAKOSINT_URL, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            return {"source": "leakosint", "data": r.json()}
        else:
            return {"source": "leakosint", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "leakosint", "error": str(e)}

# ==================== ОСНОВНОЙ ПОИСК ====================
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
        search_type = detect_type(query)
    
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
    
    # ANYSCAN
    if search_type in ["phone", "email", "fio", "inn", "snils", "passport"]:
        try:
            result["sources"].append(search_anyscan(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "anyscan", "error": str(e)})
    
    # JITLER
    if search_type in ["phone", "vk", "telegram"]:
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
    
    # FUNSTAT
    if search_type == "telegram" and query.isdigit():
        try:
            result["sources"].append(search_funstat(query))
        except Exception as e:
            result["sources"].append({"source": "funstat", "error": str(e)})
    
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
    
    # LEAKOSINT
    if LEAKOSINT_TOKEN and search_type in ["phone", "email", "fio", "inn", "snils", "passport", "ip"]:
        try:
            result["sources"].append(search_leakosint(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "leakosint", "error": str(e)})
    
    return jsonify(result)

# ==================== TEMPMAIL ====================
def create_temp_email():
    try:
        r = requests.get("https://api.tempmail.lol/generate", timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {"success": True, "email": data["address"], "token": data["token"]}
    except:
        pass
    return {"success": False, "error": "Не удалось создать почту"}

def check_temp_mail(token):
    try:
        r = requests.get(f"https://api.tempmail.lol/messages/{token}", timeout=10)
        if r.status_code == 200:
            return {"success": True, "messages": r.json()}
    except:
        pass
    return {"success": False, "error": "Не удалось проверить почту"}

@app.route('/tempmail/generate', methods=['GET'])
def tempmail_generate():
    if not check_api_key():
        return jsonify({"error": "Неверный API-ключ"}), 403
    return jsonify(create_temp_email())

@app.route('/tempmail/check/<token>', methods=['GET'])
def tempmail_check(token):
    if not check_api_key():
        return jsonify({"error": "Неверный API-ключ"}), 403
    return jsonify(check_temp_mail(token))

# ==================== HEALTH ====================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

# ==================== ROOT ====================
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "name": "DeepTrek API",
        "version": "8.0",
        "description": "OSINT-агрегатор (БЕЗ AI)",
        "author": "@kmyfg",
        "endpoints": {
            "/search": "POST - поиск",
            "/tempmail/generate": "GET - создать временную почту",
            "/tempmail/check/<token>": "GET - проверить письма",
            "/health": "GET - статус"
        },
        "sources": ["BigBase", "AnyScan", "Jitler", "VK", "AbuseIPDB", "Funstat", "OFDATA", "Snusbase", "LeakOSINT"],
        "features": {
            "search": "Поиск по 12 типам запросов"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
