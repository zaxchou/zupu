# -*- coding: utf-8 -*-
"""从 index.html（中文母本）生成 index-en.html / index-ja.html。

规则：
- 表项 = (源串, 目标串) 或 (源串, 目标串, 期望次数)；全部精确子串替换。
- 任何失配（找不到 / 次数不符）会被收集并在最后报告，且不写出文件——绝不静默。
- 母本演进后重跑本脚本即可发现漏翻（drift detector）。
- 代码注释保持中文（面向贡献者）；只有用户可见文案翻译。
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')

# ============================================================ EN 表
EN = [
  # ---- 顶栏 ----
  ('title="谱序 · 宗族源流（堂号/始祖/源流世系）"', 'title="Pedigree preface · clan origin (hall name / forebears / lineage)"'),
  ('<span class="name" id="__puName">家族族谱</span>', '<span class="name" id="__puName">Family Tree</span>'),
  ('<span class="tag">传代树</span>', '<span class="tag">Lineage Tree</span>'),
  ('title="撤销（Ctrl+Z）"', 'title="Undo (Ctrl+Z)"'),
  ('title="重做（Ctrl+Y）"', 'title="Redo (Ctrl+Y)"'),
  ('title="搜索（Ctrl+F）"', 'title="Search (Ctrl+F)"'),
  ('<button class="btn" id="btnView" title="视图">视图<', '<button class="btn" id="btnView" title="View">View<'),
  ('<button class="btn" id="btnFile" title="文件">文件<', '<button class="btn" id="btnFile" title="File">File<'),
  ('title="缩小"', 'title="Zoom out"'),
  ('title="放大"', 'title="Zoom in"'),
  ('title="适应屏幕"', 'title="Fit to screen"'),
  ('title="恢复 1:1"', 'title="Reset 1:1"'),
  ('<span id="statsChip"><b>4</b> 位成员 · 配偶 <b>2</b> · 4 代</span>', '<span id="statsChip"><b>4</b> members · spouses <b>2</b> · 4 gens</span>'),
  ('title="编辑即自动保存（存于本浏览器），无需手动操作"><span class="dot"></span>已保存</button>',
   'title="Edits are saved automatically in this browser — no action needed"><span class="dot"></span>Saved</button>'),
  ('title="帮助 / 快捷键"', 'title="Help / shortcuts"'),
  # ---- 档案弹窗 ----
  ('<h3 id="__dmTitle">人员档案</h3>', '<h3 id="__dmTitle">Profile</h3>'),
  ('<label>姓名<input id="__dmName"></label>', '<label>Name<input id="__dmName"></label>'),
  ('<label>出生<input id="__dmBirth" placeholder="1951 或 1951-03-15（约1900 / 1920? 也行；卡片只显示年份）"></label>',
   '<label>Birth<input id="__dmBirth" placeholder="1951 or 1951-03-15 (c.1900 also fine; card shows year only)"></label>'),
  ('<label>卒年<input id="__dmDeath" placeholder="1985 或 1985-07-02（在世留空）"></label>',
   '<label>Death<input id="__dmDeath" placeholder="1985 or 1985-07-02 (leave empty if living)"></label>'),
  ('<label>性别<select id="__dmGender"><option value="">男</option><option value="f">女</option></select></label>',
   '<label>Sex<select id="__dmGender"><option value="">Male</option><option value="f">Female</option></select></label>'),
  ('<label>过继<select id="__dmHeir"><option value="">无</option><option value="in">嗣子（入继此支）</option><option value="out">嗣出（出继他支）</option><option value="jian">兼祧（一子继两房）</option></select></label>',
   '<label>Adoption<select id="__dmHeir"><option value="">None</option><option value="in">Heir (adopted into this branch)</option><option value="out">Adopted out (to another branch)</option><option value="jian">Heir to two branches (dual)</option></select></label>'),
  ('<label>字<input id="__dmZi" placeholder="谱书常记，如 昭子"></label>', '<label>Zi (courtesy name)<input id="__dmZi" placeholder="as in the book, e.g. Zhaozi"></label>'),
  ('<label>号<input id="__dmHao" placeholder="可选"></label>', '<label>Hao (art name)<input id="__dmHao" placeholder="optional"></label>'),
  ('止（无传 —— 谱书凡例：无传者以黑圈标止）', 'No issue (d.s.p. — genealogical rule: marked with a black circle)'),
  ('<label>备注<textarea id="__dmNote" rows="3" placeholder="官职 / 迁徙 / 过继 / 生平注记……"></textarea></label>',
   '<label>Notes<textarea id="__dmNote" rows="3" placeholder="office / migration / adoption / life notes..."></textarea></label>'),
  ('<button class="primary" id="__dmSave">保存</button>', '<button class="primary" id="__dmSave">Save</button>'),
  ('<button class="primary" id="__setSave">保存</button>', '<button class="primary" id="__setSave">Save</button>'),
  ('>取消</button>', '>Cancel</button>', 3),
  # ---- 初始 toast ----
  ('>已自动保存在本浏览器，编辑即保存</div>', '>Saved automatically in this browser as you edit</div>'),
  # ---- 帮助弹窗 ----
  ('<h3>使用帮助</h3>', '<h3>Help</h3>'),
  ('<h4>数据是怎么保存的</h4>', '<h4>How your data is saved</h4>'),
  ('<b>保存是无感的</b>：所有修改即时自动保存在本浏览器（和 Gmail 草稿一样），没有保存按钮、没有弹窗、不需要任何操作。顶栏绿灯「已保存」常亮即安心。',
   '<b>Saving is automatic</b>: every change is saved to this browser instantly (like Gmail drafts) — no save button, no dialogs, nothing to do. The green “Saved” light in the top bar means you are safe.'),
  ('数据存在<b>这台电脑的这个浏览器</b>里。两件事需要记得：<b>换电脑/换浏览器</b>时先「文件 ▾ → 备份到文件」下载 json，到新机器「恢复备份」；<b>清理浏览器数据</b>前也先备份。旧版 html 里若有数据，「恢复备份」可直接读出。',
   'Data lives in <b>this browser on this computer</b>. Two things to remember: when <b>switching computers/browsers</b>, first use “File ▾ → Backup to file” to download the json and “Restore backup” on the new machine; also back up <b>before clearing browser data</b>. Data inside an old html export can be read directly via “Restore backup”.'),
  ('<h4>编辑</h4>', '<h4>Editing</h4>'),
  ('<tbody><tr><td><kbd>＋</kbd> 节点下方常驻按钮 / 右键节点</td><td>打开该成员的操作菜单</td></tr>',
   '<tbody><tr><td><kbd>＋</kbd> button under a node / right-click</td><td>Open the member’s action menu</td></tr>'),
  ('<tr><td><kbd>双击</kbd> 姓名</td><td>行内改名</td></tr>', '<tr><td><kbd>Double-click</kbd> a name</td><td>Rename in place</td></tr>'),
  ('<tr><td><kbd>双击</kbd> 姓名下方小字行</td><td>编辑生卒年与备注（档案）</td></tr>', '<tr><td><kbd>Double-click</kbd> the small line under a name</td><td>Edit dates & notes (profile)</td></tr>'),
  ('<tr><td><kbd>双击</kbd> 配偶名</td><td>改名；清空并确定 = 移除</td></tr>', '<tr><td><kbd>Double-click</kbd> a spouse name</td><td>Rename; clear + OK = remove</td></tr>'),
  ('<tr><td><kbd>Tab</kbd> / <kbd>Enter</kbd></td><td>为选中者加子女 / 加同辈</td></tr>', '<tr><td><kbd>Tab</kbd> / <kbd>Enter</kbd></td><td>Add child / sibling to selection</td></tr>'),
  ('<tr><td><kbd>Ctrl+Shift+S</kbd></td><td>加配偶（可多次，支持元配/继室）</td></tr>', '<tr><td><kbd>Ctrl+Shift+S</kbd></td><td>Add spouse (repeatable, supports multiple marriages)</td></tr>'),
  ('<tr><td><kbd>Ctrl+I</kbd> / <kbd>F2</kbd></td><td>档案 / 改名</td></tr>', '<tr><td><kbd>Ctrl+I</kbd> / <kbd>F2</kbd></td><td>Profile / rename</td></tr>'),
  ('<tr><td><kbd>Delete</kbd></td><td>删除（含后代，可撤销）</td></tr>', '<tr><td><kbd>Delete</kbd></td><td>Delete (with descendants, undoable)</td></tr>'),
  ('<tr><td>按住节点左右拖</td><td>调长幼次序（最左为长）</td></tr>', '<tr><td>Drag a node left/right</td><td>Reorder siblings (eldest on the left)</td></tr>'),
  ('<tr><td>按住拖到某卡片上停一下</td><td>过继：TA（连同后代整支）成为此人子女，Ctrl+Z 可撤销</td></tr>',
   '<tr><td>Drag onto a card and pause</td><td>Adopt: that person (with all descendants) becomes this member’s child; Ctrl+Z undoes</td></tr>'),
  ('<h4>视图与数据</h4>', '<h4>View & data</h4>'),
  ('<tbody><tr><td><kbd>Ctrl+滚轮</kbd></td><td>以光标为中心缩放</td></tr>', '<tbody><tr><td><kbd>Ctrl+scroll</kbd></td><td>Zoom around the cursor</td></tr>'),
  ('<tr><td>滚轮 / 触控板 / 拖空白</td><td>平移画布</td></tr>', '<tr><td>Scroll / trackpad / drag empty space</td><td>Pan the canvas</td></tr>'),
  ('<tr><td><kbd>Ctrl+F</kbd></td><td>搜索（姓名/配偶/年份/备注），Enter 循环跳转</td></tr>', '<tr><td><kbd>Ctrl+F</kbd></td><td>Search (names/spouses/years/notes), Enter cycles hits</td></tr>'),
  ('<tr><td><kbd>Ctrl+Z</kbd> / <kbd>Ctrl+Y</kbd></td><td>撤销 / 重做</td></tr>', '<tr><td><kbd>Ctrl+Z</kbd> / <kbd>Ctrl+Y</kbd></td><td>Undo / redo</td></tr>'),
  ('<tr><td><kbd>Ctrl+S</kbd></td><td>已自动保存（拦截浏览器另存，无需手动操作）</td></tr>', '<tr><td><kbd>Ctrl+S</kbd></td><td>Already auto-saved (browser save dialog is intercepted)</td></tr>'),
  ('<tr><td>蓝色角标 / 橙色角标</td><td>出生年（自动排长幼）/ 排行称谓（手动排序）</td></tr>', '<tr><td>Blue badge / orange badge</td><td>Birth year (auto order) / birth-order word (manual order)</td></tr>'),
  ('<tr><td>视图 ▾ 谱书竖排（古法）</td><td>世代成行、名字竖书（右→左）、行左标世数；导出图同款排版</td></tr>',
   '<tr><td>View ▾ Vertical book layout</td><td>Generations as rows, names written top-to-bottom (right to left), generation labels on the left; same layout in exports</td></tr>'),
  ('<tr><td>视图 ▾ 谱书显示设置</td><td>世代基准（对齐谱书世数，如勤=23世填13）/ 配偶谱式（丁嘉→丁氏嘉）/ 姓氏周开关 / 世数用汉字</td></tr>',
   '<tr><td>View ▾ Book display settings</td><td>Generation base (align with the book’s numbering) / spouse book style / surname visibility / number style</td></tr>'),
  ('<tr><td><kbd>▸ N</kbd></td><td>此支已折叠 N 位后代，点击展开</td></tr>', '<tr><td><kbd>▸ N</kbd></td><td>Branch collapsed with N descendants; click to expand</td></tr>'),
  ('<h4 id="__zbTitle">字辈表（蓝框 = 族谱中已出现）</h4>', '<h4 id="__zbTitle">Zibei table (blue = the char appears in the tree)</h4>'),
  ('>知道了</button>', '>Got it</button>'),
  # ---- 显示设置弹窗 ----
  ('<h3>谱书显示设置</h3>', '<h3>Book display settings</h3>'),
  ('<label>世代基准 —— 字辈第 1 字对应的谱书世数<input id="__cfgBase" type="number" min="1" max="99" step="1"></label>',
   '<label>Generation base — the book generation number of zibei char #1<input id="__cfgBase" type="number" min="1" max="99" step="1"></label>'),
  ('传统谱书的「世」从<b>始祖一世</b>起算，而字辈往往是后世才议定的。你家谱书「勤」字辈记为<b>廿三世</b>，「勤」是字辈第 11 字，所以「多」字辈=第 <b>13</b> 世：这里填 <b>13</b>，卡片即显示「23世·勤」；填 1 则按应用自算显示「11代」。只改显示，不影响数据。',
   'In traditional genealogy books the generation count starts at <b>1 = the founding ancestor</b>, while the zibei (generation-char) list was often agreed later. Example: if your book records zibei char #11 as <b>generation 23</b>, enter <b>13</b> here (= 23 − 11 + 1) and every card shows book generations; enter 1 to use app-computed counting. Display only — data is never changed.'),
  ('<label class="checkline"><input type="checkbox" id="__cfgSpouse"> 配偶按谱书式显示（丁嘉 → 丁氏嘉；数据仍存原名，搜索不受影响）</label>',
   '<label class="checkline"><input type="checkbox" id="__cfgSpouse"> Spouse names in book style (CJK names only; data keeps the original, search unaffected)</label>'),
  ('<label class="checkline"><input type="checkbox" id="__cfgSurname"> 姓名显示姓氏「<span id="__cfgSurName">—</span>」（关闭 = 按谱书习惯只报名；仅显示层，姓氏随数据自动识别）</label>',
   '<label class="checkline"><input type="checkbox" id="__cfgSurname"> Show the surname “<span id="__cfgSurName">—</span>” in names (off = given names only, as genealogy books often do; display only — the surname is auto-detected from the data)</label>'),
  ('<label class="checkline"><input type="checkbox" id="__cfgCn"> 世数用汉字（廿三世·勤；关闭显示 23世·勤）</label>', ''),
  # ---- 谱序弹窗 ----
  ('<h3>谱序 · 宗族源流</h3>', '<h3>Pedigree preface · clan origin</h3>'),
  ('<label>谱名<input id="__clMing" placeholder="如 潮阳泗水周氏族谱"></label>', '<label>Pedigree name<input id="__clMing" placeholder="e.g. Miller Family Genealogy"></label>'),
  ('<label>堂号<input id="__clTang" placeholder="可选，如 四知堂 / 陇西堂"></label>', '<label>Hall name<input id="__clTang" placeholder="optional, e.g. “Hall of Four Knows”"></label>'),
  ('<label>源流世系（远祖 → 近祖，用 — 相连）<input id="__clChain" placeholder="始祖 — 二世 — 三世……"></label>',
   '<label>Lineage (remote → recent ancestors, joined with —)<input id="__clChain" placeholder="Founder — 2nd gen — 3rd gen..."></label>'),
  ('<label>字辈表（空格 / 逗号 / 顿号分隔，按世代顺序；用于自动定代）<textarea id="__clZibei" rows="2" placeholder="如：德 承 传 世 泽 诗 礼 继 家 声"></textarea></label>',
   '<label>Zibei table (generation chars, space/comma separated, in generation order; drives automatic generation numbering)<textarea id="__clZibei" rows="2" placeholder="e.g. Arthur James Robert Michael"></textarea></label>'),
  ('<label>先祖<input id="__clYuan" placeholder="如 周敦颐，字茂叔，号濂溪（湖南道州）"></label>', '<label>Forebears<input id="__clYuan" placeholder="e.g. John Miller (b. 1820, Yorkshire)"></label>'),
  ('<label>始祖记<textarea id="__clShi" rows="3" placeholder="一世祖承节公讳宣道……二世祖朝奉公讳景一……"></textarea></label>',
   '<label>Founder record<textarea id="__clShi" rows="3" placeholder="1st gen: ...  2nd gen: ..."></textarea></label>'),
  ('<label>始迁祖<input id="__clQian" placeholder="如 （南宋）宣，字承节"></label>', '<label>Migrating ancestor<input id="__clQian" placeholder="e.g. (1890s) John Miller, who moved to Ohio"></label>'),
  ('<label>家族来源<textarea id="__clOrigin" rows="5" placeholder="宗支源流叙述……"></textarea></label>', '<label>Family origin<textarea id="__clOrigin" rows="5" placeholder="The story of this family branch..."></textarea></label>'),
  ('<button class="primary" id="__clSave">保存</button>', '<button class="primary" id="__clSave">Save</button>'),
  # ---- 向导 ----
  ('<h3>欢迎使用家族族谱</h3>', '<h3>Welcome</h3>'),
  ('这是一个<b>本地优先</b>的单文件应用：数据只存在<b>你的浏览器</b>里，不联网、无账号、编辑即自动保存。',
   'This is a <b>local-first</b> single-file app: data stays in <b>your browser</b> — no network, no account, edits save automatically.'),
  ('当前载入的是示例数据（赵钱孙李演示谱），三选一：', 'Demo data is loaded. Pick one to start:'),
  ('<button type="button" data-wiz="demo"><b>先看看示例</b>赵钱孙李演示谱，可随意折腾</button>',
   '<button type="button" data-wiz="demo"><b>Explore the demo</b>A sample family tree you can play with freely</button>'),
  ('<button type="button" data-wiz="import"><b>导入备份</b>恢复你自己的 json 数据</button>',
   '<button type="button" data-wiz="import"><b>Import a backup</b>Restore your own json data</button>'),
  ('<label>谱名（从空白开始时使用）<input id="__wizMing" placeholder="如 赵氏族谱 / 李氏家谱"></label>',
   '<label>Pedigree name (used when starting from scratch)<input id="__wizMing" placeholder="e.g. Miller Family Tree"></label>'),
  ('<label>堂号（可选）<input id="__wizTang" placeholder="如 四知堂"></label>', '<label>Hall name (optional)<input id="__wizTang" placeholder="optional"></label>'),
  ('<button class="primary" id="__wizGo">从空白开始</button>', '<button class="primary" id="__wizGo">Start from scratch</button>'),
  # ---- 搜索 / 提示条 / 图例 ----
  ('placeholder="搜姓名/配偶/备注…"', 'placeholder="Search names / spouses / notes…"'),
  ('title="上一个（Shift+Enter）"', 'title="Previous (Shift+Enter)"'),
  ('title="下一个（Enter）"', 'title="Next (Enter)"'),
  ('title="关闭（Esc）"', 'title="Close (Esc)"'),
  ('title="节点下方常驻「＋」或右键=操作菜单 · 双击姓名=改名 · 双击备注行=档案 · 按住拖=调次序，拖到卡片上停一下=过继 · Ctrl+滚轮=缩放 · 滚轮/拖空白=平移 · 编辑自动保存 · 详细说明见「?」帮助">操作：<b>＋/右键</b>=菜单 · <b>双击</b>=改名/档案 · <b>拖</b>=调次序或过继 · <b>Ctrl+滚轮</b>=缩放 · 滚轮/拖空白=平移 · 自动保存 · 更多见「?」帮助',
   'title="The “＋” under a node or right-click = action menu · double-click name = rename · double-click meta line = profile · drag = reorder or adopt · Ctrl+scroll = zoom · scroll/drag empty space = pan · auto-save · see “?” for help">Edit: <b>＋/right-click</b>=menu · <b>double-click</b>=rename/profile · <b>drag</b>=reorder or adopt · <b>Ctrl+scroll</b>=zoom · scroll/drag=pan · auto-save · more under “?”'),
  ('</i>总根</span>', '</i>Root</span>'),
  ('</i>第一代</span>', '</i>1st generation</span>'),
  ('</i>第二代</span>', '</i>2nd generation</span>'),
  ('</i>第三代</span>', '</i>3rd generation</span>'),
  ('</i>第四代</span>', '</i>4th generation</span>'),
  ('</i>第五代及以后</span>', '</i>5th generation and beyond</span>'),
  ('</i>待核对备注</span>', '</i>Unverified note</span>'),
  ('<b style="color:var(--birth-bg)">蓝色角标</b>=出生年（自动排）', '<b style="color:var(--birth-bg)">Blue badge</b>=birth year (auto order)'),
  ('<b style="color:var(--rank-bg)">橙色角标</b>=排行称谓（最左为长）', '<b style="color:var(--rank-bg)">Orange badge</b>=birth-order word (eldest left)'),
  ('<b style="color:var(--accent)">▸ N</b>=已折叠 N 位后代（点它展开）', '<b style="color:var(--accent)">▸ N</b>=N descendants collapsed (click to expand)'),
  ('<b style="color:#b04a72">女</b>=女性成员（男不标，谱书惯例）', '<b style="color:#b04a72">♀</b>=female member (males unmarked, per book convention)'),
  # ---- JS：称谓 / 字辈语法 ----
  ("return ['原配', '续弦', '三房', '四房', '五房', '六房', '七房', '八房'][i] || '第' + (i + 1) + '房';",
   "return ['first spouse', 'second spouse', 'third spouse', '4th spouse', '5th spouse', '6th spouse', '7th spouse', '8th spouse'][i] || 'Spouse #' + (i + 1);"),
  ("const SP_TERMS = ['配', '继配', '娶', '聘', '侧室'];", "const SP_TERMS = ['m.', '2nd m.', 'm.', 'betrothed', 'concubine'];"),
  ("function spouseBookRole(i){\n  return ['配', '继配', '三配', '四配', '五配', '六配', '七配', '八配'][i] || '第' + (i + 1) + '配';\n}",
   "function spouseBookRole(i){\n  return ['m.', '2nd m.', '3rd m.', '4th m.', '5th m.', '6th m.', '7th m.', '8th m.'][i] || 'm. #' + (i + 1);\n}"),
  ("let s = dispName(n.name) + (n.gender === 'f' ? '（女）' : '');\n  if (n.zi) s += '，字' + n.zi;\n  if (n.hao) s += '，号' + n.hao;\n  if (n.heir === 'in') s += '，嗣子';\n  if (n.heir === 'out') s += '，嗣出';\n  if (n.heir === 'jian') s += '，兼祧';\n  if (n.zhi) s += '，止';",
   "let s = dispName(n.name) + (n.gender === 'f' ? ' (f)' : '');\n  if (n.zi) s += ', zi ' + n.zi;\n  if (n.hao) s += ', hao ' + n.hao;\n  if (n.heir === 'in') s += ', heir';\n  if (n.heir === 'out') s += ', adopted out';\n  if (n.heir === 'jian') s += ', dual heir';\n  if (n.zhi) s += ', dsp';"),
  ("else if (b) parts.push(b + ' 生');", "else if (b) parts.push('b. ' + b);"),
  ("else if (d) parts.push('卒 ' + d);", "else if (d) parts.push('d. ' + d);"),
  ("return seg ? '生卒：' + seg : '';", "return seg ? 'Dates: ' + seg : '';"),
  ("return n.heir === 'in' ? '嗣子：过继来继承此支（谱书式「过继TA为子」）'\n       : n.heir === 'out' ? '嗣出：过继给他人为子（谱书式「TA过继某某为子」）'\n       : n.heir === 'jian' ? '兼祧（兼嗣）：一子兼继两房' : '';",
   "return n.heir === 'in' ? 'Heir: adopted in to continue this branch'\n       : n.heir === 'out' ? 'Adopted out: became the heir of another branch'\n       : n.heir === 'jian' ? 'Dual heir: one son continues two branches' : '';"),
  ("function genUnit(){ return genOffset() ? '世' : '代'; }", "function genUnit(){ return 'gens'; }"),
  ("const CN_D = ['零','一','二','三','四','五','六','七','八','九'];\nfunction numToCn(n){\n  n = Math.round(n);\n  if (n < 10) return CN_D[n];\n  if (n === 10) return '十';\n  if (n < 20) return '十' + CN_D[n % 10];\n  if (n < 50){\n    const t = ['','','廿','卅','卌'][Math.floor(n / 10)];\n    return t + (n % 10 ? CN_D[n % 10] : '');\n  }\n  return CN_D[Math.floor(n / 10)] + '十' + (n % 10 ? CN_D[n % 10] : '');\n}",
   "function numToCn(n){ return String(Math.round(n)); }"),
  ("function genLabel(g){ const v = g + genOffset(); return (cfg.cnNum ? numToCn(v) : v) + genUnit(); }",
   "function genLabel(g){ return 'Gen ' + (g + genOffset()); }"),
  ("const RANK_WORDS = ['长','次','三','四','五','六','七','八','九','十','十一','十二','十三','十四','十五'];",
   "const RANK_WORDS = ['1st','2nd','3rd','4th','5th','6th','7th','8th','9th','10th','11th','12th','13th','14th','15th'];"),
  ("migrate({ id:'root', name:'家族族谱', spouses:[], expanded:true, children:[] })",
   "migrate({ id:'root', name:'Family Tree', spouses:[], expanded:true, children:[] })"),
  # ---- JS：世代 tooltip ----
  ("const unused = ziOfGen ? '（本人名字未用本代字辈「' + ziOfGen + '」）' : '（名字未用字辈）';",
   "const unused = ziOfGen ? ' (this name does not use this generation’s zibei char “' + ziOfGen + '”)' : ' (name does not use a zibei char)';"),
  ("const base = genOffset() ? '（谱书世数，应用自算第' + g.gen + '代）' : '';",
   "const base = genOffset() ? ' (book generations; app-computed: Gen ' + g.gen + ')' : '';"),
  ("return '字辈「' + g.zi + '」= ' + genLabel(g.gen) + base",
   "return 'Zibei char “' + g.zi + '” = ' + genLabel(g.gen) + base"),
  ("+ (g.conflict ? '（注意：按父辈推算应为' + genLabel(g.conflict) + '，树中可能缺一代）' : '');",
   "+ (g.conflict ? ' (note: parent-based inference gives ' + genLabel(g.conflict) + ' — a generation may be missing in the tree)' : '');"),
  ("case 'parent':  return '由父/母「' + (p ? dispName(p.name) : '') + '」推算：' + genLabel(g.gen) + base + unused;",
   "case 'parent':  return 'Inferred from parent “' + (p ? dispName(p.name) : '') + '”: ' + genLabel(g.gen) + base + unused;"),
  ("case 'sibling': return '与「' + dispName(g.via || '') + '」同辈推算：' + genLabel(g.gen) + base + unused;",
   "case 'sibling': return 'Inferred as sibling of “' + dispName(g.via || '') + '”: ' + genLabel(g.gen) + base + unused;"),
  ("default:        return '按世系推算：' + genLabel(g.gen) + base + unused;",
   "default:        return 'Inferred by lineage depth: ' + genLabel(g.gen) + base + unused;"),
  # ---- JS：撤销/重做 ----
  ("toast('没有可撤销的操作');", "toast('Nothing to undo');"),
  ("toast('已撤销');", "toast('Undone');"),
  ("toast('没有可重做的操作');", "toast('Nothing to redo');"),
  ("toast('已重做');", "toast('Redone');"),
  # ---- JS：卡片 ----
  ("rk.title = '出生年 ' + yr + '：同辈按出生年自动排序，年长在左';",
   "rk.title = 'Birth year ' + yr + ': siblings auto-sorted by birth year, eldest left';"),
  ("rk.title = '同辈第 ' + (orderIdx + 1) + ' 位（最左为长）。补填出生年即可自动排序';",
   "rk.title = 'Sibling #' + (orderIdx + 1) + ' (eldest left). Fill in birth years to auto-sort';"),
  ("'<span class=\"gx\" title=\"女性成员\">女</span>'", "'<span class=\"gx\" title=\"Female member\">♀</span>'"),
  ("'\">嗣</span>'", "'\">ad</span>'"),
  ("'<span class=\"zhi\" title=\"止：谱书凡例，无传者以黑圈标止\">止</span>'", "'<span class=\"zhi\" title=\"No issue (d.s.p.): black circle per genealogical rule\">dsp</span>'"),
  ("'<span class=\"xh\" title=\"字\">字' + esc(n.zi) + '</span>'", "'<span class=\"xh\" title=\"Zi (courtesy name)\">zi ' + esc(n.zi) + '</span>'"),
  ("'<span class=\"xh\" title=\"号\">号' + esc(n.hao) + '</span>'", "'<span class=\"xh\" title=\"Hao (art name)\">hao ' + esc(n.hao) + '</span>'"),
  ('title="双击：改名 / 清空移除"><i class="role">', 'title="Double-click: rename / clear to remove"><i class="role">'),
  ("'双击备注行可编辑生卒年与备注'", "'Double-click the meta line to edit dates & notes'"),
  ("pill.title = '点击折叠此支（共 ' + cnt + ' 位后代）';", "pill.title = 'Click to collapse this branch (' + cnt + ' descendants)';"),
  ("pill.title = '此支已折叠，共 ' + cnt + ' 位后代 —— 点击展开';", "pill.title = 'Branch collapsed — ' + cnt + ' descendants. Click to expand';"),
  ("qa.title = '打开操作菜单';", "qa.title = 'Open action menu';"),
  # ---- JS：竖排行标 ----
  ("el.textContent = numToCn(g + genOffset()) + genUnit() + (zi ? '·' + zi : '');",
   "el.textContent = 'Gen ' + (g + genOffset()) + (zi ? ' · ' + zi : '');"),
  ("el.title = '本行「' + el.textContent + '」';", "el.title = 'This row: ' + el.textContent;"),
  # ---- JS：统计条 / 保存灯 ----
  ("extra = ' · 字辈第<b>' + (cfg.cnNum ? numToCn(loV) + '–' + numToCn(hiV) : loV + '–' + hiV) + '</b>' + genUnit();",
   "extra = ' · zibei range <b>' + loV + '–' + hiV + '</b>';"),
  ("'<b>' + persons + '</b> 位成员 · 配偶 <b>' + sp + '</b> · ' + (cfg.cnNum ? numToCn(totV) : totV) + ' ' + genUnit() + extra;",
   "'<b>' + persons + '</b> members · spouses <b>' + sp + '</b> · ' + totV + ' ' + genUnit() + extra;"),
  ("el.innerHTML = '<span class=\"dot\"></span>未能保存';", "el.innerHTML = '<span class=\"dot\"></span>Not saved';"),
  ("el.title = '此浏览器环境不允许写入本地存储（如无痕模式/配额已满）——'\n             + '本次修改不会被记住，请立即用「文件 ▾ → 备份到文件」导出 json！';",
   "el.title = 'This browser cannot write local storage (private mode / quota full) — '\n             + 'changes will be lost. Export a json backup now via “File ▾ → Backup to file”!';"),
  ("el.innerHTML = '<span class=\"dot\"></span>已保存';", "el.innerHTML = '<span class=\"dot\"></span>Saved';"),
  ("el.title = '所有修改都已自动保存在此浏览器 · 备份/换电脑见「文件 ▾」菜单';",
   "el.title = 'All changes are auto-saved in this browser · backup & migration under the “File ▾” menu';"),
  # ---- JS：档案 ----
  ("const t = prompt('修改姓名：', n.name);", "const t = prompt('Rename:', n.name);"),
  ("'人员档案 · '", "'Profile · '"),
  ("'<option value=\"\">（默认）</option>'", "'<option value=\"\">(default)</option>'"),
  ("row.innerHTML = '<label>配偶 ' + (i + 1) + ' · ' + esc(spName) + ' 称谓<select data-i=\"' + i + '\">' + opts + '</select></label>';",
   "row.innerHTML = '<label>Spouse ' + (i + 1) + ' · ' + esc(spName) + ' term<select data-i=\"' + i + '\">' + opts + '</select></label>';"),
  ("toast('已保存，并按出生年自动重排「' + n.name + '」同辈的长幼（年长在左）');",
   "toast('Saved; siblings of ' + n.name + ' re-sorted by birth year (eldest left)');"),
  ("toast('已保存「' + n.name + '」的档案');", "toast('Saved the profile of ' + n.name);"),
  ("toast('已保存「' + n.name + '」的档案（未填出生年，长幼按手动排列）');",
   "toast('Saved the profile of ' + n.name + ' (no birth year — siblings keep manual order)');"),
  # ---- JS：菜单 ----
  ("ctxMenu.appendChild(mi('＋ 第一代', '', '', () => addChild(n)));", "ctxMenu.appendChild(mi('＋ First generation', '', '', () => addChild(n)));"),
  ("ctxMenu.appendChild(mi('＋ 配偶', '', 'Ctrl+Shift+S', () => addSpouse(n)));", "ctxMenu.appendChild(mi('＋ Spouse', '', 'Ctrl+Shift+S', () => addSpouse(n)));"),
  ("ctxMenu.appendChild(mi('＋ 子女', '', 'Tab', () => addChild(n)));", "ctxMenu.appendChild(mi('＋ Child', '', 'Tab', () => addChild(n)));"),
  ("ctxMenu.appendChild(mi('＋ 同辈', '', 'Enter', () => addSibling(n)));", "ctxMenu.appendChild(mi('＋ Sibling', '', 'Enter', () => addSibling(n)));"),
  ("ic('pencil') + '改名'", "ic('pencil') + 'Rename'"),
  ("ic('card') + '档案'", "ic('card') + 'Profile'"),
  ("mi(n.expanded ? ic('fold') + '折叠此支' : ic('unfold') + '展开此支'", "mi(n.expanded ? ic('fold') + 'Collapse branch' : ic('unfold') + 'Expand branch'"),
  ("ic('trash') + '删除'", "ic('trash') + 'Delete'"),
  ("mi(ic('unfold') + '全展开'", "mi(ic('unfold') + 'Expand all'"),
  ("mi(ic('fold') + '全折叠'", "mi(ic('fold') + 'Collapse all'"),
  ("mi((cfg.vertical ? '✓ ' : '') + ic('filetext') + '谱书竖排（古法）'", "mi((cfg.vertical ? '✓ ' : '') + ic('filetext') + 'Vertical book layout'"),
  ("mi(ic('card') + '谱序（堂号·源流）…'", "mi(ic('card') + 'Pedigree preface (hall · origin)…'"),
  ("mi(ic('gear') + '谱书显示设置…'", "mi(ic('gear') + 'Book display settings…'"),
  ("mi(ic('download') + '备份到文件（json）'", "mi(ic('download') + 'Backup to file (json)'"),
  ("mi(ic('folder') + '恢复备份（json / 旧版 html）'", "mi(ic('folder') + 'Restore backup (json / old html)'"),
  ("mi(ic('image') + '导出图片（png）'", "mi(ic('image') + 'Export image (png)'"),
  ("mi(ic('pdf') + '导出 PDF（图谱）'", "mi(ic('pdf') + 'Export PDF (chart)'"),
  ("mi(ic('filetext') + '世系录（五世一表）'", "mi(ic('filetext') + 'Genealogy tables (5 gens each)'"),
  ("mi(ic('filetext') + '导出 MD'", "mi(ic('filetext') + 'Export Markdown'"),
  ("mi(ic('print') + '打印（纸质）'", "mi(ic('print') + 'Print (paper)'"),
  ("mi(ic('sort') + '按生年重排'", "mi(ic('sort') + 'Sort by birth year'"),
  ("mi(ic('reset') + '重置数据'", "mi(ic('reset') + 'Reset data'"),
  # ---- JS：字辈角标 ----
  ("'字辈表（第' + range + genUnit() + '，蓝框 = 族谱中已出现）';", "'Zibei table (gens ' + range + '; blue = appears in tree)';"),
  ("d.innerHTML = esc(z || '·') + '<small>第' + genLabel(i + 1) + '</small>';",
   "d.innerHTML = esc(z || '·') + '<small>' + genLabel(i + 1) + '</small>';"),
  ("d.title = '第' + genLabel(i + 1) + '字辈「' + (z || '?') + '」' + (all.includes(z) ? '（族谱中已出现）' : '');",
   "d.title = genLabel(i + 1) + ' zibei char: “' + (z || '?') + '”' + (all.includes(z) ? ' (appears in tree)' : '');"),
  ("'<span class=\"help-note\">本文件尚未配置字辈表</span>'", "'<span class=\"help-note\">No zibei table configured in this file</span>'"),
  ("FAM_SUR || '（自动识别）'", "FAM_SUR || '(auto-detected)'"),
  # ---- JS：设置/视图 toast ----
  ("toast('显示设置已保存：' + (cfg.genBase > 1 ? '字辈第 1 字 = 第 ' + cfg.genBase + ' 世' : '按应用自算代数')\n    + ' · 配偶' + (cfg.bookSpouse ? '谱书式' : '原名')\n    + ' · ' + (cfg.showSurname ? '显示姓氏' : '只报名')\n    + ' · 世数' + (cfg.cnNum ? '用汉字' : '用数字'));",
   "toast('Display settings saved: ' + (cfg.genBase > 1 ? 'zibei char #1 = book generation ' + cfg.genBase : 'app-computed generations')\n    + ' · spouses ' + (cfg.bookSpouse ? 'book style' : 'as entered')\n    + ' · ' + (cfg.showSurname ? 'surnames shown' : 'surnames omitted'));"),
  ("toast(cfg.vertical ? '已切换谱书竖排（古法）：世代成行、名字竖书、行左标世数' : '已切回常规视图');",
   "toast(cfg.vertical ? 'Switched to the vertical book layout: generations as rows, names written vertically, generation labels on the left' : 'Switched back to the regular view');"),
  # ---- JS：谱序 ----
  ("return (c.ming || '家族族谱') + (c.tang ? '（' + c.tang + '）' : '');", "return (c.ming || 'Family Tree') + (c.tang ? ' (' + c.tang + ')' : '');"),
  ("document.getElementById('__puName').textContent = c.ming || '家族族谱';", "document.getElementById('__puName').textContent = c.ming || 'Family Tree';"),
  ("document.title = (c.ming || '家族族谱') + (c.tang ? ' · ' + c.tang : '');", "document.title = (c.ming || 'Family Tree') + (c.tang ? ' · ' + c.tang : '');"),
  ("toast('谱序已保存：谱名、堂号将随导出与打印一起出现');", "toast('Pedigree preface saved: the tree name and hall name will appear in exports and prints');"),
  # ---- JS：向导 ----
  ("toast('示例数据：双击名字改名、点「＋」添加成员，所有操作都可撤销');", "toast('Demo data: double-click a name to rename, click “＋” to add members — everything is undoable');"),
  ("document.getElementById('__wizMing').value.trim() || '我的家族';", "document.getElementById('__wizMing').value.trim() || 'My Family';"),
  ("toast('空白族谱「' + ming + '」已创建：点第一个「＋」添加第一代成员');", "toast('Blank tree “' + ming + '” created: click the first “＋” to add the first generation');"),
  # ---- JS：配偶/子女/同辈/删除 ----
  ("const t = prompt('为「' + n.name + '」添加第 ' + nth + ' 位配偶姓名：\\n（如需改名/移除某位配偶，直接双击图上该配偶的名字）');",
   "const t = prompt('Add spouse #' + nth + ' for ' + n.name + ':\\n(to rename/remove a spouse later, double-click the spouse name on the card)');"),
  ("toast('「' + v + '」已是 ' + n.name + ' 的配偶，无需重复添加');", "toast(v + ' is already a spouse of ' + n.name);"),
  ("toast('已为 ' + n.name + ' 添加配偶「' + v + '」，继续点「＋配偶」可再加');", "toast('Added spouse ' + v + ' for ' + n.name + ' — click “＋ Spouse” again to add more');"),
  ("const t = prompt('修改「' + n.name + '」的第 ' + (i + 1) + ' 位配偶：\\n（清空并确定 = 移除这位配偶）', cur);",
   "const t = prompt('Edit spouse #' + (i + 1) + ' of ' + n.name + ':\\n(clear and OK = remove this spouse)', cur);"),
  ("if (confirm('确定移除配偶「' + cur + '」？')){", "if (confirm('Remove spouse “' + cur + '”?')){"),
  ("? '在「家族族谱」下添加一位第一代成员（新祖辈分支）：'", "? 'Add a first-generation member under “Family Tree” (a new ancestral branch):'"),
  (": '为「' + displayName(n) + '」添加子女姓名：'", ": 'Add a child to “' + displayName(n) + '”: '"),
  ("? '已添加第一代成员「' + t.trim() + '」（默认排最右=最幼，按住拖动可调长幼）'",
   "? 'Added first-generation member “' + t.trim() + '” (placed rightmost = youngest; drag to reorder)'"),
  (": '已为 ' + n.name + ' 添加子女「' + t.trim() + '」');", ": 'Added child “' + t.trim() + '” to ' + n.name);"),
  ("if (n.id === 'root'){ toast('根节点不能删'); return; }", "if (n.id === 'root'){ toast('The root node cannot be deleted'); return; }"),
  ("? '删除「' + displayName(n) + '」及其全部 ' + desc + ' 位后代？'", "? 'Delete “' + displayName(n) + '” and all ' + desc + ' descendants?'"),
  (": '删除「' + displayName(n) + '」？';", ": 'Delete “' + displayName(n) + '”?';"),
  ("toast('已删除（可用 Ctrl+Z 撤销）');", "toast('Deleted (Ctrl+Z to undo)');"),
  ("const t = prompt('添加一位与「' + n.name + '」同辈的成员（' + (p.id === 'root' ? '第一代' : '同父母') + '）：');",
   "const t = prompt('Add a sibling of “' + n.name + '” (' + (p.id === 'root' ? 'first generation' : 'same parents') + '):');"),
  ("toast('已添加「' + t.trim() + '」，默认排最右=最幼；按住拖到左边可成为更长');",
   "toast('Added “' + t.trim() + '” (placed rightmost = youngest; drag left to make elder)');"),
  # ---- JS：排序/过继/换位 ----
  ("? '已按出生年重排 ' + t + ' 组同辈（年长在左；无出生年的保持原次序排其后）'",
   "? 'Re-sorted ' + t + ' sibling groups by birth year (eldest left; those without a birth year keep their order at the end)'"),
  (": '暂无任何人填出生年，未做改动（先在「档案」里补出生年）');", ": 'No birth years filled yet — nothing changed (add birth years in profiles first)');"),
  ("? '「' + d.n.name + '」已移入第一代（可拖拽微调长幼）'", "? '“' + d.n.name + '” moved into the first generation (drag to fine-tune order)'"),
  (": '「' + d.n.name + '」已过继到「' + tp.name + '」名下（排最幼，可拖拽微调长幼；Ctrl+Z 可撤销）');",
   ": '“' + d.n.name + '” adopted into the family of “' + tp.name + '” (placed youngest; drag to fine-tune; Ctrl+Z undoes)');"),
  ("toast('已换位：' + me.name + ' 现在是同辈第 ' + (newIdx + 1) + ' 位（排行「' + rankWord(newIdx) + '」，最左为长）');",
   "toast('Swapped: ' + me.name + ' is now sibling #' + (newIdx + 1) + ' (' + rankWord(newIdx) + ', eldest left)');"),
  # ---- JS：搜索 ----
  ("else sbCount.textContent = '无匹配';", "else sbCount.textContent = 'No match';"),
  ("'<i class=\"gx\">女</i>'", "'<i class=\"gx\">♀</i>'"),
  # ---- JS：MD 导出 ----
  ("let line = dispName(n.name) + (n.gender === 'f' ? '（女）' : '');", "let line = dispName(n.name) + (n.gender === 'f' ? ' (f)' : '');"),
  ("if (n.zi) line += '（字' + n.zi + '）';", "if (n.zi) line += ' (zi ' + n.zi + ')';"),
  ("if (n.hao) line += '（号' + n.hao + '）';", "if (n.hao) line += ' (hao ' + n.hao + ')';"),
  ("if (n.heir === 'in') line += '（嗣子）';", "if (n.heir === 'in') line += ' (heir)';"),
  ("if (n.heir === 'out') line += '（嗣出）';", "if (n.heir === 'out') line += ' (adopted out)';"),
  ("if (n.heir === 'jian') line += '（兼祧）';", "if (n.heir === 'jian') line += ' (dual heir)';"),
  ("if (n.zhi) line += '（止）';", "if (n.zhi) line += ' (dsp)';"),
  ("download((clanOf().ming || '家族族谱') + '.md', s, 'text/markdown;charset=utf-8');", "download((clanOf().ming || 'Family Tree') + '.md', s, 'text/markdown;charset=utf-8');"),
  # ---- JS：世系录 ----
  ("kids: (n.children || []).map(c => dispName(c.name) + (c.gender === 'f' ? '（女）' : '')).join('、'),",
   "kids: (n.children || []).map(c => dispName(c.name) + (c.gender === 'f' ? ' (f)' : '')).join(', '),"),
  ("heir: n.heir === 'in' ? '嗣子' : n.heir === 'out' ? '嗣出' : n.heir === 'jian' ? '兼祧' : '',",
   "heir: n.heir === 'in' ? 'heir' : n.heir === 'out' ? 'adopted out' : n.heir === 'jian' ? 'dual heir' : '',"),
  ("zhi: n.zhi ? '止' : '',", "zhi: n.zhi ? 'dsp' : '',"),
  ('<!doctype html><html lang="zh">', '<!doctype html><html lang="en">'),
  ("esc(puTitle() + ' · 世系录')", "esc(puTitle() + ' · Genealogy Tables')"),
  ("html += '<h1>' + esc(puTitle()) + ' · 世系录</h1>';", "html += '<h1>' + esc(puTitle()) + ' · Genealogy Tables</h1>';"),
  ("'<div class=\"sub\">欧式 · 五世一表 · 导出于 ' + today + ' · 共 ' + rows.length + ' 人</div>'",
   "'<div class=\"sub\">European style · five generations per table · exported ' + today + ' · ' + rows.length + ' people</div>'"),
  ("if (c.chain)  html += '<div class=\"pre\"><b>源流世系：</b>' + esc(c.chain) + '</div>';", "if (c.chain)  html += '<div class=\"pre\"><b>Lineage:</b>' + esc(c.chain) + '</div>';"),
  ("if (c.yuanzu) html += '<div class=\"pre\"><b>先祖：</b>' + esc(c.yuanzu) + '</div>';", "if (c.yuanzu) html += '<div class=\"pre\"><b>Forebears:</b>' + esc(c.yuanzu) + '</div>';"),
  ("if (c.shizu)  html += '<div class=\"pre\"><b>始祖记：</b>' + esc(c.shizu) + '</div>';", "if (c.shizu)  html += '<div class=\"pre\"><b>Founder record:</b>' + esc(c.shizu) + '</div>';"),
  ("|| '始迁祖'", "|| 'Migrating ancestor'", 2),
  ("if (c.origin) html += '<div class=\"pre\"><b>家族来源：</b>' + esc(c.origin) + '</div>';", "if (c.origin) html += '<div class=\"pre\"><b>Family origin:</b>' + esc(c.origin) + '</div>';"),
  ("html += '<h2>未定世次</h2>';", "html += '<h2>Generation unplaced</h2>';"),
  ("html += '<h2>第' + numToCn(s0) + '世至第' + numToCn(s1) + '世</h2>';", "html += '<h2>Generations ' + numToCn(s0) + '–' + numToCn(s1) + '</h2>';"),
  ("'<table><tr><th>世次</th><th>讳</th><th>字</th><th>号</th><th>行第</th><th>生</th><th>卒</th><th>配偶</th><th>子女</th><th>记</th></tr>'",
   "'<table><tr><th>Gen</th><th>Name</th><th>Zi</th><th>Hao</th><th>Order</th><th>Born</th><th>Died</th><th>Spouse</th><th>Children</th><th>Notes</th></tr>'"),
  ("'<td class=\"c\">' + (r.gen ? numToCn(r.gen + genOffset()) + '世' + (r.zi ? '·' + r.zi : '') : '—') + '</td>'",
   "'<td class=\"c\">' + (r.gen ? 'Gen ' + numToCn(r.gen + genOffset()) + (r.zi ? ' · ' + r.zi : '') : '—') + '</td>'"),
  ("download((clanOf().ming || '家族族谱') + '-世系录-'", "download((clanOf().ming || 'Family Tree') + '-genealogy-'"),
  ("toast('世系录已下载（五世一表）：浏览器打开即可查阅或打印');", "toast('Genealogy tables downloaded (five generations per table): open in a browser to view or print');"),
  # ---- JS：导入/重置/备份 ----
  ("if (!m) throw new Error('这个 HTML 里没有族谱数据');", "if (!m) throw new Error('No genealogy data found in this HTML');"),
  ("if (!validTree(d)) throw new Error('结构不符：需要 {id,name,children[]} 树');", "if (!validTree(d)) throw new Error('Unexpected structure: need a {id,name,children[]} tree');"),
  ("toast('已导入「' + f.name + '」，数据已自动保存');", "toast('Imported “' + f.name + '” — data saved automatically');"),
  ("alert('导入失败：不是有效的族谱 JSON 文件\\n' + e.message);", "alert('Import failed: not a valid genealogy JSON file\\n' + e.message);"),
  ("if (!confirm('确定重置？当前族谱将被清空，恢复到本文件自带的初始数据。\\n（如需保留，先「备份到文件」；误删可用 Ctrl+Z）')) return;",
   "if (!confirm('Reset? The current tree will be cleared and restored to this file’s initial data.\\n(To keep it, “Backup to file” first; Ctrl+Z undoes an accidental reset)')) return;"),
  ("toast('已重置为本文件的初始数据（再次「保存到文件」可固化）');", "toast('Reset to this file’s initial data (use “Backup to file” to persist anything)');"),
  ("const fname = (clanOf().ming || '家族族谱') + '-备份-'", "const fname = (clanOf().ming || 'Family Tree') + '-backup-'"),
  ("toast('备份已下载：' + fname);", "toast('Backup downloaded: ' + fname);"),
  # ---- JS：画布 ----
  ("throw new Error('画布尚未渲染');", "throw new Error('Canvas not rendered yet');"),
  ("if (n.gender === 'f') seg('女', 11, '600', '#b04a72');", "if (n.gender === 'f') seg('♀', 11, '600', '#b04a72');"),
  ("if (n.heir) seg('嗣', 11, '700',", "if (n.heir) seg('ad', 11, '700',"),
  ("if (n.zhi) seg('止', 11, '700', '#3c4a57');", "if (n.zhi) seg('dsp', 11, '700', '#3c4a57');"),
  ("if (n.zi) seg('字' + n.zi, 11, '400', '#9aa9bb');", "if (n.zi) seg('zi ' + n.zi, 11, '400', '#9aa9bb');"),
  ("if (n.hao) seg('号' + n.hao, 11, '400', '#9aa9bb');", "if (n.hao) seg('hao ' + n.hao, 11, '400', '#9aa9bb');"),
  ("const gw = ctx.measureText('女').width + 7;", "const gw = ctx.measureText('♀').width + 7;"),
  ("ctx.fillText('女', tx + 3 + gw / 2, nameY - 4);", "ctx.fillText('♀', tx + 3 + gw / 2, nameY - 4);"),
  ("const gw = ctx.measureText('嗣').width + 7;", "const gw = ctx.measureText('ad').width + 7;"),
  ("ctx.fillText('嗣', tx + 3 + gw / 2, nameY - 4);", "ctx.fillText('ad', tx + 3 + gw / 2, nameY - 4);"),
  ("ctx.fillText('止', tx + 11, nameY - 4);", "ctx.fillText('dsp', tx + 11, nameY - 4);"),
  ("const t = (n.zi ? '字' + n.zi : '') + (n.zi && n.hao ? ' ' : '') + (n.hao ? '号' + n.hao : '');",
   "const t = (n.zi ? 'zi ' + n.zi : '') + (n.zi && n.hao ? ' ' : '') + (n.hao ? 'hao ' + n.hao : '');"),
  # ---- JS：导出文件名 / toast ----
  ("return (clanOf().ming || '家族族谱') + '-图-'", "return (clanOf().ming || 'Family Tree') + '-tree-'"),
  ("toast('图片已下载（' + cv.width + '×' + cv.height + '）');", "toast('Image downloaded (' + cv.width + '×' + cv.height + ')');"),
  ("toast('PDF 已下载（' + W + '×' + H + ' pt）');", "toast('PDF downloaded (' + W + '×' + H + ' pt)');"),
  ("toast('导出失败：' + e.message);", "toast('Export failed: ' + e.message);", 2),
  # ---- JS：打印 ----
  ("note.textContent = '谱书竖排 · 共 ' + cnt + ' 人' + (s < 1 ? '（整图已按页面缩放 ' + Math.round(s * 100) + '%）' : '');",
   "note.textContent = 'Vertical book layout · ' + cnt + ' people' + (s < 1 ? ' (scaled to ' + Math.round(s * 100) + '% for the page)' : '');"),
  ("if (n.gender === 'f') core += '（女）';", "if (n.gender === 'f') core += ' (f)';"),
  ("if (n.heir === 'in') core += '（嗣子）';", "if (n.heir === 'in') core += ' (heir)';"),
  ("if (n.heir === 'out') core += '（嗣出）';", "if (n.heir === 'out') core += ' (adopted out)';"),
  ("if (n.heir === 'jian') core += '（兼祧）';", "if (n.heir === 'jian') core += ' (dual heir)';"),
  ("if (n.zhi) core += '（止）';", "if (n.zhi) core += ' (dsp)';"),
  ("if (n.zi) zx.push('字' + n.zi);", "if (n.zi) zx.push('zi ' + n.zi);"),
  ("if (n.hao) zx.push('号' + n.hao);", "if (n.hao) zx.push('hao ' + n.hao);"),
  ("if (c.chain)  xuHtml += '<div><b>源流世系：</b>' + esc(c.chain) + '</div>';", "if (c.chain)  xuHtml += '<div><b>Lineage:</b>' + esc(c.chain) + '</div>';"),
  ("if (c.yuanzu) xuHtml += '<div><b>先祖：</b>' + esc(c.yuanzu) + '</div>';", "if (c.yuanzu) xuHtml += '<div><b>Forebears:</b>' + esc(c.yuanzu) + '</div>';"),
  ("if (c.shizu)  xuHtml += '<div><b>始祖记：</b>' + esc(c.shizu) + '</div>';", "if (c.shizu)  xuHtml += '<div><b>Founder record:</b>' + esc(c.shizu) + '</div>';"),
  ("if (c.origin) xuHtml += '<div><b>家族来源：</b>' + esc(c.origin) + '</div>';", "if (c.origin) xuHtml += '<div><b>Family origin:</b>' + esc(c.origin) + '</div>';"),
  # ---- JS：全局 ----
  ("toast('已自动保存，无需手动操作');", "toast('Already auto-saved — nothing to do');"),
  ("if (_seededFrom === 'legacy-draft') toast('已从本浏览器的历史数据恢复族谱');", "if (_seededFrom === 'legacy-draft') toast('Tree restored from this browser’s historical data');"),
  ("else if (_seededFrom === 'file') toast('自动保存已就绪：编辑即保存，无需手动操作');", "else if (_seededFrom === 'file') toast('Auto-save is on: every edit is saved, nothing to do');"),
  # ---- 结构默认值 ----
  ("let cfg = { genBase: 1, bookSpouse: true, showSurname: true, cnNum: false, vertical: false };",
   "let cfg = { genBase: 1, bookSpouse: false, showSurname: true, cnNum: false, vertical: false };"),
]

# ============================================================ JA 表
JA = [
  # ---- 顶栏 ----
  ('title="谱序 · 宗族源流（堂号/始祖/源流世系）"', 'title="譜序・宗族の源流（堂号/先祖/系統）"'),
  ('<span class="name" id="__puName">家族族谱</span>', '<span class="name" id="__puName">家系図</span>'),
  ('<span class="tag">传代树</span>', '<span class="tag">伝代ツリー</span>'),
  ('title="撤销（Ctrl+Z）"', 'title="元に戻す（Ctrl+Z）"'),
  ('title="重做（Ctrl+Y）"', 'title="やり直す（Ctrl+Y）"'),
  ('title="搜索（Ctrl+F）"', 'title="検索（Ctrl+F）"'),
  ('<button class="btn" id="btnView" title="视图">视图<', '<button class="btn" id="btnView" title="表示">表示<'),
  ('<button class="btn" id="btnFile" title="文件">文件<', '<button class="btn" id="btnFile" title="ファイル">ファイル<'),
  ('title="缩小"', 'title="縮小"'),
  ('title="放大"', 'title="拡大"'),
  ('title="适应屏幕"', 'title="画面に合わせる"'),
  ('title="恢复 1:1"', 'title="1:1 に戻す"'),
  ('<span id="statsChip"><b>4</b> 位成员 · 配偶 <b>2</b> · 4 代</span>', '<span id="statsChip"><b>4</b>人 · 配偶者 <b>2</b> · 4代</span>'),
  ('title="编辑即自动保存（存于本浏览器），无需手动操作"><span class="dot"></span>已保存</button>',
   'title="編集は自動保存されます（このブラウザに保存）"><span class="dot"></span>保存済み</button>'),
  ('title="帮助 / 快捷键"', 'title="ヘルプ / ショートカット"'),
  # ---- 档案弹窗 ----
  ('<h3 id="__dmTitle">人员档案</h3>', '<h3 id="__dmTitle">人物情報</h3>'),
  ('<label>姓名<input id="__dmName"></label>', '<label>氏名<input id="__dmName"></label>'),
  ('<label>出生<input id="__dmBirth" placeholder="1951 或 1951-03-15（约1900 / 1920? 也行；卡片只显示年份）"></label>',
   '<label>生年<input id="__dmBirth" placeholder="1951 または 1951-03-15（「明治43年」なども可。カードには年のみ表示）"></label>'),
  ('<label>卒年<input id="__dmDeath" placeholder="1985 或 1985-07-02（在世留空）"></label>',
   '<label>没年<input id="__dmDeath" placeholder="1985 または 1985-07-02（存命中は空欄）"></label>'),
  ('<label>性别<select id="__dmGender"><option value="">男</option><option value="f">女</option></select></label>',
   '<label>性別<select id="__dmGender"><option value="">男</option><option value="f">女</option></select></label>'),
  ('<label>过继<select id="__dmHeir"><option value="">无</option><option value="in">嗣子（入继此支）</option><option value="out">嗣出（出继他支）</option><option value="jian">兼祧（一子继两房）</option></select></label>',
   '<label>養縁<select id="__dmHeir"><option value="">なし</option><option value="in">嗣子（この支を継ぐ）</option><option value="out">嗣出（他家へ出す）</option><option value="jian">兼祧（二家を兼嗣）</option></select></label>'),
  ('<label>字<input id="__dmZi" placeholder="谱书常记，如 昭子"></label>', '<label>字（あざな）<input id="__dmZi" placeholder="譜に記録される字"></label>'),
  ('<label>号<input id="__dmHao" placeholder="可选"></label>', '<label>号（ごう）<input id="__dmHao" placeholder="任意"></label>'),
  ('止（无传 —— 谱书凡例：无传者以黑圈标止）', '止（無伝 —— 系図の凡例では黒丸で示す）'),
  ('<label>备注<textarea id="__dmNote" rows="3" placeholder="官职 / 迁徙 / 过继 / 生平注记……"></textarea></label>',
   '<label>備考<textarea id="__dmNote" rows="3" placeholder="官職 / 移住 / 養縁 / 生涯の注記…"></textarea></label>'),
  ('<button class="primary" id="__dmSave">保存</button>', '<button class="primary" id="__dmSave">保存</button>'),
  # ---- 初始 toast ----
  ('>已自动保存在本浏览器，编辑即保存</div>', '>このブラウザに自動保存されました。編集は即保存</div>'),
  # ---- 帮助弹窗 ----
  ('<h3>使用帮助</h3>', '<h3>ヘルプ</h3>'),
  ('<h4>数据是怎么保存的</h4>', '<h4>データの保存方法</h4>'),
  ('<b>保存是无感的</b>：所有修改即时自动保存在本浏览器（和 Gmail 草稿一样），没有保存按钮、没有弹窗、不需要任何操作。顶栏绿灯「已保存」常亮即安心。',
   '<b>保存は自動</b>：すべての変更はこのブラウザに即時保存されます（Gmail の下書きと同じ）。保存ボタンもダイアログも不要です。トップバーの緑の「保存済み」が安心の印です。'),
  ('数据存在<b>这台电脑的这个浏览器</b>里。两件事需要记得：<b>换电脑/换浏览器</b>时先「文件 ▾ → 备份到文件」下载 json，到新机器「恢复备份」；<b>清理浏览器数据</b>前也先备份。旧版 html 里若有数据，「恢复备份」可直接读出。',
   'データは<b>この PC のこのブラウザ</b>に保存されます。<b>PC やブラウザを変えるとき</b>は「ファイル ▾ → バックアップ保存」で json をダウンロードし、新しい環境で「バックアップ復元」してください。<b>ブラウザデータを消す前</b>もバックアップを。旧形式の html にデータがあれば「バックアップ復元」で直接読み込めます。'),
  ('<h4>编辑</h4>', '<h4>編集</h4>'),
  ('<tbody><tr><td><kbd>＋</kbd> 节点下方常驻按钮 / 右键节点</td><td>打开该成员的操作菜单</td></tr>',
   '<tbody><tr><td><kbd>＋</kbd> ボタン / 右クリック</td><td>メンバーの操作メニューを開く</td></tr>'),
  ('<tr><td><kbd>双击</kbd> 姓名</td><td>行内改名</td></tr>', '<tr><td><kbd>ダブルクリック</kbd> 氏名</td><td>その場で名前を変更</td></tr>'),
  ('<tr><td><kbd>双击</kbd> 姓名下方小字行</td><td>编辑生卒年与备注（档案）</td></tr>', '<tr><td><kbd>ダブルクリック</kbd> 氏名下の小さな行</td><td>生没年と備考を編集（人物情報）</td></tr>'),
  ('<tr><td><kbd>双击</kbd> 配偶名</td><td>改名；清空并确定 = 移除</td></tr>', '<tr><td><kbd>ダブルクリック</kbd> 配偶者名</td><td>名前変更。空にして決定 = 削除</td></tr>'),
  ('<tr><td><kbd>Tab</kbd> / <kbd>Enter</kbd></td><td>为选中者加子女 / 加同辈</td></tr>', '<tr><td><kbd>Tab</kbd> / <kbd>Enter</kbd></td><td>選択中の人に子 / 兄弟姉妹を追加</td></tr>'),
  ('<tr><td><kbd>Ctrl+Shift+S</kbd></td><td>加配偶（可多次，支持元配/继室）</td></tr>', '<tr><td><kbd>Ctrl+Shift+S</kbd></td><td>配偶者を追加（複数回可。先妻・継妻に対応）</td></tr>'),
  ('<tr><td><kbd>Ctrl+I</kbd> / <kbd>F2</kbd></td><td>档案 / 改名</td></tr>', '<tr><td><kbd>Ctrl+I</kbd> / <kbd>F2</kbd></td><td>人物情報 / 名前変更</td></tr>'),
  ('<tr><td><kbd>Delete</kbd></td><td>删除（含后代，可撤销）</td></tr>', '<tr><td><kbd>Delete</kbd></td><td>削除（子孫ごと。元に戻せます）</td></tr>'),
  ('<tr><td>按住节点左右拖</td><td>调长幼次序（最左为长）</td></tr>', '<tr><td>ノードを左右にドラッグ</td><td>兄弟の順序を変更（左が長）</td></tr>'),
  ('<tr><td>按住拖到某卡片上停一下</td><td>过继：TA（连同后代整支）成为此人子女，Ctrl+Z 可撤销</td></tr>',
   '<tr><td>カードに重ねて一時停止</td><td>養縁：その人（子孫全員ごと）がこの人の子になります。Ctrl+Z で取消</td></tr>'),
  ('<h4>视图与数据</h4>', '<h4>表示とデータ</h4>'),
  ('<tbody><tr><td><kbd>Ctrl+滚轮</kbd></td><td>以光标为中心缩放</td></tr>', '<tbody><tr><td><kbd>Ctrl+スクロール</kbd></td><td>カーソル位置を中心に拡大縮小</td></tr>'),
  ('<tr><td>滚轮 / 触控板 / 拖空白</td><td>平移画布</td></tr>', '<tr><td>スクロール / タッチパッド / 空白をドラッグ</td><td>キャンバスを移動</td></tr>'),
  ('<tr><td><kbd>Ctrl+F</kbd></td><td>搜索（姓名/配偶/年份/备注），Enter 循环跳转</td></tr>', '<tr><td><kbd>Ctrl+F</kbd></td><td>検索（氏名/配偶者/年/備考）。Enter で次へ</td></tr>'),
  ('<tr><td><kbd>Ctrl+Z</kbd> / <kbd>Ctrl+Y</kbd></td><td>撤销 / 重做</td></tr>', '<tr><td><kbd>Ctrl+Z</kbd> / <kbd>Ctrl+Y</kbd></td><td>元に戻す / やり直す</td></tr>'),
  ('<tr><td><kbd>Ctrl+S</kbd></td><td>已自动保存（拦截浏览器另存，无需手动操作）</td></tr>', '<tr><td><kbd>Ctrl+S</kbd></td><td>自動保存済み（ブラウザの保存ダイアログは出ません）</td></tr>'),
  ('<tr><td>蓝色角标 / 橙色角标</td><td>出生年（自动排长幼）/ 排行称谓（手动排序）</td></tr>', '<tr><td>青色バッジ / オレンジ色バッジ</td><td>生年（自動並び）/ 誕生順（手動並び）</td></tr>'),
  ('<tr><td>视图 ▾ 谱书竖排（古法）</td><td>世代成行、名字竖书（右→左）、行左标世数；导出图同款排版</td></tr>',
   '<tr><td>表示 ▾ 譜書縦書き（古法）</td><td>世代を行でまとめ、名を縦書き（右→左）、行左に世代を表示。出力も同じ体裁</td></tr>'),
  ('<tr><td>视图 ▾ 谱书显示设置</td><td>世代基准（对齐谱书世数，如勤=23世填13）/ 配偶谱式（丁嘉→丁氏嘉）/ 姓氏周开关 / 世数用汉字</td></tr>',
   '<tr><td>表示 ▾ 譜書表示設定</td><td>世代基準（譜書の世代数に合わせる）/ 配偶者の譜式 / 姓氏の表示 / 世代数の漢数字</td></tr>'),
  ('<tr><td><kbd>▸ N</kbd></td><td>此支已折叠 N 位后代，点击展开</td></tr>', '<tr><td><kbd>▸ N</kbd></td><td>この支は N 人の子孫ごと折りたたまれています。クリックで展開</td></tr>'),
  ('<h4 id="__zbTitle">字辈表（蓝框 = 族谱中已出现）</h4>', '<h4 id="__zbTitle">字輩表（青枠 = 譜に現れる字）</h4>'),
  ('>知道了</button>', '>閉じる</button>'),
  # ---- 显示设置弹窗 ----
  ('<h3>谱书显示设置</h3>', '<h3>譜書表示設定</h3>'),
  ('<label>世代基准 —— 字辈第 1 字对应的谱书世数<input id="__cfgBase" type="number" min="1" max="99" step="1"></label>',
   '<label>世代基準 —— 字輩の 1 字目が譜書で何世に当たるか<input id="__cfgBase" type="number" min="1" max="99" step="1"></label>'),
  ('传统谱书的「世」从<b>始祖一世</b>起算，而字辈往往是后世才议定的。你家谱书「勤」字辈记为<b>廿三世</b>，「勤」是字辈第 11 字，所以「多」字辈=第 <b>13</b> 世：这里填 <b>13</b>，卡片即显示「23世·勤」；填 1 则按应用自算显示「11代」。只改显示，不影响数据。',
   '伝統的な譜書の「世」は<b>始祖を一世</b>として数えますが、字輩は後世に定められることも少なくありません。例：譜書で「勤」の字輩が<b>廿三世</b>、「勤」は字輩の 11 字目なら、字輩 1 字目「多」は第 <b>13</b> 世。ここに <b>13</b> と入れるとカードは「23世・勤」と表示され、1 と入れるとアプリ計算の「11代」になります。表示のみの変更で、データには影響しません。'),
  ('<label class="checkline"><input type="checkbox" id="__cfgSpouse"> 配偶按谱书式显示（丁嘉 → 丁氏嘉；数据仍存原名，搜索不受影响）</label>',
   '<label class="checkline"><input type="checkbox" id="__cfgSpouse"> 配偶者を譜書式で表示（丁嘉 → 丁氏嘉。データは元の名のまま、検索に影響なし）</label>'),
  ('<label class="checkline"><input type="checkbox" id="__cfgSurname"> 姓名显示姓氏「<span id="__cfgSurName">—</span>」（关闭 = 按谱书习惯只报名；仅显示层，姓氏随数据自动识别）</label>',
   '<label class="checkline"><input type="checkbox" id="__cfgSurname"> 氏名に姓「<span id="__cfgSurName">—</span>」を表示（オフ = 譜書の慣例で名のみ。表示のみで、姓はデータから自動判定）</label>'),
  ('<label class="checkline"><input type="checkbox" id="__cfgCn"> 世数用汉字（廿三世·勤；关闭显示 23世·勤）</label>',
   '<label class="checkline"><input type="checkbox" id="__cfgCn"> 世代数を漢数字で表示（廿三世・勤。オフで 23世・勤）</label>'),
  # ---- 谱序弹窗 ----
  ('<h3>谱序 · 宗族源流</h3>', '<h3>譜序・宗族の源流</h3>'),
  ('<label>谱名<input id="__clMing" placeholder="如 潮阳泗水周氏族谱"></label>', '<label>譜名<input id="__clMing" placeholder="例：○○家系図"></label>'),
  ('<label>堂号<input id="__clTang" placeholder="可选，如 四知堂 / 陇西堂"></label>', '<label>堂号<input id="__clTang" placeholder="任意（例：陇西堂）"></label>'),
  ('<label>源流世系（远祖 → 近祖，用 — 相连）<input id="__clChain" placeholder="始祖 — 二世 — 三世……"></label>',
   '<label>系統（遠祖 → 近祖を — でつなぐ）<input id="__clChain" placeholder="始祖 — 二世 — 三世…"></label>'),
  ('<label>字辈表（空格 / 逗号 / 顿号分隔，按世代顺序；用于自动定代）<textarea id="__clZibei" rows="2" placeholder="如：德 承 传 世 泽 诗 礼 继 家 声"></textarea></label>',
   '<label>字輩表（空白/読点/カンマ区切り、世代順。自動世代判定に使用）<textarea id="__clZibei" rows="2" placeholder="例：義 正 健 雄"></textarea></label>'),
  ('<label>先祖<input id="__clYuan" placeholder="如 周敦颐，字茂叔，号濂溪（湖南道州）"></label>', '<label>先祖<input id="__clYuan" placeholder="例：遠祖の氏名・略伝"></label>'),
  ('<label>始祖记<textarea id="__clShi" rows="3" placeholder="一世祖承节公讳宣道……二世祖朝奉公讳景一……"></textarea></label>',
   '<label>始祖記<textarea id="__clShi" rows="3" placeholder="一世祖：…  二世祖：…"></textarea></label>'),
  ('<label>始迁祖<input id="__clQian" placeholder="如 （南宋）宣，字承节"></label>', '<label>始遷祖<input id="__clQian" placeholder="例：江戸初期に○○へ移住"></label>'),
  ('<label>家族来源<textarea id="__clOrigin" rows="5" placeholder="宗支源流叙述……"></textarea></label>', '<label>家族の由緒<textarea id="__clOrigin" rows="5" placeholder="この家支の由緒…"></textarea></label>'),
  ('<button class="primary" id="__clSave">保存</button>', '<button class="primary" id="__clSave">保存</button>'),
  ('>取消</button>', '>キャンセル</button>', 3),
  # ---- 向导 ----
  ('<h3>欢迎使用家族族谱</h3>', '<h3>家系図へようこそ</h3>'),
  ('这是一个<b>本地优先</b>的单文件应用：数据只存在<b>你的浏览器</b>里，不联网、无账号、编辑即自动保存。',
   'これは<b>ローカルファースト</b>のシングルファイルアプリです。データは<b>あなたのブラウザ</b>にのみ保存され、ネット接続もアカウントも不要、編集は自動保存されます。'),
  ('当前载入的是示例数据（赵钱孙李演示谱），三选一：', '現在はデモデータが読み込まれています。三つから選んでください：'),
  ('<button type="button" data-wiz="demo"><b>先看看示例</b>赵钱孙李演示谱，可随意折腾</button>',
   '<button type="button" data-wiz="demo"><b>まずデモを見る</b>サンプル家系図。自由にいじってOK</button>'),
  ('<button type="button" data-wiz="import"><b>导入备份</b>恢复你自己的 json 数据</button>',
   '<button type="button" data-wiz="import"><b>バックアップから復元</b>自分の json データを読み込む</button>'),
  ('<label>谱名（从空白开始时使用）<input id="__wizMing" placeholder="如 赵氏族谱 / 李氏家谱"></label>',
   '<label>譜名（白紙から始めるときに使用）<input id="__wizMing" placeholder="例：○○家系図"></label>'),
  ('<label>堂号（可选）<input id="__wizTang" placeholder="如 四知堂"></label>', '<label>堂号（任意）<input id="__wizTang" placeholder="例：陇西堂"></label>'),
  ('<button class="primary" id="__wizGo">从空白开始</button>', '<button class="primary" id="__wizGo">白紙から始める</button>'),
  # ---- 搜索 / 提示条 / 图例 ----
  ('placeholder="搜姓名/配偶/备注…"', 'placeholder="氏名・配偶者・備考を検索…"'),
  ('title="上一个（Shift+Enter）"', 'title="前へ（Shift+Enter）"'),
  ('title="下一个（Enter）"', 'title="次へ（Enter）"'),
  ('title="关闭（Esc）"', 'title="閉じる（Esc）"'),
  ('title="节点下方常驻「＋」或右键=操作菜单 · 双击姓名=改名 · 双击备注行=档案 · 按住拖=调次序，拖到卡片上停一下=过继 · Ctrl+滚轮=缩放 · 滚轮/拖空白=平移 · 编辑自动保存 · 详细说明见「?」帮助">操作：<b>＋/右键</b>=菜单 · <b>双击</b>=改名/档案 · <b>拖</b>=调次序或过继 · <b>Ctrl+滚轮</b>=缩放 · 滚轮/拖空白=平移 · 自动保存 · 更多见「?」帮助',
   'title="ノード下の「＋」や右クリック=操作メニュー · ダブルクリック=名前変更/人物情報 · ドラッグ=順序変更・養縁 · Ctrl+スクロール=拡大縮小 · スクロール/空白ドラッグ=移動 · 自動保存 · 詳しくは「?」">編集：<b>＋/右クリック</b>=メニュー · <b>ダブルクリック</b>=名前/情報 · <b>ドラッグ</b>=順序・養縁 · <b>Ctrl+スクロール</b>=拡大縮小 · 自動保存 · 詳しくは「?」'),
  ('</i>总根</span>', '</i>総根</span>'),
  ('</i>第一代</span>', '</i>第一世代</span>'),
  ('</i>第二代</span>', '</i>第二世代</span>'),
  ('</i>第三代</span>', '</i>第三世代</span>'),
  ('</i>第四代</span>', '</i>第四世代</span>'),
  ('</i>第五代及以后</span>', '</i>第五世代以降</span>'),
  ('</i>待核对备注</span>', '</i>要確認の備考</span>'),
  ('<b style="color:var(--birth-bg)">蓝色角标</b>=出生年（自动排）', '<b style="color:var(--birth-bg)">青バッジ</b>=生年（自動並び）'),
  ('<b style="color:var(--rank-bg)">橙色角标</b>=排行称谓（最左为长）', '<b style="color:var(--rank-bg)">オレンジバッジ</b>=誕生順（左が長）'),
  ('<b style="color:var(--accent)">▸ N</b>=已折叠 N 位后代（点它展开）', '<b style="color:var(--accent)">▸ N</b>=N 人の子孫を折りたたみ中（クリックで展開）'),
  ('<b style="color:#b04a72">女</b>=女性成员（男不标，谱书惯例）', '<b style="color:#b04a72">女</b>=女性のメンバー（男性は表記なし。譜書の慣例）'),
  # ---- JS：称谓 / 字辈语法 ----
  ("return ['原配', '续弦', '三房', '四房', '五房', '六房', '七房', '八房'][i] || '第' + (i + 1) + '房';",
   "return ['先妻', '継妻', '三妻', '四妻', '五妻', '六妻', '七妻', '八妻'][i] || '第' + (i + 1) + '妻';"),
  ("const SP_TERMS = ['配', '继配', '娶', '聘', '侧室'];", "const SP_TERMS = ['配', '継配', '娶', '聘', '側室'];"),
  ("return ['配', '继配', '三配', '四配', '五配', '六配', '七配', '八配'][i] || '第' + (i + 1) + '配';",
   "return ['配', '継配', '三配', '四配', '五配', '六配', '七配', '八配'][i] || '第' + (i + 1) + '配';"),
  ("else if (b) parts.push(b + ' 生');", "else if (b) parts.push(b + ' 生');"),
  ("else if (d) parts.push('卒 ' + d);", "else if (d) parts.push('卒 ' + d);"),
  ("return seg ? '生卒：' + seg : '';", "return seg ? '生没：' + seg : '';"),
  ("return n.heir === 'in' ? '嗣子：过继来继承此支（谱书式「过继TA为子」）'\n       : n.heir === 'out' ? '嗣出：过继给他人为子（谱书式「TA过继某某为子」）'\n       : n.heir === 'jian' ? '兼祧（兼嗣）：一子兼继两房' : '';",
   "return n.heir === 'in' ? '嗣子：この支を継ぐために養子に入る'\n       : n.heir === 'out' ? '嗣出：他の家の養子として出る'\n       : n.heir === 'jian' ? '兼祧（兼嗣）：一子が二家を兼ね継ぐ' : '';"),
  ("const t = ['','','廿','卅','卌'][Math.floor(n / 10)];", "const t = ['','','二十','三十','四十'][Math.floor(n / 10)];"),
  ("const RANK_WORDS = ['长','次','三','四','五','六','七','八','九','十','十一','十二','十三','十四','十五'];",
   "const RANK_WORDS = ['長','次','三','四','五','六','七','八','九','十','十一','十二','十三','十四','十五'];"),
  ("migrate({ id:'root', name:'家族族谱', spouses:[], expanded:true, children:[] })",
   "migrate({ id:'root', name:'家系図', spouses:[], expanded:true, children:[] })"),
  # ---- JS：世代 tooltip ----
  ("const unused = ziOfGen ? '（本人名字未用本代字辈「' + ziOfGen + '」）' : '（名字未用字辈）';",
   "const unused = ziOfGen ? '（この名は本世代の字輩「' + ziOfGen + '」を使用していません）' : '（名前に字輩なし）';"),
  ("const base = genOffset() ? '（谱书世数，应用自算第' + g.gen + '代）' : '';",
   "const base = genOffset() ? '（譜書の世数。アプリ計算では第' + g.gen + '代）' : '';"),
  ("return '字辈「' + g.zi + '」= ' + genLabel(g.gen) + base",
   "return '字輩「' + g.zi + '」= ' + genLabel(g.gen) + base"),
  ("+ (g.conflict ? '（注意：按父辈推算应为' + genLabel(g.conflict) + '，树中可能缺一代）' : '');",
   "+ (g.conflict ? '（注意：親からの推算では ' + genLabel(g.conflict) + '。世代が一つ欠けている可能性）' : '');"),
  ("case 'parent':  return '由父/母「' + (p ? dispName(p.name) : '') + '」推算：' + genLabel(g.gen) + base + unused;",
   "case 'parent':  return '親「' + (p ? dispName(p.name) : '') + '」からの推算：' + genLabel(g.gen) + base + unused;"),
  ("case 'sibling': return '与「' + dispName(g.via || '') + '」同辈推算：' + genLabel(g.gen) + base + unused;",
   "case 'sibling': return '「' + dispName(g.via || '') + '」と同世代として推算：' + genLabel(g.gen) + base + unused;"),
  ("default:        return '按世系推算：' + genLabel(g.gen) + base + unused;",
   "default:        return '系統の深さから推算：' + genLabel(g.gen) + base + unused;"),
  # ---- JS：撤销/重做 ----
  ("toast('没有可撤销的操作');", "toast('元に戻せる操作はありません');"),
  ("toast('已撤销');", "toast('元に戻しました');"),
  ("toast('没有可重做的操作');", "toast('やり直せる操作はありません');"),
  ("toast('已重做');", "toast('やり直しました');"),
  # ---- JS：卡片 ----
  ("rk.title = '出生年 ' + yr + '：同辈按出生年自动排序，年长在左';",
   "rk.title = '生年 ' + yr + '：兄弟は生年順に自動並び（年長が左）';"),
  ("rk.title = '同辈第 ' + (orderIdx + 1) + ' 位（最左为长）。补填出生年即可自动排序';",
   "rk.title = '兄弟の ' + (orderIdx + 1) + ' 番目（左が長）。生年を入れると自動並びになります';"),
  ("rk.title = '同辈第 ' + (orderIdx + 1) + ' 位（最左为长）。补填出生年即可自动排序';", None),  # placeholder removed below
  ("'\">嗣</span>'", None),
]

# 上の JA 配列で None を入れた箇所は「変更なし」を意味する（フィルタで除去）
JA = [t for t in JA if t[1] is not None]
EN = [t for t in EN if t[1] is not None]

# ---- JA 続き：カード以降（URN：日文 UI の残り半分）----
JA += [
  # ---- JS：竖排行标 / 统计条 / 保存灯 ----
  ("el.textContent = numToCn(g + genOffset()) + genUnit() + (zi ? '·' + zi : '');",
   "el.textContent = numToCn(g + genOffset()) + genUnit() + (zi ? '·' + zi : '');"),
  ("el.title = '本行「' + el.textContent + '」';", "el.title = 'この行：' + el.textContent;"),
  ("extra = ' · 字辈第<b>' + (cfg.cnNum ? numToCn(loV) + '–' + numToCn(hiV) : loV + '–' + hiV) + '</b>' + genUnit();",
   "extra = ' · 字輩第<b>' + (cfg.cnNum ? numToCn(loV) + '–' + numToCn(hiV) : loV + '–' + hiV) + '</b>' + genUnit();"),
  ("'<b>' + persons + '</b> 位成员 · 配偶 <b>' + sp + '</b> · ' + (cfg.cnNum ? numToCn(totV) : totV) + ' ' + genUnit() + extra;",
   "'<b>' + persons + '</b>人 · 配偶者 <b>' + sp + '</b> · ' + (cfg.cnNum ? numToCn(totV) : totV) + genUnit() + extra;"),
  ("el.innerHTML = '<span class=\"dot\"></span>未能保存';", "el.innerHTML = '<span class=\"dot\"></span>保存できず';"),
  ("el.title = '此浏览器环境不允许写入本地存储（如无痕模式/配额已满）——'\n             + '本次修改不会被记住，请立即用「文件 ▾ → 备份到文件」导出 json！';",
   "el.title = 'このブラウザはローカルストレージに書き込めません（シークレットモード／容量不足）——'\n             + '変更は保存されません。「ファイル ▾ → バックアップ保存」ですぐ json を書き出してください！';"),
  ("el.innerHTML = '<span class=\"dot\"></span>已保存';", "el.innerHTML = '<span class=\"dot\"></span>保存済み';"),
  ("el.title = '所有修改都已自动保存在此浏览器 · 备份/换电脑见「文件 ▾」菜单';",
   "el.title = 'すべての変更はこのブラウザに自動保存済み · バックアップ/機種変更は「ファイル ▾」メニュー';"),
  # ---- JS：档案 ----
  ("const t = prompt('修改姓名：', n.name);", "const t = prompt('名前を変更：', n.name);"),
  ("'人员档案 · '", "'人物情報 · '"),
  ("'<option value=\"\">（默认）</option>'", "'<option value=\"\">（既定）</option>'"),
  ("row.innerHTML = '<label>配偶 ' + (i + 1) + ' · ' + esc(spName) + ' 称谓<select data-i=\"' + i + '\">' + opts + '</select></label>';",
   "row.innerHTML = '<label>配偶者 ' + (i + 1) + ' · ' + esc(spName) + ' の呼称<select data-i=\"' + i + '\">' + opts + '</select></label>';"),
  ("toast('已保存，并按出生年自动重排「' + n.name + '」同辈的长幼（年长在左）');",
   "toast('保存しました。「' + n.name + '」の兄弟を生年順に並べ替えました（年長が左）');"),
  ("toast('已保存「' + n.name + '」的档案');", "toast('「' + n.name + '」の情報を保存しました');"),
  ("toast('已保存「' + n.name + '」的档案（未填出生年，长幼按手动排列）');",
   "toast('「' + n.name + '」の情報を保存しました（生年未入力のため、兄弟は手動順のまま）');"),
  # ---- JS：菜单 ----
  ("ctxMenu.appendChild(mi('＋ 第一代', '', '', () => addChild(n)));", "ctxMenu.appendChild(mi('＋ 第一世代', '', '', () => addChild(n)));"),
  ("ctxMenu.appendChild(mi('＋ 配偶', '', 'Ctrl+Shift+S', () => addSpouse(n)));", "ctxMenu.appendChild(mi('＋ 配偶者', '', 'Ctrl+Shift+S', () => addSpouse(n)));"),
  ("ctxMenu.appendChild(mi('＋ 子女', '', 'Tab', () => addChild(n)));", "ctxMenu.appendChild(mi('＋ 子', '', 'Tab', () => addChild(n)));"),
  ("ctxMenu.appendChild(mi('＋ 同辈', '', 'Enter', () => addSibling(n)));", "ctxMenu.appendChild(mi('＋ 兄弟姉妹', '', 'Enter', () => addSibling(n)));"),
  ("ic('pencil') + '改名'", "ic('pencil') + '名前変更'"),
  ("ic('card') + '档案'", "ic('card') + '人物情報'"),
  ("mi(n.expanded ? ic('fold') + '折叠此支' : ic('unfold') + '展开此支'", "mi(n.expanded ? ic('fold') + 'この支を折りたたむ' : ic('unfold') + 'この支を展開'"),
  ("ic('trash') + '删除'", "ic('trash') + '削除'"),
  ("mi(ic('unfold') + '全展开'", "mi(ic('unfold') + 'すべて展開'"),
  ("mi(ic('fold') + '全折叠'", "mi(ic('fold') + 'すべて折りたたむ'"),
  ("mi((cfg.vertical ? '✓ ' : '') + ic('filetext') + '谱书竖排（古法）'", "mi((cfg.vertical ? '✓ ' : '') + ic('filetext') + '譜書縦書き（古法）'"),
  ("mi(ic('card') + '谱序（堂号·源流）…'", "mi(ic('card') + '譜序（堂号・源流）…'"),
  ("mi(ic('gear') + '谱书显示设置…'", "mi(ic('gear') + '譜書表示設定…'"),
  ("mi(ic('download') + '备份到文件（json）'", "mi(ic('download') + 'バックアップ保存（json）'"),
  ("mi(ic('folder') + '恢复备份（json / 旧版 html）'", "mi(ic('folder') + 'バックアップ復元（json / 旧 html）'"),
  ("mi(ic('image') + '导出图片（png）'", "mi(ic('image') + '画像を出力（png）'"),
  ("mi(ic('pdf') + '导出 PDF（图谱）'", "mi(ic('pdf') + 'PDF を出力（図）'"),
  ("mi(ic('filetext') + '世系录（五世一表）'", "mi(ic('filetext') + '世系録（五世一表）'"),
  ("mi(ic('filetext') + '导出 MD'", "mi(ic('filetext') + 'MD を出力'"),
  ("mi(ic('print') + '打印（纸质）'", "mi(ic('print') + '印刷（紙）'"),
  ("mi(ic('sort') + '按生年重排'", "mi(ic('sort') + '生年で並べ替え'"),
  ("mi(ic('reset') + '重置数据'", "mi(ic('reset') + 'データをリセット'"),
  # ---- JS：字辈角标 ----
  ("'字辈表（第' + range + genUnit() + '，蓝框 = 族谱中已出现）';", "'字輩表（第' + range + genUnit() + '、青枠 = 譜に現れる字）';"),
  ("d.innerHTML = esc(z || '·') + '<small>第' + genLabel(i + 1) + '</small>';",
   "d.innerHTML = esc(z || '·') + '<small>第' + genLabel(i + 1) + '</small>';"),
  ("d.title = '第' + genLabel(i + 1) + '字辈「' + (z || '?') + '」' + (all.includes(z) ? '（族谱中已出现）' : '');",
   "d.title = '第' + genLabel(i + 1) + 'の字輩「' + (z || '?') + '」' + (all.includes(z) ? '（譜に現れる）' : '');"),
  ("'<span class=\"help-note\">本文件尚未配置字辈表</span>'", "'<span class=\"help-note\">このファイルには字輩表が未設定です</span>'"),
  ("FAM_SUR || '（自动识别）'", "FAM_SUR || '（自動判定）'"),
  # ---- JS：设置/视图 toast ----
  ("toast('显示设置已保存：' + (cfg.genBase > 1 ? '字辈第 1 字 = 第 ' + cfg.genBase + ' 世' : '按应用自算代数')\n    + ' · 配偶' + (cfg.bookSpouse ? '谱书式' : '原名')\n    + ' · ' + (cfg.showSurname ? '显示姓氏' : '只报名')\n    + ' · 世数' + (cfg.cnNum ? '用汉字' : '用数字'));",
   "toast('表示設定を保存しました：' + (cfg.genBase > 1 ? '字輩 1 字目 = 第 ' + cfg.genBase + ' 世' : 'アプリ計算の世代数')\n    + ' · 配偶者' + (cfg.bookSpouse ? '譜書式' : '元の名')\n    + ' · ' + (cfg.showSurname ? '姓を表示' : '名のみ')\n    + ' · 世代数' + (cfg.cnNum ? '漢数字' : '算用数字'));"),
  ("toast(cfg.vertical ? '已切换谱书竖排（古法）：世代成行、名字竖书、行左标世数' : '已切回常规视图');",
   "toast(cfg.vertical ? '譜書縦書き（古法）に切り替えました：世代を行で、名は縦書き、行左に世代' : '通常表示に戻しました');"),
  # ---- JS：谱序 ----
  ("return (c.ming || '家族族谱') + (c.tang ? '（' + c.tang + '）' : '');", "return (c.ming || '家系図') + (c.tang ? '（' + c.tang + '）' : '');"),
  ("document.getElementById('__puName').textContent = c.ming || '家族族谱';", "document.getElementById('__puName').textContent = c.ming || '家系図';"),
  ("document.title = (c.ming || '家族族谱') + (c.tang ? ' · ' + c.tang : '');", "document.title = (c.ming || '家系図') + (c.tang ? ' · ' + c.tang : '');"),
  ("toast('谱序已保存：谱名、堂号将随导出与打印一起出现');", "toast('譜序を保存しました：譜名・堂号は出力と印刷に反映されます');"),
  # ---- JS：向导 ----
  ("toast('示例数据：双击名字改名、点「＋」添加成员，所有操作都可撤销');", "toast('デモデータ：名前をダブルクリックで変更、「＋」でメンバー追加。すべて元に戻せます');"),
  ("document.getElementById('__wizMing').value.trim() || '我的家族';", "document.getElementById('__wizMing').value.trim() || 'わたしの家系';"),
  ("toast('空白族谱「' + ming + '」已创建：点第一个「＋」添加第一代成员');", "toast('白紙の家系図「' + ming + '」を作成しました：最初の「＋」で第一世代を追加');"),
  # ---- JS：配偶/子女/同辈/删除 ----
  ("const t = prompt('为「' + n.name + '」添加第 ' + nth + ' 位配偶姓名：\\n（如需改名/移除某位配偶，直接双击图上该配偶的名字）');",
   "const t = prompt('「' + n.name + '」の第 ' + nth + ' 配偶者の名前を追加：\\n（配偶者の名前変更・削除は、カード上の名前をダブルクリック）');"),
  ("toast('「' + v + '」已是 ' + n.name + ' 的配偶，无需重复添加');", "toast('「' + v + '」は既に ' + n.name + ' の配偶者です');"),
  ("toast('已为 ' + n.name + ' 添加配偶「' + v + '」，继续点「＋配偶」可再加');", "toast(n.name + ' に配偶者「' + v + '」を追加しました。「＋配偶者」で追加できます');"),
  ("const t = prompt('修改「' + n.name + '」的第 ' + (i + 1) + ' 位配偶：\\n（清空并确定 = 移除这位配偶）', cur);",
   "const t = prompt('「' + n.name + '」の第 ' + (i + 1) + ' 配偶者を変更：\\n（空にして決定 = この配偶者を削除）', cur);"),
  ("if (confirm('确定移除配偶「' + cur + '」？')){", "if (confirm('配偶者「' + cur + '」を削除しますか？')){"),
  ("? '在「家族族谱」下添加一位第一代成员（新祖辈分支）：'", "? '「家系図」の下に第一世代のメンバーを追加（新しい祖 先ブランチ）：'"),
  (": '为「' + displayName(n) + '」添加子女姓名：'", ": '「' + displayName(n) + '」に子の名前を追加：'"),
  ("? '已添加第一代成员「' + t.trim() + '」（默认排最右=最幼，按住拖动可调长幼）'",
   "? '第一世代のメンバー「' + t.trim() + '」を追加しました（初期は最右=最年少。ドラッグで順序変更可）'"),
  (": '已为 ' + n.name + ' 添加子女「' + t.trim() + '」');", ": n.name + ' に子「' + t.trim() + '」を追加しました');"),
  ("if (n.id === 'root'){ toast('根节点不能删'); return; }", "if (n.id === 'root'){ toast('ルートノードは削除できません'); return; }"),
  ("? '删除「' + displayName(n) + '」及其全部 ' + desc + ' 位后代？'", "? '「' + displayName(n) + '」と子孫全員（' + desc + '人）を削除しますか？'"),
  (": '删除「' + displayName(n) + '」？';", ": '「' + displayName(n) + '」を削除しますか？';"),
  ("toast('已删除（可用 Ctrl+Z 撤销）');", "toast('削除しました（Ctrl+Z で元に戻せます）');"),
  ("const t = prompt('添加一位与「' + n.name + '」同辈的成员（' + (p.id === 'root' ? '第一代' : '同父母') + '）：');",
   "const t = prompt('「' + n.name + '」と同世代のメンバーを追加（' + (p.id === 'root' ? '第一世代' : '同じ親') + '）：');"),
  ("toast('已添加「' + t.trim() + '」，默认排最右=最幼；按住拖到左边可成为更长');",
   "toast('「' + t.trim() + '」を追加しました（初期は最右=最年少。左へドラッグで年長に）');"),
  # ---- JS：排序/过继/换位 ----
  ("? '已按出生年重排 ' + t + ' 组同辈（年长在左；无出生年的保持原次序排其后）'",
   "? '生年順に ' + t + ' 组の兄弟を並べ替えました（年長が左。生年未入力は元の順のまま後ろへ）'"),
  (": '暂无任何人填出生年，未做改动（先在「档案」里补出生年）');", ": '生年が未入力のため変更なし（まず「人物情報」で生年を入力してください）');"),
  ("? '「' + d.n.name + '」已移入第一代（可拖拽微调长幼）'", "? '「' + d.n.name + '」を第一世代へ移動しました（ドラッグで順序調整可）'"),
  (": '「' + d.n.name + '」已过继到「' + tp.name + '」名下（排最幼，可拖拽微调长幼；Ctrl+Z 可撤销）');",
   ": '「' + d.n.name + '」を「' + tp.name + '」の養子縁組で移動しました（最年少扱い。ドラッグで調整、Ctrl+Z で取消）');"),
  ("toast('已换位：' + me.name + ' 现在是同辈第 ' + (newIdx + 1) + ' 位（排行「' + rankWord(newIdx) + '」，最左为长）');",
   "toast('入れ替えました：' + me.name + ' は兄弟の ' + (newIdx + 1) + ' 番目（' + rankWord(newIdx) + '、左が長）');"),
  # ---- JS：搜索 ----
  ("else sbCount.textContent = '无匹配';", "else sbCount.textContent = '該当なし';"),
  # ---- JS：MD 导出 ----
  ("let line = dispName(n.name) + (n.gender === 'f' ? '（女）' : '');", "let line = dispName(n.name) + (n.gender === 'f' ? '（女）' : '');"),
  ("if (n.zi) line += '（字' + n.zi + '）';", "if (n.zi) line += '（字' + n.zi + '）';"),
  ("if (n.hao) line += '（号' + n.hao + '）';", "if (n.hao) line += '（号' + n.hao + '）';"),
  ("if (n.heir === 'in') line += '（嗣子）';", "if (n.heir === 'in') line += '（嗣子）';"),
  ("if (n.heir === 'out') line += '（嗣出）';", "if (n.heir === 'out') line += '（嗣出）';"),
  ("if (n.heir === 'jian') line += '（兼祧）';", "if (n.heir === 'jian') line += '（兼祧）';"),
  ("if (n.zhi) line += '（止）';", "if (n.zhi) line += '（止）';"),
  ("download((clanOf().ming || '家族族谱') + '.md', s, 'text/markdown;charset=utf-8');", "download((clanOf().ming || '家系図') + '.md', s, 'text/markdown;charset=utf-8');"),
  # ---- JS：世系录 ----
  ("kids: (n.children || []).map(c => dispName(c.name) + (c.gender === 'f' ? '（女）' : '')).join('、'),", None),
  ("heir: n.heir === 'in' ? '嗣子' : n.heir === 'out' ? '嗣出' : n.heir === 'jian' ? '兼祧' : '',", None),
  ("zhi: n.zhi ? '止' : '',", None),
  ('<!doctype html><html lang="zh">', '<!doctype html><html lang="ja">'),
  ("html += '<h1>' + esc(puTitle()) + ' · 世系录</h1>';", "html += '<h1>' + esc(puTitle()) + ' · 世系録</h1>';"),
  ("'<div class=\"sub\">欧式 · 五世一表 · 导出于 ' + today + ' · 共 ' + rows.length + ' 人</div>'",
   "'<div class=\"sub\">欧式 · 五世一表 · 出力日 ' + today + ' · 計 ' + rows.length + ' 人</div>'"),
  ("if (c.chain)  html += '<div class=\"pre\"><b>源流世系：</b>' + esc(c.chain) + '</div>';", "if (c.chain)  html += '<div class=\"pre\"><b>系統：</b>' + esc(c.chain) + '</div>';"),
  ("if (c.yuanzu) html += '<div class=\"pre\"><b>先祖：</b>' + esc(c.yuanzu) + '</div>';", "if (c.yuanzu) html += '<div class=\"pre\"><b>先祖：</b>' + esc(c.yuanzu) + '</div>';"),
  ("if (c.shizu)  html += '<div class=\"pre\"><b>始祖记：</b>' + esc(c.shizu) + '</div>';", "if (c.shizu)  html += '<div class=\"pre\"><b>始祖記：</b>' + esc(c.shizu) + '</div>';"),
  ("if (c.origin) html += '<div class=\"pre\"><b>家族来源：</b>' + esc(c.origin) + '</div>';", "if (c.origin) html += '<div class=\"pre\"><b>家族の由緒：</b>' + esc(c.origin) + '</div>';"),
  ("html += '<h2>未定世次</h2>';", "html += '<h2>世代未定</h2>';"),
  ("html += '<h2>第' + numToCn(s0) + '世至第' + numToCn(s1) + '世</h2>';", "html += '<h2>第' + numToCn(s0) + '世から第' + numToCn(s1) + '世</h2>';"),
  ("'<table><tr><th>世次</th><th>讳</th><th>字</th><th>号</th><th>行第</th><th>生</th><th>卒</th><th>配偶</th><th>子女</th><th>记</th></tr>'",
   "'<table><tr><th>世代</th><th>諱</th><th>字</th><th>号</th><th>行第</th><th>生</th><th>卒</th><th>配偶</th><th>子</th><th>記</th></tr>'"),
  ("download((clanOf().ming || '家族族谱') + '-世系录-'", "download((clanOf().ming || '家系図') + '-世系録-'"),
  ("toast('世系录已下载（五世一表）：浏览器打开即可查阅或打印');", "toast('世系録をダウンロードしました（五世一表）。ブラウザで閲覧・印刷できます');"),
  # ---- JS：导入/重置/备份 ----
  ("if (!m) throw new Error('这个 HTML 里没有族谱数据');", "if (!m) throw new Error('この HTML に家系図データがありません');"),
  ("if (!validTree(d)) throw new Error('结构不符：需要 {id,name,children[]} 树');", "if (!validTree(d)) throw new Error('構造が不正です：{id,name,children[]} ツリーが必要');"),
  ("toast('已导入「' + f.name + '」，数据已自动保存');", "toast('「' + f.name + '」を読み込みました。データは自動保存済み');"),
  ("alert('导入失败：不是有效的族谱 JSON 文件\\n' + e.message);", "alert('読み込み失敗：有効な家系図 JSON ファイルではありません\\n' + e.message);"),
  ("if (!confirm('确定重置？当前族谱将被清空，恢复到本文件自带的初始数据。\\n（如需保留，先「备份到文件」；误删可用 Ctrl+Z）')) return;",
   "if (!confirm('リセットしますか？現在の家系図は消去され、このファイルの初期データに戻ります。\\n（残す場合は先に「バックアップ保存」。誤削除は Ctrl+Z）')) return;"),
  ("toast('已重置为本文件的初始数据（再次「保存到文件」可固化）');", "toast('このファイルの初期データにリセットしました');"),
  ("const fname = (clanOf().ming || '家族族谱') + '-备份-'", "const fname = (clanOf().ming || '家系図') + '-バックアップ-'"),
  ("toast('备份已下载：' + fname);", "toast('バックアップをダウンロードしました：' + fname);"),
  # ---- JS：画布 ----
  ("throw new Error('画布尚未渲染');", "throw new Error('キャンバスが未描画です');"),
  # ---- JS：导出文件名 / toast ----
  ("return (clanOf().ming || '家族族谱') + '-图-'", "return (clanOf().ming || '家系図') + '-図-'"),
  ("toast('图片已下载（' + cv.width + '×' + cv.height + '）');", "toast('画像をダウンロードしました（' + cv.width + '×' + cv.height + '）');"),
  ("toast('PDF 已下载（' + W + '×' + H + ' pt）');", "toast('PDF をダウンロードしました（' + W + '×' + H + ' pt）');"),
  ("toast('导出失败：' + e.message);", "toast('出力に失敗：' + e.message);", 2),
  # ---- JS：打印 ----
  ("note.textContent = '谱书竖排 · 共 ' + cnt + ' 人' + (s < 1 ? '（整图已按页面缩放 ' + Math.round(s * 100) + '%）' : '');",
   "note.textContent = '譜書縦書き · 計 ' + cnt + ' 人' + (s < 1 ? '（ページに合わせて ' + Math.round(s * 100) + '% に縮小）' : '');"),
  ("if (c.chain)  xuHtml += '<div><b>源流世系：</b>' + esc(c.chain) + '</div>';", "if (c.chain)  xuHtml += '<div><b>系統：</b>' + esc(c.chain) + '</div>';"),
  ("if (c.shizu)  xuHtml += '<div><b>始祖记：</b>' + esc(c.shizu) + '</div>';", "if (c.shizu)  xuHtml += '<div><b>始祖記：</b>' + esc(c.shizu) + '</div>';"),
  ("if (c.origin) xuHtml += '<div><b>家族来源：</b>' + esc(c.origin) + '</div>';", "if (c.origin) xuHtml += '<div><b>家族の由緒：</b>' + esc(c.origin) + '</div>';"),
  # ---- JS：全局 ----
  ("toast('已自动保存，无需手动操作');", "toast('自動保存済み。操作不要です');"),
  ("if (_seededFrom === 'legacy-draft') toast('已从本浏览器的历史数据恢复族谱');", "if (_seededFrom === 'legacy-draft') toast('このブラウザの履歴データから家系図を復元しました');"),
  ("else if (_seededFrom === 'file') toast('自动保存已就绪：编辑即保存，无需手动操作');", "else if (_seededFrom === 'file') toast('自動保存の準備完了：編集は即保存されます');"),
  # ---- 结构默认值 ----
  ("let cfg = { genBase: 1, bookSpouse: true, showSurname: true, cnNum: false, vertical: false };",
   "let cfg = { genBase: 1, bookSpouse: false, showSurname: true, cnNum: false, vertical: false };"),
]

# 続きブロック内の None（変更なし）も除去
JA = [t for t in JA if t[1] is not None]

# ============================================================ 种子数据
SEED_EN = {
  "id": "root", "name": "Family Tree", "spouses": [], "expanded": True, "demo": True,
  "clan": {
    "ming": "Demo Family Tree", "tang": "", "chain": "", "yuanzu": "", "shizu": "", "qianzu": "",
    "origin": "This is demo data. Double-click a name to rename it, click “＋” to add members; “View ▾ → Pedigree preface” edits the tree name, hall name, zibei table and lineage; “File ▾ → Restore backup” imports your own genealogy json."
  },
  "zibei": ["Arthur", "James", "Robert", "Michael"],
  "children": [
    {
      "id": "d1", "name": "James Arthur Miller", "spouses": ["Mary Wilson"], "birth": "1948", "death": "", "note": "", "expanded": True,
      "children": [
        {
          "id": "d2", "name": "Robert James Miller", "spouses": ["Elizabeth Brown"], "birth": "1972", "death": "", "note": "", "expanded": True,
          "children": [
            {
              "id": "d3", "name": "Michael Robert Miller", "spouses": [], "birth": "1998", "death": "", "note": "", "expanded": True,
              "children": [
                { "id": "d4", "name": "Daniel Michael Miller", "spouses": [], "birth": "2024", "death": "", "note": "", "expanded": True, "children": [] }
              ]
            },
            { "id": "d5", "name": "Sarah Miller", "spouses": [], "gender": "f", "birth": "2002", "death": "", "note": "", "expanded": True, "children": [] }
          ]
        },
        { "id": "d6", "name": "Thomas Reed", "spouses": [], "birth": "1975", "death": "", "note": "", "heir": "in", "expanded": True, "children": [] }
      ]
    }
  ]
}

SEED_JA = {
  "id": "root", "name": "家系図", "spouses": [], "expanded": True, "demo": True,
  "clan": {
    "ming": "家系図（デモ）", "tang": "", "chain": "", "yuanzu": "", "shizu": "", "qianzu": "",
    "origin": "これはデモデータです。名前をダブルクリックで変更、「＋」でメンバーを追加できます。「表示 ▾ → 譜序」で譜名・堂号・字輩表・系統を編集、「ファイル ▾ → バックアップ復元」で自分の json を読み込めます。"
  },
  "zibei": ["義", "正", "健", "雄"],
  "children": [
    {
      "id": "d1", "name": "林義郎", "spouses": ["山田千代"], "birth": "1948", "death": "", "note": "", "expanded": True,
      "children": [
        {
          "id": "d2", "name": "林正雄", "spouses": ["佐藤和子"], "birth": "1972", "death": "", "note": "", "expanded": True,
          "children": [
            {
              "id": "d3", "name": "林健太", "spouses": [], "birth": "1998", "death": "", "note": "", "expanded": True,
              "children": [
                { "id": "d4", "name": "林雄介", "spouses": [], "birth": "2024", "death": "", "note": "", "expanded": True, "children": [] }
              ]
            },
            { "id": "d5", "name": "林さくら", "spouses": [], "gender": "f", "birth": "2002", "death": "", "note": "", "expanded": True, "children": [] }
          ]
        },
        { "id": "d6", "name": "森誠一", "spouses": [], "birth": "1975", "death": "", "note": "", "heir": "in", "expanded": True, "children": [] }
      ]
    }
  ]
}

# 母本种子块（正则整体替换）
SEED_RE = re.compile(r'(<script id="__treeData" type="application/json">)[\s\S]*?(\n</script>)')

# ============================================================ 构建
def apply_table(src, table, label, errs):
    for item in table:
        old, new = item[0], item[1]
        want = item[2] if len(item) > 2 else 1
        if isinstance(want, int):
            n = src.count(old)
            if n != want:
                errs.append('[%s] x%d (want x%d): %r' % (label, n, want, old[:70]))
                continue
            src = src.replace(old, new)
        else:  # 'all'
            n = src.count(old)
            if n < 1:
                errs.append('[%s] x0 (want all): %r' % (label, old[:70]))
                continue
            src = src.replace(old, new)
    return src

def build(lang, table, seed, out_name, extra):
    src = io.open(SRC, encoding='utf-8').read()
    errs = []
    # 1) 翻译表
    src = apply_table(src, table, lang, errs)
    # 2) 结构性替换
    for old, new in extra:
        n = src.count(old)
        if n != 1:
            errs.append('[%s/extra] x%d (want x1): %r' % (lang, n, old[:60]))
            continue
        src = src.replace(old, new)
    # 3) 种子整体替换
    src, n = SEED_RE.subn(_seed_sub(seed), src, count=1)
    if n != 1:
        errs.append('[%s] seed block not found' % lang)
    if errs:
        print('==== %s: %d 处失配 ====' % (lang, len(errs)))
        for e in errs: print('  ' + e)
        return False
    io.open(os.path.join(ROOT, out_name), 'w', encoding='utf-8', newline='').write(src)
    # 校验：EN 不应再有用户可见的 CJK（注释一律豁免——代码注释保持中文）
    if lang == 'en':
        left = []
        in_block = False
        in_html_comment = False
        for i, l in enumerate(src.split('\n'), 1):
            work = ''
            j = 0
            while j < len(l):
                if in_block:
                    k = l.find('*/', j)
                    if k == -1: j = len(l)
                    else: in_block = False; j = k + 2
                elif l.startswith('<!--', j):
                    in_html_comment = True; j += 4
                elif in_html_comment:
                    k = l.find('-->', j)
                    if k == -1: j = len(l)
                    else: in_html_comment = False; j = k + 3
                elif l.startswith('/*', j):
                    in_block = True; j += 2
                elif l.startswith('//', j):
                    break
                else:
                    work += l[j]; j += 1
            if re.search(r'[\u3400-\u9fff]', work):
                left.append('%d\t%s' % (i, work.strip()[:100]))
        print('EN CJK residue (non-comment): %d lines' % len(left))
        for x in left[:40]: print('  ' + x)
        if left:
            return False
    print('%s -> %s OK' % (lang, out_name))
    return True

def _dump(obj):
    import json
    return json.dumps(obj, ensure_ascii=False, indent=2)

def _seed_sub(seed):
    def r(m):
        return m.group(1) + '\n' + _dump(seed) + '\n' + m.group(2)
    return r

if __name__ == '__main__':
    base = io.open(SRC, encoding='utf-8').read()
    ok = True
    ok &= build('en', EN, SEED_EN, 'index-en.html', [
      ('<html lang="zh-CN">', '<html lang="en">'),
      ('<title>家族族谱 · 传代树（可编辑）</title>', '<title>Zupu · Family Tree Builder (editable)</title>'),
      ('%E6%97%8F%3C/text%3E', 'T%3C/text%3E'),   # favicon：族 → T
    ])
    ok &= build('ja', JA, SEED_JA, 'index-ja.html', [
      ('<html lang="zh-CN">', '<html lang="ja">'),
      ('<title>家族族谱 · 传代树（可编辑）</title>', '<title>家系図・伝代ツリー（編集可）</title>'),
    ])
    sys.exit(0 if ok else 1)
