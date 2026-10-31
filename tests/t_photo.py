# -*- coding: utf-8 -*-
"""成员照片（第一期）：档案添加/头像/灯箱/开关/批量导入/备份原图/撤销恢复/导出/roundRect 回退。
全部异步等待用 wait_for_function / evaluate(promise)，无固定 sleep。"""
from helper import *
from pathlib import Path
import os
import json
import base64
import struct
import zlib

PHOTO_DIR = os.path.join(LOCAL_OUT, "photos_in")
FALLBACK_JPG = (
    b"\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00\x43\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09\x08\x0a\x0c\x14\x0d\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x23\x1c\x1e\x1f\x22\x26\x2c\x24\x22\x25\x28\x2b\x23\x26\x29\x2a\x29\x29\x27\x2a\x25\x28\x2b\x2d\x2c\x29\x2a\x29\x28\xff\xc0\x00\x11\x08\x00\x60\x00\x60\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01\x7d\x01\x02\x03\x00\x04\x11\x05\x12\x21\x31\x41\x06\x13\x51\x61\x07\x22\x71\x14\x32\x81\x91\xa1\x08\x23\x42\xb1\xc1\x15\x52\xd1\xf0\x24\x33\x62\x72\x82\x09\x0a\x16\x17\x18\x19\x1a\x25\x26\x27\x28\x29\x2a\x34\x35\x36\x37\x38\x39\x3a\x43\x44\x45\x46\x47\x48\x49\x4a\x53\x54\x55\x56\x57\x58\x59\x5a\x63\x64\x65\x66\x67\x68\x69\x6a\x73\x74\x75\x76\x77\x78\x79\x7a\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\xfb\xfa\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\x28\xa2\x8a\xff\xd9"
)


def _make_image(path, size=96, rgb=(255, 0, 0)):
    """生成测试图：优先 PIL 实色 JPEG；无 PIL 时退为纯 stdlib 生成 PNG（同扩展名规则由调用方定）"""
    try:
        from PIL import Image
        img = Image.new("RGB", (size, size), rgb)
        img.save(path, "JPEG", quality=90)
        return "jpg"
    except ImportError:
        # 最小 PNG 写入器（stdlib）：实色 RGB 8 位
        w = h = size
        raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))

        def chunk(tag, data):
            c = struct.pack(">I", len(data)) + tag + data
            return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

        png = (b"\x89PNG\r\n\x1a\n"
               + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
               + chunk(b"IDAT", zlib.compress(raw))
               + chunk(b"IEND", b""))
        with open(path, "wb") as f:
            f.write(png)
        return "png"


def build_photo_files():
    """批量导入夹具：少群.jpg（唯一匹配）/ 雷俊-2.jpg（变体匹配）/ 路人甲乙.jpg（未匹配）"""
    os.makedirs(PHOTO_DIR, exist_ok=True)
    _make_image(os.path.join(PHOTO_DIR, "少群.jpg"), 96, (30, 90, 200))
    _make_image(os.path.join(PHOTO_DIR, "雷俊-2.jpg"), 96, (20, 160, 60))
    _make_image(os.path.join(PHOTO_DIR, "路人甲乙.jpg"), 96, (200, 200, 30))
    return [os.path.join(PHOTO_DIR, n) for n in ["少群.jpg", "雷俊-2.jpg", "路人甲乙.jpg"]]


def red_jpeg(tmp_path):
    """单张纯红图（导出像素校验用）：有 PIL 用 96px JPEG；否则用内嵌 96px 红JPEG"""
    if Image_ok():
        p = os.path.join(tmp_path, "red.jpg")
        _make_image(p, 96, (255, 0, 0))
        return p
    p = os.path.join(tmp_path, "red.jpg")
    with open(p, "wb") as f:
        f.write(FALLBACK_JPG)
    return p


def Image_ok():
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def add_photo_via_modal(page, node_id="b1a1", img_path=None):
    """真实链路：右键 → 档案 → 隐藏 input set_input_files → 等头像出现"""
    page.locator('.node[data-id="%s"] .node-label' % node_id).click(button="right")
    page.locator("#__ctxMenu .mi", has_text="档案").click()
    page.wait_for_function("() => document.getElementById('__detailModal').classList.contains('open')")
    if img_path is None:
        img_path = red_jpeg(LOCAL_OUT)
    page.locator("#__dmPhotoFile").set_input_files(img_path)
    page.wait_for_function("() => document.querySelectorAll('.node[data-id=\"%s\"] img.node-avatar').length === 1" % node_id)


def setup_photo(page, node_id="b1a1", img_path=None):
    """走真实档案弹窗加照片（所有用例统一入口，保证 thumb/IDB/rev 全链路一致）"""
    add_photo_via_modal(page, node_id, img_path)


def idb_has(page, person_id):
    return page.evaluate("id => photoGet(id).then(r => !!(r && r.src && r.src.length > 100))", person_id)


def open_menu_file(page):
    page.locator("#btnFile").click()
    page.wait_for_function("() => document.getElementById('__ctxMenu').style.display === 'block'")


def close_detail_modal(page):
    """点取消关档案弹窗（焦点位置无关，确定性关闭）"""
    page.locator("#__dmCancel").click()
    page.wait_for_function("() => !document.getElementById('__detailModal').classList.contains('open')")


@testcase
def t_add_photo_avatar_thumb_idb_lightbox(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    # 无照片时：12 位成员（不含根）全部显示中性剪影
    check(page.locator(".node-avatar.ph-empty").count() == 12, "初始剪影头像 12", str(page.locator(".node-avatar.ph-empty").count()))
    check(page.locator("img.node-avatar").count() == 0, "初始无照片头像")
    # 档案弹窗照片区：方形预览 + 添加/更换 + 删除
    page.locator('.node[data-id="b1a1"] .node-label').click(button="right")
    page.locator("#__ctxMenu .mi", has_text="档案").click()
    page.wait_for_function("() => document.getElementById('__detailModal').classList.contains('open')")
    check(page.locator("#__dmPhotoBox svg").count() == 1, "弹窗预览为剪影占位")
    check(page.locator("#__dmPhotoAdd").inner_text() == "添加照片", "按钮文案=添加照片")
    check(not page.locator("#__dmPhotoDel").is_visible(), "无照片时删除钮隐藏")
    build_photo_files()  # 顺手生成批量导入夹具目录（本用例用红色单图）
    page.locator("#__dmPhotoFile").set_input_files(red_jpeg(LOCAL_OUT))
    page.wait_for_function("() => document.querySelectorAll('.node[data-id=\"b1a1\"] img.node-avatar').length === 1")
    # P2-3：头像 img 禁用原生拖拽（draggable=false + CSS 兜底）
    check(page.locator('.node[data-id="b1a1"] img.node-avatar').get_attribute("draggable") == "false", "头像 img draggable=false")
    # 头像在代数角标之前
    first_cls = page.evaluate("() => document.querySelector('.node[data-id=\"b1a1\"] .node-label').firstElementChild.className")
    check("node-avatar" in first_cls, "头像位于标签第一位（代数角标之前）", first_cls)
    # thumb 入数据 + rev
    d = page.evaluate("() => { const n = findNode('b1a1'); return { t: n.photoThumb, rev: n.photoRev }; }")
    check(d["t"] and d["t"].startswith("data:image/jpeg"), "thumb 为 JPEG data URL", str(d["t"])[:40])
    check(len(d["t"]) <= 9000, "thumb ≤6KB（base64≈8.6k 字符）", str(len(d["t"])))
    check(d["rev"] >= 1, "photoRev ≥1", str(d["rev"]))
    st = page.evaluate("() => JSON.parse(localStorage.getItem(window.__ZP.storageKey()))")
    found = []

    def w(n):
        if n.get("id") == "b1a1":
            found.append(n.get("photoThumb"))
        for c in n.get("children", []):
            w(c)
    w(st)
    check(found and found[0] == d["t"], "thumb 已随自动保存入 localStorage")
    # IDB 原图（1024 档）+ keys
    ok = page.evaluate("id => photoGet(id).then(r => !!(r && r.src && r.src.startsWith('data:image/jpeg') && r.src.length > 100))", "b1a1")
    check(ok, "IDB orig 有原图")
    keys = page.evaluate("() => photoKeys()")
    check("b1a1" in keys, "IDB keys 含 b1a1", str(keys))
    # 弹窗预览与按钮态
    check(page.locator("#__dmPhotoBox img").count() == 1, "弹窗预览为照片")
    check(page.locator("#__dmPhotoAdd").inner_text() == "更换照片", "按钮文案=更换照片")
    check(page.locator("#__dmPhotoDel").is_visible(), "删除钮可见")
    close_detail_modal(page)
    # 灯箱：点头像开；成员名；三种关闭
    page.locator('.node[data-id="b1a1"] img.node-avatar').click()
    page.wait_for_function("() => document.getElementById('__lightbox').classList.contains('open')")
    check("新洋" in page.locator("#__lbName").inner_text(), "灯箱显示成员名", page.locator("#__lbName").inner_text())
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.getElementById('__lightbox').classList.contains('open')")
    page.locator('.node[data-id="b1a1"] img.node-avatar').click()
    page.wait_for_function("() => document.getElementById('__lightbox').classList.contains('open')")
    page.locator("#__lbClose").click()
    page.wait_for_function("() => !document.getElementById('__lightbox').classList.contains('open')")
    page.locator('.node[data-id="b1a1"] img.node-avatar').click()
    page.wait_for_function("() => document.getElementById('__lightbox').classList.contains('open')")
    page.mouse.click(8, 300)   # 点遮罩（避开图与关闭钮）
    page.wait_for_function("() => !document.getElementById('__lightbox').classList.contains('open')")
    check(not errs, "无 JS 错误", str(errs))
    check(page.locator("img.node-avatar").count() == 1, "其余成员仍是剪影", str(page.locator("img.node-avatar").count()))
    ctx.close()


@testcase
def t_photo_cancel_after_pick_discards(b):
    """P3-4 回归：选图后立即「取消」→ 压缩流水线完成时也不写入（数据/IDB/卡面均无照片）"""
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    img = red_jpeg(LOCAL_OUT)
    # 闸门：拦住压缩结果，精确控制「处理完成」的时点（无固定 sleep 等异步）
    page.evaluate("""() => {
      const orig = compressPhotoFile;
      window.__gate = { release: null };
      compressPhotoFile = function(file, maxEdge, quality){
        return orig(file, maxEdge, quality).then(url => new Promise(res => {
          window.__gate.release = function(){ res(url); };
        }));
      };
    }""")
    page.locator('.node[data-id="b1a1"] .node-label').click(button="right")
    page.locator("#__ctxMenu .mi", has_text="档案").click()
    page.wait_for_function("() => document.getElementById('__detailModal').classList.contains('open')")
    page.locator("#__dmPhotoFile").set_input_files(img)
    page.wait_for_function("() => document.getElementById('__toast').textContent.indexOf('照片处理中') > -1")
    page.locator("#__dmCancel").click()   # 选图后立即取消
    page.wait_for_function("() => !document.getElementById('__detailModal').classList.contains('open')")
    page.evaluate("() => window.__gate.release()")   # 此时压缩流水线完成
    page.wait_for_timeout(150)
    d = page.evaluate("() => { const n = findNode('b1a1'); return { t: n.photoThumb, rev: n.photoRev }; }")
    check(d["t"] is None and d["rev"] is None, "取消后数据无 thumb/rev", str(d))
    keys = page.evaluate("() => photoKeys()")
    check("b1a1" not in keys, "取消后 IDB 无写入", str(keys))
    check(page.locator("img.node-avatar").count() == 0, "卡面无照片头像")
    # 正向对照：重新打开档案再选图，放行闸门 → 正常写入并渲染（弹窗已关也能刷出头像）
    page.locator('.node[data-id="b1a1"] .node-label').click(button="right")
    page.locator("#__ctxMenu .mi", has_text="档案").click()
    page.wait_for_function("() => document.getElementById('__detailModal').classList.contains('open')")
    page.locator("#__dmPhotoFile").set_input_files(img)
    page.wait_for_function("() => !!window.__gate.release")
    page.evaluate("() => window.__gate.release()")
    page.wait_for_function("() => document.querySelectorAll('.node[data-id=\"b1a1\"] img.node-avatar').length === 1")
    check(page.evaluate("() => !!findNode('b1a1').photoThumb"), "正向对照：照片已写入")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_restore_fullphotos_toast_accuracy(b):
    """P2-1 回归：恢复含原图备份的 toast 必须如实——photoPut 失败不再假报已写入"""
    import base64
    full_obj = {
        "id": "root", "name": "家族族谱", "spouses": [], "expanded": True, "children": [],
        "fullPhotos": {"px1": "data:image/jpeg;base64," + base64.b64encode(FALLBACK_JPG).decode("ascii")},
    }
    path_full = os.path.join(LOCAL_OUT, "bk_fp_toast.json")
    with open(path_full, "w", encoding="utf-8") as f:
        json.dump(full_obj, f, ensure_ascii=False)
    # 成功路径：toast 报准确张数，IDB 真有原图
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    page.locator("#__importFile").set_input_files(path_full)
    page.wait_for_function("() => document.getElementById('__toast').textContent.indexOf('照片原图已写入本机照片库（1 张）') > -1")
    ok = page.evaluate("() => photoGet('px1').then(r => !!(r && r.src))")
    check(ok, "成功路径 IDB 有 px1")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()
    # 失败路径：先关掉缓存的 IDB 连接 → 全部 photoPut resolve(false) → toast 如实报「照片库不可用」
    ctx2, page2, errs2, cons2 = fresh_page(b)
    goto(page2)
    page2.evaluate("() => _photoDB && _photoDB.close()")
    page2.locator("#__importFile").set_input_files(path_full)
    page2.wait_for_function("() => document.getElementById('__toast').textContent.indexOf('照片库不可用，仅缩略图可用') > -1")
    ok2 = page2.evaluate("() => photoGet('px1').then(r => !!r)")
    check(not ok2, "失败路径 IDB 无写入")
    check(not errs2, "无 JS 错误", str(errs2))
    ctx2.close()


@testcase
def t_avatar_click_isolation(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    setup_photo(page, "b1a1")
    close_detail_modal(page)
    page.mouse.click(60, 620)   # 点空白先取消选中（右键开菜单时选中态来自 setup）
    page.wait_for_timeout(80)
    lens0 = page.evaluate("window.__ZP.historyLens()")
    # 单击头像：开灯箱、不选中
    cls0b = page.locator('.node[data-id="b1a1"]').get_attribute("class")
    check("selected" not in cls0b, "前置：头像点击前未选中", cls0b)
    page.locator('.node[data-id="b1a1"] img.node-avatar').click()
    page.wait_for_function("() => document.getElementById('__lightbox').classList.contains('open')")
    cls = page.locator('.node[data-id="b1a1"]').get_attribute("class")
    check("selected" not in cls, "点头像不选中")
    page.keyboard.press("Escape")
    # 双击头像：不进行内嵌改名
    page.locator('.node[data-id="b1a1"] img.node-avatar').dblclick()
    page.wait_for_timeout(120)
    ce = page.locator('.node[data-id="b1a1"] .node-label').get_attribute("contenteditable")
    check(ce != "true", "双击头像不进入改名", str(ce))
    # 从头像按下并拖动：不触发拖拽（无 dragging、无历史入栈、位置不变）
    box = page.locator('.node[data-id="b1a1"] img.node-avatar').bounding_box()
    left0 = page.evaluate("() => document.querySelector('.node[data-id=\"b1a1\"]').style.left")
    page.mouse.move(box["x"] + 10, box["y"] + 10)
    page.mouse.down()
    page.mouse.move(box["x"] + 60, box["y"] + 40, steps=6)
    page.mouse.up()
    page.wait_for_timeout(150)
    left1 = page.evaluate("() => document.querySelector('.node[data-id=\"b1a1\"]').style.left")
    check(left0 == left1, "拖头像不移动节点", str((left0, left1)))
    check(page.locator('.node[data-id="b1a1"].dragging').count() == 0, "无 dragging 态")
    lens1 = page.evaluate("window.__ZP.historyLens()")
    check(lens0 == lens1, "拖头像不入撤销栈", str((lens0, lens1)))
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_photo_replace_and_delete_button(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    red1 = os.path.join(LOCAL_OUT, "ph_a.jpg")
    red2 = os.path.join(LOCAL_OUT, "ph_b.jpg")
    _make_image(red1, 96, (10, 120, 220))
    _make_image(red2, 120, (180, 40, 40))
    # 更换：同一人连续设两次仍只有 1 个头像，rev 递增，IDB 原图被覆盖
    add_photo_via_modal(page, "b1b", red1)
    rev1 = page.evaluate("() => findNode('b1b').photoRev")
    t1 = page.evaluate("() => findNode('b1b').photoThumb")
    page.locator("#__dmPhotoFile").set_input_files(red2)
    page.wait_for_function("t => findNode('b1b').photoThumb !== t", arg=t1)
    rev2 = page.evaluate("() => findNode('b1b').photoRev")
    t2 = page.evaluate("() => findNode('b1b').photoThumb")
    check(page.locator("img.node-avatar").count() == 1, "更换后仍 1 个头像", str(page.locator("img.node-avatar").count()))
    check(rev2 == rev1 + 1, "更换 rev+1", str((rev1, rev2)))
    check(t2 != t1, "更换后 thumb 变化")
    got = page.evaluate("() => photoGet('b1b').then(r => r && r.src)")
    check(got and got != "", "IDB 原图为第二张")
    # 删除按钮：thumb 清除、rev 继续 +1、剪影回归；IDB 原图留给惰性 GC
    page.locator("#__dmPhotoDel").click()
    page.wait_for_function("() => document.querySelectorAll('.node[data-id=\"b1b\"] .node-avatar.ph-empty').length === 1")
    d = page.evaluate("() => { const n = findNode('b1b'); return { t: n.photoThumb, rev: n.photoRev }; }")
    check(d["t"] is None, "删除后无 thumb", str(d))
    check(d["rev"] == rev2 + 1, "删除 rev+1", str(d))
    check(idb_has(page, "b1b"), "删除后 IDB 原图暂留（防误删，交由 GC）")
    close_detail_modal(page)
    check(page.locator("img.node-avatar").count() == 0, "卡面无照片头像")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_showphotos_toggle(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    check(page.locator(".node-avatar").count() == 12, "默认显示头像 12")
    page.locator("#btnView").click()
    page.locator("#__ctxMenu .mi", has_text="视觉设置").click()
    page.wait_for_function("() => document.getElementById('__setModal').classList.contains('open')")
    page.locator("#__cfgOther summary").click()   # 展开「其他显示项」
    page.locator("#__cfgPhotos").uncheck()
    page.wait_for_function("() => document.querySelectorAll('.node-avatar').length === 0")
    check(page.evaluate("cfg.showPhotos") is False, "关闭后 cfg.showPhotos=false")
    check(page.evaluate("JSON.parse(localStorage.getItem(CFG_KEY)).showPhotos") is False, "开关随 cfg 持久化")
    page.locator("#__cfgPhotos").check()
    page.wait_for_function("() => document.querySelectorAll('.node-avatar').length === 12")
    page.keyboard.press("Escape")
    page.reload()
    page.wait_for_function("() => document.querySelectorAll('.node-avatar').length === 12")
    check(page.evaluate("cfg.showPhotos") is True, "刷新后保持开启")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_backup_default_vs_full_and_restore(b):
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto(page)
    setup_photo(page, "b1a1")
    close_detail_modal(page)
    thumb = page.evaluate("() => findNode('b1a1').photoThumb")
    orig = page.evaluate("() => photoGet('b1a1').then(r => r && r.src)")
    # 菜单项：备份到文件（tooltip 注明含缩略图）+ 备份（含照片原图）
    open_menu_file(page)
    mi_def = page.locator("#__ctxMenu .mi", has_text="备份到文件")
    mi_full = page.locator("#__ctxMenu .mi", has_text="备份（含照片原图）")
    check(mi_def.count() == 1 and mi_full.count() == 1, "两个备份菜单项都在")
    check("缩略图" in mi_def.get_attribute("title"), "默认备份 tooltip 注明含缩略图", mi_def.get_attribute("title"))
    path_def = os.path.join(LOCAL_OUT, "bk_default.json")
    with page.expect_download() as dl:
        mi_def.click()
    dl.value.save_as(path_def)
    obj_def = json.load(open(path_def, encoding="utf-8"))
    check("fullPhotos" not in obj_def, "默认备份无 fullPhotos")
    ids = []

    def w(n):
        ids.append((n.get("id"), n.get("photoThumb")))
        for c in n.get("children", []):
            w(c)
    w(obj_def)
    check(dict(ids).get("b1a1") == thumb, "默认备份含 photoThumb")
    # 含原图版
    path_full = os.path.join(LOCAL_OUT, "bk_full.json")
    with page.expect_download() as dl2:
        open_menu_file(page)
        page.locator("#__ctxMenu .mi", has_text="备份（含照片原图）").click()
    dl2.value.save_as(path_full)
    obj_full = json.load(open(path_full, encoding="utf-8"))
    check(obj_full.get("fullPhotos", {}).get("b1a1") == orig, "含原图备份有 fullPhotos[b1a1]=原图")
    ctx.close()

    # —— 恢复默认备份：头像走 thumb，IDB 无原图 ——
    ctx2, page2, errs2, _ = fresh_page(b)
    goto(page2)
    page2.locator("#__importFile").set_input_files(path_def)
    page2.wait_for_function("() => document.querySelectorAll('.node[data-id=\"b1a1\"] img.node-avatar').length === 1")
    has = page2.evaluate("() => photoGet('b1a1').then(r => !!r)")
    check(not has, "恢复默认备份不写 IDB 原图")
    page2.locator('.node[data-id="b1a1"] img.node-avatar').click()
    page2.wait_for_function("() => document.getElementById('__lightbox').classList.contains('open')")
    page2.keyboard.press("Escape")
    check(not errs2, "默认备份恢复无 JS 错误", str(errs2))
    ctx2.close()

    # —— 恢复含原图备份：fullPhotos 写回 IDB，灯箱升级原图 ——
    ctx3, page3, errs3, _ = fresh_page(b)
    goto(page3)
    page3.locator("#__importFile").set_input_files(path_full)
    page3.wait_for_function("() => document.querySelectorAll('.node[data-id=\"b1a1\"] img.node-avatar').length === 1")
    page3.wait_for_function("() => photoGet('b1a1').then(r => !!(r && r.src))")
    got = page3.evaluate("() => photoGet('b1a1').then(r => r && r.src)")
    check(got == orig, "fullPhotos 已写回 IDB")
    page3.locator('.node[data-id="b1a1"] img.node-avatar').click()
    page3.wait_for_function("() => document.getElementById('__lightbox').classList.contains('open')")
    page3.wait_for_function("t => document.getElementById('__lbImg').src !== t", arg=thumb)
    up = page3.evaluate("() => document.getElementById('__lbImg').src")
    check(up == orig, "灯箱由 thumb 升级为原图")
    page3.keyboard.press("Escape")
    check(not errs3, "含原图恢复无 JS 错误", str(errs3))
    ctx3.close()


@testcase
def t_batch_import_folder(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    files = build_photo_files()
    # 菜单项存在（文件菜单）
    open_menu_file(page)
    check(page.locator("#__ctxMenu .mi", has_text="导入照片文件夹").count() == 1, "文件菜单有导入照片文件夹")
    page.keyboard.press("Escape")
    page.wait_for_function("() => document.getElementById('__ctxMenu').style.display !== 'block'")
    page.locator("#__photoDirInput").set_input_files(PHOTO_DIR)   # webkitdirectory 输入必须传目录
    page.wait_for_function("() => document.getElementById('__photoImpModal').classList.contains('open')")
    summ = page.locator("#__photoImpSum").inner_text()
    check("成功匹配 2" in summ, "唯一匹配 2 张（少群 / 雷俊-2 变体）", summ)
    check(page.locator("#__photoImpList .pimp-row").count() == 1, "未匹配列表 1 行")
    check("路人甲乙" in page.locator("#__photoImpList .pimp-row .fn").inner_text(), "未匹配行显示文件名")
    sel = page.locator("#__photoImpList .pimp-row select")
    opts = sel.locator("option").all_inner_texts()
    check("跳过（不导入）" in opts and "周亿树" in opts, "下拉含跳过与全部成员", str(opts[:4]))
    # 取消：不写入
    page.locator("#__photoImpCancel").click()
    page.wait_for_function("() => !document.getElementById('__photoImpModal').classList.contains('open')")
    check(page.evaluate("() => findNode('b2').photoThumb === undefined"), "取消后无写入（少群）")
    check(page.locator("img.node-avatar").count() == 0, "取消后无照片头像")
    # 再来一次：人工指定未匹配文件 → 周亿树
    page.locator("#__photoDirInput").set_input_files(PHOTO_DIR)
    page.wait_for_function("() => document.getElementById('__photoImpModal').classList.contains('open')")
    page.locator("#__photoImpList .pimp-row select").select_option(label="周亿树")
    page.locator("#__photoImpOk").click()
    page.wait_for_function("() => document.querySelectorAll('img.node-avatar').length === 3")
    thumbs = page.evaluate("() => ['b2','b1b','b1b1'].map(id => { const n = findNode(id); return n.photoThumb && n.photoRev >= 1; })")
    check(all(thumbs), "三人 thumb+rev 齐备", str(thumbs))
    keys = page.evaluate("() => photoKeys()")
    for pid in ["b2", "b1b", "b1b1"]:
        check(pid in keys, "IDB 含 " + pid, str(keys))
    # 重名成员：在少群支下再添一位「雷俊」，同名文件下拉应列出两位（带父辈标注），默认跳过
    page.evaluate("""() => {
      findNode('b2').children.push({ id: 'dup雷俊', name: '雷俊', spouses: [], birth: '', death: '', note: '', expanded: true, children: [] });
      render();
    }""")
    page.locator("#__photoDirInput").set_input_files(PHOTO_DIR)
    page.wait_for_function("() => document.getElementById('__photoImpModal').classList.contains('open')")
    rows2 = page.locator("#__photoImpList .pimp-row")
    check(rows2.count() == 2, "重名文件与未匹配文件都在确认列表", str(rows2.count()))
    sel2 = page.locator("#__photoImpList .pimp-row", has_text="雷俊-2").locator("select")
    opts2 = sel2.locator("option").all_inner_texts()
    dup_opts = [o for o in opts2 if o.startswith("雷俊")]
    check(len(dup_opts) == 2, "重名成员都列出", str(opts2))
    check(all("之子" in o for o in dup_opts), "重名选项带父辈标注", str(opts2))
    vals2 = sel2.locator("option").evaluate_all("els => els.map(e => e.value)")
    check("b1b" in vals2 and "dup雷俊" in vals2, "重名选项指向不同成员", str(vals2))
    check(sel2.input_value() == "", "重名默认跳过")
    page.locator("#__photoImpCancel").click()
    page.wait_for_function("() => !document.getElementById('__photoImpModal').classList.contains('open')")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_delete_undo_and_lazy_gc(b):
    ctx, page, errs, cons = fresh_page(b)
    goto(page)
    setup_photo(page, "b1a1")
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.getElementById('__detailModal').classList.contains('open')")
    dlg = DialogRecorder(page)
    dlg.queue("confirm", True)
    page.locator('.node[data-id="b1a1"] .node-label').click(button="right")
    page.locator("#__ctxMenu .mi", has_text="删除").click()
    page.wait_for_function("() => document.querySelectorAll('.node[data-id=\"b1a1\"]').length === 0")
    check(page.locator("img.node-avatar").count() == 0, "删人后其照片头像消失")
    # Ctrl+Z：人与照片一起回来（thumb 在数据里，原图未即时删除）
    page.keyboard.press("Control+z")
    page.wait_for_function("() => document.querySelectorAll('.node[data-id=\"b1a1\"] img.node-avatar').length === 1")
    check(page.evaluate("() => !!findNode('b1a1').photoThumb"), "撤销后 thumb 恢复")
    check(idb_has(page, "b1a1"), "撤销后 IDB 原图仍在")
    check(dlg.count() == 1, "删除经确认框", str(dlg.records))
    # 刷新：惰性 GC 只清理当前树外孤儿；b1a1 在树上应保留
    page.reload()
    page.wait_for_function("() => document.querySelectorAll('.node[data-id=\"b1a1\"] img.node-avatar').length === 1")
    check(idb_has(page, "b1a1"), "刷新 GC 后树上成员原图保留")
    # 再删人 + 刷新 → GC 清孤儿
    dlg.queue("confirm", True)
    page.locator('.node[data-id="b1a1"] .node-label').click(button="right")
    page.locator("#__ctxMenu .mi", has_text="删除").click()
    page.wait_for_function("() => document.querySelectorAll('.node[data-id=\"b1a1\"]').length === 0")
    page.reload()
    page.wait_for_function("() => document.querySelectorAll('.node[data-id=\"b1a1\"]').length === 0")
    page.wait_for_function("() => photoKeys().then(k => k.indexOf('b1a1') === -1)")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_export_four_directions_vertical_and_pixels(b):
    ctx, page, errs, cons = fresh_page(b, downloads=True)
    goto(page)
    setup_photo(page, "b1a1")   # 纯红图：导出画布应出现红色头像像素
    close_detail_modal(page)
    n_imgs = page.evaluate("() => exportPhotoImages().then(m => m.size)")
    check(n_imgs == 1, "导出预解码头像 1 张", str(n_imgs))
    red = page.evaluate("""() => exportTreeCanvas().then(cv => {
      const c2 = cv.getContext('2d');
      const d = c2.getImageData(0, 0, cv.width, cv.height).data;
      let n = 0;
      for (let i = 0; i < d.length; i += 4){
        if (d[i] > 200 && d[i+1] < 90 && d[i+2] < 90) n++;
      }
      return n;
    })""")
    check(red >= 300, "导出画布含红色头像像素", str(red))
    # 四向 × 横/竖排：导出无 JS 错误，PNG/PDF 签名正确
    for vertical in [False, True]:
        for direction in ["down", "up", "right", "left"]:
            page.locator("#btnView").click()
            page.locator("#__ctxMenu .mi", has_text="视觉设置").click()
            page.locator('[data-cfg-direction="%s"]' % direction).click()
            page.locator('[data-cfg-vertical="%s"]' % str(vertical).lower()).click()
            page.locator("#__setDone").click()
            size = page.evaluate("() => exportTreeCanvas().then(c => [c.width, c.height])")
            check(size[0] > 0 and size[1] > 0, "导出尺寸正常 %s/%s" % (direction, vertical), str(size))
            with page.expect_download() as dl:
                page.evaluate("exportPNG()")
            raw = Path(dl.value.path()).read_bytes()
            check(raw.startswith(b"\x89PNG"), "PNG 签名 %s/%s" % (direction, vertical))
    with page.expect_download() as dl2:
        page.evaluate("exportPDF()")
    raw2 = Path(dl2.value.path()).read_bytes()
    check(raw2.startswith(b"%PDF-"), "PDF 签名")
    check(not errs, "四向+竖排导出全程无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_roundrect_fallback_old_kernel(b):
    ctx, page, errs, cons = fresh_page(b)
    # 模拟老内核：页面脚本运行前删掉原生 roundRect → 应用兜底应补上 arcTo 版
    page.add_init_script("delete CanvasRenderingContext2D.prototype.roundRect;")
    goto(page)
    check(page.evaluate("() => typeof CanvasRenderingContext2D.prototype.roundRect") == "function", "老内核下 roundRect 兜底生效")
    geo = page.evaluate("""() => {
      const cv = document.createElement('canvas'); cv.width = 50; cv.height = 30;
      const c = cv.getContext('2d');
      c.beginPath(); c.roundRect(2, 2, 46, 26, 8);
      return { topEdge: c.isPointInPath(14, 4), corner: c.isPointInPath(4, 4), center: c.isPointInPath(25, 15) };
    }""")
    check(geo["topEdge"] and geo["center"] and not geo["corner"], "兜底画出圆角路径", str(geo))
    size = page.evaluate("() => exportTreeCanvas().then(c => c.width > 0)")
    check(size, "老内核模拟下导出正常")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


@testcase
def t_demo_photo_upgrade_respects_user_data(b):
    """老示例数据自动补帝王头像；用户改过的成员/真实数据绝不覆盖。"""
    ctx, page, errs, _ = fresh_page(b)
    # 用「保留真实内嵌种子（demo:true + 10 张帝王头像）」的夹具，不用 SAMPLE 夹具
    demo_fixture = Path(LOCAL_OUT) / "fixture_demo_photos.html"
    demo_fixture.write_text(Path(LOCAL_HTML).read_text(encoding="utf-8"), encoding="utf-8")
    page.goto(OUT_DIR + "/fixture_demo_photos.html")
    page.wait_for_load_state("domcontentloaded")
    page.evaluate("() => { try { localStorage.clear(); } catch(e){} }")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_function("document.querySelectorAll('img.node-avatar').length === 10")

    # 模拟老访客：示例数据在照片功能上线前保存——全树无 photoThumb/photoRev
    old_demo = page.evaluate("""() => {
      const d = JSON.parse(JSON.stringify(treeData));
      (function w(n){ delete n.photoThumb; delete n.photoRev; (n.children||[]).forEach(w); })(d);
      return JSON.stringify(d);
    }""")
    page.evaluate("v => localStorage.setItem('zupu_data_v4', v)", old_demo)
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_function("document.querySelectorAll('img.node-avatar').length === 10")
    check(page.evaluate("() => document.querySelectorAll('.node[data-id=\\'d11\\'] img.node-avatar').length") == 0,
          "宁国公主仍为剪影（种子本就无画像）")
    check(page.evaluate("treeData.children.find(n => n.id === 'd1').photoRev") == 1, "补头像后 rev 落位")
    check(page.evaluate("JSON.parse(localStorage.getItem('zupu_data_v4')).children.find(n => n.id === 'd1').photoThumb.length > 100"),
          "升级结果已自动保存")

    # 用户自定义照片（rev=9）+ 已删除照片（rev=3 无 thumb）→ 都不被覆盖
    user_mix = page.evaluate("""() => {
      const d = JSON.parse(JSON.stringify(treeData));
      const byId = {};
      (function w(n){ byId[n.id] = n; (n.children||[]).forEach(w); })(d);
      byId.d1.photoThumb = 'data:image/gif;base64,R0lGODlhAQABAAAAACw='; byId.d1.photoRev = 9;
      delete byId.d2.photoThumb; byId.d2.photoRev = 3;   // 用户主动删过照片
      return JSON.stringify(d);
    }""")
    page.evaluate("v => localStorage.setItem('zupu_data_v4', v)", user_mix)
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    check(page.evaluate("() => document.querySelector('.node[data-id=\\'d1\\'] img.node-avatar').src") ==
          "data:image/gif;base64,R0lGODlhAQABAAAAACw=", "用户自传照片不被覆盖")
    check(page.evaluate("() => document.querySelectorAll('.node[data-id=\\'d2\\'] img.node-avatar').length") == 0,
          "用户删过的照片不被回填")
    check(page.evaluate("() => document.querySelectorAll('img.node-avatar').length") == 9,
          "其余成员仍正常升级（10 - 1 自传 - 1 已删）")

    # 非示例数据（无 demo 标记）→ 完全不注入
    user_own = page.evaluate("""() => {
      const d = JSON.parse(JSON.stringify(treeData));
      delete d.demo;
      (function w(n){ delete n.photoThumb; delete n.photoRev; (n.children||[]).forEach(w); })(d);
      return JSON.stringify(d);
    }""")
    page.evaluate("v => localStorage.setItem('zupu_data_v4', v)", user_own)
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_function("document.querySelectorAll('.node').length > 0")
    page.wait_for_timeout(300)
    check(page.evaluate("() => document.querySelectorAll('img.node-avatar').length") == 0,
          "非示例数据零注入")
    check(page.evaluate("() => { const d = JSON.parse(localStorage.getItem('zupu_data_v4')); return d.photoThumb === undefined && d.children.every(n => n.photoThumb === undefined); }"),
          "用户数据未被写入任何照片字段")
    check(not errs, "无 JS 错误", str(errs))
    ctx.close()


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_module(globals(), "t_photo 成员照片第一期") else 1)
