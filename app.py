import os
import json
import re
import csv
import io
import requests
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'deeptrek-secret-key')

# ==================== ДАННЫЕ (в памяти) ====================
# Для продакшена лучше использовать БД, но для Render с памятью тоже работает
users = {}
api_keys = {
    'deeptrek_api_key_2026': {'user': 'admin', 'created': datetime.now().isoformat()}
}
banned_users = []
ADMIN_PASSWORD = 'levalevag'

# ==================== HTML ШАБЛОНЫ ====================
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
        .btn-unban:hover { background: rgba(81, 207, 102, 0.4); }
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
        .success { color: #51cf66; margin-top: 10px; }
        .error-msg { color: #ff6b6b; margin-top: 10px; }
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
            <div class="stat-card"><div class="num">{{ users_count }}</div><div class="label">Пользователей</div></div>
            <div class="stat-card"><div class="num">{{ api_keys_count }}</div><div class="label">API ключей</div></div>
            <div class="stat-card"><div class="num">{{ banned_count }}</div><div class="label">Забанено</div></div>
        </div>
        
        <div class="section">
            <h2>👥 Пользователи</h2>
            <table>
                <tr><th>ID</th><th>Имя</th><th>Username</th><th>Статус</th><th>Действия</th></tr>
                {% for user in users_list %}
                <tr>
                    <td>{{ user.id }}</td>
                    <td>{{ user.name }}</td>
                    <td>@{{ user.username }}</td>
                    <td>
                        {% if user.id in banned_users %}
                            <span class="badge banned">Забанен</span>
                        {% else %}
                            <span class="badge active">Активен</span>
                        {% endif %}
                    </td>
                    <td>
                        {% if user.id in banned_users %}
                            <form method="post" action="/admin/unban" style="display:inline;">
                                <input type="hidden" name="user_id" value="{{ user.id }}">
                                <button type="submit" class="btn btn-unban">Разбанить</button>
                            </form>
                        {% else %}
                            <form method="post" action="/admin/ban" style="display:inline;">
                                <input type="hidden" name="user_id" value="{{ user.id }}">
                                <button type="submit" class="btn btn-ban">Забанить</button>
                            </form>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
            {% if not users_list %}
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
            
            {% if api_message %}
                <div class="success">{{ api_message }}</div>
            {% endif %}
            {% if api_error %}
                <div class="error-msg">{{ api_error }}</div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

# ==================== ПОИСКОВЫЕ ФУНКЦИИ ====================
TOKENS = [
    "mXVE4sJBc4sC5NAVCysq0g",
    "GFoRzAWzDhuNBQRrZpTqMw",
    "7zagxufBfNZ4IRjfb10mpg",
    "Ay1E06CKjfaWqTDyUwtj2g"
]

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

# ==================== РОУТЫ ====================
@app.route('/')
def index():
    return jsonify({
        'name': 'DeepTrek API',
        'version': '2.0',
        'endpoints': {
            '/search': 'POST - поиск',
            '/admin': 'Админ-панель',
            '/health': 'Статус'
        }
    })

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
        return render_admin_panel()
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return render_admin_panel()
        else:
            return render_template_string(LOGIN_HTML, error='Неверный пароль')
    
    return render_template_string(LOGIN_HTML, error=None)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

def render_admin_panel():
    users_list = [{'id': uid, 'name': u.get('name', 'Unknown'), 'username': u.get('username', '')} for uid, u in users.items()]
    return render_template_string(
        ADMIN_HTML,
        users_list=users_list,
        users_count=len(users),
        api_keys=api_keys,
        api_keys_count=len(api_keys),
        banned_users=banned_users,
        banned_count=len(banned_users),
        api_message='',
        api_error=''
    )

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
    import secrets
    new_key = f"deeptrek_{secrets.token_hex(16)}"
    api_keys[new_key] = {'user': user, 'created': datetime.now().isoformat()}
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
