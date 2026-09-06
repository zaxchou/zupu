window.__SEED_JSON = {"id": "root", "name": "家族族谱", "spouses": [], "expanded": true, "demo": true, "clan": {"ming": "家族族谱（示例）", "tang": "", "chain": "", "yuanzu": "", "shizu": "", "qianzu": "", "origin": "这是一份示例数据。双击名字可改名，点「＋」添加成员；「视图 ▾ → 谱序」可改谱名、堂号、字辈表与源流；「文件 ▾ → 恢复备份」可导入你自己的族谱 json。"}, "zibei": ["德", "承", "传", "世", "泽", "诗", "礼", "继", "家", "声"], "children": [{"id": "d1", "name": "赵德祖", "spouses": ["钱婉贞"], "birth": "1948", "death": "", "note": "", "expanded": true, "children": [{"id": "d2", "name": "赵承业", "spouses": ["孙慧英"], "birth": "1972", "death": "", "note": "", "expanded": true, "children": [{"id": "d3", "name": "赵传家", "spouses": [], "birth": "1998", "death": "", "note": "", "expanded": true, "children": [{"id": "d4", "name": "赵世泽", "spouses": [], "birth": "2024", "death": "", "note": "", "expanded": true, "children": []}]}, {"id": "d5", "name": "赵传芳", "spouses": [], "gender": "f", "birth": "2002", "death": "", "note": "", "expanded": true, "children": []}]}, {"id": "d6", "name": "赵承志", "spouses": [], "birth": "1975", "death": "", "note": "", "zi": "守拙", "heir": "in", "expanded": true, "children": []}]}]};
/* =========================================================
 * 家族族谱 v13 架构分区：
 *   ①工具 ②数据层(migrate/sanitize/加载优先级) ③历史栈(撤销/重做)
 *   ④渲染三遍法 ⑤选择与行内编辑 ⑥档案弹窗 ⑦气泡菜单(+右键)
 *   ⑧编辑动作 ⑨拖拽排序 ⑩缩放平移 ⑪搜索 ⑫导入导出打印 ⑬键盘总控
 * ========================================================= */

/* ---------- ① 工具 ---------- */
function esc(s){
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
let _seq = 1;
function genId(p){ return p + '_' + Date.now().toString(36) + (_seq++); }
function findNode(id, n = treeData){
  if (!n) return null;
  if (n.id === id) return n;
  if (n.children) for (const c of n.children){ const r = findNode(id, c); if (r) return r; }
  return null;
}
function findParent(id, n = treeData, parent = null){
  if (!n) return null;
  if (n.id === id) return parent;
  if (n.children) for (const c of n.children){ const r = findParent(id, c, n); if (r) return r; }
  return null;
}
/* 配偶称谓：第 1 位=原配、第 2 位=续弦、其后三房/四房…… */
function spouseRole(i){
  return ['原配', '续弦', '三房', '四房', '五房', '六房', '七房', '八房'][i] || '第' + (i + 1) + '房';
}
/* 配偶称谓细化：可按人指定 配/继配/娶/聘/侧室（存 n.spRoles[i]，覆盖次序默认称谓）
 * 传统语义：配=初婚；继配=前妻亡故/离异后再娶初婚女；娶=再婚（再醮）妇；聘=定亲未娶 */
const SP_TERMS = ['配', '继配', '娶', '聘', '侧室'];
function spouseRoleAt(n, i){
  const o = n.spRoles && n.spRoles[i];
  return o || (cfg.vertical ? spouseBookRole(i) : spouseRole(i));
}
/* 谱书式称谓（竖排古法用）：配 / 继配 / 三配…… */
function spouseBookRole(i){
  return ['配', '继配', '三配', '四配', '五配', '六配', '七配', '八配'][i] || '第' + (i + 1) + '配';
}
function spousesText(n){
  return (n.spouses || []).map((s, i) => spouseRoleAt(n, i) + ' ' + spouseDisplay(s)).join(' · ');
}
function displayName(n){
  let s = dispName(n.name) + (n.gender === 'f' ? '（女）' : '');
  if (n.zi) s += '，字' + n.zi;
  if (n.hao) s += '，号' + n.hao;
  if (n.heir === 'in') s += '，嗣子';
  if (n.heir === 'out') s += '，嗣出';
  if (n.heir === 'jian') s += '，兼祧';
  if (n.zhi) s += '，止';
  return s + (n.spouses && n.spouses.length ? '（' + spousesText(n) + '）' : '');
}
/* 过继徽标提示 */
function heirTitle(n){
  return n.heir === 'in' ? '嗣子：过继来继承此支（谱书式「过继TA为子」）'
       : n.heir === 'out' ? '嗣出：过继给他人为子（谱书式「TA过继某某为子」）'
       : n.heir === 'jian' ? '兼祧（兼嗣）：一子兼继两房' : '';
}

/* ---------- 显示设置（本浏览器配置，与族谱数据分开存） ----------
 * genBase：字辈第 1 字对应的谱书世数（1=按应用自算「代」显示；13=勤字辈显示 23世）
 * bookSpouse：配偶按谱书式显示（丁嘉 → 丁氏嘉），仅显示层，存储与搜索仍用原名
 * showSurname：姓名是否带姓氏（姓氏随数据自动识别；关 = 只报名）
 * cnNum：世数用汉字（廿三世）；vertical：谱书竖排古法排版（世代成行、名字竖书、行左标世数） */
const CFG_KEY = 'zupu_cfg_v1';
let cfg = { genBase: 1, bookSpouse: true, showSurname: true, cnNum: false, vertical: false };
(function loadCfg(){
  try {
    const c = JSON.parse(localStorage.getItem(CFG_KEY) || '{}');
    if (typeof c.genBase === 'number' && c.genBase >= 1) cfg.genBase = Math.min(99, Math.round(c.genBase));
    if (typeof c.bookSpouse === 'boolean') cfg.bookSpouse = c.bookSpouse;
    if (typeof c.showSurname === 'boolean') cfg.showSurname = c.showSurname;
    if (typeof c.cnNum === 'boolean') cfg.cnNum = c.cnNum;
    if (typeof c.vertical === 'boolean') cfg.vertical = c.vertical;
  } catch(e){}
})();
function saveCfg(){ try { localStorage.setItem(CFG_KEY, JSON.stringify(cfg)); } catch(e){} }
function genOffset(){ return Math.max(0, cfg.genBase - 1); }
function genUnit(){ return genOffset() ? '世' : '代'; }
/* 阿拉伯数字 → 汉数字（谱书式）：10=十 11=十一 20=廿 23=廿三 30=卅 45=卌五 52=五十二 */
const CN_D = ['零','一','二','三','四','五','六','七','八','九'];
function numToCn(n){
  n = Math.round(n);
  if (n < 10) return CN_D[n];
  if (n === 10) return '十';
  if (n < 20) return '十' + CN_D[n % 10];
  if (n < 50){
    const t = ['','','廿','卅','卌'][Math.floor(n / 10)];
    return t + (n % 10 ? CN_D[n % 10] : '');
  }
  return CN_D[Math.floor(n / 10)] + '十' + (n % 10 ? CN_D[n % 10] : '');
}
function genLabel(g){ const v = g + genOffset(); return (cfg.cnNum ? numToCn(v) : v) + genUnit(); }
let FAM_SUR = '';   // 本谱姓氏：每轮渲染从成员名字首字自动统计（众数 ≥2 才认定），任意家族通用
function computeFamSur(){
  const cnt = {};
  (function w(n){
    if (n.id !== 'root' && n.id !== 'note' && n.name) cnt[n.name[0]] = (cnt[n.name[0]] || 0) + 1;
    if (n.children) n.children.forEach(w);
  })(treeData);
  let best = '', bc = 1;
  Object.keys(cnt).forEach(k => { if (cnt[k] > bc){ bc = cnt[k]; best = k; } });
  FAM_SUR = best;
}
function dispName(name){
  const s = String(name || '');
  if (cfg.showSurname || !FAM_SUR || s === FAM_SUR || !s.startsWith(FAM_SUR)) return s;
  return s.slice(FAM_SUR.length);
}
/* 谱书式配偶名：姓 + 氏 + 名（复姓取两字；已含「氏」的原样保留） */
const CS_SURN = '欧阳司马诸葛上官皇甫尉迟慕容令狐宇文轩辕东方端木长孙公孙淳于单于太叔申屠公冶宗政濮阳仲孙钟离鲜于闾丘子车亓官巫马公西漆雕乐正宰父谷梁拓跋夹谷南宫西门东郭呼延第五';
function spouseDisplay(s){
  if (!cfg.bookSpouse || !s) return s;
  if (!/[\u3400-\u9fff]/.test(s)) return s;   // 非中日文姓名（如罗马字）不补「氏」，原样返回
  if (s.indexOf('氏') > -1) return s;
  const two = CS_SURN.indexOf(s.slice(0, 2)) > -1;   // 复姓：含只有复姓两字（欧阳 → 欧阳氏）
  const sur = two ? s.slice(0, 2) : s.slice(0, 1);
  return sur + '氏' + s.slice(sur.length);           // 只有姓也补氏（黄 → 黄氏）
}
function parseYear(v){
  if (v === null || v === undefined) return null;
  const m = String(v).match(/(\d{4})/);
  return m ? parseInt(m[1], 10) : null;
}
/* 排行称谓：1→长、2→次、3→三…… */
const RANK_WORDS = ['长','次','三','四','五','六','七','八','九','十','十一','十二','十三','十四','十五'];
function rankWord(i){ return RANK_WORDS[i] || String(i + 1); }
function metaLine(n){
  const parts = [];
  const bRaw = (n.birth || '').trim(), dRaw = (n.death || '').trim();
  const by = parseYear(bRaw), dy = parseYear(dRaw);
  const b = by ? String(by) : bRaw;   // 卡面只露年份；月日收进 tooltip/搜索/备份
  const d = dy ? String(dy) : dRaw;
  if (b && d) parts.push(b + ' – ' + d);
  else if (b) parts.push(b + ' 生');
  else if (d) parts.push('卒 ' + d);
  if (n.note) parts.push(n.note);
  return parts.join(' · ');
}
/* 完整生卒（含月日）：仅当写的内容超出四位年份时出现在 tooltip */
function fullDatesLine(n){
  const b = (n.birth || '').trim(), d = (n.death || '').trim();
  const beyondYear = v => !!v && (!parseYear(v) || v !== String(parseYear(v)));
  if (!beyondYear(b) && !beyondYear(d)) return '';
  const seg = [b, d].filter(Boolean).join(b && d ? ' – ' : '');
  return seg ? '生卒：' + seg : '';
}
function countDescendants(n){
  let c = 0;
  (function w(x){ if (x.children) x.children.forEach(k => { c++; w(k); }); })(n);
  return c;
}
/* anc 的子树里是否包含 id（拖动过继的防环检查用） */
function subtreeContains(anc, id){
  if (anc.id === id) return true;
  if (anc.children) for (const c of anc.children) if (subtreeContains(c, id)) return true;
  return false;
}
/* 有出生年的同辈按年份升序自动排长幼；没数据的保持手动次序、排在其后 */
function sortSiblings(p){
  if (!p.children || p.children.length < 2) return false;
  const known = p.children.filter(c => parseYear(c.birth));
  if (!known.length) return false;
  const unknown = p.children.filter(c => !parseYear(c.birth));
  p.children = known.slice().sort((a, b) => parseYear(a.birth) - parseYear(b.birth)).concat(unknown);
  return true;
}

/* ---------- ② 数据层：唯一真源 = 本文件内嵌 JSON ----------
 * JS 里不再复制一份初始数据（v12 的双份手工同步必然漂移）。
 * 「初始模板」即本文件内嵌内容的克隆；若内嵌缺失/损坏则退化为空白根，
 * 可通过「恢复备份」救回数据（json / 旧版 HTML 均支持）。 */
function migrate(d){
  if (!d || typeof d !== 'object') return d;
  Object.keys(d).forEach(k => { if (k[0] === '_') delete d[k]; });
  if ('spouse' in d){ d.spouses = d.spouse ? [d.spouse] : []; delete d.spouse; }
  if (!Array.isArray(d.spouses)) d.spouses = [];
  if (!Array.isArray(d.children)) d.children = [];
  if (!('birth' in d)) d.birth = '';
  if (!('death' in d)) d.death = '';
  if (!('note' in d) || d.note === null) d.note = '';
  if (!('gender' in d) || d.gender !== 'f') d.gender = '';   // 性别：谱书惯例只标「女」
  if (!('zi' in d) || d.zi === null) d.zi = '';              // 字
  if (!('hao' in d) || d.hao === null) d.hao = '';           // 号
  if (!('heir' in d) || (d.heir !== 'in' && d.heir !== 'out' && d.heir !== 'jian')) d.heir = '';   // 过继：in=嗣子 out=嗣出 jian=兼祧
  if (!('zhi' in d) || d.zhi !== true) d.zhi = false;   // 止：无传（谱书黑圈标），手动标记
  if ('spRoles' in d && (typeof d.spRoles !== 'object' || d.spRoles === null || Array.isArray(d.spRoles))) delete d.spRoles;
  else if (d.spRoles){
    const cleanR = {};
    Object.keys(d.spRoles).forEach(k => {
      const i = +k;
      if (d.spRoles[k] && i >= 0 && i < d.spouses.length) cleanR[k] = d.spRoles[k];
    });
    if (Object.keys(cleanR).length) d.spRoles = cleanR; else delete d.spRoles;
  }
  if (typeof d.expanded !== 'boolean') d.expanded = true;
  if ('zibei' in d && !Array.isArray(d.zibei)) delete d.zibei;   // 字辈表（根节点字段，随文件走）
  if ('clan' in d && (typeof d.clan !== 'object' || d.clan === null || Array.isArray(d.clan))) delete d.clan;   // 谱序（堂号/源流）
  d.children.forEach(migrate);
  return d;
}

/* ---------- 字辈定代 ----------
 * 优先级：名字含字辈字（权威）> 父辈推算 > 同辈推算 > 世系偏移。
 * 推算结果与字辈冲突时（如中间缺一代），以字辈为准并在角标提示里注明。 */
function computeGenerations(){
  const map = new Map();   // id -> {gen, src:'match'|'parent'|'sibling'|'depth', zi, via, conflict}
  const zb = Array.isArray(treeData.zibei) ? treeData.zibei : [];
  if (!zb.length) return map;
  const matchOf = name => {
    const s = String(name || '');
    for (let i = 0; i < zb.length; i++) if (zb[i] && s.includes(zb[i])) return { gen: i + 1, zi: zb[i] };
    return null;
  };
  let anchors = 0;
  (function pass1(n){
    if (n.id !== 'root'){
      const m = matchOf(n.name);
      if (m){ map.set(n.id, { gen: m.gen, src: 'match', zi: m.zi }); anchors++; }
    }
    if (n.children) n.children.forEach(pass1);
  })(treeData);
  (function pass2(n, pgen){
    /* 子代 = 父代 + 1；pgen 传入的是「当前节点自己的代数」 */
    if (n.id !== 'root' && !map.get(n.id) && pgen != null)
      map.set(n.id, { gen: pgen + 1, src: 'parent' });
    const myGen = n.id === 'root' ? null : (map.get(n.id) ? map.get(n.id).gen : (pgen != null ? pgen + 1 : null));
    if (n.children) n.children.forEach(c => pass2(c, myGen));
  })(treeData, null);
  (function pass3(n){
    if (!n.children || !n.children.length) return;
    const known = n.children.find(c => map.get(c.id));
    if (known){
      const g = map.get(known.id);
      n.children.forEach(c => { if (!map.get(c.id)) map.set(c.id, { gen: g.gen, src: 'sibling', via: known.name }); });
    }
    n.children.forEach(pass3);
  })(treeData);
  if (anchors){
    let off = null;
    (function find(n, d){
      if (off != null) return;
      const e = map.get(n.id);
      if (e && e.src === 'match'){ off = e.gen - d; return; }
      if (n.children) n.children.forEach(c => find(c, d + 1));
    })(treeData, 0);
    (function fill(n, d){
      if (n.id !== 'root' && !map.get(n.id)) map.set(n.id, { gen: d + off, src: 'depth' });
      if (n.children) n.children.forEach(c => fill(c, d + 1));
    })(treeData, 0);
  }
  (function conflicts(n, pgen){
    if (n.id !== 'root'){
      const e = map.get(n.id);
      if (e && e.src === 'match' && pgen != null && e.gen !== pgen + 1) e.conflict = pgen + 1;
    }
    const g = n.id === 'root' ? null : (map.get(n.id) ? map.get(n.id).gen : pgen);
    if (n.children) n.children.forEach(c => conflicts(c, g));
  })(treeData, null);
  return map;
}
function genTitle(g, n){
  const p = findParent(n.id);
  const zbList = Array.isArray(treeData.zibei) ? treeData.zibei : [];
  const ziOfGen = zbList[g.gen - 1] || '';
  const unused = ziOfGen ? '（本人名字未用本代字辈「' + ziOfGen + '」）' : '（名字未用字辈）';
  const base = genOffset() ? '（谱书世数，应用自算第' + g.gen + '代）' : '';
  switch (g.src){
    case 'match':
      return '字辈「' + g.zi + '」= ' + genLabel(g.gen) + base
        + (g.conflict ? '（注意：按父辈推算应为' + genLabel(g.conflict) + '，树中可能缺一代）' : '');
    case 'parent':  return '由父/母「' + (p ? dispName(p.name) : '') + '」推算：' + genLabel(g.gen) + base + unused;
    case 'sibling': return '与「' + dispName(g.via || '') + '」同辈推算：' + genLabel(g.gen) + base + unused;
    default:        return '按世系推算：' + genLabel(g.gen) + base + unused;
  }
}
/* 序列化前清理：布局把 _w/_x/_y 写进数据对象，绝不能持久化。
   顶层先判 typeof，否则配偶字符串会被 Object.keys 拆成逐字对象（历史教训） */
function sanitize(n){
  if (n === null || typeof n !== 'object') return n;
  if (Array.isArray(n)) return n.map(sanitize);
  const out = {};
  Object.keys(n).forEach(k => {
    if (k[0] === '_') return;
    out[k] = sanitize(n[k]);
  });
  return out;
}
function deepEq(a, b){
  if (a === b) return true;
  if (typeof a !== typeof b || a === null || b === null) return false;
  if (Array.isArray(a)) return Array.isArray(b) && a.length === b.length && a.every((v, i) => deepEq(v, b[i]));
  if (typeof a === 'object'){
    const ka = Object.keys(a), kb = Object.keys(b);
    return ka.length === kb.length && ka.every(k => deepEq(a[k], b[k]));
  }
  return false;
}

var IS_XHS = !!(window.xhs && window.xhs.miniTool);   // 小红书容器环境
var IS_TOUCH = ('ontouchstart' in window) || navigator.maxTouchPoints > 0;
const STORAGE_KEY = 'zupu_data_v4';   // 数据真源：本浏览器（自动保存，无感）
let treeData;
let _seededFrom = '';        // 'browser' | 'file' | 'legacy-draft' | ''

const FALLBACK_TEMPLATE = migrate({ id:'root', name:'家族族谱', spouses:[], expanded:true, children:[] });
function seedRawText(){
  const el = document.getElementById('__treeData');
  if (el && el.textContent.trim()) return el.textContent.trim();
  if (window.__SEED_JSON) return JSON.stringify(window.__SEED_JSON);   // 小红书包：种子进 app.js
  return '';
}
const INIT_TEMPLATE = (function(){
  const sr = seedRawText();
  if (sr){
    try { return migrate(JSON.parse(JSON.stringify(JSON.parse(sr)))); }
    catch(e){ /* 内嵌损坏 → 空白模板，靠导入救回 */ }
  }
  return FALLBACK_TEMPLATE;
})();

function nodeCount(d){
  let c = 0;
  (function w(n){ if (n.id !== 'root') c++; if (n.children) n.children.forEach(w); })(d);
  return c;
}

/* 载入：本浏览器的数据永远是真源；浏览器里没有时（首次使用/换电脑），
   在「文件内嵌数据 / 旧版草稿」里挑成员最多的一份做初始 —— 自动抢救 */
(function loadData(){
  /* 浏览器数据一旦存在就永远优先（哪怕是刚从空白开始的数据）；
     内嵌文件 / 旧草稿只在浏览器没有数据（首次使用）时按成员数抢救播种 */
  let best = null, bestCount = -1, bestSrc = '';
  const consider = (d, src) => {
    if (!d) return;
    const c = nodeCount(d);
    if (c > bestCount){ best = d; bestCount = c; bestSrc = src; }
  };
  let browserHas = false;
  try {
    const v4 = localStorage.getItem(STORAGE_KEY);
    if (v4){
      const d = migrate(JSON.parse(v4));
      best = d; bestSrc = 'browser'; browserHas = true;   // 不再按成员数比较（v15.30：空白谱刷新被示例顶掉的 bug）
    }
  } catch(e){}
  if (!browserHas){
    const sr = seedRawText();
    if (sr){
      try { consider(migrate(JSON.parse(sr)), 'file'); } catch(e){}
    }
    try {
      Object.keys(localStorage).forEach(k => {
        if (k === STORAGE_KEY || !/^zupu_tree_data_v/.test(k)) return;
        try { consider(migrate(JSON.parse(localStorage.getItem(k))), 'legacy-draft'); } catch(e){}
      });
    } catch(e){}
  }
  treeData = best ? migrate(JSON.parse(JSON.stringify(best)))
                  : JSON.parse(JSON.stringify(INIT_TEMPLATE));
  _seededFrom = best ? bestSrc : 'empty';
  /* 不再跨候选「补齐」字辈表/谱序（v15.31）：内嵌种子已通用化为演示数据，
     补齐等于把演示内容注入用户主动清空过的真实族谱——用户删掉的就是删掉了。
     （该逻辑诞生时内嵌是同一份真实字辈，前提已随开源化消失） */
})();

let _lastSaveOk = true;   // 最近一次落盘是否成功：存储被禁用/配额满时必须让用户看见（v15.31）
function saveData(){
  /* 每次渲染（即每次编辑）无条件下自动保存到本浏览器 —— 保存是无感的 */
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(sanitize(treeData))); _lastSaveOk = true; }
  catch(e){ _lastSaveOk = false; }
}

/* ---------- ③ 历史栈（撤销 / 重做）----------
 * 快照是 sanitize 后的完整树 JSON 字符串，提交点只在真正改变数据的动作；
 * 同一节点的连续折叠/展开在 1 秒内合并成一条，防止刷满栈。 */
const HIST_MAX = 100;
let _undoStack = [], _redoStack = [];
let _lastOpKey = '', _lastOpT = 0;
function historySnapshot(){ return JSON.stringify(sanitize(treeData)); }
function pushHistory(opKey){
  const t = Date.now();
  if (opKey && opKey === _lastOpKey && t - _lastOpT < 1000){ _lastOpT = t; return; }
  /* 一旦发生真实改动就摘掉 demo 标记：向导只打扰「还没动手」的用户（v15.31） */
  if (treeData && treeData.demo) delete treeData.demo;
  _undoStack.push(historySnapshot());
  if (_undoStack.length > HIST_MAX) _undoStack.shift();
  _redoStack.length = 0;
  _lastOpKey = opKey || ''; _lastOpT = t;
  refreshUndoButtons();
}
function undo(){
  if (!_undoStack.length){ toast('没有可撤销的操作'); return; }
  _redoStack.push(historySnapshot());
  treeData = migrate(JSON.parse(_undoStack.pop()));
  afterHistoryJump(); toast('已撤销');
}
function redo(){
  if (!_redoStack.length){ toast('没有可重做的操作'); return; }
  _undoStack.push(historySnapshot());
  treeData = migrate(JSON.parse(_redoStack.pop()));
  afterHistoryJump(); toast('已重做');
}
function afterHistoryJump(){
  selectedId = null; closeMenu(); closeSearchHighlights();
  render();
}
function refreshUndoButtons(){
  document.getElementById('__undoBtn').disabled = !_undoStack.length;
  document.getElementById('__redoBtn').disabled = !_redoStack.length;
}

/* ---------- ④ 渲染：三遍法（建DOM实测宽度 → 递归布局 → 摆放+肘形连线） ---------- */
let selectedId = null;

/* 最近一次渲染的字辈映射（搜索列表显示代数用） */
let LAST_GENS = new Map();

/* 布局常量 */
const H_SPACE = 26;
const V_SPACE = 96;
const PAD = 60;
const ROW_GAP_V = 46;   // 竖排：世代行间距

/* 所有可见节点的世界坐标矩形（id → {x 中心, y 顶, w 宽, h 高}）。
   拖动过继的悬停命中检测用纯数学（不依赖 elementFromPoint，缩放/拖动中都稳定） */
const nodeRects = new Map();

function render(){
  const nodesEl = document.getElementById('nodes');
  const linesG  = document.getElementById('linesG');
  const svg     = document.getElementById('lines');
  const stage   = document.getElementById('stage');

  nodesEl.innerHTML = '<div id="__dropMarker"></div>';
  linesG.innerHTML = '';
  nodeRects.clear();
  stage.classList.toggle('v', !!cfg.vertical);   // 必须在测量前：竖排 CSS 改变卡片尺寸

  /* 第一遍：建 DOM，实测 label 宽高（offsetWidth 不受缩放影响） */
  const GENS = computeGenerations();
  LAST_GENS = GENS;
  computeFamSur();
  const domMap = new Map();
  function createDom(n, depth, orderIdx, orderTotal){
    const wrap = document.createElement('div');
    wrap.className = 'node g' + Math.min(depth, 5)
      + (selectedId === n.id ? ' selected' : '')
      + (n.id === 'note' ? ' meta-note' : '');
    wrap.dataset.id = n.id;

    /* 角标：出生年蓝框=自动排；无生年橙框=手动排行称谓 */
    if (n.id !== 'root' && n.id !== 'note'){
      const yr = parseYear(n.birth);
      if (yr){
        const rk = document.createElement('span');
        rk.className = 'rank by';
        rk.textContent = String(yr);
        rk.title = '出生年 ' + yr + '：同辈按出生年自动排序，年长在左';
        wrap.appendChild(rk);
      } else if (orderTotal > 1){
        const rk = document.createElement('span');
        rk.className = 'rank';
        rk.textContent = rankWord(orderIdx);
        rk.title = '同辈第 ' + (orderIdx + 1) + ' 位（最左为长）。补填出生年即可自动排序';
        wrap.appendChild(rk);
      }
    }

    const label = document.createElement('div');
    label.className = 'node-label';
    const meta = metaLine(n);
    label.innerHTML = esc(dispName(n.name)) + (n.gender === 'f' ? '<span class="gx" title="女性成员">女</span>' : '') +
      (n.heir ? '<span class="heir' + (n.heir === 'out' ? ' out' : n.heir === 'jian' ? ' jian' : '') + '" title="' + esc(heirTitle(n)) + '">嗣</span>' : '') +
      (n.zhi ? '<span class="zhi" title="止：谱书凡例，无传者以黑圈标止">止</span>' : '') +
      (n.zi ? '<span class="xh" title="字">字' + esc(n.zi) + '</span>' : '') +
      (n.hao ? '<span class="xh" title="号">号' + esc(n.hao) + '</span>' : '') +
      (n.spouses || []).map((s, i) =>
      (cfg.vertical ? '' : ' ') + '<span class="sp" data-sp="' + i + '" title="双击：改名 / 清空移除"><i class="role">' + esc(spouseRoleAt(n, i)) + '</i>' + esc(spouseDisplay(s)) + '</span>'
    ).join('') + (meta ? '<span class="meta">' + esc(meta) + '</span>' : '');
    label.title = [displayName(n), fullDatesLine(n), meta, '双击备注行可编辑生卒年与备注'].filter(Boolean).join('\n');

    /* 字辈代数角标（最左侧）：名字含字辈字=权威定代；未用字辈则按父/同辈推算 */
    const genInfo = GENS.get(n.id);
    if (genInfo && n.id !== 'root'){
      const zbList = Array.isArray(treeData.zibei) ? treeData.zibei : [];
      const zi = genInfo.zi || zbList[genInfo.gen - 1] || '';   // 推算代也标注本代字辈字
      const chip = document.createElement('span');
      chip.className = 'gen' + (genInfo.src === 'match' ? ' match' : '');
      chip.textContent = genLabel(genInfo.gen) + (zi ? '·' + zi : '');
      chip.title = genTitle(genInfo, n);
      label.insertBefore(chip, label.firstChild);
    }

    /* 快捷折叠/展开：有后代的卡片右侧常驻切换钮
       展开=「▾」一点收起；折叠=「▸ N」一点展开（N=后代数） */
    if (n.children && n.children.length){
      const cnt = countDescendants(n);
      const pill = document.createElement('span');
      pill.className = 'fold';
      if (n.expanded){
        pill.textContent = '▾';
        pill.title = '点击折叠此支（共 ' + cnt + ' 位后代）';
      } else {
        pill.textContent = '▸ ' + cnt;
        pill.title = '此支已折叠，共 ' + cnt + ' 位后代 —— 点击展开';
      }
      const metaEl = label.querySelector('.meta');
      if (metaEl) label.insertBefore(pill, metaEl);   // 插在姓名行内，不掉到备注行下
      else label.appendChild(pill);
    }

    wrap.appendChild(label);

    /* 常驻「＋」：点击弹出气泡菜单（点击行为由 #nodes 上的事件委托统一处理） */
    const qa = document.createElement('button');
    qa.className = 'quick-add';
    qa.textContent = '+';
    qa.title = '打开操作菜单';
    wrap.appendChild(qa);

    frag.appendChild(wrap);
    measureQueue.push({ label, depth });

    if (n.expanded && n.children) n.children.forEach((c, i) => createDom(c, depth + 1, i, n.children.length));
  }
  const frag = document.createDocumentFragment();
  const measureQueue = [];
  createDom(treeData, 0, 0, 1);
  nodesEl.appendChild(frag);
  /* 一次性测量：全部挂载后再读取尺寸，避免逐节点强制回流（几百上千人的性能关键） */
  measureQueue.forEach(q => {
    const wrap = q.label.parentNode;
    domMap.set(wrap.dataset.id, { wrap, w: q.label.offsetWidth + 3, lh: q.label.offsetHeight, d: q.depth });
  });

  /* 谱书竖排（古法）：世代行几何 —— 行高 = 该行最高卡片，行首 y 逐行累计 */
  const V = !!cfg.vertical;
  let rowTop = null, rowH = null, rowGen = null;
  if (V){
    rowH = [];
    domMap.forEach(info => { rowH[info.d] = Math.max(rowH[info.d] || 0, info.lh); });
    rowTop = [PAD];
    for (let d = 1; d < rowH.length; d++) rowTop[d] = rowTop[d - 1] + (rowH[d - 1] || V_SPACE) + ROW_GAP_V;
    rowGen = [];
    (function rg(n, d){
      if (!rowGen[d]){
        const g = GENS.get(n.id);
        if (g) rowGen[d] = g.gen;
      }
      if (n.expanded && n.children) n.children.forEach(c => rg(c, d + 1));
    })(treeData, 0);
  }

  /* 第二遍：递归布局（孩子居中时只移动子树，父节点不动） */
  function shiftSubtree(m, dx){
    m._x += dx;
    if (m.children) m.children.forEach(c => shiftSubtree(c, dx));
  }
  function layout(n, depth, xStart){
    const own = domMap.get(n.id).w;
    const kids = (n.expanded && n.children) ? n.children : [];
    const myTop = V ? rowTop[depth] : depth * V_SPACE + PAD;
    if (kids.length === 0){
      n._w = Math.max(own, 80);
      n._x = xStart + n._w / 2;
      n._y = myTop;
      return n._w;
    }
    let cw = 0;
    kids.forEach((c, i) => {
      cw += layout(c, depth + 1, xStart + cw);
      if (i < kids.length - 1) cw += H_SPACE;
    });
    const myW = Math.max(own, cw);
    if (myW > cw) kids.forEach(k => shiftSubtree(k, (myW - cw) / 2));
    n._w = myW;
    n._x = xStart + myW / 2;
    n._y = myTop;
    return myW;
  }
  layout(treeData, 0, PAD);

  /* 包围盒：只扫已渲染的子树（折叠节点的子孙没有 DOM） */
  let maxDepth = 0, minX = Infinity, maxX = -Infinity;
  (function scan(n, d){
    if (d > maxDepth) maxDepth = d;
    const w = domMap.get(n.id).w;
    if (n._x - w / 2 < minX) minX = n._x - w / 2;
    if (n._x + w / 2 > maxX) maxX = n._x + w / 2;
    if (n.expanded && n.children) n.children.forEach(c => scan(c, d + 1));
  })(treeData, 0);
  const treeW = (maxX - minX) + PAD * 2;
  const treeH = V ? (rowTop[maxDepth] + (rowH[maxDepth] || V_SPACE) + PAD)
                  : (maxDepth + 1) * V_SPACE + PAD;

  stage.style.width  = treeW + 'px';
  stage.style.height = treeH + 'px';
  stage._baseW = treeW; stage._baseH = treeH;   // 未缩放基准：缩放时按此扩大滚动范围
  svg.setAttribute('width', treeW);
  svg.setAttribute('height', treeH);
  svg.setAttribute('viewBox', '0 0 ' + treeW + ' ' + treeH);

  /* 第三遍：摆 DOM + 肘形母线（从父 label 实测底部出发）
     所有线段合并进一条 path（大族谱时 SVG 元素数从 O(n) 降到 O(1)） */
  let lineD = '';
  function addPath(d){ lineD += d; }
  function place(n){
    const info = domMap.get(n.id);
    info.wrap.style.left = n._x + 'px';
    info.wrap.style.top  = n._y + 'px';
    nodeRects.set(n.id, { x: n._x, y: n._y, w: info.w, h: info.lh });

    if (n.expanded && n.children && n.children.length){
      if (V){
        /* 竖排：父卡底 → 行间母线 → 各子卡顶（谱书式垂线） */
        const yTop = n._y + info.lh;
        const busY = rowTop[info.d] + (rowH[info.d] || V_SPACE) + ROW_GAP_V / 2;
        const firstX = n.children[0]._x;
        const lastX  = n.children[n.children.length - 1]._x;
        addPath('M ' + n._x + ' ' + yTop + ' L ' + n._x + ' ' + busY);
        if (n.children.length > 1)
          addPath('M ' + Math.min(firstX, lastX) + ' ' + busY + ' L ' + Math.max(firstX, lastX) + ' ' + busY);
        n.children.forEach(c => {
          addPath('M ' + c._x + ' ' + busY + ' L ' + c._x + ' ' + c._y);
          place(c);
        });
      } else {
        const yTop   = n._y + info.lh;
        const yChild = n._y + V_SPACE;
        const midY   = Math.max(yTop + 26, (yTop + yChild) / 2);
        const firstX = n.children[0]._x;
        const lastX  = n.children[n.children.length - 1]._x;

        addPath('M ' + n._x + ' ' + yTop + ' L ' + n._x + ' ' + midY);
        if (n.children.length > 1)
          addPath('M ' + Math.min(firstX, lastX) + ' ' + midY + ' L ' + Math.max(firstX, lastX) + ' ' + midY);
        n.children.forEach(c => {
          addPath('M ' + c._x + ' ' + midY + ' L ' + c._x + ' ' + yChild);
          place(c);
        });
      }
    }
  }
  place(treeData);
  if (lineD){
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    p.setAttribute('d', lineD);
    linesG.appendChild(p);
  }

  /* 竖排：行左世数标（谱书页边的「廿三世·勤」；固定汉字数字——阿拉伯数字竖排会逐位竖读）
     字辈字 = 该行首个成员的定代对应的字辈字，第 0 行为总根不标 */
  if (V){
    const zbRows = Array.isArray(treeData.zibei) ? treeData.zibei : [];
    for (let d = 1; d < rowTop.length; d++){
      const g = rowGen[d];
      if (!g) continue;
      const zi = zbRows[g - 1] || '';
      const el = document.createElement('div');
      el.className = 'vrow';
      el.textContent = numToCn(g + genOffset()) + genUnit() + (zi ? '·' + zi : '');
      el.title = '本行「' + el.textContent + '」';
      el.style.top = (rowTop[d] + (rowH[d] || V_SPACE) / 2) + 'px';
      nodesEl.appendChild(el);
    }
  }

  /* 恢复搜索高亮（render 重建了 DOM） */
  if (_lastQuery) applySearchHighlight();

  applyZoom();
  updateStats(GENS);
  updateClanTags();   /* 撤销/重做/导入也会改变谱序，顶栏随渲染同步 */
  saveData();         /* 每次渲染（即每次编辑）自动保存到本浏览器 —— 无感 */
  updateSaveState();  /* 必须在 saveData 之后：指示灯要反映本次落盘的真实结果（v15.31） */
}

/* ---------- 节点交互：事件委托（几百上千人时卡片零监听器，构建快、内存省） ---------- */
(function attachNodeDelegation(){
  const nodesEl = document.getElementById('nodes');
  const nodeOf = e => {
    const w = e.target.closest('.node');
    return w ? findNode(w.dataset.id) : null;
  };
  nodesEl.addEventListener('click', e => {
    const t = e.target;
    if (t.closest('.quick-add')){
      const w = t.closest('.node'); const n = nodeOf(e);
      if (n){ e.stopPropagation(); selectNode(n.id); openMenu(w, n); }
      return;
    }
    if (t.closest('.fold')){
      const n = nodeOf(e);
      if (n){ e.stopPropagation(); toggleExpand(n); }
      return;
    }
    const label = t.closest('.node-label');
    if (label){
      const n = nodeOf(e);
      if (n){ e.stopPropagation(); selectNode(n.id); }
    }
  });
  nodesEl.addEventListener('dblclick', e => {
    const t = e.target;
    const label = t.closest('.node-label');
    if (!label || label.isContentEditable) return;
    const n = nodeOf(e);
    if (!n) return;
    e.stopPropagation();
    if (t.closest('.fold')) return;                      // ▾/▸ 有自己的单击行为
    if (t.closest('.sp')){
      editSpouseAt(n, parseInt(t.closest('.sp').dataset.sp, 10));
      return;
    }
    if (t.closest('.meta')){ editDetails(n); return; }
    editNameInline(label, n);
  });
})();

function updateStats(GENS){
  const G = GENS || computeGenerations();
  let persons = 0, sp = 0, gens = 0;
  (function w(n, d){
    if (n.id !== 'root'){ persons++; sp += (n.spouses || []).length; }
    if (d > gens) gens = d;
    if (n.children) n.children.forEach(c => w(c, d + 1));
  })(treeData, 0);
  let extra = '';
  const G2 = G;
  if (G2.size){
    let lo = Infinity, hi = -Infinity;
    G2.forEach(v => { if (v.gen < lo) lo = v.gen; if (v.gen > hi) hi = v.gen; });
    if (hi > -Infinity){
      const loV = lo + genOffset(), hiV = hi + genOffset();
      extra = ' · 字辈第<b>' + (cfg.cnNum ? numToCn(loV) + '–' + numToCn(hiV) : loV + '–' + hiV) + '</b>' + genUnit();
    }
  }
  const totV = gens + genOffset();
  document.getElementById('statsChip').innerHTML =
    '<b>' + persons + '</b> 位成员 · 配偶 <b>' + sp + '</b> · ' + (cfg.cnNum ? numToCn(totV) : totV) + ' ' + genUnit() + extra;
}

/* 保存状态：自动保存无感进行，这里只给一个安心的绿灯；
   但落盘失败（无痕模式禁存、配额满）必须红字示警，不能假报已保存（v15.31） */
function updateSaveState(){
  const el = document.getElementById('saveState');
  if (!el) return;
  if (!_lastSaveOk){
    el.classList.remove('is-saved');
    el.classList.add('save-fail');
    el.innerHTML = '<span class="dot"></span>未能保存';
    el.title = '此浏览器环境不允许写入本地存储（如无痕模式/配额已满）——'
             + '本次修改不会被记住，请立即用「文件 ▾ → 备份到文件」导出 json！';
    return;
  }
  el.classList.remove('save-fail');
  el.classList.add('is-saved');
  el.innerHTML = '<span class="dot"></span>已保存';
  el.title = '所有修改都已自动保存在此浏览器 · 备份/换电脑见「文件 ▾」菜单';
}

function selectNode(id){
  selectedId = id;
  document.querySelectorAll('.node').forEach(w => {
    w.classList.toggle('selected', w.dataset.id === id);
  });
}

/* ---------- ⑤ 行内编辑 ---------- */
function editNameInline(labelEl, n){
  labelEl.textContent = n.name;
  labelEl.contentEditable = 'true';
  labelEl.style.minWidth = '60px';
  labelEl.focus();
  const r = document.createRange();
  r.selectNodeContents(labelEl);
  const sel = window.getSelection();
  sel.removeAllRanges(); sel.addRange(r);
  function commit(){
    if (labelEl.contentEditable !== 'true') return;   // 防止 blur 与回车双重 commit
    labelEl.contentEditable = 'false';
    labelEl.removeEventListener('blur', commit);
    labelEl.removeEventListener('keydown', onKey);
    const nv = labelEl.textContent.trim();
    if (nv && nv !== n.name){ pushHistory('rename:' + n.id); n.name = nv; }
    render();
  }
  function onKey(e){
    if (e.key === 'Enter'){ e.preventDefault(); commit(); }
    if (e.key === 'Escape'){ labelEl.textContent = n.name; labelEl.blur(); commit(); }
  }
  labelEl.addEventListener('blur', commit);
  labelEl.addEventListener('keydown', onKey);
}

/* ---------- 页内输入/文本弹窗（容器禁 window.prompt；触屏统一体验） ---------- */
function uiPrompt(title, def){
  return new Promise(function(resolve){
    var m = document.getElementById('__uipModal');
    document.getElementById('__uipTitle').textContent = title;
    var inp = document.getElementById('__uipInput');
    inp.value = def || '';
    m.classList.add('open');
    setTimeout(function(){ try { inp.focus(); inp.select(); } catch(e){} }, 80);
    function done(v){
      m.classList.remove('open');
      document.getElementById('__uipOk').removeEventListener('click', ok);
      document.getElementById('__uipCancel').removeEventListener('click', no);
      inp.removeEventListener('keydown', onKey);
      m.removeEventListener('mousedown', out);
      resolve(v);
    }
    function ok(){ done(inp.value); }
    function no(){ done(null); }
    function out(e){ if (e.target.id === '__uipModal') done(null); }
    function onKey(e){
      if (e.key === 'Enter'){ e.preventDefault(); e.stopPropagation(); done(inp.value); }
      if (e.key === 'Escape'){ e.preventDefault(); e.stopPropagation(); done(null); }
    }
    document.getElementById('__uipOk').addEventListener('click', ok);
    document.getElementById('__uipCancel').addEventListener('click', no);
    inp.addEventListener('keydown', onKey);
    m.addEventListener('mousedown', out);
  });
}
function showTextModal(title, text){
  var m = document.getElementById('__textModal');
  document.getElementById('__textTitle').textContent = title;
  var ta = document.getElementById('__textArea');
  ta.value = text;
  m.classList.add('open');
  document.getElementById('__textSel').onclick = function(){ ta.focus(); ta.select(); };
  document.getElementById('__textOk').onclick = function(){ m.classList.remove('open'); };
  m.onmousedown = function(e){ if (e.target.id === '__textModal') m.classList.remove('open'); };
}
function pasteImport(){
  var m = document.getElementById('__pasteModal');
  var ta = document.getElementById('__pasteArea');
  ta.value = '';
  m.classList.add('open');
  setTimeout(function(){ try { ta.focus(); } catch(e){} }, 80);
  document.getElementById('__pasteOk').onclick = function(){
    var txt = ta.value.trim();
    if (!txt) return;
    try {
      var d = JSON.parse(txt);
      if (!validTree(d)) throw new Error('结构不符：需要 {id,name,children[]} 树');
      if ((!Array.isArray(d.zibei) || !d.zibei.length) && Array.isArray(treeData.zibei)) d.zibei = treeData.zibei;
      pushHistory('import');
      treeData = migrate(d);
      selectedId = null;
      m.classList.remove('open');
      render(); fitToScreen();
      toast('已导入粘贴的备份数据，已自动保存');
    } catch(e){ alert('导入失败：不是有效的族谱 JSON 文件\n' + e.message); }
  };
  document.getElementById('__pasteCancel').onclick = function(){ m.classList.remove('open'); };
}

function editName(n){
  uiPrompt('修改姓名：', n.name).then(function(t){
    if (t !== null && t.trim()){ pushHistory('rename:' + n.id); n.name = t.trim(); render(); }
  });
}

/* ---------- ⑥ 档案弹窗 ---------- */
let _dmNode = null;
function dmIsOpen(){ return document.getElementById('__detailModal').classList.contains('open'); }
function editDetails(n){
  _dmNode = n;
  document.getElementById('__dmTitle').textContent = '人员档案 · ' + dispName(n.name);
  document.getElementById('__dmName').value  = n.name || '';
  document.getElementById('__dmBirth').value = n.birth || '';
  document.getElementById('__dmDeath').value = n.death || '';
  document.getElementById('__dmNote').value  = n.note || '';
  document.getElementById('__dmGender').value = n.gender === 'f' ? 'f' : '';
  document.getElementById('__dmHeir').value = (n.heir === 'in' || n.heir === 'out' || n.heir === 'jian') ? n.heir : '';
  document.getElementById('__dmZi').value  = n.zi || '';
  document.getElementById('__dmHao').value = n.hao || '';
  document.getElementById('__dmZhi').checked = n.zhi === true;
  /* 配偶称谓：每人可指定 配/继配/娶/聘/侧室（空=按次序默认） */
  const spHost = document.getElementById('__dmSp');
  spHost.innerHTML = '';
  (n.spouses || []).forEach((spName, i) => {
    const row = document.createElement('div');
    row.className = 'row';
    const cur = (n.spRoles && n.spRoles[i]) || '';
    const opts = ['<option value="">（默认）</option>'].concat(SP_TERMS.map(t =>
      '<option value="' + t + '"' + (cur === t ? ' selected' : '') + '>' + t + '</option>')).join('');
    row.innerHTML = '<label>配偶 ' + (i + 1) + ' · ' + esc(spName) + ' 称谓<select data-i="' + i + '">' + opts + '</select></label>';
    spHost.appendChild(row);
  });
  document.getElementById('__detailModal').classList.add('open');
  document.getElementById('__dmName').focus();
}
function closeDetails(){
  document.getElementById('__detailModal').classList.remove('open');
  _dmNode = null;
}
document.getElementById('__dmCancel').addEventListener('click', closeDetails);
document.getElementById('__detailModal').addEventListener('mousedown', e => {
  if (e.target.id === '__detailModal') closeDetails();
});
document.getElementById('__dmSave').addEventListener('click', () => {
  if (!_dmNode) return closeDetails();
  const n = _dmNode;
  const nm = document.getElementById('__dmName').value.trim();
  const birth = document.getElementById('__dmBirth').value.trim();
  const death = document.getElementById('__dmDeath').value.trim();
  const note  = document.getElementById('__dmNote').value.trim();
  const gender = document.getElementById('__dmGender').value === 'f' ? 'f' : '';
  const heirV = document.getElementById('__dmHeir').value;
  const heir = (heirV === 'in' || heirV === 'out' || heirV === 'jian') ? heirV : '';
  const zi  = document.getElementById('__dmZi').value.trim();
  const hao = document.getElementById('__dmHao').value.trim();
  const zhi = document.getElementById('__dmZhi').checked === true;
  const spRoles = {};
  let spChanged = false;
  document.querySelectorAll('#__dmSp select').forEach(sel => {
    const i = sel.dataset.i;
    const v = sel.value;
    if (v) spRoles[i] = v;
    if (v !== ((n.spRoles && n.spRoles[i]) || '')) spChanged = true;
  });
  const changed = (nm && nm !== n.name) || birth !== (n.birth || '')
    || death !== (n.death || '') || note !== (n.note || '') || gender !== (n.gender || '')
    || heir !== (n.heir || '') || zi !== (n.zi || '') || hao !== (n.hao || '')
    || zhi !== (n.zhi === true) || spChanged;
  if (!changed){ closeDetails(); return; }   // 无改动：不入历史栈
  pushHistory('details:' + n.id);            // 快照必须在改动之前，档案才能真正撤销（v15.12 修复）
  if (nm) n.name = nm;
  n.birth = birth;
  n.death = death;
  n.note  = note;
  n.gender = gender;
  n.heir = heir;
  n.zi = zi;
  n.hao = hao;
  n.zhi = zhi;
  if (Object.keys(spRoles).length) n.spRoles = spRoles; else delete n.spRoles;
  closeDetails();
  if (parseYear(n.birth)){
    const p = findParent(n.id);
    if (p && sortSiblings(p))
      toast('已保存，并按出生年自动重排「' + n.name + '」同辈的长幼（年长在左）');
    else
      toast('已保存「' + n.name + '」的档案');
  } else {
    toast('已保存「' + n.name + '」的档案（未填出生年，长幼按手动排列）');
  }
  render();
  selectNode(n.id);
});
/* 弹窗内回车=保存（备注除外）、Esc=取消。事件到 document 层被键盘总控拦下，
   不会再触发加同辈之类的全局快捷键（v12 的泄漏 bug） */
document.getElementById('__detailModal').addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.target.id !== '__dmNote'){
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('__dmSave').click();
  }
  if (e.key === 'Escape'){ e.preventDefault(); e.stopPropagation(); closeDetails(); }
});

/* ---------- ⑦ 气泡菜单（点击式，不随鼠标消失；右键同样打开） ---------- */
const ctxMenu = document.getElementById('__ctxMenu');
function mi(label, cls, hint, fn, title){
  const d = document.createElement('div');
  d.className = 'mi' + (cls ? ' ' + cls : '');
  d.innerHTML = '<span class="lbl">' + label + '</span>' + (hint ? '<span class="k">' + hint + '</span>' : '');
  if (title) d.title = title;
  d.onclick = e => { e.stopPropagation(); closeMenu(); fn(); };
  return d;
}
function msep(){
  const d = document.createElement('div');
  d.className = 'msep';
  return d;
}
function buildMenuItems(n){
  ctxMenu.innerHTML = '';
  if (n.id === 'root'){
    ctxMenu.appendChild(mi('＋ 第一代', '', '', () => addChild(n)));
  } else {
    ctxMenu.appendChild(mi('＋ 配偶', '', 'Ctrl+Shift+S', () => addSpouse(n)));
    ctxMenu.appendChild(mi('＋ 子女', '', 'Tab', () => addChild(n)));
    ctxMenu.appendChild(mi('＋ 同辈', '', 'Enter', () => addSibling(n)));
    ctxMenu.appendChild(msep());
    ctxMenu.appendChild(mi('改名', '', 'F2', () => editName(n)));
    ctxMenu.appendChild(mi('档案', '', 'Ctrl+I', () => editDetails(n)));
  }
  if (n.children && n.children.length){
    ctxMenu.appendChild(msep());
    ctxMenu.appendChild(mi(n.expanded ? '折叠此支' : '展开此支', '', '', () => toggleExpand(n)));
  }
  if (n.id !== 'root'){
    ctxMenu.appendChild(msep());
    ctxMenu.appendChild(mi('删除', 'danger', '', () => deleteNode(n)));
  }
}
function openMenu(wrap, n){
  document.querySelectorAll('.node').forEach(w => w.classList.remove('menu-open'));
  wrap.classList.add('menu-open');
  buildMenuItems(n);
  /* 先显示再测量：display:none 时 offsetWidth/Height 恒为 0（v12 定位失准根因） */
  ctxMenu.style.display = 'block';
  const rect = wrap.getBoundingClientRect();
  const mw = ctxMenu.offsetWidth;
  const mh = ctxMenu.offsetHeight;
  let left = rect.left + rect.width / 2 - mw / 2;
  left = Math.max(6, Math.min(left, window.innerWidth - mw - 6));
  let top = rect.bottom + 6;
  if (top + mh > window.innerHeight - 6) top = Math.max(6, rect.top - mh - 6);
  ctxMenu.style.left = left + 'px';
  ctxMenu.style.top  = top + 'px';
}
function closeMenu(){
  ctxMenu.style.display = 'none';
  document.querySelectorAll('.menu-open').forEach(w => w.classList.remove('menu-open'));
}
/* 点击任何空白区域关闭菜单（菜单项与「＋」都 stopPropagation，不会误关） */
document.addEventListener('click', () => closeMenu());

/* ---------- 顶栏下拉菜单：复用同一气泡面板（视图 / 文件） ---------- */
function openDropdown(btn, build){
  const wasOpen = btn.classList.contains('menu-open') && ctxMenu.style.display === 'block';
  closeMenu();
  if (wasOpen) return;                        // 再点一次 = 收起
  btn.classList.add('menu-open');
  ctxMenu.innerHTML = '';                     // 重复打开必须清空，否则菜单项累积
  build(ctxMenu);
  ctxMenu.style.display = 'block';            // 先显示再测量（v13 教训）
  const r = btn.getBoundingClientRect();
  const mw = ctxMenu.offsetWidth, mh = ctxMenu.offsetHeight;
  let left = Math.max(6, Math.min(r.right - mw, window.innerWidth - mw - 6));
  let top = r.bottom + 6;
  if (top + mh > window.innerHeight - 6) top = Math.max(6, r.top - mh - 6);
  ctxMenu.style.left = left + 'px';
  ctxMenu.style.top = top + 'px';
}
document.getElementById('btnView').addEventListener('click', e => {
  e.stopPropagation();
  const btn = document.getElementById('btnView');
  openDropdown(btn, m => {
    m.appendChild(mi((cfg.vertical ? '✓ ' : '') + '谱书竖排（古法）', '', '', toggleVertical));
    m.appendChild(msep());
    m.appendChild(mi('全展开', '', '', () => expandAll(true)));
    m.appendChild(mi('全折叠', '', '', () => expandAll(false)));
    m.appendChild(msep());
    m.appendChild(mi('谱序…', '', '', openClan, '谱名 / 堂号 / 源流 / 字辈表 / 始祖记'));
    m.appendChild(mi('显示设置…', '', '', openSettings, '字辈基准 / 配偶谱式 / 姓氏显示'));
    if (IS_TOUCH || window.innerWidth <= 860) m.appendChild(mi('帮助 / 快捷键', '', '', openHelp));
  });
});
document.getElementById('btnFile').addEventListener('click', e => {
  e.stopPropagation();
  const btn = document.getElementById('btnFile');
  openDropdown(btn, m => {
  m.appendChild(mi(IS_XHS ? '保存图片到相册' : '导出图片', '', 'png', exportPNG));
  if (IS_XHS){
      m.appendChild(mi('复制备份', '', '', function(){
      showTextModal('备份文本：点击「全选」后手动复制', JSON.stringify(sanitize(treeData), null, 2));
    }));
      m.appendChild(mi('粘贴导入备份', '', '', pasteImport));
  } else {
      m.appendChild(mi('备份到文件', '', 'json', backupToFile, '导出 json 备份：换电脑 / 防清缓存'));
      m.appendChild(mi('恢复备份', '', 'json', () => document.getElementById('__importFile').click(), '导入 json 备份（也支持旧版 HTML）'));
      m.appendChild(msep());
      m.appendChild(mi('导出 PDF', '', '', exportPDF, '图谱排版，单页'));
      m.appendChild(mi('导出世系录', '', '五世一表', exportShixilu, '欧式表格：浏览器打开即可打印'));
      m.appendChild(mi('导出 Markdown', '', 'md', exportMarkdown));
      m.appendChild(msep());
      m.appendChild(mi('打印', '', '', () => window.print(), '跟随当前视图排版'));
      m.appendChild(mi('按出生年重排', '', '', actSortByBirth));
      m.appendChild(msep());
      m.appendChild(mi('重置数据', 'danger', '', resetData, '清空并恢复为示例谱'));
  }
  });
});

/* ---------- 帮助弹窗 ---------- */
function hmIsOpen(){ return document.getElementById('__helpModal').classList.contains('open'); }
function openHelp(){
  /* 字辈表网格：蓝框 = 族谱中有人用这个字辈 */
  const lo = 1 + genOffset(), hi2 = lo + 39;
  const range = cfg.cnNum ? numToCn(lo) + '–' + numToCn(hi2) : lo + '–' + hi2;
  document.getElementById('__zbTitle').textContent =
    '字辈表（第' + range + genUnit() + '，蓝框 = 族谱中已出现）';
  const host = document.getElementById('__zbGrid');
  host.innerHTML = '';
  const zb = Array.isArray(treeData.zibei) ? treeData.zibei : [];
  if (zb.length){
    let all = '';
    (function w(n){ all += (n.name || ''); if (n.children) n.children.forEach(w); })(treeData);
    zb.forEach((z, i) => {
      const d = document.createElement('span');
      d.className = 'zb' + (z && all.includes(z) ? ' on' : '');
      d.innerHTML = esc(z || '·') + '<small>第' + genLabel(i + 1) + '</small>';
      d.title = '第' + genLabel(i + 1) + '字辈「' + (z || '?') + '」' + (all.includes(z) ? '（族谱中已出现）' : '');
      host.appendChild(d);
    });
  } else {
    host.innerHTML = '<span class="help-note">本文件尚未配置字辈表</span>';
  }
  document.getElementById('__helpModal').classList.add('open');
}
function closeHelp(){ document.getElementById('__helpModal').classList.remove('open'); }
document.getElementById('__helpClose').addEventListener('click', closeHelp);
document.getElementById('__helpModal').addEventListener('mousedown', e => {
  if (e.target.id === '__helpModal') closeHelp();
});

/* ---------- 显示设置弹窗（世代基准 / 配偶谱式） ---------- */
function smIsOpen(){ return document.getElementById('__setModal').classList.contains('open'); }
function openSettings(){
  document.getElementById('__cfgSurName').textContent = FAM_SUR || '（自动识别）';
  document.getElementById('__cfgBase').value = cfg.genBase;
  document.getElementById('__cfgSpouse').checked = !!cfg.bookSpouse;
  document.getElementById('__cfgSurname').checked = !!cfg.showSurname;
  document.getElementById('__cfgCn').checked = !!cfg.cnNum;
  document.getElementById('__setModal').classList.add('open');
  document.getElementById('__cfgBase').focus();
}
function closeSettings(){ document.getElementById('__setModal').classList.remove('open'); }
function applySettings(){
  const raw = parseInt(document.getElementById('__cfgBase').value, 10);
  cfg.genBase = isNaN(raw) ? 1 : Math.max(1, Math.min(99, raw));
  cfg.bookSpouse = document.getElementById('__cfgSpouse').checked;
  cfg.showSurname = document.getElementById('__cfgSurname').checked;
  cfg.cnNum = document.getElementById('__cfgCn').checked;
  saveCfg();
  closeSettings();
  render();
  toast('显示设置已保存：' + (cfg.genBase > 1 ? '字辈第 1 字 = 第 ' + cfg.genBase + ' 世' : '按应用自算代数')
    + ' · 配偶' + (cfg.bookSpouse ? '谱书式' : '原名')
    + ' · ' + (cfg.showSurname ? '显示姓氏' : '只报名')
    + ' · 世数' + (cfg.cnNum ? '用汉字' : '用数字'));
}
/* 谱书竖排（古法）开关：视图菜单切换 */
function toggleVertical(){
  cfg.vertical = !cfg.vertical;
  saveCfg();
  render();
  fitToScreen();
  toast(cfg.vertical ? '已切换谱书竖排（古法）：世代成行、名字竖书、行左标世数' : '已切回常规视图');
}

/* ---------- 谱序（堂号 / 源流）：数据存根节点 clan 字段，随备份导出走 ---------- */
function clanOf(){
  return treeData.clan || {};
}
function puTitle(){
  const c = clanOf();
  return (c.ming || '家族族谱') + (c.tang ? '（' + c.tang + '）' : '');
}
function updateClanTags(){
  const c = clanOf();
  document.getElementById('__puName').textContent = c.ming || '家族族谱';
  const tt = document.getElementById('__tangTag');
  if (c.tang){ tt.textContent = c.tang; tt.style.display = ''; }
  else tt.style.display = 'none';
  document.title = (c.ming || '家族族谱') + (c.tang ? ' · ' + c.tang : '');
}
function cmIsOpen(){ return document.getElementById('__clanModal').classList.contains('open'); }
function openClan(){
  const c = clanOf();
  const g = id => document.getElementById(id);
  g('__clMing').value   = c.ming   || '';
  g('__clTang').value   = c.tang   || '';
  g('__clChain').value  = c.chain  || '';
  g('__clZibei').value  = (treeData.zibei || []).join(' ');
  g('__clYuan').value   = c.yuanzu || '';
  g('__clShi').value    = c.shizu  || '';
  g('__clQian').value   = c.qianzu || '';
  g('__clOrigin').value = c.origin || '';
  g('__clanModal').classList.add('open');
  g('__clMing').focus();
}
function closeClan(){ document.getElementById('__clanModal').classList.remove('open'); }
function saveClan(){
  const g = id => document.getElementById(id).value.trim();
  const clan = {
    ming: g('__clMing'), tang: g('__clTang'), chain: g('__clChain'),
    yuanzu: g('__clYuan'), shizu: g('__clShi'), qianzu: g('__clQian'), origin: g('__clOrigin')
  };
  const zbRaw = document.getElementById('__clZibei').value.trim();
  const zibei = zbRaw ? zbRaw.split(/[\s,，、·.]+/).map(x => x.trim()).filter(Boolean) : [];
  const zibeiChanged = JSON.stringify(zibei) !== JSON.stringify(treeData.zibei || []);
  if (deepEq(clan, treeData.clan || {}) && !zibeiChanged){ closeClan(); return; }
  pushHistory('clan');
  treeData.clan = clan;
  if (zibei.length) treeData.zibei = zibei; else delete treeData.zibei;
  closeClan();
  updateClanTags();
  render();
  toast('谱序已保存：谱名、堂号将随导出与打印一起出现');
}
document.getElementById('__clSave').addEventListener('click', saveClan);
document.getElementById('__clCancel').addEventListener('click', closeClan);
document.getElementById('__clanModal').addEventListener('mousedown', e => {
  if (e.target.id === '__clanModal') closeClan();
});
document.getElementById('__clanModal').addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA'){
    e.preventDefault(); e.stopPropagation(); saveClan();
  }
  if (e.key === 'Escape'){ e.preventDefault(); e.stopPropagation(); closeClan(); }
});
document.getElementById('__brand').addEventListener('click', openClan);

/* 顶栏按钮绑定（CSP 兼容：容器禁止行内 onclick） */
var ACT_MAP = { undo: function(){ undo(); }, redo: function(){ redo(); },
  search: function(){ openSearch(); },
  zoomout: function(){ zoomBy(-0.15); }, zoomin: function(){ zoomBy(0.15); },
  fit: function(){ fitToScreen(); }, reset: function(){ resetZoom(); },
  help: function(){ openHelp(); } };
document.querySelectorAll('[data-act]').forEach(function(b){
  b.addEventListener('click', function(){ ACT_MAP[b.getAttribute('data-act')](); });
});

/* ---------- 首次运行向导（内嵌种子带 demo 标记时弹出，三选一） ---------- */
function wmIsOpen(){ return document.getElementById('__wizModal').classList.contains('open'); }
function openWizard(){ document.getElementById('__wizModal').classList.add('open'); }
function closeWizard(){ document.getElementById('__wizModal').classList.remove('open'); }
function wizardDemo(){
  treeData.demo = false;
  closeWizard(); render();
  toast('示例数据：双击名字改名、点「＋」添加成员，所有操作都可撤销');
}
function wizardBlank(){
  const ming = document.getElementById('__wizMing').value.trim() || '我的家族';
  const tang = document.getElementById('__wizTang').value.trim();
  pushHistory('wizard');
  treeData = migrate({ id: 'root', name: ming, spouses: [], expanded: true, children: [],
                       clan: { ming, tang, chain: '', yuanzu: '', shizu: '', qianzu: '', origin: '' } });
  closeWizard(); render(); fitToScreen();
  toast('空白族谱「' + ming + '」已创建：点第一个「＋」添加第一代成员');
}
function wizardImport(){
  closeWizard();
  if (IS_XHS){ pasteImport(); }   // 容器的文件选择器只能选图片，走粘贴导入
  else { document.getElementById('__importFile').click(); }
}
document.querySelectorAll('#__wizModal [data-wiz]').forEach(b => {
  b.addEventListener('click', () => { b.dataset.wiz === 'demo' ? wizardDemo() : wizardImport(); });
});
document.getElementById('__wizGo').addEventListener('click', wizardBlank);
document.getElementById('__wizModal').addEventListener('mousedown', e => {
  if (e.target.id === '__wizModal') closeWizard();   // 未选择则下次仍会提醒
});
document.getElementById('__wizModal').addEventListener('keydown', e => {
  if (e.key === 'Enter'){ e.preventDefault(); e.stopPropagation(); wizardBlank(); }
  if (e.key === 'Escape'){ e.preventDefault(); e.stopPropagation(); closeWizard(); }
});
document.getElementById('__setSave').addEventListener('click', applySettings);
document.getElementById('__setCancel').addEventListener('click', closeSettings);
document.getElementById('__setModal').addEventListener('mousedown', e => {
  if (e.target.id === '__setModal') closeSettings();
});
document.getElementById('__setModal').addEventListener('keydown', e => {
  if (e.key === 'Enter'){
    e.preventDefault(); e.stopPropagation(); applySettings();
  }
  if (e.key === 'Escape'){ e.preventDefault(); e.stopPropagation(); closeSettings(); }
});

/* ---------- ⑧ 编辑动作（每个改动数据的动作都有 pushHistory 提交点） ---------- */
function addSpouse(n){
  if (!n.spouses) n.spouses = [];
  const nth = n.spouses.length + 1;
  uiPrompt('为「' + n.name + '」添加第 ' + nth + ' 位配偶姓名：\n（如需改名/移除某位配偶，直接双击图上该配偶的名字）').then(function(t){
  if (t === null) return;
  const v = t.trim();
  if (!v) return;
  if (n.spouses.includes(v)){ toast('「' + v + '」已是 ' + n.name + ' 的配偶，无需重复添加'); return; }
  pushHistory('addSpouse:' + n.id);
  n.spouses.push(v);
  render();
  toast('已为 ' + n.name + ' 添加配偶「' + v + '」，继续点「＋配偶」可再加');
  });
}

function editSpouseAt(n, i){
  if (!n.spouses || i < 0 || i >= n.spouses.length) return;
  const cur = n.spouses[i];
  uiPrompt('修改「' + n.name + '」的第 ' + (i + 1) + ' 位配偶：\n（清空并确定 = 移除这位配偶）', cur).then(function(t){
  if (t === null) return;
  const v = t.trim();
  if (!v){
    if (confirm('确定移除配偶「' + cur + '」？')){
      pushHistory('rmSpouse:' + n.id + ':' + i);
      n.spouses.splice(i, 1);
    } else return;
  } else {
    if (v === cur) return;
    pushHistory('editSpouse:' + n.id + ':' + i);
    n.spouses[i] = v;
  }
  render();
  });
}

function addChild(n){
  uiPrompt(
    n.id === 'root'
      ? '在「家族族谱」下添加一位第一代成员（新祖辈分支）：'
      : '为「' + displayName(n) + '」添加子女姓名：'
  ).then(function(t){
  if (t === null || !t.trim()) return;
  pushHistory('addChild:' + n.id);
  if (!n.children) n.children = [];
  n.expanded = true;
  n.children.push({ id: genId('c'), name: t.trim(), spouses: [], birth:'', death:'', note:'', expanded: true, children: [] });
  render();
  selectNode(n.children[n.children.length - 1].id);
  toast(n.id === 'root'
    ? '已添加第一代成员「' + t.trim() + '」（默认排最右=最幼，按住拖动可调长幼）'
    : '已为 ' + n.name + ' 添加子女「' + t.trim() + '」');
  });
}

function deleteNode(n){
  if (n.id === 'root'){ toast('根节点不能删'); return; }
  const desc = countDescendants(n);
  const msg = desc
    ? '删除「' + displayName(n) + '」及其全部 ' + desc + ' 位后代？'
    : '删除「' + displayName(n) + '」？';
  if (!confirm(msg)) return;
  pushHistory('delete:' + n.id);
  const p = findParent(n.id);
  if (p) p.children = p.children.filter(c => c.id !== n.id);
  if (selectedId === n.id) selectedId = null;
  render();
  toast('已删除（可用 Ctrl+Z 撤销）');
}

function addSibling(n){
  const p = findParent(n.id); if (!p) return;
  uiPrompt('添加一位与「' + n.name + '」同辈的成员（' + (p.id === 'root' ? '第一代' : '同父母') + '）：').then(function(t){
  if (t === null || !t.trim()) return;
  pushHistory('addSibling:' + n.id);
  const nb = { id: genId('s'), name: t.trim(), spouses: [], birth:'', death:'', note:'', expanded: true, children: [] };
  p.children.push(nb);
  render();
  selectNode(nb.id);
  toast('已添加「' + t.trim() + '」，默认排最右=最幼；按住拖到左边可成为更长');
  });
}

function toggleExpand(n){
  pushHistory('fold:' + n.id);
  n.expanded = !n.expanded;
  render();
}
function expandAll(v){
  pushHistory('expandAll:' + v);
  (function w(n){ n.expanded = v; if (n.children) n.children.forEach(w); })(treeData);
  render();
}
function sortAllByBirth(){
  let touched = 0;
  (function w(n){ if (sortSiblings(n)) touched++; if (n.children) n.children.forEach(w); })(treeData);
  return touched;
}

function actSortByBirth(){
  pushHistory('sortByBirth');
  const t = sortAllByBirth();
  render();
  toast(t > 0
    ? '已按出生年重排 ' + t + ' 组同辈（年长在左；无出生年的保持原次序排其后）'
    : '暂无任何人填出生年，未做改动（先在「档案」里补出生年）');
}

/* 拖动过继：把 n（连同其后代）挂到 newParent 名下（排最幼），并展开新支让你看到结果 */
function reparentNode(n, newParent){
  const old = findParent(n.id);
  if (!old || newParent.id === old.id) return false;
  if (subtreeContains(n, newParent.id)) return false;   // 不能挂到自己后代名下（成环）
  old.children = old.children.filter(c => c.id !== n.id);
  if (!Array.isArray(newParent.children)) newParent.children = [];
  newParent.children.push(n);
  n.expanded = true;
  newParent.expanded = true;
  return true;
}

/* ---------- ⑨ 拖拽：兄弟间换长幼 + 悬停过继（拖到某卡片上停 0.4s = 挂到 TA 名下） ---------- */
(function(){
  const stage = document.getElementById('stage');
  let drag = null;
  let suppressClickUntil = 0;
  let dwellT = null;

  function wrapOf(id){ return document.querySelector('.node[data-id="' + id + '"]'); }
  function clearHoverMarks(){
    document.querySelectorAll('.node.drop-target, .node.drop-bad').forEach(w =>
      w.classList.remove('drop-target', 'drop-bad'));
  }
  function clearTarget(){
    if (dwellT){ clearTimeout(dwellT); dwellT = null; }
    clearHoverMarks();
    if (drag) drag.targetId = null;
  }
  /* 悬停 0.4 秒不动 → 该卡片亮起为「放到 TA 名下」目标 */
  function scheduleDwell(hoverId){
    if (dwellT) clearTimeout(dwellT);
    dwellT = setTimeout(() => {
      dwellT = null;
      if (!drag || !drag.moved || drag.hoverId !== hoverId || drag.targetId === hoverId) return;
      if (subtreeContains(drag.n, hoverId)) return;         // 自己的后代：拒绝
      clearHoverMarks();
      drag.targetId = hoverId;
      const w = wrapOf(hoverId);
      if (w) w.classList.add('drop-target');
      const m = document.getElementById('__dropMarker');
      if (m) m.style.display = 'none';                      // 过继模式下不显示插行线
    }, 400);
  }

  document.addEventListener('pointerdown', e => {
    if (!e.isPrimary || (e.pointerType === 'mouse' && e.button !== 0)) return;
    /* 菜单内按下：绝不触发关闭逻辑（mousedown 先于 click，先销毁菜单则 click 落空） */
    if (e.target.closest && (e.target.closest('#__ctxMenu') || e.target.closest('#searchBox'))) return;
    closeMenu();
    const label = e.target.closest && e.target.closest('.node-label');
    if (!label) return;
    if (document.activeElement && document.activeElement.contentEditable === 'true') return;
    const wrap = label.closest('.node');
    const id = wrap.dataset.id;
    if (id === 'root') return;
    const n = findNode(id);
    const parent = findParent(id);
    if (!n || !parent) return;   // 独子也可拖：拖去别人名下（过继）；同辈多时左右拖=换长幼
    drag = {
      id, n, parent,
      oldIdx: parent.children.findIndex(c => c.id === id),
      ids: [], baseLeft: new Map(),
      moved: false, startX: e.clientX, startY: e.clientY,
      insertIdx: -1,
      hoverId: null, targetId: null
    };
    (function collect(x){ drag.ids.push(x.id); if (x.children) x.children.forEach(collect); })(n);
  });

  document.addEventListener('pointermove', e => {
    if (!drag) return;
    const dx = e.clientX - drag.startX, dy = e.clientY - drag.startY;
    if (!drag.moved){
      if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
      drag.moved = true;
      pushHistory('drag');
      drag.els = new Map();   // 缓存元素引用：拖动期间零 DOM 查询（性能）
      drag.ids.forEach(iid => {
        const w = document.querySelector('.node[data-id="' + iid + '"]');
        if (w){ drag.baseLeft.set(iid, parseFloat(w.style.left) || 0); w.classList.add('dragging'); drag.els.set(iid, w); }
      });
    }
    /* 整个子树跟随平移（连线落位后重画） */
    drag.ids.forEach(iid => {
      const w = drag.els && drag.els.get(iid);
      if (w && drag.baseLeft.has(iid)) w.style.left = (drag.baseLeft.get(iid) + dx) + 'px';
    });
    /* 指针换算画布坐标 */
    const rect = stage.getBoundingClientRect();
    const px = (e.clientX - rect.left) / scale;
    const py = (e.clientY - rect.top) / scale;

    /* —— 悬停命中：光标停在谁身上（数学命中，被拖子树 pointer-events:none）—— */
    let hover = null;
    nodeRects.forEach((r0, nid) => {
      if (nid === drag.id || subtreeContains(drag.n, nid)) return;
      if (Math.abs(px - r0.x) <= r0.w / 2 + 4 && py >= r0.y - 4 && py <= r0.y + r0.h + 26) hover = nid;
    });
    if (drag.targetId && hover !== drag.targetId) clearTarget();
    drag.hoverId = hover;
    if (hover && hover !== drag.targetId){
      const w = wrapOf(hover);
      if (w && !w.classList.contains('drop-bad')){
        clearHoverMarks();
        if (subtreeContains(drag.n, hover)){
          w.classList.add('drop-bad');                    // 自己的后代：红框拒绝
        } else {
          scheduleDwell(hover);
        }
      }
    }
    if (drag.targetId){ return; }                          // 过继模式下不再更新插行线

    /* —— 兄弟换位逻辑（原有行为）—— */
    const sibs = drag.parent.children.filter(c => c.id !== drag.id);
    let idx = 0;
    for (const s of sibs){ if (px > s._x) idx++; else break; }
    drag.insertIdx = idx;
    const m = document.getElementById('__dropMarker');
    let mx;
    if (sibs.length === 0){ mx = drag.n._x; }
    else if (idx === 0){ mx = sibs[0]._x - (sibs[0]._w || 80) / 2 - H_SPACE / 2; }
    else if (idx >= sibs.length){ mx = sibs[sibs.length - 1]._x + (sibs[sibs.length - 1]._w || 80) / 2 + H_SPACE / 2; }
    else { mx = (sibs[idx - 1]._x + sibs[idx]._x) / 2; }
    m.style.left = mx + 'px';
    m.style.top = (drag.n._y + 12) + 'px';
    m.style.display = 'block';
  });

  document.addEventListener('pointercancel', () => {
    if (!drag) return;
    drag = null;
    if (dwellT){ clearTimeout(dwellT); dwellT = null; }
    const m2 = document.getElementById('__dropMarker');
    if (m2) m2.style.display = 'none';
    clearHoverMarks();
    document.querySelectorAll('.node.dragging').forEach(w => w.classList.remove('dragging'));
    render();   // 系统打断手势：回弹到拖动前
  });
  document.addEventListener('pointerup', () => {
    if (!drag) return;
    const d = drag; drag = null;
    if (dwellT){ clearTimeout(dwellT); dwellT = null; }
    const m = document.getElementById('__dropMarker');
    if (m) m.style.display = 'none';
    clearHoverMarks();
    if (!d.moved) return;               // 未达拖动阈值 = 普通点击（历史快照只在 move 阈值时入栈）
    suppressClickUntil = Date.now() + 350;
    d.ids.forEach(iid => {
      const w = document.querySelector('.node[data-id="' + iid + '"]');
      if (w) w.classList.remove('dragging');
    });

    /* —— 过继落点：松手时若停在有效目标上 → 挂到 TA 名下 —— */
    if (d.targetId){
      const tp = findNode(d.targetId);
      if (tp && reparentNode(d.n, tp)){
        selectedId = d.id;
        render();
        selectNode(d.id);
        toast(tp.id === 'root'
          ? '「' + d.n.name + '」已移入第一代（可拖拽微调长幼）'
          : '「' + d.n.name + '」已过继到「' + tp.name + '」名下（排最幼，可拖拽微调长幼；Ctrl+Z 可撤销）');
        return;
      }
      /* 目标非法（成环等）→ 落回原处，走普通换位收尾 */
    }

    /* —— 普通换位落点 —— */
    const arr = d.parent.children;
    const me = arr.splice(d.oldIdx, 1)[0];
    const newIdx = Math.max(0, Math.min(arr.length, d.insertIdx < 0 ? d.oldIdx : d.insertIdx));
    arr.splice(newIdx, 0, me);
    render();
    if (newIdx !== d.oldIdx)
      toast('已换位：' + me.name + ' 现在是同辈第 ' + (newIdx + 1) + ' 位（排行「' + rankWord(newIdx) + '」，最左为长）');
  });

  /* 拖完立刻的 click 不触发选中 */
  document.addEventListener('click', e => {
    if (Date.now() < suppressClickUntil){ e.stopPropagation(); e.preventDefault(); }
  }, true);
})();

/* ---------- ⑩ 缩放 / 平移 ---------- */
let scale = 1;
function applyZoom(recenter){
  const stEl = document.getElementById('stage');
  const scEl = document.getElementById('scaler');
  scEl.style.transform = 'scale(' + scale + ')';
  /* stage 盒子 = 基准×缩放：滚动范围随之正确（transform 不产生滚动范围） */
  if (stEl._baseW){ stEl.style.width = stEl._baseW * scale + 'px'; stEl.style.height = stEl._baseH * scale + 'px'; }
  if (recenter) centerStage();   /* 锚点缩放（滚轮）期间不重居中：会和锚点补偿打架 */
  document.getElementById('zoomLabel').textContent = Math.round(scale * 100) + '%';
}
/* 滚轮缩放：倍速（触控板小增量也顺滑）+ rAF 插值动画，光标锚点全程保持 */
let targetScale = 1, zoomRaf = null, zoomAnchor = null;
function animateZoom(){
  if (zoomRaf) return;
  const step = () => {
    const diff = targetScale - scale;
    if (Math.abs(diff) < 0.0015){
      scale = targetScale;
      applyZoom(!zoomAnchor);
      if (zoomAnchor) zoomAtAnchor();
      zoomRaf = null;
      return;
    }
    scale += diff * 0.35;
    applyZoom(!zoomAnchor && !window.__pinchActive);
    if (zoomAnchor) zoomAtAnchor();
    zoomRaf = requestAnimationFrame(step);
  };
  zoomRaf = requestAnimationFrame(step);
}
function zoomAtAnchor(){
  const vp = document.getElementById('viewport');
  const stEl = document.getElementById('stage');
  const ox = stEl.offsetLeft, oy = stEl.offsetTop;   // 移动端悬浮工具栏会让 stage 下移，锚点数学须含此偏移
  const rect = vp.getBoundingClientRect();
  const mx = zoomAnchor.cx - rect.left, my = zoomAnchor.cy - rect.top;
  const wx = (zoomAnchor.sl + mx - ox) / zoomAnchor.s, wy = (zoomAnchor.st + my - oy) / zoomAnchor.s;
  vp.scrollLeft = Math.max(0, ox + wx * scale - mx);
  vp.scrollTop  = Math.max(0, oy + wy * scale - my);
}
function zoomBy(d){
  scale = Math.min(2.5, Math.max(0.12, scale + d));
  targetScale = scale;
  applyZoom();
  return scale;
}
function resetZoom(){ scale = 1; targetScale = 1; applyZoom(); }
function centerStage(){
  /* 按当前缩放把舞台在视口内居中：水平居中解决“靠左”，垂直居中让画布上下都有余量 */
  const stEl = document.getElementById('stage'), vp = document.getElementById('viewport');
  if (!stEl._baseW) return;
  const barTop = window.innerWidth <= 860 ? 120 : 76;
  stEl.style.left = Math.max(0, (vp.clientWidth - stEl._baseW * scale) / 2) + 'px';
  stEl.style.top = Math.max(barTop, barTop + (vp.clientHeight - barTop - stEl._baseH * scale) / 2) + 'px';
}
function fitToScreen(){
  const vp = document.getElementById('viewport');
  const st = document.getElementById('stage');
  const w = st.offsetWidth, h = st.offsetHeight;
  if (!w || !h) return;
  scale = Math.max(0.12, Math.min((vp.clientWidth - 30) / w, (vp.clientHeight - 30) / h, 1.2));
  targetScale = scale;
  applyZoom();
  centerStage();
}
document.getElementById('viewport').addEventListener('wheel', e => {
  if (e.ctrlKey){
    e.preventDefault();
    const vp = document.getElementById('viewport');
    const rect = vp.getBoundingClientRect();
    zoomAnchor = { cx: e.clientX, cy: e.clientY, sl: vp.scrollLeft, st: vp.scrollTop, s: scale };
    setTargetScale(scale * Math.exp(-e.deltaY * 0.0016));
  }
}, { passive: false });
function setTargetScale(ns){
  targetScale = Math.min(2.5, Math.max(0.12, ns));
  animateZoom();
}

/* 平移：拖空白处（避开标签/菜单/搜索框） */
(function(){
  const vp = document.getElementById('viewport');
  let down = false, sx = 0, sy = 0, sl = 0, st = 0;
  vp.addEventListener('pointerdown', e => {
    if (!e.isPrimary || (e.pointerType === 'mouse' && e.button !== 0)) return;
    if (e.target.closest('.node-label') || e.target.closest('.quick-add') || e.target.closest('#searchBox')) return;
    down = true; sx = e.clientX; sy = e.clientY;
    sl = vp.scrollLeft; st = vp.scrollTop;
    vp.classList.add('panning');
  });
  window.addEventListener('pointermove', e => {
    if (!down) return;
    vp.scrollLeft = sl - (e.clientX - sx);
    vp.scrollTop  = st - (e.clientY - sy);
  });
  window.addEventListener('pointerup', () => { down = false; vp.classList.remove('panning'); });
  window.addEventListener('pointercancel', () => { down = false; vp.classList.remove('panning'); });
})();

/* ---------- 触屏：长按=菜单 / 双击=改名 / 双指=缩放（容器与移动端） ---------- */
(function(){
  const vp = document.getElementById('viewport');
  let lpTimer = null, lpX = 0, lpY = 0;
  let lastTapT = 0, lastTapId = '';
  let pinch = null;
  function clearLP(){ if (lpTimer){ clearTimeout(lpTimer); lpTimer = null; } }
  function tdist(ts){
    const dx = ts[0].clientX - ts[1].clientX, dy = ts[0].clientY - ts[1].clientY;
    return Math.sqrt(dx * dx + dy * dy) || 1;
  }
  vp.addEventListener('pointerdown', e => {
    if (e.pointerType !== 'touch' || !e.isPrimary) return;
    const label = e.target.closest ? e.target.closest('.node-label') : null;
    if (!label) return;
    const wrap = label.closest('.node');
    const n = wrap ? findNode(wrap.getAttribute('data-id')) : null;
    if (!n || n.id === 'root') return;
    lpX = e.clientX; lpY = e.clientY;
    clearLP();
    lpTimer = setTimeout(() => {
      lpTimer = null;
      selectNode(n.id);
      openMenu(wrap, n);
    }, 480);
  }, true);
  document.addEventListener('pointermove', e => {
    if (lpTimer && (Math.abs(e.clientX - lpX) > 10 || Math.abs(e.clientY - lpY) > 10)) clearLP();
  }, true);
  document.addEventListener('pointerup', e => {
    clearLP();
    if (e.pointerType !== 'touch') return;
    const label = e.target.closest ? e.target.closest('.node-label') : null;
    const id = label ? (label.closest('.node') ? label.closest('.node').getAttribute('data-id') : '') : '';
    const now = Date.now();
    if (id && id === lastTapId && now - lastTapT < 320){
      lastTapT = 0; lastTapId = '';
      const n = findNode(id);
      if (n){ selectNode(id); editName(n); }
      return;
    }
    lastTapT = now; lastTapId = id;
  }, true);
  vp.addEventListener('touchstart', e => {
    if (e.touches.length === 2){
      clearLP();
      window.__pinchActive = true;
      pinch = { d0: tdist(e.touches), s0: scale };
    }
  }, { passive: true });
  vp.addEventListener('touchmove', e => {
    if (pinch && e.touches.length === 2){
      e.preventDefault();
      setTargetScale(pinch.s0 * tdist(e.touches) / pinch.d0);
    }
  }, { passive: false });
  vp.addEventListener('touchend', () => { pinch = null; window.__pinchActive = false; }, { passive: true });
  vp.addEventListener('touchcancel', () => { pinch = null; window.__pinchActive = false; }, { passive: true });
})();

/* ---------- ⑪ 搜索（Ctrl+F / 顶栏放大镜；仅搜当前可见分支） ---------- */
const sbBox = document.getElementById('searchBox');
const sbInput = document.getElementById('sbInput');
const sbCount = document.getElementById('sbCount');
let _lastQuery = '';
let _hitIds = [];
let _hitIdx = -1;
function searchOpenState(){ return sbBox.classList.contains('open'); }
function openSearch(){
  sbBox.classList.add('open');
  sbInput.focus(); sbInput.select();
}
function closeSearch(){
  sbBox.classList.remove('open');
  document.getElementById('sbList').classList.remove('open');
  if (document.activeElement === sbInput) sbInput.blur();   // 焦点交还画布：否则快捷键被隐藏输入框吞掉（v15.14 修复）
  sbInput.value = '';
  setQuery('');
}
function closeSearchHighlights(){
  document.querySelectorAll('.node.hit, .node.hit-active').forEach(w => w.classList.remove('hit', 'hit-active'));
  _hitIds = []; _hitIdx = -1; sbCount.textContent = '';
}
function setQuery(q){
  _lastQuery = q.trim();
  applySearchHighlight();
}
function nodeMatches(n, q){
  return [n.name, n.zi, n.hao].concat(n.spouses || []).concat([n.birth, n.death, n.note])
    .some(v => v && String(v).includes(q));
}
function applySearchHighlight(){
  document.querySelectorAll('.node.hit, .node.hit-active').forEach(w => w.classList.remove('hit', 'hit-active'));
  _hitIds = [];
  if (!_lastQuery){ sbCount.textContent = ''; _hitIdx = -1; renderSbList(); return; }
  const q = _lastQuery;
  /* 全树匹配（含折叠分支） */
  const allIds = [];
  (function w(n){
    if (nodeMatches(n, q)) allIds.push(n.id);
    if (n.children) n.children.forEach(w);
  })(treeData);
  /* 命中在折叠支内 → 自动展开其祖先链（搜索不该有盲区） */
  let expandedAny = false;
  allIds.forEach(id => {
    let p = findParent(id);
    while (p){
      if (!p.expanded){ p.expanded = true; expandedAny = true; }
      p = findParent(p.id);
    }
  });
  if (expandedAny){ render(); return; }   // render 尾部会再次进入本函数完成高亮
  _hitIds = allIds;
  _hitIds.forEach(id => {
    const w = document.querySelector('.node[data-id="' + id + '"]');
    if (w) w.classList.add('hit');
  });
  _hitIdx = -1;
  if (_hitIds.length) stepHit(1);
  else sbCount.textContent = '无匹配';
  renderSbList();
}

/* 结果列表：点选即跳到该成员并居中选中 */
let _sbSel = 0;
function renderSbList(){
  const list = document.getElementById('sbList');
  if (!_lastQuery || !_hitIds.length){ list.classList.remove('open'); list.innerHTML = ''; return; }
  list.innerHTML = '';
  _hitIds.slice(0, 50).forEach((id, i) => {
    const n = findNode(id);
    if (!n) return;
    const item = document.createElement('div');
    item.className = 'sb-item' + (i === _sbSel ? ' sel' : '');
    const gen = LAST_GENS.get(id);
    const zb = Array.isArray(treeData.zibei) ? treeData.zibei : [];
    const gtxt = gen ? (genLabel(gen.gen) + (gen.zi || zb[gen.gen - 1] ? '·' + (gen.zi || zb[gen.gen - 1]) : '')) : '';
    item.innerHTML = (gtxt ? '<span class="g">' + esc(gtxt) + '</span>' : '') +
      '<span class="nm">' + esc(dispName(n.name)) + (n.gender === 'f' ? '<i class="gx">女</i>' : '') + '</span>' +
      '<span class="sub">' + (metaLine(n) ? esc(metaLine(n)).slice(0, 14) : (gen ? genLabel(gen.gen) : '?')) + '</span>';
    item.onclick = e => { e.stopPropagation(); jumpToHit(i); };
    list.appendChild(item);
  });
  list.classList.add('open');
  _sbSel = Math.min(_sbSel, _hitIds.length - 1);
  const sel = list.querySelector('.sb-item.sel');
  if (sel) sel.scrollIntoView({ block: 'nearest' });
}
function jumpToHit(i){
  if (!_hitIds.length) return;
  const prev = _hitIds[_hitIdx];
  if (prev){
    const pw = document.querySelector('.node[data-id="' + prev + '"]');
    if (pw) pw.classList.remove('hit-active');
  }
  _hitIdx = i;
  const id = _hitIds[i];
  const w = document.querySelector('.node[data-id="' + id + '"]');
  if (!w) return;
  w.classList.add('hit-active');
  sbCount.textContent = (i + 1) + '/' + _hitIds.length;
  const n = findNode(id);
  const r0 = nodeRects.get(id);
  const vp = document.getElementById('viewport');
  vp.scrollTo({
    left: n._x * scale - vp.clientWidth / 2,
    top:  (n._y + (r0 ? r0.h / 2 : 0)) * scale - vp.clientHeight / 2,
    behavior: 'smooth'
  });
  selectNode(id);
  renderSbList();
}
function sbMoveSel(dir){
  if (!_hitIds.length) return;
  _sbSel = ((_sbSel + dir) % _hitIds.length + _hitIds.length) % _hitIds.length;
  renderSbList();
  jumpToHit(_sbSel);
}
function stepHit(dir){
  if (!_hitIds.length) return;
  const prev = _hitIds[_hitIdx];
  if (prev){
    const pw = document.querySelector('.node[data-id="' + prev + '"]');
    if (pw) pw.classList.remove('hit-active');
  }
  _hitIdx = ((_hitIdx + dir) % _hitIds.length + _hitIds.length) % _hitIds.length;
  const id = _hitIds[_hitIdx];
  const w = document.querySelector('.node[data-id="' + id + '"]');
  if (!w) return;
  w.classList.add('hit-active');
  sbCount.textContent = (_hitIdx + 1) + '/' + _hitIds.length;
  const n = findNode(id);
  const r0 = nodeRects.get(id);
  const vp = document.getElementById('viewport');
  vp.scrollTo({
    left: n._x * scale - vp.clientWidth / 2,
    top:  (n._y + (r0 ? r0.h / 2 : 0)) * scale - vp.clientHeight / 2,
    behavior: 'smooth'
  });
}
sbInput.addEventListener('input', () => setQuery(sbInput.value));
sbInput.addEventListener('keydown', e => {
  if (e.key === 'ArrowDown'){ e.preventDefault(); sbMoveSel(1); return; }
  if (e.key === 'ArrowUp'){ e.preventDefault(); sbMoveSel(-1); return; }
  if (e.key === 'Enter'){ e.preventDefault(); jumpToHit(_sbSel); }
});
document.getElementById('sbNext').onclick = () => stepHit(1);
document.getElementById('sbPrev').onclick = () => stepHit(-1);
document.getElementById('sbClose').onclick = () => { closeSearch(); };

/* ---------- ⑫ 导入 / 导出 / 保存到文件 / 打印 ---------- */
function exportMarkdown(){
  let s = '# ' + puTitle() + '\n\n';
  (function md(n, d){
    let line = dispName(n.name) + (n.gender === 'f' ? '（女）' : '');
    if (n.zi) line += '（字' + n.zi + '）';
    if (n.hao) line += '（号' + n.hao + '）';
    if (n.heir === 'in') line += '（嗣子）';
    if (n.heir === 'out') line += '（嗣出）';
    if (n.heir === 'jian') line += '（兼祧）';
    if (n.zhi) line += '（止）';
    line += (n.spouses && n.spouses.length ? '（' + spousesText(n) + '）' : '');
    const b = (n.birth || '').trim(), de = (n.death || '').trim();
    if (b || de) line += '（' + [b, de].filter(Boolean).join(' – ') + '）';
    if (n.note) line += ' — ' + n.note;
    s += '  '.repeat(d) + '- ' + line + '\n';
    if (n.children) n.children.forEach(c => md(c, d + 1));
  })(treeData, 0);
  download((clanOf().ming || '家族族谱') + '.md', s, 'text/markdown;charset=utf-8');
}

/* ---------- 世系录（欧式：五世一表，每人一行行传） ---------- */
function exportShixilu(){
  const GENSX = LAST_GENS.size ? LAST_GENS : computeGenerations();
  const zb = Array.isArray(treeData.zibei) ? treeData.zibei : [];
  /* 行第：与卡片角标同一套规则（有生年按年排序，无生年按手动次序） */
  const ranks = new Map();
  (function rk(n){
    if (n.children && n.children.length > 1){
      const known = n.children.filter(c => parseYear(c.birth));
      const unknown = n.children.filter(c => !parseYear(c.birth));
      known.slice().sort((a, b) => parseYear(a.birth) - parseYear(b.birth)).concat(unknown)
        .forEach((c, i) => { ranks.set(c.id, i); });
    }
    if (n.children) n.children.forEach(rk);
  })(treeData);
  const rows = [];
  (function w(n){
    if (n.id !== 'root'){
      const g = GENSX.get(n.id);
      rows.push({
        gen: g ? g.gen : null,
        zi: g ? (g.zi || zb[g.gen - 1] || '') : '',
        name: n.name || '', ziname: n.zi || '', hao: n.hao || '',
        rank: ranks.has(n.id) ? rankWord(ranks.get(n.id)) : '',
        birth: (n.birth || '').trim(), death: (n.death || '').trim(),
        spouses: spousesText(n),
        kids: (n.children || []).map(c => dispName(c.name) + (c.gender === 'f' ? '（女）' : '')).join('、'),
        heir: n.heir === 'in' ? '嗣子' : n.heir === 'out' ? '嗣出' : n.heir === 'jian' ? '兼祧' : '',
        zhi: n.zhi ? '止' : '',
        note: n.note || ''
      });
    }
    if (n.children) n.children.forEach(w);
  })(treeData);
  /* 五世一表：按谱世（=应用代数+世代基准）每五代分一表 */
  const groups = new Map();
  rows.forEach(r => {
    const s = r.gen ? r.gen + genOffset() : 0;
    const gi = s === 0 ? -1 : Math.floor((s - 1) / 5);
    if (!groups.has(gi)) groups.set(gi, []);
    groups.get(gi).push(r);
  });
  const d = new Date(), pad = n => String(n).padStart(2, '0');
  const today = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  let html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>' + esc(puTitle() + ' · 世系录') + '</title><style>'
    + 'body{font-family:"Songti SC","SimSun",serif;color:#222;margin:32px auto;max-width:1120px;padding:0 18px}'
    + 'h1{font-size:22px;color:#16324f;margin:0 0 4px}'
    + 'h2{font-size:16px;color:#16324f;border-bottom:1.5px solid #c8d2dc;padding-bottom:4px;margin:26px 0 8px}'
    + '.sub{color:#667;font-size:12.5px;margin-bottom:16px}'
    + '.pre{white-space:pre-wrap;font-size:13px;line-height:1.85;background:#f7f9fb;border:1px solid #dde4ec;border-radius:8px;padding:10px 14px;margin:8px 0 2px}'
    + 'table{width:100%;border-collapse:collapse;font-size:13px;margin:6px 0 14px}'
    + 'th,td{border:1px solid #b9c3cf;padding:5px 8px;text-align:left;vertical-align:top;line-height:1.55}'
    + 'th{background:#eef2f7;color:#16324f;font-weight:700;white-space:nowrap}'
    + 'tr:nth-child(even) td{background:#fafbfc}'
    + 'td.c{white-space:nowrap}'
    + '@media print{body{margin:8mm}.pre{background:none}}'
    + '</style></head><body>';
  html += '<h1>' + esc(puTitle()) + ' · 世系录</h1>';
  html += '<div class="sub">欧式 · 五世一表 · 导出于 ' + today + ' · 共 ' + rows.length + ' 人</div>';
  const c = clanOf();
  if (c.chain)  html += '<div class="pre"><b>源流世系：</b>' + esc(c.chain) + '</div>';
  if (c.yuanzu) html += '<div class="pre"><b>先祖：</b>' + esc(c.yuanzu) + '</div>';
  if (c.shizu)  html += '<div class="pre"><b>始祖记：</b>' + esc(c.shizu) + '</div>';
  if (c.qianzu) html += '<div class="pre"><b>' + esc((c.qianzu.split('：')[0] || '始迁祖')) + '：</b>' + esc(c.qianzu.split('：').slice(1).join('：')) + '</div>';
  if (c.origin) html += '<div class="pre"><b>家族来源：</b>' + esc(c.origin) + '</div>';
  Array.from(groups.keys()).sort((a, b) => a - b).forEach(gi => {
    const list = groups.get(gi);
    if (gi < 0) html += '<h2>未定世次</h2>';
    else {
      const s0 = gi * 5 + 1, s1 = gi * 5 + 5;
      html += '<h2>第' + numToCn(s0) + '世至第' + numToCn(s1) + '世</h2>';
    }
    html += '<table><tr><th>世次</th><th>讳</th><th>字</th><th>号</th><th>行第</th><th>生</th><th>卒</th><th>配偶</th><th>子女</th><th>记</th></tr>';
    list.forEach(r => {
      const ji = [r.heir, r.zhi, r.note].filter(Boolean).join('；');
      html += '<tr>'
        + '<td class="c">' + (r.gen ? numToCn(r.gen + genOffset()) + '世' + (r.zi ? '·' + r.zi : '') : '—') + '</td>'
        + '<td><b>' + esc(dispName(r.name)) + '</b></td>'
        + '<td>' + esc(r.ziname) + '</td>'
        + '<td>' + esc(r.hao) + '</td>'
        + '<td class="c">' + esc(r.rank) + '</td>'
        + '<td class="c">' + esc(r.birth) + '</td>'
        + '<td class="c">' + esc(r.death) + '</td>'
        + '<td>' + esc(r.spouses) + '</td>'
        + '<td>' + esc(r.kids) + '</td>'
        + '<td>' + esc(ji) + '</td>'
        + '</tr>';
    });
    html += '</table>';
  });
  html += '</body></html>';
  download((clanOf().ming || '家族族谱') + '-世系录-' + d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate()) + '-' + pad(d.getHours()) + pad(d.getMinutes()) + '.html',
           html, 'text/html;charset=utf-8');
  toast('世系录已下载（五世一表）：浏览器打开即可查阅或打印');
}

function download(name, content, type){
  if (IS_XHS){ toast('小工具内不支持下载文件：请使用电脑网页版导出'); return; }
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 3000);
}

/* 校验导入结构：递归检查每人是合法对象 */
function validTree(d){
  if (!d || typeof d !== 'object' || Array.isArray(d)) return false;
  if (typeof d.name !== 'string' || typeof d.id !== 'string' || !d.id) return false;
  if (!Array.isArray(d.spouses) || !d.spouses.every(s => typeof s === 'string')) return false;
  if (!Array.isArray(d.children)) return false;
  return d.children.every(validTree);
}

document.getElementById('__importFile').addEventListener('change', function(){
  const f = this.files && this.files[0];
  this.value = '';
  if (!f) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      let txt = reader.result;
      if (/\.html?$/i.test(f.name)){
        const m = txt.match(/<script id="__treeData"[^>]*>([\s\S]*?)<\/script>/);
        if (!m) throw new Error('这个 HTML 里没有族谱数据');
        txt = m[1];
      }
      const d = JSON.parse(txt);
      if (!validTree(d)) throw new Error('结构不符：需要 {id,name,children[]} 树');
      if ((!Array.isArray(d.zibei) || !d.zibei.length) && Array.isArray(treeData.zibei))
        d.zibei = treeData.zibei;   // 导入旧数据时保留本族字辈表
      pushHistory('import');
      treeData = migrate(d);
      selectedId = null;
      render();
      fitToScreen();
      toast('已导入「' + f.name + '」，数据已自动保存');
    } catch(e){
      alert('导入失败：不是有效的族谱 JSON 文件\n' + e.message);
    }
  };
  reader.readAsText(f, 'utf-8');
});

function resetData(){
  if (!confirm('确定重置？当前族谱将被清空，恢复到本文件自带的初始数据。\n（如需保留，先「备份到文件」；误删可用 Ctrl+Z）')) return;
  pushHistory('reset');
  treeData = JSON.parse(JSON.stringify(INIT_TEMPLATE));
  selectedId = null;
  render();
  fitToScreen();
  toast('已重置为本文件的初始数据（再次「保存到文件」可固化）');
}

/* 备份到文件：纯下载一份 json（无弹窗、不写任何已有文件）。
   数据真源在浏览器，备份用于换电脑 / 防清缓存 */
function backupToFile(){
  const d = new Date(), pad = n => String(n).padStart(2, '0');
  const fname = (clanOf().ming || '家族族谱') + '-备份-' + d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate())
              + '-' + pad(d.getHours()) + pad(d.getMinutes()) + '.json';
  download(fname, JSON.stringify(sanitize(treeData), null, 2), 'application/json');
  toast('备份已下载：' + fname);
}

/* ---------- 图谱导出（png / pdf）----------
 * 按布局数据在 canvas 重绘全树（不受当前缩放/平移影响），含连线、字辈角标、
 * 排行角标、折叠角标、生卒年备注；PDF 为内嵌 jpeg 的单页文档，零依赖。 */
function exportPalette(){
  const cs = getComputedStyle(document.documentElement);
  const v = k => cs.getPropertyValue(k).trim();
  return {
    line: v('--line'), text: v('--text'), textLight: v('--text-light'),
    rootBg: v('--root-bg'), rootFg: v('--root-fg'),
    rank: v('--rank-bg'), birth: v('--birth-bg'),
    g: [v('--g1'), v('--g2'), v('--g3'), v('--g4'), v('--g5')]
  };
}
function exportTreeCanvas(){
  const stage = document.getElementById('stage');
  let W = stage.offsetWidth, H = stage.offsetHeight;
  if (!W || !H) throw new Error('画布尚未渲染');
  {   /* 标题行宽度自适应：谱名（堂号）· 日期 在窄画布（竖排）下不被裁切 */
    const d0 = new Date(), p0 = n => String(n).padStart(2, '0');
    const t0 = puTitle() + ' · ' + d0.getFullYear() + '-' + p0(d0.getMonth() + 1) + '-' + p0(d0.getDate());
    W = Math.max(W, Math.min(560, t0.length * 17 + 40));
  }
  let S = Math.min(3, 12000 / Math.max(W, H));
  if (!isFinite(S) || S <= 0) S = 1;
  const cv = document.createElement('canvas');
  cv.width = Math.round(W * S); cv.height = Math.round(H * S + 46 * S);
  const ctx = cv.getContext('2d');
  ctx.scale(S, S);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, W, H + 46);
  const d = new Date(), pad = n => String(n).padStart(2, '0');
  ctx.fillStyle = '#16324f';
  ctx.font = '600 16px "PingFang SC","Microsoft YaHei",sans-serif';
  ctx.fillText(puTitle() + ' · ' + d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()), 20, 30);
  ctx.translate((W - stage.offsetWidth) / 2, 46);   /* 加宽出的边距左右均分，树居中 */

  const P = exportPalette();
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';

  const depthMap = new Map(), rankMap = new Map();
  (function walk(n, depth, idx, total){
    depthMap.set(n.id, depth);
    rankMap.set(n.id, { idx, total });
    if (n.expanded && n.children) n.children.forEach((c, i) => walk(c, depth + 1, i, n.children.length));
  })(treeData, 0, 0, 1);
  const GENS = computeGenerations();
  const zbList = Array.isArray(treeData.zibei) ? treeData.zibei : [];
  const FONT = '"PingFang SC","Microsoft YaHei",sans-serif';

  ctx.strokeStyle = cfg.vertical ? '#d5dde6' : P.line; ctx.lineWidth = 1.5;
  (function lines(n){
    const r = nodeRects.get(n.id); if (!r) return;
    if (n.expanded && n.children && n.children.length){
      const f = nodeRects.get(n.children[0].id), l = nodeRects.get(n.children[n.children.length - 1].id);
      if (f && l){
        ctx.beginPath();
        if (cfg.vertical){
          const yTop = r.y + r.h;
          const busY = Math.max(yTop + 8, (yTop + f.y) / 2);
          ctx.moveTo(r.x, yTop); ctx.lineTo(r.x, busY);
          if (n.children.length > 1){ ctx.moveTo(Math.min(f.x, l.x), busY); ctx.lineTo(Math.max(f.x, l.x), busY); }
          n.children.forEach(c => {
            const cr = nodeRects.get(c.id);
            if (cr){ ctx.moveTo(cr.x, busY); ctx.lineTo(cr.x, cr.y); }
          });
        } else {
          const yTop = r.y + r.h, yChild = r.y + V_SPACE;
          const midY = Math.max(yTop + 26, (yTop + yChild) / 2);
          ctx.moveTo(r.x, yTop); ctx.lineTo(r.x, midY);
          if (n.children.length > 1){ ctx.moveTo(Math.min(f.x, l.x), midY); ctx.lineTo(Math.max(f.x, l.x), midY); }
          n.children.forEach(c => {
            const cr = nodeRects.get(c.id);
            if (cr){ ctx.moveTo(cr.x, midY); ctx.lineTo(cr.x, yChild); }
          });
        }
        ctx.stroke();
      }
      n.children.forEach(lines);
    }
  })(treeData);

  function rr(x, y, w, h, r){ ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
  function ellipText(t, maxW){
    if (ctx.measureText(t).width <= maxW) return t;
    while (t.length > 1 && ctx.measureText(t + '…').width > maxW) t = t.slice(0, -1);
    return t + '…';
  }
  /* 竖排节点绘制：列自右向左（古法阅读序）——名字 → 女/嗣 → 字号 → 配偶 */
  function drawNodeV(n, r, depth){
    const x = r.x - r.w / 2, y = r.y, w = r.w, h = r.h;
    const isRoot = n.id === 'root', isNote = n.id === 'note';
    const gcol = P.g[Math.min(Math.max(depth, 1), 5) - 1];
    if (isRoot){   /* 始祖：纸色底 + 细墨线，其余不画框（框退后、字为主角） */
      ctx.setLineDash([]);
      rr(x, y, w, h, 3);
      ctx.fillStyle = '#fffdf8'; ctx.fill();
      ctx.lineWidth = 1.5; ctx.strokeStyle = 'rgba(93,80,60,.5)'; ctx.stroke();
    }
    ctx.textBaseline = 'middle';
    /* 与 DOM 竖排一致：单列自上而下 名→女→嗣→止→字号→配偶（称谓+名） */
    let cy = y + 10;
    const seg = (t, size, weight, color) => {
      size = +size || 13;   // 防御：size 传错也不污染 cy 坐标
      ctx.font = weight + ' ' + size + 'px ' + FONT;
      ctx.fillStyle = color; ctx.textAlign = 'center';   // v15.23 修复：漏掉这行导致整列字左对齐起笔、视觉整体偏右
      for (let i = 0; i < t.length; i++){
        ctx.fillText(t[i], x + w / 2, cy + size / 2);
        cy += size + 2.5;
      }
    };
    seg(dispName(n.name), isRoot ? 16.5 : 16, '600', isRoot ? '#16324f' : (isNote ? '#a0a8b2' : '#29231c'));
    if (n.gender === 'f') seg('女', 11, '600', '#b04a72');
    if (n.heir) seg('嗣', 11, '700', n.heir === 'jian' ? '#2f6390' : (n.heir === 'out' ? '#b8842e' : '#a2661b'));
    if (n.zhi) seg('止', 11, '700', '#3c4a57');
    if (n.zi) seg('字' + n.zi, 11, '400', '#9aa9bb');
    if (n.hao) seg('号' + n.hao, 11, '400', '#9aa9bb');
    (n.spouses || []).forEach((s, si) => {
      seg(spouseRoleAt(n, si), 9, '400', 'rgba(150,156,164,.95)');
      seg(spouseDisplay(s), 12, '400', '#9aa0a8');
    });
    if (!n.expanded && n.children && n.children.length){
      const t = '▸ ' + countDescendants(n);
      ctx.font = '600 10px ' + FONT;
      ctx.fillStyle = '#66768c'; ctx.textAlign = 'center';
      ctx.fillText(t, x + w / 2, y - 12);   /* 与 DOM 一致：折叠钮悬于卡片上缘之外 */
    }
    ctx.textBaseline = 'alphabetic';
  }
  (function drawNode(n){
    const r = nodeRects.get(n.id);
    if (r){
      const depth = depthMap.get(n.id) || 0;
      if (cfg.vertical){ drawNodeV(n, r, depth); }
      else{
      const x = r.x - r.w / 2, y = r.y, w = r.w, h = r.h;
      const isRoot = n.id === 'root', isNote = n.id === 'note';
      const gcol = P.g[Math.min(Math.max(depth, 1), 5) - 1];
      ctx.setLineDash(isNote ? [5, 4] : []);
      rr(x, y, w, h, isRoot ? 11 : 9);
      ctx.fillStyle = isRoot ? P.rootBg : '#ffffff';
      ctx.fill();
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = isRoot ? P.rootBg : (isNote ? P.textLight : gcol);
      ctx.stroke();
      ctx.setLineDash([]);

      const gen = GENS.get(n.id);
      let chipW = 0;
      if (gen){
        const zi = gen.zi || zbList[gen.gen - 1] || '';
        const t = genLabel(gen.gen) + (zi ? '·' + zi : '');
        ctx.font = '600 10px ' + FONT;
        chipW = ctx.measureText(t).width + 10;
        const match = gen.src === 'match';
        rr(x + 14, y + 4, chipW, 16, 5);
        ctx.fillStyle = match ? '#e8f1fa' : '#eef2f7'; ctx.fill();
        ctx.lineWidth = 1; ctx.strokeStyle = match ? '#b9d6ee' : '#dbe3ec'; ctx.stroke();
        ctx.fillStyle = match ? '#2f6390' : '#66768c';
        ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
        ctx.fillText(t, x + 19, y + 12.5);
        ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
      }

      if (!isRoot && !isNote){
        const rk = rankMap.get(n.id);
        const yr = parseYear(n.birth);
        const badge = (t, bg) => {
          ctx.font = '700 10px ' + FONT;
          const bw = Math.max(ctx.measureText(t).width + 8, 16);
          rr(x - 8, y - 8, bw, 16, 8);
          ctx.fillStyle = bg; ctx.fill();
          ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
          ctx.fillText(t, x - 8 + bw / 2, y);
          ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
        };
        if (yr) badge(String(yr), P.birth);
        else if (rk.total > 1) badge(rankWord(rk.idx), P.rank);
      }

      if (!n.expanded && n.children && n.children.length){
        const t = '▸ ' + countDescendants(n);
        ctx.font = '600 10px ' + FONT;
        const pw = ctx.measureText(t).width + 12;
        rr(x + w - pw - 6, y + 4, pw, 16, 8);
        ctx.fillStyle = '#eef2f7'; ctx.fill();
        ctx.lineWidth = 1; ctx.strokeStyle = '#d5dde6'; ctx.stroke();
        ctx.fillStyle = '#66768c'; ctx.fillText(t, x + w - pw, y + 12.5);
      }

      const padX = isRoot ? 18 : 13;
      let tx = x + padX + chipW + (chipW ? 5 : 0);
      const nameY = y + (isRoot ? 20 : 15);
      ctx.textAlign = 'left';
      ctx.font = (isRoot ? '600 15px ' : '600 13px ') + FONT;
      ctx.fillStyle = isRoot ? P.rootFg : (isNote ? P.textLight : P.text);
      const nmTxt = dispName(n.name);
      ctx.fillText(nmTxt, tx, nameY);
      tx += ctx.measureText(nmTxt).width;
      if (n.gender === 'f'){
        ctx.font = '600 9.5px ' + FONT;
        const gw = ctx.measureText('女').width + 7;
        rr(tx + 3, nameY - 11, gw, 14, 4);
        ctx.fillStyle = '#fbe9f0'; ctx.fill();
        ctx.lineWidth = 1; ctx.strokeStyle = '#eebcd0'; ctx.stroke();
        ctx.fillStyle = '#b04a72'; ctx.textBaseline = 'middle';
        ctx.fillText('女', tx + 3 + gw / 2, nameY - 4);
        ctx.textBaseline = 'alphabetic';
        tx += gw + 3;
      }
      if (n.heir){
        ctx.font = '700 9.5px ' + FONT;
        const gw = ctx.measureText('嗣').width + 7;
        rr(tx + 3, nameY - 11, gw, 14, 4);
        if (n.heir === 'jian'){ ctx.fillStyle = '#eaf4fb'; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = '#7fb3d5'; }
        else { ctx.fillStyle = n.heir === 'out' ? '#ffffff' : '#fdf3e3'; ctx.fill(); ctx.lineWidth = 1; ctx.strokeStyle = '#e8c88a'; }
        ctx.stroke();
        if (n.heir === 'out') ctx.setLineDash([2, 2]);
        ctx.fillStyle = n.heir === 'jian' ? '#2f6390' : '#a2661b'; ctx.textBaseline = 'middle';
        ctx.fillText('嗣', tx + 3 + gw / 2, nameY - 4);
        ctx.setLineDash([]);
        ctx.textBaseline = 'alphabetic';
        tx += gw + 3;
      }
      if (n.zhi){
        ctx.beginPath();
        ctx.arc(tx + 11, nameY - 4.5, 7.5, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff'; ctx.fill();
        ctx.lineWidth = 1.2; ctx.strokeStyle = '#52616f'; ctx.stroke();
        ctx.fillStyle = '#3c4a57';
        ctx.font = '700 9px ' + FONT; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText('止', tx + 11, nameY - 4);
        ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
        tx += 20;
      }
      if (n.zi || n.hao){
        const t = (n.zi ? '字' + n.zi : '') + (n.zi && n.hao ? ' ' : '') + (n.hao ? '号' + n.hao : '');
        ctx.font = '400 10px ' + FONT;
        ctx.fillStyle = isRoot ? 'rgba(255,255,255,.6)' : P.textLight;
        ctx.fillText(t, tx + 4, nameY);
        tx += ctx.measureText(t).width + 4;
      }
      if (n.spouses && n.spouses.length){
        n.spouses.forEach((sp, si) => {
          ctx.font = '400 9px ' + FONT;
          const role = spouseRoleAt(n, si);
          ctx.fillStyle = isRoot ? 'rgba(255,255,255,.55)' : '#8fa0b5';
          ctx.fillText(role, tx + 4, nameY);
          tx += ctx.measureText(role).width + 8;
          const spTxt = spouseDisplay(sp);
          ctx.font = '400 13px ' + FONT;
          ctx.fillStyle = isRoot ? 'rgba(255,255,255,.66)' : P.textLight;
          ctx.fillText(spTxt, tx, nameY);
          tx += ctx.measureText(spTxt).width + 6;
        });
      }

      const meta = metaLine(n);
      if (meta){
        ctx.font = '400 10px ' + FONT;
        ctx.fillStyle = isRoot ? 'rgba(255,255,255,.75)' : P.textLight;
        ctx.fillText(ellipText(meta, w - padX * 2), x + padX, y + h - 7);
      }
      }
    }
    if (n.expanded && n.children) n.children.forEach(drawNode);
  })(treeData);

  /* 竖排：行左世数标（与页面上的谱书页边标注一致，固定汉字数字） */
  if (cfg.vertical){
    const rowGenX = [];
    (function rgx(n, d){
      if (!rowGenX[d]){
        const g = LAST_GENS.get(n.id);
        if (g) rowGenX[d] = g.gen;
      }
      if (n.expanded && n.children) n.children.forEach(c => rgx(c, d + 1));
    })(treeData, 0);
    const zbX = Array.isArray(treeData.zibei) ? treeData.zibei : [];
    ctx.font = '600 13.5px ' + FONT;
    ctx.fillStyle = '#9aa9bb'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    for (let d = 1; d < rowGenX.length; d++){
      const g = rowGenX[d];
      if (!g) continue;
      let minY = null;
      (function ny(n, dd){
        if (dd === d){
          const r0 = nodeRects.get(n.id);
          if (r0 && (minY === null || r0.y < minY)) minY = r0.y;
        }
        if (n.expanded && n.children) n.children.forEach(c => ny(c, dd + 1));
      })(treeData, 0);
      if (minY !== null){
        const zi = zbX[g - 1] || '';
        const t = numToCn(g + genOffset()) + genUnit() + (zi ? '·' + zi : '');
        for (let i = 0; i < t.length; i++) ctx.fillText(t[i], 8, minY + 14 + i * 16);
      }
    }
    ctx.textBaseline = 'alphabetic';
  }
  return cv;
}
function stampName(ext){
  const d = new Date(), pad = n => String(n).padStart(2, '0');
  return (clanOf().ming || '家族族谱') + '-图-' + d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate())
       + '-' + pad(d.getHours()) + pad(d.getMinutes()) + ext;
}
function savePngToAlbum(cv){
  try {
    var mt = window.xhs.miniTool;
    if (!(mt && mt.writeTempFile && mt.saveImageToPhotosAlbum)){ toast('当前环境不支持保存到相册'); return; }
    toast('正在保存图片…');
    mt.writeTempFile({ data: cv.toDataURL('image/png') }).then(function(r){
      return mt.saveImageToPhotosAlbum({ filePath: r.filePath });
    }).then(function(){ toast('图片已保存到相册'); })
      .catch(function(e){ toast('保存失败：' + ((e && e.errMsg) || e)); });
  } catch(e){ toast('保存失败：' + e.message); }
}
function exportPNG(){
  try {
    const cv = exportTreeCanvas();
    if (IS_XHS){ savePngToAlbum(cv); return; }
    cv.toBlob(bl => {
      download(stampName('.png'), bl, 'image/png');
      toast('图片已下载（' + cv.width + '×' + cv.height + '）');
    }, 'image/png');
  } catch(e){ toast('导出失败：' + e.message); }
}
function exportPDF(){
  try {
    const cv = exportTreeCanvas();
    const b64 = cv.toDataURL('image/jpeg', 0.95).split(',')[1];
    const img = atob(b64);
    const W = Math.round(cv.width * 0.75), H = Math.round(cv.height * 0.75);
    const content = 'q\n' + W + ' 0 0 ' + H + ' 0 0 cm\n/Im1 Do\nQ\n';
    const parts = [], offsets = [0, 0, 0, 0, 0, 0];
    let pos = 0;
    const add = str => { parts.push(str); pos += str.length; };
    const obj = (num, body) => { offsets[num] = pos; add(num + ' 0 obj\n' + body + '\nendobj\n'); };
    add('%PDF-1.4\n');
    obj(1, '<< /Type /Catalog /Pages 2 0 R >>');
    obj(2, '<< /Type /Pages /Kids [3 0 R] /Count 1 >>');
    obj(3, '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ' + W + ' ' + H + '] /Resources << /XObject << /Im1 4 0 R >> /ProcSet [/PDF /ImageC] >> /Contents 5 0 R >>');
    obj(5, '<< /Length ' + content.length + ' >>\nstream\n' + content + 'endstream');
    offsets[4] = pos;
    add('4 0 obj\n<< /Type /XObject /Subtype /Image /Width ' + cv.width + ' /Height ' + cv.height +
        ' /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ' + img.length + ' >>\nstream\n');
    parts.push(img); pos += img.length;
    add('\nendstream\nendobj\n');
    const xref = pos;
    add('xref\n0 6\n0000000000 65535 f\n');
    for (let i = 1; i <= 5; i++) add(String(offsets[i]).padStart(10, '0') + ' 00000 n\n');
    add('trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n' + xref + '\n%%EOF');
    const bytes = new Uint8Array(pos);
    let p = 0;
    parts.forEach(seg => { for (let i = 0; i < seg.length; i++) bytes[p++] = seg.charCodeAt(i) & 0xff; });
    download(stampName('.pdf'), bytes, 'application/pdf');
    toast('PDF 已下载（' + W + '×' + H + ' pt）');
  } catch(e){ toast('导出失败：' + e.message); }
}

/* 谱书竖排打印页：克隆当前舞台（卡片/连线/行左世数标），按 A4 纵向可打印区缩放，可装订成册 */
function buildPrintDomVertical(){
  const area = document.getElementById('printArea');
  area.innerHTML = '';
  const h = document.createElement('h2');
  const d = new Date(), pad = n => String(n).padStart(2, '0');
  h.textContent = puTitle() + ' · ' + d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  area.appendChild(h);
  const stage = document.getElementById('stage');
  const clone = stage.cloneNode(true);
  clone.removeAttribute('id');
  clone.className = 'ps v';
  clone.style.transform = 'none';
  clone.style.width = stage.offsetWidth + 'px';
  clone.style.height = stage.offsetHeight + 'px';
  clone.style.left = '0';
  clone.style.top = '0';
  clone.querySelectorAll('.quick-add').forEach(q => q.remove());
  clone.querySelectorAll('.selected,.hit,.hit-active,.menu-open').forEach(el =>
    el.classList.remove('selected', 'hit', 'hit-active', 'menu-open'));
  const s = Math.min(1, 700 / stage.offsetWidth, 1030 / stage.offsetHeight);   /* A4 纵向可打印区 ≈ 186×273mm */
  const wrap = document.createElement('div');
  wrap.className = 'pstage-wrap';
  wrap.style.width = Math.ceil(stage.offsetWidth * s) + 'px';
  wrap.style.height = Math.ceil(stage.offsetHeight * s) + 'px';
  clone.style.transform = 'scale(' + s + ')';
  clone.style.transformOrigin = 'top left';
  wrap.appendChild(clone);
  area.appendChild(wrap);
  let cnt = 0;
  (function w2(n){ if (n.id !== 'root') cnt++; if (n.children) n.children.forEach(w2); })(treeData);
  const note = document.createElement('div');
  note.className = 'pmeta';
  note.style.marginTop = '6px';
  note.textContent = '谱书竖排 · 共 ' + cnt + ' 人' + (s < 1 ? '（整图已按页面缩放 ' + Math.round(s * 100) + '%）' : '');
  area.appendChild(note);
}

/* 打印：画布绝对坐标跨页会切破卡片，改为现场生成文档式大纲（打印全部分支，无视折叠） */
function printMemberRow(n, gen, rank){
  let core = '<b>' + esc(dispName(n.name || '')) + '</b>';
  if (n.gender === 'f') core += '（女）';
  if (n.heir === 'in') core += '（嗣子）';
  if (n.heir === 'out') core += '（嗣出）';
  if (n.heir === 'jian') core += '（兼祧）';
  if (n.zhi) core += '（止）';
  const zx = [];
  if (n.zi) zx.push('字' + n.zi);
  if (n.hao) zx.push('号' + n.hao);
  const sps = (n.spouses && n.spouses.length)
    ? '<span class="psp">（' + esc(spousesText(n)) + '）</span>' : '';
  let extra = '';
  const b = (n.birth || '').trim(), de = (n.death || '').trim();
  if (b || de) extra += '<span class="pmeta">（' + esc([b, de].filter(Boolean).join(' – ')) + '）</span>';
  if (n.note) extra += '<span class="pmeta">— ' + esc(n.note) + '</span>';
  const genChip = gen ? '<span class="pgen">' + esc(genLabel(gen.gen) + (gen.zi ? '·' + gen.zi : '')) + '</span>'
                      : (rank ? '<span class="pgen">' + esc(rank) + '</span>' : '');
  return genChip + core + (zx.length ? '<span class="pzi">（' + esc(zx.join('·')) + '）</span>' : '') + sps + extra;
}
function buildPrintDomReal(){
  if (cfg.vertical) return buildPrintDomVertical();
  const area = document.getElementById('printArea');
  area.innerHTML = '';
  const GENSX = LAST_GENS.size ? LAST_GENS : computeGenerations();
  const ranks = new Map();
  (function rk(n){
    if (n.children && n.children.length > 1){
      const known = n.children.filter(c => parseYear(c.birth));
      const unknown = n.children.filter(c => !parseYear(c.birth));
      known.slice().sort((a, b) => parseYear(a.birth) - parseYear(b.birth)).concat(unknown)
        .forEach((c, i) => { ranks.set(c.id, i); });
    }
    if (n.children) n.children.forEach(rk);
  })(treeData);
  const h = document.createElement('h2');
  const d = new Date(), pad = n => String(n).padStart(2, '0');
  h.textContent = puTitle() + ' · ' + d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  area.appendChild(h);
  const c = clanOf();
  const xu = document.createElement('div');
  xu.className = 'pxu';
  let xuHtml = '';
  if (c.chain)  xuHtml += '<div><b>源流世系：</b>' + esc(c.chain) + '</div>';
  if (c.yuanzu) xuHtml += '<div><b>先祖：</b>' + esc(c.yuanzu) + '</div>';
  if (c.shizu)  xuHtml += '<div><b>始祖记：</b>' + esc(c.shizu) + '</div>';
  if (c.qianzu) xuHtml += '<div><b>' + esc((c.qianzu.split('：')[0] || '始迁祖')) + '：</b>' + esc(c.qianzu.split('：').slice(1).join('：')) + '</div>';
  if (c.origin) xuHtml += '<div><b>家族来源：</b>' + esc(c.origin) + '</div>';
  if (xuHtml){ xu.innerHTML = xuHtml; area.appendChild(xu); }
  const rootUl = document.createElement('ul');
  rootUl.className = 'ptree';
  (function li(n, ul){
    const row = document.createElement('li');
    row.innerHTML = printMemberRow(n, n.id === 'root' ? null : GENSX.get(n.id), ranks.get(n.id));
    if (n.children && n.children.length){
      const sub = document.createElement('ul');
      n.children.forEach(c => li(c, sub));
      row.appendChild(sub);
    }
    ul.appendChild(row);
  })(treeData, rootUl);
  area.appendChild(rootUl);
}
window.addEventListener('beforeprint', buildPrintDomReal);

/* ---------- ⑬ 键盘总控（分层守卫：搜索框 > 弹窗 > 输入型目标 > 全局快捷键） ---------- */
document.addEventListener('keydown', e => {
  const target = e.target;
  const typing = target && (
    target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable
  );
  /* Esc 最优先处理：无论焦点在哪都能层层退出 */
  if (e.key === 'Escape'){
    if (hmIsOpen()){ e.preventDefault(); e.stopPropagation(); closeHelp(); return; }
    if (searchOpenState()){ e.preventDefault(); e.stopPropagation(); closeSearch(); return; }
    if (cmIsOpen()){ e.preventDefault(); e.stopPropagation(); closeClan(); return; }
    if (wmIsOpen()){ e.preventDefault(); e.stopPropagation(); closeWizard(); return; }
    if (dmIsOpen()){ return; }            // 弹窗自己的 handler 负责
    if (smIsOpen()){ e.preventDefault(); e.stopPropagation(); closeSettings(); return; }
    closeMenu();
    return;
  }
  /* 其余按键：输入中 / 弹窗开着 一律不触发全局快捷键（v12 泄漏 bug 根因） */
  if (typing || dmIsOpen() || hmIsOpen() || smIsOpen() || cmIsOpen() || wmIsOpen() || e.defaultPrevented) return;

  const mod = e.ctrlKey || e.metaKey;
  if (mod && e.key.toLowerCase() === 'f'){ e.preventDefault(); openSearch(); return; }
  if (mod && e.key.toLowerCase() === 's' && !e.shiftKey){
    e.preventDefault();   // 已自动保存：拦下浏览器另存即可
    toast('已自动保存，无需手动操作');
    return;
  }
  if (mod && e.key.toLowerCase() === 'z'){
    e.preventDefault();
    if (e.shiftKey) redo(); else undo();
    return;
  }
  if (mod && e.key.toLowerCase() === 'y'){ e.preventDefault(); redo(); return; }

  const n = selectedId ? findNode(selectedId) : null;
  if (!n) return;
  if (e.key === 'Tab'){ e.preventDefault(); addChild(n); }
  else if (e.key === 'Enter' && n.id !== 'root'){ e.preventDefault(); addSibling(n); }
  else if (e.key === 'Delete'){ deleteNode(n); }
  else if (e.key === 'F2'){ e.preventDefault(); editName(n); }
  else if (mod && e.shiftKey && e.key.toLowerCase() === 's'){ e.preventDefault(); addSpouse(n); }
  else if (mod && e.key.toLowerCase() === 'i'){ e.preventDefault(); editDetails(n); }
});

/* 右键节点 = 打开同一份操作菜单 */
document.getElementById('viewport').addEventListener('contextmenu', e => {
  const w = e.target.closest && e.target.closest('.node');
  if (!w) return;
  e.preventDefault();
  const n = findNode(w.dataset.id);
  if (!n) return;
  selectNode(n.id);
  openMenu(w, n);
});

/* 点空白取消选中（绑在外层容器：悬浮提示条 pointer-events:none，点击落到容器） */
document.querySelector('.canvas-wrap').addEventListener('click', e => {
  if (e.target.id === 'viewport' || e.target.id === 'stage' || e.target.id === 'nodes'
      || e.target.classList.contains('canvas-wrap')){
    selectedId = null;
    document.querySelectorAll('.node').forEach(w => w.classList.remove('selected'));
  }
});

/* toast：复用静态元素 */
let _toastT;
function toast(msg){
  const el = document.getElementById('__toast');
  el.textContent = msg;
  el.style.opacity = '1';
  clearTimeout(_toastT);
  _toastT = setTimeout(() => { el.style.opacity = '0'; }, 2600);
}

/* 测试/调试句柄（内部工具，普通使用无需理会） */
window.__ZP = {
  ver: '15.30',
  get cfg(){ return cfg; },
  get data(){ return treeData; },
  set data(v){ treeData = migrate(JSON.parse(JSON.stringify(v))); pushHistory('zpSet'); render(); },
  get scale(){ return scale; },
  historyLens(){ return [_undoStack.length, _redoStack.length]; },
  rects(){ return nodeRects; },
  storageKey(){ return STORAGE_KEY; },
  findNode, sanitize, snapshot: historySnapshot
};

/* 初始化 */
render();
fitToScreen();
refreshUndoButtons();
updateClanTags();
if (treeData.demo) openWizard();   /* 首次使用：示例数据 + 三选一向导 */
if (IS_TOUCH && !localStorage.getItem('zupu_gesture_hint')){
  try { localStorage.setItem('zupu_gesture_hint', '1'); } catch(e){}   // 存储禁用时不该抛错
  var gh = document.getElementById('__gestureHint');
  gh.classList.add('show');
  setTimeout(function(){ gh.classList.remove('show'); }, 4500);
}
if (_seededFrom === 'legacy-draft') toast('已从本浏览器的历史数据恢复族谱');
else if (_seededFrom === 'file') toast('自动保存已就绪：编辑即保存，无需手动操作');
