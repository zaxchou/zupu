# -*- coding: utf-8 -*-
"""世祖独立于字辈：十世起用、输出一致、临时分支和旧配置迁移。"""
from helper import *
import json
import os
import re
import shutil
import sys


def generation_fixture(page):
    app = open(LOCAL_HTML, encoding='utf-8').read()
    root = {'id': 'root', 'name': '家族族谱', 'spouses': [], 'expanded': True, 'children': []}
    fixture, count = re.subn(r'(<script id="__treeData" type="application/json">)[\s\S]*?(\n</script>)',
                            lambda m: m.group(1) + '\n' + json.dumps(root, ensure_ascii=False) + '\n' + m.group(2),
                            app, count=1)
    assert count == 1
    os.makedirs(LOCAL_OUT, exist_ok=True)
    with open(os.path.join(LOCAL_OUT, 'fixture_generation_independent.html'), 'w', encoding='utf-8') as f:
        f.write(fixture)
    page.goto(OUT_DIR + '/fixture_generation_independent.html')
    page.wait_for_load_state('domcontentloaded')
    return page.evaluate("""() => {
      let children = [];
      for (let gen = 12; gen >= 1; gen--){
        const name = gen === 1 ? '周修' : gen === 10 ? '周勤' : gen === 11 ? '周修' : gen === 12 ? '周昭' : '祖先' + gen;
        children = [{ id: 'g' + gen, name, spouses: [], expanded: true, children }];
      }
      treeData.children = children; treeData.zibei = ['勤', '修', '昭']; migrate(treeData);
      cfg.zibeiStart = 1; cfg.vertical = false; cfg.cnNum = false; render(); saveData();
      return JSON.stringify(sanitize(treeData));
    }""")


def set_start(page, start):
    page.evaluate('openSettings()')
    if page.locator('#__cfgOther').get_attribute('open') is None:
        page.locator('#__cfgOther summary').click()
    page.locator('#__cfgBase').fill(str(start))
    page.locator('#__setDone').click()


@testcase
def t_tenth_generation_and_migration(b):
    ctx, page, errs, cons = fresh_page(b)
    original = generation_fixture(page)
    set_start(page, 10)
    info = page.evaluate('Array.from(computeGenerations(), ([id, g]) => ({id, ...g}))')
    check([g['gen'] for g in info] == list(range(1, 13)), '所有世祖从一世起且父子加一')
    check([g['ziIndex'] for g in info] == [-1] * 9 + [0, 1, 2], '十世起用之前 ziIndex 为 -1')
    check([g['zi'] for g in info] == [''] * 9 + list('勤修昭'), '字辈字只按对应诗位取字')
    check(info[0]['src'] == 'depth' and info[9]['src'] == 'match', '名字只印证字辈，提前误命中不改世祖')
    for gen in range(1, 13):
        node = page.locator(f'#stage .node[data-id="g{gen}"]')
        check(node.locator('.gen').inner_text() == f'{gen}世', '卡片世祖独立编号')
        expected = '' if gen < 10 else f'辈序{gen - 9}·' + '勤修昭'[gen - 10]
        check(node.locator('.zibei').text_content() == expected, '卡片独立辈序正确')
    check(page.locator('#stage .node[data-id="root"] .gen, #stage .node[data-id="root"] .zibei').count() == 0,
          '谱名容器没有世祖或辈序')
    check(page.evaluate("getComputedStyle(document.querySelector('#stage .node[data-id=\"g1\"] .zibei')).display") == 'none',
          '起用之前的空辈序不占位（不留下空隙）')
    tip = page.locator('#stage .node[data-id="g1"] .gen').get_attribute('title')
    check('核对' not in tip and '1世' in tip and '尚未起用字辈' in tip,
          '起用前误命中字辈只显示留空说明，不产生冲突警告', tip)
    check(all('ziConflict' not in g for g in info[:9]), '起用之前没有字辈冲突')
    check(page.evaluate('JSON.stringify(sanitize(treeData))') == original, '起用设置不修改原始族谱数据')
    stored = page.evaluate('JSON.parse(localStorage.getItem(CFG_KEY))')
    check(stored['zibeiStart'] == stored['genBase'] == 10, '新配置与旧兼容别名一起保存')
    page.reload(); page.wait_for_load_state('domcontentloaded')
    check(page.evaluate('[cfg.zibeiStart, cfg.genBase]') == [10, 10], '新设置刷新持久')
    check(page.locator('#stage .node[data-id="g10"] .zibei').inner_text() == '辈序1·勤', '刷新后十世仍第一辈')
    page.evaluate("localStorage.setItem(CFG_KEY, JSON.stringify({genBase:10}))")
    page.reload(); page.wait_for_load_state('domcontentloaded')
    check(page.evaluate('[cfg.zibeiStart, cfg.genBase]') == [10, 10], '旧 genBase 配置迁移为起用世数')
    check(page.locator('#stage .node[data-id="g1"] .gen').inner_text() == '1世', '旧配置迁移不偏移世祖')
    page.evaluate("localStorage.setItem(CFG_KEY, JSON.stringify({genBase:13,zibeiStart:10}))")
    page.reload(); page.wait_for_load_state('domcontentloaded')
    check(page.evaluate('[cfg.zibeiStart, cfg.genBase]') == [10, 10], '新字段优先于旧别名')
    check(page.evaluate('JSON.stringify(sanitize(treeData))') == original, '刷新和迁移不修改族谱数据')
    check(not errs, '无 JS 错误', str(errs))
    ctx.close()


@testcase
def t_generation_outputs_and_branch(b):
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    original = generation_fixture(page)
    set_start(page, 10)
    page.evaluate('buildPrintDomReal()')
    check(page.locator('#printArea .pgen').all_text_contents() == [f'{i}世' for i in range(1, 13)],
          '大纲打印世祖独立编号')
    check(page.locator('#printArea .pzibei').all_text_contents() == ['辈序1·勤', '辈序2·修', '辈序3·昭'],
          '大纲打印独立辈序，之前留空')
    drawn = page.evaluate("""async () => {
      const texts = [], original = CanvasRenderingContext2D.prototype.fillText;
      CanvasRenderingContext2D.prototype.fillText = function(t, ...args){ texts.push(String(t)); return original.call(this, t, ...args); };
      try { await exportTreeCanvas(); return texts; }
      finally { CanvasRenderingContext2D.prototype.fillText = original; }
    }""")
    check(all(f'{i}世' in drawn for i in range(1, 13)), 'PNG/PDF 共用 painter 绘制实际世祖')
    check(all(t in drawn for t in ['辈序1·勤', '辈序2·修', '辈序3·昭']), 'painter 独立绘制辈序')
    with page.expect_download() as dl:
        page.evaluate('exportShixilu()')
    html = open(dl.value.path(), encoding='utf-8').read()
    check('<th>世次</th><th>辈序</th>' in html, '世系录独立世次与辈序列')
    check('<td class="c">一世</td><td class="c"></td>' in html, '世系录起用前辈序为空')
    check('<td class="c">十世</td><td class="c">辈序一·勤</td>' in html, '世系录十世第一辈')
    check('第一世至第五世' in html and '第六世至第十世' in html and '第十一世至第十五世' in html,
          '五世分表不受起用设置影响')
    page.evaluate('cfg.vertical = true; render(); buildPrintDomReal()')
    expected = ['一世', '二世', '三世', '四世', '五世', '六世', '七世', '八世', '九世',
                '十世', '十一世', '十二世']
    exp_zi = ['辈序一·勤', '辈序二·修', '辈序三·昭']
    check(page.locator('#stage .vrow.row-gen').all_text_contents() == expected, '竖排世祖单独成列')
    check(page.locator('#stage .vrow.row-zibei').all_text_contents() == exp_zi, '辈序独立成列且起用前为空')
    check(page.locator('#printArea .vrow.row-gen').all_text_contents() == expected, '竖排打印世祖同步')
    check(page.locator('#printArea .vrow.row-zibei').all_text_contents() == exp_zi, '竖排打印辈序同步')
    before = page.evaluate("({cfg:JSON.stringify(cfg), storage:localStorage.getItem(CFG_KEY), gens:JSON.stringify(Array.from(LAST_GENS))})")
    branch = page.evaluate("""() => withTempRender(buildSubtreeData(findNode('g9')), () => ({
      gens: Array.from(computeGenerations().values()),
      rows: rowMarkers.map(m => m.text),
      cfg: JSON.stringify(cfg)
    }))""")
    check([g['gen'] for g in branch['gens']] == [9, 10, 11, 12], '分支根保留原九世祖，depth0计入')
    check([g['ziIndex'] for g in branch['gens']] == [-1, 0, 1, 2], '分支沿用主树起用设置')
    check(branch['rows'] == ['九世', '十世 · 辈序一·勤', '十一世 · 辈序二·修', '十二世 · 辈序三·昭'],
          '分支竖排行标包含根的九世')
    check(branch['cfg'] == before['cfg'], '临时分支不改配置')
    after = page.evaluate("({cfg:JSON.stringify(cfg), storage:localStorage.getItem(CFG_KEY), gens:JSON.stringify(Array.from(LAST_GENS))})")
    check(after == before, '临时分支恢复主树世祖缓存和配置，无保存副作用')
    check(page.evaluate('JSON.stringify(sanitize(treeData))') == original, '所有显示和导出不改原始数据')
    check(not errs, '无 JS 错误', str(errs))
    ctx.close()


@testcase
def t_no_zibei_keeps_generations(b):
    ctx, page, errs, cons = fresh_page(b)
    generation_fixture(page)
    check(page.evaluate("!computeGenerations().get('g12').ziConflict"), '字辈诗用尽之后不误报字辈冲突')
    check('核对' not in page.locator('#stage .node[data-id="g12"] .gen').get_attribute('title'),
          '诗用尽之后的提示不包含冲突警告')
    page.evaluate('delete treeData.zibei; cfg.zibeiStart = 10; render()')
    check(page.evaluate('Array.from(computeGenerations().values(), g => g.gen)') == list(range(1, 13)),
          '没有字辈表也计算完整世祖')
    check(page.locator('#stage .gen').all_text_contents() == [f'{i}世' for i in range(1, 13)], '无表也显示一至十二世')
    check(all(t == '' for t in page.locator('#stage .zibei').all_text_contents()), '无表所有字辈为空')
    check(not errs, '无 JS 错误', str(errs))
    ctx.close()


@testcase
def t_markdown_and_external_root_id(b):
    """导回 Markdown / 外部 JSON 后根容器 id 归一：谱名不被当成一世祖，世数不整体偏移"""
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    generation_fixture(page)
    set_start(page, 10)
    before = page.evaluate("""() => ({
      id: treeData.id,
      gens: Array.from(computeGenerations().values(), g => [g.gen, g.ziIndex, g.zi]),
      stats: document.getElementById('statsChip').textContent,
      labels: Array.from(document.querySelectorAll('#stage .gen'), e => e.textContent)
        .concat(Array.from(document.querySelectorAll('#stage .zibei'), e => e.textContent))
    })""")
    with page.expect_download() as dl:
        page.evaluate('exportMarkdown()')
    md = os.path.join(LOCAL_OUT, 'generation_independent.md')
    shutil.copyfile(dl.value.path(), md)
    page.locator('#__importFile').set_input_files(md)
    page.wait_for_function(
        "() => window.__ZP.data.children[0] && window.__ZP.data.children[0].id.indexOf('r_') === 0",
        timeout=5000)
    after = page.evaluate("""() => ({
      id: treeData.id,
      gens: Array.from(computeGenerations().values(), g => [g.gen, g.ziIndex, g.zi]),
      stats: document.getElementById('statsChip').textContent,
      labels: Array.from(document.querySelectorAll('#stage .gen'), e => e.textContent)
        .concat(Array.from(document.querySelectorAll('#stage .zibei'), e => e.textContent))
    })""")
    check(after['id'] == 'root', '导回 Markdown 后根容器 id 归一为 root', after['id'])
    check(after == before, '导回后世祖、辈序与统计完全不变', str(after)[:300])
    check(page.locator('#stage .node[data-id="root"] .gen').count() == 0, '导回后谱名容器不冒充一世祖')

    ext = page.evaluate("""() => {
      const d = migrate({ id: 'external-root', name: '外部族谱', spouses: [], expanded: true,
        children: [{ id: 'root', name: '甲', spouses: [], expanded: true, children: [
          { id: 'b', name: '乙', spouses: [], expanded: true, children: [] } ] }] });
      treeData = d; selectedId = null; render();
      return { rootId: d.id, firstId: d.children[0].id,
               gens: Array.from(computeGenerations().values(), g => g.gen),
               rootChips: document.querySelectorAll('#stage .node[data-id="root"] .gen').length,
               stats: document.getElementById('statsChip').textContent };
    }""")
    check(ext['rootId'] == 'root', '外部 JSON 根 id 归一为 root', str(ext))
    check(ext['firstId'] != 'root', '子节点里原有的 root id 改发新 id，保持唯一', str(ext))
    check(ext['gens'] == [1, 2], '外部 JSON 世祖从第一层真实成员起算', str(ext))
    check(ext['rootChips'] == 0 and '2 位成员' in ext['stats'], '标题容器不计成员、不带世祖角标', str(ext))
    check(not errs, '无 JS 错误', str(errs))
    ctx.close()


if __name__ == '__main__':
    sys.exit(0 if run_module(sys.modules[__name__], 't_generation_independent 世祖与字辈独立') else 1)
