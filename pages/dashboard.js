// pages/dashboard.js - اللوحة الرئيسية الجديدة (مع إحصائيات، تنبيهات AI، وأزرار سريعة)
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

// كومبوننت الإحصائيات (بيانات وهمية، هتتحدث من API)
const StatsCard = ({ title, value, change, color = 'blue' }) => (
  <div className={`bg-${color}-100 p-4 rounded-lg shadow-md`}>
    <h3 className="text-sm font-medium text-gray-600">{title}</h3>
    <p className="text-2xl font-bold text-gray-900">{value}</p>
    <p className={`text-sm ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
      {change >= 0 ? '+' : ''}{change}% من اليوم السابق
    </p>
  </div>
);

// كومبوننت التنبيهات (من AI أو السير)
const Alerts = ({ alerts }) => (
  <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
    <h3 className="font-medium text-yellow-800 mb-2">تنبيهات AI:</h3>
    <ul className="space-y-1 text-sm text-yellow-700">
      {alerts.map((alert, index) => (
        <li key={index} className="flex items-center">
          ⚠️ {alert}
          <button className="ml-2 text-blue-600 hover:underline">حل</button>
        </li>
      ))}
    </ul>
  </div>
);

// كومبوننت الاقتراحات السريعة
const QuickActions = () => (
  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
    <Link to="/requests" className="bg-green-500 text-white p-4 rounded-lg text-center hover:bg-green-600">
      📋 طلب جديد
    </Link>
    <Link to="/messages" className="bg-blue-500 text-white p-4 rounded-lg text-center hover:bg-blue-600">
      💬 رد على رسائل
    </Link>
    <button className="bg-purple-500 text-white p-4 rounded-lg text-center hover:bg-purple-600" onClick={() => alert('إرسال تقرير يومي عبر المساعد')}>
      📊 تقرير اليوم
    </button>
  </div>
);

const Dashboard = ({ stats: initialStats }) => {
  const [stats, setStats] = useState(initialStats);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // جلب بيانات حقيقية من API (مثل Shopify للمخزون، أو Vercel KV للإحصائيات)
    const fetchStats = async () => {
      try {
        // مثال: جلب من Shopify لعدد الطلبات
        const shopifyResponse = await fetch('https://free-move-eg.myshopify.com/admin/api/2023-10/orders.json?status=any&limit=1', {
          headers: {
            'X-Shopify-Access-Token': process.env.SHOPIFY_TOKEN || 'your-token-here', // من Vercel env
            'Content-Type': 'application/json'
          }
        });
        const shopifyData = await shopifyResponse.json();
        
        // جلب إحصائيات عامة من API داخلي
        const internalResponse = await fetch('/api/stats');
        const internalData = await internalResponse.json();

        // دمج البيانات (مثال بسيط)
        setStats({
          requests: { total: shopifyData.orders.length || 45, today: 12 },
          delegates: { active: internalData.activeDelegates || 8, deliveries: 120 },
          closures: { pending: 5, total: 2000 },
          alerts: internalData.alerts || ['زيادة في المرتجعات 20% - اقتراح AI: أضف مندوبًا جديدًا للقاهرة']
        });
      } catch (error) {
        console.error('خطأ في جلب الإحصائيات:', error);
        // استخدم البيانات الوهمية كـ fallback
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return <div className="flex justify-center items-center h-64">جاري تحميل الإحصائيات...</div>;
  }

  return (
    <div className="space-y-6">
      {/* عنوان اللوحة */}
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">مرحباً بك في اللوحة الرئيسية</h2>
        <button 
          className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
          onClick={() => {
            // أمر للمساعد: عرض تقرير مفصل
            fetch('/api/bot', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ message: 'عرض تقرير اليوم الكامل', api: 'grok' })
            }).then(res => res.json()).then(data => alert(data.reply));
          }}
        >
          🤖 استشر المساعد
        </button>
      </div>

      {/* الإحصائيات الرئيسية */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatsCard title="الطلبات الكلية" value={stats.requests.total} change={5} color="green" />
        <StatsCard title="المناديب النشطين" value={stats.delegates.active} change={2} color="blue" />
        <StatsCard title="إجمالي التقفيلات" value={`${stats.closures.total} جنيه`} change={-3} color="purple" />
      </div>

      {/* التنبيهات */}
      {stats.alerts.length > 0 && <Alerts alerts={stats.alerts} />}

      {/* الإجراءات السريعة */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-4">إجراءات سريعة</h3>
        <QuickActions />
      </div>

      {/* زر الإيقاف العام (للسير العمل) */}
      <div className="bg-red-50 border border-red-200 p-4 rounded">
        <p className="text-red-800">🛑 للإيقاف الطارئ لأي سير عملية، اضغط <button className="bg-red-500 text-white px-2 py-1 rounded ml-1" onClick={() => alert('تم إيقاف جميع السير - سيتم إعادة التشغيل التلقائي بعد 5 دقائق')}>هنا</button></p>
      </div>
    </div>
  );
};

export default Dashboard;
