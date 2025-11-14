// server.js - النظام الكامل مع ربط فيسبوك حقيقي
require('dotenv').config();
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

// WebSocket
const wss = new WebSocket.Server({ noServer: true });

// قاعدة البيانات
const db = new sqlite3.Database('./data.db', (err) => {
    if (err) console.error('DB Error:', err);
    else {
        console.log('قاعدة البيانات متصلة');
        initDB();
    }
});

function initDB() {
    db.serialize(() => {
        db.run(`CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, phone TEXT, address TEXT, governorate TEXT,
            details TEXT, status TEXT DEFAULT 'pending',
            agent TEXT, payment TEXT DEFAULT 'نقدي', price REAL DEFAULT 0,
            closed BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )`);

        db.run(`CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, phone TEXT, governorate TEXT, active BOOLEAN DEFAULT 1
        )`);

        db.run(`CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT, sender TEXT, text TEXT,
            post_id TEXT, comment_id TEXT,
            replied BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )`);

        db.run(`CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT
        )`);

        db.run(`CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password TEXT
        )`);

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
        if (row) res.json({ success: true });
        else res.status(401).json({ error: 'بيانات خاطئة' });
    });
});

// === فيسبوك OAuth (حقيقي) ===
app.get('/auth/facebook', (req, res) => {
    if (!process.env.FB_APP_ID || !process.env.FB_APP_SECRET) {
        return res.status(400).send('فيسبوك غير مُعَد');
    }
    const redirectUri = `${req.protocol}://${req.get('host')}/auth/facebook/callback`;
    const authUrl = `https://www.facebook.com/v18.0/dialog/oauth?client_id=${process.env.FB_APP_ID}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=pages_messaging,pages_read_engagement,pages_manage_posts&response_type=code&state=123`;
    res.redirect(authUrl);
});

app.get('/auth/facebook/callback', async (req, res) => {
    const code = req.query.code;
    if (!code) return res.send('فشل الربط');

    try {
        const tokenRes = await axios.get('https://graph.facebook.com/v18.0/oauth/access_token', {
            params: {
                client_id: process.env.FB_APP_ID,
                client_secret: process.env.FB_APP_SECRET,
                code,
                redirect_uri: `${req.protocol}://${req.get('host')}/auth/facebook/callback`
            }
        });

        const userToken = tokenRes.data.access_token;

        // جلب الصفحات
        const pagesRes = await axios.get(`https://graph.facebook.com/me/accounts?access_token=${userToken}`);
        const page = pagesRes.data.data[0];
        if (!page) return res.send('لا توجد صفحات');

        await saveSetting('fb_page_id', page.id);
        await saveSetting('fb_token', page.access_token);
        await saveSetting('fb_page_name', page.name);

        res.send(`
            <script>
                alert("تم ربط فيسبوك بنجاح! الصفحة: ${page.name}");
                window.close();
            </script>
        `);
    } catch (e) {
        res.send('خطأ: ' + e.message);
    }
});

// === API الطلبات ===
app.get('/api/orders', (req, res) => {
    db.all('SELECT * FROM orders ORDER BY created_at DESC', [], (err, rows) => res.json(rows || []));
});

app.post('/api/orders', (req, res) => {
    const { name, phone, address, governorate, details, agent, payment, price } = req.body;
    db.run(
        'INSERT INTO orders (name, phone, address, governorate, details, agent, payment, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [name, phone, address, governorate, details || '', agent || '', payment || 'نقدي', price || 0],
        function () {
            res.json({ id: this.lastID });
            broadcast({ type: 'new_order' });
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
            broadcast({ type: 'update' });
        }
    );
});

// === المناديب ===
app.get('/api/agents', (req, res) => db.all('SELECT * FROM agents', [], (err, rows) => res.json(rows || [])));

// === واتساب ===
app.post('/api/whatsapp/send', async (req, res) => {
    const { to, msg } = req.body;
    const sid = await getSetting('twilio_sid');
    const token = await getSetting('twilio_token');
    if (!sid || !token) return res.status(400).json({ error: 'واتساب غير متصل' });

    try {
        await axios.post(
            `https://api.twilio.com/2010-04-01/Accounts/${sid}/Messages.json`,
            new URLSearchParams({ To: `whatsapp:${to}`, From: 'whatsapp:+14155238886', Body: msg }),
            { auth: { username: sid, password: token } }
        );
        res.json({ success: true });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// === AI ===
app.post('/api/ai', async (req, res) => {
    const { prompt } = req.body;
    const key = await getSetting('ai_key');
    const provider = (await getSetting('ai_provider')) || 'grok';

    if (!key) return res.json({ reply: 'AI غير متصل' });

    try {
        const url = provider === 'openai'
            ? 'https://api.openai.com/v1/chat/completions'
            : 'https://api.x.ai/v1/chat/completions';
        const model = provider === 'openai' ? 'gpt-3.5-turbo' : 'grok-beta';

        const r = await axios.post(url, { model, messages: [{ role: 'user', content: prompt }] }, {
            headers: { Authorization: `Bearer ${key}` }
        });
        res.json({ reply: r.data.choices[0].message.content });
    } catch (e) {
        res.json({ reply: 'خطأ في AI' });
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
    db.run('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', [key, value], () => res.json({ success: true }));
});

function getSetting(key) {
    return new Promise(r => db.get('SELECT value FROM settings WHERE key = ?', [key], (e, row) => r(row?.value || '')));
}

function saveSetting(key, value) {
    return new Promise(r => db.run('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', [key, value], () => r()));
}

// === التوزيع التلقائي ===
cron.schedule('0 10 * * *', async () => {
    const enabled = await getSetting('dist_enabled');
    if (enabled !== 'true') return;

    const orders = await new Promise(r => db.all('SELECT * FROM orders WHERE status = "pending"', [], (e, rows) => r(rows)));
    const agents = await new Promise(r => db.all('SELECT * FROM agents', [], (e, rows) => r(rows)));

    for (let agent of agents) {
        const agentOrders = orders.filter(o => o.governorate === agent.governorate);
        if (agentOrders.length > 0) {
            const msg = `عندك ${agentOrders.length} طلبات جديدة:\n${agentOrders.map(o => `#${o.id} - ${o.name}`).join('\n')}`;
            await fetch('/api/whatsapp/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ to: agent.phone, msg })
            });
        }
    }
});

// === WebSocket ===
function broadcast(data) {
    wss.clients.forEach(c => c.readyState === WebSocket.OPEN && c.send(JSON.stringify(data)));
}

const server = app.listen(PORT, () => console.log(`السيرفر شغال على ${PORT}`));
server.on('upgrade', (req, socket, head) => wss.handleUpgrade(req, socket, head, ws => wss.emit('connection', ws, req)));