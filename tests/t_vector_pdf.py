# -*- coding: utf-8 -*-
"""实际下载的矢量 PDF 回归：文字/字体/边界、超大单页、局部高倍渲染与失败恢复。
只渲染 <=900px 缩略预览和 <=80pt 的 1000% 局部，不分配整张巨幅位图。
"""
from helper import *
from pathlib import Path
import base64
import io
import re

import fitz
from PIL import Image


# 不导入其他 t_* 模块，避免 helper.RUNNERS 被它们的装饰器污染。
def members(tree, visible=False):
    yield tree
    if not visible or tree.get("expanded", True):
        for child in tree.get("children", []):
            yield from members(child, visible)


def synthetic_tree(total):
    root = {"id": "root", "name": "矢量族谱", "expanded": True,
            "spouses": [], "children": []}
    queue = [root]
    for i in range(1, total):
        node = {"id": "v%d" % i, "name": "成员%04d" % i,
                "spouses": [], "expanded": True, "children": []}
        queue[(i - 1) // 3]["children"].append(node)
        queue.append(node)
    return root


def install_tree(page, tree):
    page.evaluate("""tree => {
      treeData=tree; cfg.showSurname=true; cfg.showPhotos=true;
      cfg.direction='down'; cfg.vertical=false; render(); fitToScreen();
    }""", tree)


def open_pdf_menu(page):
    page.locator('#btnFile').click()
    page.locator('#__ctxMenu .mi', has_text='导出 PDF').click()
    page.locator('#__pdfModal').wait_for(state='visible')


def save_pdf(page, name, mode=None, direct=False):
    if not direct:
        open_pdf_menu(page)
        if mode is not None:
            page.locator('input[name="pdfMode"][value="%s"]' % mode).check()
    with page.expect_download(timeout=90000) as dl:
        if direct:
            # 缺省参数必须与 UI 的默认 vector 保持一致。
            page.evaluate('() => exportPdfAs()')
        else:
            page.locator('#__pdfGo').click()
    path = Path(LOCAL_OUT) / name
    dl.value.save_as(str(path))
    check(path.read_bytes().startswith(b'%PDF-'), '下载文件为 PDF', str(path))
    page.wait_for_function("() => !document.getElementById('__exportBusy')")
    return path


def all_chars(pdf_page):
    raw = pdf_page.get_text('rawdict', clip=fitz.INFINITE_RECT())
    return [char for block in raw['blocks'] if block['type'] == 0
            for line in block['lines'] for span in line['spans']
            for char in span['chars'] if not char['c'].isspace()]


def assert_vector(path, names, images=0, render=False):
    raw = path.read_bytes()
    check(b'/FontFile2' in raw and b'/ToUnicode' in raw,
          'TrueType 字体与 ToUnicode 均存在')
    with fitz.open(str(path)) as doc:
        check(len(doc) == 1, '矢量导出始终单页', 'pages=%d' % len(doc))
        p = doc[0]
        check(0 < min(p.rect.width, p.rect.height) and max(p.rect.width, p.rect.height) <= 14400,
              '页面长边不超过 14400pt', str(p.rect))
        text = ''.join(p.get_text().split())
        missing = [name for name in names if ''.join(name.split()) not in text]
        check(not missing, '所有可见成员姓名均可提取',
              'missing=%d: %s' % (len(missing), missing[:8]))
        chars = all_chars(p)
        outside = [(c['c'], c['bbox']) for c in chars
                   if not (p.rect + (-.1, -.1, .1, .1)).contains(fitz.Rect(c['bbox']))]
        check(chars and not outside, '所有实际文字 bbox 均在页内',
              'outside=%d: %s' % (len(outside), outside[:5]))
        fonts = p.get_fonts(full=True)
        check(fonts and all(doc.extract_font(f[0])[3] for f in fonts),
              '每个实际引用字体均有嵌入字体数据', str(fonts[:3]))
        info = p.get_image_info()
        check(len(info) == images, '无照片时 0 images，照片只嵌入局部图',
              'images=%d expected=%d' % (len(info), images))
        full_images = [im['bbox'] for im in info
                       if fitz.Rect(im['bbox']).get_area() > p.rect.get_area() * .8]
        check(not full_images, '不含覆盖整页的图像', str(full_images))
        if render:
            # 缩略图总像素不超过 900²；1000% 仅放大含文字的小区域。
            s = min(1, 900 / max(p.rect.width, p.rect.height))
            thumb = p.get_pixmap(matrix=fitz.Matrix(s, s), alpha=False)
            check(thumb.width <= 901 and thumb.height <= 901 and min(thumb.samples) < 240,
                  '缩略预览可渲染且有可见内容')
            thumb.save(str(path.with_suffix('.preview.png')))
            c = next((c for c in chars if c['c'] == '成'),
                     next(c for c in chars if c['c'] in '矢量族谱'))
            box = fitz.Rect(c['bbox'])
            clip = fitz.Rect(box.x0 - 3, box.y0 - 3,
                             min(box.x1 + 30, box.x0 + 80),
                             min(box.y1 + 10, box.y0 + 80)) & p.rect
            zoom = p.get_pixmap(matrix=fitz.Matrix(10, 10), clip=clip, alpha=False)
            check(0 < zoom.width <= 802 and 0 < zoom.height <= 802,
                  '1000% 局部渲染受控', '%dx%d' % (zoom.width, zoom.height))
            check(min(zoom.samples) < 160 and max(zoom.samples) > 240,
                  '1000% 文字局部有墨色和背景')
            zoom.save(str(path.with_suffix('.zoom1000.png')))
    return text


@testcase
def t_pdf_modal_default_cancel_and_force_paged(b):
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        goto(page)
        downloads = []
        page.on('download', lambda d: downloads.append(d.suggested_filename))
        before = page.evaluate('() => JSON.stringify(sanitize(treeData))')
        open_pdf_menu(page)
        check(page.locator('input[name="pdfMode"][value="vector"]').is_checked(),
              '文件菜单默认选 vector')
        check(not downloads, '确认之前不下载')
        page.locator('#__pdfCancel').click()
        check(not page.locator('#__pdfModal').is_visible() and not downloads,
              '取消关闭弹窗且不生成文件')
        path = save_pdf(page, 'vector_small_forced_paged.pdf', mode='paged')
        with fitz.open(str(path)) as doc:
            check(all(abs(p.rect.width - 842) < .01 and abs(p.rect.height - 595) < .01
                      for p in doc), '小谱也能强制 A4 横向分页')
            check(doc[0].get_images(), 'paged 仍使用分页页图')
        open_pdf_menu(page)
        check(page.locator('input[name="pdfMode"][value="vector"]').is_checked(),
              '再次打开仍默认 vector')
        page.locator('#__pdfCancel').click()
        check(page.evaluate('() => JSON.stringify(sanitize(treeData))') == before,
              '模式选择不修改族谱')
        check(not errs, '无 JS 错误', str(errs))
    finally:
        ctx.close()


def large_single_page(b, total, direct=False):
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        goto(page)
        tree = synthetic_tree(total)
        install_tree(page, tree)
        check(page.locator('.node').count() == total, '夹具成员数准确', str(total))
        path = save_pdf(page, 'vector_%d.pdf' % total, mode=None if direct else 'vector', direct=direct)
        assert_vector(path, [n['name'] for n in members(tree)], render=True)
        check(not errs, '大谱导出无 JS 错误', str(errs))
    finally:
        ctx.close()


@testcase
def t_vector_130_people_single_page(b):
    large_single_page(b, 130)


@testcase
def t_vector_364_people_default_api_single_page(b):
    large_single_page(b, 364, direct=True)


@testcase
def t_vector_800_people_single_page(b):
    large_single_page(b, 800)


@testcase
def t_vector_four_directions_and_vertical_text_bounds(b):
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        goto(page)
        names = [n['name'] for n in members(SAMPLE_DATA)]
        for vertical in [False, True]:
            for direction in ['down', 'up', 'right', 'left']:
                page.evaluate("""([d,v]) => {
                  cfg.direction=d;cfg.vertical=v;render();fitToScreen();
                }""", [direction, vertical])
                path = save_pdf(page, 'vector_%s_%s.pdf' % (direction, vertical))
                assert_vector(path, names)
        check(not errs, '四方向与竖排无 JS 错误', str(errs))
    finally:
        ctx.close()


@testcase
def t_vector_default_font_28ee7_searchable(b):
    """网友真实姓名缺字回归：默认离线字体必须包含 U+28EE7，不靠替换文字或位图。"""
    from fontTools.ttLib import TTFont
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        goto(page)
        tree = {"id": "root", "name": "生僻字族谱", "spouses": [], "expanded": True,
                "children": [{"id": "rare", "name": "周\U00028ee7", "spouses": ["李氏"],
                              "note": "姓名含\U00028ee7，按原字记录", "expanded": True, "children": []}]}
        install_tree(page, tree)
        path = save_pdf(page, 'rare_28ee7.pdf', mode='vector')
        assert_vector(path, ['周\U00028ee7', '李氏'])
        with fitz.open(path) as doc:
            text = ''.join(doc[0].get_text().split())
            check('周\U00028ee7' in text, '默认字体的生僻姓名可完整搜索/复制', text[:80])
            rare_fonts = []
            for font_info in doc[0].get_fonts():
                embedded = doc.extract_font(font_info[0])[3]
                font = TTFont(io.BytesIO(embedded))
                cmap = font.getBestCmap()
                if 0x28ee7 in cmap:
                    rare_fonts.append((font, cmap[0x28ee7]))
            check(rare_fonts, '至少一个 PDF 内嵌子集确有 U+28EE7 字形')
            font, glyph_name = rare_fonts[0]
            glyph = font['glyf'][glyph_name]
            check(glyph.numberOfContours != 0, '生僻字使用真实轮廓而非空白占位')
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
            check(min(pix.samples) < 160, '含生僻姓名的 PDF 可渲染')
        check(not errs, '生僻姓名导出无 JS 错误', str(errs))
    finally:
        ctx.close()


@testcase
def t_vector_default_font_28ee7_vertical_and_branch(b):
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        goto(page)
        tree = {"id": "root", "name": "生僻字族谱", "spouses": [], "expanded": True,
                "children": [{"id": "rare", "name": "周\U00028ee7", "spouses": [], "expanded": True,
                              "children": [{"id": "kid", "name": "周明", "spouses": [], "children": []}]}]}
        install_tree(page, tree)
        page.evaluate('() => {cfg.vertical=true;render()}')
        path = save_pdf(page, 'rare_28ee7_vertical.pdf', mode='vector')
        with fitz.open(path) as doc:
            check('\U00028ee7' in doc[0].get_text(), '竖排按 Unicode 码点保留 U+28EE7')
        page.locator('.node[data-id="rare"]').click(button='right')
        page.locator('#__ctxMenu .mi', has_text='导出此支').click()
        page.locator('#__subtreePdf').click()
        with page.expect_download(timeout=90000) as dl:
            page.locator('#__pdfGo').click()
        out = Path(LOCAL_OUT) / 'rare_28ee7_branch.pdf'
        dl.value.save_as(str(out))
        with fitz.open(out) as doc:
            check('\U00028ee7' in doc[0].get_text(), '分支导出保留 U+28EE7')
        check(not errs, '竖排/分支生僻姓名导出无 JS 错误', str(errs))
    finally:
        ctx.close()


@testcase
def t_vector_custom_rare_only_font_keeps_common_names(b):
    """只含扩展字的本机 TTF 不能替掉常用字：用户字体优先，缺的常用汉字自动后备。"""
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        goto(page)
        tree = {"id": "root", "name": "生僻字族谱", "spouses": [], "expanded": True,
                "children": [{"id": "rare", "name": "周\U00028ee7", "spouses": ["李氏"],
                              "expanded": True, "children": []}]}
        install_tree(page, tree)
        open_pdf_menu(page)
        page.locator('#__pdfModal details').evaluate('(el) => {el.open=true}')
        selected = Path(LOCAL_HTML).parent / 'third_party/zupu-rare-font/ZupuRareSupport.ttf'
        page.locator('#__pdfFont').set_input_files(str(selected))
        with page.expect_download(timeout=90000) as dl:
            page.locator('#__pdfGo').click()
        out = Path(LOCAL_OUT) / 'custom_rare_fallback.pdf'
        dl.value.save_as(str(out))
        assert_vector(out, ['周\U00028ee7', '李氏'])
        with fitz.open(out) as doc:
            check(len(doc[0].get_fonts()) == 2, '稀字字体与常用字字体分别嵌入，避免缺字')
            check(not doc.is_repaired, '多字体 PDF 结构有效，无修复打开')
        check(not errs, '生僻字字体补充时无 JS 错误', str(errs))
    finally:
        ctx.close()


@testcase
def t_vector_multiline_note_and_invisible_chars(b):
    """多行备注（应用续行格式）/零宽字符/emoji 变体选择符：画布把它们当空白或不可见，
    PDF 曾因 U+000A 无字形而整单失败。"""
    import json as _json
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        tree = {
            "id": "root", "name": "家族族谱", "spouses": [], "expanded": True,
            "children": [
                {"id": "a", "name": "周\u200b吉", "note": "生于明末\n迁居台湾", "spouses": [], "expanded": True, "children": []},
                {"id": "b", "name": "周心", "note": "热爱❤️家", "spouses": [], "expanded": True, "children": []},
            ],
        }
        app = open(LOCAL_HTML, encoding="utf-8").read()
        seed = _json.dumps(tree, ensure_ascii=False)
        fixture, n = re.subn(
            r'(<script id="__treeData" type="application/json">)[\s\S]*?(\n</script>)',
            lambda m: m.group(1) + "\n" + seed + "\n" + m.group(2), app, count=1)
        assert n == 1
        path = Path(LOCAL_OUT) / "fixture_multiline.html"
        path.write_text(fixture, encoding="utf-8")
        page.goto(OUT_DIR + "/fixture_multiline.html")
        page.wait_for_load_state("domcontentloaded")
        page.evaluate("() => { localStorage.clear(); }")
        page.reload()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(300)
        open_pdf_menu(page)
        with page.expect_download(timeout=90000) as dl:
            page.locator('#__pdfGo').click()
        out = Path(LOCAL_OUT) / "multiline.pdf"
        dl.value.save_as(str(out))
        text = "".join(fitz.open(out)[0].get_text().split())
        check("迁居台湾" in text and "生于明末" in text, "多行备注完整导出（不因换行缺字失败）", text[:120])
        check("周吉" in text, "名字中的零宽字符被剥掉", text[:120])
        check("热爱" in text and "家" in text, "emoji 变体选择符剥掉后正文保留", text[:120])
        check(not errs, "无 JS 错误", str(errs))
    finally:
        ctx.close()


@testcase
def t_vector_very_long_note_fast(b):
    """万字备注曾把 ellipText 卡成 O(n²)（实测 14 秒）：宽度可加后应单遍完成。"""
    import json as _json
    import time as _time
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        tree = {
            "id": "root", "name": "家族族谱", "spouses": [], "expanded": True,
            "children": [{"id": "a", "name": "周长注", "note": "备注内容测试" * 1250, "spouses": [], "expanded": True, "children": []}],
        }
        app = open(LOCAL_HTML, encoding="utf-8").read()
        seed = _json.dumps(tree, ensure_ascii=False)
        fixture, n = re.subn(
            r'(<script id="__treeData" type="application/json">)[\s\S]*?(\n</script>)',
            lambda m: m.group(1) + "\n" + seed + "\n" + m.group(2), app, count=1)
        assert n == 1
        path = Path(LOCAL_OUT) / "fixture_longnote.html"
        path.write_text(fixture, encoding="utf-8")
        page.goto(OUT_DIR + "/fixture_longnote.html")
        page.wait_for_load_state("domcontentloaded")
        page.evaluate("() => { localStorage.clear(); }")
        page.reload()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(300)
        open_pdf_menu(page)
        t0 = _time.time()
        with page.expect_download(timeout=120000) as dl:
            page.locator('#__pdfGo').click()
        took = _time.time() - t0
        out = Path(LOCAL_OUT) / "longnote.pdf"
        dl.value.save_as(str(out))
        check(took < 8, "万字备注导出不再卡死（<8s，旧实现 14s+）", "%.1fs" % took)
        text = "".join(fitz.open(out)[0].get_text().split())
        check("备注内容测试" in text, "长备注开头可见", text[:80])
        check(not errs, "无 JS 错误", str(errs))
    finally:
        ctx.close()


@testcase
def t_branch_export_returns_completion_promise(b):
    """v15.48 回归（强化版）：走真实 __pdfGo 流程，stub exportPdfAs 为挂起 Promise——
    导出期间遮罩与 _exportLock 必须保持、全局数据是临时子树；释放后遮罩撤掉、主树恢复。"""
    ctx, page, errs, _ = fresh_page(b)
    try:
        goto(page)
        page.locator('.node[data-id="b1"]').click(button='right')
        page.locator('#__ctxMenu .mi', has_text='导出此支').click()
        page.locator('#__subtreePdf').click()
        page.locator('#__pdfModal').wait_for(state='visible')
        page.evaluate("""() => {
          window.__realExportPdfAs = exportPdfAs;
          exportPdfAs = function(){ return new Promise(res => { window.__releaseExport = res; }); };
        }""")
        page.locator('input[name="pdfMode"][value="vector"]').check()
        page.locator('#__pdfGo').click()
        page.wait_for_timeout(250)
        during = page.evaluate("""() => ({
          busy: !!document.getElementById('__exportBusy'), lock: _exportLock, root: treeData.id })""")
        check(during == {'busy': True, 'lock': True, 'root': 'b1'},
              '导出期间遮罩/锁在，全局数据是临时子树', str(during))
        page.evaluate("() => window.__releaseExport()")
        page.wait_for_function("() => !document.getElementById('__exportBusy') && !_exportLock && treeData.id === 'root'")
        after = page.evaluate("() => ({ busy: !!document.getElementById('__exportBusy'), root: treeData.id })")
        check(after['busy'] is False and after['root'] == 'root', '释放后遮罩撤掉、主树恢复', str(after))
        check(not errs, '无 JS 错误', str(errs))
    finally:
        page.evaluate("() => { if (window.__realExportPdfAs) exportPdfAs = window.__realExportPdfAs; }")
        ctx.close()


@testcase
def t_vector_long_clan_title_not_clipped(b):
    """长谱名标题不得被 PDF 页边裁掉（旧实现把导出宽度封顶 560px）。"""
    import json as _json
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        tree = {
            "id": "root", "name": "家族族谱", "spouses": [], "expanded": True,
            "clan": {"ming": "潮阳泗水周氏大家族族谱重修总谱甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥"},
            "children": [{"id": "a", "name": "周勤", "spouses": [], "expanded": True, "children": []}],
        }
        app = open(LOCAL_HTML, encoding="utf-8").read()
        seed = _json.dumps(tree, ensure_ascii=False)
        fixture, n = re.subn(
            r'(<script id="__treeData" type="application/json">)[\s\S]*?(\n</script>)',
            lambda m: m.group(1) + "\n" + seed + "\n" + m.group(2), app, count=1)
        assert n == 1
        path = Path(LOCAL_OUT) / "fixture_long_title.html"
        path.write_text(fixture, encoding="utf-8")
        page.goto(OUT_DIR + "/fixture_long_title.html")
        page.wait_for_load_state("domcontentloaded")
        page.evaluate("() => { localStorage.clear(); }")
        page.reload()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(300)
        open_pdf_menu(page)
        with page.expect_download(timeout=90000) as dl:
            page.locator('#__pdfGo').click()
        out = Path(LOCAL_OUT) / "long_title.pdf"
        dl.value.save_as(str(out))
        doc = fitz.open(out)
        pg = doc[0]
        first = sorted(pg.get_text("words"), key=lambda w: w[1])[0]
        check(first[2] <= pg.rect.width - 4, "长谱名标题完整落在页内",
              "%s <= %s" % (first[2], pg.rect.width))
        check("潮阳泗水周氏大家族族谱" in "".join(pg.get_text().split()), "标题文字可提取")
        doc.close()
        check(not errs, "长标题导出无 JS 错误", str(errs))
    finally:
        ctx.close()


@testcase
def t_vector_branch_export_keeps_absolute_generations(b):
    """导出此支：字辈表挂在总根，子树必须补字辈表与原谱绝对代数；
    分支内没有名字锚点也不能从 1 代重新起算。"""
    import json as _json
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        tree = {
            "id": "root", "name": "家族族谱", "spouses": [], "expanded": True,
            "zibei": list("多士敬宏毓勤修昭厚德"),
            "children": [
                {"id": "a", "name": "周勤", "spouses": [], "expanded": True, "children": [
                    {"id": "a1", "name": "周修", "spouses": [], "expanded": True, "children": []}]},
                {"id": "b", "name": "周甲", "spouses": [], "expanded": True, "children": [
                    {"id": "b1", "name": "周乙", "spouses": [], "expanded": True, "children": []}]},
            ],
        }
        # 用真实的九层祖先构成第十世分支，不再借名字票选制造“第六代”。
        children = tree['children']
        for level in range(9, 0, -1):
            children = [{'id': 'ancestor%d' % level, 'name': '先祖%d' % level,
                         'spouses': [], 'expanded': True, 'children': children}]
        tree['children'] = children
        app = open(LOCAL_HTML, encoding="utf-8").read()
        seed = _json.dumps(tree, ensure_ascii=False)
        fixture, n = re.subn(
            r'(<script id="__treeData" type="application/json">)[\s\S]*?(\n</script>)',
            lambda m: m.group(1) + "\n" + seed + "\n" + m.group(2), app, count=1)
        assert n == 1
        path = Path(LOCAL_OUT) / "fixture_branch_gen.html"
        path.write_text(fixture, encoding="utf-8")
        page.goto(OUT_DIR + "/fixture_branch_gen.html")
        page.wait_for_load_state("domcontentloaded")
        page.evaluate("() => { localStorage.clear(); }")
        page.reload()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(300)
        page.evaluate('() => {cfg.zibeiStart=10;render();fitToScreen()}')
        page.locator('.node[data-id="b"]').click(button='right')
        page.locator('#__ctxMenu .mi', has_text='导出此支').click()
        page.locator('#__subtreePdf').click()
        with page.expect_download(timeout=90000) as dl:
            page.locator('#__pdfGo').click()
        out = Path(LOCAL_OUT) / "branch_gen.pdf"
        dl.value.save_as(str(out))
        text = "".join(fitz.open(out)[0].get_text().split())
        check("10世" in text, "分支根沿用原谱第十世，不按名字重编", text[:120])
        check("11世" in text, "分支子代沿用原谱第十一世", text[:120])
        check("辈序1·多" in text and "辈序2·士" in text, "第十世起字辈独立从第一字开始", text[:120])
        check(not errs, "分支世代导出无 JS 错误", str(errs))
    finally:
        ctx.close()


@testcase
def t_vector_fold_marker_and_circular_photo_crop(b):
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        goto(page)
        # 横宽照片：中央绿、两侧红/蓝。cover 裁剪后头像内应只见中央绿。
        page.evaluate("""() => {
          const cv=document.createElement('canvas');cv.width=120;cv.height=40;
          const c=cv.getContext('2d');
          ['#ef2020','#20c040','#2030ef'].forEach((color,i)=>{
            c.fillStyle=color;c.fillRect(i*40,0,40,40);
          });
          const n=findNode('b2');n.photoThumb=cv.toDataURL('image/png');n.photoRev=123;
          findNode('b1').expanded=false;render();
        }""")
        visible = page.evaluate("""() => {
          const out=[];(function walk(n){out.push(n.name);
            if(n.expanded)(n.children||[]).forEach(walk);})(treeData);return out;
        }""")
        hidden = [n['name'] for n in members(SAMPLE_DATA['children'][0])][1:]
        for vertical in [False, True]:
            page.evaluate('(v) => {cfg.vertical=v;render()}', vertical)
            geometry = page.evaluate("""() => {
              const d=exportDims();return {W:d.W,H:d.H+46,pad:(d.W-d.baseW)/2,
                photo:nodeRects.get('b2'),fold:nodeRects.get('b1')};
            }""")
            path = save_pdf(page, 'vector_fold_photo_%s.pdf' % vertical)
            text = assert_vector(path, visible, images=1)
            check(all(n not in text for n in hidden), '折叠后隐藏后代不出现在 PDF')
            with fitz.open(str(path)) as doc:
                p = doc[0]
                sx, sy = p.rect.width / geometry['W'], p.rect.height / geometry['H']
                r = geometry['photo']
                cx = r['x'] if vertical else r['x'] - r['w'] / 2 + 27
                cy = r['y'] + 19 if vertical else r['y'] + r['h'] / 2
                cx, cy, radius = (cx + geometry['pad']) * sx, (cy + 46) * sy, 14 * sx
                clip = fitz.Rect(cx - radius * 1.25, cy - radius * 1.25,
                                 cx + radius * 1.25, cy + radius * 1.25)
                pix = p.get_pixmap(matrix=fitz.Matrix(6, 6), clip=clip, alpha=False)
                image = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
                def sample(dx, dy):
                    x = round((cx + dx * radius) * 6 - pix.x)
                    y = round((cy + dy * radius) * 6 - pix.y)
                    return image.getpixel((x, y))
                green = lambda rgb: rgb[1] > rgb[0] + 60 and rgb[1] > rgb[2] + 50
                check(all(green(sample(dx, dy)) for dx, dy in [(0, 0), (-.65, 0), (.65, 0), (0, .65)]),
                      '宽照片中心 cover 裁剪，未压缩显示红蓝边')
                check(not green(sample(.9, .9)), '圆外角落未泄漏照片（裁剪有效）')
                f = geometry['fold']
                fold_box = fitz.Rect((f['x'] - f['w']/2 - 6 + geometry['pad']) * sx,
                                     (f['y'] + 46 - 25) * sy,
                                     (f['x'] + f['w']/2 + 6 + geometry['pad']) * sx,
                                     (f['y'] + 46 + f['h']) * sy)
                check('5' in p.get_textbox(fold_box), '折叠标记包含正确后代数 5')
        check(not errs, '折叠/照片无 JS 错误', str(errs))
    finally:
        ctx.close()


def ui_state(page):
    return page.evaluate("""() => JSON.stringify({
      data:sanitize(treeData),history:__ZP.historyLens(),store:{...localStorage},
      rects:Array.from(nodeRects),edges:edgeSegments,markers:rowMarkers,
      selected:selectedId,stage:document.getElementById('stage').outerHTML,
      config:cfg,camera:[scale,document.getElementById('viewport').scrollLeft,
                            document.getElementById('viewport').scrollTop]
    })""")


def open_branch_pdf(page):
    page.locator('.node[data-id="b1"]').click(button='right')
    page.locator('#__ctxMenu .mi', has_text='导出此支').click()
    page.locator('#__subtreePdf').click()
    page.locator('#__pdfModal').wait_for(state='visible')


@testcase
def t_vector_subtree_scope_cancel_and_state_isolation(b):
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        goto(page)
        page.evaluate("() => {findNode('b1').expanded=false;render()}")
        open_branch_pdf(page)
        before = ui_state(page)
        page.locator('#__pdfCancel').click()
        check(ui_state(page) == before, '取消分支 PDF 不改变布局/历史/存储/镜头')
        for mode in ['vector', 'paged']:
            open_branch_pdf(page)
            before = ui_state(page)
            page.locator('input[name="pdfMode"][value="%s"]' % mode).check()
            with page.expect_download(timeout=90000) as dl:
                page.locator('#__pdfGo').click()
            path = Path(LOCAL_OUT) / ('vector_subtree_%s.pdf' % mode)
            dl.value.save_as(str(path))
            page.wait_for_function("() => !document.getElementById('__exportBusy') && !_exportLock")
            check(ui_state(page) == before, '分支 %s 完整恢复主树状态' % mode)
            check('少秀' in dl.value.suggested_filename, '分支文件名包含成员名')
            if mode == 'vector':
                names = [n['name'] for n in members(SAMPLE_DATA['children'][0])]
                text = assert_vector(path, names)
                other = [n['name'] for branch in SAMPLE_DATA['children'][1:] for n in members(branch)]
                check(all(n not in text for n in other), '导出仅含此支，无兄弟支系成员')
        check(not errs, '分支导出无 JS 错误', str(errs))
    finally:
        ctx.close()


def ascii_font_base64():
    """生成只含 ASCII 的合法微型 TTF，用于验证用户字体缺字时后备常用汉字。"""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(['.notdef', 'space', 'A'])
    fb.setupCharacterMap({32: 'space', 65: 'A'})
    glyphs = {}
    for name in ['.notdef', 'space', 'A']:
        pen = TTGlyphPen(None)
        if name != 'space':
            pen.moveTo((80, 0));pen.lineTo((520, 0));pen.lineTo((300, 700));pen.closePath()
        glyphs[name] = pen.glyph()
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({name: (600, 0) for name in glyphs})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({'familyName': 'PDFTestASCII', 'styleName': 'Regular',
                       'uniqueFontIdentifier': 'PDFTestASCII-Regular',
                       'fullName': 'PDFTestASCII Regular', 'psName': 'PDFTestASCII-Regular'})
    fb.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    fb.setupPost();fb.setupMaxp()
    buf = io.BytesIO();fb.save(buf)
    return base64.b64encode(buf.getvalue()).decode('ascii')


def assert_failed_export_recovers(page, downloads, before, label):
    page.wait_for_function("""() => !document.getElementById('__exportBusy') && !_exportLock
      && /失败|缺|不支持|无法|字体|字形/.test(document.getElementById('__toast').textContent)""")
    toast = page.locator('#__toast').inner_text()
    check(not downloads, label + '不产生残缺下载', str(downloads))
    check(ui_state(page) == before, label + '不改变主树状态')
    page.locator('#btnFile').click()
    check(page.locator('#__ctxMenu').is_visible(), label + '菜单仍可操作')
    page.keyboard.press('Escape')
    return toast


@testcase
def t_vector_invalid_font_and_injected_missing_glyph_abort(b):
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        goto(page)
        downloads = []
        page.on('download', lambda d: downloads.append(d.suggested_filename))
        before = ui_state(page)
        for font, label in [('AAAA', '损坏字体')]:
            page.evaluate("() => document.getElementById('__toast').textContent=''")
            page.evaluate("font => exportPdfAs(undefined,'vector',font)", font)
            toast = assert_failed_export_recovers(page, downloads, before, label)
            check(re.search('失败|缺|不支持|字体|字形', toast), label + '有明确失败提示', toast)
        # 用户的合法字体缺字时应自动后备，不能把常用汉字也导成错误。
        with page.expect_download(timeout=90000) as dl:
            page.evaluate("font => exportPdfAs(undefined,'vector',font)", ascii_font_base64())
        out = Path(LOCAL_OUT) / 'custom_ascii_fallback.pdf'
        dl.value.save_as(str(out))
        assert_vector(out, [n['name'] for n in members(SAMPLE_DATA)])
        check(not errs, '字体失败已被 UI 处理，无未捕获 JS 异常', str(errs))
    finally:
        ctx.close()


@testcase
def t_vector_default_font_missing_character_no_partial_file(b):
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    try:
        goto(page)
        unsupported = chr(0x10FFFF)
        page.evaluate("name => {findNode('b2').name=name;render()}", '缺字' + unsupported)
        downloads = []
        page.on('download', lambda d: downloads.append(d.suggested_filename))
        before = ui_state(page)
        open_pdf_menu(page)
        page.locator('#__pdfGo').click()
        toast = assert_failed_export_recovers(page, downloads, before, '默认字体缺字')
        check(re.search('缺|字形|不支持|missing character|glyph', toast, re.I),
              '明确缺字而非静默漏字', toast)
        check(unsupported in toast or re.search(r'(?:U\+|0x)10FFFF', toast, re.I),
              '提示指出实际缺失字符或 Unicode 码点', toast)
        # 同一页面修正名字后能再次成功导出，证明没有残留锁或坏的任务状态。
        page.evaluate("() => {findNode('b2').name='少群';render()}")
        path = save_pdf(page, 'vector_recovered.pdf')
        assert_vector(path, [n['name'] for n in members(SAMPLE_DATA)])
        check(not errs, '缺字失败及重试无未捕获 JS 异常', str(errs))
    finally:
        ctx.close()


if __name__ == '__main__':
    import sys
    sys.exit(0 if run_module(globals(), 't_vector_pdf 矢量 PDF 实际文件回归') else 1)
