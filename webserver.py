# webserver.py - Async Web Server with SSE Screen Mirroring, Live Dashboard and JSON State API
import asyncio
import json
import time
import ubinascii
import gc
from state import system_state

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ESP32-C3 Chain3 Dashboard</title>
<style>
:root{--bg:#0d1117;--card:#161b22;--border:#30363d;--text:#c9d1d9;--sub:#8b949e;--blue:#58a6ff;--green:#3fb950;--amber:#d29922;--red:#f85149}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:16px;max-width:960px;margin:auto}
header{display:flex;justify-content:space-between;align-items:center;padding-bottom:14px;border-bottom:1px solid var(--border);margin-bottom:16px}
h1{font-size:1.25rem;font-weight:600;display:flex;align-items:center;gap:8px}
.pulse{width:10px;height:10px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);animation:blink 1.8s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}
.badge{padding:3px 10px;border-radius:12px;font-size:0.75rem;font-weight:600;text-transform:uppercase}
.badge-sta{background:rgba(63,185,80,0.15);color:var(--green);border:1px solid var(--green)}
.badge-ap{background:rgba(210,153,34,0.15);color:var(--amber);border:1px solid var(--amber)}
.badge-disc{background:rgba(248,81,73,0.15);color:var(--red);border:1px solid var(--red)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px}
.card h2{font-size:0.9rem;font-weight:600;color:var(--sub);margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}
.stat{display:flex;justify-content:space-between;padding:5px 0;font-size:0.85rem;border-bottom:1px solid rgba(48,54,61,0.5)}
.stat:last-child{border-bottom:none}
.stat span:first-child{color:var(--sub)}
.val{font-weight:600;font-family:monospace;color:var(--text)}
.bar-wrap{background:#21262d;border-radius:4px;height:8px;overflow:hidden;margin-top:4px}
.bar{height:100%;background:var(--blue);width:0%;transition:width 0.4s}
table{width:100%;border-collapse:collapse;margin-top:8px;font-size:0.8rem}
th,td{padding:6px 4px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--sub);font-weight:500}
button{background:#21262d;color:var(--blue);border:1px solid var(--border);padding:4px 10px;border-radius:6px;font-size:0.75rem;cursor:pointer}
button:hover{background:#30363d}

/* Mirror Styles */
.mirror-box{display:flex;flex-direction:column;align-items:center;background:#06090e;border:2px solid #21262d;border-radius:12px;padding:18px 12px;margin:8px 0;box-shadow:inset 0 2px 10px rgba(0,0,0,0.8)}
.matrix-grid{display:grid;grid-template-columns:repeat(6,32px);gap:9px}
.led{width:32px;height:32px;border-radius:50%;background:#10151c;border:1px solid #1c2430;transition:background-color 0.08s ease,box-shadow 0.08s ease}
.sse-tag{font-size:0.7rem;color:var(--green);display:flex;align-items:center;gap:5px}
.sse-dot{width:6px;height:6px;border-radius:50%;background:var(--green)}

/* App List Styles */
.app-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px;margin-top:10px}
.app-item{background:#0e131a;border:1px solid var(--border);border-radius:6px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;font-size:0.85rem;transition:all 0.2s}
.app-item.active{border-color:var(--green);background:rgba(63,185,80,0.12);box-shadow:0 0 10px rgba(63,185,80,0.2)}
.app-item.selected{border-color:var(--blue);background:rgba(88,166,255,0.12);box-shadow:0 0 8px rgba(88,166,255,0.2)}
.app-id{background:#21262d;color:var(--text);padding:2px 7px;border-radius:4px;font-weight:bold;font-size:0.75rem;margin-right:8px}
</style>
</head>
<body>
<header>
  <h1><div class="pulse" id="pulseDot"></div> ESP32-C3 Chain3</h1>
  <div id="statusBadge" class="badge badge-sta">CONNECTING</div>
</header>

<div class="card" style="margin-bottom:14px">
  <h2>
    <span>Live Screen Mirror (6 &times; 5 Matrix)</span>
    <span class="sse-tag"><div class="sse-dot"></div> SSE Live Stream</span>
  </h2>
  <div class="mirror-box">
    <div class="matrix-grid" id="matrixGrid"></div>
  </div>
</div>

<div class="grid">
  <div class="card">
    <h2>WiFi Network <span id="wifiMode" style="font-size:0.75rem;color:var(--sub)"></span></h2>
    <div class="stat"><span>SSID</span><span id="wifiSsid" class="val">-</span></div>
    <div class="stat"><span>IP Address</span><span id="wifiIp" class="val">-</span></div>
    <div class="stat"><span>Signal (RSSI)</span><span id="wifiRssi" class="val">-</span></div>
    <div class="stat"><span>MAC Address</span><span id="wifiMac" class="val">-</span></div>
    <div class="stat"><span>Gateway</span><span id="wifiGw" class="val">-</span></div>
    <div class="stat"><span>Reconnects</span><span id="wifiRec" class="val">0</span></div>
  </div>
  <div class="card">
    <h2>System & Resources</h2>
    <div class="stat"><span>Uptime</span><span id="sysUptime" class="val">00:00:00</span></div>
    <div class="stat"><span>CPU Frequency</span><span id="sysCpu" class="val">-</span></div>
    <div class="stat"><span>RAM Usage</span><span id="sysRam" class="val">-</span></div>
    <div class="bar-wrap"><div id="ramBar" class="bar"></div></div>
    <div class="stat" style="margin-top:6px"><span>Free Heap</span><span id="sysFree" class="val">-</span></div>
  </div>
  <div class="card">
    <h2>App & Menu</h2>
    <div class="stat"><span>Active State</span><span id="appActive" class="val" style="color:var(--blue)">-</span></div>
    <div class="stat"><span>Menu Selection</span><span id="appIdx" class="val">-</span></div>
    <div class="stat"><span>Matrix Size</span><span class="val">6 &times; 5 NeoPixel</span></div>
    <div class="stat"><span>Boot Button</span><span class="val">GPIO 9 (Active LOW)</span></div>
  </div>
  <div class="card">
    <h2>MPU6050 IMU Sensors</h2>
    <div class="stat"><span>Sensor Status</span><span id="imuStatus" class="val">-</span></div>
    <div class="stat"><span>Accel X (m/s&sup2;)</span><span id="imuX" class="val">-</span></div>
    <div class="stat"><span>Accel Y (m/s&sup2;)</span><span id="imuY" class="val">-</span></div>
    <div class="stat"><span>Accel Z (m/s&sup2;)</span><span id="imuZ" class="val">-</span></div>
    <div class="stat"><span>Temperature</span><span id="imuTemp" class="val">-</span></div>
  </div>
</div>

<div class="card" style="margin-top:14px">
  <h2>
    <span>Registered Applications</span>
    <span id="appSummary" style="font-size:0.75rem;color:var(--sub)">9 Apps</span>
  </h2>
  <div class="app-list" id="appList">
    <div style="color:var(--sub);font-size:0.85rem">Loading apps...</div>
  </div>
</div>

<div class="card" style="margin-top:14px">
  <h2>Scanned Networks <button onclick="triggerScan()">Refresh Scan</button></h2>
  <table>
    <thead><tr><th>SSID</th><th>RSSI</th><th>Security</th></tr></thead>
    <tbody id="scanTable"><tr><td colspan="3" style="color:var(--sub)">No scan results yet...</td></tr></tbody>
  </table>
</div>

<script>
// Build 30 LEDs
const grid = document.getElementById('matrixGrid');
for(let i=0; i<30; i++){
  const d = document.createElement('div');
  d.className = 'led';
  grid.appendChild(d);
}
const leds = grid.children;

// Binary SSE Parser for 30 RGB triplets (90 bytes base64-encoded)
function renderBinaryScreen(b64){
  try{
    const b = atob(b64.trim());
    if(b.length < 90) return;
    for(let i=0; i<30; i++){
      const r = b.charCodeAt(i*3);
      const g = b.charCodeAt(i*3+1);
      const bl = b.charCodeAt(i*3+2);
      const c = `rgb(${r},${g},${bl})`;
      leds[i].style.backgroundColor = c;
      if(r || g || bl){
        leds[i].style.boxShadow = '0 0 12px ' + c;
        leds[i].style.borderColor = c;
      } else {
        leds[i].style.boxShadow = 'none';
        leds[i].style.borderColor = '#1c2430';
      }
    }
  }catch(err){}
}

// Server-Sent Events (SSE) with Binary Base64 Payload
let sseSource = null;
function startSSE(){
  try{
    if(sseSource){ sseSource.close(); }
    sseSource = new EventSource('/events');
    sseSource.onmessage = function(e){
      renderBinaryScreen(e.data);
    };
    sseSource.onerror = function(){
      // Reconnect handled automatically by browser EventSource
    };
  }catch(e){}
}
startSSE();

function fmtUptime(s){
  const h=Math.floor(s/3600),m=Math.floor((s%3600)/60),sec=s%60;
  return `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`;
}

async function updateState(){
  try{
    const r = await fetch('/api/state');
    if(!r.ok) return;
    const d = await r.json();

    const w = d.wifi || {};
    const badge = document.getElementById('statusBadge');
    badge.innerText = w.status || 'UNKNOWN';
    badge.className = 'badge ' + (w.status==='CONNECTED'?'badge-sta':(w.status==='AP_MODE'?'badge-ap':'badge-disc'));
    document.getElementById('wifiMode').innerText = w.mode || '';
    document.getElementById('wifiSsid').innerText = w.ssid || '-';
    document.getElementById('wifiIp').innerText = w.ip || '-';
    document.getElementById('wifiRssi').innerText = w.rssi ? (w.rssi + ' dBm') : '-';
    document.getElementById('wifiMac').innerText = w.mac || '-';
    document.getElementById('wifiGw').innerText = w.gateway || '-';
    document.getElementById('wifiRec').innerText = w.reconnect_count || '0';

    const s = d.system || {};
    document.getElementById('sysUptime').innerText = fmtUptime(s.uptime_s || 0);
    document.getElementById('sysCpu').innerText = (s.cpu_freq_mhz || 160) + ' MHz';
    const tot = s.total_ram || 1, free = s.free_ram || 0, used = tot - free;
    const pct = Math.round((used / tot) * 100);
    document.getElementById('sysRam').innerText = `${pct}% (${Math.round(used/1024)}K / ${Math.round(tot/1024)}K)`;
    document.getElementById('ramBar').style.width = pct + '%';
    document.getElementById('sysFree').innerText = `${Math.round(free/1024)} KB`;

    const a = d.app || {};
    document.getElementById('appActive').innerText = a.active || 'Menu';
    document.getElementById('appIdx').innerText = 'App ' + (a.menu_index || 1);
    if(a.list && a.list.length > 0){
      renderAppList(a.list, a.active, a.menu_index);
    }

    const imu = d.sensors || {};
    document.getElementById('imuStatus').innerText = imu.active ? 'Active' : 'Idle / Standby';
    document.getElementById('imuX').innerText = imu.x !== undefined ? imu.x : '-';
    document.getElementById('imuY').innerText = imu.y !== undefined ? imu.y : '-';
    document.getElementById('imuZ').innerText = imu.z !== undefined ? imu.z : '-';
    document.getElementById('imuTemp').innerText = imu.temp !== undefined ? (imu.temp + ' \u00b0C') : '-';

    if(w.scanned && w.scanned.length > 0){
      renderScanTable(w.scanned);
    }
  }catch(e){}
}

function renderScanTable(list){
  const tb = document.getElementById('scanTable');
  tb.innerHTML = list.slice(0, 8).map(n => `<tr><td><strong>${n.ssid}</strong></td><td>${n.rssi} dBm</td><td>${n.secure ? 'WPA/WPA2' : 'Open'}</td></tr>`).join('');
}

function renderAppList(apps, activeApp, menuIdx){
  const el = document.getElementById('appList');
  if(!apps || !apps.length) return;
  el.innerHTML = apps.map(a => {
    const isRunning = (activeApp === a.name);
    const isSelected = (activeApp === 'Menu' && menuIdx === a.id);
    let cls = 'app-item';
    let badge = '<span style="color:var(--sub);font-size:0.7rem">Ready</span>';
    if(isRunning){
      cls += ' active';
      badge = '<span class="badge badge-sta" style="font-size:0.65rem">Running</span>';
    }else if(isSelected){
      cls += ' selected';
      badge = '<span class="badge" style="background:rgba(88,166,255,0.15);color:var(--blue);border:1px solid var(--blue);font-size:0.65rem">Selected</span>';
    }
    return `<div class="${cls}">
      <div style="display:flex;align-items:center">
        <span class="app-id">${a.id}</span>
        <strong>${a.name}</strong>
      </div>
      ${badge}
    </div>`;
  }).join('');
}

async function triggerScan(){
  try{
    const r = await fetch('/api/scan');
    const list = await r.json();
    renderScanTable(list);
  }catch(e){}
}

setInterval(updateState, 2000);
updateState();
</script>
</body>
</html>
"""

HTML_BYTES = HTML_DASHBOARD.encode("utf-8")
HTML_HDR = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\nContent-Length: {len(HTML_BYTES)}\r\n\r\n".encode("utf-8")

async def _stream_sse(writer):
    try:
        headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/event-stream\r\n"
            "Cache-Control: no-cache\r\n"
            "Connection: keep-alive\r\n"
            "Access-Control-Allow-Origin: *\r\n\r\n"
        )
        writer.write(headers.encode("utf-8"))
        await writer.drain()

        last_raw = bytearray(90)
        last_heartbeat = time.ticks_ms()
        while True:
            curr = system_state.get_screen_raw()
            now = time.ticks_ms()
            if curr != last_raw or time.ticks_diff(now, last_heartbeat) > 4000:
                b64 = ubinascii.b2a_base64(curr)
                writer.write(b"data: " + b64 + b"\n")
                await writer.drain()
                last_raw[:] = curr
                last_heartbeat = now
            await asyncio.sleep_ms(60)
    except Exception:
        pass

async def handle_client(reader, writer):
    try:
        req_line = await reader.readline()
        if not req_line:
            writer.close()
            return

        parts = req_line.decode("utf-8", "ignore").split()
        if len(parts) < 2:
            writer.close()
            return

        method, path = parts[0], parts[1]

        # Drain headers
        while True:
            line = await reader.readline()
            if not line or line == b"\r\n" or line == b"\n":
                break

        if path == "/events" or path == "/api/events":
            await _stream_sse(writer)
            return
        elif path == "/api/state":
            body = json.dumps(system_state.get_summary()).encode("utf-8")
            hdr = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\nContent-Length: {len(body)}\r\n\r\n".encode("utf-8")
            writer.write(hdr + body)
        elif path == "/api/scan":
            results = system_state.wifi_manager.scan() if system_state.wifi_manager else []
            body = json.dumps(results).encode("utf-8")
            hdr = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\nContent-Length: {len(body)}\r\n\r\n".encode("utf-8")
            writer.write(hdr + body)
        elif path == "/" or path == "/index.html":
            writer.write(HTML_HDR + HTML_BYTES)
        else:
            msg = b"Not Found"
            hdr = f"HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nConnection: close\r\nContent-Length: {len(msg)}\r\n\r\n".encode("utf-8")
            writer.write(hdr + msg)

        await writer.drain()
        gc.collect()
    except Exception:
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

async def run_server(port=80):
    server = await asyncio.start_server(handle_client, "0.0.0.0", port)
    print(f"Async web server listening on port {port}")
    while True:
        await asyncio.sleep(1)
