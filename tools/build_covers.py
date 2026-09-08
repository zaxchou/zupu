# -*- coding: utf-8 -*-
"""四语言封面：docs/_cover{,en,ja,zh-Hant}-v4.html → docs/cover{,en,ja,zh-Hant}.jpg
（1920×960 JPEG，Playwright 渲染）。

版本发布时只改下面 VERSION / OLD_VERSION / OLD_TAGS，脚本幂等写入四张模板再渲染。
模板里的界面截图引用 docs/preview-tree*.png（由 tests/_out/_shot_readme.py 生成）。
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VERSION = 'v15.36'
OLD_VERSION = 'v15.35'
SUFFIXES = {'': '-v4', '-en': '-en-v4', '-ja': '-ja-v4', '-zh-Hant': '-zh-Hant-v4'}
OLD_TAGS = {'': '51 测试用例', '-en': '51 tests', '-ja': '51 テスト', '-zh-Hant': '51 測試用例'}
NEW_TAGS = {'': '52 测试用例', '-en': '52 tests', '-ja': '52 テスト', '-zh-Hant': '52 測試用例'}


def update_template(suffix):
    src = os.path.join(ROOT, 'docs', '_cover%s.html' % SUFFIXES[suffix])
    s = io.open(src, encoding='utf-8').read()
    if '>%s<' % VERSION in s:
        print('_cover%sv4.html 已是 %s' % (suffix, VERSION))
        return True
    if s.count('>%s<' % OLD_VERSION) != 1:
        print('_cover%sv4.html 找不到 %s，请检查版本常量' % (suffix, OLD_VERSION))
        return False
    s = s.replace('>%s<' % OLD_VERSION, '>%s<' % VERSION)
    old_tag = OLD_TAGS[suffix]
    if s.count(old_tag) != 1:
        print('_cover%sv4.html 找不到用例数标记 %r' % (suffix, old_tag))
        return False
    s = s.replace(old_tag, NEW_TAGS[suffix])
    io.open(src, 'w', encoding='utf-8', newline='').write(s)
    print('_cover%sv4.html -> %s / %s' % (suffix, VERSION, NEW_TAGS[suffix]))
    return True


def render(suffix):
    from playwright.sync_api import sync_playwright
    html = os.path.join(ROOT, 'docs', '_cover%s.html' % SUFFIXES[suffix])
    out = os.path.join(ROOT, 'docs', 'cover%s.jpg' % suffix)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1280, 'height': 640}, device_scale_factor=1.5)
        pg.goto('file:///' + html.replace('\\', '/'))
        pg.wait_for_timeout(400)
        pg.screenshot(path=out, type='jpeg', quality=88)
        b.close()
    print('cover%s.jpg OK (%d bytes)' % (suffix, os.path.getsize(out)))


if __name__ == '__main__':
    ok = all(update_template(sfx) for sfx in ['', '-en', '-ja', '-zh-Hant'])
    if ok or '--force-render' in sys.argv:
        for sfx in ['', '-en', '-ja', '-zh-Hant']:
            render(sfx)
    sys.exit(0 if ok else 1)
