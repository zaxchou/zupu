# -*- coding: utf-8 -*-
"""把 index.html 打包成小红书小工具离线 zip。

规范来源：~/.agents/skills/minitool-zip-builder（SKILL.md + references）。
剥离网页专用 PDF 引擎及字体，外置主脚本，检查最终资源和 ZIP。
没有 PDF marker 的老 master 仍可构建；不完整 marker 必须报错。
"""
import io
import json
import os
import re
import sys
import zipfile
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
DIST = os.path.join(ROOT, 'dist-xhs')
OUT_ZIP = os.path.join(DIST, 'zupu-minitool.zip')
MIB = 1024 * 1024
MAX_ZIP_BYTES = 10 * MIB
MAX_TEXT_BYTES = 2 * MIB
MAX_BASE64_BYTES = MIB


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pdf_block(source, name):
    start = '/* BEGIN_%s */' % name
    end = '/* END_%s */' % name
    counts = (source.count('BEGIN_' + name), source.count('END_' + name))
    if counts == (0, 0):
        return None
    require(counts == (1, 1) and source.count(start) == source.count(end) == 1,
            '%s marker 缺失、重复或格式异常' % name)
    a, b = source.index(start), source.index(end)
    require(a < b, '%s marker 顺序异常' % name)
    return a, b + len(end)


# 保留换行及字符位置，只屏蔽注释和普通字符串；原有精确扫描仍同时执行。
JS_NON_CODE = re.compile(r'''/\*[\s\S]*?\*/|//[^\r\n]*|'(?:\\[\s\S]|[^'\\])*'|"(?:\\[\s\S]|[^"\\])*"''')


def code_only(source):
    return JS_NON_CODE.sub(lambda m: re.sub(r'[^\r\n]', ' ', m.group(0)), source)


def strip_pdf_engine(source):
    engine = pdf_block(source, 'PDF_ENGINE')
    export = pdf_block(source, 'PDF_EXPORT')
    require(bool(engine) == bool(export), 'PDF_ENGINE / PDF_EXPORT 必须同时存在；缺 marker 时拒绝剥离')
    if engine:
        if export:
            require(engine[1] <= export[0] or export[1] <= engine[0], 'PDF marker 区间不能交叠')
            # 保留的导出层必须在进入引擎前退出，避免剥离后出现可达的缺失依赖。
            body = source[export[0]:export[1]]
            for name in ('openPdfExport', 'exportPdfAs'):
                pattern = (r'function\s+' + name + r'\s*\([^)]*\)\s*\{\s*'
                           r'if\s*\(\s*IS_XHS\s*\)\s*'
                           r'(?:\{\s*)?return\b')
                require(re.search(pattern, code_only(body)), '%s 必须以 IS_XHS 早退保护' % name)
        source = source[:engine[0]] + '/* PDF engine omitted in XHS package. */' + source[engine[1]:]
        print('PDF：已剥离内嵌引擎与字体；小工具不提供 PDF 保存')
    else:
        print('PDF：无引擎 marker，按老 master 构建')
    # 不允许 marker 丢失的引擎静默混入产物；EXPORT 中的调用可保留。
    code = code_only(source)
    require(not re.search(r'\bZUPU_PDF_FONT_BASE64\b|function\s+createVectorPdfContext\s*\(', code),
            '仍有未标记的 PDF 引擎或字体，拒绝构建')
    return source


class ArtifactHTML(HTMLParser):
    """用 HTML 语义检查真实标签，不把 JS 字符串中的 <script> 当成标签。"""
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.starts = [0] + [m.end() for m in re.finditer('\n', source)]
        self.scripts = []
        self.errors = []
        self.active = None
        self.feed(source)
        self.close()
        if self.active is not None:
            self.errors.append('未闭合 script 标签')

    def position(self):
        line, col = self.getpos()
        return self.starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key, value in attrs:
            if re.fullmatch(r'on[a-z]+', key):
                self.errors.append('行内事件：' + key)
            if value and re.match(r'\s*javascript\s*:', value, re.I):
                self.errors.append('javascript: URI')
            if key in ('src', 'href', 'action', 'poster', 'data') and value:
                if re.match(r'\s*(?:[a-z][a-z0-9+.-]*:|//)', value, re.I):
                    if not (tag in ('img', 'link') and value.lower().startswith('data:image/')):
                        self.errors.append('非包内资源：' + value[:100])
        if tag in ('iframe', 'object', 'base', 'embed'):
            self.errors.append('被禁标签：' + tag)
        if values.get('target', '').lower() == '_blank':
            self.errors.append('不能打开新窗口')
        if tag == 'a' and 'download' in values:
            self.errors.append('不能使用 a[download] 下载')
        if tag == 'meta' and values.get('http-equiv', '').lower() in ('content-security-policy', 'refresh'):
            self.errors.append('不能自建 CSP 或使用 meta 跳转')
        if tag == 'script':
            kind = values.get('type', '').strip().lower()
            require(kind != 'module', '禁止模块脚本')
            a = self.position()
            self.active = (a, a + len(self.get_starttag_text()), values,
                           kind not in ('application/json', 'application/ld+json'))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        require(tag != 'script', 'script 不得使用自闭合标签')

    def handle_endtag(self, tag):
        if tag == 'script':
            require(self.active is not None, '多余的 script 结束标签')
            a, body_start, attrs, executable = self.active
            end = self.position()
            self.scripts.append((a, self.source.index('>', end) + 1,
                                 self.source[body_start:end], attrs, executable))
            self.active = None


def parse_html(source):
    result = ArtifactHTML(source)
    require(not result.errors, '\n'.join(result.errors))
    return result


def audit_base64(name, text):
    # 同时累计相邻的 'chunk' + 'chunk' 或 ['chunk', 'chunk'].join('')。
    # 不让 build_pdf.py 使用的 4096 字符分片绕过单资源 1 MiB 门禁。
    last_end, total, padding = 0, 0, 0
    for match in re.finditer(r'[A-Za-z0-9+/]{128,}={0,2}', text):
        gap = text[last_end:match.start()]
        if not re.fullmatch(r'''['"]\s*(?:,|\+)\s*['"]''', gap):
            total = 0
        total += len(match.group())
        padding = len(match.group()) - len(match.group().rstrip('='))
        decoded = total * 3 // 4 - padding
        require(decoded <= MAX_BASE64_BYTES,
                '%s 含解码后超过 1 MiB 的 Base64（约 %d 字节），须移除或改为合规包内资源' % (name, decoded))
        last_end = match.end()


def audit_code(html, app_js):
    parsed = parse_html(html)
    require(len(parsed.scripts) == 1 and parsed.scripts[0][3].get('src') == './app.js',
            '产物只能引用唯一的包内经典脚本 ./app.js；存在遗漏脚本')
    require(not parsed.scripts[0][2].strip(), '外置脚本标签内不得残留代码')
    # 保留原构建器的特定被禁 API 防线。
    banned = [
        ('fetch(', '网络请求'), ('XMLHttpRequest', '网络请求'),
        ('window.prompt(', '被禁弹窗'), ('window.open(', '弹新窗口'),
        ('eval(', '动态执行'), ('new Function(', '动态执行'),
        ('onclick=', '行内事件'), ('type="module"', '模块脚本'),
        ('navigator.clipboard', '剪贴板'), ('serviceWorker', '后台运行'),
        ('<iframe', 'iframe'), ('<base ', 'base'),
        ('requestFullscreen', '全屏'), ('WebAssembly', 'WASM'),
    ]
    for pattern, why in banned:
        require(pattern not in html and pattern not in app_js, '%s 命中：%s' % (why, pattern))
    text = html + '\n' + app_js
    require(not re.search(r'https?://(?!www\.w3\.org(?:/|[\s\'"<>]))', text, re.I), '存在外部 URL')
    require(not re.search(r'''(?:url\(\s*['"]?\s*|['"])//[a-z0-9]''', text, re.I), '存在协议相对外链')
    code = code_only(app_js)
    patterns = [
        (r'\b(?:fetch|eval|Function)\s*\(', '网络请求或动态代码'),
        (r'\b(?:XMLHttpRequest|WebSocket|EventSource|RTCPeerConnection)\b', '网络通信'),
        (r'\bwindow\s*\.\s*(?:open|prompt)\s*\(', '窗口 API'),
        (r'\b(?:Worker|SharedWorker|serviceWorker|OffscreenCanvas|transferControlToOffscreen|WebAssembly|SharedArrayBuffer)\b', 'Worker / 离屏 / WASM / 多线程'),
        (r'\b(?:UnityLoader|createUnityInstance|UnityFramework)\b|\bcc\s*\.\s*game\s*\.\s*run\s*\(', '游戏引擎'),
        (r'\bnavigator\s*\.\s*(?:clipboard|geolocation|bluetooth|usb|hid|serial|getBattery|connection|credentials|locks)\b', '受限设备 API'),
        (r'\b(?:getDisplayMedia|enumerateDevices|requestFullscreen|webkitRequestFullscreen)\s*\(', '设备 / 屏幕 API'),
        (r'\bnavigator\s*\.\s*storage\s*\.\s*persist\s*\(', '持久化 API'),
        (r'\bdocument\s*\.\s*execCommand\s*\(', '剪贴板命令'),
        (r'\b(?:Accelerometer|Gyroscope|Magnetometer|DeviceMotionEvent|DeviceOrientationEvent)\b', 'Web 传感器'),
        (r'\b(?:import\s*(?:\(|[\w*{])|export\s+(?:default|const|let|var|function|class|\{))', '模块语法'),
    ]
    for pattern, why in patterns:
        require(not re.search(pattern, code), '被禁能力：' + why)
    require(not re.search(r'''\baddEventListener\s*\(\s*['"](?:devicemotion|deviceorientation)['"]''', app_js),
            '被禁 Web 传感器事件')
    # 字符串下标形式也不能绕过 Function/eval/Worker 等构造器检查。
    require(not re.search(r'''\[\s*['"](?:eval|Function|Worker|SharedWorker|OffscreenCanvas|WebAssembly)['"]\s*\]''', app_js),
            '被禁能力的字符串下标访问')
    print('合规扫描：通过；未使用 Worker / WASM / OffscreenCanvas / 游戏引擎')


def audit_files(files):
    for name, data in files.items():
        if name.endswith(('.html', '.js', '.css', '.json')):
            require(len(data) < MAX_TEXT_BYTES, '%s 达到 2 MiB 文件门禁，须人工复核后优化' % name)
            audit_base64(name, data.decode('utf-8'))
    total = sum(len(data) for data in files.values())
    if total > 5 * MIB:
        print('WARN：文本合计超过 5 MiB，须复核解压后成本')


def main():
    with io.open(SRC, encoding='utf-8') as f:
        s = strip_pdf_engine(f.read())

    # 提取 JSON 数据块；HTMLParser 不会误认脚本内用于备份导入的 <script> 字符串。
    parsed = parse_html(s)
    seeds = [item for item in parsed.scripts if item[3].get('id') == '__treeData'
             and item[3].get('type') == 'application/json']
    require(len(seeds) == 1, '必须存在唯一的种子 JSON 块')
    seed = json.loads(seeds[0][2])
    a, b = seeds[0][:2]
    s = s[:a] + s[b:]

    parsed = parse_html(s)
    executable = [item for item in parsed.scripts if item[4]]
    require(len(executable) == 1, '必须存在唯一主脚本；新增内联/外置脚本需显式纳入打包')
    a, b, app_js, attrs, _ = executable[0]
    require(not attrs.get('src') and re.match(r'\s*/\* =+', app_js), '主脚本架构锚点异常')
    require(len(app_js) > 50000, 'app.js 体积异常，可能抓错脚本块')
    s = s[:a] + '<script src="./app.js"></script>' + s[b:]
    app_js = ('window.__ZUPU_NO_PDF__ = true;\n'
              'window.__SEED_JSON = ' + json.dumps(seed, ensure_ascii=False) + ';\n' + app_js)
    s = s.replace(
        'width=device-width, initial-scale=1.0, viewport-fit=cover',
        'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover', 1)

    audit_code(s, app_js)
    files = {
        'index.html': s.encode('utf-8'),
        'app.js': app_js.encode('utf-8'),
        'mini_tool.json': b'{"is_high_consumption_scene":false}\n',
    }
    audit_files(files)
    # 先在内存中生成、审计最终 ZIP，失败不覆盖已有发布产物。
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    payload = buffer.getvalue()
    require(len(payload) <= MAX_ZIP_BYTES, '最终 ZIP 超过 10 MiB 上限')
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        require(z.namelist() == list(files), 'ZIP 清单异常或存在重复 entry')
        require(z.testzip() is None, 'ZIP 完整性检查失败')
        packed = {name: z.read(name) for name in z.namelist()}
        require(packed == files, 'ZIP 内容与审计产物不一致')
        audit_files(packed)
    if len(payload) > 2 * MIB:
        print('WARN：ZIP 超过建议的 2 MiB')

    os.makedirs(DIST, exist_ok=True)
    # 旧协议及客户端派生标记不能被误认为本次产物。
    for name in ('mini_tool.json', '.high_consumption'):
        path = os.path.join(DIST, name)
        if os.path.exists(path):
            os.remove(path)
    for name, data in files.items():
        with open(os.path.join(DIST, name), 'wb') as f:
            f.write(data)
    with open(OUT_ZIP, 'wb') as f:
        f.write(payload)
    print('产物：' + OUT_ZIP)
    for name, data in files.items():
        print('  %-16s %.1f KiB' % (name, len(data) / 1024))
    print('  zip              %.1f KiB' % (len(payload) / 1024))
    print('mini_tool.json：is_high_consumption_scene=false；性能及兼容性未实测')
    print('待用户验证：同一 ZIP 的创服平台模拟器、Android 真机扫码、iOS 真机扫码')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print('ERROR：' + str(exc))
        sys.exit(1)
