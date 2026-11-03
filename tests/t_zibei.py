# -*- coding: utf-8 -*-
"""字辈定代（v15.44 结构优先）：父子链是唯一真值（堂/亲兄弟必然同代）；
名字含「本代」字辈字=蓝色印证；含「其他代」=照常显示世系代数 + tooltip 提示核对。
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
def t_zibei_ancestors_before_first_character(b):
    """字辈从第四层开始：祖辈相对序 -2/-1/0 不截断，零也有行标。"""
    ctx, page, errs, cons = fresh_page(b)
    goto_zibei(page)
    original = page.evaluate("""() => {
      const names = ['周甲', '周乙', '周丙', '周勤', '周修', '周昭'];
      let children = [];
      for (let i = names.length - 1; i >= 0; i--)
        children = [{id: 'a' + i, name: names[i], spouses: [], expanded: true, children}];
      treeData.zibei = ['勤', '修', '昭']; treeData.children = children;
      cfg.genBase = 1; cfg.vertical = true; render();
      return JSON.stringify(sanitize(treeData));
    }""")
    relative = page.evaluate("Array.from(computeGenerations().values(), g => g.gen)")
    check(relative == [-2, -1, 0, 1, 2, 3], "保留完整相对代序", str(relative))
    expected = ['字辈前3代', '字辈前2代', '字辈前1代', '1代·勤', '2代·修', '3代·昭']
    actual = [chip_of(page, f'a{i}').inner_text() for i in range(6)]
    check(actual == expected, "基准前祖辈用人话表示", str(actual))
    rows = page.locator('.vrow').all_text_contents()
    check(rows == ['字辈前三代', '字辈前二代', '字辈前一代', '一代·勤', '二代·修', '三代·昭'],
          "祖辈竖排行标完整，零索引不丢失", str(rows))
    for i in range(3):
        tip = chip_of(page, f'a{i}').get_attribute('title')
        check(expected[i] in tip and not _re.search(r'(?:第?-\d+代|0代|undefined)', tip),
              "祖辈 tooltip 无零或负代数", tip)
    stats = page.locator('#statsChip').inner_text()
    check('字辈前3代–3代' in stats and '6 代' in stats, "统计保留祖辈范围与六代层数", stats)
    check(page.evaluate("[numToCn(-2), numToCn(0), numToCn(110)]") == ['负二', '零', '一百一十'],
          "汉字数转换支持负数与超过百世")
    page.evaluate("cfg.genBase = 10; render()")
    actual = [chip_of(page, f'a{i}').inner_text() for i in range(6)]
    check(actual == ['7世', '8世', '9世', '10世·勤', '11世·修', '12世·昭'],
          "勤从十世起，三祖辈依次七八九世", str(actual))
    check(page.evaluate("JSON.stringify(sanitize(treeData))") == original,
          "换算与布局不改族谱原始数据")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_zibei_conflict_hint(b):
    """名字含其他代字辈字：以世系为准显示，tooltip 提示核对（不再被字辈带偏）"""
    ctx, page, errs, cons = fresh_page(b)
    goto_zibei(page)
    # 把 周厚翰（名字含「厚」=字辈14）挂到 王大锤(w1) 名下 → 世系=第2代
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
    # 字辈校准偏移由全树票选决定（本夹具=10：勤善11·厚翰14），挂到 w1 下后世系=2+10=12
    check(txt == "12代·修", "冲突时以世系为准：显示12代·修（不再被「厚」带偏到14代）", txt)
    tip = chip_of(page, "z4").get_attribute("title")
    check("「厚」" in tip and "14" in tip and "核对" in tip, "tooltip 提示名字与世系不符请核对", tip)
    # 同样被挂过去的 z1 分支不受影响（票选偏移对全树一致）
    check(chip_of(page, "z1").inner_text().replace("\n", "") == "11代·勤", "整体校准不破坏其他成员",
          chip_of(page, "z1").inner_text())
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_zibei_cousins_always_same_gen(b):
    """网友反馈回归：堂兄弟（父亲是亲兄弟）必须同代——
    一支祖先名字偶然含其他代字辈字，不得把整支带偏"""
    ctx, page, errs, cons = fresh_page(b)
    data = {
        "id": "root", "name": "始祖", "spouses": [], "expanded": True,
        "zibei": list("文成高见"),
        "children": [
            { "id": "a", "name": "赵文", "spouses": [], "expanded": True, "children": [
                { "id": "a1", "name": "赵高", "spouses": [], "expanded": True, "children": [
                    { "id": "a1a", "name": "赵铁柱", "spouses": [], "expanded": True, "children": [] } ] },
                { "id": "a2", "name": "赵二狗", "spouses": [], "expanded": True, "children": [] } ] },
            { "id": "b", "name": "赵武", "spouses": [], "expanded": True, "children": [
                { "id": "b1", "name": "赵三", "spouses": [], "expanded": True, "children": [
                    { "id": "b1a", "name": "赵狗剩", "spouses": [], "expanded": True, "children": [] } ] } ] }
        ]
    }
    app = open(LOCAL_HTML, encoding="utf-8").read()
    sample_json = _json.dumps(data, ensure_ascii=False, indent=2)
    import re as _re2
    fixture, n = _re2.subn(
        r'(<script id="__treeData" type="application/json">)[\s\S]*?(\n</script>)',
        lambda m: m.group(1) + "\n" + sample_json + "\n" + m.group(2),
        app, count=1)
    assert n == 1
    path = os.path.join(LOCAL_OUT, "fixture_cousin_gen.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(fixture)
    page.goto(OUT_DIR + "/fixture_cousin_gen.html")
    page.wait_for_load_state("domcontentloaded")
    page.evaluate("() => { localStorage.clear(); }")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_function("document.querySelectorAll('.node').length >= 8")
    # 第二代：赵高（名字含「高」=第3字，曾被带偏到3代）与堂弟赵三 → 必须同代
    check(chip_of(page, "a1").inner_text().replace("\n", "") == "2代·成", "误命中者按世系显示 2代", chip_of(page, "a1").inner_text())
    check(chip_of(page, "a1").inner_text() == chip_of(page, "b1").inner_text(), "堂兄弟同代（第二代）")
    # 第三代堂兄弟：赵铁柱 vs 赵狗剩 → 必须同代
    check(chip_of(page, "a1a").inner_text() == chip_of(page, "b1a").inner_text() == "3代·高",
          "堂兄弟同代（第三代）", chip_of(page, "a1a").inner_text())
    # 误命中者的 tooltip 带核对提示；一致者仍是蓝色印证
    tip = chip_of(page, "a1").get_attribute("title")
    check("「高」" in tip and "核对" in tip, "误命中 tooltip 提示核对", tip)
    check("match" in (chip_of(page, "a").get_attribute("class") or ""), "名字与世系一致者保持蓝色印证",
          chip_of(page, "a").get_attribute("class"))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_zibei_tie_prefers_non_negative_shift(b):
    """票数并列时不得把整谱推到「字辈前」：早期名字含后代字辈字、后辈名字含前代字辈字，
    两种解释同分，应取非负偏移（3代·昭 / 4代），而不是 0/1 代。"""
    ctx, page, errs, cons = fresh_page(b)
    data = {
        "id": "root", "name": "家族族谱", "spouses": [], "expanded": True,
        "zibei": ["勤", "修", "昭", "厚"],
        "children": [
            { "id": "a", "name": "周昭", "spouses": [], "expanded": True, "children": [
                { "id": "b", "name": "周勤", "spouses": [], "expanded": True, "children": [] } ] }
        ]
    }
    app = open(LOCAL_HTML, encoding="utf-8").read()
    sample_json = _json.dumps(data, ensure_ascii=False, indent=2)
    fixture, n = _re.subn(
        r'(<script id="__treeData" type="application/json">)[\s\S]*?(\n</script>)',
        lambda m: m.group(1) + "\n" + sample_json + "\n" + m.group(2),
        app, count=1)
    assert n == 1
    path = os.path.join(LOCAL_OUT, "fixture_zibei_tie.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(fixture)
    page.goto(OUT_DIR + "/fixture_zibei_tie.html")
    page.wait_for_load_state("domcontentloaded")
    page.evaluate("() => { localStorage.clear(); }")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    check(chip_of(page, "a").inner_text().replace("\n", "") == "3代·昭",
          "并列时取非负偏移：周昭=3代·昭", chip_of(page, "a").inner_text())
    check(chip_of(page, "b").inner_text().replace("\n", "") == "4代·厚",
          "后代按世系：周勤=4代·厚", chip_of(page, "b").inner_text())
    page.evaluate("() => { cfg.genBase = 10; render(); }")
    check(chip_of(page, "a").inner_text().replace("\n", "") == "12世·昭",
          "基准10时同偏移换算：12世·昭", chip_of(page, "a").inner_text())
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_zibei_rescued_draft_no_injection(b):
    """v15.31 新契约：旧草稿（无 zibei）成员更多而胜出播种时，成员被恢复，
    但字辈表不再从内嵌/其他草稿「补齐」——内嵌已是通用演示数据，注入即污染"""
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
    check(page.evaluate('!!window.__ZP.findNode("old1")'), "旧草稿成员胜出播种")
    zb = page.evaluate("window.__ZP.data.zibei")
    check(not zb, "字辈表不被演示数据注入（保持空）", str(zb))
    check(page.locator('.node[data-id="z1"] .gen').count() == 0, "无字辈表则无世代角标")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_zibei_cleared_stays_cleared(b):
    """v15.31 回归：用户在谱序里主动清空字辈表并保存后，刷新不得被演示字辈「复活」"""
    ctx, page, errs, cons = fresh_page(b)
    goto_zibei(page)
    check(page.evaluate("window.__ZP.data.zibei.length") == 40, "初始有 40 代字辈表")
    # 打开谱序（点左上角谱名品牌），清空字辈输入框，保存
    page.evaluate("openClan()")
    page.wait_for_timeout(150)
    page.locator("#__clZibei").fill("")
    page.locator("#__clSave").click()
    page.wait_for_timeout(250)
    zb_after = page.evaluate("window.__ZP.data.zibei")
    check(not zb_after, "保存清空后数据中已无字辈表", str(zb_after))
    # 刷新：浏览器数据优先且不再被补齐 → 字辈表保持空
    page.reload(); page.wait_for_load_state("domcontentloaded")
    zb_reload = page.evaluate("window.__ZP.data.zibei")
    check(not zb_reload, "刷新后字辈表保持清空（不被演示数据复活）", str(zb_reload))
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
    page.locator('#btnHelp').click()
    page.locator('#__ctxMenu .mi', has_text='帮助 / 快捷键').click()
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
