# -*- coding: utf-8 -*-
"""拖动过继：把一个人（连同整支后代）拖到另一张卡片上，成为其子女。
悬停 0.4s 确认目标；自己的后代红框拒绝（防成环）；折叠目标自动展开。"""
from helper import *


def drag_onto(page, src_sel, dst_sel, dwell_ms=560):
    """真实鼠标：从 src 卡片中心拖到 dst 卡片中心并悬停 dwell_ms 后松手"""
    s = page.locator(src_sel).bounding_box()
    d = page.locator(dst_sel).bounding_box()
    sx, sy = s["x"] + s["width"] / 2, s["y"] + s["height"] / 2
    tx, ty = d["x"] + d["width"] / 2, d["y"] + d["height"] / 2
    page.mouse.move(sx, sy)
    page.mouse.down()
    for i in range(1, 11):
        page.mouse.move(sx + (tx - sx) * i / 10, sy + (ty - sy) * i / 10)
    page.wait_for_timeout(dwell_ms)          # 悬停触发过继目标
    page.mouse.up()
    page.wait_for_timeout(450)               # 过 suppressClickUntil


@testcase
def t_reparent_basic_and_undo(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    # 把 雷茂勋(b2a，连同其子 周厚翰) 拖到 雷俊(b1b) 卡片上 → 成为雷俊的子女
    drag_onto(page, '.node[data-id="b2a"] .node-label', '.node[data-id="b1b"] .node-label')
    kids = page.evaluate('window.__ZP.findNode("b1b").children.map(c=>c.name)')
    check("雷茂勋" in kids, "过继成功：雷茂勋到了雷俊名下", str(kids))
    oldsibs = page.evaluate('window.__ZP.findNode("b2").children.map(c=>c.name)')
    check("雷茂勋" not in oldsibs, "已从原父亲少群名下移除", str(oldsibs))
    grand = page.evaluate('window.__ZP.findNode("b2a").children.map(c=>c.name)')
    check(grand == ["周厚翰"], "整支后代跟随迁移", str(grand))
    # 代数联动：root→b1→b1b→b2a→b2a1 = 4 代
    stats = page.locator("#statsChip").inner_text().replace("\n", "")
    check("4 代" in stats, "统计条代数更新为 4 代", stats)
    # 整支可见（目标自动展开）
    vis = page.locator('.node[data-id="b2a1"]').is_visible()
    check(vis, "迁移后的孙辈在画布可见")
    # 排行角标：雷俊名下 [周亿树, 雷茂勋] → 雷茂勋 是「次」
    badge = page.locator('.node[data-id="b2a"] .rank').inner_text()
    check(badge == "次", "新同辈组排行角标更新", badge)
    # 撤销整支回到原位
    page.keyboard.press("Control+z")
    page.wait_for_timeout(200)
    back = page.evaluate('window.__ZP.findNode("b2").children.map(c=>c.name)')
    check("雷茂勋" in back, "撤销后回到少群名下", str(back))
    stats2 = page.locator("#statsChip").inner_text().replace("\n", "")
    check("3 代" in stats2, "撤销后代数恢复 3 代", stats2)
    check(dlg.count() == 0, "全程零原生对话框", str(dlg.records))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_reparent_reject_cycle(b):
    """把分支拖到自己后代名下：红框拒绝，数据不变"""
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    drag_onto(page, '.node[data-id="b1"] .node-label', '.node[data-id="b1a"] .node-label')
    parent = page.evaluate('window.findParent("b1")?.id || "root"')
    check(parent == "root", "成环过继被拒绝，b1 仍在第一代", str(parent))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_reparent_onto_collapsed_expands(b):
    """目标是折叠分支：过继后自动展开看到结果"""
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    # 先折叠 b1
    page.locator('.node[data-id="b1"] .quick-add').click()
    page.locator('#__ctxMenu .mi', has_text="折叠").click()
    page.wait_for_timeout(200)
    check(page.locator('.node[data-id="b1"] .fold').count() == 1, "b1 已折叠")
    # 把 b3a(雷波美) 拖到折叠的 b1 上
    drag_onto(page, '.node[data-id="b3a"] .node-label', '.node[data-id="b1"] .node-label')
    kids = page.evaluate('window.__ZP.findNode("b1").children.map(c=>c.name)')
    check(any("雷波美" in k for k in kids), "过继进折叠分支", str(kids))
    expanded = page.evaluate('window.__ZP.findNode("b1").expanded')
    check(expanded is True, "目标分支自动展开", str(expanded))
    check(page.locator('.node[data-id="b3a"]').is_visible(), "画布上可见新挂的成员")
    check(page.locator('.node[data-id="b1"] .fold').inner_text().replace("\n", "") == "▾",
          "展开后为快捷折叠钮")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_reparent_single_child_draggable(b):
    """独子也能拖（v14.2 放开同辈≥2 限制）：把独子周厚翰过继给雷旭"""
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    n_before = page.evaluate('window.__ZP.findNode("b2a").children.length')
    check(n_before == 1, "周厚翰是独子", str(n_before))
    drag_onto(page, '.node[data-id="b2a1"] .node-label', '.node[data-id="b3"] .node-label')
    kids = page.evaluate('window.__ZP.findNode("b3").children.map(c=>c.name)')
    check("周厚翰" in kids, "独子过继成功：周厚翰到雷旭名下", str(kids))
    empty = page.evaluate('window.__ZP.findNode("b2a").children.length')
    check(empty == 0, "原分支变为无后", str(empty))
    # 独子左右拖仍是普通换位：过继后 [雷波美, 周厚翰]，把雷波美向右拖 → 移到周厚翰之后
    s = page.locator('.node[data-id="b3a"] .node-label').bounding_box()
    cx, cy = s["x"] + s["width"] / 2, s["y"] + s["height"] / 2
    page.mouse.move(cx, cy); page.mouse.down()
    page.mouse.move(cx + 150, cy, steps=10)    # 越过右邻（周厚翰）中心 → 换到其右
    page.mouse.up()
    page.wait_for_timeout(450)
    order = page.evaluate('window.__ZP.findNode("b3").children.map(c=>c.name)')
    check(order == ["周厚翰", "雷波美（?）"], "普通拖拽换位仍正常", str(order))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


if __name__ == "__main__":
    import sys as _sys
    ok = run_module(_sys.modules[__name__], "t_reparent 拖动过继")
    sys.exit(0 if ok else 1)
