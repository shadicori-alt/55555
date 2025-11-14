// server.js - النظام الكامل: بسم الله
const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const WebSocket = require('ws');
const path = require('path');
const cron = require('node-cron');

const app = express();
const PORT = process.env.PORT || 3000;

// الإعدادات
app.use(cors());
app.use(bodyParser.json());
app.use(express.static('public'));

// WebSocket للتحديث الفوري
const wss = new WebSocket.Server({ noServer: true });

// قاعدة البيانات
const db = new sqlite3.Database('./data.db', (err) => {
    if (err) console.error('DB Error:', err);
    else {
        console.log('✅ قاعدة البيانات متصلة');
        initDB();
    }
});

// إنشاء الجداول
function initDB() {
    db.serialize(() => {
        // الطلبات
        db.run(`CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, phone TEXT, address TEXT, governorate TEXT,
            details TEXT, status TEXT DEFAULT 'pending',
            agent TEXT, payment TEXT DEFAULT 'نقدي', price REAL DEFAULT 0,
            closed BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )`);

        // المناديب
        db.run(`CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, phone TEXT, governorate TEXT, active BOOLEAN DEFAULT 1
        )`);

        // الرسائل (تعليقات + رسائل)
        db.run(`CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT, sender TEXT, text TEXT,
            post_id TEXT, comment_id TEXT,
            replied BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )`);

        // الإعدادات
        db.run(`CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT
        )`);

        // المستخدم (تسجيل الدخول)
        db.run(`CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password TEXT
        )`);

        // التذكيرات
        db.run(`CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER, message TEXT, time TEXT, repeat TEXT DEFAULT 'لا'
        )`);

        // بيانات افتراضية
        db.run(`INSERT OR IGNORE INTO users (username, password) VALUES ('admin', '1234')`);
        db.run(`INSERT OR IGNORE INTO agents (name, phone, governorate) VALUES 
            ('أحمد محمد', '01012345678', 'القاهرة'),
            ('محمد علي', '01112345678', 'الجيزة')`);
    });
}

// === تسجيل الدخول ===
app.post('/api/login', (req, res) => {
    const { username, password } = req.body;
    db.get('SELECT * FROM users WHERE username = ? AND password = ?', [username, password], (err, row) => {
        if (row) {
            res.json({ success: true });
        } else {
            res.status(401).json({ error: 'بيانات خاطئة' });
        }
    });
});

// === API الطلبات ===
app.get('/api/orders', (req, res) => {
    db.all('SELECT * FROM orders ORDER BY created_at DESC', [], (err, rows) => {
        res.json(rows || []);
    });
});

app.post('/api/orders', (req, res) => {
    const { name, phone, address, governorate, details, agent, payment, price } = req.body;
    db.run(
        'INSERT INTO orders (name, phone, address, governorate, details, agent, payment, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [name, phone, address, governorate, details || '', agent || '', payment || 'نقدي', price || 0],
        function () {
            res.json({ id: this.lastID });
            broadcast({ type: 'new_order', orderId: this.lastID });
        }
    );
});

app.put('/api/orders/:id', (req, res) => {
    const { status, closed, price, payment } = req.body;
    db.run(
        'UPDATE orders SET status = ?, closed = ?, price = ?, payment = ? WHERE id = ?',
        [status || 'pending', closed ? 1 : 0, price || 0, payment || 'نقدي', req.params.id],
        () => {
            res.json({ success: true });
            broadcast({ type: 'update_order', orderId: req.params.id });
        }
    );
});

// === المناديب ===
app.get('/api/agents', (req, res) => {
    db.all('SELECT * FROM agents', [], (err, rows) => res.json(rows || []));
});

app.post('/api/agents', (req, res) => {
    const { name, phone, governorate } = req.body;
    db.run('INSERT INTO agents (name, phone, governorate) VALUES (?, ?, ?)', [name, phone, governorate], function () {
        res.json({ id: this.lastID });
    });
});

// === الرسائل (Inbox) ===
app.get('/api/messages', (req, res) => {
    db.all('SELECT * FROM messages ORDER BY created_at DESC LIMIT 50', [], (err, rows) => res.json(rows || []));
});

app.post('/api/messages', (req, res) => {
    const { channel, sender, text, post_id, comment_id } = req.body;
    db.run('INSERT INTO messages (channel, sender, text, post_id, comment_id) VALUES (?, ?, ?, ?, ?)',
        [channel, sender, text, post_id || '', comment_id || ''], () => {
            res.json({ success: true });
            broadcast({ type: 'new_message' });
        });
});

// === واتساب (Twilio) ===
app.post('/api/whatsapp/send', async (req, res) => {
    const { to, msg } = req.body;
    const sid = await getSetting('twilio_sid');
    const token = await getSetting('twilio_token');
    if (!sid || !token) return res.status(400).json({ error: 'واتساب غير متصل' });

    try {
        await axios.post(
            `https://api.twilio.com/2010-04-01/Accounts/${sid}/Messages.json`,
            new URLSearchParams({
                To: `whatsapp:${to}`,
                From: 'whatsapp:+14155238886',
                Body: msg
            }),
            { auth: { username: sid, password: token } }
        );
        res.json({ success: true });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// === الذكاء الاصطناعي (Grok / OpenAI) ===
app.post('/api/ai', async (req, res) => {
    const { prompt } = req.body;
    const key = await getSetting('ai_key');
    const provider = (await getSetting('ai_provider')) || 'grok';

    if (!key) {
        return res.json({ reply: 'الذكاء الاصطناعي غير متصل. تم تسجيل الطلب.' });
    }

    try {
        const url = provider === 'openai'
            ? 'https://api.openai.com/v1/chat/completions'
            : 'https://api.x.ai/v1/chat/completions';
        const model = provider === 'openai' ? 'gpt-3.5-turbo' : 'grok-beta';

        const response = await axios.post(url, {
            model,
            messages: [{ role: 'user', content: prompt }]
        }, {
            headers: { Authorization: `Bearer ${key}` }
        });

        res.json({ reply: response.data.choices[0].message.content });
    } catch (e) {
        res.json({ reply: 'خطأ في الذكاء الاصطناعي' });
    }
});

// === الإعدادات ===
app.get('/api/settings', (req, res) => {
    db.all('SELECT key, value FROM settings', [], (err, rows) => {
        const s = {};
        rows.forEach(r => s[r.key] = r.value);
        res.json(s);
    });
});

app.post('/api/settings', (req, res) => {
    const { key, value } = req.body;
    db.run('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', [key, value], () => {
        res.json({ success: true });
    });
});

function getSetting(key) {
    return new Promise(resolve => {
        db.get('SELECT value FROM settings WHERE key = ?', [key], (err, row) => {
            resolve(row?.value || '');
        });
    });
}

// === التوزيع التلقائي (كل يوم 10 صباحًا) ===
cron.schedule('0 10 * * *', async () => {
    const distEnabled = await getSetting('dist_enabled');
    if (distEnabled !== 'true') return;

    const orders = await new Promise(r => db.all('SELECT * FROM orders WHERE status = "pending" AND closed = 0', [], (e, rows) => r(rows)));
    const agents = await new Promise(r => db.all('SELECT * FROM agents WHERE active = 1', [], (e, rows) => r(rows)));

    for (let agent of agents) {
        const agentOrders = orders.filter(o Sustainability => o.governorate === agent.governorate);
        if (agentOrders.length > 0) {
            const msg = `عندك ${agentOrders.length} طلبات جديدة في ${agent.governorate}:\n${agentOrders.map(o => `#${o.id} - ${o.name}`).join('\n')}\nرابط التطبيق: ${process.env.URL || 'https://yourapp.onrender.com'}/agent/${agent.phone}`;
            await fetch('/api/whatsapp/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ to: agent.phone, msg })
            });
            // تحديث الحالة
            agentOrders.forEach(o => {
                db.run('UPDATE orders SET status = "delivering", agent = ? WHERE id = ?', [agent.name, o.id]);
            });
        }
    }
});

// === WebSocket للتحديث الفوري ===
function broadcast(data) {
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(data));
        }
    });
}

// بدء السيرفر
const server = app.listen(PORT, () => {
    console.log(`🚀 السيرفر شغال على المنفذ ${PORT}`);
});

server.on('upgrade', (req, socket, head) => {
    wss.handleUpgrade(req, socket, head, ws => {
        wss.emit('connection', ws, req);
    });
});