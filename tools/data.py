"""Regenerate the data files the page reads.

Run from the repo root:  python3 tools/data.py
Needs: openpyxl, fonttools, brotli, and npm (to fetch the stroke and font packages).

Outputs:
  docs/strokes/s*.json    stroke outlines from g0v zh-stroke-data, sharded by code point,
                          for the characters in 教育部《國語小字典》 (docs/data/)
  src/zhuyin-font.css     LXGW WenKai TC subset for bopomofo and fixed header text
"""
import base64, glob, io, json, os, re, subprocess, tarfile, tempfile, zipfile

import openpyxl
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT_ZIP = os.path.join(ROOT, 'docs', 'data', 'dict_mini_2019_20260929.zip')
STROKE_PKG = 'zh-stroke-data@0.0.75'
FONT_PKG = 'lxgw-wenkai-tc-webfont@1.2.0'
SHARDS = 200
FONT_TEXT = '姓名日期家長簽名第頁國語生字練習產生器0123456789/ '


def dict_chars():
    with zipfile.ZipFile(DICT_ZIP) as z:
        name = next(n for n in z.namelist() if n.endswith('.xlsx'))
        ws = openpyxl.load_workbook(io.BytesIO(z.read(name)), read_only=True).worksheets[0]
        return {row[0] for row in ws.iter_rows(min_row=2, max_col=1, values_only=True) if row[0]}


def npm_pack(pkg, tmp):
    dest = os.path.join(tmp, pkg.replace('@', '_').replace('/', '_'))
    os.makedirs(dest)
    subprocess.run(['npm', 'pack', pkg, '--silent', '--pack-destination', dest], check=True, stdout=subprocess.DEVNULL)
    return glob.glob(os.path.join(dest, '*.tgz'))[0]


def build_strokes(chars, tmp):
    tgz = npm_pack(STROKE_PKG, tmp)
    shards = [{} for _ in range(SHARDS)]
    q = lambda v: str(round(v / 2))
    pt = lambda p: q(p['x']) + ' ' + q(p['y'])
    with tarfile.open(tgz) as tar:
        for m in tar:
            hit = re.fullmatch(r'package/json/([0-9a-f]+)\.json', m.name)
            if not hit or chr(int(hit.group(1), 16)) not in chars:
                continue
            strokes = []
            for s in json.load(tar.extractfile(m)):
                d = []
                for p in s['outline']:
                    t = p['type']
                    if t in 'ML':
                        d.append(t + pt(p))
                    elif t == 'Q':
                        d.append('Q' + pt(p['begin']) + ' ' + pt(p['end']))
                    elif t == 'C':
                        d.append('C' + pt(p['begin']) + ' ' + pt(p['mid']) + ' ' + pt(p['end']))
                start = s['track'][0]
                strokes.append([''.join(d) + 'Z', round(start['x'] / 2), round(start['y'] / 2)])
            cp = int(hit.group(1), 16)
            shards[cp % SHARDS][chr(cp)] = strokes
    out = os.path.join(ROOT, 'docs', 'strokes')
    os.makedirs(out, exist_ok=True)
    for i, sh in enumerate(shards):
        json.dump(sh, open(os.path.join(out, f's{i}.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('strokes:', sum(map(len, shards)), 'chars')


def build_font(tmp):
    tgz = npm_pack(FONT_PKG, tmp)
    need = set(range(0x3105, 0x312A)) | {0x2C7, 0x2CA, 0x2CB, 0x2D9} | set(map(ord, FONT_TEXT))
    faces = []
    with tarfile.open(tgz) as tar:
        for m in tar:
            if not re.fullmatch(r'package/files/lxgwwenkaitc-regular-subset-\d+\.woff2', m.name):
                continue
            font = TTFont(io.BytesIO(tar.extractfile(m).read()))
            have = set(font.getBestCmap()) & need
            if not have:
                continue
            opts = subset.Options()
            opts.flavor = 'woff2'
            sub = subset.Subsetter(opts)
            sub.populate(unicodes=have)
            sub.subset(font)
            buf = io.BytesIO()
            font.save(buf)
            faces.append('@font-face{font-family:"LXGW WenKai TC";font-weight:400;src:url(data:font/woff2;base64,%s) format("woff2");unicode-range:%s}'
                         % (base64.b64encode(buf.getvalue()).decode(), ','.join('U+%x' % c for c in sorted(have))))
    open(os.path.join(ROOT, 'src', 'zhuyin-font.css'), 'w', encoding='utf-8').write('\n'.join(faces) + '\n')
    print('font faces:', len(faces))


if __name__ == '__main__':
    import logging
    logging.getLogger('fontTools').setLevel(logging.ERROR)
    with tempfile.TemporaryDirectory() as tmp:
        chars = dict_chars()
        build_strokes(chars, tmp)
        build_font(tmp)
