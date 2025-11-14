let ws;
function connect() {
    ws = new WebSocket(`ws://${location.host}`);
    ws.onmessage = () => loadAll();
    ws.onclose = () => setTimeout(connect, 3000);
}
connect();

async function loadAll() {
    const [orders, agents] = await Promise.all([
        fetch('/api/orders').then(r => r.json()),
        fetch('/api/agents').then(r => r.json())
    ]);
    document.getElementById('total').textContent = orders.length;
    document.getElementById('pending').textContent = orders.filter(o => o.status === 'pending').length;
    renderOrders(orders);
    renderAgents(agents);
}

function renderOrders(orders) {
    const list = document.getElementById('orders-list');
    list.innerHTML = orders.map(o => `
        <div class="border p-3 rounded mb-2">
            <strong>${o.name}</strong> - ${o.phone}
            <select class="form-select form-select-sm float-end w-auto" onchange="updateStatus(${o.id}, this.value)">
                <option ${o.status==='pending'?'selected':''}>معلق</option>
                <option ${o.status==='delivering'?'selected':''}>جاري</option>
                <option ${o.status==='done'?'selected':''}>تم</option>
            </select>
        </div>
    `).join('') || '<p>لا توجد طلبات</p>';
}

async function updateStatus(id, status) {
    await fetch(`/api/orders/${id}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({status}) });
}

function addOrder() {
    const name = prompt('الاسم:');
    const phone = prompt('الهاتف:');
    if (name && phone) {
        fetch('/api/orders', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name, phone, address: '', agent: '', payment: 'نقدي'}) });
    }
}

function renderAgents(agents) {
    document.getElementById('agents-list').innerHTML = agents.map(a => `
        <div class="border p-3 rounded text-center">
            <p class="fw-bold">${a.name}</p>
            <button class="btn btn-sm ${a.active?'btn-success':'btn-secondary'}">نشط</button>
        </div>
    `).join('');
}

async function saveKeys() {
    const keys = {
        twilio_sid: document.getElementById('twilio_sid').value,
        twilio_token: document.getElementById('twilio_token').value,
        grok_key: document.getElementById('grok_key').value
    };
    for (let [k, v] of Object.entries(keys)) {
        if (v) await fetch('/api/settings', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({key: k, value: v}) });
    }
    alert('تم الحفظ');
}

document.querySelectorAll('.nav-link').forEach(l => l.onclick = () => {
    document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
    document.getElementById(l.dataset.page).style.display = 'block';
    document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));
    l.classList.add('active');
});

loadAll();