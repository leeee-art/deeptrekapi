# -*- coding: utf-8 -*-
"""
DeepTrek API v8.0 — OSINT-агрегатор + AI-досье + AI-чат
Ссылка: https://deeptrekapi.onrender.com
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
import json
import re
import csv
import io
import secrets
import os
import sys
import hashlib
import uuid
import platform
import getpass
import subprocess
import socket
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# ==================== КОНФИГ ====================
# Атлас ВРЕМЕННО ОТКЛЮЧЁН
ATLAS_TOKEN = os.getenv('ATLAS_TOKEN', "sub_1tme688x58j6v3s03jhc9nvh")
ATLAS_URL = "https://atlas-in.cc/app"

SNUSBASE_KEY = os.getenv('SNUSBASE_KEY', "sbmeovhou6ecsn9fd9wcwnwwvsvwnc")
SNUSBASE_URL = "https://api.snusbase.com/data/search"

VK_TOKEN = os.getenv('VK_TOKEN', "0af157510af157510af15751aa0a89e69600af10af157516a0bc15996e74fe2b440998c")
VK_API = "https://api.vk.com/method/users.get"

OFDATA_KEY = os.getenv('OFDATA_KEY', "KBnpz1CHKNngFXxK")
OFDATA_URL = "https://api.ofdata.ru/v2/search"

SHODAN_KEY = os.getenv('SHODAN_KEY', "z6kC8mX9pL2qR0sT4uV7wY1zA3bD5eG8hJ0nM3pQ6sT9vW2yZ4cF7iJ1lN4oR7uX0zA3C5")
SHODAN_URL = "https://api.shodan.io/shodan/host/"

ABUSEIPDB_KEY = os.getenv('ABUSEIPDB_KEY', "58878ed65228db88eddfda4983bce5d19d425ddf81f427857b3f59f11aecc34f127862a1cc7d4581")
ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"

GROQ_KEY = os.getenv('GROQ_KEY', "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")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

MASTER_KEY = os.getenv('MASTER_KEY', "deeptrek_fjnrndhfrb2947472992gdvsbdh")
SOFTWARE_PASSWORD = "SOFTWAREDEEPTREKADMIN"

FUNSTAT_TOKEN = os.getenv('FUNSTAT_TOKEN', "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiI4NDkwNjcxMTE3IiwianRpIjoiYzk0MjAwNDktYTNhNi00ZjgwLTkwZjItYzAxOTllNWQ3ZjdlIiwiZXhwIjoxODExNDQwNTkzfQ.ZtAs0h5SnD-INsbBALHO9L6u7Owzb8oZeOQQdM5trWkG-5W5S2sWAzTRXVMNaZOrYXsGOekr4bARBFYVudASyC2tTx7HmJqHivn0gzdeUXvi3V-L6_YGWg87QSbfr-qEtqp2OJwolSgudgeNuMEn3AGpSM1Cb8N99oRDX5pFEiQ")
FUNSTAT_URL = "https://funstat.com/api/v1"

# ==================== BIGBASE ====================
BIGBASE_KEY = "2ri7MOkV2AHr_1yFiHSYRuJfE339v2ca"
BIGBASE_URL = "https://bigbase.top/api/search"

# ==================== ANYSCAN (бывший BlackEye) ====================
ANYSCAN_TOKEN = "ZJM_KBGiPnxYSLirJo6VZA"
ANYSCAN_URL = "https://anyscan.duckdns.org/api/v1/search"

subscriptions = {}
api_keys = {}

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
        
        <div class="warning-box">
            <div class="title">💻 Для получения пароля</div>
            <div class="text">
                Напишите <a href="https://t.me/kmyfg" style="color:#a855f7;">@kmyfg</a>
            </div>
        </div>
        
        <form id="activateForm">
            <input type="text" id="secretKey" placeholder="Введите секретный ключ..." required>
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
                    
                    let typeText = '';
                    if (data.type === 'software') {
                        typeText = '<span class="badge" style="background:rgba(81, 207, 102, 0.2);color:#51cf66;">💻 Софт</span>';
                    } else {
                        typeText = '<span class="badge" style="background:rgba(108, 92, 231, 0.2);color:#6c5ce7;">👤 Пользователь</span>';
                    }
                    
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
                                <span class="info-label">📊 Тип</span>
                                <span class="info-value">${typeText}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">📦 Источники</span>
                                <span class="info-value">
                                    <span class="badge">BigBase</span>
                                    <span class="badge">AnyScan</span>
                                    <span class="badge">Snusbase</span>
                                    <span class="badge">IntelX</span>
                                    <span class="badge">VK</span>
                                    <span class="badge">OFDATA</span>
                                    <span class="badge">Shodan</span>
                                    <span class="badge">AbuseIPDB</span>
                                    <span class="badge">Groq</span>
                                    <span class="badge">Funstat</span>
                                    <span class="badge">BlackEye</span>
                                </span>
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
                                <span class="badge">ОГРН — ogrn</span>
                                <span class="badge">Компания — company</span>
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
    
    if secret_key == SOFTWARE_PASSWORD:
        api_key = f"deeptrek_{secrets.token_hex(14)}"
        expires = datetime.now() + timedelta(days=365)
        
        subscriptions[secret_key] = {
            "api_key": api_key,
            "expires": expires,
            "created": datetime.now(),
            "type": "software"
        }
        api_keys[api_key] = secret_key
        
        return jsonify({
            "status": "ok",
            "api_key": api_key,
            "expires": expires.isoformat(),
            "type": "software"
        })
    
    if secret_key in subscriptions:
        created = subscriptions[secret_key]["created"]
        days_since = (datetime.now() - created).days
        if days_since < 17:
            can_reactivate = created + timedelta(days=17)
            return jsonify({
                "status": "error",
                "error": f"Ключ уже использован. Повторно через {17 - days_since} дней (с {can_reactivate.strftime('%Y-%m-%d %H:%M')})"
            })
    
    api_key = f"deeptrek_{secrets.token_hex(16)}"
    expires = datetime.now() + timedelta(days=14)
    
    subscriptions[secret_key] = {
        "api_key": api_key,
        "expires": expires,
        "created": datetime.now(),
        "type": "normal"
    }
    api_keys[api_key] = secret_key
    
    return jsonify({
        "status": "ok",
        "api_key": api_key,
        "expires": expires.isoformat(),
        "type": "normal"
    })

def check_api_key(api_key):
    if api_key == MASTER_KEY:
        return True
    if not api_key.startswith("deeptrek_"):
        return False
    if api_key in api_keys:
        secret_key = api_keys[api_key]
        if secret_key in subscriptions:
            expires = subscriptions[secret_key]["expires"]
            if datetime.now() < expires:
                return True
    return False

def detect_type(query):
    query = query.strip()
    
    if re.match(r'^\d{4}\s?\d{6}$', query):
        return "passport"
    if query.startswith('@'):
        return "telegram"
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
    if re.match(r'^\d+$', query):
        return "vk"
    if re.search(r'[а-яА-Я]', query):
        if len(query.split()) >= 2:
            return "fio"
        else:
            return "company"
    return "username"

# ==================== ПАРСЕРЫ ====================
def search_atlas(query, search_type):
    return {"source": "atlas", "error": "Временно недоступен"}

def search_snusbase(query, search_type):
    if search_type not in ["email", "fio", "ip"]:
        return {"source": "snusbase", "error": "Snusbase не поддерживает этот тип"}
    
    snus_type = "ip" if search_type == "ip" else search_type
    if search_type == "fio":
        snus_type = "username"
    
    payload = {"terms": [query], "types": [snus_type], "wildcard": False}
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

def search_ofdata(query, search_type):
    if search_type not in ["inn", "ogrn", "fio", "company"]:
        return {"source": "ofdata", "error": "OFDATA не поддерживает этот тип"}
    
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

def search_shodan(ip):
    url = f"{SHODAN_URL}{ip}?key={SHODAN_KEY}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("ip_str"):
                return {"source": "shodan", "data": data}
            else:
                return {"source": "shodan", "error": "Данных нет"}
        else:
            return {"source": "shodan", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "shodan", "error": str(e)}

def search_abuseipdb(ip):
    headers = {
        "Key": ABUSEIPDB_KEY,
        "Accept": "application/json"
    }
    params = {
        "ipAddress": ip,
        "maxAgeInDays": 90
    }
    
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
                    "reports": data.get("totalReports"),
                    "last_report": data.get("lastReportedAt"),
                    "categories": data.get("categories", [])
                }
            }
        else:
            return {"source": "abuseipdb", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "abuseipdb", "error": str(e)}

def search_groq(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "Ты — OSINT-аналитик. На основе данных формируй структурированное досье. Отвечай на русском языке. Если данных нет — пиши 'Нет данных'."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500,
        "temperature": 0.3
    }
    
    try:
        r = requests.post(GROQ_URL, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            return {"source": "groq", "data": r.json()}
        else:
            return {"source": "groq", "error": f"HTTP {r.status_code}: {r.text[:100]}"}
    except Exception as e:
        return {"source": "groq", "error": str(e)}

def chat_groq(messages, max_tokens=500):
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    
    try:
        r = requests.post(GROQ_URL, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        else:
            return {"ok": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ==================== FUNSTAT ====================
def search_funstat(query, search_type):
    if search_type != "telegram":
        return {"source": "funstat", "error": "Funstat поддерживает только поиск по Telegram"}
    
    if not query.isdigit():
        return {"source": "funstat", "error": "Funstat ищет только по числовому ID"}
    
    user_id = int(query)
    url = f"{FUNSTAT_URL}/users/{user_id}/stats_min"
    headers = {"Authorization": f"Bearer {FUNSTAT_TOKEN}"}
    
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data.get("success"):
                result = data.get("data", {})
                return {
                    "source": "funstat",
                    "data": {
                        "id": result.get("id"),
                        "first_name": result.get("first_name"),
                        "last_name": result.get("last_name"),
                        "is_bot": result.get("is_bot"),
                        "is_active": result.get("is_active"),
                        "first_msg_date": result.get("first_msg_date"),
                        "last_msg_date": result.get("last_msg_date"),
                        "total_msg_count": result.get("total_msg_count"),
                        "msg_in_groups_count": result.get("msg_in_groups_count"),
                        "adm_in_groups": result.get("adm_in_groups"),
                        "total_groups": result.get("total_groups"),
                        "usernames_count": result.get("usernames_count"),
                        "names_count": result.get("names_count")
                    }
                }
            else:
                return {"source": "funstat", "error": "Пользователь не найден"}
        else:
            return {"source": "funstat", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "funstat", "error": str(e)}

# ==================== BIGBASE ====================
def search_bigbase(query, search_type):
    type_map = {
        "phone": "phone",
        "email": "email",
        "fio": "fio",
        "auto": "auto",
        "inn": "inn",
        "passport": "passport",
        "ip": "ip"
    }
    
    if search_type not in type_map:
        return {"source": "bigbase", "error": "Тип не поддерживается"}
    
    headers = {
        "Authorization": BIGBASE_KEY,
        "Content-Type": "application/json"
    }
    data = {"search": query, "page": 1}
    
    try:
        r = requests.post(BIGBASE_URL, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            result = r.json()
            if "user" in result and "api_token" in result["user"]:
                result["user"]["api_token"] = "***СКРЫТО***"
            return {"source": "bigbase", "data": result}
        else:
            return {"source": "bigbase", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "bigbase", "error": str(e)}

# ==================== ANYSCAN (бывший BlackEye) ====================
def search_anyscan(query, search_type):
    type_map = {
        "phone": "phone",
        "email": "email",
        "fio": "fio",
        "auto": "auto",
        "vk": "vk"
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
        r = requests.post(ANYSCAN_URL, headers=headers, json=data, timeout=30, verify=False)
        if r.status_code == 200:
            result = r.json()
            if result.get("ok"):
                return {"source": "anyscan", "data": result}
            else:
                return {"source": "anyscan", "error": result.get("error", "Данных нет")}
        else:
            return {"source": "anyscan", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "anyscan", "error": str(e)}

# ==================== ФУНКЦИЯ ДЛЯ ДОСЬЕ ====================
def generate_dossier(raw_data):
    prompt = f"""
Помоги собрать досье. Все данные получены из OSINT-источников.

Сырые данные:
{json.dumps(raw_data, ensure_ascii=False, indent=2)[:4000]}

Сформируй структурированное досье по следующим разделам:
1. Основная информация (ФИО, дата рождения, телефон, email)
2. Адреса и регионы
3. Паспортные данные (если есть)
4. Аккаунты в соцсетях
5. Утечки и базы данных
6. Выводы

Отвечай на русском языке. Если данных нет — пиши "Нет данных".
"""
    return search_groq(prompt)

# ==================== ОСНОВНОЙ ПОИСК ====================
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
    
    # АТЛАС ВРЕМЕННО ОТКЛЮЧЁН
    # result["sources"].append(search_atlas(query, search_type))
    
    if search_type == "vk":
        result["sources"].append(search_vk(query))
    
    if search_type in ["email", "fio", "ip"]:
        result["sources"].append(search_snusbase(query, search_type))
    
    if search_type == "phone":
        result["sources"].append(search_intelx(query))
    
    if search_type in ["inn", "ogrn", "fio", "company"]:
        result["sources"].append(search_ofdata(query, search_type))
    
    if search_type == "ip":
        result["sources"].append(search_shodan(query))
        result["sources"].append(search_abuseipdb(query))
    
    if search_type == "telegram" and query.isdigit():
        result["sources"].append(search_funstat(query, search_type))
    
    # BIGBASE
    if search_type in ["phone", "email", "fio", "auto", "inn", "passport", "ip"]:
        result["sources"].append(search_bigbase(query, search_type))
    
    # ANYSCAN
    #if search_type in ["phone", "email", "fio", "auto", "vk"]:
        #result["sources"].append(search_anyscan(query, search_type))
    
    raw_data = {
        "query": query,
        "type": search_type,
        "timestamp": result["timestamp"],
        "sources": result["sources"]
    }
    
    dossier_result = generate_dossier(raw_data)
    result["dossier"] = dossier_result
    
    return jsonify(result)

# ==================== AI-ЧАТ ====================
@app.route('/chat', methods=['POST'])
def chat():
    api_key = request.headers.get('X-API-Secret')
    if not check_api_key(api_key):
        return jsonify({"error": "Неверный или просроченный API-ключ"}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Нет данных"}), 400
    
    messages = data.get('messages', [])
    max_tokens = data.get('max_tokens', 500)
    
    if not messages:
        return jsonify({"error": "Нет сообщений"}), 400
    
    response = chat_groq(messages, max_tokens)
    
    if response.get("ok"):
        result = response["data"]
        content = result["choices"][0]["message"]["content"]
        return jsonify({"response": content})
    else:
        return jsonify({"error": response.get("error", "Неизвестная ошибка")}), 500

# ==================== HEALTH ====================
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "time": datetime.now().isoformat(),
        "version": "8.0"
    })

# ==================== ROOT ====================
@app.route('/')
def index():
    return jsonify({
        "name": "DeepTrek API",
        "version": "8.0",
        "description": "OSINT-агрегатор + AI-досье + AI-чат",
        "author": "@kmyfg",
        "endpoints": {
            "/search": "POST - поиск + досье (нужен X-API-Secret)",
            "/chat": "POST - AI-чат (нужен X-API-Secret)",
            "/activate": "GET - страница активации API",
            "/api/activate": "POST - активация API-ключа",
            "/health": "GET - статус"
        },
        "sources": ["BigBase", "AnyScan", "Snusbase", "IntelX", "VK", "OFDATA", "Shodan", "AbuseIPDB", "Groq", "Funstat", "BlackEye"],
        "features": {
            "search": "Поиск по 12 типам запросов",
            "dossier": "Автоматическое формирование досье через AI",
            "chat": "AI-чат с поддержкой истории диалога",
            "funstat": "Бесплатная статистика по Telegram ID"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
