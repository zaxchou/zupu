# -*- coding: utf-8 -*-
"""Markdown 导出→导入往返（v2 机器可解析格式）。
导出用真实菜单点击（expect_download），导入走 __importFile set_input_files；
断言 treeData 与原树深度相等（忽略 id / expanded）、姓氏显示不影响导出全名、
备注含竖线不丢字、坏文件 alert 带行号且数据不动、重名同辈不互串。"""
from helper import *
import sys as _sys
import os as _os
import shutil as _shutil

# 富字段树：女/字/号/嗣子/嗣出/兼祧/止/多配偶/生卒（1951-03-15、约1900）/
# 备注（全角｜、（）、—、换行）/ 重名同辈 / clan 全字段 / zibei
RICH = {
  "id": "root", "name": "始祖雷公", "spouses": ["太始祖母吴氏"],
  "clan": {
    "ming": "雷氏宗谱", "tang": "冯翊堂",
    "chain": "雷公—震初—恒—谦益",
    "yuanzu": "始祖雷公，字震初",
    "shizu": "一世祖：雷震初\n二世祖：雷恒",
    "qianzu": "始迁祖：雷恒，明初自赣迁鄂",
    "origin": "吾族出自冯翊。\n明洪武二年徙居黄冈。\n谱成于光绪廿六年。"
  },
  "zibei": ["震", "恒", "谦", "豫"],
  "children": [
    { "id": "a1", "name": "雷谦益（?）", "gender": "f", "zi": "德坤", "hao": "韫玉",
      "heir": "in", "birth": "约1900", "death": "1951-03-15",
      "spouses": ["王秀兰", "李淑芬", "张桂香"],
      "note": "原稿注：兼祧叔房｜名下有小字\n第二行备注（含括号）—破折号",
      "expanded": True, "children": [
        { "id": "a1x", "name": "雷豫顺", "zhi": True, "note": "止于此，无传",
          "spouses": [], "expanded": True, "children": [] },
        { "id": "a1y", "name": "雷豫发", "heir": "out", "spouses": [], "expanded": True, "children": [] },
        { "id": "a1z", "name": "雷豫发", "heir": "jian", "spouses": [], "expanded": True, "children": [] } ] },
    { "id": "a2", "name": "雷谦亨", "spouses": ["陈氏"], "birth": "1910", "death": "约1980",
      "expanded": True, "children": [] }
  ]
}


def set_tree(page, data):
    page.evaluate(
        "d => { window.__ZP.data = d;"
        " window.__mdOrig = JSON.parse(JSON.stringify(window.__ZP.sanitize(window.__ZP.data))); }",
        data)


def snapshot(page):
    return page.evaluate("() => JSON.stringify(window.__ZP.sanitize(window.__ZP.data))")


def export_md(page, out_name):
    """真实链路导出：#btnFile → 菜单「导出 Markdown（可导回）」→ 下载"""
    with page.expect_download() as di:
        page.locator("#btnFile").click()
        page.locator('#__ctxMenu .mi', has_text="导出 Markdown").click()
    local = _os.path.join(LOCAL_OUT, out_name)
    _shutil.copyfile(di.value.path(), local)
    return local, di.value.suggested_filename


def norm_deep_eq(page):
    """忽略 id / expanded / _ 开头布局字段后整树 deepEq（clan / zibei 一并比较）"""
    return page.evaluate("""() => {
      const norm = n => {
        const c = JSON.parse(JSON.stringify(n));
        (function w(x){
          Object.keys(x).forEach(k => { if (k[0] === '_') delete x[k]; });
          delete x.id; x.expanded = true; (x.children || []).forEach(w);
        })(c);
        return c;
      };
      return deepEq(norm(window.__ZP.data), norm(window.__mdOrig));
    }""")


@testcase
def t_md_rich_roundtrip(b):
    """富字段树：真实菜单导出 md → __importFile 导回 → treeData deepEqual"""
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    dlg = DialogRecorder(page)
    goto(page)
    set_tree(page, RICH)
    local, fname = export_md(page, "exp_rich.md")
    check(fname == "雷氏宗谱.md", "md 文件名 = 谱名", fname)
    md_text = open(local, encoding="utf-8").read()
    check(md_text.startswith("# 雷氏宗谱\n"), "标题行 = 谱名", md_text[:40])
    check("堂号：冯翊堂" in md_text, "头部：堂号", md_text)
    check("始祖：始祖雷公，字震初" in md_text, "头部：始祖", md_text)
    check("始祖记：一世祖：雷震初" in md_text and "  二世祖：雷恒" in md_text,
          "头部：始祖记多行续行 2 空格缩进", md_text)
    check("始迁祖：雷恒，明初自赣迁鄂" in md_text, "头部：始迁祖", md_text)
    check("源流：雷公—震初—恒—谦益" in md_text, "头部：源流", md_text)
    check("字辈：震 恒 谦 豫" in md_text, "头部：字辈空格分隔", md_text)
    check("谱序：吾族出自冯翊。" in md_text and "\n  明洪武二年徙居黄冈。" in md_text,
          "头部：谱序多行续行", md_text)
    check("- 始祖雷公 | 配：太始祖母吴氏" in md_text, "根行（深度0）含配偶段", md_text)
    check("- 雷谦益（?） | 性别：女 | 字：德坤 | 号：韫玉 | 嗣子 | 配：王秀兰、李淑芬、张桂香"
          " | 生：约1900 | 卒：1951-03-15 | 注：原稿注：兼祧叔房｜名下有小字" in md_text,
          "富字段人员行（段式、保序、原始全名）", md_text)
    check("  第二行备注（含括号）—破折号" in md_text, "备注换行续行缩进输出", md_text)
    check("- 雷豫顺 | 止 | 注：止于此，无传" in md_text, "止段", md_text)
    check("- 雷豫发 | 嗣出" in md_text and "- 雷豫发 | 兼祧" in md_text, "嗣出/兼祧段", md_text)
    # 导回：隐藏 input set_input_files（真实 change → FileReader → importMarkdown）
    page.locator("#__importFile").set_input_files(local)
    page.wait_for_function("() => window.__ZP.data.id.indexOf('r_') === 0", timeout=5000)
    check(norm_deep_eq(page), "往返后 treeData deepEqual（忽略 id/expanded，含 clan/zibei）")
    check(dlg.count() == 0, "成功导入零弹窗", str(dlg.records))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_md_surname_off_fidelity(b):
    """保真回归：关掉「姓氏显示」后导出，md 仍含原始全名（不再走 dispName）"""
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto(page)
    page.evaluate("() => { cfg.showSurname = false; saveCfg(); render(); }")
    check(page.evaluate("() => window.__ZP.cfg.showSurname") is False, "姓氏显示已关")
    local, fname = export_md(page, "exp_sur.md")
    check(fname == "家族族谱.md", "无谱名 fallback 文件名", fname)
    md_text = open(local, encoding="utf-8").read()
    check("- 雷志成" in md_text, "关姓氏显示后导出仍为全名（雷志成）", md_text)
    check(md_text.count("志成") == md_text.count("雷志成"), "不出现剥姓氏名（志成）", md_text)
    check("- 雷波美（?）" in md_text, "含括号名保真", md_text)
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_md_pipe_and_paren_names(b):
    """备注含全角｜原样往返；含半角｜并回备注不丢字；（?）类名字不丢字"""
    data = {
      "id": "root", "name": "根", "spouses": [], "expanded": True, "children": [
        { "id": "p1", "name": "雷波美（?）", "spouses": [], "expanded": True, "children": [],
          "note": "备注甲｜备注乙（全角竖线原样）" },
        { "id": "p2", "name": "雷官福", "spouses": [], "expanded": True, "children": [],
          "note": "半角竖线a|b\n续行" },
        { "id": "p3", "name": "李三元（?）", "spouses": ["王五（?）"], "expanded": True, "children": [] } ]
    }
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto(page)
    set_tree(page, data)
    local, _fname = export_md(page, "exp_pipe.md")
    md_text = open(local, encoding="utf-8").read()
    check("备注甲｜备注乙（全角竖线原样）" in md_text, "全角｜原样输出", md_text)
    check("注：半角竖线a|b" in md_text, "半角｜在备注段内输出", md_text)
    page.locator("#__importFile").set_input_files(local)
    page.wait_for_function("() => window.__ZP.data.id.indexOf('r_') === 0", timeout=5000)
    r = page.evaluate("""() => {
      const k = window.__ZP.data.children;
      return { n0: k[0].name, note0: k[0].note,
               n1: k[1].name, note1: k[1].note,
               n2: k[2].name, sp2: k[2].spouses[0] };
    }""")
    check(r["n0"] == "雷波美（?）", "（?）名字往返保真", str(r))
    check(r["note0"] == "备注甲｜备注乙（全角竖线原样）", "全角｜备注原样往返", str(r))
    check(r["note1"] == "半角竖线a\nb\n续行", "半角｜备注并回备注不丢字（｜→换行）", str(r))
    check(r["n2"] == "李三元（?）" and r["sp2"] == "王五（?）", "名字/配偶含括号保真", str(r))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_md_bad_files_alert_and_no_mutation(b):
    """坏文件：深度跳级 / 多根行 / 无树 → alert 带行号，treeData 一字不动"""
    ctx, page, errs, cons = fresh_page(b)
    dlg = DialogRecorder(page)
    goto(page)
    before = snapshot(page)
    out = LOCAL_OUT

    # ① 深度跳级（第 4 行比上一层深超过一层）
    p1 = _os.path.join(out, "bad_jump.md")
    open(p1, "w", encoding="utf-8").write("# 谱\n\n- 甲\n    - 乙\n")
    page.locator("#__importFile").set_input_files(p1)
    page.wait_for_timeout(400)
    msgs = dlg.messages()
    check(len(msgs) == 1 and "第 4 行" in msgs[0], "跳级报错带行号 第 4 行", str(msgs))
    check("缩进跳级" in msgs[0], "跳级报错详情", str(msgs))
    check(snapshot(page) == before, "跳级失败后 treeData 不变")

    # ② 深度 0 出现第二行（多根）
    p2 = _os.path.join(out, "bad_two_roots.md")
    open(p2, "w", encoding="utf-8").write("- 甲\n- 乙\n")
    page.locator("#__importFile").set_input_files(p2)
    page.wait_for_timeout(400)
    msgs = dlg.messages()
    check(len(msgs) == 2 and "第 2 行" in msgs[1], "多根报错带行号 第 2 行", str(msgs))
    check(snapshot(page) == before, "多根失败后 treeData 不变")

    # ③ 无树（没有「- 」行）
    p3 = _os.path.join(out, "bad_no_tree.md")
    open(p3, "w", encoding="utf-8").write("# 只有头部\n堂号：某堂\n")
    page.locator("#__importFile").set_input_files(p3)
    page.wait_for_timeout(400)
    msgs = dlg.messages()
    check(len(msgs) == 3 and "族谱树缺失" in msgs[2], "无树报错", str(msgs))
    check(snapshot(page) == before, "无树失败后 treeData 不变")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_md_dup_children_roundtrip(b):
    """多子女同名单：三个「雷同」互不吞并，顺序保持，整树 deepEqual"""
    data = {
      "id": "root", "name": "根", "spouses": [], "expanded": True, "children": [
        { "id": "d1", "name": "雷同", "spouses": [], "expanded": True, "children": [] },
        { "id": "d2", "name": "雷同", "spouses": [], "expanded": True, "children": [] },
        { "id": "d3", "name": "雷同", "spouses": [], "expanded": True, "children": [] } ]
    }
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto(page)
    set_tree(page, data)
    local, _fname = export_md(page, "exp_dup.md")
    md_text = open(local, encoding="utf-8").read()
    check(md_text.count("  - 雷同\n") == 3, "三个同名子女各占一行", md_text)
    page.locator("#__importFile").set_input_files(local)
    page.wait_for_function("() => window.__ZP.data.id.indexOf('r_') === 0", timeout=5000)
    kids = page.evaluate("() => window.__ZP.data.children.map(c => c.name)")
    check(kids == ["雷同", "雷同", "雷同"], "重名同辈不吞并、保序", str(kids))
    check(norm_deep_eq(page), "重名树往返 deepEqual")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


if __name__ == "__main__":
    ok = run_module(_sys.modules[__name__], "t_md_roundtrip Markdown 往返")
    _sys.exit(0 if ok else 1)
