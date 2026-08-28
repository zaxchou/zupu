# -*- coding: utf-8 -*-
"""折叠角标、拖拽换位（真实鼠标事件）、撤销合并"""
from helper import *


@testcase
def t_fold_pill_and_reexpand(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    page.locator('.node[data-id="b1"] .quick-add').click()
    page.locator('#__ctxMenu .mi', has_text="折叠").click()
    page.wait_for_timeout(200)
    nodes = page.locator(".node").count()
    check(nodes == 8, "折叠后隐藏 5 位后代", f"got {nodes}")
    pill_txt = page.locator('.node[data-id="b1"] .fold').inner_text().replace("\n", "")
    check("5" in pill_txt, "折叠人数角标 ▸ 5", pill_txt)
    # 点角标直接展开
    page.locator('.node[data-id="b1"] .fold').click()
    page.wait_for_timeout(200)
    check(page.locator(".node").count() == 13, "点角标重新展开")
    # 展开的卡片现在常驻「▾」快捷折叠钮
    check(page.locator('.node[data-id="b1"] .fold').inner_text().replace("\n", "") == "▾",
          "展开态显示快捷折叠钮 ▾")
    # 根折叠 → 只剩根自己，角标 ▸ 12
    page.locator('.node[data-id="root"] .quick-add').click()
    page.locator('#__ctxMenu .mi', has_text="折叠").click()
    page.wait_for_timeout(200)
    check(page.locator(".node").count() == 1, "根折叠只剩根")
    rpill = page.locator('.node[data-id="root"] .fold').inner_text()
    check("12" in rpill, "根角标显示全部后代", rpill)
    # 全展开恢复（已收进「视图」下拉菜单）
    page.locator("#btnView").click()
    page.locator('#__ctxMenu .mi', has_text="全展开").click()
    page.wait_for_timeout(200)
    check(page.locator(".node").count() == 13, "视图菜单全展开恢复")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_drag_swap_siblings(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    order_before = page.evaluate('window.__ZP.findNode("b1a").children.map(c=>c.name)')
    check(order_before == ["周新洋", "周亿宁（?）"], "初始长幼次序", str(order_before))

    src = page.locator('.node[data-id="b1a2"] .node-label').bounding_box()
    dst = page.locator('.node[data-id="b1a1"] .node-label').bounding_box()
    sx, sy = src["x"] + src["width"] / 2, src["y"] + src["height"] / 2
    tx, ty = dst["x"] + dst["width"] * 0.18, dst["y"] + dst["height"] / 2

    page.mouse.move(sx, sy)
    page.mouse.down()
    # 逐步移动：先越过 8px 阈值触发拖拽态
    for i in range(1, 13):
        page.mouse.move(sx + (tx - sx) * i / 12, sy + (ty - sy) * i / 12)
    page.wait_for_timeout(60)
    marker_visible = page.locator("#__dropMarker").is_visible()
    check(marker_visible, "拖拽落点指示线出现")
    page.mouse.up()
    # mouseup 处理器同步完成落位与渲染
    order_after = page.evaluate('window.__ZP.findNode("b1a").children.map(c=>c.name)')
    check(order_after == ["周亿宁（?）", "周新洋"], "拖拽后次序互换", str(order_after))
    # 排行角标更新：原第 1 位现在排第 2，应标「次」
    badge = page.locator('.node[data-id="b1a1"] .rank').inner_text()
    check(badge == "次", "排行角标跟随更新", badge)
    check(dlg.count() == 0, "纯拖拽零对话框", str(dlg.records))
    # 拖完 350ms 内的立即点击被吞
    lb = page.locator('.node[data-id="b1a1"] .node-label')
    lb.click()
    cls = lb.locator("xpath=..").get_attribute("class")
    check(cls and "selected" not in cls, "拖完 350ms 内的点击被吞")
    page.wait_for_timeout(400)
    lb.click()
    cls2 = lb.locator("xpath=..").get_attribute("class")
    check(cls2 and "selected" in cls2, "窗口期后点击恢复正常选中")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_drag_noop_no_history(b):
    """原地小幅点击式「拖拽」不应产生历史记录"""
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    u0 = page.evaluate("window.__ZP.historyLens()[0]")
    src = page.locator('.node[data-id="b1a2"] .node-label').bounding_box()
    cx = src["x"] + src["width"] / 2
    cy = src["y"] + src["height"] / 2
    page.mouse.move(cx, cy)
    page.mouse.down()
    page.mouse.move(cx + 3, cy)     # 未过 8px 阈值
    page.mouse.move(cx + 4, cy + 2)
    page.mouse.up()
    page.wait_for_timeout(120)
    u1 = page.evaluate("window.__ZP.historyLens()[0]")
    check(u1 == u0, "未达阈值不入栈", f"{u0}->{u1}")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


if __name__ == "__main__":
    import sys as _sys
    ok = run_module(_sys.modules[__name__], "t_fold_drag 折叠/拖拽/历史边界")
    sys.exit(0 if ok else 1)
