# -*- coding: utf-8 -*-
"""字辈定代：名字含字辈字=权威；未用字辈按父/同辈推算；冲突提示缺代。
使用独立夹具（fixture_zibei），不影响其他模块的示例数据。"""
from helper import *
import json as _json
import os
import re as _re
import os as _os

ZIBEI = list("多士敬宏毓英资衍芳绪勤修昭厚德翊赞耀明良攸子崇伯钦淑宪绍懿徽植本宗永健嗣典运开祥")


def zibei_fixture_url():
    """构造带字辈的小树：
    root → [周勤善(勤11) → 周少群(推12) → 周豪(推13) → 周厚翰(厚14,match)],
            [王大锤(无匹配,无锚点兄弟→世系推算)]"""
    data = {
        "id": "root", "name": "家族族谱", "spouses": [], "expanded": True,
        "zibei": ZIBEI,
        "children": [
            { "id": "z1", "name": "周勤善", "spouses": [], "expanded": True, "children": [
                { "id": "z2", "name": "周少群", "spouses": [], "expanded": True, "children": [
                    { "id": "z3", "name": "周豪", "spouses": [], "expanded": True, "children": [
                        { "id": "z4", "name": "周厚翰", "spouses": [], "expanded": True, "children": [] } ] } ] } ] },
            { "id": "w1", "name": "王大锤", "spouses": [], "expanded": True, "children": [] },
        ]
    }
    app = open(LOCAL_HTML, encoding="utf-8").read()
    sample_json = _json.dumps(data, ensure_ascii=False, indent=2)
    import re as _re
    fixture, n = _re.subn(
        r'(<script id="__treeData" type="application/json">)[\s\S]*?(\n</script>)',
        lambda m: m.group(1) + "\n" + sample_json + "\n" + m.group(2),
        app, count=1)
    assert n == 1
    _os.makedirs(LOCAL_OUT, exist_ok=True)
    path = os.path.join(LOCAL_OUT, "fixture_zibei.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(fixture)
    return OUT_DIR + "/fixture_zibei.html"


def goto_zibei(page):
    url = zibei_fixture_url()
    page.goto(url)
    page.wait_for_load_state("domcontentloaded")
    page.evaluate("() => { localStorage.clear(); }")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    return page


def chip_of(page, nid):
    return page.locator(f'.node[data-id="{nid}"] .gen')


@testcase
def t_zibei_match_and_infer(b):
    ctx, page, errs, cons = fresh_page(b)
    goto_zibei(page)
    check(chip_of(page, "z1").inner_text().replace("\n", "") == "11代·勤", "字辈匹配：勤善=11·勤",
          chip_of(page, "z1").inner_text())
    check(chip_of(page, "z2").inner_text().replace("\n", "") == "12代·修", "父辈推算：少群=12·修（带本代字辈）",
          chip_of(page, "z2").inner_text())
    check(chip_of(page, "z3").inner_text().replace("\n", "") == "13代·昭", "父辈推算：豪=13·昭（带本代字辈）",
          chip_of(page, "z3").inner_text())
    check(chip_of(page, "z4").inner_text().replace("\n", "") == "14代·厚", "字辈匹配：厚翰=14·厚",
          chip_of(page, "z4").inner_text())
    # 蓝色=字辈匹配，灰色=推算
    cls_match = chip_of(page, "z1").get_attribute("class")
    cls_infer = chip_of(page, "z2").get_attribute("class")
    check("match" in cls_match and "match" not in (cls_infer or ""), "匹配/推算样式区分", f"{cls_match}/{cls_infer}")
    # tooltip 语义
    tip2 = chip_of(page, "z2").get_attribute("title")
    check("推算" in tip2 and "12" in tip2, "推算角标 tooltip 说明来源", tip2)
    tip1 = chip_of(page, "z1").get_attribute("title")
    check("字辈「勤」" in tip1 and "缺一代" not in tip1, "匹配角标 tooltip 无冲突警告", tip1)
    # 统计条带字辈范围
    stats = page.locator("#statsChip").inner_text().replace("\n", "")
    check("字辈第11–14代" in stats, "统计条显示字辈代范围", stats)
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_zibei_conflict_hint(b):
    """结构缺代（父链推算与字辈冲突）：以字辈为准，tooltip 提示可能缺一代"""
    ctx, page, errs, cons = fresh_page(b)
    goto_zibei(page)
    # 把 周厚翰 挂到 王大锤(w1) 名下 → 父链推算=第2代，与字辈14冲突
    s = page.locator('.node[data-id="z4"] .node-label').bounding_box()
    d = page.locator('.node[data-id="w1"] .node-label').bounding_box()
    sx, sy = s["x"] + s["width"] / 2, s["y"] + s["height"] / 2
    tx, ty = d["x"] + d["width"] / 2, d["y"] + d["height"] / 2
    page.mouse.move(sx, sy); page.mouse.down()
    for i in range(1, 11):
        page.mouse.move(sx + (tx - sx) * i / 10, sy + (ty - sy) * i / 10)
    page.wait_for_timeout(560)
    page.mouse.up()
    page.wait_for_timeout(450)
    txt = chip_of(page, "z4").inner_text().replace("\n", "")
    check(txt == "14代·厚", "冲突时以字辈为准：仍显示14·厚", txt)
    tip = chip_of(page, "z4").get_attribute("title")
    check("缺一代" in tip and "2" in tip, "tooltip 提示可能缺一代", tip)
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_zibei_rescued_draft_keeps_table(b):
    """v15.1 核心回归：旧草稿（无 zibei）成员更多而胜出播种时，字辈表自动补齐、角标不丢"""
    ctx, page, errs, cons = fresh_page(b)
    data = {
        "id": "root", "name": "家族族谱", "spouses": [], "expanded": True,
        "children": [
            { "id": "z1", "name": "周勤善", "spouses": [], "expanded": True, "children": [] },
            { "id": "w1", "name": "王大锤", "spouses": [], "expanded": True, "children": [] },
            { "id": "old1", "name": "旧稿成员一", "spouses": [], "expanded": True, "children": [] },
            { "id": "old2", "name": "旧稿成员二", "spouses": [], "expanded": True, "children": [] },
            { "id": "old3", "name": "旧稿成员三", "spouses": [], "expanded": True, "children": [] },
            { "id": "old4", "name": "旧稿成员四", "spouses": [], "expanded": True, "children": [] }
        ]
    }
    script = "localStorage.setItem('zupu_tree_data_v3_old', " + _json.dumps(_json.dumps(data, ensure_ascii=False)) + ");"
    page.add_init_script(script)
    goto_zibei(page)
    check(page.evaluate('!!window.__ZP.findNode("old1")'), "旧草稿胜出播种")
    check(page.evaluate("window.__ZP.data.zibei.length") == 40, "字辈表自动补齐 40 代")
    chip = page.locator('.node[data-id="z1"] .gen').inner_text().replace("\n", "")
    check("11代·勤" in chip, "角标恢复显示", chip)
    check("字辈第" in page.locator("#statsChip").inner_text(), "统计条字辈范围恢复")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_zibei_save_persists_and_help_grid(b):
    """字辈表随自动保存固化；备份 json 携带字辈表；帮助弹窗 40 格全表高亮在谱字辈"""
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto_zibei(page)
    zb_in_data = page.evaluate("window.__ZP.data.zibei.length")
    check(zb_in_data == 40, "数据中字辈表 40 代", str(zb_in_data))
    # 自动保存语义：刷新后字辈表仍在（浏览器存储），无需任何保存动作
    page.reload(); page.wait_for_load_state("domcontentloaded")
    check(page.evaluate("window.__ZP.data.zibei.length") == 40, "刷新后字辈表仍在（自动保存）")
    # 备份下载同样携带字辈表
    with page.expect_download() as di:
        page.locator("#btnFile").click()
        page.locator('#__ctxMenu .mi', has_text="备份到文件").click()
    data = _json.loads(open(di.value.path(), encoding="utf-8").read())
    check(data.get("zibei") == ZIBEI, "备份 json 携带完整字辈表")
    # 帮助弹窗网格
    page.locator('button[title="帮助 / 快捷键"]').click()
    page.wait_for_timeout(200)
    total = page.locator("#__zbGrid .zb").count()
    on = page.locator("#__zbGrid .zb.on").count()
    check(total == 40, "字辈全表 40 格", str(total))
    check(on == 2, "高亮已出现的勤/厚 2 格", str(on))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


import re as _re
def _re_search_zibei(html):
    m = _re.search(r'<script id="__treeData" type="application/json">(.*?)</script>', html, _re.S)
    assert m, "saved html missing json"
    return m.group(1).strip()


if __name__ == "__main__":
    import sys as _sys
    ok = run_module(_sys.modules[__name__], "t_zibei 字辈定代")
    sys.exit(0 if ok else 1)
