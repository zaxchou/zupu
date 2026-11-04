# -*- coding: utf-8 -*-
"""世祖与字辈独立：父子链决定世祖（堂/亲兄弟必然同世）；
字辈从设置世数起用，名字只作印证；本辈已有字辈时误命中其他字才提示核对。
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
    page.evaluate("treeData.zibei = ['勤', '修', '昭', '厚']; render()")
    for i, zi in enumerate('勤修昭厚', 1):
        check(chip_of(page, f'z{i}').inner_text() == f'{i}世', '世祖只按父子层级排列')
        check(page.locator(f'.node[data-id="z{i}"] .zibei').inner_text() == f'辈序{i}·{zi}',
              '字辈单独显示对应辈序')
    # 蓝色=字辈匹配，灰色=推算
    cls_match = chip_of(page, "z1").get_attribute("class")
    cls_infer = chip_of(page, "z2").get_attribute("class")
    check("match" in cls_match and "match" not in (cls_infer or ""), "匹配/推算样式区分", f"{cls_match}/{cls_infer}")
    # tooltip 语义
    tip2 = chip_of(page, "z2").get_attribute("title")
    check("推算" in tip2 and "2世" in tip2 and '辈序2·修' in tip2, "推算角标 tooltip 说明来源", tip2)
    tip1 = chip_of(page, "z1").get_attribute("title")
    check("字辈「勤」" in tip1 and "缺一代" not in tip1, "匹配角标 tooltip 无冲突警告", tip1)
    # 统计条带字辈范围
    stats = page.locator("#statsChip").inner_text().replace("\n", "")
    check("世祖第1–4世" in stats and '辈序1–4' in stats, "统计条分列世祖与辈序范围", stats)
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_zibei_ancestors_before_first_character(b):
    """字辈从第四世开始，前三世辈序留空，世祖从一世起。"""
    ctx, page, errs, cons = fresh_page(b)
    goto_zibei(page)
    original = page.evaluate("""() => {
      const names = ['周甲', '周乙', '周丙', '周勤', '周修', '周昭'];
      let children = [];
      for (let i = names.length - 1; i >= 0; i--)
        children = [{id: 'a' + i, name: names[i], spouses: [], expanded: true, children}];
      treeData.zibei = ['勤', '修', '昭']; treeData.children = children;
      cfg.zibeiStart = 4; cfg.vertical = true; render();
      return JSON.stringify(sanitize(treeData));
    }""")
    relative = page.evaluate("Array.from(computeGenerations().values(), g => g.gen)")
    check(relative == [1, 2, 3, 4, 5, 6], "世祖从第一层成员按一世起", str(relative))
    expected = ['1世', '2世', '3世', '4世', '5世', '6世']
    actual = [chip_of(page, f'a{i}').inner_text() for i in range(6)]
    check(actual == expected, "基准前祖辈用人话表示", str(actual))
    rows = page.locator('.vrow.row-gen').all_text_contents()
    zrows = page.locator('.vrow.row-zibei').all_text_contents()
    check(rows == ['一世', '二世', '三世', '四世', '五世', '六世'],
          "竖排行标列只显示世祖", str(rows))
    check(zrows == ['辈序一·勤', '辈序二·修', '辈序三·昭'],
          "辈序独立成列，起用前不显示", str(zrows))
    for i in range(3):
        tip = chip_of(page, f'a{i}').get_attribute('title')
        check(expected[i] in tip and not _re.search(r'(?:第?-\d+代|0代|undefined)', tip),
              "祖辈 tooltip 无零或负代数", tip)
    stats = page.locator('#statsChip').inner_text()
    check('世祖第1–6世' in stats and '辈序1–3' in stats and '6 代' in stats, "统计分列世祖与辈序范围", stats)
    check(page.evaluate("[numToCn(-2), numToCn(0), numToCn(110)]") == ['负二', '零', '一百一十'],
          "汉字数转换支持负数与超过百世")
    page.evaluate("cfg.genBase = 10; render()")
    actual = [chip_of(page, f'a{i}').inner_text() for i in range(6)]
    check(actual == expected, "起用世数改十世，不改变世祖编号", str(actual))
    check(page.locator('.node[data-id="a3"] .zibei').text_content() == '', '十世之前辈序为空')
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
    check(txt == "2世", "冲突时仍按父子结构显示第二世", txt)
    check(page.locator('.node[data-id="z4"] .zibei').inner_text() == '辈序2·士', '误命中字辈不改变辈序')
    tip = chip_of(page, "z4").get_attribute("title")
    check("「厚」" in tip and "14" in tip and "核对" in tip, "tooltip 提示名字与世系不符请核对", tip)
    # 其他分支保持原世祖编号。
    check(chip_of(page, "z1").inner_text().replace("\n", "") == "1世", "误命中不改变其他成员世祖", 
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
    check(chip_of(page, "a1").inner_text() == "2世", "误命中者按世系显示第二世", chip_of(page, "a1").inner_text())
    check(page.locator('.node[data-id="a1"] .zibei').inner_text() == '辈序2·成', '辈序独立按表取字')
    check(chip_of(page, "a1").inner_text() == chip_of(page, "b1").inner_text(), "堂兄弟同代（第二代）")
    # 第三代堂兄弟：赵铁柱 vs 赵狗剩 → 必须同代
    check(chip_of(page, "a1a").inner_text() == chip_of(page, "b1a").inner_text() == "3世",
          "堂兄弟同代（第三代）", chip_of(page, "a1a").inner_text())
    # 误命中者的 tooltip 带核对提示；一致者仍是蓝色印证
    tip = chip_of(page, "a1").get_attribute("title")
    check("「高」" in tip and "核对" in tip, "误命中 tooltip 提示核对", tip)
    check("match" in (chip_of(page, "a").get_attribute("class") or ""), "名字与世系一致者保持蓝色印证",
          chip_of(page, "a").get_attribute("class"))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_zibei_names_never_shift_generation(b):
    """名字含其他辈字，不得使任何世祖编号偏移。"""
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
    check(chip_of(page, "a").inner_text() == "1世", "周昭始终为一世祖")
    check(chip_of(page, "b").inner_text() == "2世", "子女为二世祖")
    page.evaluate("() => { cfg.genBase = 10; render(); }")
    check(chip_of(page, "a").inner_text() == "1世", "字辈从十世起不改变世祖")
    check(page.locator('.node[data-id="a"] .zibei').text_content() == '', '起用之前字辈为空')
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
    check(chip_of(page, 'z1').inner_text() == '1世', "无字辈表仍显示世祖编号")
    check(page.locator('.node[data-id="z1"] .zibei').text_content() == '', '无表字辈为空')
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
