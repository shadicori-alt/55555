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
    # # if not session.get('logged_in'):  # معلق مؤقتًا – روح مباشرة
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

@app.route('/api/connections/setup', methods=['POST'])
def setup_connection():
    data = request.get_json()
    service = data.get('service')
    if service == 'messenger':
        return jsonify({'message': 'ربط Messenger: أضف webhook إلى https://your-app.vercel.app/api/messenger-webhook'})
    elif service == 'whatsapp':
        return jsonify({'message': 'ربط WhatsApp: استخدم Cloud API endpoint'})
    return jsonify({'message': 'خدمة غير مدعومة'})

@app.route('/api/connections/test-ai', methods=['POST'])
def test_ai():
    data = request.get_json()
    provider = data.get('provider')
    key = data.get('key')
    return jsonify({'message': f'اختبار {provider} ناجح! Key محفوظ. (استخدم للبوت)'})

@app.route('/api/connections/log')
def connections_log():
    return jsonify({'logs': ['Messenger متصل 2024-11-15', 'Shopify جاهز', 'AI Grok نشط']})

@app.route('/api/requests')
def get_requests():
    return jsonify({
        'requests': [
            {'id': '001', 'client': 'أحمد محمد', 'governorate': 'القاهرة', 'delegate': 'مندوب 1', 'status': 'قيد التنفيذ', 'date': '2024-11-15'},
            {'id': '002', 'client': 'فاطمة علي', 'governorate': 'الإسكندرية', 'delegate': 'مندوب 2', 'status': 'مكتمل', 'date': '2024-11-14'}
        ]
    })

@app.route('/api/delegates')
def get_delegates():
    return jsonify({
        'delegates': [
            {'id': '1', 'name': 'أحمد علي', 'phone': '0123456789', 'deliveries': '25', 'rating': '4.5/5', 'active': True, 'status': 'نشط'},
            {'id': '2', 'name': 'محمد أحمد', 'phone': '0987654321', 'deliveries': '18', 'rating': '4.2/5', 'active': False, 'status': 'معطل'}
        ]
    })

# Placeholders for other pages (معلق اللوجين)
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