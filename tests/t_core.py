# -*- coding: utf-8 -*-
"""核心回归：加载、渲染计数、选中、统计条、搜索开合（handoff §9 基线）"""
from helper import *

HTML = r"Z:\BaiduNetdiskWorkspace\myagent-work\zcode\legacy\index.html"


@testcase
def t_load_and_counts(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    check(not errs, "页面无 JS 错误", str(errs))
    # 全展开初始：13 个节点（含根）
    n = page.locator(".node").count()
    check(n == 13, "初始节点数 13", f"got {n}")
    # 配偶小字 7 处
    sp = page.locator(".node-label .sp").count()
    check(sp == 7, "配偶标注数 7", f"got {sp}")
    # 橙色排行角标 7 个（同辈组 4/2/2，note 不标）
    rk = page.locator(".rank:not(.by)").count()
    check(rk == 7, "橙色排行角标 7", f"got {rk}")
    by = page.locator(".rank.by").count()
    check(by == 0, "无出生年时无蓝色角标", f"got {by}")
    # 统计条
    stats = page.locator("#statsChip").inner_text().replace("\n", "")
    check("12" in stats and "7" in stats and "3 代" in stats, "统计条内容正确", stats)
    # 首次载入提示（示例数据来自文件内嵌 → 自动保存就绪）
    toast = page.locator("#__toast").inner_text()
    check("自动保存" in toast, "提示自动保存就绪", toast)
    ctx.close()


@testcase
def t_select_deselect(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    label = page.locator('.node[data-id="b1a1"] .node-label')
    label.click()
    cls = page.locator('.node[data-id="b1a1"]').get_attribute("class")
    check("selected" in cls, "单击选中")
    # 点空白取消（#stage 区域）
    page.mouse.click(60, 620)
    cls2 = page.locator('.node[data-id="b1a1"]').get_attribute("class")
    check("selected" not in (cls2 or ""), "点空白取消选中")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_doubleclick_name_inline_edit(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    lb = page.locator('.node[data-id="b1a1"] .node-label')
    lb.dblclick()
    ce = lb.get_attribute("contenteditable")
    check(ce == "true", "双击进入行内编辑", str(ce))
    page.keyboard.press("Control+a")
    page.keyboard.type("周新涛")
    page.keyboard.press("Enter")
    page.wait_for_timeout(150)
    name = page.evaluate('window.__ZP.findNode("b1a1").name')
    check(name == "周新涛", "行内改名提交", name)
    txt = page.locator('.node[data-id="b1a1"] .node-label').inner_text()
    check(txt.startswith("周新涛"), "改名后 DOM 更新", txt)
    ulen, rlen = page.evaluate("window.__ZP.historyLens()")
    check(ulen >= 1, "改名入撤销栈", f"undo={ulen}")
    check(dlg.count() == 0, "全程零原生对话框", str(dlg.records))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_search_open_close(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    page.keyboard.press("Control+f")
    visible = page.locator("#searchBox").is_visible()
    check(visible, "Ctrl+F 打开搜索面板")
    page.locator("#sbInput").fill("雷")
    page.wait_for_timeout(120)
    cnt = page.locator("#sbCount").inner_text()
    check(cnt.strip() == "1/6", "命中 6 人显示计数", cnt)
    hits = page.locator(".node.hit").count()
    check(hits == 6, "高亮 6 个节点", f"got {hits}")
    act = page.locator(".node.hit-active").count()
    check(act == 1, "唯一活动命中", f"got {act}")
    # 下一个循环
    page.locator("#sbNext").click()
    cnt2 = page.locator("#sbCount").inner_text()
    check(cnt2.strip() == "2/6", "下一个滚动", cnt2)
    page.keyboard.press("Escape")
    page.wait_for_timeout(80)
    check(not page.locator("#searchBox").is_visible(), "Esc 关闭搜索")
    check(page.locator(".node.hit").count() == 0, "关闭清除高亮")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


if __name__ == "__main__":
    import sys as _sys
    ok = run_module(_sys.modules[__name__], "t_core 核心加载/渲染/选中/搜索")
    sys.exit(0 if ok else 1)
