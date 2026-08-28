# -*- coding: utf-8 -*-
"""v15 自动保存：数据真源 = 本浏览器（无感、零弹窗、零下载）。
覆盖：编辑即存/刷新恢复/跨页面一致/旧草稿自动抢救/备份下载/旧版 html 导入/重置。"""
from helper import *
import json as _json
import os as _os
import re as _re


def real_edit(page):
    page.locator('.node[data-id="b3a"] .node-label').click()
    page.keyboard.press("Control+i")
    page.locator("#__dmBirth").fill("1948")
    page.keyboard.press("Enter")
    page.wait_for_timeout(250)


def make_backup_expect(page):
    """触发「文件 ▾ → 备份」并等待下载，返回 (文件名, json 文本)"""
    page.locator("#btnFile").click()
    page.locator('#__ctxMenu .mi', has_text="备份到文件").click()
    return page


@testcase
def t_autosave_reload_and_light(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    check("已保存" in page.locator("#saveState").inner_text(), "状态灯=已保存",
          page.locator("#saveState").inner_text())
    check(page.locator(".topbar button.primary").count() == 0, "无保存按钮（Gmail 式）")
    dlg = DialogRecorder(page)
    # 编辑 → 自动保存
    real_edit(page)
    page.wait_for_timeout(150)
    v4 = page.evaluate("k => localStorage.getItem(k)", page.evaluate("window.__ZP.storageKey()"))
    check(v4 and "1948" in v4, "编辑即自动写入浏览器存储", str(bool(v4)))
    check(dlg.count() == 0, "零弹窗", str(dlg.records))
    # 刷新不丢
    page.reload(); page.wait_for_load_state("domcontentloaded")
    check(page.evaluate('window.__ZP.findNode("b3a").birth') == "1948", "刷新后数据还在")
    check("已保存" in page.locator("#saveState").inner_text(), "刷新后状态灯仍=已保存")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_autosave_cross_page_same_browser(b):
    """同一浏览器 = 同一份数据：页面 A 的编辑，页面 B 打开即见（Gmail 式账号感）"""
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    real_edit(page)
    page.wait_for_timeout(150)
    p2 = ctx.new_page()
    p2.goto(FIXTURE_URL); p2.wait_for_load_state("domcontentloaded")
    check(p2.evaluate('window.__ZP.findNode("b3a").birth') == "1948",
          "新开页面读到同一份数据")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_autosave_legacy_draft_rescue(b):
    """自动抢救：浏览器里有旧版草稿且比文件内嵌数据丰富 → 自动采用并提示"""
    ctx, page, errs, cons = fresh_page(b)
    # 预置一份「成员更多」的旧版草稿（模拟 v14 时代的浏览器遗留）
    bigger = _json.loads(_json.dumps(SAMPLE_DATA))
    bigger["children"].append({ "id": "old1", "name": "旧稿成员", "spouses": [],
                                "expanded": True, "children": [] })
    # add_init_script 不支持参数注入，直接把数据序列化进脚本
    script = "localStorage.setItem('zupu_tree_data_v3_legacy', " + _json.dumps(_json.dumps(bigger, ensure_ascii=False)) + ");"
    page.add_init_script(script)
    goto(page)
    check(page.evaluate('!!window.__ZP.findNode("old1")'), "旧草稿中的成员被自动恢复")
    toast = page.locator("#__toast").inner_text()
    check("历史数据恢复" in toast or "自动保存" in toast, "恢复提示出现", toast)
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_backup_download_and_restore(b):
    """备份=纯下载 json（零弹窗）；恢复=选文件即可（含旧版 html 的读取）"""
    out_local = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "_out")
    _os.makedirs(out_local, exist_ok=True)
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    dlg = DialogRecorder(page)
    goto(page)
    real_edit(page)   # b3a birth=1948
    with page.expect_download() as di:
        make_backup_expect(page)
    d = di.value
    check(_re.match(r"^家族族谱-备份-\d{8}-\d{4}\.json$", d.suggested_filename),
          "备份文件名带日期", d.suggested_filename)
    data = _json.loads(open(d.path(), encoding="utf-8").read())
    def find(dd, nid):
        if dd.get("id") == nid: return dd
        for c in dd.get("children", []):
            r = find(c, nid)
            if r: return r
    check(find(data, "b3a")["birth"] == "1948", "备份含最新编辑")
    check(dlg.count() == 0, "备份零弹窗", str(dlg.records))

    # 恢复：旧版 html（内嵌数据不同的副本）也能直接读
    variant_html = open(FIXTURE_FILE, encoding="utf-8").read().replace("雷旭", "雷振南")
    vpath = _os.path.join(out_local, "old_copy.html")
    with open(vpath, "w", encoding="utf-8") as f:
        f.write(variant_html)
    page.locator("#btnFile").click()
    page.locator('#__ctxMenu .mi', has_text="恢复备份").click()
    page.locator("#__importFile").set_input_files(vpath)
    page.wait_for_timeout(400)
    check(page.evaluate('window.__ZP.findNode("b3").name') == "雷振南",
          "旧版 html 导入成功（数据替换）")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_reset_reseed(b):
    """重置：清空当前族谱回到文件自带的初始数据（v4 随之更新）"""
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    page.locator('.node[data-id="b3"] .node-label').click()
    dlg.queue("confirm", True)
    page.keyboard.press("Delete")
    page.wait_for_timeout(200)
    check(page.locator(".node").count() == 11, "先删掉一支（雷旭父子 2 节点）", str(page.locator(".node").count()))
    page.locator("#btnFile").click()
    dlg.queue("confirm", True)
    page.locator('#__ctxMenu .mi', has_text="重置数据").click()
    page.wait_for_timeout(300)
    check(page.locator(".node").count() == 13, "重置后回到初始 13 节点", str(page.locator(".node").count()))
    v4 = page.evaluate("k => localStorage.getItem(k)", page.evaluate("window.__ZP.storageKey()"))
    check(v4 and "雷旭" in v4, "重置结果已自动保存", str(bool(v4)))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


if __name__ == "__main__":
    import sys as _sys
    ok = run_module(_sys.modules[__name__], "t_autosave 无感保存")
    sys.exit(0 if ok else 1)
