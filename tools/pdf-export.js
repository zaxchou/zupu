/* ---------- PDF：单页矢量阅读 / A4 分页打印 ---------- */
let _pdfSubtree = null;
function pdfIsOpen(){ return document.getElementById('__pdfModal').classList.contains('open'); }
function exportPDF(){ openPdfExport(null); }
function openPdfExport(n){
  if (IS_XHS) return;
  if (NO_PDF) return;
  _pdfSubtree = n;
  document.querySelector('input[name="pdfMode"][value="vector"]').checked = true;
  /* 超大谱预选「A4 分页」：矢量页上限 14400pt，布局超过 ~13000px 时单页名字
     会小于 13pt，预选分页更实用；用户仍可改回单页高清。不用 pdfNeedsPaging——
     那是旧 12000px 栅格启发式，对矢量页过于激进 */
  try {
    const dims = exportDims();
    if (Math.max(dims.W, dims.H) > 13000) {
      document.querySelector('input[name="pdfMode"][value="paged"]').checked = true;
    }
  } catch (e) { /* 画布尚未渲染时保持默认单页 */ }
  document.getElementById('__pdfFont').value = '';
  document.getElementById('__pdfModal').classList.add('open');
  document.getElementById('__pdfGo').focus();
}
function closePdfExport(){
  document.getElementById('__pdfModal').classList.remove('open');
  _pdfSubtree = null;
}
function readPdfFont(file){
  if (!file) return Promise.resolve(null);
  if (file.size > 40 * 1024 * 1024) return Promise.reject(new Error('字体文件超过 40 MB，请选择较小的 TrueType 字体'));
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1]);
    reader.onerror = () => reject(new Error('无法读取字体文件'));
    reader.readAsDataURL(file);
  });
}
document.getElementById('__pdfCancel').addEventListener('click', closePdfExport);
document.getElementById('__pdfModal').addEventListener('mousedown', e => {
  if (e.target.id === '__pdfModal') closePdfExport();
});
document.getElementById('__pdfModal').addEventListener('keydown', e => {
  if (e.key === 'Escape'){ e.stopPropagation(); closePdfExport(); }
});
document.getElementById('__pdfGo').addEventListener('click', () => {
  const n = _pdfSubtree;
  const mode = document.querySelector('input[name="pdfMode"]:checked').value;
  const file = document.getElementById('__pdfFont').files[0];
  closePdfExport();
  exportBusy(true, '正在准备 PDF…');
  readPdfFont(mode === 'vector' ? file : null).then(font => {
    if (n) return runSubtreeExport('pdf', mode, font, n);
    return exportPdfAs(undefined, mode, font);
  }).catch(e => toast('导出失败：' + ((e && e.message) || e)))
    .then(() => exportBusy(false));
});
function buildVectorPdf(dims, fontBase64){
  const ctx = createVectorPdfContext(dims.W, dims.H + 46, fontBase64);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, dims.W, dims.H + 46);
  ctx.fillStyle = '#16324f';
  ctx.font = '600 16px sans-serif';
  ctx.fillText(dims.title, 20, 30);
  ctx.translate((dims.W - dims.baseW) / 2, 46);
  return exportPhotoImages().then(photoImgs => {
    paintTreeBody(ctx, photoImgs);
    return ctx.toBytes();
  });
}
function exportPdfAs(base, mode, fontBase64){
  if (IS_XHS) return Promise.resolve();
  if (NO_PDF) return Promise.resolve();
  let dims;
  try { dims = exportDims(); }
  catch (e){ toast('导出失败：' + e.message); return Promise.resolve(); }
  exportBusy(true, mode === 'paged' ? '正在生成分页 PDF…' : '正在生成单页高清 PDF…');
  /* 让忙碌提示先绘制，再进行字体解析与矢量绘图。 */
  return new Promise(resolve => setTimeout(resolve, 20)).then(() => {
    if (mode === 'paged') return buildPagedPdf(dims);
    return buildVectorPdf(dims, fontBase64).then(bytes => ({ bytes, pages: 1 }));
  }).then(r => {
    if (!r) return;
    download(stampName('.pdf', base), r.bytes, 'application/pdf');
    if (mode === 'paged') toast('树较大，已分为 ' + r.pages + ' 页（A4 横向，可打印）');
    else toast('单页高清 PDF 已下载（文字与线条可放大查看）');
  }).catch(e => toast('导出失败：' + ((e && e.message) || e)))
    .then(() => exportBusy(false));
}
