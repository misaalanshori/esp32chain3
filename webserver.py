# webserver.py - Async MVC Web Server Engine with Chunked Streaming & Route Dispatching
import asyncio
import gc
from aop import ROUTES

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
button{background:#21262d;color:var(--blue);border:1px solid var(--border);padding:6px 12px;border-radius:6px;font-size:0.75rem;cursor:pointer}
button:hover{background:#30363d}

/* Mirror Styles */
.mirror-box{display:flex;flex-direction:column;align-items:center;background:#06090e;border:2px solid #21262d;border-radius:12px;padding:18px 12px;margin:8px 0;box-shadow:inset 0 2px 10px rgba(0,0,0,0.8)}
.matrix-grid{display:grid;grid-template-columns:repeat(6,32px);gap:9px}
.led{width:32px;height:32px;border-radius:50%;background:#10151c;border:1px solid #1c2430;transition:background-color 0.08s ease,box-shadow 0.08s ease}
.sse-tag{font-size:0.7rem;color:var(--green);display:flex;align-items:center;gap:5px}
.sse-dot{width:6px;height:6px;border-radius:50%;background:var(--green)}

/* App List Styles */
.app-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:8px;margin-top:10px}
.app-item{background:#0e131a;border:1px solid var(--border);border-radius:6px;padding:8px 10px;display:flex;align-items:center;justify-content:space-between;font-size:0.85rem;transition:all 0.2s}
.app-item.active{border-color:var(--green);background:rgba(63,185,80,0.12);box-shadow:0 0 10px rgba(63,185,80,0.2)}
.app-item.selected{border-color:var(--blue);background:rgba(88,166,255,0.12);box-shadow:0 0 8px rgba(88,166,255,0.2)}
.app-id{background:#21262d;color:var(--text);padding:2px 6px;border-radius:4px;font-weight:bold;font-size:0.75rem;margin-right:6px}

/* Web Controllers UI */
.tab-btn{background:#161b22;color:var(--sub);border:1px solid var(--border);padding:6px 14px;border-radius:6px;font-size:0.8rem;cursor:pointer}
.tab-btn.active{background:#21262d;color:var(--blue);border-color:var(--blue)}
.paint-grid{display:grid;grid-template-columns:repeat(6,28px);gap:4px;background:#090d13;padding:8px;border-radius:8px;border:1px solid var(--border)}
.paint-cell{width:28px;height:28px;border-radius:4px;background:#161b22;border:1px solid #21262d;cursor:pointer}
.palette{display:grid;grid-template-columns:repeat(5,24px);gap:4px}
.swatch{width:24px;height:24px;border-radius:4px;cursor:pointer;border:1px solid #000}
.eff-btn{background:#161b22;color:var(--sub);border:1px solid var(--border);padding:6px 10px;border-radius:6px;cursor:pointer}
.eff-btn.active{border-color:var(--amber);color:var(--amber);background:rgba(210,153,34,0.15)}
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

<div class="card" style="margin-bottom:14px">
  <h2>
    <span>Web Controller Interfaces</span>
    <span style="font-size:0.75rem;color:var(--sub)">Apps 10 &ndash; 12</span>
  </h2>
  <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap">
    <button class="tab-btn active" id="btn-paint" onclick="switchTab('paint')">WebPaint (10)</button>
    <button class="tab-btn" id="btn-ticker" onclick="switchTab('ticker')">WebTicker (11)</button>
    <button class="tab-btn" id="btn-studio" onclick="switchTab('studio')">WebStudio (12)</button>
  </div>

  <div id="panel-paint">
    <div style="display:flex;gap:14px;align-items:flex-start;flex-wrap:wrap">
      <div>
        <div class="paint-grid" id="paintCanvas"></div>
        <div style="display:flex;gap:6px;margin-top:8px">
          <button onclick="clearCanvas()">Clear</button>
          <button onclick="sendCanvas()" style="background:var(--blue);color:#fff">Send & Launch</button>
        </div>
      </div>
      <div>
        <div style="font-size:0.8rem;color:var(--sub);margin-bottom:6px">Palette:</div>
        <div class="palette" id="paletteBox"></div>
        <input type="color" id="customColor" value="#00ffff" style="margin-top:6px;width:100%;height:28px;background:none;border:1px solid var(--border);border-radius:4px;cursor:pointer" onchange="pickColor(this.value)">
      </div>
    </div>
  </div>

  <div id="panel-ticker" style="display:none">
    <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">
      <input type="text" id="tickerInput" value="HELLO ESP32" placeholder="Scroll text..." style="flex:1;min-width:180px;background:#0d1117;color:var(--text);border:1px solid var(--border);border-radius:6px;padding:7px 10px">
      <input type="color" id="tickerColor" value="#00ffff" style="height:34px;width:44px;background:none;border:1px solid var(--border);border-radius:6px;cursor:pointer">
      <button onclick="sendTicker()" style="background:var(--blue);color:#fff">Send & Scroll</button>
    </div>
    <div style="display:flex;gap:6px;flex-wrap:wrap">
      <span style="font-size:0.75rem;color:var(--sub);align-self:center">Presets:</span>
      <button onclick="presetTicker('HELLO')">HELLO</button>
      <button onclick="presetTicker('AFK')">AFK</button>
      <button onclick="presetTicker('BUSY')">BUSY</button>
      <button onclick="presetTicker('COFFEE')">COFFEE</button>
      <button onclick="presetTicker('ONLINE')">ONLINE</button>
    </div>
  </div>

  <div id="panel-studio" style="display:none">
    <div style="display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap">
      <button class="eff-btn active" id="eff-candle" onclick="pickEff('candle', this)">Candle</button>
      <button class="eff-btn" id="eff-breath" onclick="pickEff('breath', this)">Breathing</button>
      <button class="eff-btn" id="eff-strobe" onclick="pickEff('strobe', this)">Strobe</button>
      <button class="eff-btn" id="eff-wave" onclick="pickEff('wave', this)">Wave</button>
      <button class="eff-btn" id="eff-solid" onclick="pickEff('solid', this)">Solid</button>
    </div>
    <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
      <div style="display:flex;align-items:center;gap:6px">
        <span style="font-size:0.8rem;color:var(--sub)">Color:</span>
        <input type="color" id="studioColor" value="#ff8800" style="height:32px;width:44px;background:none;border:1px solid var(--border);border-radius:6px;cursor:pointer" onchange="sendStudio()">
      </div>
      <button onclick="sendStudio()" style="background:var(--blue);color:#fff">Apply Effect</button>
    </div>
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
    <div style="display:flex;gap:6px;align-items:center">
      <button onclick="launchApp('menu')" style="padding:3px 8px;font-size:0.7rem">Return to Menu</button>
      <span id="appSummary" style="font-size:0.75rem;color:var(--sub)">13 Apps</span>
    </div>
  </h2>
  <div class="app-list" id="appList">
    <div style="color:var(--sub);font-size:0.85rem">Loading apps...</div>
  </div>
</div>

<div class="card" style="margin-top:14px">
  <h2>
    <span>MPU6050 3-Axis Spectrogram Heatmap</span>
    <span class="sse-tag"><div class="sse-dot"></div> 300 Hz (&lt;5ms) SSE Stream</span>
  </h2>
  <div style="margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">
    <div style="display:flex;align-items:center;gap:6px">
      <span style="font-size:0.8rem;color:var(--sub)">Axis:</span>
      <button class="eff-btn active" id="ax-xyz" onclick="setSpectroAxis('xyz', this)" style="padding:2px 8px;font-size:0.75rem">XYZ</button>
      <button class="eff-btn" id="ax-x" onclick="setSpectroAxis('x', this)" style="padding:2px 8px;font-size:0.75rem">X</button>
      <button class="eff-btn" id="ax-y" onclick="setSpectroAxis('y', this)" style="padding:2px 8px;font-size:0.75rem">Y</button>
      <button class="eff-btn" id="ax-z" onclick="setSpectroAxis('z', this)" style="padding:2px 8px;font-size:0.75rem">Z</button>
    </div>
    <div style="display:flex;align-items:center;gap:8px">
      <div style="font-size:0.8rem;color:var(--sub)">Energy: <strong id="fftEnergyVal" style="color:var(--text)">0</strong></div>
      <button onclick="launchApp(13)" style="padding:2px 8px;font-size:0.7rem">Launch MPU_FFT (13)</button>
    </div>
  </div>

  <div class="bar-wrap" style="height:8px;margin-bottom:10px"><div id="fftEnergyBar" class="bar" style="background:var(--green)"></div></div>

  <div style="position:relative;background:#050810;border:1px solid var(--border);border-radius:6px;overflow:hidden">
    <div style="position:absolute;left:4px;top:2px;font-size:0.65rem;color:var(--sub);font-family:monospace;pointer-events:none">150 Hz &uarr;</div>
    <div style="position:absolute;left:4px;bottom:2px;font-size:0.65rem;color:var(--sub);font-family:monospace;pointer-events:none">0 Hz (DC Filtered) &darr;</div>
    <div style="position:absolute;right:6px;top:2px;font-size:0.65rem;color:var(--sub);font-family:monospace;pointer-events:none" id="peakFreqText">Peak: - Hz</div>
    <canvas id="spectroCanvas" width="360" height="112" style="width:100%;height:112px;display:block;image-rendering:pixelated"></canvas>
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;font-size:0.7rem;color:var(--sub)">
    <span>&larr; Earlier Time</span>
    <span style="display:flex;align-items:center;gap:4px">
      <span>Inferno:</span>
      <div style="width:60px;height:8px;border-radius:2px;background:linear-gradient(to right, #000, #3c096c, #e85d04, #ffdd00, #fff)"></div>
      <span>Peak</span>
    </span>
    <span>Live (Now) &rarr;</span>
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
const grid = document.getElementById('matrixGrid');
for(let i=0; i<30; i++){
  const d = document.createElement('div');
  d.className = 'led';
  grid.appendChild(d);
}
const leds = grid.children;

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

let sseSource = null;
function startSSE(){
  try{
    if(sseSource){ sseSource.close(); }
    sseSource = new EventSource('/events');
    sseSource.onmessage = function(e){
      renderBinaryScreen(e.data);
    };
    sseSource.onerror = function(){};
  }catch(e){}
}
startSSE();

let spectroAxis = 'xyz';
function setSpectroAxis(ax, btn){
  spectroAxis = ax;
  document.querySelectorAll('#ax-xyz, #ax-x, #ax-y, #ax-z').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

function getHeatColor(val){
  const norm = Math.min(1, Math.max(0, val / 255));
  if(norm < 0.25){
    const t = norm / 0.25;
    return `rgb(${Math.round(40 * t)}, ${Math.round(10 * t)}, ${Math.round(80 * t)})`;
  }else if(norm < 0.5){
    const t = (norm - 0.25) / 0.25;
    return `rgb(${Math.round(40 + 180 * t)}, ${Math.round(10 + 40 * t)}, ${Math.round(80 - 60 * t)})`;
  }else if(norm < 0.75){
    const t = (norm - 0.5) / 0.25;
    return `rgb(${Math.round(220 + 35 * t)}, ${Math.round(50 + 170 * t)}, ${Math.round(20 - 10 * t)})`;
  }else{
    const t = (norm - 0.75) / 0.25;
    return `rgb(255, ${Math.round(220 + 35 * t)}, ${Math.round(10 + 245 * t)})`;
  }
}

let fftSource = null;
const spectroCanvas = document.getElementById('spectroCanvas');
const spectroCtx = spectroCanvas ? spectroCanvas.getContext('2d') : null;
if(spectroCtx){
  spectroCtx.fillStyle = '#050810';
  spectroCtx.fillRect(0, 0, spectroCanvas.width, spectroCanvas.height);
}

function startFftSSE(){
  try{
    if(fftSource) fftSource.close();
    fftSource = new EventSource('/events/fft');
    fftSource.onmessage = function(e){
      try{
        const b = atob(e.data.trim());
        if(b.length < 50) return;
        const energy = b.charCodeAt(1);
        document.getElementById('fftEnergyVal').innerText = energy;
        const eBar = document.getElementById('fftEnergyBar');
        const pct = Math.min(100, Math.round((energy / 255) * 100));
        eBar.style.width = pct + '%';
        eBar.style.backgroundColor = (pct > 65) ? 'var(--red)' : ((pct > 30) ? 'var(--amber)' : 'var(--green)');

        if(spectroCtx){
          const w = spectroCanvas.width, h = spectroCanvas.height;
          // Waterfall scroll: shift canvas left by 2px
          spectroCtx.drawImage(spectroCanvas, -2, 0);

          const binH = h / 16;
          let peakBin = 0, peakMag = 0;
          for(let i=0; i<16; i++){
            const mx = b.charCodeAt(2 + i);
            const my = b.charCodeAt(18 + i);
            const mz = b.charCodeAt(34 + i);
            let val = 0;
            if(spectroAxis === 'xyz') val = Math.max(mx, my, mz);
            else if(spectroAxis === 'x') val = mx;
            else if(spectroAxis === 'y') val = my;
            else if(spectroAxis === 'z') val = mz;

            if(i > 0 && val > peakMag){ peakMag = val; peakBin = i; }

            spectroCtx.fillStyle = getHeatColor(val);
            spectroCtx.fillRect(w - 2, h - Math.round((i + 1) * binH), 2, Math.ceil(binH) + 1);
          }
          const peakHz = Math.round(peakBin * 9.38);
          document.getElementById('peakFreqText').innerText = `Peak: ${peakHz} Hz (${peakMag})`;
        }
      }catch(err){}
    };
  }catch(e){}
}
startFftSSE();

let paintColor = '#00ffff';
const paintBuf = Array(30).fill('#000000');
const paintGrid = document.getElementById('paintCanvas');
let isMouseDown = false;
document.body.onmousedown = () => isMouseDown = true;
document.body.onmouseup = () => isMouseDown = false;

for(let i=0; i<30; i++){
  const c = document.createElement('div');
  c.className = 'paint-cell';
  c.onmousedown = () => { paintBuf[i] = paintColor; c.style.backgroundColor = paintColor; };
  c.onmouseenter = () => { if(isMouseDown){ paintBuf[i] = paintColor; c.style.backgroundColor = paintColor; } };
  paintGrid.appendChild(c);
}

const paletteColors = ['#ff0000','#ff8800','#ffff00','#00ff00','#00ffff','#0088ff','#aa00ff','#ffffff','#555555','#000000'];
const palBox = document.getElementById('paletteBox');
paletteColors.forEach(col => {
  const s = document.createElement('div');
  s.className = 'swatch';
  s.style.backgroundColor = col;
  s.onclick = () => pickColor(col);
  palBox.appendChild(s);
});

function pickColor(c){
  paintColor = c;
  document.getElementById('customColor').value = c;
}
function clearCanvas(){
  paintBuf.fill('#000000');
  Array.from(paintGrid.children).forEach(c => c.style.backgroundColor = '#161b22');
  sendCanvas();
}
async function sendCanvas(){
  await fetch('/api/paint', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({pixels:paintBuf})});
}

function presetTicker(t){
  document.getElementById('tickerInput').value = t;
  sendTicker();
}
async function sendTicker(){
  const t = document.getElementById('tickerInput').value;
  const c = document.getElementById('tickerColor').value;
  await fetch('/api/ticker', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text:t, color:c})});
}

let curEff = 'candle';
function pickEff(e, btn){
  curEff = e;
  document.querySelectorAll('.eff-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  sendStudio();
}
async function sendStudio(){
  const c = document.getElementById('studioColor').value;
  await fetch('/api/studio', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({effect:curEff, color:c})});
}

async function launchApp(target){
  try{
    await fetch('/api/launch', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({app:target})});
    setTimeout(updateState, 100);
  }catch(e){}
}

function switchTab(t){
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('btn-' + t).classList.add('active');
  document.getElementById('panel-paint').style.display = (t==='paint')?'block':'none';
  document.getElementById('panel-ticker').style.display = (t==='ticker')?'block':'none';
  document.getElementById('panel-studio').style.display = (t==='studio')?'block':'none';
}

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
    let btnHtml = '';
    if(isRunning){
      cls += ' active';
      btnHtml = `<button onclick="launchApp('menu')" style="background:var(--red);color:#fff;padding:2px 8px;font-size:0.7rem;border:none">Exit</button>`;
    }else{
      if(isSelected) cls += ' selected';
      btnHtml = `<button onclick="launchApp(${a.id})" style="background:#21262d;color:var(--blue);padding:2px 8px;font-size:0.7rem">Launch &#9654;</button>`;
    }
    return `<div class="${cls}">
      <div style="display:flex;align-items:center">
        <span class="app-id">${a.id}</span>
        <strong>${a.name}</strong>
      </div>
      ${btnHtml}
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

class HttpRequest:
    def __init__(self, method, path, headers, body, writer):
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body
        self.writer = writer

class WebServer:
    def __init__(self, ioc, port=80):
        self.ioc = ioc
        self.port = port
        self.routes = []

    def register_controller(self, controller_instance):
        cls = controller_instance.__class__
        for method, path, fn in ROUTES:
            for attr in dir(cls):
                if getattr(cls, attr) == fn:
                    self.routes.append((method, path, controller_instance, fn))
                    break

    async def _dispatch(self, request):
        for method, route_path, ctrl, action in self.routes:
            if method == request.method and route_path == request.path:
                return await action(ctrl, request)
        return 404, "text/plain", "Not Found"

    async def handle_client(self, reader, writer):
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

            # Read headers
            headers = {}
            content_len = 0
            while True:
                line = await reader.readline()
                if not line or line == b"\r\n" or line == b"\n":
                    break
                if line.lower().startswith(b"content-length:"):
                    try:
                        content_len = int(line.split(b":")[1].strip())
                    except Exception:
                        pass

            body = b""
            if content_len > 0:
                body = await reader.readexactly(content_len)

            request = HttpRequest(method, path, headers, body, writer)

            if method == "OPTIONS":
                writer.write(b"HTTP/1.1 204 No Content\r\nAccess-Control-Allow-Origin: *\r\nAccess-Control-Allow-Methods: GET, POST, OPTIONS\r\nAccess-Control-Allow-Headers: Content-Type\r\nConnection: close\r\n\r\n")
            elif path == "/" or path == "/index.html":
                # Static MVC View streaming
                writer.write(HTML_HDR)
                await writer.drain()
                CHUNK_SIZE = 1460
                for i in range(0, len(HTML_BYTES), CHUNK_SIZE):
                    writer.write(HTML_BYTES[i:i + CHUNK_SIZE])
                    await writer.drain()
            else:
                # Dispatch through AOP Route Table
                code, ctype, res_body = await self._dispatch(request)
                if code is not None:
                    res_bytes = res_body.encode("utf-8") if isinstance(res_body, str) else res_body
                    hdr = f"HTTP/1.1 {code} OK\r\nContent-Type: {ctype}\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\nContent-Length: {len(res_bytes)}\r\n\r\n".encode("utf-8")
                    writer.write(hdr + res_bytes)

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

    async def run_server(self):
        server = await asyncio.start_server(self.handle_client, "0.0.0.0", self.port)
        print(f"MVC WebServer listening on port {self.port}")
        while True:
            await asyncio.sleep(1)
