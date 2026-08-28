# -*- coding: utf-8 -*-
"""谱书式显示（v15.12）：性别「女」徽标、配偶谱书式（丁嘉→丁氏嘉）、
世代基准对齐谱书世数（勤=23世→字辈第1字填13）。
使用独立夹具 fixture_book，不影响其他模块的示例数据。"""
from helper import *
import sys as _sys
import os
import json as _json
import re as _re
import os as _os

ZIBEI = list("多士敬宏毓英资衍芳绪勤修昭厚德翊赞耀明良攸子崇伯钦淑宪绍懿徽植本宗永健嗣典运开祥")


def book_fixture_url():
    """带字辈 + 配偶 + 女性成员的小树：
    root → [周勤善(勤11,配翁秀英) → 周少群(女,12,配李平) → 周昭麟(13,配丁嘉)],
            [周昭凤(女,昭13)]"""
    data = {
        "id": "root", "name": "家族族谱", "spouses": [], "expanded": True,
        "zibei": ZIBEI,
        "clan": {
            "ming": "潮阳泗水周氏族谱", "tang": "申锡堂",
            "chain": "濂溪—焘—縯—良卿—宣道—景一—梅叟",
            "yuanzu": "北宋 周敦颐，字茂叔，号濂溪",
            "shizu": "一世祖：承节公讳宣道\n二世祖：朝奉公讳景一",
            "qianzu": "始迁祖：（南宋）宣，字承节",
            "origin": "景一长子梅叟偕三个胞弟卜居潮阳泗水。"
        },
        "children": [
            { "id": "z1", "name": "周勤善", "spouses": ["翁秀英"], "expanded": True, "children": [
                { "id": "z2", "name": "周少群", "spouses": ["李平"], "gender": "f",
                  "expanded": True, "children": [
                    { "id": "z3", "name": "周昭麟", "spouses": ["丁嘉"], "expanded": True, "children": [] } ] } ] },
            { "id": "w1", "name": "周昭凤", "spouses": [], "gender": "f", "expanded": True, "children": [] },
        ]
    }
    app = open(LOCAL_HTML, encoding="utf-8").read()
    sample_json = _json.dumps(data, ensure_ascii=False, indent=2)
    fixture, n = _re.subn(
        r'(<script id="__treeData" type="application/json">)[\s\S]*?(\n</script>)',
        lambda m: m.group(1) + "\n" + sample_json + "\n" + m.group(2),
        app, count=1)
    assert n == 1
    _os.makedirs(LOCAL_OUT, exist_ok=True)
    path = os.path.join(LOCAL_OUT, "fixture_book.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(fixture)
    return OUT_DIR + "/fixture_book.html"


def goto_book(page):
    url = book_fixture_url()
    page.goto(url)
    page.wait_for_load_state("domcontentloaded")
    page.evaluate("() => { localStorage.clear(); }")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    return page


def open_settings(page, base=None, spouse=None):
    page.locator("#btnView").click()
    page.locator("#__ctxMenu .mi", has_text="谱书显示设置").click()
    if base is not None:
        page.fill("#__cfgBase", str(base))
    if spouse is not None:
        page.set_checked("#__cfgSpouse", spouse)


@testcase
def t_spouse_book_display_and_gender_badge(b):
    ctx, page, errs, cons = fresh_page(b)
    goto_book(page)
    # 默认开启谱书式：丁嘉 → 丁氏嘉（显示层），原始数据不变
    sp = page.locator('.node[data-id="z3"] .sp[data-sp="0"]').inner_text().replace("\n", "")
    check("丁氏嘉" in sp, "配偶谱书式显示：丁嘉→丁氏嘉", sp)
    raw = page.evaluate('window.__ZP.findNode("z3").spouses')
    check(raw == ["丁嘉"], "存储仍为原名", str(raw))
    sp1 = page.locator('.node[data-id="z1"] .sp[data-sp="0"]').inner_text().replace("\n", "")
    check("翁氏秀英" in sp1, "配偶谱书式显示：翁秀英→翁氏秀英", sp1)
    # 已含「氏」/ 复姓 / 只有姓 的边界
    cases = page.evaluate('[spouseDisplay("郭马氏"), spouseDisplay("欧阳明"), spouseDisplay("黄"), spouseDisplay("丁嘉"), spouseDisplay("欧阳")]')
    check(cases == ["郭马氏", "欧阳氏明", "黄氏", "丁氏嘉", "欧阳氏"], "边界：已有氏/复姓/只有姓补氏", str(cases))
    # 搜索按原名命中（显示层不影响搜索）
    page.evaluate("openSearch()")
    page.fill("#sbInput", "李平")
    page.wait_for_timeout(150)
    cnt = page.locator("#sbCount").inner_text()
    check(cnt == "1/1", "搜索按原名命中", cnt)
    item = page.locator(".sb-item .nm").first.inner_text()
    check("周少群" in item, "搜索列表显示成员原名（命中其配偶名）", item)
    page.evaluate("closeSearch()")
    # 女性徽标：z2/z3 无（z3 未标）、w1 有
    check(page.locator('.node[data-id="w1"] .gx').count() == 1, "女性成员显示「女」徽标")
    check(page.locator('.node[data-id="w1"] .gx').inner_text() == "女", "徽标文字为女")
    check(page.locator('.node[data-id="z1"] .gx').count() == 0, "男性不标（谱书惯例）")
    # 关闭谱书式 → 恢复原名
    open_settings(page, spouse=False)
    page.locator("#__setSave").click()
    page.wait_for_timeout(120)
    sp_off = page.locator('.node[data-id="z3"] .sp[data-sp="0"]').inner_text().replace("\n", "")
    check("丁嘉" in sp_off and "丁氏嘉" not in sp_off, "关闭后恢复原名显示", sp_off)
    # 设置持久化：刷新后仍为原名、女性徽标仍在（数据自动保存）
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    sp2 = page.locator('.node[data-id="z3"] .sp[data-sp="0"]').inner_text().replace("\n", "")
    check("丁氏嘉" not in sp2, "设置刷新后持久（关闭态）", sp2)
    check(page.locator('.node[data-id="w1"] .gx').count() == 1, "性别随数据持久化")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_gender_edit_modal_and_undo(b):
    ctx, page, errs, cons = fresh_page(b)
    goto_book(page)
    # 档案弹窗：性别选女
    page.locator('.node[data-id="z1"] .quick-add').click()
    page.locator("#__ctxMenu .mi", has_text="档案").click()
    page.select_option("#__dmGender", "f")
    page.locator("#__dmSave").click()
    page.wait_for_timeout(120)
    check(page.locator('.node[data-id="z1"] .gx').count() == 1, "档案设女后卡片出现徽标")
    g = page.evaluate('window.__ZP.findNode("z1").gender')
    check(g == "f", "数据写入 gender=f", str(g))
    # 撤销 → 徽标消失
    page.keyboard.press("Control+z")
    page.wait_for_timeout(120)
    check(page.locator('.node[data-id="z1"] .gx').count() == 0, "撤销后徽标消失")
    g2 = page.evaluate('window.__ZP.findNode("z1").gender')
    check(g2 == "", "撤销后 gender 复位", str(g2))
    # 档案里选回「男」= 清除标记
    page.locator('.node[data-id="w1"] .quick-add').click()
    page.locator("#__ctxMenu .mi", has_text="档案").click()
    page.select_option("#__dmGender", "")
    page.locator("#__dmSave").click()
    page.wait_for_timeout(120)
    check(page.locator('.node[data-id="w1"] .gx').count() == 0, "改回男后徽标移除")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_genbase_alignment(b):
    ctx, page, errs, cons = fresh_page(b)
    goto_book(page)
    chip = lambda nid: page.locator(f'.node[data-id="{nid}"] .gen').inner_text().replace("\n", "")
    check(chip("z1") == "11代·勤", "默认按应用自算：11代·勤", chip("z1"))
    # 对齐谱书：字辈第 1 字（多）= 第 13 世 → 勤 11+12=23世
    open_settings(page, base=13)
    page.locator("#__setSave").click()
    page.wait_for_timeout(150)
    check(chip("z1") == "23世·勤", "世代基准13：勤=23世", chip("z1"))
    check(chip("z2") == "24世·修", "推算代同样偏移：修=24世", chip("z2"))
    check(chip("z3") == "25世·昭", "昭=25世", chip("z3"))
    tip = page.locator('.node[data-id="z1"] .gen').get_attribute("title")
    check("谱书世数" in tip and "第11代" in tip, "tooltip 注明谱书世数与应用代数", tip)
    stats = page.locator("#statsChip").inner_text().replace("\n", "")
    check("字辈第23–25世" in stats, "统计条范围用世数", stats)
    # 帮助网格同步
    page.evaluate("openHelp()")
    h4 = page.locator("#__zbTitle").inner_text()
    check("13–52世" in h4, "帮助字辈表标题用世数", h4)
    small = page.locator('#__zbGrid .zb').nth(10).inner_text()
    check("第23世" in small, "第11字标注23世", small)
    page.evaluate("closeHelp()")
    # 搜索列表同步
    page.evaluate("openSearch()")
    page.fill("#sbInput", "昭麟")
    page.wait_for_timeout(150)
    g = page.locator(".sb-item .g").first.inner_text()
    check(g == "25世·昭", "搜索徽标用世数", g)
    page.evaluate("closeSearch()")
    # 持久化：刷新后仍是世数
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    check(chip("z1") == "23世·勤", "世代基准刷新后持久", chip("z1"))
    # 改回 1 → 恢复「代」
    open_settings(page, base=1)
    page.locator("#__setSave").click()
    page.wait_for_timeout(120)
    check(chip("z1") == "11代·勤", "改回1恢复代数", chip("z1"))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_export_book_style(b):
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto_book(page)
    open_settings(page, base=13)
    page.locator("#__setSave").click()
    page.wait_for_timeout(120)
    # 画布渲染（PNG/PDF 的底）：谱式显示 + 女徽标 + 世数下不报错
    size = page.evaluate("() => { const c = exportTreeCanvas(); return { w: c.width, h: c.height }; }")
    check(size["w"] > 0 and size["h"] > 0, "画布含新元素可渲染", str(size))
    # MD 导出：女（女）、配偶谱式、与视图一致
    with page.expect_download() as dl:
        page.evaluate("exportMarkdown()")
    d = dl.value
    path = os.path.join(LOCAL_OUT, "md_export.md")
    d.save_as(path)
    txt = open(path, encoding="utf-8").read()
    check("周少群（女）" in txt, "MD 含（女）标记", txt[:80])
    check("丁氏嘉" in txt, "MD 配偶用谱书式", "丁氏嘉" in txt and txt[:120])
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_surname_toggle(b):
    ctx, page, errs, cons = fresh_page(b)
    goto_book(page)
    # 默认显示姓氏：卡片带「周」（inner_text 前面还有「11代·勤」角标）
    nm = page.locator('.node[data-id="z1"] .node-label').inner_text()
    check("周勤善" in nm, "默认显示姓氏周", nm)
    # 关闭 → 只报名：周勤善 → 勤善；数据与搜索不受影响
    open_settings(page)
    page.set_checked("#__cfgSurname", False)
    page.locator("#__setSave").click()
    page.wait_for_timeout(150)
    nm2 = page.locator('.node[data-id="z1"] .node-label').inner_text()
    check("勤善" in nm2 and "周勤善" not in nm2, "关闭后只报名", nm2)
    raw = page.evaluate('window.__ZP.findNode("z1").name')
    check(raw == "周勤善", "存储仍为全名", raw)
    dn = page.evaluate('displayName(window.__ZP.findNode("z1"))')
    check(dn.startswith("勤善（"), "tooltip/提示同样只报名", dn)
    # 搜索按原名（含姓）仍命中，列表只报名
    page.evaluate("openSearch()")
    page.fill("#sbInput", "周少群")
    page.wait_for_timeout(150)
    cnt = page.locator("#sbCount").inner_text()
    item = page.locator(".sb-item .nm").first.inner_text()
    check(cnt == "1/1", "按全名搜索仍命中", cnt)
    check(item.startswith("少群"), "搜索列表只报名", item)
    page.evaluate("closeSearch()")
    # 单姓边界：名字只有「周」时不剥
    keep = page.evaluate("dispName('周')")
    check(keep == "周", "单字「周」不剥", keep)
    # 非周姓开头不受影响
    keep2 = page.evaluate("dispName('雷志成')")
    check(keep2 == "雷志成", "非周姓名字不动", keep2)
    # 刷新持久
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    nm3 = page.locator('.node[data-id="z1"] .node-label').inner_text()
    check("勤善" in nm3 and "周勤善" not in nm3, "姓氏开关刷新后持久", nm3)
    # 打开设置恢复显示姓氏
    open_settings(page)
    page.set_checked("#__cfgSurname", True)
    page.locator("#__setSave").click()
    page.wait_for_timeout(120)
    nm4 = page.locator('.node[data-id="z1"] .node-label').inner_text()
    check("周勤善" in nm4, "恢复显示姓氏", nm4)
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_heir_zihao_fields(b):
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto_book(page)
    # 档案：嗣出 + 字 + 号
    page.locator('.node[data-id="z1"] .quick-add').click()
    page.locator("#__ctxMenu .mi", has_text="档案").click()
    page.select_option("#__dmHeir", "out")
    page.fill("#__dmZi", "子明")
    page.fill("#__dmHao", "竹溪")
    page.locator("#__dmSave").click()
    page.wait_for_timeout(150)
    heir = page.locator('.node[data-id="z1"] .heir')
    check(heir.count() == 1 and heir.inner_text() == "嗣", "嗣出徽标显示", heir.inner_text() if heir.count() else "无")
    check("嗣出" in (heir.get_attribute("title") or ""), "嗣徽标 tooltip 注明嗣出", heir.get_attribute("title"))
    check("out" in (heir.get_attribute("class") or ""), "嗣出为描边样式", heir.get_attribute("class"))
    xh = page.locator('.node[data-id="z1"] .xh').all_inner_texts()
    check(xh == ["字子明", "号竹溪"], "字/号小字显示", str(xh))
    raw = page.evaluate('() => { const n = window.__ZP.findNode("z1"); return [n.heir, n.zi, n.hao]; }')
    check(raw == ["out", "子明", "竹溪"], "数据写入 heir/zi/hao", str(raw))
    # MD 导出（撤销前）：嗣出 + 字号齐全
    with page.expect_download() as dl:
        page.evaluate("exportMarkdown()")
    path = os.path.join(LOCAL_OUT, "md_heir.md")
    dl.value.save_as(path)
    txt = open(path, encoding="utf-8").read()
    check("（嗣出）" in txt, "MD 含嗣出", "嗣出" in txt)
    check("字子明" in txt and "号竹溪" in txt, "MD 含字/号", "字号" in txt)
    # 搜索按字/号命中
    page.evaluate("openSearch()")
    page.fill("#sbInput", "竹溪")
    page.wait_for_timeout(150)
    check(page.locator("#sbCount").inner_text() == "1/1", "按号搜索命中", page.locator("#sbCount").inner_text())
    page.evaluate("closeSearch()")
    # 撤销：嗣/字号一起回退
    page.keyboard.press("Control+z")
    page.wait_for_timeout(120)
    check(page.locator('.node[data-id="z1"] .heir').count() == 0, "撤销后嗣徽标消失")
    check(page.locator('.node[data-id="z1"] .xh').count() == 0, "撤销后字号消失")
    # 嗣子（入继）+ 导出包含
    page.locator('.node[data-id="z2"] .quick-add').click()
    page.locator("#__ctxMenu .mi", has_text="档案").click()
    page.select_option("#__dmHeir", "in")
    page.locator("#__dmSave").click()
    page.wait_for_timeout(120)
    with page.expect_download() as dl:
        page.evaluate("exportMarkdown()")
    path2 = os.path.join(LOCAL_OUT, "md_heir2.md")
    dl.value.save_as(path2)
    txt2 = open(path2, encoding="utf-8").read()
    check("（嗣子）" in txt2, "MD 含嗣子", "嗣子" in txt2)
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_cn_numeral(b):
    ctx, page, errs, cons = fresh_page(b)
    goto_book(page)
    open_settings(page, base=13)
    page.set_checked("#__cfgCn", True)
    page.locator("#__setSave").click()
    page.wait_for_timeout(150)
    chip = lambda nid: page.locator(f'.node[data-id="{nid}"] .gen').inner_text().replace("\n", "")
    check(chip("z1") == "廿三世·勤", "汉字世数：廿三世·勤", chip("z1"))
    check(chip("z3") == "廿五世·昭", "廿五世·昭", chip("z3"))
    stats = page.locator("#statsChip").inner_text().replace("\n", "")
    check("字辈第廿三–廿五世" in stats, "统计条汉字范围", stats)
    page.evaluate("openHelp()")
    check("第十三–五十二世" in page.locator("#__zbTitle").inner_text(), "帮助表标题汉字", page.locator("#__zbTitle").inner_text())
    check("第廿三世" in page.locator('#__zbGrid .zb').nth(10).inner_text(), "第11字标廿三世", page.locator('#__zbGrid .zb').nth(10).inner_text())
    page.evaluate("closeHelp()")
    page.evaluate("openSearch()")
    page.fill("#sbInput", "勤善")
    page.wait_for_timeout(150)
    check(page.locator(".sb-item .g").first.inner_text() == "廿三世·勤", "搜索徽标汉字", page.locator(".sb-item .g").first.inner_text())
    page.evaluate("closeSearch()")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    check(chip("z1") == "廿三世·勤", "汉字设置刷新后持久", chip("z1"))
    # 基准=1 时也可用汉字：十一代
    open_settings(page, base=1)
    page.locator("#__setSave").click()
    page.wait_for_timeout(120)
    check(chip("z1") == "十一代·勤", "代数也可用汉字", chip("z1"))
    open_settings(page)
    page.set_checked("#__cfgCn", False)
    page.locator("#__setSave").click()
    page.wait_for_timeout(120)
    check(chip("z1") == "11代·勤", "关闭恢复数字", chip("z1"))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_vertical_book_view(b):
    ctx, page, errs, cons = fresh_page(b)
    goto_book(page)
    # 开竖排：视图菜单
    page.locator("#btnView").click()
    page.locator("#__ctxMenu .mi", has_text="谱书竖排").click()
    page.wait_for_timeout(250)
    check("v" in (page.locator("#stage").get_attribute("class") or ""), "stage 挂 v 类", page.locator("#stage").get_attribute("class"))
    wm = page.evaluate("getComputedStyle(document.querySelector('.node[data-id=\\'z1\\'] .node-label')).writingMode")
    check(wm == "vertical-rl", "卡片竖书 writing-mode", wm)
    # 几何：世代成行（子行在父行下方、同辈同行），同辈横向铺开
    pos = page.evaluate("""() => {
      const p = id => { const n = window.__ZP.findNode(id); return [n._x, n._y]; };
      return { z1: p("z1"), z2: p("z2"), w1: p("w1") };
    }""")
    check(pos["z2"][1] > pos["z1"][1], "子代行在父代行下方", str(pos))
    check(abs(pos["z1"][1] - pos["w1"][1]) < 2, "同辈同行", str(pos))
    check(abs(pos["z1"][0] - pos["w1"][0]) > 10, "同辈横向铺开", str(pos))
    # 行左世数标（默认基准：第 1 行 = 十一代·勤；固定汉字数字，带本代字辈字）
    vrows = page.locator(".vrow")
    check(vrows.count() >= 1, "行左世数标存在", str(vrows.count()))
    check(vrows.first.inner_text() == "十一代·勤", "世数标内容（含字辈）", vrows.first.inner_text())
    # 竖排下折叠/展开仍可用
    fold = page.locator('.node[data-id="z1"] .fold')
    check(fold.count() == 1, "折叠钮存在", str(fold.count()))
    fold.click()
    page.wait_for_timeout(150)
    check(page.locator('.node[data-id="z2"]').count() == 0, "竖排下可折叠")
    fold.click()
    page.wait_for_timeout(150)
    check(page.locator('.node[data-id="z2"]').count() == 1, "竖排下可展开")
    # 竖排下画布导出正常
    size = page.evaluate("() => { const c = exportTreeCanvas(); return { w: c.width, h: c.height }; }")
    check(size["w"] > 0 and size["h"] > 0, "竖排画布可导出", str(size))
    # 竖排打印 = 谱书竖排页（克隆舞台，可装订）
    page.evaluate("buildPrintDomReal()")
    check(page.locator("#printArea .ps.v").count() == 1, "竖排打印为谱书竖排页")
    check(page.locator("#printArea .ps .vrow").count() >= 1, "打印页含行左世数标")
    check(page.locator("#printArea .quick-add").count() == 0, "打印页无交互按钮")
    check(page.locator("#printArea li").count() == 0, "竖排打印不是大纲式")
    page.evaluate("toggleVertical()")
    page.wait_for_timeout(150)
    page.evaluate("buildPrintDomReal()")
    check(page.locator("#printArea li").count() == 5, "切回常规后打印恢复大纲式（夹具5人）")
    page.evaluate("toggleVertical()")   # 恢复竖排，供后续「刷新持久」断言
    page.wait_for_timeout(150)
    # 刷新持久；再点菜单切回常规
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    check("v" in (page.locator("#stage").get_attribute("class") or ""), "竖排刷新后持久")
    page.locator("#btnView").click()
    page.locator("#__ctxMenu .mi", has_text="谱书竖排").click()
    page.wait_for_timeout(200)
    check("v" not in (page.locator("#stage").get_attribute("class") or ""), "切回常规视图")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_clan_xu(b):
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto_book(page)
    # 谱序随数据载入：顶栏显示谱名/堂号
    check(page.evaluate("window.__ZP.data.clan && window.__ZP.data.clan.tang") == "申锡堂", "谱序随数据载入")
    check(page.locator("#__puName").inner_text() == "潮阳泗水周氏族谱", "顶栏谱名", page.locator("#__puName").inner_text())
    check(page.locator("#__tangTag").inner_text() == "申锡堂", "顶栏堂号", page.locator("#__tangTag").inner_text())
    check("潮阳泗水周氏族谱" in page.title(), "标签页标题带谱名", page.title())
    # 谱序弹窗：编辑堂号
    page.locator("#btnView").click()
    page.locator("#__ctxMenu .mi", has_text="谱序").click()
    check(page.locator("#__clTang").input_value() == "申锡堂", "弹窗回填现有谱序")
    page.fill("#__clTang", "爱莲堂")
    page.locator("#__clSave").click()
    page.wait_for_timeout(150)
    check(page.locator("#__tangTag").inner_text() == "爱莲堂", "堂号即时更新", page.locator("#__tangTag").inner_text())
    check(page.evaluate("window.__ZP.data.clan.tang") == "爱莲堂", "数据写入 clan")
    # 导出标题带谱名（堂号）
    with page.expect_download() as dl:
        page.evaluate("exportMarkdown()")
    path = os.path.join(LOCAL_OUT, "md_clan.md")
    dl.value.save_as(path)
    txt = open(path, encoding="utf-8").read()
    check(txt.startswith("# 潮阳泗水周氏族谱（爱莲堂）"), "MD 标题带谱名堂号", txt[:40])
    # 撤销恢复申锡堂
    page.keyboard.press("Control+z")
    page.wait_for_timeout(120)
    check(page.evaluate("window.__ZP.data.clan.tang") == "申锡堂", "谱序可撤销")
    check(page.locator("#__tangTag").inner_text() == "申锡堂", "顶栏同步恢复")
    # 刷新持久
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    check(page.evaluate("window.__ZP.data.clan.tang") == "申锡堂", "谱序刷新持久")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_shixilu_export(b):
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto_book(page)
    # 设定世代基准13 → 谱世 23-25世，同属「第廿一世至第廿五世」表
    open_settings(page, base=13)
    page.locator("#__setSave").click()
    page.wait_for_timeout(120)
    with page.expect_download() as dl:
        page.evaluate("exportShixilu()")
    path = os.path.join(LOCAL_OUT, "shixilu.html")
    dl.value.save_as(path)
    txt = open(path, encoding="utf-8").read()
    # 标题与谱序摘要
    check("<h1>潮阳泗水周氏族谱（申锡堂） · 世系录</h1>" in txt, "标题带谱名堂号", txt[:120])
    check("源流世系：" in txt and "濂溪" in txt, "文首带谱序摘要", "源流世系" in txt)
    check("第廿一世至第廿五世" in txt, "五世一表分组（汉字）", "第廿一世至第廿五世" in txt)
    # 表头与行传内容
    for kw in ["<th>世次</th>", "<th>讳</th>", "<th>字</th>", "<th>号</th>", "<th>行第</th>",
               "<th>生</th>", "<th>卒</th>", "<th>配偶</th>", "<th>子女</th>", "<th>记</th>"]:
        check(kw in txt, "表头含 " + kw, kw in txt)
    check("廿三世·勤" in txt and "<b>周勤善</b>" in txt, "勤善行：世次+讳", "廿三世·勤" in txt)
    check("廿四世·修" in txt and "<b>周少群</b>" in txt, "少群行", "廿四世·修" in txt)
    check("<b>周昭凤</b>" in txt, "昭凤行存在", "昭凤" in txt)
    check("原配 李氏平" in txt, "配偶列", "李氏平" in txt)
    check("勤善" in txt and "少群" in txt, "子女列含后代名", "少群" in txt)
    check("共 4 人" in txt, "人数统计", "共 4 人" in txt)
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_jian_tiao(b):
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto_book(page)
    # 档案设兼祧
    page.locator('.node[data-id="z3"] .quick-add').click()
    page.locator("#__ctxMenu .mi", has_text="档案").click()
    page.select_option("#__dmHeir", "jian")
    page.locator("#__dmSave").click()
    page.wait_for_timeout(150)
    heir = page.locator('.node[data-id="z3"] .heir')
    check(heir.count() == 1 and heir.inner_text() == "嗣", "兼祧徽标显示")
    check("jian" in (heir.get_attribute("class") or ""), "兼祧专属样式类", heir.get_attribute("class"))
    check("兼祧" in (heir.get_attribute("title") or ""), "tooltip 注明兼祧", heir.get_attribute("title"))
    check(page.evaluate('window.__ZP.findNode("z3").heir') == "jian", "数据 heir=jian")
    dn = page.evaluate('displayName(window.__ZP.findNode("z3"))')
    check("兼祧" in dn, "displayName 含兼祧", dn)
    # 打印行与 MD 都带（兼祧）
    with page.expect_download() as dl:
        page.evaluate("exportMarkdown()")
    path = os.path.join(LOCAL_OUT, "md_jian.md")
    dl.value.save_as(path)
    check("（兼祧）" in open(path, encoding="utf-8").read(), "MD 含（兼祧）")
    # 画布可渲染（横排徽标分支）
    size = page.evaluate("() => { const c = exportTreeCanvas(); return c.width > 0; }")
    check(size, "横排画布含兼祧徽标可渲染")
    # 撤销复位
    page.keyboard.press("Control+z")
    page.wait_for_timeout(120)
    check(page.locator('.node[data-id="z3"] .heir').count() == 0, "撤销后徽标消失")
    check(page.evaluate('window.__ZP.findNode("z3").heir') == "", "撤销后 heir 复位")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_zhi_mark(b):
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto_book(page)
    # 档案勾选「止」
    page.locator('.node[data-id="w1"] .quick-add').click()
    page.locator("#__ctxMenu .mi", has_text="档案").click()
    page.set_checked("#__dmZhi", True)
    page.locator("#__dmSave").click()
    page.wait_for_timeout(150)
    zhi = page.locator('.node[data-id="w1"] .zhi')
    check(zhi.count() == 1 and zhi.inner_text() == "止", "止徽标（黑圈）显示")
    check("黑圈" in (zhi.get_attribute("title") or ""), "tooltip 注明谱书凡例", zhi.get_attribute("title"))
    check(page.evaluate('window.__ZP.findNode("w1").zhi') is True, "数据 zhi=true")
    dn = page.evaluate('displayName(window.__ZP.findNode("w1"))')
    check("止" in dn, "displayName 含止", dn)
    # MD 导出带（止）
    with page.expect_download() as dl:
        page.evaluate("exportMarkdown()")
    path = os.path.join(LOCAL_OUT, "md_zhi.md")
    dl.value.save_as(path)
    check("（止）" in open(path, encoding="utf-8").read(), "MD 含（止）")
    # 世系录「记」列含止
    with page.expect_download() as dl2:
        page.evaluate("exportShixilu()")
    path2 = os.path.join(LOCAL_OUT, "sl_zhi.html")
    dl2.value.save_as(path2)
    check("止" in open(path2, encoding="utf-8").read(), "世系录记列含止")
    # 画布横竖两式可渲染
    check(page.evaluate("() => exportTreeCanvas().width > 0"), "横排画布含止可渲染")
    page.evaluate("toggleVertical()")
    page.wait_for_timeout(150)
    check(page.evaluate("() => exportTreeCanvas().width > 0"), "竖排画布含止可渲染")
    check(page.locator('.node[data-id="w1"] .zhi').count() == 1, "竖排卡面止徽标仍在")
    page.evaluate("toggleVertical()")
    page.wait_for_timeout(150)
    # 撤销复位
    page.keyboard.press("Control+z")
    page.wait_for_timeout(120)
    check(page.locator('.node[data-id="w1"] .zhi').count() == 0, "撤销后止徽标消失")
    check(page.evaluate('window.__ZP.findNode("w1").zhi') is False, "撤销后 zhi 复位")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_spouse_terms(b):
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto_book(page)
    dlg = DialogRecorder(page)
    # 先给 z1 加第二位配偶（默认次序称谓=续弦）
    dlg.queue("prompt", "王秀兰")   # 必须在点击前入队：prompt 随点击同步弹出
    page.locator('.node[data-id="z1"] .quick-add').click()
    page.locator("#__ctxMenu .mi", has_text="配偶").click()
    page.wait_for_timeout(200)
    role2 = page.locator('.node[data-id="z1"] .sp[data-sp="1"] .role').inner_text()
    check(role2 == "续弦", "次序默认称谓：续弦", role2)
    # 档案弹窗：给配偶2指定「娶」
    page.locator('.node[data-id="z1"] .quick-add').click()
    page.locator("#__ctxMenu .mi", has_text="档案").click()
    rows = page.locator("#__dmSp .row")
    check(rows.count() == 2, "弹窗按配偶生成称谓行", str(rows.count()))
    page.locator('#__dmSp select[data-i="1"]').select_option("娶")
    page.locator("#__dmSave").click()
    page.wait_for_timeout(150)
    role2b = page.locator('.node[data-id="z1"] .sp[data-sp="1"] .role').inner_text()
    check(role2b == "娶", "卡片称谓被覆盖为娶", role2b)
    role1 = page.locator('.node[data-id="z1"] .sp[data-sp="0"] .role').inner_text()
    check(role1 == "原配", "配偶1保持默认称谓", role1)
    raw = page.evaluate('window.__ZP.findNode("z1").spRoles')
    check(raw == {"1": "娶"}, "数据 spRoles 仅存覆盖项", str(raw))
    # 撤销恢复
    page.keyboard.press("Control+z")
    page.wait_for_timeout(120)
    check(page.evaluate("window.__ZP.findNode('z1').spRoles") is None, "撤销后覆盖清除")
    # 重新设置，竖排下覆盖优先于谱书默认
    page.locator('.node[data-id="z1"] .quick-add').click()
    page.locator("#__ctxMenu .mi", has_text="档案").click()
    page.locator('#__dmSp select[data-i="1"]').select_option("娶")
    page.locator("#__dmSave").click()
    page.wait_for_timeout(120)
    page.evaluate("toggleVertical()")
    page.wait_for_timeout(150)
    role2v = page.locator('.node[data-id="z1"] .sp[data-sp="1"] .role').inner_text()
    check(role2v == "娶", "竖排下覆盖仍生效", role2v)
    role1v = page.locator('.node[data-id="z1"] .sp[data-sp="0"] .role').inner_text()
    check(role1v == "配", "竖排未覆盖者用谱书默认（配）", role1v)
    page.evaluate("toggleVertical()")
    page.wait_for_timeout(120)
    # MD 导出同步
    with page.expect_download() as dl:
        page.evaluate("exportMarkdown()")
    path = os.path.join(LOCAL_OUT, "md_term.md")
    dl.value.save_as(path)
    txt = open(path, encoding="utf-8").read()
    check("娶 王氏秀兰" in txt, "MD 称谓同步（配偶名走谱书式）", "娶 王氏秀兰" in txt)
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


def _run():
    ok = run_module(_sys.modules[__name__], "t_bookfmt 谱书式显示")
    _sys.exit(0 if ok else 1)


if __name__ == "__main__":
    _run()
