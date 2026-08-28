# -*- coding: utf-8 -*-
"""v15.8：大族谱性能 + 搜索自动展开折叠支"""
from helper import *
import json as _json
import os as _os


@testcase
def t_search_auto_expands_collapsed(b):
    """全折叠后搜索折叠支内成员：自动展开那一支、命中定位"""
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    page.locator("#btnView").click()
    page.locator('#__ctxMenu .mi', has_text="全折叠").click()
    page.wait_for_timeout(200)
    check(page.locator(".node").count() == 1, "全折叠后只剩根")
    page.keyboard.press("Control+f")
    page.locator("#sbInput").fill("周新洋")
    page.wait_for_timeout(600)
    n = page.locator(".node").count()
    check(n > 1, "命中折叠支自动展开", f"nodes={n}")
    active = page.locator(".node.hit-active")
    check(active.count() == 1 and "周新洋" in active.inner_text(), "命中并高亮定位",
          active.inner_text() if active.count() else "无")
    check(page.evaluate("window.__ZP.findNode('b1').expanded") is True, "祖先链已展开")
    # 结果列表点选 → 居中选中
    page.locator("#sbList .sb-item").first.click()
    page.wait_for_timeout(400)
    check(page.locator(".node.selected").count() == 1, "点选结果后成员被选中")
    check(dlg.count() == 0, "零弹窗", str(dlg.records))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_perf_big_tree_render(b):
    """大族谱性能：约 680 位成员渲染 < 2.5s，交互元素数量受控"""
    ctx, page, errs, cons = fresh_page(b)
    goto(page)

    def gen_big():
        root = {"id": "root", "name": "家族族谱", "spouses": [], "expanded": True,
                "zibei": list("多士敬宏毓英资衍芳绪勤修昭厚德翊赞耀明良攸子崇伯钦淑宪绍懿徽植本宗永健嗣典运开祥"),
                "children": []}
        def add(parent, depth, path):
            if depth == 0:
                return
            kid = {"id": path, "name": "成员" + path, "spouses": ["配" + path],
                   "expanded": True, "birth": "", "death": "", "note": "", "children": []}
            parent["children"].append(kid)
            for i in range(4):
                add(kid, depth - 1, path + chr(97 + i))
        for i in range(8):
            add(root, 4, "g%d" % i)
        return root

    page.evaluate("d => { window.__ZP.data = d; }", gen_big())
    page.wait_for_timeout(200)
    n = page.locator(".node").count()
    check(n == 681, "680 位成员 + 根全部渲染", str(n))
    t = page.evaluate("() => { const t0 = performance.now(); render(); return performance.now() - t0; }")
    check(t < 2500, "680 人渲染耗时可接受", f"{t:.0f}ms")
    paths = page.evaluate("document.querySelectorAll('#linesG path').length")
    check(paths == 1, "连线合并为单条 path", str(paths))
    # 大树下搜索仍工作
    page.keyboard.press("Control+f")
    page.locator("#sbInput").fill("成员g2a")
    page.wait_for_timeout(400)
    cnt = page.locator("#sbCount").inner_text()
    check(cnt.strip() == "1/21", "大树下搜索计数", cnt)
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()

if __name__ == "__main__":
    import sys as _sys
    ok = run_module(_sys.modules[__name__], "t_perf 大族谱性能")
    sys.exit(0 if ok else 1)
