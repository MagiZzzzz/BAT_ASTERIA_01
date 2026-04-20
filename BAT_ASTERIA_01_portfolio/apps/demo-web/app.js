const fmt = (n, unit = '') => `${n}${unit}`;
const el = (tag, cls, html) => {
  const x = document.createElement(tag);
  if (cls) x.className = cls;
  if (html !== undefined) x.innerHTML = html;
  return x;
};

async function loadOverview() {
  const res = await fetch('/api/v1/overview');
  return res.json();
}

function render(snapshot) {
  const kpis = document.getElementById('kpis');
  const zones = document.getElementById('zones');
  const alarms = document.getElementById('alarms');
  const systems = document.getElementById('systems');
  const scenarioStatus = document.getElementById('scenario-status');

  kpis.innerHTML = '';
  [
    ['Alarmes ouvertes', snapshot.kpi.open_alarms],
    ['Puissance instantanée', fmt(snapshot.kpi.power_kw, ' kW')],
    ['CO2 max', fmt(snapshot.kpi.co2_max_ppm, ' ppm')],
    ['Zones occupées', snapshot.kpi.occupied_zones],
    ['CTA actives', snapshot.kpi.ahu_running],
  ].forEach(([label, value]) => {
    const box = el('div', 'kpi');
    box.appendChild(el('span', 'label', label));
    box.appendChild(el('div', 'value', value));
    kpis.appendChild(box);
  });

  zones.innerHTML = '';
  snapshot.zones.forEach(z => {
    const row = el('div', 'item');
    row.innerHTML = `
      <div>
        <strong>${z.name}</strong><br/>
        <span class="muted">Temp ${z.temperature.toFixed(1)}°C · CO2 ${z.co2} ppm · ${z.occupied ? 'Occupé' : 'Inoccupé'}</span>
      </div>
      <span class="badge ${z.co2 > 1100 ? 'danger' : z.co2 > 900 ? 'warn' : 'ok'}">${z.id}</span>
    `;
    zones.appendChild(row);
  });

  alarms.innerHTML = '';
  snapshot.alarms.forEach(a => {
    const row = el('div', 'item');
    row.innerHTML = `
      <div>
        <strong>${a.label}</strong><br/>
        <span class="muted">${a.id}</span>
      </div>
      <span class="badge ${a.active ? (a.severity === 'critical' ? 'danger' : 'warn') : 'ok'}">${a.active ? 'ACTIF' : 'OK'}</span>
    `;
    alarms.appendChild(row);
  });

  systems.innerHTML = '';
  [
    ['BACnet', 'ok'],
    ['Modbus', 'ok'],
    ['LoRaWAN', 'ok'],
    ['MQTT', 'ok'],
    ['Historian', 'ok'],
  ].forEach(([label, status]) => {
    const li = document.createElement('li');
    li.className = 'item';
    li.innerHTML = `<span>${label}</span><span class="badge ok">${status}</span>`;
    systems.appendChild(li);
  });

  scenarioStatus.textContent = snapshot.scenarios['ahu-failure'].running || snapshot.scenarios['high-co2'].running || snapshot.scenarios['schedule-switchover'].running
    ? 'Un scénario est en cours. La supervision s’actualise en direct.'
    : 'Aucun scénario en cours.';
}

async function triggerScenario(name) {
  const r = await fetch(`/api/v1/scenarios/${name}/trigger`, { method: 'POST' });
  render((await r.json()).snapshot);
}

async function resetScenario(name) {
  const r = await fetch(`/api/v1/scenarios/${name}/reset`, { method: 'POST' });
  render((await r.json()).snapshot);
}

document.addEventListener('click', async (e) => {
  const btn = e.target.closest('button');
  if (!btn) return;
  if (btn.dataset.scenario) await triggerScenario(btn.dataset.scenario);
  if (btn.dataset.reset) {
    for (const s of ['ahu-failure','high-co2','schedule-switchover']) {
      await resetScenario(s);
    }
  }
});

(async () => {
  render(await loadOverview());
  const wsProto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${wsProto}//${location.host}/ws/live`);
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.snapshot) render(msg.snapshot);
    } catch (_) {}
  };
})();
