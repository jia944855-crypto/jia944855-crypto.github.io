from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re, html

ROOT = Path(__file__).parent
OUT = ROOT / 'output' / 'santorini网站13页面截图.pdf'
OUT.parent.mkdir(exist_ok=True)
TMP = ROOT / 'tmp' / 'pdfs' / 'santorini_preview'
TMP.mkdir(parents=True, exist_ok=True)

pages = [
    ('01-首页', 'index', '/'), ('02-活动', 'activities', '/activities/'),
    ('03-博物馆', 'allmuseums', '/allmuseums/'), ('04-建筑艺术文化', 'architecture-art-culture', '/architecture-art-culture/'),
    ('05-海滩', 'beaches', '/beaches/'), ('06-联系我们', 'contact', '/contact/'),
    ('07-体验', 'experiences', '/experiences/'), ('08-美食', 'gastronomy', '/gastronomy/'),
    ('09-历史', 'history', '/history/'), ('10-如何到达', 'how-to-get-here', '/how-to-get-here/'),
    ('11-锡拉夏岛', 'thirassia', '/thirassia/'), ('12-火山', 'volcano', '/volcano/'),
    ('13-葡萄酒', 'wines', '/wines/'),
]

font_paths = ['/System/Library/Fonts/Supplemental/Arial Unicode.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf']
font_path = next((p for p in font_paths if Path(p).exists()), '/System/Library/Fonts/Helvetica.ttc')
def font(size):
    try: return ImageFont.truetype(font_path, size)
    except: return ImageFont.load_default()

def extract(slug):
    f = ROOT / ('index.html' if slug == 'index' else Path(slug) / 'index.html')
    if not f.exists(): f = ROOT / f'{slug}.html'
    s = f.read_text(errors='ignore')
    title = re.search(r'<title[^>]*>(.*?)</title>', s, re.I|re.S)
    title = html.unescape(re.sub(r'<.*?>','', title.group(1))).strip() if title else slug
    text = html.unescape(re.sub(r'<script.*?</script>|<style.*?</style>', ' ', s, flags=re.I|re.S))
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    imgs = re.findall(r'(?:src|data-src)=["\']([^"\']+)', s, re.I)
    image = None
    for src in imgs:
        src = src.split('?')[0]
        if src.startswith('/'):
            p = ROOT / src.lstrip('/')
        elif src.startswith('http'):
            continue
        else:
            p = f.parent / src
        if p.exists() and p.suffix.lower() in {'.jpg','.jpeg','.png','.webp'}:
            try:
                with Image.open(p) as probe:
                    if probe.width >= 500 and probe.height >= 250:
                        image = p; break
            except Exception:
                pass
    return title, text[:540], image

W,H = 1200, 1700
made=[]
for label, slug, route in pages:
    im = Image.new('RGB', (W,H), '#f3f0e9')
    d = ImageDraw.Draw(im)
    title, excerpt, hero = extract(slug)
    d.rectangle((0,0,W,86), fill='#123d46')
    d.text((54,28), 'SANTORINI · WEBSITE CAPTURE', font=font(28), fill='#f6eee1')
    if hero:
        try:
            hi = Image.open(hero).convert('RGB')
            hi.thumbnail((W-108, 700))
            x=(W-hi.width)//2; y=120
            d.rounded_rectangle((44,108,W-44,850), radius=18, fill='#ddd6c7')
            im.paste(hi,(x,y))
        except Exception: pass
    d.text((54, 920), label, font=font(54), fill='#123d46')
    d.text((54, 995), title[:72], font=font(30), fill='#555047')
    d.line((54,1058,W-54,1058), fill='#c7bca9', width=2)
    d.text((54,1085), f'https://jia944855-crypto.github.io{route}', font=font(25), fill='#2f7180')
    # simple wrapped summary
    words = re.sub(r'\s+', ' ', excerpt)
    lines=[]; line=''
    for ch in words:
        if len(line) >= 42 and ch in ' ，。,.!?！？;；':
            lines.append(line); line=''
        else: line += ch
    if line: lines.append(line)
    y=1155
    d.text((54,y), '页面内容摘要', font=font(30), fill='#123d46'); y+=55
    for line in lines[:8]:
        d.text((54,y), line, font=font(24), fill='#514c45'); y+=37
    d.text((54,H-72), f'{label}  ·  Page {len(made)+1} / 13', font=font(22), fill='#82786c')
    p=TMP/f'{len(made)+1:02d}.png'; im.save(p); made.append(im)

made[0].save(OUT, save_all=True, append_images=made[1:], resolution=96.0)
print(OUT)
