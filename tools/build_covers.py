# -*- coding: utf-8 -*-
"""从 docs/_cover.html（中文封面源）生成 docs/_cover-en.html / docs/_cover-ja.html。
替换带断言，失配即报错。渲染 PNG 由调用方用 Playwright 完成。"""
import io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'docs', '_cover.html')

EN = [
  ('<html lang="zh">', '<html lang="en">'),
  ('font-family:"PingFang SC","Microsoft YaHei",sans-serif;', 'font-family:"Segoe UI",Arial,sans-serif;'),
  ('"Songti SC","SimSun",serif', 'Georgia,"Times New Roman",serif', 3),
  ('text-orientation:upright', 'text-orientation:mixed', 3),   # 拉丁字母书脊式（旋转 90°，可读）
  ('font-size:96px;letter-spacing:18px;color:#29231c;', 'font-size:64px;letter-spacing:6px;line-height:1.15;color:#29231c;'),
  ('font-size:22px;font-weight:700;color:#29231c;background:', 'font-size:15px;font-weight:700;color:#29231c;background:'),
  ('font-size:76px;font-weight:700;color:#1f1b14;letter-spacing:4px', 'font-size:72px;font-weight:700;color:#1f1b14;letter-spacing:0'),
  ('letter-spacing:10px;color:#8a6a2a', 'letter-spacing:3px;color:#8a6a2a'),
  ('letter-spacing:2px}\n  .desc b', 'letter-spacing:.5px}\n  .desc b'),
  ('<b>开源</b> · 单文件 · 本地优先 · 无账号', '<b>Open source</b> · Single file · Local-first · No account'),
  ('<h1>家族族谱 · 传代树</h1>', '<h1>Family Tree</h1>'),
  ('零依赖 · <b>谱书竖排（古法）</b> · 字辈定代 · 五世一表世系录 · 无感自动保存',
   'Zero dependencies · <b>Vertical book layout</b> · Zibei generations · Auto-save'),
  ('<div class="chip">常规传代树</div><div class="chip">谱书竖排</div>',
   '<div class="chip">Standard tree</div><div class="chip">Vertical book</div>'),
  ('<div class="chip">字辈定代</div><div class="chip">PNG / PDF / 世系录</div>',
   '<div class="chip">Zibei generations</div><div class="chip">PNG / PDF / Tables</div>'),
  ('>第一代<', '>Gen 1<'), ('>第二代<', '>Gen 2<'), ('>第三代<', '>Gen 3<'), ('>第四代<', '>Gen 4<'),
  ('>德祖<', '>Arthur<'), ('>承业<', '>James<'), ('>传家<', '>Robert<'), ('>世泽<', '>Michael<'),
  ('测试用例', 'tests'),
  ('<span>传</span><span>家</span><span>之</span><span>谱</span>',
   '<span>Z</span><span>U</span><span>P</span><span>U</span>'),
  ('<div class="title-v">家族族谱</div>', '<div class="title-v">FAMILY<br>TREE</div>'),
]

JA = [
  ('<html lang="zh">', '<html lang="ja">'),
  ('font-family:"PingFang SC","Microsoft YaHei",sans-serif;',
   'font-family:"Hiragino Kaku Gothic ProN","Yu Gothic","Microsoft YaHei",sans-serif;'),
  ('"Songti SC","SimSun",serif', '"Yu Mincho","Hiragino Mincho ProN","MS Mincho",serif', 3),
  ('font-family:"KaiTi","STKaiti","SimSun",serif', 'font-family:"Yu Mincho","MS Mincho",serif'),
  ('letter-spacing:10px;color:#8a6a2a', 'letter-spacing:5px;color:#8a6a2a'),
  ('<b>开源</b> · 单文件 · 本地优先 · 无账号', '<b>オープンソース</b> · 単一ファイル · ローカル優先 · アカウント不要'),
  ('<h1>家族族谱 · 传代树</h1>', '<h1>家系図・伝代ツリー</h1>'),
  ('零依赖 · <b>谱书竖排（古法）</b> · 字辈定代 · 五世一表世系录 · 无感自动保存',
   '依存ゼロ · <b>譜書縦書き（古法）</b> · 字輩世代判定 · 五世一表・世系録 · 自動保存'),
  ('<div class="chip">常规传代树</div><div class="chip">谱书竖排</div>',
   '<div class="chip">通常ツリー</div><div class="chip">譜書縦書き</div>'),
  ('<div class="chip">字辈定代</div><div class="chip">PNG / PDF / 世系录</div>',
   '<div class="chip">字輩世代</div><div class="chip">PNG / PDF / 世系録</div>'),
  ('>第一代<', '>第一世代<'), ('>第二代<', '>第二世代<'), ('>第三代<', '>第三世代<'), ('>第四代<', '>第四世代<'),
  ('>德祖<', '>林家<'), ('>承业<', '>義郎<'), ('>传家<', '>正雄<'), ('>世泽<', '>健太<'),
  ('测试用例', 'テスト'),
  ('<span>传</span><span>家</span><span>之</span><span>谱</span>',
   '<span>家</span><span>系</span><span>図</span><span>譜</span>'),
  ('<div class="title-v">家族族谱</div>', '<div class="title-v">家系図</div>'),
]

def build(table, out):
    s = io.open(SRC, encoding='utf-8').read()
    errs = []
    for item in table:
        old, new = item[0], item[1]
        want = item[2] if len(item) > 2 else 1
        n = s.count(old)
        if n != want:
            errs.append('x%d (want x%d): %r' % (n, want, old[:50]))
            continue
        s = s.replace(old, new)
    if errs:
        print(out, 'FAIL')
        for e in errs: print('  ' + e)
        return False
    io.open(os.path.join(ROOT, 'docs', out), 'w', encoding='utf-8', newline='').write(s)
    print(out, 'OK')
    return True

def build_hant_cover():
    """繁体封面：整文件 s2twp + 台湾正黑/明体字体替换。"""
    from opencc import OpenCC
    cc = OpenCC('s2twp')
    s = cc.convert(io.open(SRC, encoding='utf-8').read())
    pairs = [
      ('<html lang="zh">', '<html lang="zh-Hant">'),
      ('font-family:"PingFang SC","Microsoft YaHei",sans-serif;',
       'font-family:"PingFang TC","Microsoft JhengHei",sans-serif;'),
      ('"Songti SC","SimSun",serif', '"Songti TC","PMingLiU","SimSun",serif', 3),
      ('font-family:"KaiTi","STKaiti","SimSun",serif', 'font-family:"PMingLiU","KaiTi",serif'),
      ('賬號', '帳號'),
    ]
    errs = []
    for item in pairs:
        old, new = item[0], item[1]
        want = item[2] if len(item) > 2 else 1
        n = s.count(old)
        if n != want:
            errs.append('x%d (want x%d): %r' % (n, want, old[:40]))
            continue
        s = s.replace(old, new)
    if errs:
        print('_cover-zh-Hant.html FAIL')
        for e in errs: print('  ' + e)
        return False
    io.open(os.path.join(ROOT, 'docs', '_cover-zh-Hant.html'), 'w', encoding='utf-8', newline='').write(s)
    print('_cover-zh-Hant.html OK')
    return True

if __name__ == '__main__':
    # 版本与用例数只维护在中文源里，其余语言继承
    src = io.open(SRC, encoding='utf-8').read()
    if 'v15.33' not in src:   # 幂等：已升级则跳过
        for old, new in [('v15.32', 'v15.33'), ('52 测试用例', '53 测试用例')]:
            assert src.count(old) == 1, old
            src = src.replace(old, new)
        io.open(SRC, 'w', encoding='utf-8', newline='').write(src)
    ok = build(EN, '_cover-en.html') & build(JA, '_cover-ja.html') & build_hant_cover()
    sys.exit(0 if ok else 1)
