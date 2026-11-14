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


def _touch_path(cdp, start, end, steps=14):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart",
        "touchPoints": [{"x": round(start[0]), "y": round(start[1])}]})
    for i in range(1, steps + 1):
        x = start[0] + (end[0] - start[0]) * i / steps
        y = start[1] + (end[1] - start[1]) * i / steps
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove",
            "touchPoints": [{"x": round(x), "y": round(y)}]})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


@testcase
def t_touch_pickup_pan_and_edgescroll(b):
    """v15.58 手机拖拽重排：按住卡片滑动=平移（不误拖）、长按拾起拖动换位、
       拖到视口边缘画布自动滚动；长按不再弹菜单（菜单走选中操作条）。"""
    ctx, page, errs, cons = fresh_page(b, 390, 844, touch=True, mobile=True)
    goto(page)
    page.evaluate("setTargetScale(1.5)")
    page.wait_for_timeout(400)
    cdp = ctx.new_cdp_session(page)
    # ① 按在卡片上滑动 = 平移画布，卡片不换位
    card = page.locator('.node[data-id="b2"]').first
    card.scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    cb = card.bounding_box()
    sl0 = page.evaluate("() => [document.getElementById('viewport').scrollLeft, document.getElementById('viewport').scrollTop]")
    _touch_path(cdp, (cb["x"] + cb["width"] / 2, cb["y"] + cb["height"] / 2),
                     (cb["x"] + cb["width"] / 2 - 160, cb["y"] + cb["height"] / 2 - 60))
    page.wait_for_timeout(250)
    sl1 = page.evaluate("() => [document.getElementById('viewport').scrollLeft, document.getElementById('viewport').scrollTop]")
    check(sl0 != sl1, "按在卡片上滑动 = 平移画布", str((sl0, sl1)))
    check(page.evaluate("() => window.__ZP.findNode('b2')") is not None and
          page.evaluate("() => findParent('b2').children.map(c=>c.id)").count("b2") == 1,
          "滑动不改折叠/次序")
    # ② 长按拾起：卡浮起、菜单不弹；拖到右侧同辈松手 = 换位
    page.evaluate("setTargetScale(1.0)")
    page.wait_for_function("zoomRaf === null")   # 缩放动画结束再取坐标（动画中途卡片会移位）
    card = page.locator('.node[data-id="b1a1"]').first
    card.scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    cb = card.bounding_box()
    cx, cy = cb["x"] + cb["width"] / 2, cb["y"] + cb["height"] / 2
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": round(cx), "y": round(cy)}]})
    page.wait_for_timeout(450)
    check(page.evaluate("() => document.querySelectorAll('.node.dragging').length") > 0,
          "长按 300ms 拾起（卡片进入拖动态）")
    check(page.evaluate("() => document.getElementById('__ctxMenu').style.display") != "block",
          "长按不再弹菜单（入口迁移到操作条「⋯」）")
    target = page.locator('.node[data-id="b1a2"]').first.bounding_box()
    _touch_path(cdp, (cx, cy), (target["x"] + target["width"] + 30, target["y"] + target["height"] / 2), steps=16)
    page.wait_for_timeout(300)
    order = page.evaluate("() => window.__ZP.findNode('b1a').children.map(c => c.id)")
    check(order == ["b1a2", "b1a1"], "拾起拖动完成换位", str(order))
    page.evaluate("undo()")
    page.wait_for_timeout(150)
    # ③ 拖到视口右缘：画布自动滚动
    page.evaluate("setTargetScale(1.2)")
    page.wait_for_timeout(300)
    card = page.locator('.node[data-id="b2"]').first
    card.scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    cb = card.bounding_box()
    cx, cy = cb["x"] + cb["width"] / 2, cb["y"] + cb["height"] / 2
    sl2 = page.evaluate("() => document.getElementById('viewport').scrollLeft")
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": round(cx), "y": round(cy)}]})
    page.wait_for_timeout(400)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": 385, "y": round(cy)}]})
    page.wait_for_timeout(900)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    page.wait_for_timeout(300)
    sl3 = page.evaluate("() => document.getElementById('viewport').scrollLeft")
    check(sl3 > sl2 + 50, "拖到视口边缘自动滚动露出隐藏区域", f"{sl2} -> {sl3}")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_selbar_reorder_and_menu(b):
    """v15.58 选中操作条：前移/后移/最前/最后精确排序（手机不依赖拖动），⋯ 打开成员菜单；
       菜单内也有四个排序项；越界移动有提示且不写历史。"""
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    page.locator('.node[data-id="b1a1"] .node-label').click()
    page.wait_for_timeout(200)
    check(page.locator('#__selBar').count() == 1 and page.locator('#__selBar .sa-btn').count() == 6,
          "选中出现操作条（⋯ + 四个排序钮 + ✕ 关闭）")
    before = page.evaluate("() => window.__ZP.findNode('b1a').children.map(c => c.id)")
    page.locator('#__selBar .sa-btn[title*="后移"]').click()   # b1a1 是第一位：后移 → 交换
    page.wait_for_timeout(250)
    mid = page.evaluate("() => window.__ZP.findNode('b1a').children.map(c => c.id)")
    check(mid == ["b1a2", "b1a1"], "后移一位生效", str(mid))
    page.locator('#__selBar .sa-btn[title*="后移"]').click()   # 已是最后：提示且不动
    page.wait_for_timeout(200)
    check("无需再移" in page.locator("#__toast").text_content(), "越界移动有提示")
    lens = page.evaluate("() => window.__ZP.historyLens()")
    page.locator('#__selBar .sa-btn[title*="最前"]').click()
    page.wait_for_timeout(250)
    check(page.evaluate("() => window.__ZP.findNode('b1a').children.map(c => c.id)") == ["b1a1", "b1a2"],
          "移到最前生效")
    check(page.evaluate("() => window.__ZP.historyLens()") != lens, "排序写入撤销历史")
    page.evaluate("undo()")
    page.wait_for_timeout(150)
    page.locator('.node[data-id="b1a1"] .node-label').click()
    page.wait_for_timeout(150)
    page.locator('#__selBar .sa-btn[title*="更多"]').click()
    page.wait_for_timeout(200)
    items = page.locator('#__ctxMenu .mi').all_text_contents()
    check(all(t in items for t in ["移到最前", "前移一位", "后移一位", "移到最后"]),
          "成员菜单含四个排序项", str(items))
    page.locator('#__ctxMenu .mi', has_text="移到最前").click()   # undo 后 b1a1 在第 2 位
    page.wait_for_timeout(250)
    check(page.evaluate("() => window.__ZP.findNode('b1a').children.map(c => c.id)") == ["b1a1", "b1a2"],
          "菜单排序项生效")
    # 三条消失路径：✕ 按钮 / 点空白处 / Esc（网友反馈「不知道怎么让它消失」）
    page.locator('#__selBar .sa-btn[title*="取消选中"]').click()
    page.wait_for_timeout(150)
    check(page.locator('#__selBar').count() == 0
          and page.evaluate("() => document.querySelectorAll('.node.selected').length") == 0,
          "✕ 取消选中并收起操作条")
    page.locator('.node[data-id="b1a1"] .node-label').click()
    page.wait_for_timeout(150)
    check(page.locator('#__selBar').count() == 1, "重新选中再现操作条")
    page.mouse.click(600, 700)   # 空白画布
    page.wait_for_timeout(150)
    check(page.locator('#__selBar').count() == 0, "点空白处取消选中")
    page.locator('.node[data-id="b1a1"] .node-label').click()
    page.wait_for_timeout(150)
    page.keyboard.press("Escape")
    page.wait_for_timeout(150)
    check(page.locator('#__selBar').count() == 0, "Esc 取消选中")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


if __name__ == "__main__":
    import sys as _sys
    ok = run_module(_sys.modules[__name__], "t_fold_drag 折叠/拖拽/历史边界")
    sys.exit(0 if ok else 1)
