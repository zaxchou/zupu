# -*- coding: utf-8 -*-
"""首次运行向导（v15.30）：内嵌 demo 种子自动弹三选一；
先看示例 / 从空白开始 两条路径与持久化。独立夹具。"""
from helper import *
import sys as _sys
import os
import json as _json
import re as _re
import os as _os

DEMO = {
    "id": "root", "name": "家族族谱", "spouses": [], "expanded": True, "demo": True,
    "clan": {"ming": "家族族谱（示例）", "tang": ""},
    "zibei": ["德", "承", "传", "世", "泽"],
    "children": [
        {"id": "w1", "name": "赵德祖", "spouses": ["钱婉贞"], "expanded": True, "children": [
            {"id": "w2", "name": "赵承业", "spouses": [], "expanded": True, "children": []}]}
    ]
}


def wizard_fixture_url():
    app = open(LOCAL_HTML, encoding="utf-8").read()
    sample_json = _json.dumps(DEMO, ensure_ascii=False, indent=2)
    fixture, n = _re.subn(
        r'(<script id="__treeData" type="application/json">)[\s\S]*?(\n</script>)',
        lambda m: m.group(1) + "\n" + sample_json + "\n" + m.group(2),
        app, count=1)
    assert n == 1
    _os.makedirs(LOCAL_OUT, exist_ok=True)
    path = os.path.join(LOCAL_OUT, "fixture_wizard.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(fixture)
    return OUT_DIR + "/fixture_wizard.html"


def goto_wizard(page):
    page.goto(wizard_fixture_url())
    page.wait_for_load_state("domcontentloaded")
    page.evaluate("() => { localStorage.clear(); }")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    return page


@testcase
def t_wizard_demo_path(b):
    ctx, page, errs, cons = fresh_page(b)
    goto_wizard(page)
    # demo 种子 → 向导自动弹出
    check(page.locator("#__wizModal").is_visible(), "首次载入自动弹欢迎向导")
    # 先看看示例：数据保留、demo 标记清除
    page.locator('#__wizModal [data-wiz="demo"]').click()
    page.wait_for_timeout(150)
    check(not page.locator("#__wizModal").is_visible(), "选择后向导关闭")
    check(page.evaluate("window.__ZP.data.demo") is False, "demo 标记清除")
    check(page.evaluate('window.__ZP.findNode("w1").name') == "赵德祖", "示例数据保留")
    # 刷新后不再弹
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    check(not page.locator("#__wizModal").is_visible(), "刷新后不再弹向导")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_wizard_blank_start(b):
    ctx, page, errs, cons = fresh_page(b)
    goto_wizard(page)
    # 从空白开始：谱名/堂号生效
    page.fill("#__wizMing", "李氏族谱")
    page.fill("#__wizTang", "陇西堂")
    page.locator("#__wizGo").click()
    page.wait_for_timeout(200)
    check(page.locator(".node").count() == 1, "空白族谱仅根节点", str(page.locator(".node").count()))
    check(page.evaluate('window.__ZP.data.name') == "李氏族谱", "根名=谱名", page.evaluate('window.__ZP.data.name'))
    check(page.evaluate('window.__ZP.data.clan.tang') == "陇西堂", "堂号写入", page.evaluate('window.__ZP.data.clan.tang'))
    check(page.evaluate("window.__ZP.data.demo") is None, "demo 标记移除")
    check(page.locator("#__puName").inner_text() == "李氏族谱", "顶栏谱名同步", page.locator("#__puName").inner_text())
    # 刷新持久，且不再弹向导
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    check(page.locator(".node").count() == 1, "空白族谱刷新持久")
    check(not page.locator("#__wizModal").is_visible(), "不再弹向导")
    # 之后正常编辑可用：＋ 添加第一代
    dlg = DialogRecorder(page)
    dlg.queue("prompt", "李元怙")   # prompt 随点击同步弹出，须先入队
    page.locator('.node .quick-add').first.click()
    page.locator("#__ctxMenu .mi", has_text="第一代").click()
    page.wait_for_timeout(150)
    check(page.locator(".node").count() == 2, "空白谱可正常添加成员")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


def _run():
    ok = run_module(_sys.modules[__name__], "t_wizard 首次运行向导")
    _sys.exit(0 if ok else 1)


if __name__ == "__main__":
    _run()
