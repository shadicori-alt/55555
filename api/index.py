import os
import sys

# إصلاح المسارات
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from app import app
    print("✅ تم استيراد app.py بنجاح")
except Exception as e:
    print(f"❌ خطأ في استيراد app.py: {e}")
    # بديل طارئ
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return "✅ التطبيق يعمل! المشكلة في الاستيراد."

def handler(request, context):
    try:
        return app(request.environ, lambda status, headers: [])
    except Exception as e:
        error_msg = f"❌ خطأ في handler: {str(e)}"
        print(error_msg)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/plain'},
            'body': error_msg
        }