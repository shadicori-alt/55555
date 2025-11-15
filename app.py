from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import requests  # للـ APIs مثل Shopify
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key_change_this_in_production')  # غيرها في env

# بيانات وهمية للإحصائيات (هتتحدث من DB لاحقًا، مثل Supabase)
MOCK_SERVICES = {
    'facebook': True,
    'whatsapp': True,
    'shopify': True,
    'openai': True,
    'deepseek': False,
    'grok': True
}

MOCK_STATS = {
    'today_messages': 25,
    'today_comments': 15,
    'new_orders': 10,
    'active_agents': 5,
    'activeDelegates': 8,
    'totalClosures': 2000,
    'todayRequests': 12,
    'alerts': ['زيادة في المرتجعات 20% - اقتراح AI: أضف مندوبًا جديدًا للقاهرة']
}

# Route الرئيسي - صفحة الدخول
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # تحقق بسيط (غير لـ DB حقيقي أو bcrypt للأمان)
        if username == 'admin' and password == '123456':  # غير الباسورد في الإنتاج
            session['logged_in'] = True
            session['username'] = username
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('dashboard'))  # نقل فوري للداشبورد
        
        flash('بيانات خاطئة، يرجى المحاولة مرة أخرى.', 'error')
    
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')  # افترض templates/login.html موجود

# Route الداشبورد
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        flash('يجب تسجيل الدخول أولاً.', 'error')
        return redirect(url_for('login'))
    
    # تمرير البيانات للـ template
    return render_template('dashboard.html',
                          today_messages=MOCK_STATS['today_messages'],
                          today_comments=MOCK_STATS['today_comments'],
                          new_orders=MOCK_STATS['new_orders'],
                          active_agents=MOCK_STATS['active_agents'],
                          services=MOCK_SERVICES,
                          shopify_token=os.getenv('SHOPIFY_TOKEN', ''))

# Route الخروج
@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح.', 'info')
    return redirect(url_for('login'))

# API للإحصائيات الداخلية
@app.route('/api/stats')
def get_stats():
    return jsonify(MOCK_STATS)

# API لـ Shopify stats
@app.route('/api/shopify/stats')
def shopify_stats():
    token = os.getenv('SHOPIFY_TOKEN')
    if not token:
        return jsonify({'orders': 0, 'error': 'Token missing'})
    
    try:
        headers = {'X-Shopify-Access-Token': token}
        response = requests.get('https://free-move-eg.myshopify.com/admin/api/2023-10/orders.json?status=any&limit=250', headers=headers, timeout=5)
        if response.ok:
            data = response.json()
            return jsonify({'orders': len(data.get('orders', []))})
        else:
            return jsonify({'orders': 0, 'error': 'API error'})
    except Exception as e:
        return jsonify({'orders': 0, 'error': str(e)})

# API للمساعد الذكي (bot)
@app.route('/api/bot', methods=['POST'])
def bot():
    data = request.get_json()
    message = data.get('message', '')
    api = data.get('api', 'grok')  # أو 'deepseek' أو 'openai'
    
    # رد بسيط (غير لربط حقيقي مع API مثل requests.post('https://api.x.ai/v1/chat/completions'))
    if api == 'grok':
        reply = f"رد ذكي من Grok: بناءً على '{message}'، اقتراحي: تحقق من الطلبات الجديدة في Shopify. عدد الطلبات: {MOCK_STATS['todayRequests']}."
    else:
        reply = f"رد من {api}: تم تحليل الرسالة '{message}'."
    
    return jsonify({'reply': reply})

# API لإيقاف جميع السير
@app.route('/api/workflow/stop-all', methods=['POST'])
def stop_all_workflow():
    # هنا كود الإيقاف (مثل تحديث DB أو flag في Redis/Vercel KV)
    print("إيقاف جميع السير العمليات!")  # log
    return jsonify({'message': 'تم إيقاف جميع السير العمليات بنجاح! سيتم إعادة التشغيل تلقائيًا بعد 5 دقائق.'})

# API لحل التنبيهات
@app.route('/api/alerts/resolve', methods=['POST'])
def resolve_alert():
    data = request.get_json()
    alert = data.get('alert', '')
    # حفظ في log أو DB
    print(f"حُل التنبيه: {alert}")
    MOCK_STATS['alerts'] = [a for a in MOCK_STATS['alerts'] if a != alert]  # إزالة مؤقتة
    return jsonify({'status': 'resolved'})

# API لتبديل الخدمات (toggle-service)
@app.route('/admin/toggle-service', methods=['POST'])
def toggle_service():
    data = request.get_json()
    service = data.get('service')
    status = data.get('status')
    
    if service in MOCK_SERVICES:
        MOCK_SERVICES[service] = status
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'خدمة غير موجودة'})

# Routes placeholders للأقسام الأخرى (عشان التنقل يشتغل، أضف templates ليها لاحقًا)
@app.route('/connections')
def connections():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('connections.html', services=MOCK_SERVICES)

@app.route('/requests')
def requests():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('requests.html')

@app.route('/delegates')
def delegates():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('delegates.html')

@app.route('/accounts')
def accounts():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('accounts.html')

@app.route('/workflow')
def workflow():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('workflow.html')

@app.route('/messages')
def messages():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('messages.html')

# تشغيل التطبيق
if __name__ == '__main__':
    app.run(debug=True)
else:
    # لـ Vercel، استخدم gunicorn أو vercel.json
    application = app