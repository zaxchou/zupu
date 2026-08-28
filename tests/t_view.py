# -*- coding: utf-8 -*-
"""缩放锚点 / 滚轮平移 / 拖空白平移 / 打印文档树

锚点验证的关键前提：画布必须比视口大（否则滚动被上下界钳到 0，
数学上无从区分「锚点正确」与「没滚」）。因此本文件一律用小视口。
"""
from helper import *
import os, re


@testcase
def t_zoom_anchor_and_controls(b):
    ctx, page, errs, cons = fresh_page(b, width=760, height=540)
    goto(page)
    page.locator('button[title="恢复 1:1"]').click()
    s0 = page.evaluate("window.__ZP.scale")
    check(abs(s0 - 1) < 1e-9, "1:1 复位", str(s0))

    info = page.evaluate("""() => {
      const vp = document.getElementById('viewport');
      const box = document.querySelector('.node[data-id=\\"b2a\\"] .node-label').getBoundingClientRect();
      const vr = vp.getBoundingClientRect();
      return { sl: vp.scrollLeft, st: vp.scrollTop, s: __ZP.scale,
               mx: box.x + box.width/2 - vr.left, my: box.y + box.height/2 - vr.top };
    }""")
    check(info["mx"] > 40 and info["my"] > 40, "光标点不在钳制边界", str(info))

    # Ctrl+滚轮放大一格：CDP 合成 wheel 不带修饰键，注入带 ctrlKey 的参数事件
    # 专测 handler 分支与锚点数学（受托事件路径由真实浏览器保证）。
    vpr_l = page.evaluate("document.getElementById('viewport').getBoundingClientRect().left")
    vpr_t = page.evaluate("document.getElementById('viewport').getBoundingClientRect().top")
    page.evaluate("""(pt) => {
      const vp = document.getElementById('viewport');
      vp.dispatchEvent(new WheelEvent('wheel', { deltaY: -240, ctrlKey: true,
        clientX: pt.l + pt.mx, clientY: pt.t + pt.my, bubbles: true, cancelable: true }));
    }""", {"l": vpr_l, "t": vpr_t, "mx": info["mx"], "my": info["my"]})
    page.wait_for_timeout(600)   # 等缩放动画完全收敛

    res = page.evaluate("""(o) => {
      const vp = document.getElementById('viewport');
      const s2 = __ZP.scale;
      return { sl: vp.scrollLeft, st: vp.scrollTop, s2 };
    }""", info)
    # v15.6 滚轮为倍速缩放：单次 deltaY=-240 → ×e^(240*0.0016)
    expected_mult = 2.718281828459045 ** (240 * 0.0016)
    check(abs(res["s2"] / s0 - expected_mult) < 1e-6, "滚轮倍速缩放（×e^k）",
          f"s2={res['s2']} expect~{s0 * expected_mult}")
    check(abs(res["s2"] - s0) > 0.05, "确有放大")
    # 期望值按完整钳制公式：max(0, min(需求量, 最大可滚动量))
    expL_raw = (info["sl"] + info["mx"]) / info["s"] * res["s2"] - info["mx"]
    expT_raw = (info["st"] + info["my"]) / info["s"] * res["s2"] - info["my"]
    lims = page.evaluate("""() => {
      const vp = document.getElementById('viewport');
      const st = document.getElementById('stage');
      return { h: Math.max(0, st.offsetWidth*__ZP.scale - vp.clientWidth),
               v: Math.max(0, st.offsetHeight*__ZP.scale - vp.clientHeight) };
    }""")
    expL = max(0.0, min(expL_raw, lims["h"]))
    expT = max(0.0, min(expT_raw, lims["v"]))
    check(abs(res["sl"] - expL) <= 2, "横向锚点保持（含边界钳制）",
          f"sl={res['sl']} exp={expL}")
    check(abs(res["st"] - expT) <= 2, "纵向锚点保持（含边界钳制）",
          f"st={res['st']} exp={expT}")
    lbl = page.locator("#zoomLabel").inner_text()
    check(lbl == str(round(s0 * expected_mult * 100)) + "%", "百分比标签同步", lbl)

    for _ in range(80):
        page.locator('button[title="放大"]').click()
    hi = page.evaluate("window.__ZP.scale")
    check(hi <= 2.5 + 1e-9, "放大上限 250%", str(hi))
    for _ in range(500):
        page.locator('button[title="缩小"]').click()
        if page.evaluate("window.__ZP.scale") <= 0.12:
            break
    lo = page.evaluate("window.__ZP.scale")
    check(lo >= 0.12 - 1e-9, "缩小下限 12%", str(lo))
    page.locator('button[title="适应屏幕"]').click()
    fs = page.evaluate("window.__ZP.scale")
    check(0.12 <= fs <= 1.2, "适应屏幕夹在 [0.12,1.2]", str(fs))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_native_wheel_and_blank_drag_pan(b):
    ctx, page, errs, cons = fresh_page(b, width=900, height=470)
    goto(page)
    page.locator('button[title="恢复 1:1"]').click()
    ovf = page.evaluate("""() => {
      const vp=document.getElementById('viewport'), st=document.getElementById('stage');
      return { sw: st.offsetWidth*__ZP.scale, sh: st.offsetHeight*__ZP.scale,
               cw: vp.clientWidth, ch: vp.clientHeight };
    }""")
    check(ovf["sw"] > ovf["cw"] and ovf["sh"] > ovf["ch"], "存在双向溢出", str(ovf))

    # 先做拖空白平移：点取「第一行节点上方」的空白带（首行上方必无卡片）。
    # x 取左侧 0.30：无头 Chromium 对部分合成拖动像素路径会丢弃垂直滚动
    # （有头模式同路径正常，应用代码无嫌疑），左侧空白带在无头/有头下都稳定。
    spot = page.evaluate("""() => {
      const vp=document.getElementById('viewport');
      const r=vp.getBoundingClientRect();
      vp.scrollTo(0,0);
      return { x: Math.round(r.left + r.width*0.30), y: Math.round(r.top + 20) };
    }""")
    lim0 = page.evaluate("""() => {
      const vp=document.getElementById('viewport'), st=document.getElementById('stage');
      return { h: Math.max(0, st.offsetWidth*__ZP.scale - vp.clientWidth),
               v: Math.max(0, st.offsetHeight*__ZP.scale - vp.clientHeight) };
    }""")
    # 确认该点确实是空白（elementFromPoint 不落在卡片/按钮上）
    tag = page.evaluate("""(pt) => {
      const el = document.elementFromPoint(pt.x, pt.y);
      return el ? (el.id || el.className || el.tagName) : 'null';
    }""", spot)
    check(tag in ("viewport", "stage", "nodes", "tips"), "落点是画布空白", str(tag))
    sl0 = page.evaluate("document.getElementById('viewport').scrollLeft")
    st0 = page.evaluate("document.getElementById('viewport').scrollTop")
    page.mouse.move(spot["x"], spot["y"])
    page.mouse.down()
    page.mouse.move(spot["x"] - 160, spot["y"] - 120, steps=6)
    page.mouse.up()
    page.wait_for_timeout(150)
    sl1 = page.evaluate("document.getElementById('viewport').scrollLeft")
    st1 = page.evaluate("document.getElementById('viewport').scrollTop")
    check(sl1 - sl0 >= min(110, lim0["h"]), "拖空白横向平移（按余量钳制）",
          f"{sl0}->{sl1} 余量{lim0['h']}")
    check(st1 - st0 >= min(80, lim0["v"]), "拖空白纵向平移（按余量钳制）",
          f"{st0}->{st1} 余量{lim0['v']}")
    cls = page.locator("#viewport").get_attribute("class")
    check(cls and "panning" not in cls, "松手结束平移态")

    # 再测普通滚轮横向滚动；先回到最左，保证有余量
    page.evaluate("() => document.getElementById('viewport').scrollTo({left:0,top:0})")
    page.mouse.move(450, 320)
    for _ in range(4):
        page.mouse.wheel(300, 0)
    page.wait_for_timeout(150)
    sl2 = page.evaluate("document.getElementById('viewport').scrollLeft")
    check(sl2 >= 60, "普通滚轮可平移(v12 完全无效)", f"scrollLeft={sl2}")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_print_document_tree(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    # 触发打印前钩子（真实浏览器打印亦走此路径）
    page.emulate_media(media="print")
    page.evaluate("() => window.dispatchEvent(new Event('beforeprint'))")
    li_count = page.locator("#printArea li").count()
    check(li_count == 13, "打印大纲覆盖全部成员（无视折叠）", f"got {li_count}")
    disp_vp = page.evaluate("getComputedStyle(document.getElementById('viewport')).display")
    check(disp_vp == "none", "打印时隐藏画布", disp_vp)
    disp_pa = page.evaluate("getComputedStyle(document.getElementById('printArea')).display")
    check(disp_pa == "block", "打印时显示文档区", disp_pa)
    title = page.locator("#printArea h2").inner_text()
    check(re.search(r"\d{4}-\d{2}-\d{2}", title), "打印标题带日期", title)
    # 打印 PDF 管线冒烟
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_out", "print_smoke.pdf")
    page.pdf(path=out, format="A4", landscape=True)
    check(os.path.exists(out) and os.path.getsize(out) > 8000, "PDF 生成", str(out))
    page.emulate_media(media="screen")
    disp_pa2 = page.evaluate("getComputedStyle(document.getElementById('printArea')).display")
    check(disp_pa2 == "none", "屏幕模式隐藏打印区", disp_pa2)
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


if __name__ == "__main__":
    import sys as _sys
    ok = run_module(_sys.modules[__name__], "t_view 缩放/平移/打印")
    sys.exit(0 if ok else 1)
