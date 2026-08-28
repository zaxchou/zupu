# -*- coding: utf-8 -*-
"""公共设施：页面地址、错误/对话框采集器、断言工具。
遵循 handoff §8 的教训：单 dialog handler + 可变变量收集；关键交互用真实鼠标事件。"""
import sys, io, time, traceback, re
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8931"
PAGE_PATH = BASE + "/" + "%E5%AE%B6%E6%97%8F%E6%97%8F%E8%B0%B1-%E6%80%9D%E7%BB%B4%E5%AF%BC%E5%9B%BE.html"
OUT_DIR = BASE + "/tests/_out"
LOCAL_OUT = r"Z:\BaiduNetdiskWorkspace\myagent-work\zcode\legacy\tests\_out"
LOCAL_HTML = r"Z:\BaiduNetdiskWorkspace\myagent-work\zcode\legacy\家族族谱-思维导图.html"
FIXTURE_URL = OUT_DIR + "/fixture.html"
FIXTURE_FILE = LOCAL_OUT + r"\fixture.html"

# 测试夹具：示例数据（13 人三族支 + 待核对备注）。用户主文件里是他的真实数据，
# 测试绝不碰主文件 —— 所有用例都跑在 _out/fixture.html（示例数据 + 最新代码）上。
SAMPLE_DATA = {
  "id": "root", "name": "家族族谱", "spouses": [], "expanded": True, "children": [
    { "id": "b1", "name": "少秀（春?）", "spouses": ["保壬新妹"], "expanded": True, "children": [
        { "id": "b1a", "name": "雷志成", "spouses": ["俞贵玄（美?）"], "expanded": True, "children": [
            { "id": "b1a1", "name": "周新洋", "spouses": [], "expanded": True, "children": [] },
            { "id": "b1a2", "name": "周亿宁（?）", "spouses": [], "expanded": True, "children": [] } ] },
        { "id": "b1b", "name": "雷俊", "spouses": ["陈爱霞"], "expanded": True, "children": [
            { "id": "b1b1", "name": "周亿树", "spouses": [], "expanded": True, "children": [] } ] } ] },
    { "id": "b2", "name": "少群", "spouses": ["李平"], "expanded": True, "children": [
        { "id": "b2a", "name": "雷茂勋", "spouses": ["李平"], "expanded": True, "children": [
            { "id": "b2a1", "name": "周厚翰", "spouses": [], "expanded": True, "children": [] } ] } ] },
    { "id": "b3", "name": "雷旭", "spouses": ["陈新辉"], "expanded": True, "children": [
        { "id": "b3a", "name": "雷波美（?）", "spouses": [], "expanded": True, "children": [] } ] },
    { "id": "note", "name": "雷聿（郝?）", "spouses": ["徐海"],
      "note": "原稿左上角备注，辈分关系待核对", "expanded": True, "children": [] } ]
}

def build_fixture():
    """用示例数据 + 最新代码生成测试夹具页（每次运行套件前刷新）"""
    import json as _json, re as _re, os as _os
    app = open(LOCAL_HTML, encoding="utf-8").read()
    sample_json = _json.dumps(SAMPLE_DATA, ensure_ascii=False, indent=2)
    fixture, n = _re.subn(
        r'(<script id="__treeData" type="application/json">)[\s\S]*?(\n</script>)',
        lambda m: m.group(1) + "\n" + sample_json + "\n" + m.group(2),
        app, count=1)
    assert n == 1, "fixture: 未找到内嵌 JSON 块"
    _os.makedirs(LOCAL_OUT, exist_ok=True)
    with open(FIXTURE_FILE, "w", encoding="utf-8") as f:
        f.write(fixture)
    return FIXTURE_FILE


class DialogRecorder:
    """单 handler 收集全部原生对话框；按预设脚本应答，其余记录并 dismiss。"""

    def __init__(self, page):
        self.records = []          # [(type, message)]
        self.scripts = []          # FIFO: ('prompt', value|None) / ('confirm', bool) / ('accept',)
        page.on("dialog", self._on)

    def queue(self, kind, answer):
        self.scripts.append((kind, answer))

    def _on(self, dlg):
        self.records.append((dlg.type, dlg.message))
        if self.scripts:
            kind, ans = self.scripts.pop(0)
        else:
            kind, ans = ("dismiss", None)
        try:
            if kind == "prompt":
                dlg.accept(ans)
            elif kind == "confirm":
                (dlg.accept if ans else dlg.dismiss)()
            elif kind == "accept":
                dlg.accept()
            else:
                dlg.dismiss()
        except Exception:
            # already handled 防御
            pass

    def count(self):
        return len(self.records)

    def clear(self):
        self.records.clear()

    def messages(self):
        return [m for _, m in self.records]


def fresh_page(browser, width=1400, height=900, downloads=False):
    ctx = browser.new_context(viewport={"width": width, "height": height},
                              accept_downloads=downloads)
    page = ctx.new_page()
    errs = []
    cons = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.on("console", lambda m: cons.append(m.text) if m.type == "error" else None)
    return ctx, page, errs, cons


def goto(page):
    build_fixture()   # 每次都从最新代码重建夹具（示例数据）
    page.goto(FIXTURE_URL)
    page.wait_for_load_state("domcontentloaded")
    page.evaluate("() => { localStorage.clear(); }")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    return page


class CheckFailure(AssertionError):
    pass


def check(cond, msg, detail=""):
    if not cond:
        raise CheckFailure(f"{msg}  {detail}")


RUNNERS = []


def testcase(fn):
    RUNNERS.append(fn)
    return fn


def run_module(module_or_globals, title):
    """执行本文件中 @testcase 注册的全部用例；返回是否全绿。"""
    if not isinstance(module_or_globals, dict):
        module_or_globals = vars(module_or_globals)
    ok = True
    print(f"===== {title} =====")
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        for fn in module_or_globals["RUNNERS"]:
            name = fn.__name__
            t0 = time.time()
            try:
                fn(b)
                print(f"  PASS {name}  ({time.time()-t0:.1f}s)")
            except Exception as e:
                ok = False
                print(f"  FAIL {name}: {e}")
                traceback.print_exc(limit=3)
        b.close()
    return ok
