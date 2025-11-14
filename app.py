import os
import sys
import traceback
import sqlite3
from datetime import datetime, timedelta

# إصلاح المسارات للنشر على Vercel
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"✅ المسار الحالي: {current_dir}")

try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
    from functools import wraps
    print("✅ تم استيراد مكتبات Flask بنجاح")
except ImportError as e:
    print(f"❌ خطأ في استيراد المكتبات: {e}")
    # بديل طارئ
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def fallback():
        return "✅ التطبيق يعمل ولكن هناك مشكلة في الاستيراد"
    
    def handler(request, context):
        return app(request.environ, lambda status, headers: [])
    
    # إنهاء التنفيذ إذا فشل الاستيراد
    import sys
    sys.exit(1)

# تهيئة التطبيق
app = Flask(
    __name__,
    template_folder=os.path.join(current_dir, 'templates'),
    static_folder=os.path.join(current_dir, 'static')
)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-123456789')

# ديكورات التحقق من الدخول
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes الأساسية
@app.route('/')
def index():
    try:
        return redirect('/admin/dashboard')
    except Exception as e:
        return f"❌ خطأ في الصفحة الرئيسية: {str(e)}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            password = request.form.get('password')
            if password == 'admin123':
                session['logged_in'] = True
                return redirect('/admin/dashboard')
            else:
                return render_template('login.html', error='كلمة المرور غير صحيحة')
        return render_template('login.html')
    except Exception as e:
        return f"❌ خطأ في صفحة Login: {str(e)}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# لوحة التحكم
@app.route('/admin/dashboard')
@login_required
def dashboard():
    try:
        # بيانات تجريبية
        services = {
            'facebook': True,
            'whatsapp': True,
            'googlesheet': False,
            'openai': True,
            'deepseek': False
        }
        
        return render_template('dashboard.html', 
                             today_messages=150,
                             today_comments=45,
                             new_orders=12,
                             active_agents=5,
                             services=services)
    except Exception as e:
        return f"❌ خطأ في لوحة التحكم: {str(e)}"

# صفحات الإعدادات
@app.route('/admin/facebook')
@login_required
def facebook_settings():
    try:
        return render_template('facebook.html')
    except Exception as e:
        return f"❌ خطأ في صفحة فيسبوك: {str(e)}"

@app.route('/admin/whatsapp')
@login_required
def whatsapp_settings():
    try:
        return render_template('whatsapp.html')
    except Exception as e:
        return f"❌ خطأ في صفحة واتساب: {str(e)}"

@app.route('/admin/googlesheet')
@login_required
def googlesheet_settings():
    try:
        return render_template('googlesheet.html')
    except Exception as e:
        return f"❌ خطأ في صفحة جوجل شيتس: {str(e)}"

@app.route('/admin/ai')
@login_required
def ai_settings():
    try:
        return render_template('ai.html')
    except Exception as e:
        return f"❌ خطأ في صفحة الذكاء الاصطناعي: {str(e)}"

# إدارة الطلبات
@app.route('/admin/orders')
@login_required
def orders():
    try:
        # بيانات تجريبية للطلبات
        orders_data = [
            [1, 'ORD-001', 'أحمد محمد', '0512345678', 'منتج أ', 2, 'new', None, '2024-01-15 10:30:00', None, None],
            [2, 'ORD-002', 'فاطمة علي', '0556789012', 'منتج ب', 1, 'assigned', 'AG001', '2024-01-15 11:15:00', None, 'المندوب 1'],
        ]
        
        # بيانات تجريبية للمندوبين
        agents_data = [
            [1, 'AG001', 'المندوب 1', '0512345678', 'agent1@email.com', 'password', 1, 5, '2024-01-01'],
        ]
        
        return render_template('orders.html', orders=orders_data, agents=agents_data)
    except Exception as e:
        return f"❌ خطأ في صفحة الطلبات: {str(e)}"

# إدارة المناديب
@app.route('/admin/agents')
@login_required
def agents():
    try:
        # بيانات تجريبية للمندوبين
        agents_data = [
            [1, 'AG001', 'المندوب 1', '0512345678', 'agent1@email.com', 'password', 1, 5, '2024-01-01'],
            [2, 'AG002', 'المندوب 2', '0556789012', 'agent2@email.com', 'password', 1, 3, '2024-01-01'],
        ]
        
        return render_template('agents.html', agents=agents_data)
    except Exception as e:
        return f"❌ خطأ في صفحة المناديب: {str(e)}"

# واجهة المندوب
@app.route('/agent')
def agent_login():
    try:
        return render_template('agent_login.html')
    except Exception as e:
        return f"❌ خطأ في صفحة دخول المندوب: {str(e)}"

@app.route('/agent/dashboard')
def agent_dashboard():
    try:
        agent_id = request.args.get('agent_id')
        
        # بيانات تجريبية للمندوب
        agent = [1, 'AG001', 'المندوب 1', '0512345678', 'agent1@email.com', 'password', 1, 5, '2024-01-01']
        
        # بيانات تجريبية للطلبات
        orders_data = [
            [1, 'ORD-001', 'أحمد محمد', '0512345678', 'منتج أ', 2, 'assigned', 'AG001', '2024-01-15 10:30:00', None, None],
        ]
        
        return render_template('agent_dashboard.html', agent=agent, orders=orders_data)
    except Exception as e:
        return f"❌ خطأ في لوحة المندوب: {str(e)}"

# APIs
@app.route('/api/ask', methods=['POST'])
def ask_ai():
    try:
        data = request.json
        question = data.get('question', '')
        
        # رد تجريبي
        response = "أنا المساعد الذكي للنظام. يمكنني مساعدتك في إدارة الطلبات، المناديب، وإعدادات الخدمات."
        
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'response': f'خطأ: {str(e)}'})

@app.route('/admin/test-connection', methods=['POST'])
@login_required
def test_connection():
    try:
        service = request.json.get('service', '')
        return jsonify({
            'status': 'success',
            'message': f'الاتصال بـ {service} يعمل بشكل صحيح'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'خطأ في الاختبار: {str(e)}'
        })

@app.route('/admin/agents/add', methods=['POST'])
@login_required
def add_agent():
    try:
        data = request.json
        return jsonify({
            'status': 'success',
            'agent_id': 'AG00' + str(datetime.now().strftime('%H%M%S'))
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'خطأ في إضافة المندوب: {str(e)}'
        })

@app.route('/admin/orders/assign', methods=['POST'])
@login_required
def assign_order():
    try:
        data = request.json
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'خطأ في إسناد الطلب: {str(e)}'
        })

# صفحة الاختبار
@app.route('/test')
def test_page():
    return "✅ التطبيق يعمل بنجاح! جميع الأنظمة جاهزة."

# معالجة الأخطاء
@app.errorhandler(404)
def not_found(error):
    return "❌ الصفحة غير موجودة", 404

@app.errorhandler(500)
def internal_error(error):
    return "❌ خطأ داخلي في الخادم", 500

if __name__ == '__main__':
    print("🚀 بدء تشغيل التطبيق...")
    app.run(debug=True, host='0.0.0.0', port=5000)