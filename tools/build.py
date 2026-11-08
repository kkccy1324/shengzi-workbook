"""Assemble the website and the single-file offline version from src/.

Run from the repo root:  python3 tools/build.py
Outputs:
  docs/index.html          GitHub Pages site (installable, works offline after first visit)
  docs/sw.js               service worker that caches every file listed below
  docs/shengzi-offline.zip single HTML file for computers, no network needed
"""
import base64, hashlib, json, os, re, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
SRC = os.path.join(ROOT, 'src', 'shengzi.html')
FONT_CSS = os.path.join(ROOT, 'src', 'zhuyin-font.css')
JSPDF = 'vendor/jspdf.umd.min.js'
JSPDF_CDN = '<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>'
SHARDS = 200
DICT_ZIP = 'data/dict_mini_2019_20260929.zip'

HEAD = '''<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
{title}
{extra}<style>:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0;font:14px system-ui,sans-serif}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
<style>
{font}</style>
</head>
<body>
'''

PWA_HEAD = '''<meta name="theme-color" content="#2c6a52">
<meta name="description" content="輸入生字即自動校對注音並標出教育部標準筆順，產生田字格生字練習簿，可下載 PDF 列印。">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="生字練習簿">
'''

PWA_SCRIPT = '''<script>
(function () {
  var msg = document.getElementById('offline-msg');
  if (!('serviceWorker' in navigator) || !msg) return;
  msg.hidden = false;
  msg.textContent = '正在下載離線資料（約 17 MB），完成前請保持連線…';
  navigator.serviceWorker.register('sw.js').catch(function () {
    msg.textContent = '這個瀏覽器無法啟用離線使用，連網時仍可正常使用。';
  });
  navigator.serviceWorker.ready.then(function () {
    msg.textContent = '已可離線使用。iPhone 請用 Safari 的「分享 → 加入主畫面」，之後從主畫面開啟。';
  });
  // A new version took over while this (old) page is open: offer a reload instead of waiting for a second restart.
  var hadController = !!navigator.serviceWorker.controller;
  navigator.serviceWorker.addEventListener('controllerchange', function () {
    if (!hadController) return;
    var n = document.getElementById('notice'), b = document.createElement('button');
    b.type = 'button';
    b.className = 'btn-line';
    b.textContent = '更新';
    b.onclick = function () { location.reload(); };
    n.className = 'notice';
    n.replaceChildren('有新版本可以使用，點「更新」換成新版（不會清除你輸入的生字）。 ', b);
    n.hidden = false;
  });
})();
</script>
'''

SW = '''const CACHE = 'shengzi-%(version)s';
const FILES = %(files)s;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.match(e.request, { ignoreSearch: true }).then(hit => hit || fetch(e.request)));
});
'''


def split_source():
    src = open(SRC, encoding='utf-8').read()
    head, body = src.split('<style>', 1)
    title = re.search(r'<title>.*?</title>', head).group(0)
    assert JSPDF_CDN in body
    return title, '<style>' + body


def read(path):
    return open(os.path.join(DOCS, path), encoding='utf-8').read()


def write(path, text):
    open(os.path.join(DOCS, path), 'w', encoding='utf-8').write(text)


def build_site(title, body, font):
    body = body.replace(JSPDF_CDN, f'<script src="{JSPDF}"></script>')
    write('index.html', HEAD.format(title=title, extra=PWA_HEAD, font=font) + body + PWA_SCRIPT + '</body>\n</html>\n')

    files = ['./', 'index.html', 'manifest.webmanifest', JSPDF, DICT_ZIP,
             'icons/icon-192.png', 'icons/icon-512.png', 'icons/apple-touch-icon.png']
    files += [f'strokes/s{i}.json' for i in range(SHARDS)]
    digest = hashlib.sha256()
    for f in files[1:]:
        digest.update(open(os.path.join(DOCS, f), 'rb').read())
    write('sw.js', SW % {'version': digest.hexdigest()[:12], 'files': json.dumps(files)})


def build_offline(title, body, font):
    def data_tag(id_, text):
        return '<script type="application/json" id="%s">%s</script>' % (id_, text.replace('</', '<\\/'))

    zip_b64 = base64.b64encode(open(os.path.join(DOCS, DICT_ZIP), 'rb').read()).decode()
    data = ['<script type="application/octet-stream" id="data-dict-zip">%s</script>' % zip_b64]
    data += [data_tag(f'data-s{i}', read(f'strokes/s{i}.json')) for i in range(SHARDS)]
    jspdf = read(JSPDF).replace('</script', '<\\/script')
    body = body.replace(JSPDF_CDN, '\n'.join(data) + '\n<script>' + jspdf + '</script>')
    html = HEAD.format(title=title, extra='', font=font) + body + '</body>\n</html>\n'
    with zipfile.ZipFile(os.path.join(DOCS, 'shengzi-offline.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        # Fixed timestamp so the same source always builds the same zip (CI checks docs/ is up to date)
        info = zipfile.ZipInfo('生字練習簿產生器-離線版.html', date_time=(2026, 1, 1, 0, 0, 0))
        z.writestr(info, html, compress_type=zipfile.ZIP_DEFLATED)


if __name__ == '__main__':
    title, body = split_source()
    font = open(FONT_CSS, encoding='utf-8').read()
    build_site(title, body, font)
    build_offline(title, body, font)
    print('built docs/index.html, docs/sw.js, docs/shengzi-offline.zip')
