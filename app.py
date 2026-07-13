from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

API_SECRET = "deeptrek_fjnrndhfrb2947472992gdvsbdh"

BLACKEYE_TOKEN = "y06BzECXTqtOjzdIcTVQPw"
BLACKEYE_URL = "https://blackeyebot.duckdns.org/api/v1/search"

# ==================== АВТО-ОПРЕДЕЛЕНИЕ ТИПА ====================
def detect_type(query):
    query = query.strip()
    
    # ФИО — если есть русские буквы и пробелы
    if re.search(r'[а-яА-Я]', query) and re.search(r'\s', query):
        return "fio"
    
    # Email
    if re.search(r'@', query):
        return "email"
    
    # Телефон
    if re.match(r'^[78]\d{10}$', re.sub(r'\D', '', query)):
        return "phone"
    
    # ИНН (10 или 12 цифр)
    if re.match(r'^\d{10}$|^\d{12}$', query):
        return "inn"
    
    # СНИЛС (11 цифр)
    if re.match(r'^\d{11}$', re.sub(r'\D', '', query)):
        return "snils"
    
    # Паспорт (серия 4 цифры + номер 6 цифр)
    if re.match(r'^\d{4}\s?\d{6}$', query) or re.match(r'^\d{10}$', query):
        return "passport"
    
    return "fio"

# ==================== BLACKEYE ====================
def search_blackeye(query, search_type):
    data = {
        "type": search_type,
        "q": query,
        "limit": 100
    }
    try:
        r = requests.post(
            BLACKEYE_URL,
            headers={"Authorization": f"Bearer {BLACKEYE_TOKEN}", "Content-Type": "application/json"},
            json=data,
            timeout=30
        )
        if r.status_code == 200:
            return {"source": "blackeye", "data": r.json()}
        else:
            return {"source": "blackeye", "error": f"Код: {r.status_code}"}
    except Exception as e:
        return {"source": "blackeye", "error": str(e)}

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
    
    search_type = data.get('type')
    if not search_type:
        search_type = detect_type(query)
    
    result = {
        "query": query,
        "type": search_type,
        "timestamp": datetime.now().isoformat(),
        "sources": [search_blackeye(query, search_type)]
    }
    
    return jsonify(result)

# ==================== HEALTH ====================
@app.route('/health')
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

# ==================== ROOT ====================
@app.route('/')
def index():
    return jsonify({
        "name": "DeepTrek API",
        "version": "6.0",
        "endpoints": {
            "/search": "POST - поиск (нужен X-API-Secret)",
            "/health": "GET - статус"
        },
        "source": "BlackEye"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
