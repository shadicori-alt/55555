#!/usr/bin/env python3
"""
نظام إدارة التواصل الذكي
تشغيل التطبيق الرئيسي
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def setup_environment():
    """إعداد البيئة اللازمة للتطبيق"""
    
    # إنشاء مجلد static إذا لم يوجد
    static_dir = Path("static")
    static_dir.mkdir(exist_ok=True)
    
    # إنشاء مجلد uploads إذا لم يوجد
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    # تعيين متغيرات البيئة
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1')
    
    # التحقق من وجود متغيرات مهمة
    if not os.environ.get('ADMIN_PASS'):
        os.environ['ADMIN_PASS'] = 'admin123'
        print("⚠️  تم تعيين كلمة مرور المسؤول الافتراضية: admin123")
        print("   يرجى تغييرها من خلال متغير البيئة ADMIN_PASS")
    
    if not os.environ.get('SECRET_KEY'):
        os.environ['SECRET_KEY'] = 'your-secret-key-change-this'
        print("⚠️  تم تعيين مفتاح سري افتراضي")
        print("   يرجى تغييره من خلال متغير البيئة SECRET_KEY")

def install_requirements():
    """تثبيت المتطلبات اللازمة"""
    
    requirements = [
        'flask',
        'requests',
        'openai',
        'python-dotenv'
    ]
    
    print("📦 جاري التحقق من المتطلبات...")
    
    for req in requirements:
        try:
            __import__(req.replace('-', '_'))
            print(f"✅ {req} مثبت")
        except ImportError:
            print(f"📥 تثبيت {req}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', req])

def initialize_database():
    """تهيئة قاعدة البيانات"""
    
    print("🗄️  تهيئة قاعدة البيانات...")
    
    try:
        # استيراد وحدة قاعدة البيانات
        import db
        db.init_database()
        print("✅ تم تهيئة قاعدة البيانات بنجاح")
        
        # إضافة بيانات تجريبية
        add_sample_data()
        
    except Exception as e:
        print(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
        return False
    
    return True

def add_sample_data():
    """إضافة بيانات تجريبية للاختبار"""
    
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    try:
        # التحقق من وجود بيانات
        cursor.execute('SELECT COUNT(*) FROM agents')
        if cursor.fetchone()[0] == 0:
            # إضافة مندوب تجريبي
            cursor.execute('''
                INSERT INTO agents (agent_id, name, phone, email, password, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('demo_agent', 'أحمد محمد', '01012345678', 'ahmed@example.com', 'demo123', 1))
            
            # إضافة طلبات تجريبية
            sample_orders = [
                ('ORD001', 'سارة أحمد', '01123456789', 'فستان سهرة أسود', 1, 'new', '', '2024-01-15 10:30:00'),
                ('ORD002', 'محمود علي', '01234567890', 'بنطلون جينز', 2, 'assigned', 'demo_agent', '2024-01-15 11:45:00'),
                ('ORD003', 'نورا حسن', '01098765432', 'بلوزة قطنية', 3, 'in_progress', 'demo_agent', '2024-01-15 12:15:00'),
            ]
            
            for order in sample_orders:
                cursor.execute('''
                    INSERT INTO orders (order_id, customer_name, customer_phone, product, quantity, status, agent_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', order)
            
            # إضافة منتجات تجريبية من Shopify
            sample_products = [
                ('PROD001', 'فستان سهرة أسود', 'فستان سهرة أنيق باللون الأسود، مناسب للمناسبات الخاصة', '350', 'ملابس', 'https://via.placeholder.com/300', 1),
                ('PROD002', 'بنطلون جينز كلاسيك', 'بنطلون جينز عالي الجودة بقصة كلاسيكية', '280', 'ملابس', 'https://via.placeholder.com/300', 1),
                ('PROD003', 'بلوزة قطنية بيضاء', 'بلوزة قطنية مريحة باللون الأبيض', '150', 'ملابس', 'https://via.placeholder.com/300', 1),
            ]
            
            for product in sample_products:
                cursor.execute('''
                    INSERT INTO shopify_products (product_id, title, description, price, category, image_url, availability)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', product)
            
            conn.commit()
            print("✅ تم إضافة بيانات تجريبية مصرية")
        
    except Exception as e:
        print(f"⚠️  لم يتم إضافة بيانات تجريبية: {e}")
    
    finally:
        conn.close()

def check_python_version():
    """التحقق من إصدار بايثون"""
    
    if sys.version_info < (3, 7):
        print("❌ يتطلب Python 3.7 أو أحدث")
        print(f"   الإصدار الحالي: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} متوافق")
    return True

def main():
    """الدالة الرئيسية"""
    
    print("🚀 بدء تشغيل نظام إدارة التواصل الذكي")
    print("=" * 50)
    
    # التحقق من إصدار بايثون
    if not check_python_version():
        return
    
    # إعداد البيئة
    setup_environment()
    
    # تثبيت المتطلبات
    try:
        install_requirements()
    except Exception as e:
        print(f"⚠️  تحذير: لم يتم تثبيت جميع المتطلبات: {e}")
        print("   يمكنك تثبيتهم يدوياً باستخدام: pip install -r requirements.txt")
    
    # تهيئة قاعدة البيانات
    if not initialize_database():
        print("❌ فشل تهيئة قاعدة البيانات")
        return
    
    print("\n🎯 جاهز للتشغيل!")
    print("=" * 50)
    print("📱 لوحة التحكم: http://localhost:5000/admin/dashboard")
    print("📱 دخول المندوب: http://localhost:5000/agent")
    print("🔑 كلمة مرور المسؤول:", os.environ.get('ADMIN_PASS', 'admin123'))
    print("\n⚡ بدء تشغيل الخادم...")
    
    # تشغيل التطبيق
    try:
        from app import app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False
        )
    except ImportError:
        print("❌ لم يتم العثور على ملف app.py")
        print("   تأكد من وجود جميع ملفات المشروع")
    except Exception as e:
        print(f"❌ خطأ في تشغيل التطبيق: {e}")

if __name__ == '__main__':
    main()