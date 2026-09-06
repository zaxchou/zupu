# -*- coding: utf-8 -*-
"""把 index.html 打包成小红书小工具离线 zip。

规范来源：~/.agents/skills/minitool-zip-builder（SKILL.md + references）。
要点：
- 容器 CSP 禁止内联 <script>：把唯一可执行脚本提取为 ./app.js
- 种子 JSON 从 <script type="application/json"> 转成 app.js 顶部的 window.__SEED_JSON
- viewport 追加 maximum-scale=1.0, user-scalable=no（禁捏合页面缩放，应用自带缩放）
- index.html 必须在 zip 根目录
"""
import io
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
DIST = os.path.join(ROOT, 'dist-xhs')
OUT_ZIP = os.path.join(DIST, 'zupu-minitool.zip')


def main():
    s = io.open(SRC, encoding='utf-8').read()

    # 1) 提取种子 JSON（type="application/json" 的数据块）
    m = re.search(r'<script id="__treeData" type="application/json">([\s\S]*?)</script>', s)
    assert m, '种子 JSON 块未找到'
    seed = json.loads(m.group(1))
    s = s.replace(m.group(0), '', 1)

    # 2) 提取可执行脚本 → app.js（源码只有一个无 type 的内联 script）
    m = re.search(r'<script>\n?([\s\S]*?)</script>', s)
    assert m, '可执行脚本未找到'
    app_js = m.group(1)
    assert 'import ' not in app_js[:200] and 'export ' not in app_js[:200]
    s = s.replace(m.group(0), '<script src="./app.js"></script>', 1)
    app_js = 'window.__SEED_JSON = ' + json.dumps(seed, ensure_ascii=False) + ';\n' + app_js

    # 3) viewport：禁页面缩放（应用内部自带缩放）
    s = s.replace(
        'width=device-width, initial-scale=1.0, viewport-fit=cover',
        'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover', 1)

    # 4) 合规扫描（命中即失败）
    banned = [
        ('fetch(', '网络请求'), ('XMLHttpRequest', '网络请求'),
        ('window.prompt(', '被禁弹窗'), ('window.open(', '弹新窗口'),
        ('eval(', '动态执行'), ('new Function(', '动态执行'),
        ('onclick=', '行内事件'), ('type="module"', '模块脚本'),
        ('navigator.clipboard', '剪贴板'), ('serviceWorker', '后台运行'),
        ('<iframe', 'iframe'), ('<base ', 'base'),
        ('requestFullscreen', '全屏'), ('WebAssembly', 'WASM'),
    ]
    errs = []
    for pat, why in banned:
        if pat in s or pat in app_js:
            errs.append('%s 命中：%s' % (why, pat))
    if re.search(r'https?://(?!www\.w3\.org)', s + app_js):
        hits = re.findall(r'https?://[^\s"\')<>]+', s + app_js)
        errs.append('外部 URL：' + ' | '.join(hits[:5]))
    if errs:
        print('== 合规扫描失败 ==')
        for e in errs:
            print('  ERROR', e)
        sys.exit(1)
    print('合规扫描：通过（无违禁 API / 行内事件 / 外部资源）')

    # 5) 写 dist
    os.makedirs(DIST, exist_ok=True)
    io.open(os.path.join(DIST, 'index.html'), 'w', encoding='utf-8', newline='').write(s)
    io.open(os.path.join(DIST, 'app.js'), 'w', encoding='utf-8', newline='').write(app_js)

    # 6) 打 zip（index.html 必须在根；压缩目录内容而非目录本身）
    if os.path.exists(OUT_ZIP):
        os.remove(OUT_ZIP)
    with zipfile.ZipFile(OUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(DIST, 'index.html'), 'index.html')
        z.write(os.path.join(DIST, 'app.js'), 'app.js')

    print('产物：' + OUT_ZIP)
    print('  index.html %.1f KB' % (os.path.getsize(os.path.join(DIST, 'index.html')) / 1024))
    print('  app.js     %.1f KB' % (os.path.getsize(os.path.join(DIST, 'app.js')) / 1024))
    print('  zip        %.1f KB' % (os.path.getsize(OUT_ZIP) / 1024))


if __name__ == '__main__':
    main()
