import os
import json
import re
import csv
import io
import secrets
import requests
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'deeptrek-secret-key')

# ==================== ДАННЫЕ ====================
users = {}
banned_users = []
ADMIN_PASSWORD = 'levalevag'

# ==================== API КЛЮЧИ ====================
api_keys = {
    'deeptrek_api_key_2026': {'user': 'admin', 'created': datetime.now().isoformat()},
    'deeptrek_6269af4f5a0dd20043c3d231c4d68f78': {'user': 'Test', 'created': datetime.now().isoformat()}
}

# ==================== ТОКЕНЫ BLACKEYE ====================
TOKENS = [
    "mXVE4sJBc4sC5NAVCysq0g",
    "GFoRzAWzDhuNBQRrZpTqMw",
    "7zagxufBfNZ4IRjfb10mpg",
    "Ay1E06CKjfaWqTDyUwtj2g"
]

# ==================== ПОИСКОВЫЕ ФУНКЦИИ ====================
def search_blackeye(query):
    for token in TOKENS:
        try:
            r = requests.post(
                "https://blackeyebot.duckdns.org/api/v1/search",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"query": query},
                timeout=15
            )
            if r.status_code == 200:
                return r.json()
        except:
            continue
    return {"error": "BlackEye не отвечает"}

def intelx_search_phone(phone):
    phone = re.sub(r'\D', '', phone)
    if len(phone) < 8:
        return {"error": "Номер слишком короткий"}
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
                return {"results": results}
            return {"error": "Данных нет"}
        return {"error": "Файл не найден"}
    except Exception as e:
        return {"error": str(e)}

def get_phone_info(phone):
    phone = re.sub(r'\D', '', phone)
    try:
        url = f"https://htmlweb.ru/geo/api.php?json&telcod={phone[-10:]}"
        r = requests.get(url, timeout=10)
        data = r.json()
        return {
            'country': data.get('country', 'Неизвестно'),
            'region': data.get('region', 'Неизвестно'),
            'city': data.get('city', 'Неизвестно'),
            'operator': data.get('operator', 'Неизвестно'),
        }
    except:
        return {'error': 'Ошибка'}

# ==================== ПРОВЕРКА API КЛЮЧА ====================
def check_api_key():
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return None
    return api_key if api_key in api_keys else None

# ==================== HTML СТРАНИЦА (информация об API) ====================
HOME_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepTrek API</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0b0b1a;
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 30px 20px;
        }
        .container {
            max-width: 900px;
            width: 100%;
            background: #151528;
            border-radius: 24px;
            padding: 50px 40px;
            border: 1px solid #2a2a4a;
            box-shadow: 0 20px 60px rgba(0,0,0,0.8);
        }
        .logo {
            font-size: 48px;
            font-weight: 800;
            background: linear-gradient(135deg, #6c5ce7, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            letter-spacing: -1px;
        }
        .badge {
            display: inline-block;
            background: rgba(168, 85, 247, 0.15);
            color: #a855f7;
            padding: 4px 16px;
            border-radius: 20px;
            font-size: 13px;
            margin: 8px auto 20px;
            border: 1px solid rgba(168, 85, 247, 0.2);
        }
        .subtitle {
            text-align: center;
            color: #888;
            font-size: 18px;
            margin-bottom: 30px;
            font-weight: 300;
        }
        .divider {
            border: none;
            height: 1px;
            background: linear-gradient(to right, transparent, #2a2a4a, transparent);
            margin: 30px 0;
        }
        .section { margin-bottom: 30px; }
        .section h2 {
            font-size: 20px;
            color: #a855f7;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section p, .section li { color: #c0c0c0; line-height: 1.7; font-size: 15px; }
        .section ul { list-style: none; padding: 0; }
        .section ul li {
            padding: 8px 0;
            border-bottom: 1px solid #1a1a3a;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section ul li:last-child { border-bottom: none; }
        .icon { font-size: 20px; min-width: 30px; }
        .code-block {
            background: #0e0e20;
            padding: 15px 20px;
            border-radius: 12px;
            border: 1px solid #2a2a4a;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #a855f7;
            overflow-x: auto;
            margin: 10px 0;
        }
        .links {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 20px;
        }
        .links a {
            color: #a855f7;
            text-decoration: none;
            padding: 10px 24px;
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 30px;
            transition: 0.3s;
            font-size: 14px;
        }
        .links a:hover {
            background: rgba(168, 85, 247, 0.1);
            box-shadow: 0 0 20px rgba(168, 85, 247, 0.1);
        }
        .footer {
            text-align: center;
            color: #555;
            font-size: 13px;
            margin-top: 30px;
        }
        .endpoint {
            background: #0e0e20;
            padding: 12px 16px;
            border-radius: 10px;
            margin: 8px 0;
            border-left: 3px solid #a855f7;
        }
        .endpoint .method {
            color: #51cf66;
            font-weight: 700;
            font-size: 13px;
        }
        .endpoint .path {
            color: #a855f7;
            font-family: monospace;
        }
        .endpoint .desc {
            color: #888;
            font-size: 13px;
        }
        @media (max-width: 600px) {
            .container { padding: 30px 20px; }
            .logo { font-size: 32px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🔍 DeepTrek</div>
        <div style="text-align: center;"><span class="badge">⚡ OSINT API</span></div>
        <p class="subtitle">API для поиска информации по открытым источникам</p>
        
        <hr class="divider">
        
        <div class="section">
            <h2>📌 Доступные эндпоинты</h2>
            
            <div class="endpoint">
                <div><span class="method">GET</span> <span class="path">/</span></div>
                <div class="desc">Информация об API (эта страница)</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">GET</span> <span class="path">/health</span></div>
                <div class="desc">Проверка статуса API</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">POST</span> <span class="path">/search</span></div>
                <div class="desc">Универсальный поиск (телефон, email, ФИО, ИНН, СНИЛС, госномер, IP, домен)</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">GET/POST</span> <span class="path">/admin</span></div>
                <div class="desc">Админ-панель (пароль: levalevag)</div>
            </div>
        </div>
        
        <hr class="divider">
        
        <div class="section">
            <h2>🔧 Пример запроса</h2>
            <div class="code-block">
curl -X POST https://deeptrekapi.onrender.com/search \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: ваш_ключ" \\
  -d '{"query": "79233756070", "type": "phone"}'
            </div>
        </div>
        
        <hr class="divider">
        
        <div class="section">
            <h2>📋 Типы поиска</h2>
            <ul>
                <li><span class="icon">📞</span> <strong>phone</strong> — номер телефона</li>
                <li><span class="icon">✉️</span> <strong>email</strong> — email адрес</li>
                <li><span class="icon">👤</span> <strong>fio</strong> — ФИО</li>
                <li><span class="icon">🆔</span> <strong>inn</strong> — ИНН</li>
                <li><span class="icon">🆔</span> <strong>snils</strong> — СНИЛС</li>
                <li><span class="icon">🚗</span> <strong>car</strong> — госномер</li>
                <li><span class="icon">🌐</span> <strong>ip</strong> — IP адрес</li>
                <li><span class="icon">🌐</span> <strong>domain</strong> — домен</li>
            </ul>
        </div>
        
        <hr class="divider">
        
        <div class="links">
            <a href="https://t.me/DeepTrek" target="_blank">📨 Канал</a>
            <a href="https://t.me/DeepTrekBot" target="_blank">🤖 Бот</a>
            <a href="https://deeptrek.pythonanywhere.com" target="_blank">🌐 Сайт</a>
            <a href="/admin" target="_blank">👑 Админка</a>
        </div>
        
        <div class="footer">
            DeepTrek API © 2026 • OSINT инструмент
        </div>
    </div>
</body>
</html>
'''

# ==================== HTML АДМИНКА ====================
LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>DeepTrek Админ</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #0b0b1a; color: #e0e0e0; min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .container { max-width: 400px; width: 100%; background: #151528; border-radius: 20px; padding: 40px; border: 1px solid #2a2a4a; }
        .logo { font-size: 28px; font-weight: 700; color: #a855f7; text-align: center; margin-bottom: 30px; }
        input { width: 100%; padding: 14px; background: #0e0e20; border: 1px solid #2a2a4a; border-radius: 12px; color: #fff; font-size: 16px; margin-bottom: 15px; outline: none; }
        input:focus { border-color: #a855f7; }
        button { width: 100%; padding: 14px; background: linear-gradient(135deg, #6c5ce7, #a855f7); border: none; border-radius: 12px; color: #fff; font-size: 16px; font-weight: 600; cursor: pointer; }
        button:hover { transform: scale(1.02); }
        .error { color: #ff6b6b; text-align: center; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🔑 DeepTrek Админ</div>
        <form method="post">
            <input type="password" name="password" placeholder="Пароль" required>
            <button type="submit">Войти</button>
        </form>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
'''

ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>DeepTrek Админ</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #0b0b1a; color: #e0e0e0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: #151528; border-radius: 20px; padding: 30px; border: 1px solid #2a2a4a; }
        .header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 30px; }
        .header h1 { color: #a855f7; font-size: 24px; }
        .header a { color: #888; text-decoration: none; padding: 8px 16px; border: 1px solid #2a2a4a; border-radius: 10px; }
        .header a:hover { border-color: #a855f7; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .stat-card { background: #0e0e20; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #1a1a3a; }
        .stat-card .num { font-size: 28px; font-weight: 700; color: #a855f7; }
        .stat-card .label { color: #888; font-size: 13px; margin-top: 4px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #1a1a3a; }
        th { color: #a855f7; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
        td { color: #c0c0c0; font-size: 14px; }
        .btn { padding: 6px 14px; border-radius: 8px; border: none; cursor: pointer; font-size: 12px; font-weight: 600; }
        .btn-ban { background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }
        .btn-ban:hover { background: rgba(255, 107, 107, 0.4); }
        .btn-unban { background: rgba(81, 207, 102, 0.2); color: #51cf66; }
        .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .badge.banned { background: rgba(255, 107, 107, 0.15); color: #ff6b6b; }
        .badge.active { background: rgba(81, 207, 102, 0.15); color: #51cf66; }
        .api-key { font-family: monospace; background: #0e0e20; padding: 4px 10px; border-radius: 6px; font-size: 12px; }
        .section { margin-top: 30px; }
        .section h2 { color: #a855f7; font-size: 18px; margin-bottom: 15px; }
        .flex { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
        .flex input { padding: 10px; background: #0e0e20; border: 1px solid #2a2a4a; border-radius: 8px; color: #fff; font-size: 14px; flex: 1; min-width: 200px; }
        .flex button { padding: 10px 20px; background: linear-gradient(135deg, #6c5ce7, #a855f7); border: none; border-radius: 8px; color: #fff; font-weight: 600; cursor: pointer; }
        .flex button:hover { transform: scale(1.02); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>👑 DeepTrek Админ</h1>
            <div>
                <a href="/">🏠 Главная</a>
                <a href="/admin/logout">🚪 Выйти</a>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card"><div class="num">{{ users|length }}</div><div class="label">Пользователей</div></div>
            <div class="stat-card"><div class="num">{{ api_keys|length }}</div><div class="label">API ключей</div></div>
            <div class="stat-card"><div class="num">{{ banned_users|length }}</div><div class="label">Забанено</div></div>
        </div>
        
        <div class="section">
            <h2>👥 Пользователи</h2>
            <table>
                <tr><th>ID</th><th>Имя</th><th>Username</th><th>Статус</th><th>Действия</th></tr>
                {% for user_id, user in users.items() %}
                <tr>
                    <td>{{ user_id }}</td>
                    <td>{{ user.get('name', 'Unknown') }}</td>
                    <td>@{{ user.get('username', '') }}</td>
                    <td>
                        {% if user_id|string in banned_users %}
                            <span class="badge banned">Забанен</span>
                        {% else %}
                            <span class="badge active">Активен</span>
                        {% endif %}
                    </td>
                    <td>
                        {% if user_id|string in banned_users %}
                            <form method="post" action="/admin/unban" style="display:inline;">
                                <input type="hidden" name="user_id" value="{{ user_id }}">
                                <button type="submit" class="btn btn-unban">Разбанить</button>
                            </form>
                        {% else %}
                            <form method="post" action="/admin/ban" style="display:inline;">
                                <input type="hidden" name="user_id" value="{{ user_id }}">
                                <button type="submit" class="btn btn-ban">Забанить</button>
                            </form>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
            {% if not users %}
                <p style="color:#888; margin-top:15px;">Пользователей пока нет</p>
            {% endif %}
        </div>
        
        <div class="section">
            <h2>🔑 API Ключи</h2>
            <table>
                <tr><th>Ключ</th><th>Владелец</th><th>Создан</th></tr>
                {% for key, data in api_keys.items() %}
                <tr>
                    <td><code class="api-key">{{ key }}</code></td>
                    <td>{{ data.user }}</td>
                    <td>{{ data.created }}</td>
                </tr>
                {% endfor %}
            </table>
            
            <form method="post" action="/admin/api/create" class="flex" style="margin-top:20px;">
                <input type="text" name="user" placeholder="Владелец ключа" required>
                <button type="submit">➕ Создать ключ</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

# ==================== РОУТЫ ====================
@app.route('/')
def home():
    return render_template_string(HOME_HTML)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Нет данных'}), 400
    
    query = data.get('query', '').strip()
    search_type = data.get('type', 'phone')
    
    if not query:
        return jsonify({'error': 'Пустой запрос'}), 400
    
    # Проверка API ключа
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key not in api_keys:
        return jsonify({'error': 'Неверный или отсутствующий API-ключ'}), 403
    
    result = {
        'query': query,
        'type': search_type,
        'timestamp': datetime.now().isoformat(),
        'sources': {}
    }
    
    if search_type == 'phone':
        intelx = intelx_search_phone(query)
        if 'results' in intelx:
            result['sources']['intelx'] = intelx['results']
        
        info = get_phone_info(query)
        if 'error' not in info:
            result['sources']['htmlweb'] = info
    
    blackeye = search_blackeye(query)
    if 'results' in blackeye:
        result['sources']['blackeye'] = blackeye['results']
    
    return jsonify(result)

# ==================== АДМИН-РОУТЫ ====================
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return render_template_string(
            ADMIN_HTML,
            users=users,
            api_keys=api_keys,
            banned_users=banned_users
        )
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return render_template_string(
                ADMIN_HTML,
                users=users,
                api_keys=api_keys,
                banned_users=banned_users
            )
        else:
            return render_template_string(LOGIN_HTML, error='Неверный пароль')
    
    return render_template_string(LOGIN_HTML, error=None)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/ban', methods=['POST'])
def admin_ban():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    user_id = request.form.get('user_id')
    if user_id and user_id not in banned_users:
        banned_users.append(user_id)
    return redirect(url_for('admin_login'))

@app.route('/admin/unban', methods=['POST'])
def admin_unban():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    user_id = request.form.get('user_id')
    if user_id in banned_users:
        banned_users.remove(user_id)
    return redirect(url_for('admin_login'))

@app.route('/admin/api/create', methods=['POST'])
def admin_create_api():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    user = request.form.get('user', 'unknown')
    new_key = f"deeptrek_{secrets.token_hex(16)}"
    api_keys[new_key] = {'user': user, 'created': datetime.now().isoformat()}
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
