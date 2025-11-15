from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key_change_this_in_production')

MOCK_SERVICES = {
    'facebook': True, 'whatsapp': True, 'shopify': True, 'openai': True, 'deepseek': False, 'grok': True
}

MOCK_STATS = {
    'today_messages': 25, 'today_comments': 15, 'new_orders': 10, 'active_agents': 5,
    'activeDelegates': 8, 'totalClosures': 2000, 'todayRequests': 12,
    'alerts': ['زيادة في المرتجعات 20% - اقتراح AI: أضف مندوبًا جديدًا للقاهرة']
}

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == 'admin' and password == '123456':
            session['logged_in'] = True
            session['username'] = username
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('dashboard'))
        flash('بيانات خاطئة.', 'error')
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # # if not session.get('logged_in'):  # علقت مؤقتًا عشان تدخل مباشرة
    # #     return redirect(url_for('login'))
    return render_template('dashboard.html',
                          today_messages=MOCK_STATS['today_messages'],
                          today_comments=MOCK_STATS['today_comments'],
                          new_orders=MOCK_STATS['new_orders'],
                          active_agents=MOCK_STATS['active_agents'],
                          services=MOCK_SERVICES,
                          shopify_token=os.getenv('SHOPIFY_TOKEN', ''))

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج.', 'info')
    return redirect(url_for('login'))

@app.route('/api/stats')
def get_stats():
    return jsonify(MOCK_STATS)

@app.route('/api/shopify/stats')
def shopify_stats():
    token = os.getenv('SHOPIFY_TOKEN')
    if not token:
        return jsonify({'orders': 0, 'error': 'Token missing'})
    try:
        headers = {'X-Shopify-Access-Token': token}
        response = requests.get('https://free-move-eg.myshopify.com/admin/api/2023-10/orders.json?status=any&limit=250', headers=headers, timeout=5)
        data = response.json() if response.ok else {'orders': []}
        return jsonify({'orders': len(data.get('orders', []))})
    except Exception:
        return jsonify({'orders': 0})

@app.route('/api/bot', methods=['POST'])
def bot():
    data = request.get_json()
    message = data.get('message', '')
    api = data.get('api', 'grok')
    reply = f"رد من {api}: بناءً على '{message}'، اقتراح: تحقق من الطلبات ({MOCK_STATS['todayRequests']})."
    return jsonify({'reply': reply})

@app.route('/api/workflow/stop-all', methods=['POST'])
def stop_all_workflow():
    return jsonify({'message': 'تم الإيقاف! إعادة تلقائي بعد 5 دقائق.'})

@app.route('/api/alerts/resolve', methods=['POST'])
def resolve_alert():
    data = request.get_json()
    alert = data.get('alert', '')
    MOCK_STATS['alerts'] = [a for a in MOCK_STATS['alerts'] if a != alert]
    return jsonify({'status': 'resolved'})

@app.route('/admin/toggle-service', methods=['POST'])
def toggle_service():
    data = request.get_json()
    service = data.get('service')
    status = data.get('status')
    if service in MOCK_SERVICES:
        MOCK_SERVICES[service] = status
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'})

# Placeholders for other pages (علقت اللوجين مؤقتًا)
for page in ['connections', 'requests', 'delegates', 'accounts', 'workflow', 'messages']:
    @app.route(f'/{page}')
    def route_placeholder():
        # # if not session.get('logged_in'):
        # #     return redirect(url_for('login'))
        return render_template(f'{page}.html')

if __name__ == '__main__':
    app.run(debug=True)
else:
    application = app