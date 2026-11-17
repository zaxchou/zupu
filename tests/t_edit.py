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
    page.keyboard.press("Escape")   # 关闭菜单（新布局下固定坐标会误触菜单项）
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
    page.locator('.node[data-id="b1a1"] .quick-add').click()
    page.locator('#__ctxMenu .mi', has_text="子女").click()
    page.fill("#__uipInput", "测试子")
    page.click("#__uipOk")
    page.wait_for_timeout(200)
    kids = page.evaluate('window.__ZP.findNode("b1a1").children.map(c=>c.name)')
    check("测试子" in kids, "菜单纯点击添加子女成功", str(kids))
    sel = page.evaluate("document.querySelector('.node.selected')?.dataset.id || null")
    check(sel is not None, "新节点自动选中", str(sel))
    ulen, rlen = page.evaluate("window.__ZP.historyLens()")
    check(ulen >= 1, "添加动作入撤销栈")
    rlen2 = page.evaluate("window.__ZP.historyLens()[1]")
    check(rlen2 == 0, "新操作清空重做栈")
    check(dlg.count() == 0, "零原生弹窗（页内输入弹窗替代）", str(dlg.records))
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
    page.keyboard.press("Control+Shift+s")
    page.fill("#__uipInput", "王秀兰")
    page.click("#__uipOk")
    page.wait_for_timeout(150)
    sps = page.evaluate('window.__ZP.findNode("b1a1").spouses')
    check(sps == ["王秀兰"], "快捷键添加配偶", str(sps))
    # 第二位
    page.keyboard.press("Control+Shift+s")
    page.fill("#__uipInput", "刘二妮")
    page.click("#__uipOk")
    page.wait_for_timeout(120)
    # 双击第二位配偶文字 → 弹窗预填改名
    sp_el = page.locator('.node[data-id="b1a1"] .sp[data-sp="1"]')
    sp_el.dblclick()
    page.fill("#__uipInput", "王改嫁")
    page.click("#__uipOk")
    page.wait_for_timeout(120)
    sps2 = page.evaluate('window.__ZP.findNode("b1a1").spouses')
    check(sps2 == ["王秀兰", "王改嫁"], "双击配偶改名", str(sps2))
    # 双击清空 + 页内确认 → 移除（v15.56 起不再用系统 confirm）
    page.locator('.node[data-id="b1a1"] .sp[data-sp="1"]').dblclick()
    page.fill("#__uipInput", "")
    page.click("#__uipOk")
    confirm_page(page, True)
    page.wait_for_timeout(150)
    sps3 = page.evaluate('window.__ZP.findNode("b1a1").spouses')
    check(sps3 == ["王秀兰"], "清空确认后移除配偶", str(sps3))
    # 重复添加拒绝
    before = page.evaluate("window.__ZP.historyLens()")
    page.keyboard.press("Control+Shift+s")
    page.fill("#__uipInput", "王秀兰")
    page.click("#__uipOk")
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
    title = delete_choice(page, "cancel")   # v15.60 删除二选一弹窗，先取消
    page.wait_for_timeout(100)
    check("5 位后代" in title, "删除弹窗统计全部后代(v12 只报直系)",
          title)
    check(dlg.count() == 0, "删除走页内弹窗，不再弹系统 confirm", str(dlg.records))
    # 再次按 Delete；取消则不删
    page.keyboard.press("Delete")
    delete_choice(page, "cancel")
    page.wait_for_timeout(100)
    alive = page.evaluate('!!window.__ZP.findNode("b1")')
    check(alive, "取消则不删")
    page.keyboard.press("Delete")
    delete_choice(page, "all")
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


@testcase
def t_delete_keep_self_detaches_descendants(b):
    """v15.60 网友场景：误「＋父辈」后想只删错误的人。仅删除此人 → 后代按原次序
       整体上移一层；世祖按结构自动重算；撤销完整恢复。"""
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    # 复刻网友操作：给 b1a1 之上加一个错误的「父辈」（b1a1 变成新人的孩子）
    page.locator('.node[data-id="b1a1"] .node-label').click()
    page.locator('.node[data-id="b1a1"] .quick-add').click()
    page.locator('#__ctxMenu .mi', has_text='父辈').click()
    page.fill('#__parentInput', '错误的人')
    page.locator('#__parentOk').click()
    page.wait_for_timeout(250)
    wrong = page.evaluate("() => { const p = findParent('b1a1'); return {id: p.id, kids: p.children.map(c => c.id)}; }")
    check(wrong['id'] != 'b1a' and 'b1a1' in wrong['kids'], '前置：错误父辈已插入且带走了 b1a1', str(wrong))
    # 删除这个错误的人 → 选「仅删除此人」
    wrong_id = wrong['id']
    page.locator(f'.node[data-id="{wrong_id}"] .node-label').click()
    page.keyboard.press('Delete')
    title = delete_choice(page, 'sub')
    page.wait_for_timeout(250)
    check('1 位后代' in title, '弹窗列出该人名下后代数', title)
    check(not page.evaluate(f'() => !!findNode("{wrong_id}")'), '错误的人已删除')
    back = page.evaluate("() => { const p = findParent('b1a1'); return {id: p.id, kids: p.children.map(c => c.id)}; }")
    check(back['id'] == 'b1a' and back['kids'] == ['b1a1', 'b1a2'],
          'b1a1 回到原父名下且次序不变', str(back))
    gens = page.evaluate("() => Array.from(computeGenerations().values(), g => g.gen).join(',')")
    check(gens == '1,2,3,3,2,3,1,2,3,1,2,1', '世祖按结构自动重算（b1a1 回到 3 世，无偏移）', gens)
    # 配偶/档案随人删除：错误的人不残留
    check(page.evaluate(f'() => JSON.stringify(sanitize(treeData)).indexOf("{wrong_id}") === -1'),
          '数据中不残留被删节点')
    # 撤销完整恢复
    page.evaluate('undo()')
    page.wait_for_timeout(200)
    check(page.evaluate(f'() => !!findNode("{wrong_id}")')
          and page.evaluate("() => findParent('b1a1').id") == wrong_id,
          '撤销恢复错误父辈（回到删除前结构）')
    page.evaluate('undo()')   # 再撤销一步回到加父辈之前
    page.wait_for_timeout(200)
    check(page.evaluate("() => findParent('b1a1').id") == 'b1a', '连撤两步回到加父辈之前')
    # 无后代的人：保持一句话确认（不出现二选一）
    leaf = page.evaluate("() => { const n = findNode('b1a2'); return n && (!n.children || !n.children.length); }")
    check(leaf, '前置：b1a2 是叶节点')
    page.locator('.node[data-id="b1a2"] .node-label').click()
    page.keyboard.press('Delete')
    page.wait_for_timeout(250)
    check(page.locator('#__ucfModal').get_attribute('class') == 'open'
          and page.locator('#__uddModal').get_attribute('class') == '',
          '叶节点删除保持单步确认，不出现二选一')
    confirm_page(page, True)
    page.wait_for_timeout(150)
    check(not page.evaluate("() => !!findNode('b1a2')"), '叶节点确认后删除')
    check(not errs, '无 JS 错误', str(errs))
    ctx.close()


@testcase
def t_touch_double_tap_spouse_and_name(b):
    """网友反馈：手机上双击配偶没反应。v15.57：触屏轻点配偶即进编辑；
       双击窗口放宽到 450ms（慢节奏双击也生效）；弹窗打开后 350ms 内的
       第二下点击不会把刚弹出的编辑框关掉。"""
    ctx, page, errs, cons = fresh_page(b, 390, 844, touch=True, mobile=True)
    goto(page)
    page.evaluate("setTargetScale(1.8)")
    page.wait_for_timeout(400)
    sp = page.locator('.node[data-id="b1"] .sp[data-sp="0"]').first
    sp.scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    box = sp.bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.touchscreen.tap(x, y)
    page.wait_for_timeout(300)
    title = page.locator("#__uipTitle").text_content()
    check("配偶" in title, "触屏轻点配偶 → 改配偶弹窗", title)
    page.evaluate("document.getElementById('__uipCancel').click()")
    page.wait_for_timeout(150)
    # 快速双击配偶：第二下落在遮罩上，不能把刚打开的弹窗瞬间关掉
    page.touchscreen.tap(x, y)
    page.wait_for_timeout(120)
    page.touchscreen.tap(x, y)
    page.wait_for_timeout(150)
    title_d = page.locator("#__uipTitle").text_content()
    check(page.locator("#__uipModal").get_attribute("class") == "open"
          and "配偶" in title_d, "双击的第二下不会关掉刚打开的编辑框", title_d)
    page.evaluate("document.getElementById('__uipCancel').click()")
    page.wait_for_timeout(150)
    nm = page.locator('.node[data-id="b2"] .node-label').first
    nm.scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    nb = nm.bounding_box()
    nx, ny = nb["x"] + nb["width"] / 2, nb["y"] + nb["height"] / 2
    page.touchscreen.tap(nx, ny)
    page.wait_for_timeout(80)
    page.touchscreen.tap(nx, ny)
    page.wait_for_timeout(300)
    title2 = page.locator("#__uipTitle").text_content()
    check("修改姓名" in title2, "触屏双轻点名字 → 改名弹窗", title2)
    page.evaluate("document.getElementById('__uipCancel').click()")
    page.wait_for_timeout(100)
    # 慢节奏双击（间隔 ~400ms，超出旧 320ms 窗口）也要生效
    page.touchscreen.tap(nx, ny)
    page.wait_for_timeout(400)
    page.touchscreen.tap(nx, ny)
    page.wait_for_timeout(300)
    title3 = page.locator("#__uipTitle").text_content()
    check("修改姓名" in title3, "400ms 间隔的慢双击 → 改名弹窗", title3)
    page.evaluate("document.getElementById('__uipCancel').click()")
    page.wait_for_timeout(100)
    # 轻点选中 → 操作条「⋯」→ 菜单 → 删除（v15.58 长按改为拾起拖动，菜单入口迁移）
    dlg = DialogRecorder(page)
    card = page.locator('.node[data-id="b1"]').first
    card.scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    page.evaluate("""() => {
      const v = document.getElementById('viewport');
      const r = document.querySelector('.node[data-id="b1"]').getBoundingClientRect();
      v.scrollLeft += r.left + r.width / 2 - innerWidth / 2;
      v.scrollTop += r.top + r.height / 2 - innerHeight / 2;
    }""")
    page.wait_for_timeout(150)
    page.locator('.node[data-id="b1"] .node-label').click()
    page.wait_for_timeout(200)
    check(page.locator('#__selBar').count() == 1, "触屏轻点选中出现操作条")
    page.locator('#__selBar .sa-btn[title*="更多"]').click()
    page.wait_for_timeout(200)
    check(page.evaluate("() => document.getElementById('__ctxMenu').style.display === 'block'"),
          "操作条「⋯」打开成员菜单")
    page.locator("#__ctxMenu .mi", has_text="删除").click()
    delete_choice(page, "all")
    page.wait_for_timeout(200)
    check(not page.evaluate("!!window.__ZP.findNode('b1')"), "udd 确认后整支删除")
    check(dlg.count() == 0, "手机路径同样不弹系统 confirm", str(dlg.records))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


if __name__ == "__main__":
    import sys as _sys
    ok = run_module(_sys.modules[__name__], "t_edit 菜单/弹窗键盘/配偶/删除撤销")
    sys.exit(0 if ok else 1)
