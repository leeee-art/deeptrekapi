from flask import Flask, request, jsonify
import requests
import json
import re
import csv
import io
from datetime import datetime

app = Flask(__name__)

# ==================== ТОКЕНЫ ====================
ATLAS_TOKEN = "sub_1tme688x58j6v3s03jhc9nvh"
ATLAS_URL = "https://atlas-in.cc/app"

BLACKEYE_TOKEN = "Ay1E06CKjfaWqTDyUwtj2g"
BLACKEYE_URL = "https://blackeyebot.duckdns.org/api/v1/search"

# ==================== АВТО-ОПРЕДЕЛЕНИЕ ТИПА ====================
def detect_type(query):
    query = query.strip()
    
    if re.match(r'^[78]\d{10}$', re.sub(r'\D', '', query)):
        return "phone"
    if re.search(r'@', query):
        return "email"
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
    return "fio"

# ==================== ATLAS ====================
def search_atlas(query, search_type):
    params = {
        "token": ATLAS_TOKEN,
        "type": search_type,
        "search": query,
        "method": "full"
    }
    try:
        response = requests.get(ATLAS_URL, params=params, timeout=30)
        return {"source": "atlas", "data": response.json()} if response.status_code == 200 else {"source": "atlas", "error": f"Код: {response.status_code}"}
    except Exception as e:
        return {"source": "atlas", "error": str(e)}

# ==================== BLACKEYE ====================
def search_blackeye(query, search_type):
    data = {
        "type": search_type,
        "q": query,
        "limit": 100
    }
    try:
        response = requests.post(
            BLACKEYE_URL,
            headers={"Authorization": f"Bearer {BLACKEYE_TOKEN}", "Content-Type": "application/json"},
            json=data,
            timeout=20
        )
        return {"source": "blackeye", "data": response.json()} if response.status_code == 200 else {"source": "blackeye", "error": f"Код: {response.status_code}"}
    except Exception as e:
        return {"source": "blackeye", "error": str(e)}

# ==================== INTELX (только по номеру) ====================
def search_intelx(phone):
    phone = re.sub(r'\D', '', phone)
    if len(phone) < 8:
        return {"source": "intelx", "error": "Номер слишком короткий"}
    
    url = f"https://data.intelx.io/saverudata/db2/dbpn/{phone[:2]}/{phone[2:4]}/{phone[4:6]}/{phone[6:8]}.csv"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if response.status_code == 200:
            reader = csv.reader(io.StringIO(response.text))
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

# ==================== ОБЩИЙ ПОИСК ====================
@app.route('/search', methods=['POST'])
def search():
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
    
    # Atlas (всегда)
    results["sources"].append(search_atlas(query, search_type))
    
    # BlackEye (всегда)
    results["sources"].append(search_blackeye(query, search_type))
    
    # IntelX (только для телефонов)
    if search_type == "phone":
        results["sources"].append(search_intelx(query))
    
    return jsonify(results)

# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
