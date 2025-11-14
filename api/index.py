import os
import sys

# إضافة المسار الحالي لاستيراد المكتبات
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from app import app
except ImportError as e:
    # بديل إذا فشل الاستيراد
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return "✅ التطبيق يعمل! ولكن هناك مشكلة في الاستيراد."

def handler(request, context):
    try:
        return app(request.environ, lambda status, headers: [])
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/plain'},
            'body': f'❌ خطأ في التطبيق: {str(e)}'
        }