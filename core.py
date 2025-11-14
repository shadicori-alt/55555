import openai
import requests
import json
import re
from datetime import datetime
from db import get_service_token, add_log

class AIEngine:
    def __init__(self):
        self.openai_key = get_service_token('openai')
        self.deepseek_key = get_service_token('deepseek')
        self.model = 'openai'  # أو 'deepseek' حسب الإعدادات
        
        # سياقات مختلفة
        self.contexts = {
            'customer': self._get_customer_context(),
            'assistant': self._get_assistant_context(),
            'admin': self._get_admin_context()
        }
        
    def generate_response(self, message, context_type='customer', variables={}):
        try:
            context = self.contexts.get(context_type, '')
            
            if self.model == 'openai' and self.openai_key:
                return self._openai_generate(message, context, variables)
            elif self.model == 'deepseek' and self.deepseek_key:
                return self._deepseek_generate(message, context, variables)
            else:
                return self._default_response(message, variables, context_type)
        except Exception as e:
            add_log('error', f'AI generation failed: {str(e)}', 'ai')
            return self._default_response(message, variables, context_type)
    
    def _get_customer_context(self):
        return """
        أنت مساعد خدمة عملاء ودي ومحترف لشركة تجارة إلكترونية مصرية.
        مهمتك مساعدة العملاء في:
        - الإجابة على استفسارات المنتجات والأسعار
        - تقديم معلومات عن حالة الطلبات
        - حل المشكلات والشكاوى
        - تقديم دعم فني
        
        قواعد الرد:
        - كن ودوداً ومحترفاً
        - استخدم اللغة العربية الفصحى مع بعض العامية المصرية
        - قدم معلومات دقيقة ومفيدة
        - لا تكذب أو تبالغ في وصف المنتجات
        - إذا لم تكن متأكداً، اطلب من العميل الانتظار للتحقق
        """
    
    def _get_assistant_context(self):
        return """
        أنت مساعد ذكي متخصص في إدارة أنظمة التواصل والطلبات.
        مهمتك مساعدة المسؤول والمناديب في:
        - شرح وظائف النظام خطوة بخطوة
        - تقديم نصائح لتحسين الأداء
        - حل المشكلات التقنية
        - تحليل البيانات وتقديم تقارير
        - إرشادات إعدادات الخدمات الخارجية
        
        قواعد الرد:
        - استخدم لغة تقنية دقيقة
        - قدم أمثلة عملية
        - رتب المعلومات بشكل منطقي
        - اشرح الأسباب والنتائج
        """
    
    def _get_admin_context(self):
        return """
        أنت مستشار إداري متخصص في إدارة الأعمال والتجارة الإلكترونية.
        مهمتك مساعدة إدارة الشركة في:
        - تحليل أداء المبيعات والطلبات
        - تقديم تقارير إدارية
        - تحليل سلوك العملاء
        - تقديم توصيات لتحسين العمليات
        - متابعة أداء المناديب
        
        قواعد الرد:
        - استخدم لغة إدارية احترافية
        - قدم تحليلات مبنية على بيانات
        - ركز على النتائج والتوصيات
        - استخدم المصطلحات الإدارية الصحيحة
        """
    
    def _openai_generate(self, message, context, variables):
        openai.api_key = self.openai_key
        
        prompt = f"""
        أنت مساعد ذكي للرد على رسائل العملاء. 
        السياق: {context}
        الرسالة: {message}
        
        قم بالرد بشكل ودي ومفيد. استخدم المتغيرات التالية إذا لزم الأمر:
        {json.dumps(variables, ensure_ascii=False)}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def _deepseek_generate(self, message, context, variables):
        # دمج DeepSeek API (مماثل لـ OpenAI)
        headers = {
            'Authorization': f'Bearer {self.deepseek_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'deepseek-chat',
            'messages': [
                {"role": "system", "content": "أنت مساعد ذكي للرد على رسائل العملاء."},
                {"role": "user", "content": f"السياق: {context}\nالرسالة: {message}"}
            ],
            'max_tokens': 150,
            'temperature': 0.7
        }
        
        response = requests.post('https://api.deepseek.com/v1/chat/completions', 
                               headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception("DeepSeek API error")
    
    def _default_response(self, message, variables, context_type='customer'):
        # ردود افتراضية ذكية حسب السياق
        if context_type == 'customer':
            responses = {
                'مرحبا': 'مرحباً بك! 👋 أنا مساعدك الشخصي، كيف يمكنني مساعدتك اليوم؟',
                'شكرا': 'العفو! 😊 في خدمتك دائماً، لا تنسى متابعة صفحتنا للمزيد من العروض.',
                'السعر': '💰 الأسعار تختلف حسب المنتج. أرسل لي صورة المنتج المطلوب أو رقم الموديل وسأقوم بإخبارك بالسعر فوراً!',
                'العنوان': '📍 عنواننا: القاهرة، مصر. يمكننا أيضاً توصيل الطلب لأي مكان داخل القاهرة والجيزة.',
                'التوصيل': '🚚 خدمة التوصيل متاحة داخل القاهرة والجيزة خلال 24-48 ساعة. تكلفة التوصيل 25 جنيه.',
                'الدفع': '💳 نقبل الدفع نقداً عند الاستلام أو تحويل بنكي أو فودافون كاش.',
                'متاح': '✅ معظم المنتجات متاحة، أرسل لي اسم المنتج أو صورته للتأكد من توافره.',
                'خصم': '🎯 عروض خاصة متاحة حالياً! اشترِ 2 واحصل على الثالث مجاناً على منتجات مختارة.'
            }
        elif context_type == 'assistant':
            responses = {
                'شرح': 'سأشرح لك هذه الصفحة خطوة بخطوة. هذه الصفحة تتيح لك إدارة إعدادات فيسبوك وربط حسابك بسهولة.',
                'مساعدة': 'أنا هنا للمساعدة! يمكنني شرح أي جزء من النظام، تقديم نصائح لتحسين الأداء، أو مساعدتك في حل المشكلات.',
                'إعدادات': 'يمكنك تعديل الإعدادات من القائمة الجانبية. كل خدمة لها صفحة إعدادات مستقلة للتحكم الكامل.'
            }
        else:
            responses = {
                'تقرير': 'سأقوم بتحليل البيانات وتقديم تقرير إداري شامل عن أداء النظام وتوصيات للتحسين.',
                'تحليل': 'بناءً على البيانات المتوفرة، يمكنني تحليل أداء المبيعات، سلوك العملاء، وكفاءة المناديب.'
            }
        
        # البحث عن مطابقات ذكية
        for key, value in responses.items():
            if key.lower() in message.lower():
                return self._replace_variables(value, variables)
        
        # ردود افتراضية حسب السياق
        if context_type == 'customer':
            return self._replace_variables('شكراً لتواصلك معنا! 😊 سأقوم بالرد عليك فوراً، كيف يمكنني مساعدتك اليوم؟', variables)
        elif context_type == 'assistant':
            return self._replace_variables('كيف يمكنني مساعدتك في إدارة النظام اليوم؟ يمكنني شرح أي جزء أو مساعدتك في حل المشكلات.', variables)
        else:
            return self._replace_variables('كيف يمكنني مساعدتك في اتخاذ القرارات الإدارية اليوم؟', variables)
    
    def _replace_variables(self, text, variables):
        for key, value in variables.items():
            text = text.replace(f'{{{key}}}', str(value))
        return text

class ResponseManager:
    def __init__(self):
        self.ai = AIEngine()
        self.egyptian_kb = EgyptianKnowledgeBase()
        self.management_kb = ManagementKnowledgeBase()
        
        # ذاكرة للبوت من Shopify (سيتم تحديثها ديناميكياً)
        self.shopify_memory = {
            'products': [],
            'categories': ['ملابس', 'اكسسوارات', 'احذية'],
            'popular_items': [],
            'recent_orders': []
        }
    
    def update_shopify_memory(self, products_data):
        """تحديث ذاكرة المنتجات من Shopify"""
        self.shopify_memory['products'] = products_data
        self.shopify_memory['popular_items'] = self._get_popular_items(products_data)
    
    def _get_popular_items(self, products):
        """الحصول على المنتجات الأكثر شعبية"""
        # محاكاة - في الواقع يجب جلبها من بيانات الطلبات
        return products[:5] if len(products) > 5 else products
    
    def process_comment(self, comment_data):
        from db import get_service_token
        
        page_id = comment_data.get('page_id')
        post_id = comment_data.get('post_id')
        user_name = comment_data.get('user_name')
        message = comment_data.get('message')
        
        # تحليل نوع الاستفسار
        inquiry_type = self._analyze_inquiry(message)
        
        # جلب قالب الرد للمنشور
        reply_template = self._get_post_reply_template(post_id)
        
        variables = {
            'name': user_name,
            'page_name': self._get_page_name(page_id),
            'order_id': self._extract_order_id(message),
            'product_info': self._get_relevant_product_info(message),
            'shipping_info': self._get_shipping_context(message)
        }
        
        # إذا كان هناك قالب مخصص، استخدمه
        if reply_template:
            response = self.ai.generate_response(message, reply_template, variables)
        else:
            # استخدام الذكاء الاصطناعي مع السياق المناسب
            if inquiry_type in ['price', 'product', 'availability']:
                # إضافة معلومات من Shopify وقاعدة المعرفة
                context = self._build_context_for_inquiry(inquiry_type, message)
                response = self.ai.generate_response(message, context, variables)
            else:
                response = self.ai.generate_response(message, '', variables)
        
        return response
    
    def _analyze_inquiry(self, message):
        """تحليل نوع الاستفسار"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['سعر', 'كم', 'بكام', 'السعر']):
            return 'price'
        elif any(word in message_lower for word in ['متاح', 'فيه', 'عندك', 'عندكم']):
            return 'availability'
        elif any(word in message_lower for word in ['توصيل', 'شحن', 'وصل', 'متى']):
            return 'shipping'
        elif any(word in message_lower for word in ['منتج', 'قطعة', 'حاجة', ' item']):
            return 'product'
        else:
            return 'general'
    
    def _get_relevant_product_info(self, message):
        """الحصول على معلومات المنتجات المرتبطة"""
        # محاكاة - في الواقع يجب تحليل الرسالة واستخراج الكلمات المفتاحية
        for category in self.egyptian_kb.products:
            if category in message:
                return self.egyptian_kb.get_product_info(category)
        return {}
    
    def _get_shipping_context(self, message):
        """الحصول على سياق التوصيل"""
        # محاكاة - استخراج المدينة من الرسالة
        for city in self.egyptian_kb.shipping_info:
            if city in message:
                return self.egyptian_kb.get_shipping_info(city)
        return {}
    
    def _build_context_for_inquiry(self, inquiry_type, message):
        """بناء سياق مخصص حسب نوع الاستفسار"""
        if inquiry_type == 'price':
            return f"العميل يسأل عن السعر. المنتجات المتاحة: {self.shopify_memory.get('categories', [])}. استخدم معلومات الأسعار المصرية."
        elif inquiry_type == 'availability':
            return f"العميل يسأل عن توافر منتج. المنتجات المتاحة: {self.shopify_memory.get('categories', [])}. تحقق من التوافر."
        elif inquiry_type == 'shipping':
            return "العميل يسأل عن التوصيل. معلومات التوصيل: متاح داخل القاهرة والجيزة خلال 1-2 يوم."
        else:
            return ""
    
    def generate_daily_report(self):
        """توليد تقرير يومي"""
        report_template = self.management_kb.get_report_template('يومي')
        
        # محاكاة - في الواقع يجب جلب البيانات من قاعدة البيانات
        report_data = {
            'الطلبات': {
                'الاجمالي': 25,
                'القيمة': '12500 جنيه',
                'الناجحة': 23,
                'الملغاة': 2
            },
            'العملاء': {
                'الجدد': 8,
                'الدائمون': 17
            },
            'المناديب': {
                'النشطون': 5,
                'افضل_مندوب': 'أحمد'
            }
        }
        
        report = f"""
        📊 التقرير اليومي - {datetime.now().strftime('%Y-%m-%d')}
        
        📈 أداء الطلبات:
        • إجمالي الطلبات: {report_data['طلبات']['الاجمالي']}
        • القيمة الإجمالية: {report_data['طلبات']['القيمة']}
        • الطلبات الناجحة: {report_data['طلبات']['الناجحة']}
        • الطلبات الملغاة: {report_data['طلبات']['الملغاة']}
        
        👥 العملاء:
        • عملاء جدد: {report_data['العملاء']['الجدد']}
        • عملاء دائمون: {report_data['العملاء']['الدائمون']}
        
        🚚 المناديب:
        • مناديب نشطون: {report_data['المناديب']['النشطون']}
        • أفضل مندوب: {report_data['المناديب']['افضل_مندوب']}
        
        💡 توصيات:
        • متابعة العملاء الجدد لتحويلهم إلى عملاء دائمين
        • تحفيز المناديب على زيادة الأداء
        • مراجعة أسباب إلغاء الطلبات
        """
        
        return report
    
    def process_message(self, message_data):
        user_name = message_data.get('user_name')
        message = message_data.get('message')
        page_id = message_data.get('page_id')
        
        # التحقق من رسالة الترحيب
        if self._is_first_message(message_data.get('user_id'), page_id):
            welcome_msg = self._get_welcome_message(page_id)
            if welcome_msg:
                return welcome_msg
        
        variables = {
            'name': user_name,
            'page_name': self._get_page_name(page_id)
        }
        
        # تحليل نوع الرسالة واستخدام السياق المناسب
        inquiry_type = self._analyze_inquiry(message)
        
        if inquiry_type in ['price', 'product', 'availability', 'shipping']:
            # استخدام الذكاء الاصطناعي مع السياق المخصص
            context = self._build_context_for_inquiry(inquiry_type, message)
            response = self.ai.generate_response(message, context, variables)
        else:
            # استخدام الردود الافتراضية مع سياق العملاء
            response = self.ai.generate_response(message, '', variables, 'customer')
        
        return response
    
    def process_message(self, message_data):
        user_name = message_data.get('user_name')
        message = message_data.get('message')
        page_id = message_data.get('page_id')
        
        # التحقق من رسالة الترحيب
        if self._is_first_message(message_data.get('user_id'), page_id):
            welcome_msg = self._get_welcome_message(page_id)
            if welcome_msg:
                return welcome_msg
        
        variables = {
            'name': user_name,
            'page_name': self._get_page_name(page_id)
        }
        
        response = self.ai.generate_response(message, '', variables)
        return response
    
    def _get_post_reply_template(self, post_id):
        # جلب قالب الرد من قاعدة البيانات
        from db import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT auto_reply FROM posts WHERE post_id = ?', (post_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def _get_page_name(self, page_id):
        from db import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT page_name FROM pages WHERE page_id = ?', (page_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 'الصفحة'
    
    def _extract_order_id(self, message):
        # استخراج رقم الطلب من الرسالة
        match = re.search(r'#\d+', message)
        return match.group(0) if match else ''
    
    def _is_first_message(self, user_id, page_id):
        from db import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM inbox 
            WHERE user_id = ? AND page_id = ?
        ''', (user_id, page_id))
        count = cursor.fetchone()[0]
        conn.close()
        return count == 0
    
    def _get_welcome_message(self, page_id):
        from db import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT welcome_message FROM pages WHERE page_id = ?', (page_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

class ConnectionTester:
    def test_facebook_connection(self, access_token):
        try:
            url = f"https://graph.facebook.com/v18.0/me?access_token={access_token}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'success',
                    'message': 'الاتصال بنجاح',
                    'data': data
                }
            else:
                return {
                    'status': 'error',
                    'message': f'فشل الاتصال: {response.status_code}',
                    'error': response.text
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': 'خطأ في الاتصال',
                'error': str(e)
            }
    
    def test_whatsapp_connection(self, access_token):
        try:
            # اختبار الاتصال بـ WhatsApp Business API
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # اختبار الحصول على معلومات الحساب
            response = requests.get(
                'https://graph.facebook.com/v18.0/me',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'message': 'الاتصال بنجاح',
                    'data': response.json()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'فشل الاتصال: {response.status_code}',
                    'error': response.text
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': 'خطأ في الاتصال',
                'error': str(e)
            }
    
    def test_google_sheets_connection(self, access_token):
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # اختبار الوصول إلى Google Sheets API
            response = requests.get(
                'https://www.googleapis.com/drive/v3/files?q=mimeType="application/vnd.google-apps.spreadsheet"',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'message': 'الاتصال بنجاح',
                    'data': response.json()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'فشل الاتصال: {response.status_code}',
                    'error': response.text
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': 'خطأ في الاتصال',
                'error': str(e)
            }

# مكتبات المعرفة
class EgyptianKnowledgeBase:
    """مكتبة المعرفة المصرية للتجارة الإلكترونية"""
    
    def __init__(self):
        self.products = {
            'ملابس': {
                'الاسعار': 'من 150 إلى 500 جنيه',
                'المقاسات': 'S, M, L, XL, XXL',
                'الوان': 'أسود، أبيض، رمادي، كحلي، بيج',
                'توصيل': '1-2 يوم داخل القاهرة'
            },
            'اكسسوارات': {
                'الاسعار': 'من 50 إلى 300 جنيه',
                'الانواع': 'ساعات، نظارات، حقائب، مجوهرات',
                'توصيل': '2-3 أيام لجميع المحافظات'
    class WhatsAppReporter:
    """نظام التقارير التلقائي للواتساب"""
    
    def __init__(self, response_manager):
        self.response_manager = response_manager
        self.report_schedule = {
            'daily': '09:00',  # الساعة 9 صباحاً
            'weekly': 'monday 10:00',  # الاثنين الساعة 10
            'monthly': '1st 09:00'  # أول الشهر الساعة 9
        }
    
    def send_daily_report(self, admin_phone):
        """إرسال التقرير اليومي عبر واتساب"""
        try:
            report = self.response_manager.generate_daily_report()
            
            # محاكاة - في الواقع يجب استخدام WhatsApp Business API
            print(f"📱 إرسال تقرير يومي إلى {admin_phone}")
            print(report)
            
            # تسجيل الإرسال
            add_log('info', f'Daily report sent to {admin_phone}', 'whatsapp_reporter')
            
            return True
            
        except Exception as e:
            add_log('error', f'Failed to send daily report: {str(e)}', 'whatsapp_reporter')
            return False
    
    def send_agent_performance_report(self, agent_phone, agent_data):
        """إرسال تقرير أداء المندوب"""
        try:
            report = f"""
            📊 تقرير أدائك اليومي - {datetime.now().strftime('%Y-%m-%d')}
            
            🚚 الطلبات المكتملة: {agent_data.get('completed_orders', 0)}
            💰 إجمالي المبيعات: {agent_data.get('total_sales', 0)} جنيه
            ⭐ تقييم العملاء: {agent_data.get('customer_rating', 0)}/5
            🏆 ترتيبك: #{agent_data.get('rank', 0)} بين المناديب
            
            💡 نصائح لتحسين الأداء:
            • حاول تقليل وقت التوصيل
            • تواصل بشكل أفضل مع العملاء
            • استفد من ساعات الذروة
            
            استمر في العمل الجيد! 👏
            """
            
            print(f"📱 إرسال تقرير أداء إلى {agent_phone}")
            print(report)
            
            return True
            
        except Exception as e:
            add_log('error', f'Failed to send agent report: {str(e)}', 'whatsapp_reporter')
            return False

if __name__ == '__main__':
    # اختبار الوظائف
    ai = AIEngine()
    print("AI Engine initialized successfully!")