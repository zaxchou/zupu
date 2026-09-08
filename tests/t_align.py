# -*- coding: utf-8 -*-
"""对齐回归（v15.36）：抓「flex 列容器残留行 margin」与「弹窗内子元素右溢」两类 bug。

真实事故：≤860px 下 .wiz-actions 切列向，但基础样式 `>*+*{margin-left:10px}`
未翻转，第二个向导按钮被推右 10px 且右缘溢出。逐弹窗 × 双视口扫描。
"""
from helper import *
import sys as _sys

CHECK_JS = r"""
() => {
  const problems = [];
  document.querySelectorAll('.modal-mask').forEach(m => {
    if (!m.classList.contains('open')) return;
    const mname = m.id || m.className;
    m.querySelectorAll('*').forEach(el => {
      const cs = getComputedStyle(el);
      if ((cs.display === 'flex' || cs.display === 'inline-flex') && cs.flexDirection === 'column') {
        [...el.children].forEach(ch => {
          const ml = parseFloat(getComputedStyle(ch).marginLeft);
          if (ml > 0)
            problems.push(mname + ': 列容器 ' + (el.className || el.tagName) + ' 子元素 ' +
                          (ch.className || ch.tagName) + ' 残留 marginLeft=' + ml);
        });
      }
    });
    const scan = (parent, depth) => {
      if (depth > 3) return;
      const pr = parent.getBoundingClientRect();
      [...parent.children].forEach(ch => {
        const r = ch.getBoundingClientRect();
        if (r.width > 0 && r.right - pr.right > 1)
          problems.push(mname + ': ' + (parent.className || parent.tagName) + ' 子元素 ' +
                        (ch.className || ch.tagName) + ' 右溢 ' + (r.right - pr.right).toFixed(1) + 'px');
        scan(ch, depth + 1);
      });
    };
    const box = m.querySelector('.modal, .uip-box');
    if (box) scan(box, 0);
  });
  return problems;
};
"""

OPEN_JS = {
    'wizard':   "(function(){ openWizard(); })()",
    'profile':  "(function(){ editDetails(treeData); })()",
    'clan':     "(function(){ openClan(); })()",
    'settings': "(function(){ openSettings(); })()",
    'help':     "(function(){ openHelp(); })()",
    'uip':      "(function(){ uiPrompt('测试：'); })()",
    'text':     "(function(){ showTextModal('测试文本', 'abc'); })()",
    'paste':    "(function(){ pasteImport(); })()",
}


@testcase
def t_modal_alignment(b):
    allprobs = []
    for w, h, tag in [(390, 844, 'mobile'), (1100, 700, 'desktop')]:
        ctx, page, errs, cons = fresh_page(b, w, h)
        try:
            goto(page)
            for m, js in OPEN_JS.items():
                try:
                    page.evaluate(js)
                    page.wait_for_timeout(200)
                    for x in page.evaluate(CHECK_JS):
                        allprobs.append('[%s %s] %s' % (tag, m, x))
                finally:
                    page.evaluate("(function(){var e=document.querySelector('.modal-mask.open');"
                                  "if(e)e.classList.remove('open');})()")
                    page.wait_for_timeout(100)
            check(not errs, '无 JS 错误', str(errs[:3]))
        finally:
            ctx.close()
    check(not allprobs, '弹窗对齐（列容器无残留行距、无子元素右溢）', '; '.join(allprobs[:4]))


def _run():
    ok = run_module(_sys.modules[__name__], "t_align 弹窗对齐")
    _sys.exit(0 if ok else 1)


if __name__ == "__main__":
    _run()
