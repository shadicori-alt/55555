// public/app.js - كامل 100%
let ws;
const settings = {};

function login() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            document.getElementById('login').style.display = 'none';
            document.getElementById('app').style.display = 'block';
            connectWebSocket();
            loadAllData();
        } else alert('خطأ');
    });
}

function connectWebSocket() {
    ws = new WebSocket(`wss://${location.host}`);
    ws.onmessage = () => loadAllData();
    ws.onclose = () => setTimeout(connectWebSocket, 3000);
}

async function loadAllData() {
    const [orders, agents, s] = await Promise.all([
        fetch('/api/orders').then(r => r.json()),
        fetch('/api/agents').then(r => r.json()),
        fetch('/api/settings').then(r => r.json())
    ]);
    Object.assign(settings, s);
    renderLinks();
    renderOrders(orders);
    renderAgents(agents);
    renderAccounts(orders);
}

function renderLinks() {
    document.getElementById('fb-status').textContent = settings.fb_page_name || 'غير متصل';
    document.getElementById('fb-status').className = settings.fb_token ? 'badge bg-success ms-2' : 'badge bg-secondary ms-2';
    document.getElementById('fb-connect').onclick = () => {
        const win = window.open('/auth/facebook', 'fb', 'width=600,height=700');
        const check = setInterval(() => { if (win.closed) { clearInterval(check); loadAllData(); } }, 1000);
    };
    document.getElementById('twilio-sid').value = settings.twilio_sid || '';
    document.getElementById('twilio-token').value = settings.twilio_token || '';
}

async function saveSetting(k, v) {
    await fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: k, value: v }) });
}
function saveTwilio() { saveSetting('twilio_sid', document.getElementById('twilio-sid').value); saveSetting('twilio_token', document.getElementById('twilio-token').value); alert('تم'); }

function renderOrders(orders) {
    const list = document.getElementById('orders-list');
    list.innerHTML = orders.map(o => `
        <div class="border p-3 rounded mb-2 ${o.closed ? 'bg-light' : ''}">
            <div class="d-flex justify-content-between">
                <div><strong>#${o.id}</strong> ${o.name} - ${o.governorate}</div>
                ${!o.closed ? `<button class="btn btn-sm btn-success" onclick="closeOrder(${o.id})">تقفيل</button>` : `<span class="badge bg-success">مُقفل</span>`}
            </div>
        </div>
    `).join('');
}

function addOrder() {
    const name = prompt('اسم:'); const phone = prompt('هاتف:'); const gov = prompt('محافظة:');
    if (name && phone && gov) fetch('/api/orders', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, phone, governorate: gov }) }).then(loadAllData);
}

function closeOrder(id) {
    const price = prompt('المبلغ:');
    if (price) fetch(`/api/orders/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ closed: true, price }) }).then(loadAllData);
}

function renderAgents(agents) {
    document.getElementById('agents-list').innerHTML = agents.map(a => `
        <div class="col-md-4"><div class="card p-3 text-center"><h6>${a.name}</h6><p>${a.governorate}</p></div></div>
    `).join('');
}

function addAgent() {
    const name = prompt('اسم:'); const phone = prompt('هاتف:'); const gov = prompt('محافظة:');
    if (name && phone && gov) fetch('/api/agents', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, phone, governorate: gov }) }).then(loadAllData);
}

function renderAccounts(orders) {
    const today = new Date().toISOString().split('T')[0];
    const closed = orders.filter(o => o.closed && o.created_at.startsWith(today));
    const total = closed.reduce((s, o) => s + o.price, 0);
    document.getElementById('today-total').textContent = total;
}

function toggleStep(step) {
    const btn = document.getElementById(`step-${step}`);
    btn.textContent = btn.textContent === 'تشغيل' ? 'إيقاف' : 'تشغيل';
    btn.className = btn.textContent === 'إيقاف' ? 'btn btn-sm btn-outline-danger w-100' : 'btn btn-sm btn-outline-primary w-100';
}
function stopAll() {
    ['page', 'order', 'dist', 'close'].forEach(s => {
        const btn = document.getElementById(`step-${s}`);
        btn.textContent = 'تشغيل';
        btn.className = 'btn btn-sm btn-outline-primary w-100';
    });
}

document.querySelectorAll('.nav-link').forEach(l => l.onclick = () => {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));
    document.getElementById(l.dataset.page).classList.add('active');
    l.classList.add('active');
});