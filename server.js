// server.js - النظام الكامل
const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const cron = require('node-cron');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(bodyParser.json());
app.use(express.static('public'));

const wss = new WebSocket.Server({ noServer: true });

const db = new sqlite3.Database('./data.db', (err) => {
    if (err) console.error(err);
    else { console.log('DB Connected'); initDB(); }
});

function initDB() {
    db.serialize(() => {
        // الطلبات
        db.run(`CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, phone TEXT, address TEXT, governorate TEXT,
            details TEXT, status TEXT DEFAULT 'pending',
            agent TEXT, payment TEXT, price REAL, closed BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )`);

        // المناديب
        db.run(`CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, phone TEXT, governorate TEXT, active BOOLEAN DEFAULT 1
        )`);

        // الرسائل
        db.run(`CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT, sender TEXT, text TEXT,
            post_id TEXT, comment_id TEXT,
            replied BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )`);

        // إعدادات
        db.run(`CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT
        )`);

        // المستخدم
        db.run(`CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT, password TEXT
        )`);

        // التذكيرات
        db.run(`CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER, message TEXT, time TEXT, repeat TEXT
        )`);

        // بيانات افتراضية
        db.run(`INSERT OR IGNORE INTO agents (name, phone, governorate) VALUES 
            ('أحمد محمد', '01012345678', 'القاهرة'), 
            ('محمد علي', '01112345678', 'الجيزة')`);
        
        db.run(`INSERT OR IGNORE INTO users (username, password) VALUES ('admin', '1234')`);
    });
}

// === تسجيل الدخول ===
app.post('/api/login', (req, res) => {
    const { username, password } = req.body;
    db.get('SELECT * FROM users WHERE username = ? AND password = ?', [username, password], (err, row) => {
        if (row) res.json({ success: true });
        else res.status(401).json({ error: 'Invalid credentials' });
    });
});

// === API الطلبات ===
app.get('/api/orders', (req, res) => db.all('SELECT * FROM orders ORDER BY created_at DESC', [], (err, rows) => res.json(rows || [])));
app.post('/api/orders', (req, res) => {
    const { name, phone, address, governorate, details, agent, payment, price } = req.body;
    db.run('INSERT INTO orders (name, phone, address, governorate, details, agent, payment, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [name, phone, address, governorate, details, agent, payment, price], function() {
            res.json({ id: this.lastID });
            broadcast({ type: 'new_order' });
        });
});
app.put('/api/orders/:id', (req, res) => {
    const { status, closed, price } = req.body;
    db.run('UPDATE orders SET status = ?, closed = ?, price = ? WHERE id = ?', [status, closed ? 1 : 0, price, req.params.id], () => {
        res.json({ success: true });
        broadcast({ type: 'update' });
    });
});

// === المناديب ===
app.get('/api/agents', (req, res) => db.all('SELECT * FROM agents', [], (err, rows) => res.json(rows || [])));

// === الرسائل ===
app.get('/api/messages', (req, res) => db.all('SELECT * FROM messages ORDER BY created_at DESC LIMIT 50', [], (err, rows) => res.json(rows || [])));
app.post('/api/messages', (req, res) => {
    const { channel, sender, text, post_id, comment_id } = req.body;
    db.run('INSERT INTO messages (channel, sender, text, post_id, comment_id) VALUES (?, ?, ?, ?, ?)',
        [channel, sender, text, post_id, comment_id], () => res.json({ success: true }));
});

// === واتساب ===
app.post('/api/whatsapp/send', async (req, res) => {
    const { to, msg } = req.body;
    const sid = await getSetting('twilio_sid');
    const token = await getSetting('twilio_token');
    if (!sid || !token) return res.status(400).json({ error: 'No Twilio' });
    try {
        await axios.post(`https://api.twilio.com/2010-04-01/Accounts/${sid}/Messages.json`, new URLSearchParams({
            To: `whatsapp:${to}`, From: 'whatsapp:+14155238886', Body: msg
        }), { auth: { username: sid, password: token } });
        res.json({ success: true });
    } catch (e) { res.status(500).json({ error: e.message }); }
});

// === AI ===
app.post('/api/ai', async (req, res) => {
    const { prompt } = req.body;
    const key = await getSetting('ai_key');
    const provider = await getSetting('ai_provider') || 'grok';
    if (!key) return res.json({ reply: 'AI غير متصل' });
    try {
        const url = provider === 'openai' ? 'https://api.openai.com/v1/chat/completions' : 'https://api.x.ai/v1/chat/completions';
        const model = provider === 'openai' ? 'gpt-3.5-turbo' : 'grok-beta';
        const r = await axios.post(url, { model, messages: [{ role: 'user', content: prompt }] }, { headers: { Authorization: `Bearer ${key}` } });
        res.json({ reply: r.data.choices[0].message.content });
    } catch (e) { res.json({ reply: 'خطأ في AI' }); }
});

// === إعدادات ===
app.post('/api/settings', (req, res) => {
    const { key, value } = req.body;
    db.run('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', [key, value], () => res.json({ success: true }));
});
function getSetting(key) {
    return new Promise(r => db.get('SELECT value FROM settings WHERE key = ?', [key], (e, row) => r(row?.value || '')));
}

// === التوزيع التلقائي ===
cron.schedule('0 10 * * *', async () => {
    const time = await getSetting('dist_time');
    if (time !== '10:00') return;
    const orders = await new Promise(r => db.all('SELECT * FROM orders WHERE status = "pending"', [], (e, rows) => r(rows)));
    const agents = await new Promise(r => db.all('SELECT * FROM agents', [], (e, rows) => r(rows)));
    for (let agent of agents) {
        const agentOrders = orders.filter(o => o.governorate === agent.governorate);
        if (agentOrders.length > 0) {
            const msg = `عندك ${agentOrders.length} طلبات جديدة: ${agentOrders.map(o => `#${o.id}`).join(', ')}`;
            await fetch('/api/whatsapp/send', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ to: agent.phone, msg }) });
        }
    }
});

// === WebSocket ===
function broadcast(data) {
    wss.clients.forEach(c => c.readyState === WebSocket.OPEN && c.send(JSON.stringify(data)));
}

const server = app.listen(PORT, () => console.log(`Server on ${PORT}`));
server.on('upgrade', (req, socket, head) => wss.handleUpgrade(req, socket, head, ws => wss.emit('connection', ws, req)));