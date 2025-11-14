// api/index.js - Vercel API Route (السيرفر كله)
import express from 'express';
import { createServer } from 'http';
import { Server as SocketIOServer } from 'socket.io';
import sqlite3 from 'sqlite3';
import axios from 'axios';
import cors from 'cors';
import 'dotenv/config';

const app = express();
const server = createServer(app);
const io = new SocketIOServer(server, { cors: { origin: '*' } });

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// قاعدة البيانات
const db = new sqlite3.Database('./data.db');
db.serialize(() => {
    db.run(`CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, address TEXT, governorate TEXT, details TEXT, status TEXT DEFAULT 'pending', agent TEXT, payment TEXT DEFAULT 'نقدي', price REAL DEFAULT 0, closed BOOLEAN DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)`);
    db.run(`CREATE TABLE IF NOT EXISTS agents (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, governorate TEXT, active BOOLEAN DEFAULT 1)`);
    db.run(`CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)`);
    db.run(`CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)`);
    db.run(`INSERT OR IGNORE INTO users (username, password) VALUES ('admin', '1234')`);
    db.run(`INSERT OR IGNORE INTO agents (name, phone, governorate) VALUES ('أحمد', '01012345678', 'القاهرة')`);
});

// === تسجيل الدخول ===
app.post('/api/login', (req, res) => {
    const { username, password } = req.body;
    db.get('SELECT * FROM users WHERE username = ? AND password = ?', [username, password], (err, row) => {
        res.json(row ? { success: true } : { error: 'خطأ' });
    });
});

// === الطلبات ===
app.get('/api/orders', (req, res) => {
    db.all('SELECT * FROM orders ORDER BY created_at DESC', [], (err, rows) => res.json(rows || []));
});

app.post('/api/orders', (req, res) => {
    const { name, phone, governorate } = req.body;
    db.run('INSERT INTO orders (name, phone, governorate) VALUES (?, ?, ?)', [name, phone, governorate], function() {
        res.json({ id: this.lastID });
        io.emit('update');
    });
});

app.put('/api/orders/:id', (req, res) => {
    const { status, closed, price, payment } = req.body;
    db.run('UPDATE orders SET status = ?, closed = ?, price = ?, payment = ? WHERE id = ?', [status, closed ? 1 : 0, price || 0, payment || 'نقدي', req.params.id], () => {
        res.json({ success: true });
        io.emit('update');
    });
});

// === المناديب ===
app.get('/api/agents', (req, res) => {
    db.all('SELECT * FROM agents', [], (err, rows) => res.json(rows || []));
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

// === فيسبوك OAuth ===
app.get('/auth/facebook', (req, res) => {
    const redirectUri = `https://${req.get('host')}/auth/facebook/callback`;
    const url = `https://www.facebook.com/v18.0/dialog/oauth?client_id=${process.env.FB_APP_ID}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=pages_messaging,pages_read_engagement&response_type=code`;
    res.redirect(url);
});

app.get('/auth/facebook/callback', async (req, res) => {
    const code = req.query.code;
    if (!code) return res.send('فشل الربط');

    try {
        const tokenRes = await axios.get('https://graph.facebook.com/v18.0/oauth/access_token', {
            params: { client_id: process.env.FB_APP_ID, client_secret: process.env.FB_APP_SECRET, code, redirect_uri: `https://${req.get('host')}/auth/facebook/callback` }
        });
        const pageRes = await axios.get(`https://graph.facebook.com/me/accounts?access_token=${tokenRes.data.access_token}`);
        const page = pageRes.data.data[0];
        if (!page) return res.send('لا توجد صفحات');

        db.run('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', ['fb_token', page.access_token]);
        db.run('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', ['fb_page_name', page.name]);

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

// === WebSocket ===
io.on('connection', (socket) => {
    console.log('متصل');
});

// Vercel Handler
export default function handler(req, res) {
    if (req.method === 'GET' && !req.url.startsWith('/api') && !req.url.startsWith('/auth')) {
        res.sendFile(require('path').join(__dirname, '../public/index.html'));
    }
}