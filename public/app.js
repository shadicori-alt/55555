// app.js
let ws;
function login() {
    const u = document.getElementById('username').value;
    const p = document.getElementById('password').value;
    fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: u, password: p }) })
        .then(r => r.json())
        .then(d => {
            if (d.success) {
                document.getElementById('login').style.display = 'none';
                document.getElementById('app').style.display = 'block';
                connect();
                loadAll();
            } else alert('خطأ في تسجيل الدخول');
        });
}

function connect() {
    ws = new WebSocket(`ws://${location.host}`);
    ws.onmessage = () => loadAll();
}

function showPage(id) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelector(`[data-page="${id}"]`).classList.add('active');
}

async function loadAll() {
    // تحميل كل البيانات
}

// باقي الـ JS (سأرسله في الرد التالي)

document.getElementById('chat-bot').onclick = () => {
    document.getElementById('chat-window').style.display = document.getElementById('chat-window').style.display === 'block' ? 'none' : 'block';
};