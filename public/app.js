// app.js - الملف الرئيسي المعدل (React App مع Router و Tailwind)
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link, useNavigate } from 'react-router-dom';
import Dashboard from './pages/dashboard'; // اللوحة الرئيسية الجديدة
import Connections from './pages/connections'; // الارتباطات (مع ربط Messenger/WhatsApp/AI/Shopify)
import Requests from './pages/requests'; // الطلبات (مع محافظ ومخزون)
import Delegates from './pages/delegates'; // المناديب (مع تطبيق خفيف وإشعارات)
import Accounts from './pages/accounts'; // الحسابات/التقفيلات
import Workflow from './pages/workflow'; // سير العمل (جديد مع أزرار إيقاف)
import Messages from './pages/messages'; // الرسائل والتعليقات
import BotAssistant from './components/BotAssistant'; // المساعد الذكي (كومبوننت منفصل)

// بيانات وهمية للإحصائيات (هتتحدث من API لاحقًا)
const mockStats = {
  requests: { total: 45, today: 12 },
  delegates: { active: 8, deliveries: 120 },
  closures: { pending: 5, total: 2000 },
  alerts: ['زيادة في المرتجعات 20% - اقتراح AI: أضف مندوبًا جديدًا']
};

function Sidebar() {
  const [isOpen, setIsOpen] = useState(true);
  return (
    <div className={`bg-gray-800 text-white h-screen p-4 ${isOpen ? 'w-64' : 'w-20'} transition-width duration-300 fixed`}>
      <button onClick={() => setIsOpen(!isOpen)} className="mb-4 p-2 bg-gray-700 rounded">☰</button>
      <nav>
        <ul className="space-y-2">
          <li><Link to="/" className="block p-2 hover:bg-gray-700 rounded">🏠 اللوحة الرئيسية</Link></li>
          <li><Link to="/connections" className="block p-2 hover:bg-gray-700 rounded">🔗 الارتباطات</Link></li>
          <li><Link to="/requests" className="block p-2 hover:bg-gray-700 rounded">📋 الطلبات</Link></li>
          <li><Link to="/delegates" className="block p-2 hover:bg-gray-700 rounded">🚚 المناديب</Link></li>
          <li><Link to="/accounts" className="block p-2 hover:bg-gray-700 rounded">💰 الحسابات</Link></li>
          <li><Link to="/workflow" className="block p-2 hover:bg-gray-700 rounded">⚙️ سير العمل</Link></li>
          <li><Link to="/messages" className="block p-2 hover:bg-gray-700 rounded">💬 الرسائل</Link></li>
          <li><button onClick={() => window.open('/delegate-app', '_blank')} className="block p-2 hover:bg-gray-700 rounded w-full text-left">📱 تطبيق المناديب</button></li>
        </ul>
      </nav>
      <div className="mt-4 p-2 bg-blue-600 rounded">
        <BotAssistant /> {/* المساعد الذكي هنا كزر دردشة */}
      </div>
    </div>
  );
}

function AppContent() {
  const navigate = useNavigate();
  useEffect(() => {
    // تحميل بيانات من API عند التحميل (مثل Shopify للإحصائيات)
    const fetchData = async () => {
      try {
        const response = await fetch('/api/stats', { // API جديد هنعمله لاحقًا
          headers: { 'Authorization': `Bearer ${process.env.SHOPIFY_TOKEN}` } // من Vercel env
        });
        // حدث mockStats هنا
      } catch (error) {
        console.error('خطأ في تحميل البيانات:', error);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="ml-64 p-6 bg-gray-100 min-h-screen"> {/* margin للـ sidebar */}
      <header className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold">نظام الإدارة الذكي</h1>
        <div className="space-x-2">
          <button onClick={() => navigate('/')} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">تحديث</button>
          <button className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600" onClick={() => { /* إيقاف عام */ alert('إيقاف جميع السير - تأكيد؟'); }}>🛑 إيقاف عام</button>
        </div>
      </header>
      <Routes>
        <Route path="/" element={<Dashboard stats={mockStats} />} />
        <Route path="/connections" element={<Connections />} />
        <Route path="/requests" element={<Requests />} />
        <Route path="/delegates" element={<Delegates />} />
        <Route path="/accounts" element={<Accounts />} />
        <Route path="/workflow" element={<Workflow />} />
        <Route path="/messages" element={<Messages />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="flex">
        <Sidebar />
        <AppContent />
      </div>
    </Router>
  );
}

// كومبوننت المساعد الذكي البسيط (هيتمدد لاحقًا)
function BotAssistant() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const sendMessage = async () => {
    if (!message) return;
    try {
      const response = await fetch('/api/bot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, api: 'grok' }) // تبديل AI هنا
      });
      const data = await response.json();
      alert(`رد المساعد: ${data.reply}`); // عرض في دردشة لاحقًا
    } catch (error) {
      alert('خطأ في الاتصال بالمساعد');
    }
    setMessage('');
  };

  return (
    <div>
      <button onClick={() => setIsOpen(!isOpen)} className="text-sm">🤖 المساعد الذكي</button>
      {isOpen && (
        <div className="mt-2 p-2 bg-gray-700 rounded">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="أمرك... (مثل: عرض تقرير)"
            className="w-full p-1 text-black rounded mb-1"
          />
          <button onClick={sendMessage} className="w-full bg-green-500 text-white p-1 rounded">إرسال</button>
        </div>
      )}
    </div>
  );
}

export default App;