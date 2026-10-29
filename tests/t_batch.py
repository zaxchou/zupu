# -*- coding: utf-8 -*-
"""批量添加回归（v15.39）：顺序追加、整批撤销、同辈挂同一父、根节点第一代模式。"""
from helper import *
import sys as _sys


@testcase
def t_batch_add_children_and_undo(b):
    ctx, page, errs, cons = fresh_page(b, 1400, 900)
    try:
        goto(page)
        page.evaluate("(function(){ const n=window.__ZP.findNode('b1'); openMenu(document.querySelector('.node[data-id=\"b1\"]'), n); })()")
        page.wait_for_timeout(200)
        check(page.locator('#__ctxMenu .mi', has_text='批量添加').count() == 1, '右键菜单含「批量添加…」')
        page.locator('#__ctxMenu .mi', has_text='批量添加').click()
        page.wait_for_timeout(250)
        check(page.locator('#__batchModal.open').count() == 1, '批量弹窗打开')
        page.fill('#__batchInput', '测试一，测试二、' + chr(10) + '测试三')
        check(page.locator('#__batchCount').inner_text().strip() == '将添加 3 人', '实时计数',
              page.locator('#__batchCount').inner_text())
        page.click('#__batchOk')
        page.wait_for_timeout(350)
        names = page.evaluate("window.__ZP.findNode('b1').children.map(function(c){return c.name})")
        check(names[-3:] == ['测试一', '测试二', '测试三'], '批量子女按输入顺序追加在既有子女之后', str(names))
        page.keyboard.press('Control+z')
        page.wait_for_timeout(350)
        names2 = page.evaluate("window.__ZP.findNode('b1').children.map(function(c){return c.name})")
        check(len(names2) == len(names) - 3, 'Ctrl+Z 整批撤销', str(names2))
        check(not errs, '无 JS 错误', str(errs[:3]))
    finally:
        ctx.close()


@testcase
def t_batch_siblings_and_root(b):
    ctx, page, errs, cons = fresh_page(b, 1400, 900)
    try:
        goto(page)
        # 同辈批量：挂到同一父下、排在既有同辈之后
        page.evaluate("(function(){ openBatchAdd(window.__ZP.findNode('b1a1')); })()")
        page.evaluate("(function(){ document.querySelectorAll('#__batchRel button')[1].click();"
                      " document.getElementById('__batchInput').value='同辈甲,同辈乙'; updateBatchCount(); })()")
        page.click('#__batchOk')
        page.wait_for_timeout(350)
        sib = page.evaluate("window.__ZP.findNode('b1a').children.map(function(c){return c.name})")
        check(sib[-2:] == ['同辈甲', '同辈乙'], '批量同辈挂同一父且排后', str(sib))
        # 根节点：关系切换隐藏、标题为第一代、批量加第一代
        page.evaluate("(function(){ openBatchAdd(window.__ZP.findNode('root')); })()")
        page.wait_for_timeout(150)
        check(page.evaluate("document.getElementById('__batchRel').style.display") == 'none', '根节点隐藏关系切换')
        check('第一代' in page.locator('#__batchTitle').inner_text(), '根弹窗标题含「第一代」',
              page.locator('#__batchTitle').inner_text())
        page.fill('#__batchInput', '根一,根二')
        page.click('#__batchOk')
        page.wait_for_timeout(350)
        check(page.evaluate("window.__ZP.data.children.length") >= 4, '根节点批量添加第一代成员')
        check(not errs, '无 JS 错误', str(errs[:3]))
    finally:
        ctx.close()


def _run():
    ok = run_module(_sys.modules[__name__], "t_batch 批量添加")
    _sys.exit(0 if ok else 1)


if __name__ == "__main__":
    _run()
