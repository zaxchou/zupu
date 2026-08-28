# -*- coding: utf-8 -*-
"""菜单、增删改、档案弹窗与 v12 键盘泄漏 bug 的专项回归。
关键断言：弹窗内 Tab/Delete/回车 绝不触发全局快捷键或多余原生对话框。"""
from helper import *


@testcase
def t_menu_open_items_and_bounds(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    # 普通节点菜单
    qa = page.locator('.node[data-id="b1a1"] .quick-add')
    qa.click()
    check(page.locator("#__ctxMenu").is_visible(), "＋ 打开菜单")
    items = page.locator("#__ctxMenu .mi").all_inner_texts()
    joined = "|".join(items)
    for kw in ["配偶", "子女", "同辈", "改名", "档案", "删除"]:
        check(kw in joined, f"普通节点含「{kw}」", joined)
    # 菜单尺寸实测（v12 在 display:none 下测量恒 0，靠兜底值定位）
    m = page.locator("#__ctxMenu").bounding_box()
    check(m["width"] > 130, "菜单宽度实测>130（证明先显示后测量）", str(m))
    vw = page.evaluate("window.innerWidth")
    check(m["x"] >= 0 and m["x"] + m["width"] <= vw, "菜单未横向越界", str(m))
    # 右键同样打开
    page.mouse.click(60, 620)   # 关闭
    lb = page.locator('.node[data-id="b2a"] .node-label')
    lb.click(button="right")
    check(page.locator("#__ctxMenu").is_visible(), "右键打开菜单")
    # 根节点菜单
    page.keyboard.press("Escape")
    page.locator('.node[data-id="root"] .quick-add').click()
    root_items = "|".join(page.locator("#__ctxMenu .mi").all_inner_texts())
    check("第一代" in root_items and "配偶" not in root_items and "删除" not in root_items,
          "根节点菜单项正确", root_items)
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_add_child_via_menu(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    dlg.queue("prompt", "测试子")
    page.locator('.node[data-id="b1a1"] .quick-add').click()
    page.locator('#__ctxMenu .mi', has_text="子女").click()
    page.wait_for_timeout(200)
    kids = page.evaluate('window.__ZP.findNode("b1a1").children.map(c=>c.name)')
    check("测试子" in kids, "菜单纯点击添加子女成功", str(kids))
    sel = page.evaluate("document.querySelector('.node.selected')?.dataset.id || null")
    check(sel is not None, "新节点自动选中", str(sel))
    ulen, rlen = page.evaluate("window.__ZP.historyLens()")
    check(ulen >= 1, "添加动作入撤销栈")
    rlen2 = page.evaluate("window.__ZP.historyLens()[1]")
    check(rlen2 == 0, "新操作清空重做栈")
    check(dlg.count() == 1, "恰好一次 prompt", str(dlg.records))
    ctx.close()


@testcase
def t_modal_keyboard_no_leak(b):
    """v12 泄漏三连回归：Tab 弹加子女？Delete 弹删除？回车保存后弹加同辈？——都必须为零"""
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    # 选中 周新洋 并打开档案
    page.locator('.node[data-id="b1a1"] .node-label').click()
    page.keyboard.press("Control+i")
    check(page.locator("#__detailModal").is_visible(), "Ctrl+I 打开档案")
    birth = page.locator("#__dmBirth")
    birth.fill("")
    birth.click()
    birth.type("1935")
    # ★ 泄漏点1：输入框里按 Tab —— 必须移动焦点，不得触发「加子女」prompt
    page.keyboard.press("Tab")
    active = page.evaluate("document.activeElement && document.activeElement.id")
    check(active == "__dmDeath", "Tab 在弹窗内正常移动焦点", str(active))
    check(dlg.count() == 0, "Tab 未泄漏成快捷键", str(dlg.records))
    # ★ 泄漏点2：输入框里按 Delete —— 不得触发「删除确认」
    death = page.locator("#__dmDeath")
    death.click()
    death.type("1990")
    page.keyboard.press("Delete")
    page.wait_for_timeout(120)
    check(dlg.count() == 0, "Delete 未泄漏成删除确认", str(dlg.records))
    check(page.locator("#__detailModal").is_visible(), "弹窗未被误关")
    # ★ 泄漏点3：姓名框回车=保存，保存后不得再弹「加同辈」
    name_in = page.locator("#__dmName")
    name_in.fill("周新洋")
    page.keyboard.press("Enter")
    page.wait_for_timeout(250)
    check(not page.locator("#__detailModal").is_visible(), "回车保存并关闭弹窗")
    b_val = page.evaluate('window.__ZP.findNode("b1a1").birth')
    d_val = page.evaluate('window.__ZP.findNode("b1a1").death')
    check(b_val == "1935" and d_val == "1990", "生卒年已写入数据", f"{b_val}/{d_val}")
    check(dlg.count() == 0, "回车保存后无第二个对话框（v12 会弹加同辈）", str(dlg.records))
    # 蓝色角标出现
    byc = page.locator('.node[data-id="b1a1"] .rank.by').count()
    check(byc == 1, "填生年后显示蓝色年份角标", f"got {byc}")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_spouse_add_edit_remove(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    page.locator('.node[data-id="b1a1"] .node-label').click()
    # Ctrl+Shift+S 加配偶
    dlg.queue("prompt", "王秀兰")
    page.keyboard.press("Control+Shift+s")
    page.wait_for_timeout(150)
    sps = page.evaluate('window.__ZP.findNode("b1a1").spouses')
    check(sps == ["王秀兰"], "快捷键添加配偶", str(sps))
    # 第二位
    dlg.clear(); dlg.queue("prompt", "刘二妮")
    dlg.queue("prompt", "王改嫁")     # 紧接的双击修改预填
    page.keyboard.press("Control+Shift+s")
    page.wait_for_timeout(120)
    # 双击第二位配偶文字 → 预填 prompt 改名
    sp_el = page.locator('.node[data-id="b1a1"] .sp[data-sp="1"]')
    sp_el.dblclick()
    page.wait_for_timeout(120)
    sps2 = page.evaluate('window.__ZP.findNode("b1a1").spouses')
    check(sps2 == ["王秀兰", "王改嫁"], "双击配偶改名", str(sps2))
    # 双击清空 + confirm → 移除
    dlg.clear(); dlg.queue("prompt", ""); dlg.queue("confirm", True)
    page.locator('.node[data-id="b1a1"] .sp[data-sp="1"]').dblclick()
    page.wait_for_timeout(150)
    sps3 = page.evaluate('window.__ZP.findNode("b1a1").spouses')
    check(sps3 == ["王秀兰"], "清空确认后移除配偶", str(sps3))
    # 重复添加拒绝
    before = page.evaluate("window.__ZP.historyLens()")
    dlg.clear(); dlg.queue("prompt", "王秀兰")
    page.keyboard.press("Control+Shift+s")
    page.wait_for_timeout(120)
    n = page.evaluate('window.__ZP.findNode("b1a1").spouses.length')
    check(n == 1, "重复配偶被拒", f"count={n}")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_delete_count_and_undo_redo(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    page.locator('.node[data-id="b1"] .node-label').click()
    page.keyboard.press("Delete")
    page.wait_for_timeout(100)
    msgs = dlg.messages()
    check(len(msgs) == 1 and "5 位后代" in msgs[0], "删除确认统计全部后代(v12 只报直系)",
          str(msgs))
    dlg.queue("confirm", False)      # 先取消
    # 上一步已经消耗一次 dialog；重新按 Delete 出现的 confirm 由脚本应答
    page.keyboard.press("Delete")
    page.wait_for_timeout(100)
    alive = page.evaluate('!!window.__ZP.findNode("b1")')
    check(alive, "取消则不删")
    dlg.clear(); dlg.queue("confirm", True)
    page.keyboard.press("Delete")
    page.wait_for_timeout(200)
    gone = page.evaluate('!!window.__ZP.findNode("b1")')
    check(not gone, "确认后整支删除")
    nodes = page.locator(".node").count()
    check(nodes == 7, "删除后剩 7 个节点(13-6)", f"got {nodes}")
    stats = page.locator("#statsChip").inner_text().replace("\n", "")
    check("6" in stats, "统计条联动更新", stats)
    # 撤销恢复整支
    page.keyboard.press("Control+z")
    page.wait_for_timeout(200)
    back = page.evaluate('!!window.__ZP.findNode("b1")')
    kids = page.evaluate('window.__ZP.findNode("b1").children.length')
    check(back and kids == 2, "撤销恢复分支及后代", f"kids={kids}")
    nodes2 = page.locator(".node").count()
    check(nodes2 == 13, "撤销后节点数复原", f"got {nodes2}")
    # 重做再删 → 再用标准撤销快捷键 Ctrl+Z 留下
    page.keyboard.press("Control+y")
    page.wait_for_timeout(200)
    check(not page.evaluate('!!window.__ZP.findNode("b1")'), "重做再次删除")
    page.keyboard.press("Control+z")
    page.wait_for_timeout(200)
    check(page.evaluate('!!window.__ZP.findNode("b1")'), "再次撤销恢复（Ctrl+Shift+Z=重做的约定语义）")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


if __name__ == "__main__":
    import sys as _sys
    ok = run_module(_sys.modules[__name__], "t_edit 菜单/弹窗键盘/配偶/删除撤销")
    sys.exit(0 if ok else 1)
