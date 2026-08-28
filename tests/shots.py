# -*- coding: utf-8 -*-
"""视觉核对截图：初始视图 / 视图下拉 / 文件下拉 / 帮助弹窗 / 折叠态"""
from helper import *
import os

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_out")
os.makedirs(out, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    goto(page)
    page.wait_for_timeout(600)
    page.screenshot(path=os.path.join(out, "shot_1_initial.png"))

    page.locator("#btnFile").click()
    page.wait_for_timeout(250)
    page.screenshot(path=os.path.join(out, "shot_2_filemenu.png"))
    page.keyboard.press("Escape")

    page.locator("#btnView").click()
    page.wait_for_timeout(250)
    page.screenshot(path=os.path.join(out, "shot_3_viewmenu.png"))
    page.keyboard.press("Escape")

    page.locator('button[title="帮助 / 快捷键"]').click()
    page.wait_for_timeout(250)
    page.screenshot(path=os.path.join(out, "shot_4_help.png"))
    page.keyboard.press("Escape")

    # 折叠态
    page.locator('.node[data-id="b1"] .quick-add').click()
    page.locator('#__ctxMenu .mi', has_text="折叠").click()
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(out, "shot_5_folded.png"))
    b.close()
print("screenshots done")
