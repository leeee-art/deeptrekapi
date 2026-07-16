# -*- coding: utf-8 -*-
"""
DeepTrek API v8.0
OSINT-агрегатор для поиска по открытым источникам

Ссылка: https://deeptrekapi.onrender.com
Автор: @kmyfg
"""

from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import requests
import json
import re
import csv
import io
import secrets
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# ==================== КОНФИГУРАЦИЯ ====================
# Все ключи вынесены в переменные окружения для безопасности
# Если переменная не задана, используется значение по умолчанию

# Атлас — основной источник (ФИО, телефон, email, авто, ИНН, СНИЛС, паспорт, IP)
ATLAS_TOKEN = os.getenv('ATLAS_TOKEN', "sub_1tme688x58j6v3s03jhc9nvh")
ATLAS_URL = "https://atlas-in.cc/app"

# BlackEye — временно отключён
BLACKEYE_TOKEN = os.getenv('BLACKEYE_TOKEN', "")
BLACKEYE_URL = "https://blackeyebot.duckdns.org/api/v1/search"

# Snusbase — базы утечек (email, username, IP)
SNUSBASE_KEY = os.getenv('SNUSBASE_KEY', "sbmeovhou6ecsn9fd9wcwnwwvsvwnc")
SNUSBASE_URL = "https://api.snusbase.com/data/search"

# VK API — поиск по ID
VK_TOKEN = os.getenv('VK_TOKEN', "0af157510af157510af15751aa0a89e69600af10af157516a0bc15996e74fe2b440998c")
VK_API = "https://api.vk.com/method/users.get"

# OFDATA — государственные реестры (ИНН, ОГРН, ФИО, компании)
OFDATA_KEY = os.getenv('OFDATA_KEY', "KBnpz1CHKNngFXxK")
OFDATA_URL = "https://api.ofdata.ru/v2/search"

# Мастер-ключ для бота
MASTER_KEY = os.getenv('MASTER_KEY', "deeptrek_fjnrndhfrb2947472992gdvsbdh")

# Пароль для активации софта (выдаётся вручную через @kmyfg)
SOFTWARE_PASSWORD = "SOFTWAREDEEPTREKADMIN"

# RaidfindSoft — бесплатный, но слабый источник
RAIDFIND_URL = "http://204.12.227.173:6414/search"

# ==================== ХРАНИЛИЩЕ ====================
# subscriptions: {secret_key: {"api_key": str, "expires": datetime, "created": datetime, "type": str}}
# api_keys: {api_key: secret_key}
subscriptions = {}
api_keys = {}

# ==================== HTML-СТРАНИЦЫ ====================
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
                                    <span class="badge">Atlas</span>
                                    <span class="badge">Snusbase</span>
                                    <span class="badge">IntelX</span>
                                    <span class="badge">VK</span>
                                    <span class="badge">OFDATA</span>
                                    <span class="badge">Raidfind</span>
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

SOFT_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepTrek — Софт</title>
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
            max-width: 800px;
            width: 100%;
            background: #151528;
            border-radius: 20px;
            padding: 40px;
            border: 1px solid #6c5ce7;
            box-shadow: 0 0 40px rgba(108, 92, 231, 0.15);
        }
        .logo { font-size: 32px; font-weight: 700; background: linear-gradient(135deg, #6c5ce7, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 4px; }
        .subtitle { text-align: center; color: #888; font-size: 14px; margin-bottom: 25px; }
        .code-box {
            background: #0a0a18;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 13px;
            color: #c0c0c0;
            overflow-x: auto;
            margin: 15px 0;
            border: 1px solid #2a2a4a;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, #6c5ce7, #a855f7);
            border: none;
            border-radius: 8px;
            color: #fff;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: 0.3s;
        }
        .btn:hover { transform: scale(1.02); box-shadow: 0 0 30px rgba(108, 92, 231, 0.3); }
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
        <div class="logo">💻 DeepTrek Soft</div>
        <div class="subtitle">Терминальный OSINT-клиент</div>
        
        <div class="warning-box">
            <div class="title">🔑 Как получить доступ:</div>
            <div class="text">
                1. Перейди на <a href="/activate" style="color:#a855f7;">страницу активации</a><br>
                2. Получи пароль у <a href="https://t.me/kmyfg" style="color:#a855f7;">@kmyfg</a><br>
                3. Введи пароль на странице активации<br>
                4. Получи API-ключ для софта
            </div>
        </div>
        
        <h3 style="margin-top:20px;color:#a855f7;">📥 Скачать софт:</h3>
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin:15px 0;">
            <a href="/download/soft.py" class="btn">🐍 Python (скрипт)</a>
        </div>
        
        <h3 style="margin-top:20px;color:#a855f7;">📋 Команды софта:</h3>
        <div class="code-box">
            > help                  - справка
            > search +79123456789   - поиск по телефону
            > search user@mail.ru   - поиск по email
            > search Иванов Иван    - поиск по ФИО
            > search А123ВС77       - поиск по авто
            > search 7712345678     - поиск по ИНН
            > exit                  - выход
        </div>
        
        <div class="footer">DeepTrek Soft © 2026</div>
    </div>
</body>
</html>
'''

SOFT_SCRIPT = '''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepTrek Soft — клиент для терминального поиска
"""

import requests
import json
import os
import sys
import shutil
from datetime import datetime

BASE_URL = "https://deeptrekapi.onrender.com"
API_URL = f"{BASE_URL}/search"
ACTIVATE_URL = f"{BASE_URL}/api/activate"

RESET = "\\033[0m"
BOLD = "\\033[1m"
RED = "\\033[91m"
GREEN = "\\033[92m"
YELLOW = "\\033[93m"
CYAN = "\\033[96m"
WHITE = "\\033[97m"
MAGENTA = "\\033[95m"
DIM = "\\033[2m"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def get_width():
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80

def center(text):
    width = get_width()
    lines = text.split('\\n')
    result = []
    for line in lines:
        clean = line
        for code in [RESET, BOLD, RED, GREEN, YELLOW, CYAN, WHITE, MAGENTA, DIM]:
            clean = clean.replace(code, '')
        pad = max(0, (width - len(clean)) // 2)
        result.append(" " * pad + line)
    return '\\n'.join(result)

def print_banner():
    banner = """
    ██████╗ ███████╗███████╗██████╗ ████████╗██████╗ ███████╗██╗  ██╗
    ██╔══██╗██╔════╝██╔════╝██╔══██╗╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝
    ██║  ██║█████╗  █████╗  ██████╔╝   ██║   ██████╔╝█████╗  █████╔╝ 
    ██║  ██║██╔══╝  ██╔══╝  ██╔══██╗   ██║   ██╔══██╗██╔══╝  ██╔═██╗ 
    ██████╔╝███████╗███████╗██║  ██║   ██║   ██║  ██║███████╗██║  ██╗
    ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
    """
    print(center(banner))
    print(center("🔍 OSINT-клиент для DeepTrek API"))
    print(center("📌 Версия 2.0"))
    print(center("🌐 " + BASE_URL))
    print()

def get_api_key():
    print(center(f"{CYAN}🔑 Введите пароль для активации:{RESET}"))
    print(center(f"{YELLOW}ℹ️  Пароль можно получить у @kmyfg на {BASE_URL}/activate{RESET}"))
    print()
    
    password = input(center(f"{WHITE}Пароль: {RESET}")).strip()
    
    if not password:
        print(center(f"{RED}❌ Пароль не может быть пустым{RESET}"))
        return None
    
    print(center(f"{CYAN}⏳ Активация...{RESET}"))
    
    try:
        r = requests.post(ACTIVATE_URL, json={"secret_key": password}, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "ok":
                api_key = data.get("api_key")
                expires = data.get("expires", "неизвестно")
                print(center(f"{GREEN}✅ API-ключ получен!{RESET}"))
                print(center(f"{GREEN}📅 Действует до: {expires[:16]}{RESET}"))
                return api_key
            else:
                print(center(f"{RED}❌ {data.get('error', 'Неизвестная ошибка')}{RESET}"))
                return None
        else:
            print(center(f"{RED}❌ HTTP {r.status_code}{RESET}"))
            return None
    except requests.exceptions.Timeout:
        print(center(f"{RED}❌ Таймаут. Проверь интернет.{RESET}"))
        return None
    except Exception as e:
        print(center(f"{RED}❌ Ошибка: {str(e)}{RESET}"))
        return None

def search(api_key, query):
    try:
        r = requests.post(API_URL, headers={"X-API-Secret": api_key}, json={"query": query}, timeout=60)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        elif r.status_code == 403:
            return {"ok": False, "error": "Неверный API-ключ"}
        else:
            return {"ok": False, "error": f"HTTP {r.status_code}"}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "Таймаут"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def print_result(data):
    if not data.get("ok"):
        print(f"{RED}❌ Ошибка: {data.get('error', 'Неизвестная ошибка')}{RESET}")
        return
    
    result = data.get("data", {})
    
    print(f"\\n{GREEN}✅ Найдено!{RESET}")
    print(f"{CYAN}📱 Запрос: {result.get('query', '')}{RESET}")
    print(f"{CYAN}📅 Время: {result.get('timestamp', '')[:16]}{RESET}")
    print(f"{CYAN}📊 Тип: {result.get('type', '')}{RESET}")
    print()
    
    for source in result.get('sources', []):
        if 'error' in source:
            print(f"{RED}❌ {source.get('source', '').upper()}: {source.get('error', 'Ошибка')}{RESET}")
            continue
        
        src_name = source.get('source', '').upper()
        print(f"{GREEN}✅ {src_name}{RESET}")
        
        if src_name == "ATLAS":
            data = source.get('data', {})
            fast = data.get('fast_result', {})
            sources = data.get('result', {}).get('sources', {})
            bases = sources.get('Базы Данных', [])
            
            if fast:
                print(f"  {YELLOW}📌 Быстрый результат:{RESET}")
                if fast.get('fullname'):
                    print(f"    {WHITE}ФИО:{RESET} {', '.join([x[0] for x in fast['fullname'][:5]])}")
                if fast.get('birthday'):
                    print(f"    {WHITE}Даты рождения:{RESET} {', '.join([x[0] for x in fast['birthday'][:3]])}")
                if fast.get('email'):
                    print(f"    {WHITE}Email:{RESET} {', '.join([x[0] for x in fast['email'][:3]])}")
                if fast.get('phone'):
                    print(f"    {WHITE}Телефоны:{RESET} {', '.join([x[0] for x in fast['phone'][:3]])}")
                if fast.get('region'):
                    print(f"    {WHITE}Регионы:{RESET} {', '.join([x[0][:50] for x in fast['region'][:2]])}")
            
            if bases:
                print(f"  {MAGENTA}📂 Базы данных ({len(bases)} записей):{RESET}")
                for i, entry in enumerate(bases[:5], 1):
                    print(f"    {DIM}{i}.{RESET}")
                    for key, value in entry.items():
                        if key in ['source', 'phone', 'fio', 'email', 'address', 'bdate', 'inn', 'passport']:
                            print(f"      {WHITE}{key}:{RESET} {value}")
                    print()
        
        elif src_name == "INTELX":
            data = source.get('data', [])
            if data:
                print(f"  {MAGENTA}📂 IntelX данные ({len(data)} записей):{RESET}")
                for entry in data[:3]:
                    print(f"    {entry}")
        
        elif src_name == "OFDATA":
            data = source.get('data', {})
            if data.get('data', {}).get('Записи'):
                entries = data['data']['Записи']
                print(f"  {MAGENTA}📂 OFDATA ({len(entries)} записей):{RESET}")
                for entry in entries[:3]:
                    if 'НаимСокр' in entry:
                        print(f"    {WHITE}Компания:{RESET} {entry.get('НаимСокр', '')}")
                    if 'ФИО' in entry:
                        print(f"    {WHITE}ФИО:{RESET} {entry.get('ФИО', '')}")
                    if 'ИНН' in entry:
                        print(f"    {WHITE}ИНН:{RESET} {entry.get('ИНН', '')}")
                    print()
        
        elif src_name == "SNUSBASE":
            data = source.get('data', {})
            if data.get('results'):
                print(f"  {MAGENTA}📂 Snusbase данные:{RESET}")
                for entry in data['results'][:3]:
                    print(f"    {entry}")
        
        elif src_name == "VK":
            data = source.get('data', [])
            if data:
                print(f"  {MAGENTA}📂 VK данные:{RESET}")
                for entry in data:
                    if 'first_name' in entry:
                        print(f"    {WHITE}Имя:{RESET} {entry.get('first_name', '')} {entry.get('last_name', '')}")
                        print(f"    {WHITE}Статус:{RESET} {entry.get('status', '')}")
                        print(f"    {WHITE}Страна:{RESET} {entry.get('country', {}).get('title', '')}")
    
    print()
    print(center(f"{YELLOW}📄 Полный JSON:{RESET}"))
    print(center(json.dumps(result, ensure_ascii=False, indent=2)[:2000]))

def main():
    clear()
    print_banner()
    
    api_key = get_api_key()
    if not api_key:
        print(center(f"{RED}❌ Не удалось получить API-ключ. Выход...{RESET}"))
        sys.exit(1)
    
    while True:
        print()
        print(center(f"{GREEN}┌────────────────────────────────────────────────────┐{RESET}"))
        print(center(f"{GREEN}│  {WHITE}Введите запрос или 'exit' для выхода                   {GREEN}│{RESET}"))
        print(center(f"{GREEN}│  {DIM}help - справка по типам запросов                     {GREEN}│{RESET}"))
        print(center(f"{GREEN}└────────────────────────────────────────────────────┘{RESET}"))
        print()
        
        query = input(center(f"{CYAN}🔍 > {RESET}")).strip()
        
        if not query:
            continue
        
        if query.lower() in ["exit", "quit", "q"]:
            print(center(f"{GREEN}👋 До свидания!{RESET}"))
            break
        
        if query.lower() == "help":
            print(center(f"{YELLOW}📋 Примеры запросов:{RESET}"))
            print(center(f"{WHITE}  +79123456789  - телефон{RESET}"))
            print(center(f"{WHITE}  user@mail.ru  - email{RESET}"))
            print(center(f"{WHITE}  Иванов Иван   - ФИО{RESET}"))
            print(center(f"{WHITE}  А123ВС77      - авто{RESET}"))
            print(center(f"{WHITE}  7712345678    - ИНН{RESET}"))
            continue
        
        print(center(f"{CYAN}⏳ Поиск...{RESET}"))
        
        result = search(api_key, query)
        print_result(result)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(center(f"\\n{GREEN}👋 Выход...{RESET}"))
        sys.exit(0)
'''

# ==================== ЭНДПОИНТЫ ====================

@app.route('/')
def index():
    """Главная страница API"""
    return jsonify({
        "name": "DeepTrek API",
        "version": "8.0",
        "description": "OSINT-агрегатор для поиска по открытым источникам",
        "author": "@kmyfg",
        "endpoints": {
            "/search": {
                "method": "POST",
                "description": "Поиск по запросу",
                "headers": {"X-API-Secret": "Ваш API-ключ"},
                "body": {"query": "строка запроса", "type": "тип (опционально)"},
                "example": 'curl -X POST https://deeptrekapi.onrender.com/search -H "X-API-Secret: KEY" -d \'{"query": "+79123456789"}\''
            },
            "/activate": {
                "method": "GET",
                "description": "Страница активации API-ключа"
            },
            "/api/activate": {
                "method": "POST",
                "description": "Активация API-ключа по секретному ключу",
                "body": {"secret_key": "секретный ключ"}
            },
            "/soft": {
                "method": "GET",
                "description": "Страница с софтом для скачивания"
            },
            "/download/soft.py": {
                "method": "GET",
                "description": "Скачать скрипт для терминального поиска"
            },
            "/health": {
                "method": "GET",
                "description": "Проверка статуса сервера"
            }
        },
        "sources": ["Atlas", "Snusbase", "IntelX", "VK", "OFDATA", "Raidfind"],
        "supported_types": {
            "phone": "Номер телефона (79123456789)",
            "email": "Email (user@mail.ru)",
            "fio": "ФИО (Иванов Иван)",
            "auto": "Госномер (А123ВС77)",
            "inn": "ИНН (7712345678)",
            "ogrn": "ОГРН (1027700132195)",
            "snils": "СНИЛС (12345678900)",
            "passport": "Паспорт (1234 567890)",
            "ip": "IP-адрес (8.8.8.8)",
            "telegram": "Telegram (@username)",
            "vk": "VK ID (123456)",
            "company": "Название компании (ООО Ромашка)"
        }
    })

@app.route('/activate')
def activate_page():
    """Страница активации API-ключа"""
    return render_template_string(ACTIVATE_HTML)

@app.route('/soft')
def soft_page():
    """Страница с софтом"""
    return render_template_string(SOFT_PAGE)

@app.route('/download/soft.py')
def download_soft():
    """Скачать скрипт софта"""
    return SOFT_SCRIPT, 200, {'Content-Type': 'text/x-python', 'Content-Disposition': 'attachment; filename=soft.py'}

@app.route('/api/activate', methods=['POST'])
def activate():
    """
    Активация API-ключа
    ---
    tags:
      - Активация
    parameters:
      - name: secret_key
        in: body
        required: true
        schema:
          type: object
          properties:
            secret_key:
              type: string
    responses:
      200:
        description: Успешная активация
        schema:
          type: object
          properties:
            status:
              type: string
            api_key:
              type: string
            expires:
              type: string
            type:
              type: string
    """
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
    """Проверка валидности API-ключа"""
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
    """Автоопределение типа запроса"""
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

# ==================== ПАРСЕРЫ ИСТОЧНИКОВ ====================

def search_atlas(query, search_type):
    """Поиск через Атлас — основной источник"""
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

def search_snusbase(query, search_type):
    """Поиск через Snusbase — базы утечек"""
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
    """Поиск через IntelX — открытые CSV-базы по номерам телефонов"""
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
    """Поиск через VK API по ID"""
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
    """Поиск через OFDATA — государственные реестры"""
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

def search_raidfind(query, search_type):
    """Поиск через RaidfindSoft — бесплатный, но слабый источник"""
    type_map = {
        "phone": "phone",
        "email": "email",
        "fio": "fio",
        "vk": "vk"
    }
    if search_type not in type_map:
        return {"source": "raidfind", "error": "Raidfind не поддерживает этот тип"}
    payload = {
        "phone": query,
        "mode": "premium",
        "query_type": type_map[search_type]
    }
    try:
        r = requests.post(RAIDFIND_URL, json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("ok"):
                return {"source": "raidfind", "data": data}
            else:
                return {"source": "raidfind", "error": data.get("error", "Данных нет")}
        else:
            return {"source": "raidfind", "error": f"HTTP {r.status_code}"}
    except requests.exceptions.Timeout:
        return {"source": "raidfind", "error": "Таймаут"}
    except Exception as e:
        return {"source": "raidfind", "error": str(e)}

# ==================== ОСНОВНОЙ ЭНДПОИНТ ====================

@app.route('/search', methods=['POST'])
def search():
    """
    Поиск по открытым источникам
    ---
    tags:
      - Поиск
    parameters:
      - name: X-API-Secret
        in: header
        required: true
        type: string
      - name: query
        in: body
        required: true
        schema:
          type: object
          properties:
            query:
              type: string
            type:
              type: string
    responses:
      200:
        description: Результат поиска
        schema:
          type: object
          properties:
            query:
              type: string
            type:
              type: string
            timestamp:
              type: string
            sources:
              type: array
    """
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
    
    # Атлас — почти всё
    result["sources"].append(search_atlas(query, search_type))
    
    # Snusbase — email, fio, ip
    if search_type in ["email", "fio", "ip"]:
        result["sources"].append(search_snusbase(query, search_type))
    
    # IntelX — только телефоны
    if search_type == "phone":
        result["sources"].append(search_intelx(query))
    
    # VK — числа (ID)
    if search_type == "vk":
        result["sources"].append(search_vk(query))
    
    # OFDATA — ИНН, ОГРН, ФИО, компании
    if search_type in ["inn", "ogrn", "fio", "company"]:
        result["sources"].append(search_ofdata(query, search_type))
    
    # Telegram — через Атлас
    if search_type == "telegram":
        result["sources"].append(search_atlas(query, search_type))
    
    # Авто — через Атлас
    if search_type == "auto":
        result["sources"].append(search_atlas(query, search_type))
    
    # Raidfind — телефон, email, ФИО, VK
    if search_type in ["phone", "email", "fio", "vk"]:
        result["sources"].append(search_raidfind(query, search_type))
    
    return jsonify(result)

@app.route('/health')
def health():
    """Проверка статуса сервера"""
    return jsonify({
        "status": "ok",
        "time": datetime.now().isoformat(),
        "version": "8.0"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
