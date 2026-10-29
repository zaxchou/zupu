# -*- coding: utf-8 -*-
"""即时视觉设置、四向真实布局、方向拖拽/命中与导出/打印回归。"""
from helper import *
from pathlib import Path
import re


def choose(page, direction, vertical=False):
    page.locator('#btnView').click()
    page.locator('#__ctxMenu .mi', has_text='视觉设置').click()
    page.locator('[data-cfg-direction="%s"]' % direction).click()
    page.locator('[data-cfg-vertical="%s"]' % str(vertical).lower()).click()
    page.locator('#__setDone').click()


@testcase
def t_instant_settings_camera_and_persistence(b):
    ctx, page, errs, _ = fresh_page(b)
    goto(page)
    page.evaluate("() => { scale=.73; applyZoom(); centerStage(); const vp=document.getElementById('viewport'); vp.scrollBy(81,53); }")
    camera = lambda: page.evaluate("[scale,document.getElementById('viewport').scrollLeft,document.getElementById('viewport').scrollTop]")
    before = camera()
    page.locator('#btnView').click()
    page.locator('#__ctxMenu .mi', has_text='视觉设置').click()
    check(not page.locator('#__cfgOther').get_attribute('open'), '其他显示项默认收起')
    check(page.locator('#__setSave,#__setCancel').count() == 0, '无保存/取消步骤')
    page.locator('[data-cfg-direction="right"]').click()
    page.locator('[data-cfg-theme="dark"]').click()
    check(page.evaluate("cfg.direction === 'right' && document.body.dataset.theme === 'dark'"), '点击立即预览')
    check(page.evaluate("JSON.parse(localStorage.getItem(CFG_KEY)).direction") == 'right', '未关闭即持久化')
    check(camera() == before, '预览保持镜头', str((before, camera())))
    page.keyboard.press('Escape')
    check(camera() == before, '关闭保留镜头')
    page.reload()
    check(page.evaluate("cfg.direction === 'right' && cfg.theme === 'dark' && !cfg.vertical"), '刷新持久且竖排独立')
    check(not errs, '无JS错误', str(errs))
    ctx.close()


@testcase
def t_four_directions_geometry_fit_and_outputs(b):
    ctx, page, errs, _ = fresh_page(b, downloads=True)
    goto(page)
    for vertical in [False, True]:
        for direction in ['down', 'up', 'right', 'left']:
            choose(page, direction, vertical)
            data = page.evaluate("""() => {
              const r=id=>nodeRects.get(id), st=document.getElementById('stage');
              let bounds=true, edges=true;
              nodeRects.forEach(q=>{ if(q.x-q.w/2 < 0 || q.x+q.w/2 > st._baseW || q.y < 0 || q.y+q.h > st._baseH) bounds=false; });
              edgeSegments.forEach(([x,y,xx,yy])=>{if (![x,y,xx,yy].every(Number.isFinite) || (x!==xx && y!==yy)) edges=false;});
              return {root:r('root'), a:r('b1'), b:r('b2'), c:r('b1a'), bounds,edges,
                writing:getComputedStyle(document.querySelector('[data-id="b1"] .node-label')).writingMode,
                order:treeData.children.map(n=>n.id)};
            }""")
            check(data['bounds'] and data['edges'], '有效边界与正交连线', str((direction, vertical, data)))
            r, a, c = data['root'], data['a'], data['c']
            if direction == 'down':
                check(a['y'] > r['y'] + r['h'] and c['y'] > a['y'] + a['h'], '向下世代')
            elif direction == 'up':
                check(a['y'] + a['h'] < r['y'] and c['y'] + c['h'] < a['y'], '向上世代')
            elif direction == 'right':
                check(a['x'] - a['w']/2 > r['x'] + r['w']/2 and c['x'] > a['x'], '向右世代')
            else:
                check(a['x'] + a['w']/2 < r['x'] - r['w']/2 and c['x'] < a['x'], '向左世代')
            axis = 'y' if direction in ['right', 'left'] else 'x'
            check(a[axis] < data['b'][axis], '同辈保持原顺序')
            check(data['order'] == ['b1', 'b2', 'b3', 'note'], '方向不改变亲子/长幼数据')
            check(data['writing'] == ('vertical-rl' if vertical else 'horizontal-tb'), '文字不随方向旋转')
            page.evaluate('fitToScreen()')
            first = page.evaluate('scale')
            page.evaluate('fitToScreen()')
            check(abs(first-page.evaluate('scale')) < 1e-9, '重复fit不漂移')
            # 导出在镜头改变后仍是同一套世界坐标和图片尺寸。
            size1 = page.evaluate('() => { const c=exportTreeCanvas();return [c.width,c.height]; }')
            page.evaluate('() => { scale=1.54;applyZoom(); }')
            size2 = page.evaluate('() => { const c=exportTreeCanvas();return [c.width,c.height]; }')
            check(size1 == size2, '导出尺寸不受镜头影响', str((size1,size2)))
            for kind in ['PNG', 'PDF']:
                with page.expect_download() as dl:
                    page.evaluate('export%s()' % kind)
                path = Path(LOCAL_OUT)/('visual_%s_%s.%s' % (direction, vertical, kind.lower()))
                dl.value.save_as(str(path))
                raw = path.read_bytes()
                check(raw.startswith(b'\x89PNG' if kind == 'PNG' else b'%PDF-'), '方向文件签名')
                if kind == 'PDF':
                    m = re.search(rb'/MediaBox \[0 0 (\d+) (\d+)\]', raw)
                    check(m and abs(int(m[1])-round(size1[0]*.75)) <= 1, 'PDF尺寸来自方向图谱')
            page.evaluate('buildPrintDomReal()')
            if vertical or direction != 'down':
                check(page.locator('#printArea .ps .node').count() == 13, '方向打印克隆完整图谱')
                check(page.evaluate("getComputedStyle(document.querySelector('#printArea #scaler')).zoom") == '1', '打印清除镜头倍率')
                check(page.locator('#printArea .ps').get_attribute('data-direction') == direction, '打印保留方向')
            else:
                check(page.locator('#printArea li').count() == 13, '默认向下大纲行为保留')
    check(not errs, '无JS错误', str(errs))
    ctx.close()


@testcase
def t_direction_drag_reorder_and_reparent_at_zoom(b):
    ctx, page, errs, _ = fresh_page(b, 1500, 1000)
    goto(page)
    for direction in ['down', 'up', 'right', 'left']:
        choose(page, direction)
        page.evaluate('() => {scale=.65;applyZoom();centerStage()}')
        source = page.locator('[data-id="b1a1"] .node-label').bounding_box()
        target = page.locator('[data-id="b1a2"] .node-label').bounding_box()
        sx, sy = source['x']+source['width']/2, source['y']+source['height']/2
        tx, ty = target['x']+target['width']/2, target['y']+target['height']/2
        if direction in ['left','right']:
            ty += target['height']/2 + 22
        else:
            tx += target['width']/2 + 22
        page.mouse.move(sx,sy);page.mouse.down();page.mouse.move(tx,ty,steps=8)
        delta = page.evaluate("() => {const n=findNode('b1a1'),e=document.querySelector('[data-id=\"b1a1\"]');return [parseFloat(e.style.left)-n._x,parseFloat(e.style.top)-n._y]}")
        check(abs(delta[0]-(tx-sx)/.65)<1 and abs(delta[1]-(ty-sy)/.65)<1, '拖动按世界坐标跟随', str(delta))
        page.mouse.up()
        check(page.evaluate("findNode('b1a').children.map(n=>n.id)") == ['b1a2','b1a1'], '方向内拖拽调整长幼', direction)
        page.evaluate('undo()')
        page.wait_for_timeout(360)
        # 过继：真实鼠标停留在目标中心，验证CSS zoom下数学命中。
        source = page.locator('[data-id="b1a1"] .node-label').bounding_box()
        target = page.locator('[data-id="b2a"] .node-label').bounding_box()
        page.mouse.move(source['x']+source['width']/2,source['y']+source['height']/2)
        page.mouse.down()
        page.mouse.move(target['x']+target['width']/2,target['y']+target['height']/2,steps=8)
        page.wait_for_timeout(450)
        check('drop-target' in page.locator('[data-id="b2a"]').get_attribute('class'), '方向过继命中', direction)
        page.mouse.up()
        check(page.evaluate("findParent('b1a1').id") == 'b2a', '过继父子关系正确', direction)
        page.evaluate('undo()')
        page.wait_for_timeout(360)
    check(not errs, '无JS错误', str(errs))
    ctx.close()


@testcase
def t_zoom_support_fallback_and_measurement_stability(b):
    ctx, page, errs, _ = fresh_page(b)
    goto(page)
    before = page.evaluate('Array.from(nodeRects)')
    page.evaluate('() => {scale=1.54;applyZoom();render()}')
    check(page.evaluate('Array.from(nodeRects)') == before, '放大后重绘保持基准布局')
    check(page.evaluate("getComputedStyle(document.getElementById('scaler')).willChange") == 'auto', '无常驻合成层提示')
    check(page.evaluate("getComputedStyle(document.getElementById('scaler')).transform") == 'none', '支持浏览器使用排版缩放')
    page.screenshot(path=str(Path(LOCAL_OUT)/'text_zoom_154.png'))
    page.evaluate("() => {const original=CSS.supports;window.__restoreSupport=()=>CSS.supports=original;CSS.supports=()=>false;applyZoom()}")
    check(page.evaluate("document.getElementById('scaler').style.transform") == 'scale(1.54)', '不支持zoom时变换回退')
    page.screenshot(path=str(Path(LOCAL_OUT)/'text_transform_154.png'))
    page.evaluate('__restoreSupport()')
    check(not errs, '无JS错误', str(errs))
    ctx.close()


@testcase
def t_keyboard_storage_failure_and_selected_anchor(b):
    ctx, page, errs, _ = fresh_page(b)
    goto(page)
    page.locator('[data-id="b2"] .node-label').click()
    point = lambda: page.evaluate("() => {const q=document.querySelector('[data-id=\"b2\"] .node-label').getBoundingClientRect();return [q.x+q.width/2,q.y+q.height/2]}")
    original = point()
    page.evaluate('openSettings()')
    page.locator('[data-cfg-direction="left"]').focus()
    page.keyboard.press('Enter')
    check(page.evaluate("cfg.direction") == 'left', 'Enter激活方向按钮')
    check(page.locator('#__setModal').is_visible(), '键盘选中不关闭面板')
    moved = point()
    check(max(abs(a-b) for a,b in zip(original,moved)) < 3, '方向切换保持选中成员屏幕位置', str((original,moved)))
    page.locator('#__cfgOther summary').focus();page.keyboard.press('Enter')
    check(page.locator('#__cfgOther').get_attribute('open') is not None, 'Enter展开其他显示项')
    page.evaluate("() => {const orig=Storage.prototype.setItem;window.__restoreStorage=()=>{Storage.prototype.setItem=orig;};Storage.prototype.setItem=function(k,v){if(k===CFG_KEY)throw Error('blocked');return orig.call(this,k,v)}}")
    page.locator('[data-cfg-theme="dark"]').click()
    check(page.evaluate("cfg.theme") == 'dark', '保存失败仍保留预览')
    check(page.locator('#__cfgSaveStatus').is_visible() and not page.locator('#__cfgSavedNote').is_visible(), '设置保存失败有局部真实状态')
    page.evaluate('__restoreStorage()')
    page.locator('#__cfgRetry').click()
    check(not page.locator('#__cfgSaveStatus').is_visible(), '重试成功清除失败状态')
    check(page.evaluate("JSON.parse(localStorage.getItem(CFG_KEY)).theme") == 'dark', '重试保存当前预览')
    check(not errs, '无JS错误', str(errs))
    ctx.close()


@testcase
def t_fit_avoids_overlays_on_mobile_and_resize(b):
    ctx, page, errs, _ = fresh_page(b, 1280, 720)
    goto(page)
    for width,height in [(1280,720),(390,844),(1100,700)]:
        page.set_viewport_size({'width':width,'height':height})
        page.wait_for_timeout(100)
        page.evaluate('fitToScreen()')
        result = page.evaluate("""() => {const area=availableCanvasRect(),vp=document.getElementById('viewport').getBoundingClientRect();let ok=true;nodeRects.forEach((r,id)=>{const q=document.querySelector('[data-id="'+id+'"] .node-label').getBoundingClientRect();if(q.top<vp.top+area.top-1 || q.bottom>vp.top+area.top+area.height+1 || q.left<vp.left+area.left-1 || q.right>vp.left+area.left+area.width+1)ok=false;});return {ok,area};}""")
        check(result['ok'], 'fit避开工具栏与底部浮层', str((width,result)))
    check(not errs, '无JS错误', str(errs));ctx.close()


@testcase
def t_horizontal_book_export_generation_marker(b):
    ctx, page, errs, _ = fresh_page(b)
    goto(page)
    page.evaluate("() => {treeData.children=[{id:'single',name:'周勤甲',expanded:true,spouses:[],children:[]}];treeData.zibei=['勤'];cfg.genBase=23;render()}")
    for direction in ['right','left']:
        choose(page,direction,True)
        result = page.evaluate("""() => {const draws=[],proto=CanvasRenderingContext2D.prototype,original=proto.fillText;proto.fillText=function(t,x,y){draws.push({t:String(t),x,y});return original.apply(this,arguments)};try{exportTreeCanvas()}finally{proto.fillText=original}const m=rowMarkers[0],r=nodeRects.get('single');return {draws,m,r,writing:getComputedStyle(document.querySelector('.vrow')).writingMode};}""")
        marker = [t for t in result['draws'] if t['t'] == '廿三世·勤']
        check(len(marker) == 1, '图片世数标整条横排绘制', str(result['draws']))
        check(marker[0]['y']+10 < result['r']['y'], '世数标与姓名无垂直重叠')
        check(result['writing'] == 'horizontal-tb', 'DOM世数标与导出一致')
    check(not errs, '无JS错误', str(errs));ctx.close()


if __name__ == '__main__':
    import sys
    sys.exit(0 if run_module(globals(), 't_visual 即时视觉设置与四向布局') else 1)
