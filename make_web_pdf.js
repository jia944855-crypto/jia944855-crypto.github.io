const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');
const WebSocket = global.WebSocket;
const { execFileSync } = require('child_process');

const root = process.cwd();
const outDir = `${root}/tmp/pdfs/santorini_pages`;
fs.mkdirSync(outDir, { recursive: true });
const pages = [
  ['01-首页', '/'],
  ['02-活动', '/activities/'],
  ['03-博物馆', '/allmuseums/'],
  ['04-建筑艺术文化', '/architecture-art-culture/'],
  ['05-海滩', '/beaches/'],
  ['06-联系我们', '/contact/'],
  ['07-体验', '/experiences/'],
  ['08-美食', '/gastronomy/'],
  ['09-历史', '/history/'],
  ['10-如何到达', '/how-to-get-here/'],
  ['11-锡拉夏岛', '/thirassia/'],
  ['12-火山', '/volcano/'],
  ['13-葡萄酒', '/wines/'],
];

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function getJson(url) { return new Promise((resolve, reject) => http.get(url, res => { let s=''; res.on('data', d=>s+=d); res.on('end', ()=>resolve(JSON.parse(s))); }).on('error', reject)); }
function cdp(ws, method, params={}) {
  return new Promise((resolve, reject) => {
    const id = ++cdp.next;
    const timer = setTimeout(() => reject(new Error(`CDP timeout ${method}`)), 30000);
    cdp.pending[id] = {resolve: v=>{clearTimeout(timer); resolve(v)}, reject};
    ws.send(JSON.stringify({id, method, params}));
  });
}
cdp.next = 0; cdp.pending = {};

(async () => {
  const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const chrome = spawn(chromePath, [
    '--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
    '--remote-debugging-port=9223', '--user-data-dir=/private/tmp/santorini-pdf-profile',
    '--window-size=1440,1000', 'about:blank'
  ], {stdio:'ignore'});
  let version;
  for (let i=0; i<30; i++) { try { version = await getJson('http://127.0.0.1:9223/json/version'); break; } catch { await sleep(300); } }
  if (!version) throw new Error('Chrome remote debugging did not start');
  const ws = new WebSocket(version.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { ws.onopen=resolve; ws.onerror=reject; });
  ws.onmessage = e => { const m=JSON.parse(e.data); if (m.id && cdp.pending[m.id]) { const p=cdp.pending[m.id]; delete cdp.pending[m.id]; m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); } };
  await cdp(ws, 'Page.enable');
  await cdp(ws, 'Emulation.setDeviceMetricsOverride', {width:1440, height:1000, deviceScaleFactor:1, mobile:false});
  for (const [name, route] of pages) {
    await cdp(ws, 'Page.navigate', {url:`http://127.0.0.1:8777${route}`});
    await sleep(1800);
    await cdp(ws, 'Runtime.evaluate', {expression:`document.fonts && document.fonts.ready` , awaitPromise:true, returnByValue:true}).catch(()=>{});
    await cdp(ws, 'Runtime.evaluate', {expression:`Promise.all(Array.from(document.images).map(i=>i.complete?true:new Promise(r=>{i.onload=i.onerror=()=>r(true)})))`, awaitPromise:true, returnByValue:true}).catch(()=>{});
    await sleep(800);
    const dims = await cdp(ws, 'Runtime.evaluate', {expression:`({w:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth),h:Math.max(document.documentElement.scrollHeight,document.body.scrollHeight)})`, returnByValue:true});
    const w = Math.min(Math.max(dims.result.value.w, 900), 1440);
    const h = Math.min(Math.max(dims.result.value.h, 1000), 30000);
    const shot = await cdp(ws, 'Page.captureScreenshot', {format:'png', fromSurface:true, captureBeyondViewport:true, clip:{x:0,y:0,width:w,height:h,scale:1}});
    fs.writeFileSync(`${outDir}/${name}.png`, Buffer.from(shot.data,'base64'));
  }
  ws.close(); chrome.kill('SIGTERM');
  const py = `
from PIL import Image
from pathlib import Path
files = sorted(Path(r'${outDir}').glob('*.png'))
imgs=[]
for f in files:
    im=Image.open(f).convert('RGB')
    imgs.append(im)
imgs[0].save(r'${root}/output/santorini网站13页面截图.pdf', save_all=True, append_images=imgs[1:], resolution=96.0)
`;
  fs.mkdirSync(`${root}/output`, {recursive:true});
  require('child_process').execFileSync('python3', ['-c', py], {stdio:'inherit'});
})();
