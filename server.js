// server.js
const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const WebSocket = require('ws');
const path = require('path');

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
        db.run(`CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, address TEXT, status TEXT DEFAULT 'pending', agent TEXT, payment TEXT)`);
        db.run(`CREATE TABLE IF NOT EXISTS agents (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, active BOOLEAN DEFAULT 1)`);
        db.run(`CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, channel TEXT, sender TEXT, text TEXT, replied BOOLEAN DEFAULT 0)`);
        db.run(`CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)`);
        db.run(`INSERT OR IGNORE INTO agents (name, phone) VALUES ('أحمد', '01012345678')`);
    });
}

// API
app.get('/api/orders', (req, res) => db.all('SELECT * FROM orders', [], (err, rows) => res.json(rows || [])));
app.post('/api/orders', (req, res) => {
    const { name, phone, address, agent, payment } = req.body;
    db.run('INSERT INTO orders (name, phone, address, agent, payment) VALUES (?, ?, ?, ?, ?)', [name, phone, address, agent, payment], function() {
        res.json({ id: this.lastID });
        broadcast({ type: 'new_order' });
    });
});
app.put('/api/orders/:id', (req, res) => {
    const { status } = req.body;
    db.run('UPDATE orders SET status = ? WHERE id = ?', [status, req.params.id], () => {
        res.json({ success: true });
        broadcast({ type: 'update' });
    });
});

app.get('/api/agents', (req, res) => db.all('SELECT * FROM agents', [], (err, rows) => res.json(rows || [])));
app.post('/api/whatsapp', async (req, res) => {
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

app.post('/api/grok', async (req, res) => {
    const { prompt } = req.body;
    const key = await getSetting('grok_key');
    if (!key) return res.status(400).json({ error: 'No Key' });
    try {
        const r = await axios.post('https://api.x.ai/v1/chat/completions', { model: 'grok-beta', messages: [{ role: 'user', content: prompt }] }, { headers: { Authorization: `Bearer ${key}` } });
        res.json({ reply: r.data.choices[0].message.content });
    } catch (e) { res.status(500).json({ error: e.message }); }
});

app.post('/api/settings', (req, res) => {
    const { key, value } = req.body;
    db.run('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', [key, value], () => res.json({ success: true }));
});

function getSetting(key) {
    return new Promise(resolve => db.get('SELECT value FROM settings WHERE key = ?', [key], (err, row) => resolve(row?.value || '')));
}

function broadcast(data) {
    wss.clients.forEach(client => client.readyState === WebSocket.OPEN && client.send(JSON.stringify(data)));
}

const server = app.listen(PORT, () => console.log(`Server on ${PORT}`));
server.on('upgrade', (req, socket, head) => wss.handleUpgrade(req, socket, head, ws => wss.emit('connection', ws, req)));