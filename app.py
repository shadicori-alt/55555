from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3
import json
import os
from functools import wraps
from datetime import datetime, timedelta
import requests
from db import (
    init_database, get_service_status, update_service_status, 
    save_service_token, get_service_token, add_log
)
from core import AIEngine, ResponseManager, ConnectionTester, generate_quick_buttons, WhatsAppReporter, ShopifyIntegration

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASS', 'admin123')

# تهيئة قاعدة البيانات
init_database()

# ديكورات التحقق من الدخول
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# الصفحة الرئيسية للدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# لوحة التحكم الرئيسية
@app.route('/admin/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    # إحصائيات اليوم
    today = datetime.now().date()
    
    # عدد الرسائل اليوم
    cursor.execute('''
        SELECT COUNT(*) FROM inbox 
        WHERE DATE(created_time) = ?
    ''', (today,))
    today_messages = cursor.fetchone()[0]
    
    # عدد التعليقات اليوم
    cursor.execute('''
        SELECT COUNT(*) FROM comments 
        WHERE DATE(created_time) = ?
    ''', (today,))
    today_comments = cursor.fetchone()[0]
    
    # عدد الطلبات
    cursor.execute('SELECT COUNT(*) FROM orders WHERE status = ?', ('new',))
    new_orders = cursor.fetchone()[0]
    
    # عدد المناديب النشطين
    cursor.execute('SELECT COUNT(*) FROM agents WHERE status = 1')
    active_agents = cursor.fetchone()[0]
    
    # حالة الخدمات
    services = {
        'facebook': get_service_status('facebook'),
        'whatsapp': get_service_status('whatsapp'),
        'googlesheet': get_service_status('googlesheet'),
        'openai': get_service_status('openai'),
        'deepseek': get_service_status('deepseek')
    }
    
    conn.close()
    
    return render_template('dashboard.html', 
                         today_messages=today_messages,
                         today_comments=today_comments,
                         new_orders=new_orders,
                         active_agents=active_agents,
                         services=services)

# إدارة فيسبوك
@app.route('/admin/facebook')
@login_required
def facebook_settings():
    return render_template('facebook.html')

@app.route('/admin/facebook/connect')
@login_required
def facebook_connect():
    # OAuth redirect لفيسبوك
    app_id = request.args.get('app_id')
    redirect_uri = url_for('facebook_callback', _external=True)
    
    fb_auth_url = f"""https://www.facebook.com/v18.0/dialog/oauth?
        client_id={app_id}&
        redirect_uri={redirect_uri}&
        scope=pages_manage_posts,pages_manage_metadata,pages_read_engagement,pages_show_list&
        response_type=code"""
    
    return redirect(fb_auth_url)

@app.route('/admin/facebook/callback')
def facebook_callback():
    code = request.args.get('code')
    if code:
        # تبادل الكود بتوكن
        # هذا مثال مبسط - في الواقع تحتاج إلى client_secret
        access_token = "exchange_code_for_token"
        save_service_token('facebook', access_token)
        update_service_status('facebook', True)
        add_log('info', 'Facebook connected successfully', 'facebook')
    
    return redirect(url_for('facebook_settings'))

# إدارة واتساب
@app.route('/admin/whatsapp')
@login_required
def whatsapp_settings():
    return render_template('whatsapp.html')

@app.route('/admin/whatsapp/connect', methods=['POST'])
@login_required
def whatsapp_connect():
    phone_number = request.json.get('phone_number')
    access_token = request.json.get('access_token')
    
    if phone_number and access_token:
        save_service_token('whatsapp', access_token)
        update_service_status('whatsapp', True)
        add_log('info', 'WhatsApp Business connected', 'whatsapp')
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Missing data'})

# إدارة جوجل شيتس
@app.route('/admin/googlesheet')
@login_required
def googlesheet_settings():
    return render_template('googlesheet.html')

@app.route('/admin/googlesheet/connect')
@login_required
def googlesheet_connect():
    # OAuth redirect لجوجل
    client_id = request.args.get('client_id')
    redirect_uri = url_for('googlesheet_callback', _external=True)
    
    google_auth_url = f"""https://accounts.google.com/o/oauth2/v2/auth?
        client_id={client_id}&
        redirect_uri={redirect_uri}&
        scope=https://www.googleapis.com/auth/spreadsheets&
        response_type=code&
        access_type=offline"""
    
    return redirect(google_auth_url)

@app.route('/admin/googlesheet/callback')
def googlesheet_callback():
    code = request.args.get('code')
    if code:
        access_token = "exchange_code_for_token"
        save_service_token('googlesheet', access_token)
        update_service_status('googlesheet', True)
        add_log('info', 'Google Sheets connected', 'googlesheet')
    
    return redirect(url_for('googlesheet_settings'))

# إدارة الذكاء الاصطناعي
@app.route('/admin/ai')
@login_required
def ai_settings():
    return render_template('ai.html')

@app.route('/admin/ai/update', methods=['POST'])
@login_required
def update_ai():
    data = request.json
    model = data.get('model')
    api_key = data.get('api_key')
    
    if model and api_key:
        save_service_token(model, api_key)
        update_service_status(model, True)
        add_log('info', f'{model.upper()} AI model updated', 'ai')
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Missing data'})

# إدارة الطلبات
@app.route('/admin/orders')
@login_required
def orders():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT o.*, a.name as agent_name 
        FROM orders o 
        LEFT JOIN agents a ON o.agent_id = a.agent_id
        ORDER BY o.created_at DESC
    ''')
    orders = cursor.fetchall()
    
    cursor.execute('SELECT * FROM agents WHERE status = 1')
    agents = cursor.fetchall()
    
    conn.close()
    
    return render_template('orders.html', orders=orders, agents=agents)

@app.route('/admin/orders/assign', methods=['POST'])
@login_required
def assign_order():
    data = request.json
    order_id = data.get('order_id')
    agent_id = data.get('agent_id')
    
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET agent_id = ?, status = ? WHERE order_id = ?', 
                   (agent_id, 'assigned', order_id))
    conn.commit()
    conn.close()
    
    add_log('info', f'Order {order_id} assigned to agent {agent_id}', 'orders')
    return jsonify({'status': 'success'})

# إدارة المناديب
@app.route('/admin/agents')
@login_required
def agents():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM agents ORDER BY created_at DESC')
    agents = cursor.fetchall()
    conn.close()
    
    return render_template('agents.html', agents=agents)

@app.route('/admin/agents/add', methods=['POST'])
@login_required
def add_agent():
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    email = data.get('email')
    password = data.get('password')
    
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    agent_id = f"agent_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    cursor.execute('''
        INSERT INTO agents (agent_id, name, phone, email, password)
        VALUES (?, ?, ?, ?, ?)
    ''', (agent_id, name, phone, email, password))
    
    conn.commit()
    conn.close()
    
    add_log('info', f'New agent added: {name}', 'agents')
    return jsonify({'status': 'success', 'agent_id': agent_id})

# اختبار الاتصالات
@app.route('/admin/test-connection', methods=['POST'])
@login_required
def test_connection():
    service = request.json.get('service')
    tester = ConnectionTester()
    
    if service == 'facebook':
        token = get_service_token('facebook')
        result = tester.test_facebook_connection(token)
    elif service == 'whatsapp':
        token = get_service_token('whatsapp')
        result = tester.test_whatsapp_connection(token)
    elif service == 'googlesheet':
        token = get_service_token('googlesheet')
        result = tester.test_google_sheets_connection(token)
    else:
        result = {'status': 'error', 'message': 'Service not supported'}
    
    return jsonify(result)

# API للمساعد الذكي
@app.route('/api/ask', methods=['POST'])
def ask_ai():
    data = request.json
    question = data.get('question')
    page_context = data.get('page_context', '')
    context_type = data.get('context_type', 'assistant')  # customer, assistant, admin
    
    manager = ResponseManager()
    
    if context_type == 'assistant':
        response = manager.process_assistant_query(question, page_context)
    else:
        ai = AIEngine()
        response = ai.generate_response(question, page_context, {}, context_type)
    
    return jsonify({'response': response})

# API للتقارير
@app.route('/api/reports/daily', methods=['POST'])
@login_required
def generate_daily_report():
    """توليد تقرير يومي"""
    try:
        manager = ResponseManager()
        report = manager.generate_daily_report()
        
        return jsonify({
            'status': 'success',
            'report': report
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

# API لإرسال تقرير واتساب
@app.route('/api/whatsapp/send-report', methods=['POST'])
@login_required
def send_whatsapp_report():
    """إرسال تقرير عبر واتساب"""
    data = request.json
    phone = data.get('phone')
    report_type = data.get('type', 'daily')
    
    try:
        manager = ResponseManager()
        reporter = WhatsAppReporter(manager)
        
        if report_type == 'daily':
            success = reporter.send_daily_report(phone)
        elif report_type == 'agent':
            agent_data = data.get('agent_data', {})
            success = reporter.send_agent_performance_report(phone, agent_data)
        
        return jsonify({
            'status': 'success' if success else 'error',
            'message': 'تم إرسال التقرير بنجاح' if success else 'فشل إرسال التقرير'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

# API لربط Shopify
@app.route('/api/shopify/connect', methods=['POST'])
@login_required
def connect_shopify():
    """ربط متجر Shopify"""
    data = request.json
    store_url = data.get('store_url')
    api_key = data.get('api_key')
    
    try:
        shopify = ShopifyIntegration(store_url)
        products = shopify.fetch_products(api_key)
        
        if products:
            # تحديث ذاكرة المنتجات
            manager = ResponseManager()
            manager.update_shopify_memory(products)
            
            return jsonify({
                'status': 'success',
                'message': f'تم ربط {len(products)} منتج من Shopify',
                'products_count': len(products)
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'فشل جلب المنتجات من Shopify'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

# واجهة الموبايل للمناديب
@app.route('/agent')
def agent_login():
    return render_template('agent_login.html')

@app.route('/agent/dashboard')
def agent_dashboard():
    agent_id = request.args.get('agent_id')
    if not agent_id:
        return redirect(url_for('agent_login'))
    
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    # جلب الطلبات المسندة للمندوب
    cursor.execute('''
        SELECT * FROM orders 
        WHERE agent_id = ? AND status IN ('assigned', 'in_progress')
        ORDER BY created_at DESC
    ''', (agent_id,))
    orders = cursor.fetchall()
    
    # معلومات المندوب
    cursor.execute('SELECT * FROM agents WHERE agent_id = ?', (agent_id,))
    agent = cursor.fetchone()
    
    conn.close()
    
    return render_template('agent_dashboard.html', orders=orders, agent=agent)

# Webhook لفيسبوك
@app.route('/webhook/facebook', methods=['GET', 'POST'])
def facebook_webhook():
    if request.method == 'GET':
        # التحقق من Webhook
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if verify_token == 'your-verify-token':
            return challenge
        return 'Invalid verify token'
    
    elif request.method == 'POST':
        # معالجة الأحداث الواردة
        data = request.json
        
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for event in entry.get('changes', []):
                    if event.get('field') == 'feed':
                        # معالجة تعليق جديد
                        comment_data = {
                            'comment_id': event.get('value', {}).get('comment_id'),
                            'post_id': event.get('value', {}).get('post_id'),
                            'user_name': event.get('value', {}).get('from', {}).get('name'),
                            'message': event.get('value', {}).get('message'),
                            'page_id': entry.get('id')
                        }
                        
                        if get_service_status('facebook'):
                            # معالجة الرد التلقائي في خيط منفصل
                            from threading import Thread
                            thread = Thread(target=process_auto_reply, args=(comment_data,))
                            thread.start()
        
        return 'OK'

def process_auto_reply(comment_data):
    try:
        manager = ResponseManager()
        reply = manager.process_comment(comment_data)
        
        # إرسال الرد عبر Facebook API
        access_token = get_service_token('facebook')
        if access_token:
            # كود إرسال الرد (مبسط)
            pass
            
    except Exception as e:
        add_log('error', f'Auto reply failed: {str(e)}', 'facebook')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)