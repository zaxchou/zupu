# -*- coding: utf-8 -*-
"""主题回归（v15.38）：默认羊皮纸、切换暗色、刷新持久化、设置项回填。"""
from helper import *
import sys as _sys


@testcase
def t_theme_default_switch_persist(b):
    ctx, page, errs, cons = fresh_page(b, 1400, 900)
    try:
        goto(page)
        check(page.evaluate("document.body.dataset.theme") == "parchment",
              "默认主题为羊皮纸", page.evaluate("document.body.dataset.theme"))
        # 显示设置里切到暗色
        page.evaluate("(function(){ openSettings(); })()")
        check(page.locator('#__cfgTheme').input_value() == "parchment", "设置项回填当前主题",
              page.locator('#__cfgTheme').input_value())
        page.select_option('#__cfgTheme', 'dark')
        page.click('#__setSave')
        page.wait_for_timeout(250)
        check(page.evaluate("document.body.dataset.theme") == "dark", "切换后立即生效")
        # 刷新后持久（不用 goto——goto 会清 localStorage）
        page.reload()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(300)
        check(page.evaluate("document.body.dataset.theme") == "dark", "刷新后主题持久",
              page.evaluate("document.body.dataset.theme"))
        check(page.evaluate("JSON.parse(localStorage.getItem('zupu_cfg_v1')).theme") == "dark",
              "主题写入 cfg 存储")
        # 切回羊皮纸
        page.evaluate("(function(){ openSettings(); document.getElementById('__cfgTheme').value='parchment'; applySettings(); })()")
        page.wait_for_timeout(200)
        check(page.evaluate("document.body.dataset.theme") == "parchment", "可切回羊皮纸")
        check(not errs, "无 JS 错误", str(errs[:3]))
    finally:
        ctx.close()


def _run():
    ok = run_module(_sys.modules[__name__], "t_theme 配色主题")
    _sys.exit(0 if ok else 1)


if __name__ == "__main__":
    _run()
