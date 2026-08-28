# -*- coding: utf-8 -*-
"""图谱导出：PNG / PDF 直下载（零弹窗）。断言文件签名、命名、尺寸合理。"""
from helper import *
import os as _os
import shutil as _shutil


def export_and_save(page, menu_text, out_path):
    with page.expect_download() as di:
        page.locator("#btnFile").click()
        page.locator('#__ctxMenu .mi', has_text=menu_text).click()
    _shutil.copyfile(di.value.path(), out_path)
    return di.value.suggested_filename


@testcase
def t_export_png(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    dlg = DialogRecorder(page)
    fn = export_and_save(page, "导出图片", _os.path.join(LOCAL_OUT, "exp.png"))
    import re as _re
    check(_re.match(r"^家族族谱-图-\d{8}-\d{4}\.png$", fn), "png 文件名", fn)
    head = open(_os.path.join(LOCAL_OUT, "exp.png"), "rb").read(8)
    check(head.startswith(b"\x89PNG"), "PNG 签名", str(head))
    size = _os.path.getsize(_os.path.join(LOCAL_OUT, "exp.png"))
    check(size > 20000, "png 有实际内容", str(size))
    check(dlg.count() == 0, "导出零弹窗", str(dlg.records))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_export_pdf(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    fn = export_and_save(page, "导出 PDF", _os.path.join(LOCAL_OUT, "exp.pdf"))
    import re as _re
    check(_re.match(r"^家族族谱-图-\d{8}-\d{4}\.pdf$", fn), "pdf 文件名", fn)
    raw = open(_os.path.join(LOCAL_OUT, "exp.pdf"), "rb").read()
    check(raw[:5] == b"%PDF-", "PDF 签名", str(raw[:8]))
    check(b"/DCTDecode" in raw and b"/MediaBox" in raw, "PDF 结构（内嵌图像+页面）")
    size = _os.path.getsize(_os.path.join(LOCAL_OUT, "exp.pdf"))
    check(size > 15000, "pdf 有实际内容", str(size))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_export_respects_collapsed(b):
    """导出按布局重绘：折叠分支只画折叠角标，不画隐藏节点"""
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto(page)
    page.locator('.node[data-id="b1"] .quick-add').click()
    page.locator('#__ctxMenu .mi', has_text="折叠").click()
    page.wait_for_timeout(200)
    fn = export_and_save(page, "导出图片", _os.path.join(LOCAL_OUT, "exp_fold.png"))
    size = _os.path.getsize(_os.path.join(LOCAL_OUT, "exp_fold.png"))
    check(size > 15000, "折叠态导出成功", str(size))
    # 全展开后再导出，文件应更大（更多卡片）
    page.locator('.node[data-id="b1"] .fold').click()
    page.wait_for_timeout(200)
    fn2 = export_and_save(page, "导出图片", _os.path.join(LOCAL_OUT, "exp_open.png"))
    size2 = _os.path.getsize(_os.path.join(LOCAL_OUT, "exp_open.png"))
    check(size2 > size, "展开后导出内容更多", f"{size} -> {size2}")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()
