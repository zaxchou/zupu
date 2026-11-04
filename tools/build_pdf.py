# -*- coding: utf-8 -*-
"""Inline the offline PDF engine and its Apache-licensed font into index.html.

Run this before build_i18n.py. The HTML remains independently usable via file://.
The XHS builder removes BEGIN_PDF_ENGINE because that container cannot save PDF.
"""
from pathlib import Path
import base64
import re

ROOT = Path(__file__).resolve().parents[1]


def replace_block(source, start, end, content):
    block = start + '\n' + content.rstrip() + '\n' + end
    pattern = re.escape(start) + r'[\s\S]*?' + re.escape(end)
    if start in source:
        result, n = re.subn(pattern, lambda _: block, source, count=1)
        assert n == 1
        return result
    return None, block


def main():
    path = ROOT / 'index.html'
    source = path.read_text(encoding='utf-8')
    font = (ROOT / 'third_party/droid-sans/DroidSansFallbackFull.ttf').read_bytes()
    encoded = base64.b64encode(font).decode('ascii')
    chunks = [encoded[i:i + 4096] for i in range(0, len(encoded), 4096)]
    font_js = 'const ZUPU_PDF_FONT_BASE64 = [\n' + ',\n'.join("'" + c + "'" for c in chunks) + "\n].join('');\n"
    # OFL 后备字体独立嵌入，与 Apache 常用字体分开保留许可及字体对象。
    supplement = (ROOT / 'third_party/zupu-rare-font/ZupuRareSupport.ttf').read_bytes()
    rare_encoded = base64.b64encode(supplement).decode('ascii')
    rare_chunks = [rare_encoded[i:i + 4096] for i in range(0, len(rare_encoded), 4096)]
    font_js += 'const ZUPU_PDF_SUPPLEMENT_BASE64 = [\n' + ',\n'.join("'" + c + "'" for c in rare_chunks) + "\n].join('');\n"
    engine = font_js + (ROOT / 'tools/pdf-vector.js').read_text(encoding='utf-8')
    result = replace_block(source, '/* BEGIN_PDF_ENGINE */', '/* END_PDF_ENGINE */', engine)
    if isinstance(result, tuple):
        _, block = result
        marker = 'function exportPalette(){'
        assert source.count(marker) == 1
        source = source.replace(marker, block + '\n' + marker, 1)
    else:
        source = result
    export = (ROOT / 'tools/pdf-export.js').read_text(encoding='utf-8')
    result = replace_block(source, '/* BEGIN_PDF_EXPORT */', '/* END_PDF_EXPORT */', export)
    if isinstance(result, tuple):
        _, block = result
        source, n = re.subn(r'function exportPDF\(\)\{[\s\S]*?(?=\n/\* ---------- 导出此支)',
                            lambda _: block + '\n', source, count=1)
        assert n == 1
    else:
        source = result
    path.write_text(source, encoding='utf-8', newline='')
    print('PDF engine inlined; font: %d bytes; HTML: %d bytes' % (len(font), path.stat().st_size))


if __name__ == '__main__':
    main()
