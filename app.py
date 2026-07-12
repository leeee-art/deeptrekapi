from flask import Flask, request, jsonify
import requests
import json
import re
import csv
import io
from datetime import datetime

app = Flask(__name__)

API_SECRET = "deeptrek_fjnrndhfrb2947472992gdvsbdh"

# ==================== ТОКЕНЫ ====================
ATLAS_TOKEN = "sub_1tme688x58j6v3s03jhc9nvh"
ATLAS_URL = "https://atlas-in.cc/app"

SNUSBASE_KEY = "sbmeovhou6ecsn9fd9wcwnwwvsvwnc"
SNUSBASE_URL = "https://api.snusbase.com/data/search"

VK_TOKEN = "0af157510af157510af15751aa0a89e69600af10af157516a0bc15996e74fe2b440998c"
VK_API = "https://api.vk.com/method/users.get"

# ==================== АВТО-ОПРЕДЕЛЕНИЕ ТИПА ====================
def detect_type(query):
    query = query.strip()
    if re.search(r'@', query):
        return "email"
    if re.match(r'^[78]\d{10}$', re.sub(r'\D', '', query)):
        return "phone"
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', query):
        return "ip"
    if re.match(r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$', query, re.IGNORECASE):
        return "auto"
    if re.match(r'^[A-HJ-NPR-Z0-9]{17}$', query, re.IGNORECASE):
        return "vin"
    if re.match(r'^\d{10}$|^\d{12}$', query):
        return "inn"
    if re.match(r'^\d{11}$', re.sub(r'\D', '', query)):
        return "snils"
    if re.match(r'^\d{4}\s?\d{6}$', query) or re.match(r'^\d{10}$', query):
        return "passport"
    if query.startswith('@'):
        return "telegram"
    if re.match(r'^\d+$', query):
        return "vk"
    # Если ничего не подошло — считаем, что это ник или ФИО
    return "username"

# ==================== ATLAS ====================
def search_atlas(query, search_type):
    params = {
        "token": ATLAS_TOKEN,
        "type": search_type,
        "search": query,
        "method": "full"
    }
    try:
        r = requests.get(ATLAS_URL, params=params, timeout=30)
        return {"source": "atlas", "data": r.json()} if r.status_code == 200 else {"source": "atlas", "error": f"Код: {r.status_code}"}
    except Exception as e:
        return {"source": "atlas", "error": str(e)}

# ==================== SNUSBASE (ИСПРАВЛЕН) ====================
def search_snusbase(query, search_type):
    # Определяем тип для Snusbase
    if search_type == "email":
        snus_type = "email"
    elif search_type in ["username", "fio"]:
        snus_type = "username"
    else:
        snus_type = "username"
    
    payload = {
        "terms": [query],
        "types": [snus_type],
        "wildcard": False
    }
    headers = {
        "Auth": SNUSBASE_KEY,
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(SNUSBASE_URL, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return {"source": "snusbase", "data": r.json()}
        else:
            return {"source": "snusbase", "error": f"Код: {r.status_code}"}
    except Exception as e:
        return {"source": "snusbase", "error": str(e)}

# ==================== INTELX ====================
def search_intelx(phone):
    phone = re.sub(r'\D', '', phone)
    if len(phone) < 8:
        return {"source": "intelx", "error": "Номер слишком короткий"}
    
    url = f"https://data.intelx.io/saverudata/db2/dbpn/{phone[:2]}/{phone[2:4]}/{phone[4:6]}/{phone[6:8]}.csv"
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.status_code == 200:
            reader = csv.reader(io.StringIO(r.text))
            rows = list(reader)
            if len(rows) > 1:
                headers = rows[0]
                results = []
                for row in rows[1:]:
                    if phone in ' '.join(row):
                        result = {}
                        for i, v in enumerate(row):
                            if i < len(headers) and v:
                                result[headers[i]] = v
                        results.append(result)
                return {"source": "intelx", "data": results}
        return {"source": "intelx", "error": "Данных нет"}
    except Exception as e:
        return {"source": "intelx", "error": str(e)}

# ==================== VK ====================
def search_vk(query):
    params = {
        "access_token": VK_TOKEN,
        "v": "5.131",
        "user_ids": query,
        "fields": "first_name,last_name,status,sex,country,photo_max_orig"
    }
    try:
        r = requests.get(VK_API, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if "response" in data and data["response"]:
                return {"source": "vk", "data": data["response"]}
            else:
                return {"source": "vk", "error": "Пользователь не найден"}
        else:
            return {"source": "vk", "error": f"Код: {r.status_code}"}
    except Exception as e:
        return {"source": "vk", "error": str(e)}

# ==================== ПОИСК ====================
@app.route('/search', methods=['POST'])
def search():
    secret = request.headers.get('X-API-Secret')
    if secret != API_SECRET:
        return jsonify({"error": "Неверный секретный ключ"}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Нет данных"}), 400
    
    query = data.get('query', '').strip()
    if not query:
        return jsonify({"error": "Пустой запрос"}), 400
    
    search_type = detect_type(query)
    results = {
        "query": query,
        "type": search_type,
        "timestamp": datetime.now().isoformat(),
        "sources": []
    }
    
    # Atlas — всегда
    results["sources"].append(search_atlas(query, search_type))
    
    # Snusbase — для email, username, fio
    if search_type in ["email", "username", "fio"]:
        results["sources"].append(search_snusbase(query, search_type))
    
    # IntelX — только для телефона
    if search_type == "phone":
        results["sources"].append(search_intelx(query))
    
    # VK — для ID или короткого адреса
    if search_type == "vk" or re.match(r'^[a-zA-Z0-9_.]+$', query):
        results["sources"].append(search_vk(query))
    
    return jsonify(results)

# ==================== HEALTH ====================
@app.route('/health')
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

# ==================== ROOT ====================
@app.route('/')
def index():
    return jsonify({
        "name": "DeepTrek API",
        "version": "3.1",
        "endpoints": {
            "/search": "POST - поиск (нужен X-API-Secret)",
            "/health": "GET - статус"
        },
        "sources": ["Atlas", "Snusbase", "IntelX", "VK"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
