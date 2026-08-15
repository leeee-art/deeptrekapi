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

# ==================== КОНФИГ (ИЗ .env) ====================

MASTER_KEY = os.environ.get('MASTER_KEY', 'deeptrek_fjnrndhfrb2947472992gdvsbdh')

# BIGBASE
BIGBASE_KEY = os.environ.get('BIGBASE_KEY', 'G1MFiznW5I7JJ-O4lwCg29nx2v0Xn6DE')
BIGBASE_URL = os.environ.get('BIGBASE_URL', 'https://bigbase.top/api/search')

# WHITE SEARCH
WHITE_SEARCH_KEY = os.environ.get('WHITE_SEARCH_KEY', 'WS-PUBLIC-9X7K-2M4P')
WHITE_SEARCH_URL = os.environ.get('WHITE_SEARCH_URL', 'https://api.whitesearch.workers.dev/api')

# INFINITY
INFINITY_TOKEN = os.environ.get('INFINITY_TOKEN', 'Bjm928HUcvsw923ZMBX19gd110FWSZgd')
INFINITY_URL = os.environ.get('INFINITY_URL', 'https://infinity-search.fun/find.php')

# JITLER
JITLER_TOKEN = os.environ.get('JITLER_TOKEN', 'kcWgDpRlesD30v6SvqeLOejO')
JITLER_URL = os.environ.get('JITLER_URL', 'https://api.jitler.top')

# VK
VK_TOKEN = os.environ.get('VK_TOKEN', '0af157510af157510af15751aa0a89e69600af10af157516a0bc15996e74fe2b440998c')
VK_API = os.environ.get('VK_API', 'https://api.vk.com/method/users.get')

# SNUSBASE
SNUSBASE_KEY = os.environ.get('SNUSBASE_KEY', 'sbmeovhou6ecsn9fd9wcwnwwvsvwnc')
SNUSBASE_URL = os.environ.get('SNUSBASE_URL', 'https://api.snusbase.com/data/search')

# ABUSEIPDB
ABUSEIPDB_KEY = os.environ.get('ABUSEIPDB_KEY', '58878ed65228db88eddfda4983bce5d19d425ddf81f427857b3f59f11aecc34f127862a1cc7d4581')
ABUSEIPDB_URL = os.environ.get('ABUSEIPDB_URL', 'https://api.abuseipdb.com/api/v2/check')

# PROXYCHECK
PROXYCHECK_KEY = os.environ.get('PROXYCHECK_KEY', '9fcd3e6622f96a780f0908ce414bb16360d3779d8253f484f319e02cc5c25065')
PROXYCHECK_URL = os.environ.get('PROXYCHECK_URL', 'https://proxycheck.io/v2/')

# HUDSON ROCK
HUDSON_IP_URL = os.environ.get('HUDSON_IP_URL', 'https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-ip')
HUDSON_USERNAME_URL = os.environ.get('HUDSON_USERNAME_URL', 'https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-username')
HUDSON_EMAIL_URL = os.environ.get('HUDSON_EMAIL_URL', 'https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-email')

# PROXYNOVA
PROXYNOVA_URL = os.environ.get('PROXYNOVA_URL', 'https://api.proxynova.com/comb')

# IP2LOCATION
IP2LOCATION_KEY = os.environ.get('IP2LOCATION_KEY', '965108E0429BB3E9329066D8D015564C')
IP2LOCATION_URL = os.environ.get('IP2LOCATION_URL', 'https://api.ip2location.io')

# OFDATA
OFDATA_KEY = os.environ.get('OFDATA_KEY', 'KBnpz1CHKNngFXxK')
OFDATA_URL = os.environ.get('OFDATA_URL', 'https://api.ofdata.ru/v2/search')

# FUNSTAT
FUNSTAT_TOKEN = os.environ.get('FUNSTAT_TOKEN', 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiI4NDkwNjcxMTE3IiwianRpIjoiYzk0MjAwNDktYTNhNi00ZjgwLTkwZjItYzAxOTllNWQ3ZjdlIiwiZXhwIjoxODExNDQwNTkzfQ.ZtAs0h5SnD-INsbBALHO9L6u7Owzb8oZeOQQdM5trWkG-5W5S2sWAzTRXVMNaZOrYXsGOekr4bARBFYVudASyC2tTx7HmJqHivn0gzdeUXvi3V-L6_YGWg87QSbfr-qEtqp2OJwolSgudgeNuMEn3AGpSM1Cb8N99oRDX5pFEiQ')

# SMSC
SMSC_LOGIN = os.environ.get('SMSC_LOGIN', 'kirahacker333')
SMSC_PASSWORD = os.environ.get('SMSC_PASSWORD', 'Zangar5050')
SMSC_URL = os.environ.get('SMSC_URL', 'https://smsc.ru/sys/info.php')

# ANYAPI
ANYAPI_KEY = os.environ.get('ANYAPI_KEY', 'sk-wlpObrPCnFwhEciP7KljEQ')
ANYAPI_URL = os.environ.get('ANYAPI_URL', 'https://api.anyapi.ai/v1')

# GITHUB
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_API_URL = os.environ.get('GITHUB_API_URL', 'https://api.github.com')

# ==================== ХРАНИЛИЩЕ ИСТОРИИ (30 СООБЩЕНИЙ) ====================
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

# ==================== КРАСИВЫЙ ВЫВОД BIGBASE ====================
def format_bigbase_result(data):
    """Форматирует результат BigBase для красивого вывода"""
    if not data:
        return "❌ Данных нет"
    
    if data.get("error"):
        return f"❌ Ошибка: {data['error']}"
    
    result = []
    result.append("=" * 60)
    result.append("📊 BIGBASE — РЕЗУЛЬТАТЫ ПОИСКА")
    result.append("=" * 60)
    
    # Статистика
    count = data.get("count_result", 0)
    pages = data.get("total_pages", 0)
    time_taken = data.get("time", 0)
    
    result.append(f"📌 Найдено: {count} записей")
    result.append(f"📌 Страниц: {pages}")
    result.append(f"⏱️ Время: {time_taken}с")
    
    # Информация о пользователе
    user = data.get("user", {})
    if user:
        result.append(f"\n👤 Аккаунт:")
        result.append(f"  Логин: {user.get('login', '***')}")
        result.append(f"  Баланс: {user.get('balance', 0)}")
        result.append(f"  Запросов: {user.get('queries', 0)}")
        result.append(f"  Подписка: {user.get('subscribe', 0)}")
        result.append(f"  Запросов по подписке: {user.get('subscribe_queries', 0)}")
    
    # Записи
    records = data.get("records", [])
    if not records:
        result.append("\n❌ Записей не найдено")
        return "\n".join(result)
    
    result.append(f"\n📦 НАЙДЕННЫЕ ЗАПИСИ ({len(records)}):")
    result.append("-" * 60)
    
    for idx, record in enumerate(records[:20], 1):
        result.append(f"\n─── ЗАПИСЬ #{idx} ───")
        
        # ID записи
        record_id = record.get("record_id", "N/A")
        result.append(f"  🆔 ID: {record_id}")
        
        # Базовая информация
        base_info = record.get("base_info", {})
        if base_info:
            name = base_info.get("name", "")
            description = base_info.get("description", "")
            if name:
                result.append(f"  📚 База: {name}")
            if description:
                result.append(f"  📝 Описание: {description[:100]}...")
        
        # Данные записи (base_record)
        base_record = record.get("base_record", [])
        if base_record:
            result.append(f"\n  📋 ДАННЫЕ:")
            for field in base_record:
                if isinstance(field, list) and len(field) >= 2:
                    key = field[0]
                    value = field[1]
                    if value and str(value).strip():
                        if isinstance(value, list):
                            if len(value) > 0 and isinstance(value[0], list):
                                for sub in value[:3]:
                                    if isinstance(sub, list):
                                        parts = []
                                        for item in sub:
                                            if isinstance(item, list) and len(item) >= 2:
                                                parts.append(f"{item[0]}: {item[1]}")
                                        if parts:
                                            result.append(f"    • {', '.join(parts)}")
                            else:
                                result.append(f"    • {', '.join([str(x) for x in value[:5]])}")
                        elif isinstance(value, dict):
                            result.append(f"    • {json.dumps(value, ensure_ascii=False)[:100]}...")
                        else:
                            result.append(f"    • {key}: {value}")
        
        # Связи (connections)
        connections = record.get("connections", [])
        if connections:
            result.append(f"\n  🔗 СВЯЗИ ({len(connections)}):")
            for conn in connections[:5]:
                conn_type = conn.get("type", "unknown")
                conn_title = conn.get("title", "")
                if conn_title:
                    result.append(f"    • [{conn_type}] {conn_title}")
                else:
                    for key, value in conn.items():
                        if key not in ["type", "id", "title", "links"] and value:
                            if isinstance(value, list) and value:
                                first = value[0]
                                if isinstance(first, dict):
                                    val_str = first.get("value", first.get("name", str(first)))
                                    result.append(f"    • {key}: {val_str}")
                                else:
                                    result.append(f"    • {key}: {value}")
                            break
    
    if len(records) > 20:
        result.append(f"\n... и ещё {len(records) - 20} записей")
    
    result.append("\n" + "=" * 60)
    return "\n".join(result)

# ==================== ANYAPI ====================
def ask_anyapi(prompt, model="google/gemma-4-26b-a4b-it:free", max_tokens=500, temperature=0.7, user_id=None):
    if not ANYAPI_KEY:
        return "Ошибка: ANYAPI_KEY не настроен"
    
    headers = {
        "Authorization": f"Bearer {ANYAPI_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if user_id:
        messages = get_history(user_id)
    
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    try:
        r = requests.post(f"{ANYAPI_URL}/chat/completions", headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            response = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            if user_id:
                add_to_history(user_id, "user", prompt)
                add_to_history(user_id, "assistant", response)
            return response
        return f"Ошибка {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Ошибка: {e}"

# ==================== GITHUB ====================
def search_github_user(username):
    if not GITHUB_TOKEN:
        return {"source": "github", "error": "GITHUB_TOKEN не настроен"}
    
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        url = f"{GITHUB_API_URL}/users/{username}"
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            return {
                "source": "github",
                "data": {
                    "login": data.get('login'),
                    "name": data.get('name'),
                    "email": data.get('email'),
                    "company": data.get('company'),
                    "bio": data.get('bio'),
                    "location": data.get('location'),
                    "public_repos": data.get('public_repos', 0),
                    "followers": data.get('followers', 0),
                    "following": data.get('following', 0),
                    "html_url": data.get('html_url'),
                    "created_at": data.get('created_at'),
                    "blog": data.get('blog'),
                    "twitter_username": data.get('twitter_username'),
                    "avatar_url": data.get('avatar_url')
                }
            }
        elif r.status_code == 404:
            return {"source": "github", "error": "Пользователь не найден"}
        else:
            return {"source": "github", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "github", "error": str(e)}

def search_github_email(email):
    if not GITHUB_TOKEN:
        return {"source": "github_email", "error": "GITHUB_TOKEN не настроен"}
    
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        url = f"{GITHUB_API_URL}/search/commits"
        params = {"q": email}
        r = requests.get(url, headers=headers, params=params, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            items = data.get('items', [])
            results = []
            for item in items[:10]:
                commit = item.get('commit', {})
                author = commit.get('author', {})
                repo = item.get('repository', {})
                results.append({
                    "repo": repo.get('full_name'),
                    "message": commit.get('message', '')[:100],
                    "author_name": author.get('name'),
                    "author_email": author.get('email'),
                    "date": author.get('date'),
                    "url": item.get('html_url')
                })
            return {
                "source": "github_email",
                "data": {
                    "total": data.get('total_count', 0),
                    "results": results
                }
            }
        else:
            return {"source": "github_email", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "github_email", "error": str(e)}

# ==================== ОПРЕДЕЛЕНИЕ ТИПА ====================
def detect_type(query: str) -> Tuple[str, Optional[str]]:
    query = query.strip()
    if not query:
        return "unknown", None
    
    # ГРЗ
    auto_clean = re.sub(r'\s+', '', query.upper())
    auto_patterns = [
        r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$',
        r'^[АВЕКМНОРСТУХ]{2}\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$',
        r'^[A-Z]\d{3}[A-Z]{2}\d{2,3}$',
    ]
    for pattern in auto_patterns:
        if re.match(pattern, auto_clean):
            return "auto", auto_clean
    
    # VIN
    vin_clean = re.sub(r'\s+', '', query.upper())
    if re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin_clean):
        return "vin", vin_clean
    
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
    
    # ОГРН
    if re.match(r'^\d{13}$', query):
        return "ogrn", query
    
    return "username", query

def check_api_key():
    return request.headers.get('X-API-Key') == MASTER_KEY

# ==================== ПОИСКОВЫЕ ФУНКЦИИ ====================

# BIGBASE
def search_bigbase(query, search_type):
    try:
        headers = {"Authorization": BIGBASE_KEY, "Content-Type": "application/json"}
        data = {"search": query, "page": 0}
        r = requests.post(BIGBASE_URL, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            result = r.json()
            result = sanitize_bigbase(result)
            if result.get("records") and result.get("count_result", 0) == 0:
                result["count_result"] = len(result["records"])
            return {"source": "bigbase", "data": result}
        return {"source": "bigbase", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "bigbase", "error": str(e)}

# WHITE SEARCH
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
        url = f"{WHITE_SEARCH_URL}{endpoint}"
        headers = {"X-API-Key": WHITE_SEARCH_KEY}
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

# INFINITY
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

# JITLER
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

# INTELX
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

# VK
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

# SNUSBASE
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

# ABUSEIPDB
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

# PROXYCHECK
def search_proxycheck(ip):
    try:
        r = requests.get(f"{PROXYCHECK_URL}{ip}", params={"key": PROXYCHECK_KEY}, timeout=10)
        if r.status_code == 200:
            return {"source": "proxycheck", "data": r.json()}
        return {"source": "proxycheck", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "proxycheck", "error": str(e)}

# HUDSON ROCK
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

# PROXYNOVA
def search_proxynova(query):
    try:
        r = requests.get(PROXYNOVA_URL, params={"query": query, "start": 0, "limit": 100}, timeout=15)
        if r.status_code == 200:
            return {"source": "proxynova", "data": r.json()}
        return {"source": "proxynova", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "proxynova", "error": str(e)}

# IP2LOCATION
def search_ip2location(ip):
    try:
        r = requests.get(IP2LOCATION_URL, params={"key": IP2LOCATION_KEY, "ip": ip}, timeout=10)
        if r.status_code == 200:
            return {"source": "ip2location", "data": r.json()}
        return {"source": "ip2location", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "ip2location", "error": str(e)}

# OFDATA
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

# FUNSTAT
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

# SMSC
def search_smsc():
    try:
        r = requests.get(SMSC_URL, params={"login": SMSC_LOGIN, "psw": SMSC_PASSWORD}, timeout=10)
        if r.status_code == 200:
            return {"source": "smsc", "data": r.text}
        return {"source": "smsc", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "smsc", "error": str(e)}

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
    
    # ===== BIGBASE (С КРАСИВЫМ ВЫВОДОМ) =====
    if search_type in ["phone", "email", "fio", "auto", "inn", "passport", "ip", "vin", "ogrn", "company"]:
        try:
            bigbase_raw = search_bigbase(query, search_type)
            if bigbase_raw.get("data"):
                # Формируем красивый текстовый отчёт
                bigbase_raw["formatted"] = format_bigbase_result(bigbase_raw["data"])
                # Убираем сырой data, чтобы не дублировать
                del bigbase_raw["data"]
            result["sources"].append(bigbase_raw)
        except Exception as e:
            result["sources"].append({"source": "bigbase", "error": str(e)})
    
    # ===== WHITE SEARCH =====
    if search_type in ["phone", "email", "fio", "telegram", "telegram_id", "telegram_username", "vk", "ip", "snils", "inn", "passport", "auto", "vin"]:
        try:
            result["sources"].append(search_white_search(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "white_search", "error": str(e)})
    
    # ===== INFINITY =====
    if search_type in ["phone", "email", "fio", "auto"]:
        try:
            result["sources"].append(search_infinity(query, search_type))
        except Exception as e:
            result["sources"].append({"source": "infinity", "error": str(e)})
    
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
    
    # ===== GITHUB =====
    if search_type == "username":
        try:
            result["sources"].append(search_github_user(query))
        except Exception as e:
            result["sources"].append({"source": "github", "error": str(e)})
    
    if search_type == "email":
        try:
            result["sources"].append(search_github_email(query))
        except Exception as e:
            result["sources"].append({"source": "github_email", "error": str(e)})
    
    return jsonify(result)

# ============================================
# AI ЧАТ (С ИСТОРИЕЙ 30 СООБЩЕНИЙ)
# ============================================
@app.route('/chat', methods=['POST'])
def chat():
    if not check_api_key():
        return jsonify({"error": "Неверный API-ключ"}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Нет данных"}), 400
    
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({"error": "Пустой запрос"}), 400
    
    user_id = data.get('user_id', 'default_user')
    model = data.get('model', 'google/gemma-4-26b-a4b-it:free')
    
    response = ask_anyapi(prompt, model, user_id=user_id)
    
    history = get_history(user_id)
    
    return jsonify({
        "prompt": prompt,
        "model": model,
        "response": response,
        "history_length": len(history),
        "max_history": MAX_HISTORY,
        "timestamp": datetime.now().isoformat()
    })

# ============================================
# ОЧИСТКА ИСТОРИИ
# ============================================
@app.route('/chat/clear', methods=['POST'])
def clear_chat():
    if not check_api_key():
        return jsonify({"error": "Неверный API-ключ"}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Нет данных"}), 400
    
    user_id = data.get('user_id', 'default_user')
    
    clear_history(user_id)
    
    return jsonify({
        "status": "ok",
        "message": f"История чата для {user_id} очищена"
    })

# ============================================
# GITHUB ЭНДПОИНТЫ
# ============================================
@app.route('/github/user/<username>', methods=['GET'])
def github_user(username):
    if not check_api_key():
        return jsonify({"error": "Неверный API-ключ"}), 403
    
    result = search_github_user(username)
    return jsonify(result)

@app.route('/github/email/<email>', methods=['GET'])
def github_email(email):
    if not check_api_key():
        return jsonify({"error": "Неверный API-ключ"}), 403
    
    result = search_github_email(email)
    return jsonify(result)

# ============================================
# TEMPMAIL
# ============================================
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
        "version": "16.0",
        "description": "OSINT-агрегатор с BigBase, White Search, Infinity, Jitler, IntelX, VK, Snusbase, AbuseIPDB, Proxycheck, Hudson Rock, Proxynova, IP2Location, OFDATA, Funstat, SMSC, GitHub, AnyAPI",
        "author": "@kmyfg",
        "sources": [
            "BigBase (ГРЗ, VIN, телефон, email, ФИО, ИНН, паспорт, IP, ОГРН) — с красивым выводом!",
            "White Search (ГРЗ, VIN, телефон, email, ФИО, Telegram, VK, IP, СНИЛС, ИНН)",
            "Infinity (ГРЗ, телефон, email, ФИО)",
            "Jitler (Telegram, телефон)",
            "IntelX (телефон)",
            "VK",
            "Snusbase (email, ФИО, IP)",
            "AbuseIPDB (IP)",
            "Proxycheck (IP)",
            "Hudson Rock (IP, username, email)",
            "Proxynova (email, ФИО, username)",
            "IP2Location (IP)",
            "OFDATA (ИНН, ОГРН, ФИО, компания)",
            "Funstat (Telegram ID)",
            "SMSC",
            "GitHub (username, email)",
            "AnyAPI (AI чат с историей 30 сообщений)"
        ],
        "total_sources": 17,
        "endpoints": {
            "/search": "POST - основной поиск (BigBase с красивым выводом)",
            "/chat": "POST - AI чат (AnyAPI, история 30 сообщений)",
            "/chat/clear": "POST - очистка истории чата",
            "/github/user/<username>": "GET - информация о пользователе GitHub",
            "/github/email/<email>": "GET - поиск email в GitHub",
            "/tempmail/generate": "GET - генерация временной почты",
            "/tempmail/check/<token>": "GET - проверка временной почты",
            "/health": "GET - статус"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)