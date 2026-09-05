# -*- coding: utf-8 -*-
"""多语言版本（v15.32）：index-en / index-ja 冒烟——能起、向导可用、添加成员可用、
世代角标按各自语言的字辈（世代名）工作、界面无中文残留（en）。
直接使用生成文件自身的内嵌种子（即该语言的演示谱），不另造数据。"""
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
    # 字辈（世代名）定代：d1 = James Arthur Miller → Gen 1
    chip = page.locator('.node[data-id="d1"] .gen').inner_text().replace("\n", "")
    check("Gen 1" in chip, "EN: generation chip via generational name", chip)
    chip4 = page.locator('.node[data-id="d4"] .gen').inner_text().replace("\n", "")
    check("Gen 4" in chip4, "EN: 4th gen chip", chip4)
    # 添加第一代成员
    dlg = DialogRecorder(page)
    dlg.queue("prompt", "Adam Miller")
    page.locator('.node .quick-add').first.click()
    page.locator("#__ctxMenu .mi", has_text="First generation").click()
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
    # 字輩定代：林義郎 → 第1代
    chip = page.locator('.node[data-id="d1"] .gen').inner_text().replace("\n", "")
    check("1" in chip, "JA: 世代バッジ（字輩一致）", chip)
    chip4 = page.locator('.node[data-id="d4"] .gen').inner_text().replace("\n", "")
    check("4" in chip4, "JA: 第4世代バッジ", chip4)
    # 兄弟姉妹メニューで追加
    dlg = DialogRecorder(page)
    dlg.queue("prompt", "林花子")
    page.locator('.node .quick-add').first.click()
    page.locator("#__ctxMenu .mi", has_text="第一世代").click()
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
    check(page.evaluate("window.__ZP.data.name") == "家族族譜", "繁：示例譜已轉繁體",
          page.evaluate("window.__ZP.data.name"))
    dlg = DialogRecorder(page)
    dlg.queue("prompt", "趙傳心")
    page.locator('.node .quick-add').first.click()
    page.locator("#__ctxMenu .mi", has_text="第一代").click()
    page.wait_for_timeout(250)
    check(page.evaluate("window.__ZP.data.children.length") == 2, "繁：可正常添加成員")
    check(page.evaluate("localStorage.getItem('zupu_data_v4') === null"), "繁：獨立儲存（不寫簡體鍵）")
    check(page.evaluate("localStorage.getItem('zupu_data_v4_hant') !== null"), "繁：寫入自己的儲存鍵")
    check(not errs, "繁：無 JS 錯誤", str(errs))
    ctx.close()


if __name__ == "__main__":
    ok = run_module(_sys.modules[__name__], "t_i18n 多语言版本")
    _sys.exit(0 if ok else 1)
