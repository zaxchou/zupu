# -*- coding: utf-8 -*-
"""多语言冒烟：英/日/繁页面、向导、添加成员及独立世祖/字辈角标。
冒烟使用各语言演示种子；十一层夹具核对起用10与无字辈表时的结构编号。"""
from helper import *
import sys as _sys
import os
import re as _re
import os as _os

LOCAL_EN = r"Z:\BaiduNetdiskWorkspace\myagent-work\zcode\legacy\index-en.html"
LOCAL_JA = r"Z:\BaiduNetdiskWorkspace\myagent-work\zcode\legacy\index-ja.html"


def lang_url(local, name):
    app = open(local, encoding="utf-8").read()
    path = os.path.join(LOCAL_OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(app)
    return OUT_DIR + "/" + name


def goto_lang(page, url):
    page.goto(url)
    page.wait_for_load_state("domcontentloaded")
    page.evaluate("() => { localStorage.clear(); }")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    return page


@testcase
def t_i18n_en_smoke(b):
    ctx, page, errs, cons = fresh_page(b)
    goto_lang(page, lang_url(LOCAL_EN, "fixture_en.html"))
    check(page.locator("#__wizModal").is_visible(), "EN: first load shows the welcome wizard")
    page.locator('#__wizModal [data-wiz="demo"]').click()
    page.wait_for_timeout(150)
    check(not page.locator("#__wizModal").is_visible(), "EN: wizard closes after choice")
    check("Saved" in page.locator("#saveState").inner_text(), "EN: save light is English",
          page.locator("#saveState").inner_text())
    check("View" in page.locator("#btnView").inner_text(), "EN: View menu is English")
    stats = page.locator("#statsChip").inner_text()
    check("members" in stats and "gens" in stats, "EN: stats chip is English", stats)
    # 世祖按父子结构编号，字辈在独立角标中按辈序显示。
    chip = page.locator('.node[data-id="d1"] .gen').inner_text()
    check(chip == "Generation 1", "EN: first member has structural generation 1", chip)
    sequence = page.locator('.node[data-id="d1"] .zibei').inner_text()
    check(sequence == "Generation-name sequence 1 · Xing", "EN: first generation-name badge is separate", sequence)
    chip4 = page.locator('.node[data-id="d6"] .gen').inner_text()
    check(chip4 == "Generation 4", "EN: Zhu Zhanji has structural generation 4", chip4)
    chip5 = page.locator('.node[data-id="d5"] .gen').inner_text()
    check(chip5 == "Generation 3", "EN: Zhu Gaochi has structural generation 3", chip5)
    sequence5 = page.locator('.node[data-id="d5"] .zibei').inner_text()
    check(sequence5 == "Generation-name sequence 3 · Gao", "EN: Gao is in the independent sequence badge", sequence5)
    # 添加第一代成员
    dlg = DialogRecorder(page)
    page.locator('.node .quick-add').first.click()
    page.locator("#__ctxMenu .mi", has_text="First generation").click()
    page.fill("#__uipInput", "Adam Miller")
    page.click("#__uipOk")
    page.wait_for_timeout(250)
    check(page.evaluate('window.__ZP.data.children.length') == 2, "EN: adding a first-gen member works")
    # 顶栏 / 图例不得残留中文
    top = page.locator(".topbar").inner_text()
    check(not _re.search(r"[\u3400-\u9fff]", top), "EN: topbar has no Chinese", top)
    legend = page.locator(".legend").inner_text()
    check(not _re.search(r"[\u3400-\u9fff]", legend), "EN: legend has no Chinese", legend)
    check(not page.evaluate("window.__ZP.data.demo"), "EN: demo flag cleared after choosing")
    check(page.evaluate("localStorage.getItem('zupu_data_v4') === null"), "EN: standalone storage (never writes the zh key)")
    check(page.evaluate("localStorage.getItem('zupu_data_v4_en') !== null"), "EN: writes its own storage key")
    check(not errs, "EN: no JS errors", str(errs))
    ctx.close()


@testcase
def t_i18n_ja_smoke(b):
    ctx, page, errs, cons = fresh_page(b)
    goto_lang(page, lang_url(LOCAL_JA, "fixture_ja.html"))
    check(page.locator("#__wizModal").is_visible(), "JA: 初回読み込みでウェルカム画面")
    page.locator('#__wizModal [data-wiz="demo"]').click()
    page.wait_for_timeout(150)
    check(not page.locator("#__wizModal").is_visible(), "JA: 選択後ウェルカム画面が閉じる")
    check("保存済み" in page.locator("#saveState").inner_text(), "JA: 保存ライトが日本語",
          page.locator("#saveState").inner_text())
    check("表示" in page.locator("#btnView").inner_text(), "JA: 表示メニューが日本語")
    stats = page.locator("#statsChip").inner_text()
    check("人" in stats and "代" in stats, "JA: 統計チップが日本語", stats)
    # 世代は親子関係から数え、字輩順序は別のバッジで表示する。
    chip = page.locator('.node[data-id="d1"] .gen').inner_text()
    check(chip == "1世代", "JA: 親子関係から数えた第1世代", chip)
    sequence = page.locator('.node[data-id="d1"] .zibei').inner_text()
    check(sequence == "字輩順序1・興", "JA: 独立した字輩順序バッジ", sequence)
    chip4 = page.locator('.node[data-id="d6"] .gen').inner_text()
    check(chip4 == "4世代", "JA: 朱瞻基は第4世代", chip4)
    sequence3 = page.locator('.node[data-id="d5"] .zibei').inner_text()
    check(sequence3 == "字輩順序3・高", "JA: 第3世代の字輩は別表示", sequence3)
    # 兄弟姉妹メニューで追加
    dlg = DialogRecorder(page)
    page.locator('.node .quick-add').first.click()
    page.locator("#__ctxMenu .mi", has_text="第一世代").click()
    page.fill("#__uipInput", "林花子")
    page.click("#__uipOk")
    page.wait_for_timeout(250)
    check(page.evaluate('window.__ZP.data.children.length') == 2, "JA: メンバー追加が動く")
    check(not page.evaluate("window.__ZP.data.demo"), "JA: 選択後に demo フラグ解除")
    check(page.evaluate("localStorage.getItem('zupu_data_v4') === null"), "JA: 独立ストレージ（中国語版のキーに書かない）")
    check(page.evaluate("localStorage.getItem('zupu_data_v4_ja') !== null"), "JA: 自分のストレージキーに書く")
    check(not errs, "JA: JS エラーなし", str(errs))
    ctx.close()


@testcase
def t_i18n_zh_hant_smoke(b):
    ctx, page, errs, cons = fresh_page(b)
    goto_lang(page, lang_url(r"Z:\BaiduNetdiskWorkspace\myagent-work\zcode\legacy\index-zh-Hant.html", "fixture_hant.html"))
    check(page.locator("#__wizModal").is_visible(), "繁：首次載入彈出歡迎嚮導")
    page.locator('#__wizModal [data-wiz="demo"]').click()
    page.wait_for_timeout(150)
    check(not page.locator("#__wizModal").is_visible(), "繁：選擇後嚮導關閉")
    check("儲存" in page.locator("#saveState").inner_text(), "繁：狀態燈為台灣用語（儲存）",
          page.locator("#saveState").inner_text())
    check("檔案" in page.locator("#btnFile").inner_text(), "繁：檔案選單為台灣用語")
    stats = page.locator("#statsChip").inner_text()
    check("位成員" in stats, "繁：統計條為繁體", stats)
    check(page.evaluate("window.__ZP.data.name") == "明朝帝系", "繁：示例譜為明帝系",
          page.evaluate("window.__ZP.data.name"))
    check(page.evaluate("window.__ZP.findNode('d5').name") == "朱高熾", "繁：種子已 OpenCC 轉繁（炽→熾）",
          page.evaluate("window.__ZP.findNode('d5').name"))
    dlg = DialogRecorder(page)
    page.locator('.node .quick-add').first.click()
    page.locator("#__ctxMenu .mi", has_text="第一代").click()
    page.fill("#__uipInput", "趙傳心")
    page.click("#__uipOk")
    page.wait_for_timeout(250)
    check(page.evaluate("window.__ZP.data.children.length") == 2, "繁：可正常添加成員")
    check(page.evaluate("localStorage.getItem('zupu_data_v4') === null"), "繁：獨立儲存（不寫簡體鍵）")
    check(page.evaluate("localStorage.getItem('zupu_data_v4_hant') !== null"), "繁：寫入自己的儲存鍵")
    check(not errs, "繁：無 JS 錯誤", str(errs))
    ctx.close()


@testcase
def t_i18n_independent_generation_sequence(b):
    cases = [
        (LOCAL_EN, "fixture_en.html", "Generation {}", "Generation-name sequence {} · {}"),
        (LOCAL_JA, "fixture_ja.html", "{}世代", "字輩順序{}・{}"),
        (r"Z:\BaiduNetdiskWorkspace\myagent-work\zcode\legacy\index-zh-Hant.html",
         "fixture_hant.html", "{}世", "輩序{}·{}"),
    ]
    for local, name, gen_text, sequence_text in cases:
        ctx, page, errs, cons = fresh_page(b)
        try:
            goto_lang(page, lang_url(local, name))
            page.locator('#__wizModal [data-wiz="demo"]').click()
            # 连续十一层；名字含第2字也不能改变结构世数或起用前的空辈序。
            page.evaluate("""() => {
                const root = {id:'root', name:'Tree', spouses:[], expanded:true,
                              zibei:['Alpha', 'Beta'], children:[]};
                let parent = root;
                for (let i = 1; i <= 11; i++) {
                    const child = {id:'g' + i, name:i === 1 ? 'Beta' : 'Member ' + i,
                                   spouses:[], expanded:true, children:[]};
                    parent.children.push(child);
                    parent = child;
                }
                window.__ZP.cfg.zibeiStart = 10;
                window.__ZP.cfg.cnNum = false;
                window.__ZP.data = root;
            }""")
            for i in (1, 9, 10, 11):
                chip = page.locator(f'.node[data-id="g{i}"] .gen').inner_text()
                check(chip == gen_text.format(i), f"{name}: generation {i} follows structure", chip)
            for i in (1, 9):
                badge = page.locator(f'.node[data-id="g{i}"] .zibei')
                check(badge.inner_text() == "" and not badge.is_visible(),
                      f"{name}: sequence stays empty and hidden before generation 10")
            for i, zi in ((10, "Alpha"), (11, "Beta")):
                badge = page.locator(f'.node[data-id="g{i}"] .zibei').inner_text()
                check(badge == sequence_text.format(i - 9, zi),
                      f"{name}: generation {i} uses independent sequence {i - 9}", badge)
            check(page.locator('.node[data-id="root"] .gen, .node[data-id="root"] .zibei').count() == 0,
                  f"{name}: tree title has neither generation nor sequence badge")
            page.evaluate("() => { const d = window.__ZP.data; d.zibei = []; window.__ZP.data = d; }")
            badges = page.locator('.node .zibei')
            check(all(text == "" for text in badges.all_inner_texts())
                  and all(not badge.is_visible() for badge in badges.all()),
                  f"{name}: unconfigured sequence badges stay empty and hidden")
            check(page.locator('.node .gen').count() == 11, f"{name}: all generations remain without a sequence")
            check(page.locator('.node[data-id="g11"] .gen').inner_text() == gen_text.format(11),
                  f"{name}: no sequence still preserves generation 11")
            check(not errs, f"{name}: no JS errors", str(errs))
        finally:
            ctx.close()


if __name__ == "__main__":
    ok = run_module(_sys.modules[__name__], "t_i18n 多语言版本")
    _sys.exit(0 if ok else 1)
