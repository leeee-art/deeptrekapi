from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import re
import csv
import io
import socket
import whois
import dns.resolver
import yt_dlp
from datetime import datetime

app = Flask(__name__)
CORS(app)

API_SECRET = "deeptrek_fjnrndhfrb2947472992gdvsbdh"

# ==================== ТОКЕНЫ ====================
ATLAS_TOKEN = "sub_1tme688x58j6v3s03jhc9nvh"
ATLAS_URL = "https://atlas-in.cc/app"

BLACKEYE_TOKEN = "y06BzECXTqtOjzdIcTVQPw"
BLACKEYE_URL = "https://blackeyebot.duckdns.org/api/v1/search"

SNUSBASE_KEY = "sbmeovhou6ecsn9fd9wcwnwwvsvwnc"
SNUSBASE_URL = "https://api.snusbase.com/data/search"

VK_TOKEN = "0af157510af157510af15751aa0a89e69600af10af157516a0bc15996e74fe2b440998c"
VK_API = "https://api.vk.com/method/users.get"

VERIPHONE_KEY = "A9A2A88762854D45888BA49E8F98509C"
OMKAR_API_KEY = "ok_ad50fb80682eff950d34e7a9b3a77c8c"

# ==================== АВТО-ОПРЕДЕЛЕНИЕ ТИПА ====================
def detect_type(query):
    query = query.strip()
    
    # ФИО — если есть русские буквы
    if re.search(r'[а-яА-Я]', query):
        return "fio"
    
    # YouTube ссылка
    if re.search(r'(youtube\.com|youtu\.be)', query):
        return "youtube"
    
    # TikTok
    if re.search(r'tiktok\.com/@', query):
        return "tiktok"
    
    # Email
    if re.search(r'@', query):
        return "email"
    
    # Телефон
    if re.match(r'^[78]\d{10}$', re.sub(r'\D', '', query)):
        return "phone"
    
    # IP
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', query):
        return "ip"
    
    # Госномер
    if re.match(r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$', query, re.IGNORECASE):
        return "auto"
    
    # VIN
    if re.match(r'^[A-HJ-NPR-Z0-9]{17}$', query, re.IGNORECASE):
        return "vin"
    
    # ИНН
    if re.match(r'^\d{10}$|^\d{12}$', query):
        return "inn"
    
    # СНИЛС
    if re.match(r'^\d{11}$', re.sub(r'\D', '', query)):
        return "snils"
    
    # Паспорт
    if re.match(r'^\d{4}\s?\d{6}$', query) or re.match(r'^\d{10}$', query):
        return "passport"
    
    # Telegram
    if query.startswith('@'):
        return "telegram"
    
    # VK
    if re.match(r'^\d+$', query):
        return "vk"
    
    return "username"

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
        "sources": []
    }
    
    # === ATLAS ===
    result["sources"].append(search_atlas(query, search_type))
    
    # === BLACKEYE ===
    result["sources"].append(search_blackeye(query, search_type))
    
    # === SNUSBASE ===
    if search_type in ["email", "username", "fio"]:
        result["sources"].append(search_snusbase(query, search_type))
    
    # === INTELX ===
    if search_type == "phone":
        result["sources"].append(search_intelx(query))
    
    # === VK ===
    if search_type == "vk":
        result["sources"].append(search_vk(query))
    
    # === TIKTOK ===
    if search_type == "tiktok":
        result["sources"].append(search_tiktok(query))
    
    # === YOUTUBE ===
    if search_type == "youtube":
        result["sources"].append(search_youtube(query))
    
    # === VERIPHONE ===
    if search_type == "phone":
        result["sources"].append(search_veriphone(query))
    
    # === WHATSAPP ===
    if search_type == "phone":
        result["sources"].append(search_whatsapp(query))
    
    # === ODNOKLASSNIKI ===
    if search_type == "phone":
        result["sources"].append(search_odnoklassniki(query))
    
    # === OMKAR PHONE ===
    if search_type == "phone":
        result["sources"].append(search_omkar_phone(query))
    
    # === OMKAR EMAIL ===
    if search_type == "email":
        result["sources"].append(search_omkar_email(query))
    
    # === BIN CARD ===
    if re.match(r'^\d{6,8}$', query):
        result["sources"].append(search_card_bin(query))
    
    # === БАНК ПО ИНН ===
    if search_type == "inn":
        result["sources"].append(search_bank_by_inn(query))
    
    # === WHOIS ===
    if '.' in query and not re.search(r'[а-яА-Я]', query):
        result["sources"].append(search_whois(query))
        result["sources"].append(search_dns(query))
    
    return jsonify(result)

# ==================== ВСЕ ПАРСЕРЫ ====================

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

def search_tiktok(query):
    username = query.replace('@', '').strip()
    if 'tiktok.com/@' in query:
        username = query.split('tiktok.com/@')[-1].split('/')[0]
    url = f"https://www.tiktok.com/@{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            followers = re.search(r'"followerCount":(\d+)', r.text)
            followers = int(followers.group(1)) if followers else 0
            name = re.search(r'"nickname":"([^"]+)"', r.text)
            name = name.group(1) if name else None
            likes = re.search(r'"heartCount":(\d+)', r.text)
            likes = int(likes.group(1)) if likes else 0
            return {"source": "tiktok", "data": {"username": username, "name": name, "followers": followers, "likes": likes}}
        return {"source": "tiktok", "error": "Пользователь не найден"}
    except Exception as e:
        return {"source": "tiktok", "error": str(e)}

def search_youtube(query):
    try:
        ydl_opts = {'quiet': True, 'extract_flat': False, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if info:
                return {"source": "youtube", "data": {
                    "title": info.get('title'),
                    "description": info.get('description'),
                    "view_count": info.get('view_count'),
                    "like_count": info.get('like_count'),
                    "duration": info.get('duration_string'),
                    "channel": info.get('channel'),
                    "channel_url": info.get('channel_url'),
                    "upload_date": info.get('upload_date'),
                    "url": info.get('webpage_url'),
                    "thumbnail": info.get('thumbnail')
                }}
        return {"source": "youtube", "error": "Не удалось получить информацию"}
    except Exception as e:
        return {"source": "youtube", "error": str(e)}

def search_veriphone(phone):
    phone_clean = re.sub(r'\D', '', phone)
    url = "https://api.veriphone.io/v2/verify"
    params = {"phone": phone_clean, "key": VERIPHONE_KEY}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {"source": "veriphone", "data": {
                "valid": data.get("valid"),
                "country": data.get("country_code"),
                "carrier": data.get("carrier"),
                "type": data.get("phone_type")
            }}
        return {"source": "veriphone", "error": f"Код: {r.status_code}"}
    except Exception as e:
        return {"source": "veriphone", "error": str(e)}

def search_whatsapp(phone):
    phone_clean = re.sub(r'\D', '', phone)
    if phone_clean.startswith('8'):
        phone_clean = '7' + phone_clean[1:]
    elif not phone_clean.startswith('7'):
        phone_clean = '7' + phone_clean
    try:
        r = requests.get(f"https://wa.me/{phone_clean}", timeout=10, allow_redirects=True)
        if r.status_code == 200:
            if "This phone number is not on WhatsApp" in r.text:
                return {"source": "whatsapp", "data": {"exists": False, "phone": phone_clean}}
            else:
                return {"source": "whatsapp", "data": {"exists": True, "phone": phone_clean}}
        return {"source": "whatsapp", "error": f"Код: {r.status_code}"}
    except Exception as e:
        return {"source": "whatsapp", "error": str(e)}

def search_odnoklassniki(phone):
    phone_clean = re.sub(r'\D', '', phone)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        url = "https://ok.ru/search"
        params = {"st.mode": "Users", "st.query": phone_clean}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            match = re.search(r'num-found["\s]*:["\s]*(\d+)', r.text)
            if match and int(match.group(1)) > 0:
                return {"source": "odnoklassniki", "data": {"exists": True, "phone": phone_clean}}
            else:
                return {"source": "odnoklassniki", "data": {"exists": False, "phone": phone_clean}}
        return {"source": "odnoklassniki", "error": f"Код: {r.status_code}"}
    except Exception as e:
        return {"source": "odnoklassniki", "error": str(e)}

def search_omkar_phone(phone):
    url = "https://carrier-lookup-api.omkar.cloud/lookup"
    params = {"phone": phone}
    headers = {"API-Key": OMKAR_API_KEY}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return {"source": "omkar", "data": r.json()}
        return {"source": "omkar", "error": f"Код: {r.status_code}"}
    except Exception as e:
        return {"source": "omkar", "error": str(e)}

def search_omkar_email(email):
    url = "https://email-verification-api.omkar.cloud/verify"
    params = {"email": email}
    headers = {"API-Key": OMKAR_API_KEY}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return {"source": "omkar", "data": r.json()}
        return {"source": "omkar", "error": f"Код: {r.status_code}"}
    except Exception as e:
        return {"source": "omkar", "error": str(e)}

def search_card_bin(bin_number):
    bin_number = bin_number[:6]
    url = f"https://lookup.binlist.net/{bin_number}"
    headers = {'Accept-Version': '3'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {"source": "binlist", "data": {
                "bin": bin_number,
                "bank": data.get('bank', {}).get('name'),
                "country": data.get('country', {}).get('name'),
                "brand": data.get('scheme'),
                "type": data.get('type')
            }}
        return {"source": "binlist", "error": f"Код: {r.status_code}"}
    except Exception as e:
        return {"source": "binlist", "error": str(e)}

def search_bank_by_inn(inn):
    banks = {
        "7707083893": "Сбербанк",
        "7702070139": "ВТБ",
        "7710140679": "Т-Банк",
        "7728168971": "Альфа-Банк",
        "7710030411": "ЮниКредит",
        "7744000302": "Райффайзенбанк",
        "7744001497": "Газпромбанк",
        "7725114488": "Россельхозбанк",
        "7734203979": "Московский Кредитный Банк",
        "7709202522": "Банк Открытие",
        "4401116480": "Совкомбанк",
        "7744000912": "Промсвязьбанк",
        "7830000023": "Росбанк",
        "7706115350": "МТС-Банк",
        "7736255716": "Русский Стандарт",
        "7727009645": "Почта Банк",
        "7728230191": "Озон Банк",
        "7702235133": "Центральный Банк РФ",
        "7831000571": "Банк Санкт-Петербург",
        "7704010100": "Росгосстрах Банк",
        "7705426190": "Дойче Банк",
        "7744001678": "Новикомбанк",
        "7710383406": "Экспобанк",
        "7725161778": "ФК Открытие",
        "7704037971": "Абсолют Банк",
        "7704120582": "Транскапиталбанк",
        "7708023639": "Номос-Банк",
        "7723013520": "Российский Капитал",
        "7811322120": "Балтийский Банк",
        "7728073774": "Связь-Банк",
        "7708010008": "Банк Зенит",
        "7717019510": "Кредит Европа Банк",
        "7707309927": "Уралсиб",
        "7804000073": "Банк Санкт-Петербург",
        "7724008957": "Интерпромбанк",
        "7730161008": "Московский Индустриальный Банк",
        "7728020682": "Банк ДОМ.РФ",
        "7715015200": "Хоум Кредит Банк",
        "7710031876": "Банк Синара"
    }
    return {"source": "bank", "data": {"inn": inn, "bank": banks.get(inn, "Банк не найден")}}

def search_whois(domain):
    try:
        w = whois.whois(domain)
        return {"source": "whois", "data": {
            "domain": domain,
            "registrar": str(w.registrar) if w.registrar else None,
            "creation_date": str(w.creation_date) if w.creation_date else None,
            "expiration_date": str(w.expiration_date) if w.expiration_date else None,
            "name_servers": w.name_servers
        }}
    except Exception as e:
        return {"source": "whois", "error": str(e)}

def search_dns(domain):
    records = {}
    types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']
    for record_type in types:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            records[record_type] = [str(r) for r in answers]
        except:
            records[record_type] = []
    return {"source": "dns", "data": {"domain": domain, "records": records}}

# ==================== HEALTH ====================
@app.route('/health')
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

# ==================== ROOT ====================
@app.route('/')
def index():
    return jsonify({
        "name": "DeepTrek API",
        "version": "5.0",
        "endpoints": {
            "/search": "POST - поиск (нужен X-API-Secret)",
            "/health": "GET - статус"
        },
        "sources": ["Atlas", "BlackEye", "Snusbase", "IntelX", "VK", "TikTok", "YouTube", "Veriphone", "WhatsApp", "Odnoklassniki", "Omkar", "Binlist", "Bank", "WHOIS", "DNS"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
