# -*- coding: utf-8 -*-
"""大族谱导出：显式选择 A4 分页 PDF、导出此支、PNG 上限回归。
页数断言用中小树 + __ZP.pagePlan 纯公式（不真渲 300 页）；PDF 实际渲染验证页图矩阵。"""
from helper import *
import os as _os
import re as _re
import json as _json
import math as _math
import struct as _struct
import shutil as _shutil
import time as _time

PDF_OUT = _os.path.join(LOCAL_OUT, "big_export.pdf")


def big_tree(target):
    """满三叉合成树到约 target 人（参考 tests/_out/_measure_big_export.py 的 big_tree）"""
    root = {"id": "root", "name": "家族族谱", "spouses": [], "expanded": True, "children": []}
    count = [0]
    gid = [0]

    def add(parent, depth, maxd):
        gid[0] += 1
        count[0] += 1
        n = {"id": "p%d" % gid[0], "name": "成员%d" % gid[0], "spouses": ["配%d" % gid[0]],
             "birth": str(1900 + gid[0] % 100), "expanded": True, "children": []}
        parent["children"].append(n)
        if depth < maxd:
            for _ in range(3):
                if count[0] >= target:
                    break
                add(n, depth + 1, maxd)

    while count[0] < target:
        add(root, 0, 6)
    return root, count[0]


def big_fixture_url(tree, name):
    """合成树 → 夹具页 URL（最新代码 + 指定种子数据，不碰用户主文件）"""
    app = open(LOCAL_HTML, encoding="utf-8").read()
    seed = _json.dumps(tree, ensure_ascii=False)
    out, n = _re.subn(r'(<script id="__treeData" type="application/json">)[\s\S]*?(\n</script>)',
                      lambda m: m.group(1) + "\n" + seed + "\n" + m.group(2), app, count=1)
    check(n == 1, "夹具：未找到内嵌 JSON 块")
    path = _os.path.join(LOCAL_OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    return OUT_DIR + "/" + name


def open_big(page, url):
    page.goto(url)
    page.wait_for_load_state("domcontentloaded")
    page.evaluate("() => { localStorage.clear(); }")
    page.reload()
    page.wait_for_load_state("domcontentloaded")


def export_via_file_menu(page, menu_text, out_path, mode="vector"):
    with page.expect_download(timeout=90000) as di:
        page.locator("#btnFile").click()
        page.locator('#__ctxMenu .mi', has_text=menu_text).click()
        if menu_text == "导出 PDF":
            check(page.locator('#__pdfModal').is_visible(), "PDF 模式弹窗出现")
            page.locator('input[name="pdfMode"][value="%s"]' % mode).check()
            page.locator('#__pdfGo').click()
    _shutil.copyfile(di.value.path(), out_path)
    return di.value.suggested_filename


def pdf_facts(raw):
    """从手写 PDF 提取 /Count、每页 MediaBox、头尾签名"""
    counts = [int(x) for x in _re.findall(rb"/Count (\d+)", raw)]
    boxes = _re.findall(rb"/MediaBox \[0 0 842 595\]", raw)
    return {"head": raw[:5], "tail": raw.strip()[-5:], "counts": counts, "boxes": len(boxes)}


def check_xref(raw, label):
    """xref 结构校验：条目数==/Size、每条偏移精确指向 '<n> 0 obj'、最高对象号==Size-1、
    startxref 指回 xref 表（末页 Image 不得缺条目）"""
    m_size = _re.search(rb"/Size (\d+)", raw)
    check(m_size is not None, label + "：/Size 存在")
    size = int(m_size.group(1))
    m_sx = _re.search(rb"startxref\n(\d+)\n%%EOF\s*$", raw)
    check(m_sx is not None, label + "：startxref 存在")
    xs = int(m_sx.group(1))
    check(raw[xs:xs + 4] == b"xref", label + "：startxref 指回 xref 表", str(raw[xs:xs + 8]))
    m_cnt = _re.match(rb"xref\n0 (\d+)\n", raw[xs:xs + 32])
    check(m_cnt is not None, label + "：xref 头格式")
    cnt = int(m_cnt.group(1))
    check(cnt == size, label + "：xref 条目数==/Size（末对象不缺条目）", "%d vs %d" % (cnt, size))
    sec = raw[xs:m_sx.start()]
    # 规范固定 20 字节条目，EOL 可为 " \n" / " \r" / "\r\n"；剥离行尾再断言
    entries = [e.rstrip(b" \r") for e in sec.split(b"\n")[2:2 + cnt]]
    check(all(e.endswith(b" n") or e.endswith(b" f") for e in entries),
          label + "：xref 条目格式", str(entries[:2]))
    check(entries[0] == b"0000000000 65535 f", label + "：对象 0 为 free 条目", str(entries[0]))
    bad = []
    for num in range(1, cnt):
        off = int(entries[num].split()[0])
        expect = ("%d 0 obj" % num).encode()
        if raw[off:off + len(expect)] != expect:
            bad.append((num, off, raw[off:off + 16]))
    check(not bad, label + "：所有 xref 偏移指向对应对象", str(bad[:5]))
    nums = [int(x) for x in _re.findall(rb"(\d+) 0 obj\r?\n", raw[:xs])]
    check(max(nums) == size - 1, label + "：最高对象号==Size-1", "%s vs %d" % (max(nums), size - 1))


@testcase
def t_small_pdf_still_single(b):
    """1. 小树 PDF 保持现状：单页（/Count 1），MediaBox 非分页 A4 规格"""
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto(page)
    fn = export_via_file_menu(page, "导出 PDF", PDF_OUT)
    check(_re.match(r"^家族族谱-图-\d{8}-\d{4}\.pdf$", fn), "文件名沿用 stampName", fn)
    raw = open(PDF_OUT, "rb").read()
    f = pdf_facts(raw)
    check(f["head"] == b"%PDF-", "PDF 文件头", str(f["head"]))
    check(f["tail"] == b"%%EOF", "PDF 文件尾", str(f["tail"]))
    check(f["counts"] == [1], "小树单页 /Count 1", str(f["counts"]))
    check(b"/MediaBox [0 0 842 595]" not in raw, "小树页面=图谱尺寸而非 A4 分页规格")
    check(b"/FontFile2" in raw and b"/ToUnicode" in raw, "默认矢量 PDF 嵌入字体与 Unicode 映射")
    import fitz
    with fitz.open(PDF_OUT) as doc:
        check("少群" in "".join(doc[0].get_text().split()), "小树文字可提取")
        check(not doc[0].get_images(full=True), "无照片时不嵌入整页图")
    check_xref(raw, "小树单页 PDF")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_big_pdf_paged(b):
    """2. ~130 人合成树：显式 paged，页数=ceil 公式，每页图正确铺满 842×595pt。"""
    tree, n = big_tree(130)
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    open_big(page, big_fixture_url(tree, "fixture_big130.html"))
    dims = page.evaluate("""() => {
      const st = document.getElementById('stage');
      return { w: st._baseW, h: st._baseH, plan: window.__ZP.pagePlan(st._baseW, st._baseH),
               paging: window.__ZP.pdfNeedsPaging(st._baseW, st._baseH) };
    }""")
    check(dims["paging"], "130 人树触发分页阈值（max(W,H)>约10400）", str(dims))
    t0 = _time.time()
    fn = export_via_file_menu(page, "导出 PDF", PDF_OUT, mode="paged")
    took = _time.time() - t0
    check(took < 60, "分页导出耗时可接受", "%.1fs" % took)
    check(fn.endswith(".pdf"), "文件名 .pdf", fn)
    raw = open(PDF_OUT, "rb").read()
    f = pdf_facts(raw)
    check(f["head"] == b"%PDF-", "PDF 文件头", str(f["head"]))
    check(f["tail"] == b"%%EOF", "PDF 文件尾", str(f["tail"]))
    check(f["counts"] and f["counts"][0] >= 2, "多页 /Count>=2", str(f["counts"]))
    check(f["counts"][0] == dims["plan"]["total"], "页数与 ceil 公式一致",
          "pdf=%s plan=%s dims=%sx%s" % (f["counts"], dims["plan"], dims["w"], dims["h"]))
    check(f["boxes"] == f["counts"][0], "每页 MediaBox 均为 842×595",
          "boxes=%s count=%s" % (f["boxes"], f["counts"]))
    check(f["counts"][0] == f["boxes"], "无遗漏页")
    check_xref(raw, "分页 PDF")
    toast = page.locator("#__toast").inner_text()
    check("已分为" in toast and "页" in toast, "分页 toast 说明", toast)
    # 像素级：每页应是白底图（防止空画布/底色缺失整页发黑），尺寸=2x 密度 1684×1190
    soi = bytes([0xff, 0xd8])
    eoi = bytes([0xff, 0xd9])
    jpegs, i = [], 0
    while True:
        s = raw.find(soi, i)
        if s < 0:
            break
        e = raw.find(eoi, s)
        jpegs.append(raw[s:e + 2])
        i = e + 2
    check(len(jpegs) == f["counts"][0], "每页各嵌一幅 JPEG", str(len(jpegs)))
    import base64 as _b64
    px = page.evaluate("""async (b64) => {
      const img = new Image();
      img.src = 'data:image/jpeg;base64,' + b64;
      await new Promise(r => { img.onload = r; });
      const cv = document.createElement('canvas');
      cv.width = img.width; cv.height = img.height;
      const c = cv.getContext('2d');
      c.drawImage(img, 0, 0);
      const d = c.getImageData(0, 0, cv.width, cv.height).data;
      let dark = 0, tot = 0;
      for (let k = 0; k < d.length; k += 40) { tot++; if (d[k] < 128 && d[k+1] < 128 && d[k+2] < 128) dark++; }
      return { w: img.width, h: img.height, darkPct: dark / tot * 100 };
    }""", _b64.b64encode(jpegs[-1]).decode())
    check(px["w"] == 1684 and px["h"] == 1190, "页图像 1684×1190（2x 密度）", str(px))
    check(px["darkPct"] < 20, "末页白底为主（无整页发黑）", str(px))
    # 2x 是 JPEG 像素密度，PDF 绘图矩阵必须使用物理页尺寸，否则右/下半页会被裁掉。
    import fitz
    from PIL import Image, ImageChops, ImageStat
    import io
    with fitz.open(PDF_OUT) as doc:
        bad_matrices = []
        for i, pdf_page in enumerate(doc):
            content = b"\n".join(doc.xref_stream(x) for x in pdf_page.get_contents())
            matrices = _re.findall(rb"([\d.]+)\s+0\s+0\s+([\d.]+)\s+0\s+0\s+cm", content)
            if not matrices or any(abs(float(w) - 842) > .01 or abs(float(h) - 595) > .01
                                   for w, h in matrices):
                bad_matrices.append((i + 1, matrices))
            rects = pdf_page.get_image_rects(pdf_page.get_images()[0][0])
            if len(rects) != 1 or max(abs(a - b) for a, b in zip(rects[0], pdf_page.rect)) > .01:
                bad_matrices.append((i + 1, str(rects)))
        check(not bad_matrices, "全部页图矩阵为 842×595pt 且铺满 MediaBox", str(bad_matrices[:5]))
        # 首/末页用真实 PDF 渲染对照原 JPEG 的 1/2 缩图，覆盖内容不同的切片。
        diffs = []
        for i in sorted({0, len(doc) - 1}):
            pix = doc[i].get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
            rendered = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            source = Image.open(io.BytesIO(jpegs[i])).convert("RGB").resize(
                (842, 595), Image.Resampling.BOX)
            diff = max(ImageStat.Stat(ImageChops.difference(rendered, source)).mean)
            diffs.append((i + 1, round(diff, 3)))
            check(diff < 4, "实际 PDF 渲染与整幅页图缩小一致", str(diffs))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_big_png_wide(b):
    """3. ~200 人合成树 PNG：exportTreeCanvas 宽 >=20000（12000 上限提升生效）"""
    tree, n = big_tree(200)
    ctx, page, errs, cons = fresh_page(b)
    open_big(page, big_fixture_url(tree, "fixture_big200.html"))
    cv = page.evaluate("() => exportTreeCanvas().then(cv => ({ w: cv.width, h: cv.height, s: cv._exportS }))")
    check(cv["w"] >= 20000, "PNG 宽 >=20000", str(cv))
    check(cv["s"] > 0, "画布携带有效倍率", str(cv))
    # 公式守卫：面积 <=80MP；364 人级布局 S≈0.39 属预期（大谱靠分页 PDF）
    g = page.evaluate("() => ({ s364: window.__ZP.pngScale(56153, 2000),"
                      " sGuard: window.__ZP.pngScale(10000, 9000) })")
    check(abs(g["s364"] - 22000 / 56153) < 1e-9, "364 人布局 S≈0.39（22000 上限主导）", str(g))
    check(abs(g["sGuard"] - _math.sqrt(8e7 / 9e7)) < 1e-9, "80MP 面积守卫生效", str(g))
    # Safari：上限回退 12000（临时置位后还原，不影响其他用例）
    sf = page.evaluate("""() => {
      const old = IS_SAFARI;
      IS_SAFARI = true;
      const s = window.__ZP.pngScale(56153, 2000);
      IS_SAFARI = old;
      return s;
    }""")
    check(abs(sf - 12000 / 56153) < 1e-9, "Safari 维持 12000 上限", str(sf))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_subtree_export_isolated(b):
    """4. 导出此支：弹窗→PNG；treeData/撤销栈/localStorage 不变，原选中态保留"""
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto(page)
    page.locator('.node[data-id="b1"]').click(button="right")
    page.locator('#__ctxMenu .mi', has_text="导出此支").click()
    check(page.locator("#__subtreeModal").is_visible(), "弹窗出现")
    check("少秀" in page.locator("#__subtreeTitle").inner_text(), "弹窗标题含成员名")
    hint = page.locator("#__subtreeHint").inner_text()
    check(_re.search(r"共\s*6\s*人", hint) and "后代" in hint, "提示含后代人数（正则）", hint)
    pre_data = page.evaluate("() => JSON.stringify(__ZP.sanitize(__ZP.data))")
    pre_hist = page.evaluate("() => __ZP.historyLens()")
    pre_store = page.evaluate("() => localStorage.getItem(__ZP.storageKey())")
    sel0 = page.evaluate("() => { const e = document.querySelector('.node.selected'); return e ? e.dataset.id : null; }")
    full = page.evaluate("() => exportTreeCanvas().then(cv => ({ w: cv.width, h: cv.height }))")
    with page.expect_download() as di:
        page.locator("#__subtreePng").click()
    fn = di.value.suggested_filename
    check(fn.startswith("少秀") and fn.endswith(".png"), "文件名=成员名", fn)
    fh = open(di.value.path(), "rb").read()
    check(fh.startswith(b"\x89PNG"), "PNG 签名", str(fh[:8]))
    w, h = _struct.unpack(">II", fh[16:24])
    check(w < full["w"] and h < full["h"], "子树画布小于全树导出",
          "sub=%dx%d full=%dx%d" % (w, h, full["w"], full["h"]))
    check(not page.locator("#__subtreeModal").is_visible(), "导出后弹窗已关")
    sel1 = page.evaluate("() => { const e = document.querySelector('.node.selected'); return e ? e.dataset.id : null; }")
    check(sel0 == sel1 and sel0 == "b1", "原选中态保留", "%s -> %s" % (sel0, sel1))
    check(page.evaluate("() => JSON.stringify(__ZP.sanitize(__ZP.data))") == pre_data, "treeData 深比较不变")
    check(page.evaluate("() => __ZP.historyLens()") == pre_hist, "historyLens 不变",
          "%s -> %s" % (pre_hist, page.evaluate("() => __ZP.historyLens()")))
    check(page.evaluate("() => localStorage.getItem(__ZP.storageKey())") == pre_store, "localStorage 数据不变")
    check(page.locator("#__exportBusy").count() == 0, "导出遮罩已移除")
    # Esc 可关
    page.locator('.node[data-id="b2"]').click(button="right")
    page.locator('#__ctxMenu .mi', has_text="导出此支").click()
    check(page.locator("#__subtreeModal").is_visible(), "弹窗再次出现")
    page.keyboard.press("Escape")
    page.wait_for_timeout(100)
    check(not page.locator("#__subtreeModal").is_visible(), "Esc 关闭弹窗")
    # 点遮罩可关
    page.locator('.node[data-id="b2"]').click(button="right")
    page.locator('#__ctxMenu .mi', has_text="导出此支").click()
    page.locator("#__subtreeModal").click(position={"x": 5, "y": 5})
    page.wait_for_timeout(100)
    check(not page.locator("#__subtreeModal").is_visible(), "点遮罩关闭弹窗")
    check(page.evaluate("() => __ZP.historyLens()") == pre_hist, "开合弹窗不进历史")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_page_formula(b):
    """5. 分页页数公式与实现一致：纯函数对照 Python 复算 + 超上限中止不产文件"""
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto(page)
    # 纯函数：JS pagePlan vs 规范公式（S_tile=clamp(max(595/H,842/W),0.6,2.5)，cols/rows 上取整）
    cases = [[1388, 452], [18865, 862], [56153, 2000], [3000, 42000], [560, 11000], [10300, 600], [10500, 600]]
    js = page.evaluate("(cases) => cases.map(([w, h]) => window.__ZP.pagePlan(w, h))", cases)
    for (w, h), plan in zip(cases, js):
        s = max(0.6, min(2.5, max(595 / h, 842 / w)))
        cols = _math.ceil(w * s / 842)
        rows = _math.ceil(h * s / 595)
        check(abs(plan["S"] - s) < 1e-9 and plan["cols"] == cols and plan["rows"] == rows
              and plan["total"] == cols * rows, "公式一致 %dx%d" % (w, h), str(plan))
    # 阈值边界：约 10400px 处翻转（浮点边界取安全余量验证两侧）
    check(page.evaluate("() => window.__ZP.pdfNeedsPaging(10300, 600)") is False, "阈值内仍单页")
    check(page.evaluate("() => window.__ZP.pdfNeedsPaging(10500, 600)") is True, "超阈值改分页")
    # 切片起点（tileStarts）：首片从 0、末片强制贴边、相邻片无缝（宽树 364 人 cols=41 含旧版缺口回归场景）
    cov = page.evaluate("""() => [8420, 7000, 10420, 18865, 34000, 42100, 56153].map(W => {
      const H = 2000;
      const plan = window.__ZP.pagePlan(W, H);
      const tw = 842 / plan.S, th = 595 / plan.S;
      const xs = window.__ZP.tileStarts(plan.cols, tw, W);
      const ys = window.__ZP.tileStarts(plan.rows, th, H);
      const ok = (st, t, world) => st.length > 0 && st[0] === 0
        && Math.abs(st[st.length - 1] + t - world) < 1e-6
        && st.every((s, i) => i === 0 || (s >= st[i - 1] && s - st[i - 1] <= t + 1e-6));
      return { W: W, cols: plan.cols, rows: plan.rows, okX: ok(xs, tw, W), okY: ok(ys, th, H) };
    })""")
    for r in cov:
        check(r["okX"] and r["okY"], "切片无缝覆盖 W=%s（cols=%s，rows=%s）" % (r["W"], r["cols"], r["rows"]), str(r))
    one = page.evaluate("() => window.__ZP.tileStarts(7, 1403.3333333333333, 8420)")
    exp = [i * (8420 - 1403.3333333333333) / 6 for i in range(7)]
    check(len(one) == 7 and all(abs(a - b) < 1e-9 for a, b in zip(one, exp)), "tileStarts 与 Python 复算一致", str(one))
    # 超过 300 页上限：toast 引导「导出此支」并中止（不产残缺文件——此处直接调用不渲染）
    abort = page.evaluate("""() => new Promise(res => {
      const dl = []; const orig = download;
      window.download = function(){ dl.push(arguments); };
      buildPagedPdf({ baseW: 200000, baseH: 2000, W: 200000, H: 2000, title: 't' }).then(r => {
        window.download = orig;
        res({ r: r === null, downloads: dl.length, toast: document.getElementById('__toast').textContent });
      });
    })""")
    check(abort["r"] is True, "超 300 页返回空（中止）", str(abort))
    check(abort["downloads"] == 0, "不产残缺文件", str(abort))
    check("导出此支" in abort["toast"], "toast 引导导出此支", abort["toast"])
    # 分页文件与公式一致（中小树 100 人 → 页数个位数复核；130 人见 t_big_pdf_paged）
    tree, n = big_tree(100)
    open_big(page, big_fixture_url(tree, "fixture_big100.html"))
    dims = page.evaluate("""() => {
      const st = document.getElementById('stage');
      return { w: st._baseW, h: st._baseH, plan: window.__ZP.pagePlan(st._baseW, st._baseH),
               paging: window.__ZP.pdfNeedsPaging(st._baseW, st._baseH) };
    }""")
    check(dims["paging"], "100 人树已过分页阈值", str(dims))
    export_via_file_menu(page, "导出 PDF", PDF_OUT, mode="paged")
    f = pdf_facts(open(PDF_OUT, "rb").read())
    check(f["counts"][0] == dims["plan"]["total"], "100 人树页数与公式一致",
          "pdf=%s plan=%s dims=%sx%s" % (f["counts"], dims["plan"], dims["w"], dims["h"]))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_export_journey_no_errors(b):
    """6. 全程无 JS 错误：文件导出、右键弹窗开合、小树此支 PDF（单页）一条龙"""
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto(page)
    export_via_file_menu(page, "导出图片", _os.path.join(LOCAL_OUT, "journey.png"))
    page.locator('.node[data-id="b1"]').click(button="right")
    page.locator('#__ctxMenu .mi', has_text="导出此支").click()
    page.locator("#__subtreePdf").click()
    check(page.locator("#__pdfModal").is_visible(), "此支 PDF 先选择模式")
    page.locator('input[name="pdfMode"][value="vector"]').check()
    with page.expect_download() as di:
        page.locator("#__pdfGo").click()
    fn = di.value.suggested_filename
    check(fn.startswith("少秀") and fn.endswith(".pdf"), "此支 PDF 文件名", fn)
    f = pdf_facts(open(di.value.path(), "rb").read())
    check(f["counts"] == [1], "小树此支仍单页（分页阈值按子树自身尺寸）", str(f["counts"]))
    check(f["head"] == b"%PDF-" and f["tail"] == b"%%EOF", "PDF 结构完整")
    # 弹窗取消按钮
    page.locator('.node[data-id="b3"]').click(button="right")
    page.locator('#__ctxMenu .mi', has_text="导出此支").click()
    page.locator("#__subtreeCancel").click()
    check(not page.locator("#__subtreeModal").is_visible(), "取消按钮关闭弹窗")
    check(not page.locator("#__exportBusy").count() > 0, "遮罩不残留")
    check(page.evaluate("() => __ZP.historyLens()") == [0, 0], "全程零历史写入")
    check(not errs, "无 JS 错误", str(errs))
    check(not [c for c in cons if "error" in c.lower()], "无 console 错误", str(cons[:3]))
    ctx.close()


if __name__ == "__main__":
    import sys as _sys
    ok = run_module(_sys.modules[__name__], "t_big_export 大族谱导出：分页PDF/此支/PNG上限")
    sys.exit(0 if ok else 1)
