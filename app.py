from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
import json
import re
import csv
import io
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# ==================== БАЗА ПОДПИСОК ====================
# В реальном проекте использовать БД
subscriptions = {}  # {secret_key: {"api_key": str, "expires": datetime, "created": datetime, "used": bool}}
api_keys = {}       # {api_key: secret_key}

# ==================== HTML СТРАНИЦА АКТИВАЦИИ ====================
ACTIVATE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepTrek — Активация API</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0b0b1a;
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            width: 100%;
            background: #151528;
            border-radius: 20px;
            padding: 40px;
            border: 1px solid #6c5ce7;
            box-shadow: 0 0 40px rgba(108, 92, 231, 0.15);
        }
        .logo { font-size: 32px; font-weight: 700; background: linear-gradient(135deg, #6c5ce7, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 4px; }
        .subtitle { text-align: center; color: #888; font-size: 14px; margin-bottom: 25px; }
        input {
            width: 100%;
            padding: 14px;
            background: #0e0e20;
            border: 1px solid #3a2a5a;
            border-radius: 12px;
            color: #fff;
            font-size: 16px;
            outline: none;
            margin-bottom: 15px;
            font-family: monospace;
        }
        input:focus { border-color: #6c5ce7; box-shadow: 0 0 20px rgba(108, 92, 231, 0.2); }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #6c5ce7, #a855f7);
            border: none;
            border-radius: 12px;
            color: #fff;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.3s;
        }
        button:hover { transform: scale(1.02); box-shadow: 0 0 30px rgba(108, 92, 231, 0.3); }
        .result { margin-top: 20px; padding: 20px; background: #0e0e20; border-radius: 12px; border: 1px solid #2a2a4a; display: none; }
        .result.show { display: block; }
        .success { color: #51cf66; }
        .error { color: #ff6b6b; }
        .warning { color: #f1c40f; }
        .key-box {
            background: #0a0a18;
            padding: 12px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 13px;
            color: #a855f7;
            word-break: break-all;
            margin: 10px 0;
            border: 1px solid #2a2a4a;
        }
        .code-box {
            background: #0a0a18;
            padding: 12px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 11px;
            color: #c0c0c0;
            overflow-x: auto;
            margin: 10px 0;
            border: 1px solid #2a2a4a;
            white-space: pre-wrap;
        }
        .badge {
            display: inline-block;
            background: rgba(168, 85, 247, 0.2);
            color: #a855f7;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 12px;
            margin: 3px;
        }
        .footer { text-align: center; color: #555; font-size: 12px; margin-top: 20px; }
        .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #1a1a3a; }
        .info-label { color: #888; }
        .info-value { color: #e0e0e0; font-weight: 600; }
        .expires { color: #51cf66; }
        .warning-box {
            background: #1a1a2a;
            padding: 12px;
            border-radius: 8px;
            border-left: 3px solid #f1c40f;
            margin: 10px 0;
        }
        .warning-box .title { color: #f1c40f; font-weight: 600; font-size: 13px; }
        .warning-box .text { color: #c0c0c0; font-size: 12px; margin-top: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🔍 DeepTrek</div>
        <div class="subtitle">Активация API ключа</div>
        
        <form id="activateForm">
            <input type="text" id="secretKey" placeholder="Введите секретный ключ (начинается с deeptrek_)" required>
            <button type="submit">🔑 Активировать</button>
        </form>
        
        <div class="result" id="result">
            <div id="resultContent"></div>
        </div>
        
        <div class="footer">DeepTrek API © 2026</div>
    </div>
    
    <script>
        document.getElementById('activateForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const secretKey = document.getElementById('secretKey').value.trim();
            const resultDiv = document.getElementById('result');
            const contentDiv = document.getElementById('resultContent');
            
            if (!secretKey) {
                contentDiv.innerHTML = '<div class="error">❌ Введите секретный ключ</div>';
                resultDiv.className = 'result show';
                return;
            }
            
            if (!secretKey.startsWith('deeptrek_')) {
                contentDiv.innerHTML = '<div class="error">❌ Неверный формат ключа. Ключ должен начинаться с "deeptrek_"</div>';
                resultDiv.className = 'result show';
                return;
            }
            
            // Проверка длины ключа (от 35 до 39 символов)
            if (secretKey.length < 35 || secretKey.length > 39) {
                contentDiv.innerHTML = `<div class="error">❌ Неверная длина ключа. Допустимо от 35 до 39 символов. Текущая длина: ${secretKey.length}</div>`;
                resultDiv.className = 'result show';
                return;
            }
            
            resultDiv.className = 'result show';
            contentDiv.innerHTML = '⏳ Активация...';
            
            try {
                const response = await fetch('/api/activate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ secret_key: secretKey })
                });
                
                const data = await response.json();
                
                if (data.status === 'ok') {
                    const expires = new Date(data.expires);
                    const formattedExpires = expires.toLocaleString('ru-RU', {
                        day: '2-digit', month: '2-digit', year: 'numeric',
                        hour: '2-digit', minute: '2-digit'
                    });
                    
                    const reactivateDate = new Date(data.can_reactivate);
                    const formattedReactive = reactivateDate.toLocaleString('ru-RU', {
                        day: '2-digit', month: '2-digit', year: 'numeric',
                        hour: '2-digit', minute: '2-digit'
                    });
                    
                    contentDiv.innerHTML = `
                        <div class="success">✅ API ключ успешно активирован!</div>
                        
                        <div style="margin: 15px 0;">
                            <div class="info-row">
                                <span class="info-label">🔑 API-ключ</span>
                                <span class="info-value" style="font-family:monospace; font-size:12px; color:#a855f7;">${data.api_key}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">📅 Действует до</span>
                                <span class="info-value expires">${formattedExpires}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">📊 Лимит</span>
                                <span class="info-value" style="color:#51cf66;">∞ Безлимит</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">📦 Источники</span>
                                <span class="info-value">
                                    <span class="badge">Atlas</span>
                                    <span class="badge">BlackEye</span>
                                    <span class="badge">Snusbase</span>
                                    <span class="badge">IntelX</span>
                                    <span class="badge">VK</span>
                                </span>
                            </div>
                        </div>
                        
                        <div class="warning-box">
                            <div class="title">⚠️ ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ</div>
                            <div class="text">
                                • Секретный ключ можно использовать <strong>ТОЛЬКО 1 РАЗ</strong><br>
                                • Повторная активация возможна только через <strong>17 дней</strong> после первой активации<br>
                                • Дата повторной активации: <strong>${formattedReactive}</strong><br>
                                • Длина ключа: ${secretKey.length} символов (от 35 до 39)<br>
                                • Если вы попытаетесь активировать ключ раньше — получите ошибку
                            </div>
                        </div>
                        
                        <div style="margin: 15px 0; padding: 12px; background: #1a1a3a; border-radius: 8px; border-left: 3px solid #a855f7;">
                            <div style="color: #888; font-size: 13px; font-weight: 600; margin-bottom: 5px;">📌 Пример запроса</div>
                            <div class="code-box">curl -X POST https://deeptrekapi.onrender.com/search \\<br>  -H "Content-Type: application/json" \\<br>  -H "X-API-Secret: ${data.api_key}" \\<br>  -d '{"query": "79123456789"}'</div>
                        </div>
                        
                        <div style="margin: 15px 0; padding: 12px; background: #1a1a3a; border-radius: 8px; border-left: 3px solid #51cf66;">
                            <div style="color: #888; font-size: 13px; font-weight: 600; margin-bottom: 5px;">📋 Поддерживаемые типы</div>
                            <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                                <span class="badge">Телефон — phone</span>
                                <span class="badge">Email — email</span>
                                <span class="badge">ФИО — fio</span>
                                <span class="badge">ИНН — inn</span>
                                <span class="badge">СНИЛС — snils</span>
                                <span class="badge">Паспорт — passport</span>
                                <span class="badge">Госномер — auto</span>
                                <span class="badge">IP — ip</span>
                                <span class="badge">Telegram — @username</span>
                                <span class="badge">VK — id</span>
                            </div>
                        </div>
                    `;
                } else {
                    contentDiv.innerHTML = `<div class="error">❌ ${data.error}</div>`;
                }
            } catch (error) {
                contentDiv.innerHTML = `<div class="error">❌ Ошибка: ${error.message}</div>`;
            }
        });
    </script>
</body>
</html>
'''

# ==================== ТОКЕНЫ ====================
ATLAS_TOKEN = "sub_1tme688x58j6v3s03jhc9nvh"
ATLAS_URL = "https://atlas-in.cc/app"

BLACKEYE_TOKEN = "y06BzECXTqtOjzdIcTVQPw"
BLACKEYE_URL = "https://blackeyebot.duckdns.org/api/v1/search"

SNUSBASE_KEY = "sbmeovhou6ecsn9fd9wcwnwwvsvwnc"
SNUSBASE_URL = "https://api.snusbase.com/data/search"

VK_TOKEN = "0af157510af157510af15751aa0a89e69600af10af157516a0bc15996e74fe2b440998c"
VK_API = "https://api.vk.com/method/users.get"

# ==================== АКТИВАЦИЯ ====================
@app.route('/activate')
def activate_page():
    return render_template_string(ACTIVATE_HTML)

@app.route('/api/activate', methods=['POST'])
def activate():
    data = request.get_json()
    secret_key = data.get('secret_key', '').strip()
    
    if not secret_key:
        return jsonify({"status": "error", "error": "Введите секретный ключ"})
    
    # Проверка формата
    if not secret_key.startswith('deeptrek_'):
        return jsonify({"status": "error", "error": "Неверный формат ключа. Ключ должен начинаться с 'deeptrek_'"})
    
    # Проверка длины (от 35 до 39 символов)
    if len(secret_key) < 35 or len(secret_key) > 39:
        return jsonify({"status": "error", "error": f"Неверная длина ключа. Допустимо от 35 до 39 символов. Текущая длина: {len(secret_key)}"})
    
    # Проверка, не использован ли уже этот ключ
    if secret_key in subscriptions:
        # Проверяем, прошло ли 17 дней
        created = subscriptions[secret_key]["created"]
        days_since = (datetime.now() - created).days
        if days_since < 17:
            can_reactivate = created + timedelta(days=17)
            return jsonify({
                "status": "error",
                "error": f"Этот ключ уже использован. Повторная активация возможна через {17 - days_since} дней (с {can_reactivate.strftime('%Y-%m-%d %H:%M')})"
            })
        else:
            # Если прошло 17+ дней — можно использовать снова
            # Генерируем новый API-ключ
            api_key = f"deeptrek_{secrets.token_hex(16)}"
            expires = datetime.now() + timedelta(days=14)
            subscriptions[secret_key] = {
                "api_key": api_key,
                "expires": expires,
                "created": datetime.now(),
                "used": True
            }
            api_keys[api_key] = secret_key
            
            return jsonify({
                "status": "ok",
                "api_key": api_key,
                "expires": expires.isoformat(),
                "can_reactivate": (datetime.now() + timedelta(days=17)).isoformat()
            })
    
    # Генерируем новый API-ключ
    api_key = f"deeptrek_{secrets.token_hex(16)}"
    
    # Сохраняем в базу (14 дней)
    expires = datetime.now() + timedelta(days=14)
    subscriptions[secret_key] = {
        "api_key": api_key,
        "expires": expires,
        "created": datetime.now(),
        "used": True
    }
    api_keys[api_key] = secret_key
    
    return jsonify({
        "status": "ok",
        "api_key": api_key,
        "expires": expires.isoformat(),
        "can_reactivate": (datetime.now() + timedelta(days=17)).isoformat()
    })

# ==================== ПОИСК ====================
def check_api_key(api_key):
    if api_key in api_keys:
        secret_key = api_keys[api_key]
        if secret_key in subscriptions:
            expires = subscriptions[secret_key]["expires"]
            if datetime.now() < expires:
                return True
    return False

def detect_type(query):
    query = query.strip()
    if re.match(r'^\d+$', query):
        return "vk"
    if re.match(r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$', query, re.IGNORECASE):
        return "auto"
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', query):
        return "ip"
    if query.startswith('@'):
        return "telegram"
    if re.search(r'[а-яА-Я]', query) and re.search(r'\s', query):
        return "fio"
    if re.search(r'@', query):
        return "email"
    if re.match(r'^[78]\d{10}$', re.sub(r'\D', '', query)):
        return "phone"
    if re.match(r'^\d{10}$|^\d{12}$', query):
        return "inn"
    if re.match(r'^\d{11}$', re.sub(r'\D', '', query)):
        return "snils"
    if re.match(r'^\d{4}\s?\d{6}$', query) or re.match(r'^\d{10}$', query):
        return "passport"
    return "fio"

# ==================== ПАРСЕРЫ ====================
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

def search_blackeye(query, search_type):
    data = {"type": search_type, "q": query, "limit": 100}
    try:
        r = requests.post(
            BLACKEYE_URL,
            headers={"Authorization": f"Bearer {BLACKEYE_TOKEN}", "Content-Type": "application/json"},
            json=data,
            timeout=30
        )
        return {"source": "blackeye", "data": r.json()} if r.status_code == 200 else {"source": "blackeye", "error": f"Код: {r.status_code}"}
    except Exception as e:
        return {"source": "blackeye", "error": str(e)}

def search_snusbase(query, search_type):
    if not search_type:
        search_type = "email" if re.search(r'@', query) else "username"
    payload = {"terms": [query], "types": [search_type], "wildcard": False}
    headers = {"Auth": SNUSBASE_KEY, "Content-Type": "application/json"}
    try:
        r = requests.post(SNUSBASE_URL, headers=headers, json=payload, timeout=30)
        return {"source": "snusbase", "data": r.json()} if r.status_code == 200 else {"source": "snusbase", "error": f"Код: {r.status_code}"}
    except Exception as e:
        return {"source": "snusbase", "error": str(e)}

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
        return {"source": "vk", "error": "Пользователь не найден"}
    except Exception as e:
        return {"source": "vk", "error": str(e)}

# ==================== ПОИСК ====================
@app.route('/search', methods=['POST'])
def search():
    api_key = request.headers.get('X-API-Secret')
    
    if not check_api_key(api_key):
        return jsonify({"error": "Неверный или просроченный API-ключ"}), 403
    
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
    
    result["sources"].append(search_atlas(query, search_type))
    result["sources"].append(search_blackeye(query, search_type))
    
    if search_type in ["email", "username", "fio"]:
        result["sources"].append(search_snusbase(query, search_type))
    if search_type == "phone":
        result["sources"].append(search_intelx(query))
    if search_type == "vk":
        result["sources"].append(search_vk(query))
    
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
            "/activate": "GET - страница активации API",
            "/health": "GET - статус"
        },
        "sources": ["Atlas", "BlackEye", "Snusbase", "IntelX", "VK"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
