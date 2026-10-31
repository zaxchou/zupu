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
  ('<button class="btn" id="btnView" title="查看">查看<', '<button class="btn" id="btnView" title="View">View<'),
  ('<button class="btn" id="btnFile" title="文件">文件<', '<button class="btn" id="btnFile" title="File">File<'),
  ('title="缩小"', 'title="Zoom out"'),
  ('title="放大"', 'title="Zoom in"'),
  ('title="适应屏幕"', 'title="Fit to screen"'),
  ("mi('适应屏幕', '', '', fitToScreen)", "mi('Fit to screen', '', '', fitToScreen)"),
  ('title="恢复 1:1"', 'title="Actual size"'),
  ("mi('实际大小', '', '1:1', resetZoom)", "mi('Actual size', '', '1:1', resetZoom)"),
  ('<span id="statsChip"><b>4</b> 位成员 · 配偶 <b>2</b> · 4 代</span>', '<span id="statsChip"><b>4</b> members · spouses <b>2</b> · 4 gens</span>'),
  ('title="编辑即自动保存（存于本浏览器），无需手动操作"><span class="dot"></span>已保存</button>',
   'title="Edits are saved automatically in this browser — no action needed"><span class="dot"></span>Saved</button>'),
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
  ('>取消</button>', '>Cancel</button>', 7),
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
  ('<tr><td>按住节点拖动</td><td>调长幼次序（横向世代沿上下拖动，其余沿左右拖动；最上或最左为长）</td></tr>', '<tr><td>Drag a node</td><td>Reorder siblings (drag up/down for horizontal generations, otherwise left/right; eldest at the top or left)</td></tr>'),
  ('<tr><td>按住拖到某卡片上停一下</td><td>过继：TA（连同后代整支）成为此人子女，Ctrl+Z 可撤销</td></tr>',
   '<tr><td>Drag onto a card and pause</td><td>Adopt: that person (with all descendants) becomes this member’s child; Ctrl+Z undoes</td></tr>'),
  ('<h4>视图与数据</h4>', '<h4>View & data</h4>'),
  ('<tbody><tr><td><kbd>滚轮</kbd></td><td>以光标为中心缩放；在视觉设置中可关闭，改用 Ctrl＋滚轮缩放</td></tr>', '<tbody><tr><td><kbd>Scroll wheel</kbd></td><td>Zoom around the cursor; turn this off in Visual settings to zoom with Ctrl+scroll instead</td></tr>'),
  ('<tr><td>左键按住空白拖动</td><td>平移画布；触屏单指拖动、双指缩放</td></tr>', '<tr><td>Left-click and drag empty space</td><td>Pan the canvas; on touchscreens, drag with one finger to pan and pinch with two fingers to zoom</td></tr>'),
  ('<tr><td><kbd>Ctrl+F</kbd></td><td>搜索（姓名/配偶/年份/备注），Enter 循环跳转</td></tr>', '<tr><td><kbd>Ctrl+F</kbd></td><td>Search (names/spouses/years/notes), Enter cycles hits</td></tr>'),
  ('<tr><td><kbd>Ctrl+Z</kbd> / <kbd>Ctrl+Y</kbd></td><td>撤销 / 重做</td></tr>', '<tr><td><kbd>Ctrl+Z</kbd> / <kbd>Ctrl+Y</kbd></td><td>Undo / redo</td></tr>'),
  ('<tr><td><kbd>Ctrl+S</kbd></td><td>已自动保存（拦截浏览器另存，无需手动操作）</td></tr>', '<tr><td><kbd>Ctrl+S</kbd></td><td>Already auto-saved (browser save dialog is intercepted)</td></tr>'),
  ('<tr><td>蓝色角标 / 橙色角标</td><td>出生年（自动排长幼）/ 排行称谓（手动排序）</td></tr>', '<tr><td>Blue badge / orange badge</td><td>Birth year (auto order) / birth-order word (manual order)</td></tr>'),
  ('<tr><td>查看 ▾ 视觉设置 · 谱书竖排</td><td>世代成行、名字竖书（右→左）、行左标世数；导出图同款排版</td></tr>', '<tr><td>View ▾ Visual settings · Vertical book layout</td><td>Generations as rows, names written top-to-bottom (right to left), generation labels on the left; same layout in exports</td></tr>'),
  ('<tr><td>查看 ▾ 视觉设置</td><td>世代基准（对齐谱书世数，如勤=23世填13）/ 配偶谱式（丁嘉→丁氏嘉）/ 姓氏周开关 / 世数用汉字</td></tr>', '<tr><td>View ▾ Visual settings</td><td>Generation base (align with the book’s numbering) / spouse book style / surname visibility / number style</td></tr>'),
  ('<tr><td><kbd>▸ N</kbd></td><td>此支已折叠 N 位后代，点击展开</td></tr>', '<tr><td><kbd>▸ N</kbd></td><td>Branch collapsed with N descendants; click to expand</td></tr>'),
  ('<h4 id="__zbTitle">字辈表（蓝框 = 族谱中已出现）</h4>', '<h4 id="__zbTitle">Zibei table (blue = the char appears in the tree)</h4>'),
  ('>知道了</button>', '>Got it</button>'),
  # ---- 显示设置弹窗 ----
  ('<h3 id="__setTitle">视觉设置</h3>', '<h3 id="__setTitle">Visual settings</h3>'),
  ('<button class="btn" id="btnHelp" title="帮助">帮助<', '<button class="btn" id="btnHelp" title="Help">Help<'),
  ('aria-label="关闭"', 'aria-label="Close"', 2),
  ('选中即生效，自动保存在本浏览器。', 'Changes take effect immediately and are saved in this browser.'),
  ('视觉设置未能保存；当前预览仍有效，刷新后可能丢失。', 'Visual settings could not be saved. The current preview still works, but changes may be lost after a reload.'),
  ('重试保存', 'Retry saving'),
  ('<legend>排列方向</legend>', '<legend>Layout direction</legend>'),
  ('<span>从上到下</span>', '<span>Top to bottom</span>'),
  ('<span>从下到上</span>', '<span>Bottom to top</span>'),
  ('<span>从左到右</span>', '<span>Left to right</span>'),
  ('<span>从右到左</span>', '<span>Right to left</span>'),
  ('<legend>配色主题</legend>', '<legend>Colour theme</legend>'),
  ('<span>羊皮纸</span>', '<span>Parchment</span>'),
  ('<span>晴空</span>', '<span>Sky</span>'),
  ('<span>暗色</span>', '<span>Dark</span>'),
  ('<legend>文字排版</legend>', '<legend>Text layout</legend>'),
  ('data-cfg-vertical="false">常规横排</button>', 'data-cfg-vertical="false">Horizontal text</button>'),
  ('data-cfg-vertical="true">谱书竖排</button>', 'data-cfg-vertical="true">Vertical book layout</button>'),
  ('<summary>其他显示项</summary>', '<summary>Other display options</summary>'),
  ('id="__setDone" type="button">关闭</button>', 'id="__setDone" type="button">Close</button>'),
  ('<label class="checkline"><input type="checkbox" id="__cfgWheelZoom"> 滚轮直接缩放（关闭后：滚轮平移，Ctrl＋滚轮缩放）</label>',
   '<label class="checkline"><input type="checkbox" id="__cfgWheelZoom"> Zoom directly with the scroll wheel (off: scroll to pan, Ctrl+scroll to zoom)</label>'),
  ("mi(\'批量添加…\', \'\', \'\', () => openBatchAdd(n))", "mi(\'Batch add…\', \'\', \'\', () => openBatchAdd(n))", 2),
  ('<h3 id="__batchTitle">批量添加</h3>', '<h3 id="__batchTitle">Batch add</h3>'),
  (">子女</button>", ">Child</button>"),
  (">同辈</button>", ">Sibling</button>"),
  ("每行一个名字；也可用逗号、顿号分隔", "One name per line, or separate with commas"),
  ("支持逗号 / 顿号 / 换行分隔 · 先输入=年长", "Commas, dots or newlines separate names; first = eldest"),
  ("\'将添加 \' + batchNames().length + \' 人\'", "\'Will add \' + batchNames().length"),
  ("\'批量添加 · 在「\' + n.name + \'」下添加第一代成员\'", "\'Batch add · first generation under “\' + n.name + \'”\'"),
  ("\'批量添加 · 为「\' + n.name + \'」添加（先输入=年长）\'", "\'Batch add · for “\' + n.name + \'” (first = eldest)\'"),
  ("const what = asSibling ? (parent.id === \'root\' ? \'第一代成员\' : \'同辈\') : \'子女\';", "const what = asSibling ? (parent.id === \'root\' ? \'first-generation members\' : \'siblings\') : \'children\';"),
  ("toast(\'已为「\' + parent.name + \'」添加 \' + names.length + \' 位\' + what + \'（Ctrl+Z 可整批撤销）\');", "toast(\'Added \' + names.length + \' \' + what + \' for “\' + parent.name + \'” (Ctrl+Z undoes the whole batch)\');"),
  (">添加</button>", ">Add</button>", 2),
  ("mi('＋ 父辈…', '', '', () => openAddParent(n))", "mi('＋ Parent…', '', '', () => openAddParent(n))", 1),
  ("<h3 id=\"__parentTitle\">＋ 父辈</h3>", "<h3 id=\"__parentTitle\">＋ Parent</h3>"),
  ("'为「' + n.name + '」添加父辈'", "'Add a parent to \"' + n.name + '\"'"),
  ("'在「' + n.name + '」与其原父辈之间插入一代，「' + n.name + '」及其后代整体下移一辈。'", "'Inserts a generation between \"' + n.name + '\" and its current parent — \"' + n.name + '\" and all descendants shift down one level.'"),
  ("'「' + n.name + '」及其后代将整体下移一辈（成为新父辈的子女）。'", "'\"' + n.name + '\" and all descendants shift down one level (becoming children of the new parent).'"),
  ("同辈一起上移（整辈下移）", "Move siblings up together (whole generation shifts down)"),
  ("父辈姓名", "Parent's name"),
  ("toast('已添加父辈「' + t + '」，「' + n.name + '」' + (withSibs ? '及同辈已' : '已') + '下移一辈');", "toast('Parent \"' + t + '\" added — \"' + n.name + '\"' + (withSibs ? ' and siblings' : '') + ' shifted down one level');"),
  ("if (!pr){ toast('该成员没有上级'); return; }", "if (!pr){ toast('No parent found'); return; }"),

  ("<span id=\"__batchCount\">将添加 0 人</span>", "<span id=\"__batchCount\">Will add 0</span>"),

  ('<label>世代基准 —— 字辈第 1 字对应的谱书世数<input id="__cfgBase" type="number" min="1" max="99" step="1"></label>',
   '<label>Generation base — the book generation number of zibei char #1<input id="__cfgBase" type="number" min="1" max="99" step="1"></label>'),
  ('传统谱书的「世」从<b>始祖一世</b>起算，而字辈往往是后世才议定的。你家谱书「勤」字辈记为<b>廿三世</b>，「勤」是字辈第 11 字，所以「多」字辈=第 <b>13</b> 世：这里填 <b>13</b>，卡片即显示「23世·勤」；填 1 则按应用自算显示「11代」。只改显示，不影响数据。',
   'In traditional genealogy books the generation count starts at <b>1 = the founding ancestor</b>, while the zibei (generation-char) list was often agreed later. Example: if your book records zibei char #11 as <b>generation 23</b>, enter <b>13</b> here (= 23 − 11 + 1) and every card shows book generations; enter 1 to use app-computed counting. Display only — data is never changed.'),
  ('<label class="checkline"><input type="checkbox" id="__cfgSpouse"> 配偶按谱书式显示（丁嘉 → 丁氏嘉；数据仍存原名，搜索不受影响）</label>',
   '<label class="checkline"><input type="checkbox" id="__cfgSpouse"> Spouse names in book style (CJK names only; data keeps the original, search unaffected)</label>'),
  ('<label class="checkline"><input type="checkbox" id="__cfgSurname"> 姓名显示姓氏「<span id="__cfgSurName">—</span>」（关闭 = 按谱书习惯只报名；仅显示层，姓氏随数据自动识别）</label>',
   '<label class="checkline"><input type="checkbox" id="__cfgSurname"> Show the surname “<span id="__cfgSurName">—</span>” in names (off = given names only, as genealogy books often do; display only — the surname is auto-detected from the data)</label>'),
  ('<label class="checkline"><input type="checkbox" id="__cfgCn"> 世数用汉字（廿三世·勤；关闭显示 23世·勤）</label>', '<label class="checkline" style="display:none" aria-hidden="true"><input type="checkbox" id="__cfgCn" tabindex="-1"> Chinese generation numerals</label>'),
  # ---- 谱序弹窗 ----
  ('<h3>谱序 · 宗族源流</h3>', '<h3>Pedigree preface · clan origin</h3>'),
  ('<label>谱名<input id="__clMing" placeholder="如 潮阳泗水周氏族谱"></label>', '<label>Pedigree name<input id="__clMing" placeholder="e.g. Miller Family Genealogy"></label>'),
  ('<label>堂号<input id="__clTang" placeholder="可选，如 四知堂 / 陇西堂"></label>', '<label>Hall name<input id="__clTang" placeholder="optional, e.g. “Hall of Four Knows”"></label>'),
  ('<label>源流世系（远祖 → 近祖，用 — 相连）<input id="__clChain" placeholder="始祖 — 二世 — 三世……"></label>',
   '<label>Lineage (remote → recent ancestors, joined with —)<input id="__clChain" placeholder="Founder — 2nd gen — 3rd gen..."></label>'),
  ('<label>字辈表（空格 / 逗号 / 顿号分隔，按世代顺序；用于自动定代）<textarea id="__clZibei" rows="2" placeholder="如：高 瞻 祁 见 祐 厚 载 翊 常 由"></textarea></label>',
   '<label>Zibei table (generation chars, space/comma separated, in generation order; drives automatic generation numbering)<textarea id="__clZibei" rows="2" placeholder="e.g. Gao Zhan Qi Jian You"></textarea></label>'),
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
  ('当前载入的是示例数据，三选一：', 'Demo data is loaded. Pick one to start:'),
  ('<button type="button" data-wiz="demo"><b>先看看示例</b>明朝皇室世系，真实历史</button>',
   '<button type="button" data-wiz="demo"><b>Explore the demo</b>The real Ming imperial line — play with it freely</button>'),
  ('<button type="button" data-wiz="import"><b>导入之前的备份</b>老用户专用：恢复你以前导出的 json 文件</button>',
   '<button type="button" data-wiz="import"><b>Import a previous backup</b>For returning users: restore a json file you exported before</button>'),
  ('<label>谱名（从空白开始时使用）<input id="__wizMing" placeholder="如 赵氏族谱 / 李氏家谱"></label>',
   '<label>Pedigree name (used when starting from scratch)<input id="__wizMing" placeholder="e.g. Miller Family Tree"></label>'),
  ('<label>堂号（可选）<input id="__wizTang" placeholder="如 四知堂"></label>', '<label>Hall name (optional)<input id="__wizTang" placeholder="optional"></label>'),
  ('<button class="primary" id="__wizGo">从空白开始</button>', '<button class="primary" id="__wizGo">Start from scratch</button>'),
  # ---- 搜索 / 提示条 / 图例 ----
  ('placeholder="搜姓名/配偶/备注…"', 'placeholder="Search names / spouses / notes…"'),
  ('title="上一个（Shift+Enter）"', 'title="Previous (Shift+Enter)"'),
  ('title="下一个（Enter）"', 'title="Next (Enter)"'),
  ('title="关闭（Esc）"', 'title="Close (Esc)"', 2),
  ('title="节点下方常驻「＋」或右键=操作菜单 · 双击姓名=改名 · 双击备注行=档案 · 拖节点=调次序或过继 · 点头像=看照片 · 滚轮=缩放（视觉设置可关闭） · 左键拖空白=平移 · 编辑自动保存 · 详细说明见「帮助」菜单">操作：<b>＋/右键</b>=菜单 · <b>双击</b>=改名/档案 · <b>拖节点</b>=调次序或过继 · <b>点头像</b>=看照片 · <b>滚轮</b>=缩放（设置可关闭） · 左键拖空白=平移 · 自动保存 · 更多见「帮助」菜单', 'title="The “＋” under a node or right-click = action menu · double-click name = rename · double-click meta line = profile · drag a node = reorder or adopt · click an avatar = view the photo · scroll = zoom (can be turned off in Visual settings) · left-click and drag empty space = pan · auto-save · see the “Help” menu">Edit: <b>＋/right-click</b>=menu · <b>double-click</b>=rename/profile · <b>drag node</b>=reorder or adopt · <b>click avatar</b>=view photo · <b>scroll</b>=zoom (can be turned off in settings) · left-drag empty space=pan · auto-save · more under “Help”'),
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
  # 姓氏算法常量保持原值，以 Unicode 转义避免被 EN 文案残留检查误报。
  ("const CS_SURN = '欧阳司马诸葛上官皇甫尉迟慕容令狐宇文轩辕东方端木长孙公孙淳于单于太叔申屠公冶宗政濮阳仲孙钟离鲜于闾丘子车亓官巫马公西漆雕乐正宰父谷梁拓跋夹谷南宫西门东郭呼延第五';",
   "const CS_SURN = '" + '欧阳司马诸葛上官皇甫尉迟慕容令狐宇文轩辕东方端木长孙公孙淳于单于太叔申屠公冶宗政濮阳仲孙钟离鲜于闾丘子车亓官巫马公西漆雕乐正宰父谷梁拓跋夹谷南宫西门东郭呼延第五'.encode('unicode_escape').decode('ascii') + "';"),
  ("if (s.indexOf('氏') > -1) return s;", r"if (s.indexOf('\u6c0f') > -1) return s;"),
  ("return sur + '氏' + s.slice(sur.length);", r"return sur + '\u6c0f' + s.slice(sur.length);"),
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
  ("const text = numToCn(g + genOffset()) + genUnit() + (zbRows[g - 1] ? '·' + zbRows[g - 1] : '');", "const text = 'Gen ' + (g + genOffset()) + (zbRows[g - 1] ? ' · ' + zbRows[g - 1] : '');"),
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
  ("ctxMenu.appendChild(mi(n.expanded ? '折叠此支' : '展开此支', '', '', () => toggleExpand(n)));", "ctxMenu.appendChild(mi(n.expanded ? 'Collapse branch' : 'Expand branch', '', '', () => toggleExpand(n)));"),
  ("ctxMenu.appendChild(mi('改名', '', 'F2', () => editName(n)));", "ctxMenu.appendChild(mi('Rename', '', 'F2', () => editName(n)));"),
  ("ctxMenu.appendChild(mi('档案', '', 'Ctrl+I', () => editDetails(n)));", "ctxMenu.appendChild(mi('Profile', '', 'Ctrl+I', () => editDetails(n)));"),
  ("ctxMenu.appendChild(mi('删除', 'danger', '', () => deleteNode(n)));", "ctxMenu.appendChild(mi('Delete', 'danger', '', () => deleteNode(n)));"),
  ("m.appendChild(mi('全展开', '', '', () => expandAll(true)));", "m.appendChild(mi('Expand all', '', '', () => expandAll(true)));"),
  ("m.appendChild(mi('全折叠', '', '', () => expandAll(false)));", "m.appendChild(mi('Collapse all', '', '', () => expandAll(false)));"),
  ("m.appendChild(mi('谱序…', '', '', openClan, '谱名 / 堂号 / 源流 / 字辈表 / 始祖记'));", "m.appendChild(mi('Preface…', '', '', openClan, 'Clan name / hall / origin / zibei table / founding ancestor'));"),
  ("m.appendChild(mi('视觉设置…', '', '', openSettings));", "m.appendChild(mi('Visual settings…', '', '', openSettings));"),
  ("mi('帮助 / 快捷键', '', '', openHelp)", "mi('Help / shortcuts', '', '', openHelp)"),
  ("mi(IS_XHS ? '保存图片到相册' : '导出图片', '', 'png', exportPNG));", "mi(IS_XHS ? 'Save to album' : 'Export image', '', 'png', exportPNG));"),
  ("mi('复制备份', '', '', function(){", "mi('Copy backup', '', '', function(){"),
  ("mi('粘贴导入备份', '', '', pasteImport));", "mi('Paste to restore', '', '', pasteImport));"),
  ("mi('备份到文件', '', 'json', backupToFile, '导出 json 备份（含成员照片缩略图）：换电脑 / 防清缓存'));", "mi('Back up to file', '', 'json', backupToFile, 'Export a JSON backup (with member photo thumbnails): move computers / guard against cleared storage'));"),
  ("mi('恢复备份', '', 'json', () => document.getElementById('__importFile').click(), '导入 json 备份（也支持旧版 HTML）'));", "mi('Restore backup', '', 'json', () => document.getElementById('__importFile').click(), 'Import a JSON backup (old HTML files also supported)'));"),
  ("mi('导出 PDF', '', '', exportPDF, '图谱排版，单页'));", "mi('Export PDF', '', '', exportPDF, 'Chart layout, single page'));"),
  ("mi('导出世系录', '', '五世一表', exportShixilu, '欧式表格：浏览器打开即可打印'));", "mi('Export lineage tables', '', '5 gens each', exportShixilu, 'Classic grid: open in browser and print'));"),
  ("mi('导出 Markdown', '', 'md', exportMarkdown));", "mi('Export Markdown', '', 'md', exportMarkdown));"),
  ("mi('打印', '', '', () => window.print(), '跟随当前视图排版'));", "mi('Print', '', '', () => window.print(), 'Follows the current view layout'));"),
  ("mi('按出生年重排', '', '', actSortByBirth));", "mi('Sort by birth year', '', '', actSortByBirth));"),
  ("mi('重置数据', 'danger', '', resetData, '清空并恢复为示例谱'));", "mi('Reset data', 'danger', '', resetData, 'Clear and restore the demo tree'));"),
  # ---- JS：字辈角标 ----
  ("'字辈表（第' + range + genUnit() + '，蓝框 = 族谱中已出现）';", "'Zibei table (gens ' + range + '; blue = appears in tree)';"),
  ("d.innerHTML = esc(z || '·') + '<small>第' + genLabel(i + 1) + '</small>';",
   "d.innerHTML = esc(z || '·') + '<small>' + genLabel(i + 1) + '</small>';"),
  ("d.title = '第' + genLabel(i + 1) + '字辈「' + (z || '?') + '」' + (all.includes(z) ? '（族谱中已出现）' : '');",
   "d.title = genLabel(i + 1) + ' zibei char: “' + (z || '?') + '”' + (all.includes(z) ? ' (appears in tree)' : '');"),
  ("'<span class=\"help-note\">本文件尚未配置字辈表</span>'", "'<span class=\"help-note\">No zibei table configured in this file</span>'"),
  ("FAM_SUR || '（自动识别）'", "FAM_SUR || '(auto-detected)'"),
  # ---- JS：设置/视图 toast ----
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
  ("toast('「' + v + '」已是 ' + n.name + ' 的配偶，无需重复添加');", "toast(v + ' is already a spouse of ' + n.name);"),
  ("toast('已为 ' + n.name + ' 添加配偶「' + v + '」，继续点「＋配偶」可再加');", "toast('Added spouse ' + v + ' for ' + n.name + ' — click “＋ Spouse” again to add more');"),
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
  ('>确定</button>', '>OK</button>'),
  ('<h3>粘贴备份 json 导入</h3>', '<h3>Paste backup JSON to import</h3>'),
  ('id="__pasteOk">导入</button>', 'id="__pasteOk">Import</button>'),
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
  ("if (!validTree(d)) throw new Error('结构不符：需要 {id,name,children[]} 树');", "if (!validTree(d)) throw new Error('Unexpected structure: need a {id,name,children[]} tree');", 2),
  ("toast('已导入「' + f.name + '」，数据已自动保存');", "toast('Imported “' + f.name + '” — data saved automatically');"),
  ("? '已导入「' + f.name + '」，数据已自动保存，照片原图已写入本机照片库（' + ok + ' 张）'",
   "? 'Imported “' + f.name + '” — data saved automatically; ' + ok + ' original photos written to the local photo library'"),
  (": '已导入「' + f.name + '」，数据已自动保存，照片库不可用，仅缩略图可用');",
   ": 'Imported “' + f.name + '” — data saved automatically; photo library unavailable — thumbnails only');"),
  ("alert('导入失败：不是有效的族谱 JSON 文件\\n' + e.message);", "alert('Import failed: not a valid genealogy JSON file\\n' + e.message);", 2),
  ("if (!confirm('确定重置？当前族谱将被清空，恢复到本文件自带的初始数据。\\n（如需保留，先「备份到文件」；误删可用 Ctrl+Z）')) return;",
   "if (!confirm('Reset? The current tree will be cleared and restored to this file’s initial data.\\n(To keep it, “Backup to file” first; Ctrl+Z undoes an accidental reset)')) return;"),
  ("toast('已重置为本文件的初始数据（再次「保存到文件」可固化）');", "toast('Reset to this file’s initial data (use “Backup to file” to persist anything)');"),
  ("const fname = (clanOf().ming || '家族族谱') + '-备份-'", "const fname = (clanOf().ming || 'Family Tree') + '-backup-'"),
  (": '备份已下载：' + fname);", ": 'Backup downloaded: ' + fname);"),
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
  (".catch(e => toast('导出失败：' + ((e && e.message) || e)));", ".catch(e => toast('Export failed: ' + ((e && e.message) || e)));", 2),
  # ---- JS：打印 ----
  ("note.textContent = (cfg.vertical ? '谱书竖排' : '常规横排') + ' · 共 ' + cnt + ' 人' + (s < 1 ? '（整图已按页面缩放 ' + Math.round(s * 100) + '%）' : '');", "note.textContent = (cfg.vertical ? 'Vertical book layout' : 'Horizontal text') + ' · ' + cnt + ' people' + (s < 1 ? ' (scaled to ' + Math.round(s * 100) + '% for the page)' : '');"),
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
  ('genBase: 1, bookSpouse: true, showSurname: true', 'genBase: 1, bookSpouse: false, showSurname: true'),
  # ---- 触摸手势提示 / 输入弹窗 / 文本弹窗 / 粘贴导入 / XHS 提示 ----
  ('<div id="__gestureHint">单指拖动平移 · 双指捏合缩放 · 长按卡片更多操作</div>',
   '<div id="__gestureHint">One finger: pan · Pinch: zoom · Long-press a card for more</div>'),
  ('<h3 id="__uipTitle">输入</h3>', '<h3 id="__uipTitle">Input</h3>'),
  ('<h3 id="__textTitle">文本</h3>', '<h3 id="__textTitle">Text</h3>'),
  ('<button id="__textSel">全选</button><button class="primary" id="__textOk">关闭</button>',
   '<button id="__textSel">Select all</button><button class="primary" id="__textOk">Close</button>'),
  ("toast('已导入粘贴的备份数据，已自动保存');", "toast('Pasted backup imported and auto-saved');"),
  ("? '已导入粘贴的备份数据，已自动保存，照片原图已写入本机照片库（' + ok + ' 张）'",
   "? 'Pasted backup imported and auto-saved; ' + ok + ' original photos written to the local photo library'"),
  (": '已导入粘贴的备份数据，已自动保存，照片库不可用，仅缩略图可用');",
   ": 'Pasted backup imported and auto-saved; photo library unavailable — thumbnails only');"),
  ("uiPrompt('修改姓名：', n.name).then(function(t){", "uiPrompt('Rename:', n.name).then(function(t){"),
  ("uiPrompt('为「' + n.name + '」添加第 ' + nth + ' 位配偶姓名：\\n（如需改名/移除某位配偶，直接双击图上该配偶的名字）').then(function(t){",
   "uiPrompt('Add spouse #' + nth + ' for “' + n.name + '”:\\n(to rename or remove a spouse, double-click the spouse name on the card)').then(function(t){"),
  ("uiPrompt('修改「' + n.name + '」的第 ' + (i + 1) + ' 位配偶：\\n（清空并确定 = 移除这位配偶）', cur).then(function(t){",
   "uiPrompt('Edit spouse #' + (i + 1) + ' of “' + n.name + '”:\\n(clear and OK = remove this spouse)', cur).then(function(t){"),
  ("uiPrompt('添加一位与「' + n.name + '」同辈的成员（' + (p.id === 'root' ? '第一代' : '同父母') + '）：').then(function(t){",
   "uiPrompt('Add a sibling of “' + n.name + '” (' + (p.id === 'root' ? 'first generation' : 'same parents') + '):').then(function(t){"),
  ("if (IS_XHS){ toast('小工具内不支持下载文件：请使用电脑网页版导出'); return; }",
   "if (IS_XHS){ toast('Downloads are not available in the mini tool: export from the desktop web version'); return; }"),
  ("toast('当前环境不支持保存到相册')", "toast('Saving to album is not supported here')"),
  ("toast('正在保存图片…');", "toast('Saving image…');"),
  ("toast('图片已保存到相册')", "toast('Image saved to album')"),
  ("toast('保存失败：' + ((e && e.errMsg) || e));", "toast('Save failed: ' + ((e && e.errMsg) || e));"),
  ("toast('保存失败：' + e.message);", "toast('Save failed: ' + e.message);"),
  ("showTextModal('备份文本：点击「全选」后手动复制'",
   "showTextModal('Backup text: tap “Select all”, then copy manually'"),
  # ---- 成员照片（第一期）----
  ('title="成员照片（方形预览）"', 'title="Member photo (square preview)"'),
  ('id="__dmPhotoAdd">添加照片</button>', 'id="__dmPhotoAdd">Add photo</button>'),
  ('id="__dmPhotoDel" style="display:none">删除照片</button>', 'id="__dmPhotoDel" style="display:none">Remove photo</button>'),
  ('alt="成员照片"', 'alt="Member photo"', 2),
  ('<h3 id="__photoImpTitle">照片导入结果</h3>', '<h3 id="__photoImpTitle">Photo import results</h3>'),
  ('id="__photoImpOk">导入</button>', 'id="__photoImpOk">Import</button>'),
  ('<tr><td>成员照片</td><td>「档案」里添加照片后卡片显示圆形头像，点头像看大图；文件 ▾ 可按文件夹批量导入照片，备份（含照片原图）换电脑不丢原图</td></tr>',
   '<tr><td>Member photos</td><td>Once a photo is added in the profile, cards show a round avatar — click an avatar to view it large; File ▾ can batch-import photos from a folder, and “Backup (with original photos)” keeps originals when you switch computers</td></tr>'),
  ('<label class="checkline"><input type="checkbox" id="__cfgPhotos"> 成员照片头像（卡片显示照片/剪影，点头像看大图）</label>',
   '<label class="checkline"><input type="checkbox" id="__cfgPhotos"> Member photo avatars (cards show photo/silhouette; click an avatar to view large)</label>'),
  # 姓氏算法常量同款约定：正则里的中文「副本/复件/拷贝」用 Unicode 转义，避免 EN 残留检查误报
  (r"b = b.replace(/(\s*[-－—]\s*\d{1,3}\s*|\s*[（(]\s*\d{1,3}\s*[）)]|\s*[（(]\s*\d+\s*[）)]|\s*(副本|复件|拷贝|copy|new)\s*)+$/i, '').trim();",
   r"b = b.replace(/(\s*[-－—]\s*\d{1,3}\s*|\s*[（(]\s*\d{1,3}\s*[）)]|\s*[（(]\s*\d+\s*[）)]|\s*(\u526f\u672c|\u590d\u4ef6|\u62f7\u8d1d|copy|new)\s*)+$/i, '').trim();"),
  ("av.title = '点头像看大图';", "av.title = 'Click to view larger';"),
  ("av.title = '在「档案」里可添加照片';", "av.title = 'Add a photo in the profile';"),
  ("addB.textContent = '更换照片';", "addB.textContent = 'Replace photo';"),
  ("addB.textContent = '添加照片';", "addB.textContent = 'Add photo';"),
  ("toast('已删除「' + n.name + '」的照片');", "toast('Removed the photo of ' + n.name);"),
  ("toast('照片处理中…');", "toast('Processing photo…');"),
  ("toast('已为「' + n.name + '」设置照片');", "toast('Photo set for ' + n.name);"),
  ("}).catch(() => toast('照片读取失败：请换一张图片文件'));", "}).catch(() => toast('Could not read the photo: try another image file'));"),
  ("new Error('照片存储不可用')", "new Error('Photo storage unavailable')"),
  ("new Error('照片读取失败')", "new Error('Photo read failed')"),
  ("new Error('图片解码失败')", "new Error('Image decoding failed')"),
  ("new Error('图片尺寸为 0')", "new Error('Image size is 0')"),
  ("new Error('文件读取失败')", "new Error('File read failed')"),
  ("m.appendChild(mi('备份（含照片原图）', '', 'json', () => backupToFile(true), '在备份 json 里附上全部原图，换电脑后点头像仍可看大图（文件更大）'));",
   "m.appendChild(mi('Backup (with original photos)', '', 'json', () => backupToFile(true), 'Attach all original photos to the backup json — photos still open large after switching computers (larger file)'));"),
  ("m.appendChild(mi('导入照片文件夹…', '', '', () => document.getElementById('__photoDirInput').click(), '按文件名匹配成员姓名，批量设置照片'));",
   "m.appendChild(mi('Import photo folder…', '', '', () => document.getElementById('__photoDirInput').click(), 'Match members by file name and set photos in bulk'));"),
  ("sel.appendChild(new Option('跳过（不导入）', ''));", "sel.appendChild(new Option('Skip (do not import)', ''));"),
  ("return m.name + (dupBaseNames[m.name] && p ? '（' + (p.id === 'root' ? '第一代' : p.name + '之子') + '）' : '');",
   "return m.name + (dupBaseNames[m.name] && p ? ' (' + (p.id === 'root' ? '1st generation' : 'son of ' + p.name) + ')' : '');"),
  ("'成功匹配 ' + auto + ' 张（确认后写入）'", "auto + ' auto-matched (written on confirm)'"),
  ("' · 需人工确认 ' + list.children.length + ' 张'", "' · ' + list.children.length + ' to review manually'"),
  ("'（共扫描 ' + total + ' 张；确认导入时才读取压缩，跳过零成本）';", "' (' + total + ' photos scanned in total; compression runs only on confirm, skipping costs nothing)';"),
  ("document.getElementById('__photoImpOk').textContent = '确认导入';", "document.getElementById('__photoImpOk').textContent = 'Confirm import';"),
  ("if (!imgs.length){ toast('该文件夹里没有图片文件'); return; }", "if (!imgs.length){ toast('No image files in that folder'); return; }"),
  ("toast('正在读取并压缩照片（' + cnt + ' 张）…');", "toast('Reading and compressing photos (' + cnt + ')…');"),
  ("toast('已取消，未写入任何照片');", "toast('Cancelled — no photos written');"),
  ("if (!cnt){ toast('未选择任何成员，未写入照片'); return; }", "if (!cnt){ toast('No member selected — no photos written'); return; }"),
  ("toast('已为 ' + (cnt - bad) + ' 位成员设置照片（同一人已有照片 = 更换）'",
   "toast('Set photos for ' + (cnt - bad) + ' member(s) (existing photo = replaced)'"),
  ("+ (bad ? '，' + bad + ' 张读取失败' : ''));", "+ (bad ? ', ' + bad + ' failed to read' : ''));"),
  ("? '备份已下载（含 ' + Object.keys(full).length + ' 张照片原图）：' + fname", "? 'Backup downloaded (with ' + Object.keys(full).length + ' original photos): ' + fname"),
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
  ('<button class="btn" id="btnView" title="查看">查看<', '<button class="btn" id="btnView" title="表示">表示<'),
  ('<button class="btn" id="btnFile" title="文件">文件<', '<button class="btn" id="btnFile" title="ファイル">ファイル<'),
  ('title="缩小"', 'title="縮小"'),
  ('title="放大"', 'title="拡大"'),
  ('title="适应屏幕"', 'title="画面に合わせる"'),
  ("mi('适应屏幕', '', '', fitToScreen)", "mi('画面に合わせる', '', '', fitToScreen)"),
  ('title="恢复 1:1"', 'title="実際のサイズ"'),
  ("mi('实际大小', '', '1:1', resetZoom)", "mi('実際のサイズ', '', '1:1', resetZoom)"),
  ('<span id="statsChip"><b>4</b> 位成员 · 配偶 <b>2</b> · 4 代</span>', '<span id="statsChip"><b>4</b>人 · 配偶者 <b>2</b> · 4代</span>'),
  ('title="编辑即自动保存（存于本浏览器），无需手动操作"><span class="dot"></span>已保存</button>',
   'title="編集は自動保存されます（このブラウザに保存）"><span class="dot"></span>保存済み</button>'),
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
  ('<tr><td>按住节点拖动</td><td>调长幼次序（横向世代沿上下拖动，其余沿左右拖动；最上或最左为长）</td></tr>', '<tr><td>ノードをドラッグ</td><td>兄弟姉妹の順序を変更（世代が横方向なら上下、それ以外は左右。上端または左端が年長）</td></tr>'),
  ('<tr><td>按住拖到某卡片上停一下</td><td>过继：TA（连同后代整支）成为此人子女，Ctrl+Z 可撤销</td></tr>',
   '<tr><td>カードに重ねて一時停止</td><td>養縁：その人（子孫全員ごと）がこの人の子になります。Ctrl+Z で取消</td></tr>'),
  ('<h4>视图与数据</h4>', '<h4>表示とデータ</h4>'),
  ('<tbody><tr><td><kbd>滚轮</kbd></td><td>以光标为中心缩放；在视觉设置中可关闭，改用 Ctrl＋滚轮缩放</td></tr>', '<tbody><tr><td><kbd>スクロール</kbd></td><td>カーソル位置を中心に拡大縮小。表示設定でオフにすると Ctrl＋スクロールで拡大縮小</td></tr>'),
  ('<tr><td>左键按住空白拖动</td><td>平移画布；触屏单指拖动、双指缩放</td></tr>', '<tr><td>空白を左ボタンでドラッグ</td><td>キャンバスを移動。タッチ操作は 1 本指でドラッグ移動、2 本指のピンチで拡大縮小</td></tr>'),
  ('<tr><td><kbd>Ctrl+F</kbd></td><td>搜索（姓名/配偶/年份/备注），Enter 循环跳转</td></tr>', '<tr><td><kbd>Ctrl+F</kbd></td><td>検索（氏名/配偶者/年/備考）。Enter で次へ</td></tr>'),
  ('<tr><td><kbd>Ctrl+Z</kbd> / <kbd>Ctrl+Y</kbd></td><td>撤销 / 重做</td></tr>', '<tr><td><kbd>Ctrl+Z</kbd> / <kbd>Ctrl+Y</kbd></td><td>元に戻す / やり直す</td></tr>'),
  ('<tr><td><kbd>Ctrl+S</kbd></td><td>已自动保存（拦截浏览器另存，无需手动操作）</td></tr>', '<tr><td><kbd>Ctrl+S</kbd></td><td>自動保存済み（ブラウザの保存ダイアログは出ません）</td></tr>'),
  ('<tr><td>蓝色角标 / 橙色角标</td><td>出生年（自动排长幼）/ 排行称谓（手动排序）</td></tr>', '<tr><td>青色バッジ / オレンジ色バッジ</td><td>生年（自動並び）/ 誕生順（手動並び）</td></tr>'),
  ('<tr><td>查看 ▾ 视觉设置 · 谱书竖排</td><td>世代成行、名字竖书（右→左）、行左标世数；导出图同款排版</td></tr>', '<tr><td>表示 ▾ 表示設定 · 譜書縦書き</td><td>世代を行でまとめ、名を縦書き（右→左）、行左に世代を表示。出力も同じ体裁</td></tr>'),
  ('<tr><td>查看 ▾ 视觉设置</td><td>世代基准（对齐谱书世数，如勤=23世填13）/ 配偶谱式（丁嘉→丁氏嘉）/ 姓氏周开关 / 世数用汉字</td></tr>', '<tr><td>表示 ▾ 表示設定</td><td>世代基準（譜書の世代数に合わせる）/ 配偶者の譜式 / 姓氏の表示 / 世代数の漢数字</td></tr>'),
  ('<tr><td><kbd>▸ N</kbd></td><td>此支已折叠 N 位后代，点击展开</td></tr>', '<tr><td><kbd>▸ N</kbd></td><td>この支は N 人の子孫ごと折りたたまれています。クリックで展開</td></tr>'),
  ('<h4 id="__zbTitle">字辈表（蓝框 = 族谱中已出现）</h4>', '<h4 id="__zbTitle">字輩表（青枠 = 譜に現れる字）</h4>'),
  ('>知道了</button>', '>閉じる</button>'),
  # ---- 显示设置弹窗 ----
  ('<h3 id="__setTitle">视觉设置</h3>', '<h3 id="__setTitle">表示設定</h3>'),
  ('<button class="btn" id="btnHelp" title="帮助">帮助<', '<button class="btn" id="btnHelp" title="ヘルプ">ヘルプ<'),
  ('aria-label="关闭"', 'aria-label="閉じる"', 2),
  ('选中即生效，自动保存在本浏览器。', '選択するとすぐに反映され、このブラウザに自動保存されます。'),
  ('视觉设置未能保存；当前预览仍有效，刷新后可能丢失。', '表示設定を保存できませんでした。現在のプレビューは有効ですが、再読み込みすると変更が失われる可能性があります。'),
  ('重试保存', '保存を再試行'),
  ('<legend>排列方向</legend>', '<legend>配置方向</legend>'),
  ('<span>从上到下</span>', '<span>上から下</span>'),
  ('<span>从下到上</span>', '<span>下から上</span>'),
  ('<span>从左到右</span>', '<span>左から右</span>'),
  ('<span>从右到左</span>', '<span>右から左</span>'),
  ('<legend>配色主题</legend>', '<legend>配色テーマ</legend>'),
  ('<span>羊皮纸</span>', '<span>羊皮紙</span>'),
  ('<span>晴空</span>', '<span>晴空</span>'),
  ('<span>暗色</span>', '<span>ダーク</span>'),
  ('<legend>文字排版</legend>', '<legend>文字組み</legend>'),
  ('data-cfg-vertical="false">常规横排</button>', 'data-cfg-vertical="false">通常の横書き</button>'),
  ('data-cfg-vertical="true">谱书竖排</button>', 'data-cfg-vertical="true">譜書縦書き</button>'),
  ('<summary>其他显示项</summary>', '<summary>その他の表示項目</summary>'),
  ('id="__setDone" type="button">关闭</button>', 'id="__setDone" type="button">閉じる</button>'),
  ('<label class="checkline"><input type="checkbox" id="__cfgWheelZoom"> 滚轮直接缩放（关闭后：滚轮平移，Ctrl＋滚轮缩放）</label>',
   '<label class="checkline"><input type="checkbox" id="__cfgWheelZoom"> スクロールだけで拡大縮小（オフ：スクロールで移動、Ctrl＋スクロールで拡大縮小）</label>'),
  ("mi(\'批量添加…\', \'\', \'\', () => openBatchAdd(n))", "mi(\'一括追加…\', \'\', \'\', () => openBatchAdd(n))", 2),
  ('<h3 id="__batchTitle">批量添加</h3>', '<h3 id="__batchTitle">一括追加</h3>'),
  (">子女</button>", ">子</button>"),
  (">同辈</button>", ">兄弟姉妹</button>"),
  ("每行一个名字；也可用逗号、顿号分隔", "1 行に 1 名。カンマ・読点区切りも可"),
  ("支持逗号 / 顿号 / 换行分隔 · 先输入=年长", "カンマ・読点・改行で区切り · 先に入力した人が年長"),
  ("\'将添加 \' + batchNames().length + \' 人\'", "\'追加する人数：\' + batchNames().length"),
  ("\'批量添加 · 在「\' + n.name + \'」下添加第一代成员\'", "\'一括追加 · 「\' + n.name + \'」の第一世代に追加\'"),
  ("\'批量添加 · 为「\' + n.name + \'」添加（先输入=年长）\'", "\'一括追加 · 「\' + n.name + \'」に追加（先頭=年長）\'"),
  ("const what = asSibling ? (parent.id === \'root\' ? \'第一代成员\' : \'同辈\') : \'子女\';", "const what = asSibling ? (parent.id === \'root\' ? \'第一世代メンバー\' : \'兄弟姉妹\') : \'子\';"),
  ("toast(\'已为「\' + parent.name + \'」添加 \' + names.length + \' 位\' + what + \'（Ctrl+Z 可整批撤销）\');", "toast(\'「\' + parent.name + \'」に \' + names.length + \' 人（\' + what + \'）を追加しました（Ctrl+Z で一括取り消し）\');"),
  (">添加</button>", ">追加</button>", 2),
  ("mi('＋ 父辈…', '', '', () => openAddParent(n))", "mi('＋ 親世代…', '', '', () => openAddParent(n))", 1),
  ("<h3 id=\"__parentTitle\">＋ 父辈</h3>", "<h3 id=\"__parentTitle\">＋ 親世代</h3>"),
  ("'为「' + n.name + '」添加父辈'", "'「' + n.name + '」に親世代を追加'"),
  ("'在「' + n.name + '」与其原父辈之间插入一代，「' + n.name + '」及其后代整体下移一辈。'", "'「' + n.name + '」と現在の親の間に一世代を挿入。「' + n.name + '」とその子孫は一世代下がります。'"),
  ("'「' + n.name + '」及其后代将整体下移一辈（成为新父辈的子女）。'", "'「' + n.name + '」とその子孫は一世代下がります（新しい親世代の子になります）。'"),
  ("同辈一起上移（整辈下移）", "兄弟姉妹も一緒に上へ（世代ごとに下がる)"),
  ("父辈姓名", "父世代の氏名"),
  ("toast('已添加父辈「' + t + '」，「' + n.name + '」' + (withSibs ? '及同辈已' : '已') + '下移一辈');", "toast('父世代「' + t + '」を追加。「' + n.name + '」' + (withSibs ? 'と兄弟姉妹は' : '') + '一世代下がりました');"),
  ("if (!pr){ toast('该成员没有上级'); return; }", "if (!pr){ toast('上位のメンバーが見つかりません'); return; }"),

  ("<span id=\"__batchCount\">将添加 0 人</span>", "<span id=\"__batchCount\">追加する人数：0</span>"),

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
  ('<label>字辈表（空格 / 逗号 / 顿号分隔，按世代顺序；用于自动定代）<textarea id="__clZibei" rows="2" placeholder="如：高 瞻 祁 见 祐 厚 载 翊 常 由"></textarea></label>',
   '<label>字輩表（空白/読点/カンマ区切り、世代順。自動世代判定に使用）<textarea id="__clZibei" rows="2" placeholder="例：高 瞻 祁 見 祐"></textarea></label>'),
  ('<label>先祖<input id="__clYuan" placeholder="如 周敦颐，字茂叔，号濂溪（湖南道州）"></label>', '<label>先祖<input id="__clYuan" placeholder="例：遠祖の氏名・略伝"></label>'),
  ('<label>始祖记<textarea id="__clShi" rows="3" placeholder="一世祖承节公讳宣道……二世祖朝奉公讳景一……"></textarea></label>',
   '<label>始祖記<textarea id="__clShi" rows="3" placeholder="一世祖：…  二世祖：…"></textarea></label>'),
  ('<label>始迁祖<input id="__clQian" placeholder="如 （南宋）宣，字承节"></label>', '<label>始遷祖<input id="__clQian" placeholder="例：江戸初期に○○へ移住"></label>'),
  ('<label>家族来源<textarea id="__clOrigin" rows="5" placeholder="宗支源流叙述……"></textarea></label>', '<label>家族の由緒<textarea id="__clOrigin" rows="5" placeholder="この家支の由緒…"></textarea></label>'),
  ('<button class="primary" id="__clSave">保存</button>', '<button class="primary" id="__clSave">保存</button>'),
  ('>取消</button>', '>キャンセル</button>', 7),
  # ---- 向导 ----
  ('<h3>欢迎使用家族族谱</h3>', '<h3>家系図へようこそ</h3>'),
  ('这是一个<b>本地优先</b>的单文件应用：数据只存在<b>你的浏览器</b>里，不联网、无账号、编辑即自动保存。',
   'これは<b>ローカルファースト</b>のシングルファイルアプリです。データは<b>あなたのブラウザ</b>にのみ保存され、ネット接続もアカウントも不要、編集は自動保存されます。'),
  ('当前载入的是示例数据，三选一：', '現在はデモデータが読み込まれています。三つから選んでください：'),
  ('<button type="button" data-wiz="demo"><b>先看看示例</b>明朝皇室世系，真实历史</button>',
   '<button type="button" data-wiz="demo"><b>まずデモを見る</b>明皇室の実在系譜。自由にいじってOK</button>'),
  ('<button type="button" data-wiz="import"><b>导入之前的备份</b>老用户专用：恢复你以前导出的 json 文件</button>',
   '<button type="button" data-wiz="import"><b>以前のバックアップから復元</b>以前書き出した json ファイルを読み込む</button>'),
  ('<label>谱名（从空白开始时使用）<input id="__wizMing" placeholder="如 赵氏族谱 / 李氏家谱"></label>',
   '<label>譜名（白紙から始めるときに使用）<input id="__wizMing" placeholder="例：○○家系図"></label>'),
  ('<label>堂号（可选）<input id="__wizTang" placeholder="如 四知堂"></label>', '<label>堂号（任意）<input id="__wizTang" placeholder="例：陇西堂"></label>'),
  ('<button class="primary" id="__wizGo">从空白开始</button>', '<button class="primary" id="__wizGo">白紙から始める</button>'),
  # ---- 搜索 / 提示条 / 图例 ----
  ('placeholder="搜姓名/配偶/备注…"', 'placeholder="氏名・配偶者・備考を検索…"'),
  ('title="上一个（Shift+Enter）"', 'title="前へ（Shift+Enter）"'),
  ('title="下一个（Enter）"', 'title="次へ（Enter）"'),
  ('title="关闭（Esc）"', 'title="閉じる（Esc）"', 2),
  ('title="节点下方常驻「＋」或右键=操作菜单 · 双击姓名=改名 · 双击备注行=档案 · 拖节点=调次序或过继 · 点头像=看照片 · 滚轮=缩放（视觉设置可关闭） · 左键拖空白=平移 · 编辑自动保存 · 详细说明见「帮助」菜单">操作：<b>＋/右键</b>=菜单 · <b>双击</b>=改名/档案 · <b>拖节点</b>=调次序或过继 · <b>点头像</b>=看照片 · <b>滚轮</b>=缩放（设置可关闭） · 左键拖空白=平移 · 自动保存 · 更多见「帮助」菜单', 'title="ノード下の「＋」や右クリック=操作メニュー · 氏名をダブルクリック=名前変更 · 備考行をダブルクリック=人物情報 · ノードをドラッグ=順序変更・養縁 · アバターをクリック=写真を表示 · スクロール=拡大縮小（表示設定でオフにできます） · 空白を左ボタンでドラッグ=移動 · 自動保存 · 詳しくは「ヘルプ」">編集：<b>＋/右クリック</b>=メニュー · <b>ダブルクリック</b>=名前/情報 · <b>ノードをドラッグ</b>=順序・養縁 · <b>アバターをクリック</b>=写真を表示 · <b>スクロール</b>=拡大縮小（設定でオフ可） · 空白を左ドラッグ=移動 · 自動保存 · 詳しくは「ヘルプ」'),
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
  # EN 表にのみ存在していた既存 1 件（ユーザー可視 tooltip）の JA 補完
  ('title="双击：改名 / 清空移除"><i class="role">', 'title="ダブルクリック：名前変更 / 空で削除"><i class="role">'),
]

# 上の JA 配列で None を入れた箇所は「変更なし」を意味する（フィルタで除去）
JA = [t for t in JA if t[1] is not None]
EN = [t for t in EN if t[1] is not None]

# ---- JA 続き：カード以降（URN：日文 UI の残り半分）----
JA += [
  # ---- JS：竖排行标 / 统计条 / 保存灯 ----
  ("const text = numToCn(g + genOffset()) + genUnit() + (zbRows[g - 1] ? '·' + zbRows[g - 1] : '');", "const text = numToCn(g + genOffset()) + genUnit() + (zbRows[g - 1] ? '・' + zbRows[g - 1] : '');"),
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
  ("ctxMenu.appendChild(mi(n.expanded ? '折叠此支' : '展开此支', '', '', () => toggleExpand(n)));", "ctxMenu.appendChild(mi(n.expanded ? 'この支を折りたたむ' : 'この支を展開', '', '', () => toggleExpand(n)));"),
  ("ctxMenu.appendChild(mi('改名', '', 'F2', () => editName(n)));", "ctxMenu.appendChild(mi('名前変更', '', 'F2', () => editName(n)));"),
  ("ctxMenu.appendChild(mi('档案', '', 'Ctrl+I', () => editDetails(n)));", "ctxMenu.appendChild(mi('人物情報', '', 'Ctrl+I', () => editDetails(n)));"),
  ("ctxMenu.appendChild(mi('删除', 'danger', '', () => deleteNode(n)));", "ctxMenu.appendChild(mi('削除', 'danger', '', () => deleteNode(n)));"),
  ("m.appendChild(mi('全展开', '', '', () => expandAll(true)));", "m.appendChild(mi('すべて展開', '', '', () => expandAll(true)));"),
  ("m.appendChild(mi('全折叠', '', '', () => expandAll(false)));", "m.appendChild(mi('すべて折りたたむ', '', '', () => expandAll(false)));"),
  ("m.appendChild(mi('谱序…', '', '', openClan, '谱名 / 堂号 / 源流 / 字辈表 / 始祖记'));", "m.appendChild(mi('譜序…', '', '', openClan, '譜名 / 堂号 / 由来 / 字輩表 / 始祖記'));"),
  ("m.appendChild(mi('视觉设置…', '', '', openSettings));", "m.appendChild(mi('表示設定…', '', '', openSettings));"),
  ("mi('帮助 / 快捷键', '', '', openHelp)", "mi('ヘルプ / ショートカット', '', '', openHelp)"),
  ("mi(IS_XHS ? '保存图片到相册' : '导出图片', '', 'png', exportPNG));", "mi(IS_XHS ? 'アルバムに保存' : '画像を出力', '', 'png', exportPNG));"),
  ("mi('复制备份', '', '', function(){", "mi('バックアップをコピー', '', '', function(){"),
  ("mi('粘贴导入备份', '', '', pasteImport));", "mi('貼り付けで復元', '', '', pasteImport));"),
  ("mi('备份到文件', '', 'json', backupToFile, '导出 json 备份（含成员照片缩略图）：换电脑 / 防清缓存'));", "mi('バックアップ保存', '', 'json', backupToFile, 'json バックアップを書き出す（メンバー写真のサムネイル付き。機種変更 / キャッシュ消去対策）'));"),
  ("mi('恢复备份', '', 'json', () => document.getElementById('__importFile').click(), '导入 json 备份（也支持旧版 HTML）'));", "mi('バックアップ復元', '', 'json', () => document.getElementById('__importFile').click(), 'json バックアップを読み込む（旧 HTML も対応）'));"),
  ("mi('导出 PDF', '', '', exportPDF, '图谱排版，单页'));", "mi('PDF を出力', '', '', exportPDF, '図表レイアウト、1 ページ'));"),
  ("mi('导出世系录', '', '五世一表', exportShixilu, '欧式表格：浏览器打开即可打印'));", "mi('世系録を出力', '', '五世一表', exportShixilu, '欧式表：ブラウザで開いてそのまま印刷'));"),
  ("mi('导出 Markdown', '', 'md', exportMarkdown));", "mi('Markdown を出力', '', 'md', exportMarkdown));"),
  ("mi('打印', '', '', () => window.print(), '跟随当前视图排版'));", "mi('印刷', '', '', () => window.print(), '現在のビューのレイアウトで印刷'));"),
  ("mi('按出生年重排', '', '', actSortByBirth));", "mi('生年で並べ替え', '', '', actSortByBirth));"),
  ("mi('重置数据', 'danger', '', resetData, '清空并恢复为示例谱'));", "mi('データをリセット', 'danger', '', resetData, '消去してサンプル譜に戻す'));"),
  # ---- JS：字辈角标 ----
  ("'字辈表（第' + range + genUnit() + '，蓝框 = 族谱中已出现）';", "'字輩表（第' + range + genUnit() + '、青枠 = 譜に現れる字）';"),
  ("d.innerHTML = esc(z || '·') + '<small>第' + genLabel(i + 1) + '</small>';",
   "d.innerHTML = esc(z || '·') + '<small>第' + genLabel(i + 1) + '</small>';"),
  ("d.title = '第' + genLabel(i + 1) + '字辈「' + (z || '?') + '」' + (all.includes(z) ? '（族谱中已出现）' : '');",
   "d.title = '第' + genLabel(i + 1) + 'の字輩「' + (z || '?') + '」' + (all.includes(z) ? '（譜に現れる）' : '');"),
  ("'<span class=\"help-note\">本文件尚未配置字辈表</span>'", "'<span class=\"help-note\">このファイルには字輩表が未設定です</span>'"),
  ("FAM_SUR || '（自动识别）'", "FAM_SUR || '（自動判定）'"),
  # ---- JS：设置/视图 toast ----
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
  ("toast('「' + v + '」已是 ' + n.name + ' 的配偶，无需重复添加');", "toast('「' + v + '」は既に ' + n.name + ' の配偶者です');"),
  ("toast('已为 ' + n.name + ' 添加配偶「' + v + '」，继续点「＋配偶」可再加');", "toast(n.name + ' に配偶者「' + v + '」を追加しました。「＋配偶者」で追加できます');"),
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
  ("if (!validTree(d)) throw new Error('结构不符：需要 {id,name,children[]} 树');", "if (!validTree(d)) throw new Error('構造が不正です：{id,name,children[]} ツリーが必要');", 2),
  ("toast('已导入「' + f.name + '」，数据已自动保存');", "toast('「' + f.name + '」を読み込みました。データは自動保存済み');"),
  ("? '已导入「' + f.name + '」，数据已自动保存，照片原图已写入本机照片库（' + ok + ' 张）'",
   "? '「' + f.name + '」を読み込みました。データは自動保存済み。写真のオリジナル ' + ok + ' 枚を本体の写真庫に書き込みました'"),
  (": '已导入「' + f.name + '」，数据已自动保存，照片库不可用，仅缩略图可用');",
   ": '「' + f.name + '」を読み込みました。データは自動保存済み。写真ライブラリを利用できないため、サムネイルのみ表示されます');"),
  ("alert('导入失败：不是有效的族谱 JSON 文件\\n' + e.message);", "alert('読み込み失敗：有効な家系図 JSON ファイルではありません\\n' + e.message);", 2),
  ("if (!confirm('确定重置？当前族谱将被清空，恢复到本文件自带的初始数据。\\n（如需保留，先「备份到文件」；误删可用 Ctrl+Z）')) return;",
   "if (!confirm('リセットしますか？現在の家系図は消去され、このファイルの初期データに戻ります。\\n（残す場合は先に「バックアップ保存」。誤削除は Ctrl+Z）')) return;"),
  ("toast('已重置为本文件的初始数据（再次「保存到文件」可固化）');", "toast('このファイルの初期データにリセットしました');"),
  ("const fname = (clanOf().ming || '家族族谱') + '-备份-'", "const fname = (clanOf().ming || '家系図') + '-バックアップ-'"),
  (": '备份已下载：' + fname);", ": 'バックアップをダウンロードしました：' + fname);"),
  # ---- JS：画布 ----
  ("throw new Error('画布尚未渲染');", "throw new Error('キャンバスが未描画です');"),
  # ---- JS：导出文件名 / toast ----
  ("return (clanOf().ming || '家族族谱') + '-图-'", "return (clanOf().ming || '家系図') + '-図-'"),
  ("toast('图片已下载（' + cv.width + '×' + cv.height + '）');", "toast('画像をダウンロードしました（' + cv.width + '×' + cv.height + '）');"),
  ("toast('PDF 已下载（' + W + '×' + H + ' pt）');", "toast('PDF をダウンロードしました（' + W + '×' + H + ' pt）');"),
  (".catch(e => toast('导出失败：' + ((e && e.message) || e)));", ".catch(e => toast('出力に失敗：' + ((e && e.message) || e)));", 2),
  # ---- JS：打印 ----
  ("note.textContent = (cfg.vertical ? '谱书竖排' : '常规横排') + ' · 共 ' + cnt + ' 人' + (s < 1 ? '（整图已按页面缩放 ' + Math.round(s * 100) + '%）' : '');", "note.textContent = (cfg.vertical ? '譜書縦書き' : '通常の横書き') + ' · 計 ' + cnt + ' 人' + (s < 1 ? '（ページに合わせて ' + Math.round(s * 100) + '% に縮小）' : '');"),
  ("if (c.chain)  xuHtml += '<div><b>源流世系：</b>' + esc(c.chain) + '</div>';", "if (c.chain)  xuHtml += '<div><b>系統：</b>' + esc(c.chain) + '</div>';"),
  ("if (c.shizu)  xuHtml += '<div><b>始祖记：</b>' + esc(c.shizu) + '</div>';", "if (c.shizu)  xuHtml += '<div><b>始祖記：</b>' + esc(c.shizu) + '</div>';"),
  ("if (c.origin) xuHtml += '<div><b>家族来源：</b>' + esc(c.origin) + '</div>';", "if (c.origin) xuHtml += '<div><b>家族の由緒：</b>' + esc(c.origin) + '</div>';"),
  # ---- JS：全局 ----
  ("toast('已自动保存，无需手动操作');", "toast('自動保存済み。操作不要です');"),
  ("if (_seededFrom === 'legacy-draft') toast('已从本浏览器的历史数据恢复族谱');", "if (_seededFrom === 'legacy-draft') toast('このブラウザの履歴データから家系図を復元しました');"),
  ("else if (_seededFrom === 'file') toast('自动保存已就绪：编辑即保存，无需手动操作');", "else if (_seededFrom === 'file') toast('自動保存の準備完了：編集は即保存されます');"),
  # ---- 结构默认值 ----
  ('genBase: 1, bookSpouse: true, showSurname: true', 'genBase: 1, bookSpouse: false, showSurname: true'),
  # ---- タッチ操作ヒント / 入力モーダル / テキストモーダル / 貼り付け導入 / XHS 用 ----
  ('<div id="__gestureHint">单指拖动平移 · 双指捏合缩放 · 长按卡片更多操作</div>',
   '<div id="__gestureHint">1 本指でドラッグ移動 · ピンチで拡大縮小 · カード長押しでメニュー</div>'),
  ('<h3 id="__uipTitle">输入</h3>', '<h3 id="__uipTitle">入力</h3>'),
  ('<h3 id="__textTitle">文本</h3>', '<h3 id="__textTitle">テキスト</h3>'),
  ('<button id="__textSel">全选</button><button class="primary" id="__textOk">关闭</button>',
   '<button id="__textSel">すべて選択</button><button class="primary" id="__textOk">閉じる</button>'),
  ('<h3>粘贴备份 json 导入</h3>', '<h3>バックアップ json を貼り付けて復元</h3>'),
  ("toast('已导入粘贴的备份数据，已自动保存');", "toast('貼り付けたバックアップを読み込み、自動保存しました');"),
  ("? '已导入粘贴的备份数据，已自动保存，照片原图已写入本机照片库（' + ok + ' 张）'",
   "? '貼り付けたバックアップを読み込み、自動保存しました。写真のオリジナル ' + ok + ' 枚を本体の写真庫に書き込みました'"),
  (": '已导入粘贴的备份数据，已自动保存，照片库不可用，仅缩略图可用');",
   ": '貼り付けたバックアップを読み込み、自動保存しました。写真ライブラリを利用できないため、サムネイルのみ表示されます');"),
  ("uiPrompt('修改姓名：', n.name).then(function(t){", "uiPrompt('名前を変更：', n.name).then(function(t){"),
  ("uiPrompt('为「' + n.name + '」添加第 ' + nth + ' 位配偶姓名：\\n（如需改名/移除某位配偶，直接双击图上该配偶的名字）').then(function(t){",
   "uiPrompt('「' + n.name + '」の第 ' + nth + ' 配偶者を追加：\\n（改名・削除はカード上の配偶者名をダブルクリック）').then(function(t){"),
  ("uiPrompt('修改「' + n.name + '」的第 ' + (i + 1) + ' 位配偶：\\n（清空并确定 = 移除这位配偶）', cur).then(function(t){",
   "uiPrompt('「' + n.name + '」の第 ' + (i + 1) + ' 配偶者を編集：\\n（空にして決定 = この配偶者を削除）', cur).then(function(t){"),
  ("uiPrompt('添加一位与「' + n.name + '」同辈的成员（' + (p.id === 'root' ? '第一代' : '同父母') + '）：').then(function(t){",
   "uiPrompt('「' + n.name + '」と同世代のメンバーを追加（' + (p.id === 'root' ? '第一世代' : '同じ両親') + '）：').then(function(t){"),
  ("if (IS_XHS){ toast('小工具内不支持下载文件：请使用电脑网页版导出'); return; }",
   "if (IS_XHS){ toast('ミニツール内ではダウンロードできません：PC 版ウェブで書き出してください'); return; }"),
  ("toast('当前环境不支持保存到相册')", "toast('この環境ではアルバム保存に対応していません')"),
  ("toast('正在保存图片…');", "toast('画像を保存中…');"),
  ("toast('图片已保存到相册')", "toast('画像をアルバムに保存しました')"),
  ("toast('保存失败：' + ((e && e.errMsg) || e));", "toast('保存に失敗しました：' + ((e && e.errMsg) || e));"),
  ("toast('保存失败：' + e.message);", "toast('保存に失敗しました：' + e.message);"),
  ("showTextModal('备份文本：点击「全选」后手动复制'",
   "showTextModal('バックアップテキスト：「すべて選択」から手動コピー'"),
  # ---- メンバー写真（第一期）----
  ('title="成员照片（方形预览）"', 'title="メンバー写真（正方形プレビュー）"'),
  ('id="__dmPhotoAdd">添加照片</button>', 'id="__dmPhotoAdd">写真を追加</button>'),
  ('id="__dmPhotoDel" style="display:none">删除照片</button>', 'id="__dmPhotoDel" style="display:none">写真を削除</button>'),
  ('alt="成员照片"', 'alt="メンバー写真"', 2),
  ('<h3 id="__photoImpTitle">照片导入结果</h3>', '<h3 id="__photoImpTitle">写真取り込み結果</h3>'),
  ('id="__photoImpOk">导入</button>', 'id="__photoImpOk">取り込む</button>'),
  ('<tr><td>成员照片</td><td>「档案」里添加照片后卡片显示圆形头像，点头像看大图；文件 ▾ 可按文件夹批量导入照片，备份（含照片原图）换电脑不丢原图</td></tr>',
   '<tr><td>メンバー写真</td><td>「人物情報」で写真を追加するとカードに丸いアバターが表示され、クリックで拡大表示。ファイル ▾ からフォルダ単位で写真を一括取り込みでき、「バックアップ（写真オリジナル付き）」なら PC を変えてもオリジナルを失いません</td></tr>'),
  ('<label class="checkline"><input type="checkbox" id="__cfgPhotos"> 成员照片头像（卡片显示照片/剪影，点头像看大图）</label>',
   '<label class="checkline"><input type="checkbox" id="__cfgPhotos"> メンバー写真アバター（カードに写真/シルエットを表示。クリックで拡大表示）</label>'),
  ("av.title = '点头像看大图';", "av.title = 'クリックで拡大表示';"),
  ("av.title = '在「档案」里可添加照片';", "av.title = '「人物情報」で写真を追加できます';"),
  ("addB.textContent = '更换照片';", "addB.textContent = '写真を変更';"),
  ("addB.textContent = '添加照片';", "addB.textContent = '写真を追加';"),
  ("toast('已删除「' + n.name + '」的照片');", "toast('「' + n.name + '」の写真を削除しました');"),
  ("toast('照片处理中…');", "toast('写真を処理中…');"),
  ("toast('已为「' + n.name + '」设置照片');", "toast('「' + n.name + '」に写真を設定しました');"),
  ("}).catch(() => toast('照片读取失败：请换一张图片文件'));", "}).catch(() => toast('写真を読み込めませんでした：別の画像ファイルをお試しください'));"),
  ("new Error('照片存储不可用')", "new Error('写真ストレージを使用できません')"),
  ("new Error('照片读取失败')", "new Error('写真の読み込みに失敗しました')"),
  ("new Error('图片解码失败')", "new Error('画像をデコードできませんでした')"),
  ("new Error('图片尺寸为 0')", "new Error('画像サイズが 0 です')"),
  ("new Error('文件读取失败')", "new Error('ファイルを読み込めませんでした')"),
  ("m.appendChild(mi('备份（含照片原图）', '', 'json', () => backupToFile(true), '在备份 json 里附上全部原图，换电脑后点头像仍可看大图（文件更大）'));",
   "m.appendChild(mi('バックアップ（写真オリジナル付き）', '', 'json', () => backupToFile(true), 'バックアップ json にオリジナル全件を添付します。PC を変えた後もアバターをクリックで拡大表示できます（ファイルは大きくなります）'));"),
  ("m.appendChild(mi('导入照片文件夹…', '', '', () => document.getElementById('__photoDirInput').click(), '按文件名匹配成员姓名，批量设置照片'));",
   "m.appendChild(mi('写真フォルダを取り込む…', '', '', () => document.getElementById('__photoDirInput').click(), 'ファイル名でメンバー名を照合し、写真を一括設定'));"),
  ("sel.appendChild(new Option('跳过（不导入）', ''));", "sel.appendChild(new Option('スキップ（取り込まない）', ''));"),
  ("return m.name + (dupBaseNames[m.name] && p ? '（' + (p.id === 'root' ? '第一代' : p.name + '之子') + '）' : '');",
   "return m.name + (dupBaseNames[m.name] && p ? '（' + (p.id === 'root' ? '第一世代' : p.name + ' の子') + '）' : '');"),
  ("'成功匹配 ' + auto + ' 张（确认后写入）'", "'自動一致 ' + auto + ' 枚（確認後に書き込み）'"),
  ("' · 需人工确认 ' + list.children.length + ' 张'", "' · 要確認 ' + list.children.length + ' 枚'"),
  ("'（共扫描 ' + total + ' 张；确认导入时才读取压缩，跳过零成本）';", "'（スキャン計 ' + total + ' 枚。圧縮は取り込み確定時のみ。スキップなら負荷なし）';"),
  ("document.getElementById('__photoImpOk').textContent = '确认导入';", "document.getElementById('__photoImpOk').textContent = '確認して取り込む';"),
  ("if (!imgs.length){ toast('该文件夹里没有图片文件'); return; }", "if (!imgs.length){ toast('このフォルダに画像ファイルがありません'); return; }"),
  ("toast('正在读取并压缩照片（' + cnt + ' 张）…');", "toast('写真を読み込み・圧縮しています（' + cnt + ' 枚）…');"),
  ("toast('已取消，未写入任何照片');", "toast('キャンセルしました。写真は書き込んでいません');"),
  ("if (!cnt){ toast('未选择任何成员，未写入照片'); return; }", "if (!cnt){ toast('メンバーが選択されていないため、写真は書き込んでいません'); return; }"),
  ("toast('已为 ' + (cnt - bad) + ' 位成员设置照片（同一人已有照片 = 更换）'",
   "toast((cnt - bad) + ' 人のメンバーに写真を設定しました（既存の写真は置き換え）'"),
  ("+ (bad ? '，' + bad + ' 张读取失败' : ''));", "+ (bad ? '，' + bad + ' 枚は読み込みに失敗' : ''));"),
  ("? '备份已下载（含 ' + Object.keys(full).length + ' 张照片原图）：' + fname", "? 'バックアップをダウンロードしました（写真オリジナル ' + Object.keys(full).length + ' 枚付き）：' + fname"),
]

# 続きブロック内の None（変更なし）も除去
JA = [t for t in JA if t[1] is not None]

# ============================================================ 种子数据
SEED_EN = {
  "id": "root", "name": "Ming Imperial Line", "spouses": [], "expanded": True, "demo": True,
  "clan": {
    "ming": "Ming Imperial Line (Demo)", "tang": "", "chain": "", "yuanzu": "Zhu Zhongba (5th ancestor)", "shizu": "", "qianzu": "",
    "origin": "The real imperial line of the Ming dynasty (excerpt). The Zhu family were farmers — ancestors used rank numbers for names: Zhong-ba, Bai-liu, Si-jiu, Chu-yi, Wu-si. Zhu Yuanzhang was first named Chong-ba, later Xing-zong, courtesy name Guo-rui. He gave each son's branch a twenty-character generation poem; the imperial line comes from prince Zhu Di: \u201cGao Zhan Qi Jian You, Hou Zai Yi Chang You\u201d — the dynasty ended exactly at the \u201cYou\u201d generation. The crown-prince Zhu Biao branch had its own poem, so Jianwen Emperor Yun-wen is not in the Yan branch poem. Double-click a name to rename, click \u201c\uff0b\u201d to add members; \u201cFile \u25be \u2192 Preface\u201d makes it your own family tree. Portraits: official Ming imperial seated portraits (National Palace Museum, Taipei; public domain). The Jianwen and Jingtai portraits are later copies; no portrait survives for Princess Ningguo."
  },
  "zibei": ["Xing", "Mu", "Gao", "Zhan", "Qi", "Jian", "You", "Hou", "Zai", "Yi", "Chang"],
  "children": [
    { "id": "d1", "name": "Zhu Yuanzhang", "spouses": ["Empress Ma"], "birth": "1328", "death": "1398", "note": "Hongwu Emperor", "zi": "Guo-rui", "expanded": True, "children": [
      { "id": "d2", "name": "Zhu Biao", "spouses": [], "birth": "1355", "death": "1392", "note": "Crown Prince Yiwen", "expanded": True, "children": [
        { "id": "d3", "name": "Zhu Yunwen", "spouses": [], "birth": "1377", "death": "", "note": "Jianwen Emperor (fate unknown)", "expanded": True, "children": [] } ] },
      { "id": "d4", "name": "Zhu Di", "spouses": ["Empress Xu"], "birth": "1360", "death": "1424", "note": "Yongle Emperor", "expanded": True, "children": [
        { "id": "d5", "name": "Zhu Gaochi", "spouses": ["Empress Zhang"], "birth": "1378", "death": "1425", "note": "Hongxi Emperor", "expanded": True, "children": [
          { "id": "d6", "name": "Zhu Zhanji", "spouses": [], "birth": "1399", "death": "1435", "note": "Xuande Emperor", "expanded": True, "children": [
            { "id": "d7", "name": "Zhu Qizhen", "spouses": [], "birth": "1427", "death": "1464", "note": "Yingzong (Zhengtong / Tianshun)", "expanded": True, "children": [
              { "id": "d9", "name": "Zhu Jianshen", "spouses": [], "birth": "1447", "death": "1487", "note": "Chenghua Emperor", "expanded": True, "children": [
                { "id": "d10", "name": "Zhu Youtang", "spouses": [], "birth": "1470", "death": "1505", "note": "Hongzhi Emperor", "expanded": True, "children": [] } ] } ] },
            { "id": "d8", "name": "Zhu Qiyu", "spouses": [], "birth": "1428", "death": "1457", "note": "Jingtai Emperor", "expanded": True, "children": [] } ] } ] } ] },
      { "id": "d11", "name": "Princess Ningguo", "spouses": ["Prince Consort Mei"], "gender": "f", "birth": "1364", "death": "", "note": "Eldest daughter", "expanded": True, "children": [] }
    ] }
  ]
}

SEED_JA = {
  "id": "root", "name": "明朝帝系", "spouses": [], "expanded": True, "demo": True,
  "clan": {
    "ming": "明朝帝系（デモ）", "tang": "", "chain": "", "yuanzu": "朱仲八（五世祖）", "shizu": "", "qianzu": "",
    "origin": "明皇室の実際の系譜（抜粋）。朱家は代々農民で、先祖は排行の数字を名に用いました：仲八、百六、四九、初一、五四——朱元璋の原名は重八、後に興宗、字は国瑞。二十六人の息子の各支に二十字の字輩詩を定めました。帝系は燕王・朱棣の一支から：「高瞻祁見祐、厚載翊常由」——明はまさに「由」の世代で幕を下ろしました。太子・朱標の一支は「允文遵祖訓」なので、建文帝・允炆は燕王の字輩に含まれません。名前をダブルクリックで変更、「＋」でメンバー追加；「ファイル ▾ → 譜序」で自分の家の譜にできます。肖像：明代皇帝の坐像（台北故宮博物院蔵、パブリックドメイン）。建文帝・代宗は後世の模本、寧国公主の肖像は伝わっていません。"
  },
  "zibei": ["興", "木", "高", "瞻", "祁", "見", "祐", "厚", "載", "翊", "常", "由"],
  "children": [
    { "id": "d1", "name": "朱元璋", "spouses": ["馬氏"], "birth": "1328", "death": "1398", "note": "明太祖（洪武）", "zi": "国瑞", "expanded": True, "children": [
      { "id": "d2", "name": "朱標", "spouses": [], "birth": "1355", "death": "1392", "note": "懿文太子", "expanded": True, "children": [
        { "id": "d3", "name": "朱允炆", "spouses": [], "birth": "1377", "death": "", "note": "建文帝（行方不明）", "expanded": True, "children": [] } ] },
      { "id": "d4", "name": "朱棣", "spouses": ["徐氏"], "birth": "1360", "death": "1424", "note": "明成祖（永楽）", "expanded": True, "children": [
        { "id": "d5", "name": "朱高熾", "spouses": ["張氏"], "birth": "1378", "death": "1425", "note": "明仁宗（洪熙）", "expanded": True, "children": [
          { "id": "d6", "name": "朱瞻基", "spouses": [], "birth": "1399", "death": "1435", "note": "明宣宗（宣徳）", "expanded": True, "children": [
            { "id": "d7", "name": "朱祁鎮", "spouses": [], "birth": "1427", "death": "1464", "note": "明英宗（正統・天順）", "expanded": True, "children": [
              { "id": "d9", "name": "朱見深", "spouses": [], "birth": "1447", "death": "1487", "note": "明憲宗（成化）", "expanded": True, "children": [
                { "id": "d10", "name": "朱祐樘", "spouses": [], "birth": "1470", "death": "1505", "note": "明孝宗（弘治）", "expanded": True, "children": [] } ] } ] },
            { "id": "d8", "name": "朱祁鈺", "spouses": [], "birth": "1428", "death": "1457", "note": "明代宗（景泰）", "expanded": True, "children": [] } ] } ] } ] },
      { "id": "d11", "name": "寧国公主", "spouses": ["梅殷"], "gender": "f", "birth": "1364", "death": "", "note": "明太祖の長女", "expanded": True, "children": [] }
    ] }
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

# ============================================================ 繁体中文（OpenCC 全文件转换）
def build_hant():
    """繁体版：整文件 s2twp（简→繁台湾用语，代码全 ASCII 不受影响），
    叠加独立存储键与 lang 属性。示例谱与注释一并转换，四语言内容保持同构。"""
    from opencc import OpenCC
    cc = OpenCC('s2twp')
    src = cc.convert(io.open(SRC, encoding='utf-8').read())
    errs = []
    for old, new in [
      ('<html lang="zh-CN">', '<html lang="zh-Hant">'),
      ("const STORAGE_KEY = 'zupu_data_v4';", "const STORAGE_KEY = 'zupu_data_v4_hant';"),
      ("const CFG_KEY = 'zupu_cfg_v1';", "const CFG_KEY = 'zupu_cfg_v1_hant';"),
      # s2twp 用词微调：台湾惯用「帳號」
      ('賬號', '帳號'),
    ]:
        n = src.count(old)
        if n != 1:
            errs.append('x%d: %r' % (n, old[:50]))
            continue
        src = src.replace(old, new)
    # 哨兵：台湾用语必须出现，简体原文必须消失
    for sentinel in ['儲存', '檔案', '字輩', '家族族譜']:
        if sentinel not in src:
            errs.append('sentinel missing: ' + sentinel)
    for leftover in ['数据真源', '字辈表']:
        if leftover in src:
            errs.append('simplified leftover: ' + leftover)
    if errs:
        print('zh-Hant FAIL')
        for e in errs: print('  ' + e)
        return False
    io.open(os.path.join(ROOT, 'index-zh-Hant.html'), 'w', encoding='utf-8', newline='').write(src)
    print('zh-Hant -> index-zh-Hant.html OK')
    return True

if __name__ == '__main__':
    base = io.open(SRC, encoding='utf-8').read()
    ok = True
    ok &= build('en', EN, SEED_EN, 'index-en.html', [
      ('<html lang="zh-CN">', '<html lang="en">'),
      ('<title>家族族谱 · 传代树（可编辑）</title>', '<title>Zupu · Family Tree Builder (editable)</title>'),
      ('%E6%97%8F%3C/text%3E', 'T%3C/text%3E'),   # favicon：族 → T
      # 完全独立：各语言文件使用自己的浏览器存储（数据与设置互不相通）
      ("const STORAGE_KEY = 'zupu_data_v4';", "const STORAGE_KEY = 'zupu_data_v4_en';"),
      ("const CFG_KEY = 'zupu_cfg_v1';", "const CFG_KEY = 'zupu_cfg_v1_en';"),
    ])
    ok &= build('ja', JA, SEED_JA, 'index-ja.html', [
      ('<html lang="zh-CN">', '<html lang="ja">'),
      ('<title>家族族谱 · 传代树（可编辑）</title>', '<title>家系図・伝代ツリー（編集可）</title>'),
      ("const STORAGE_KEY = 'zupu_data_v4';", "const STORAGE_KEY = 'zupu_data_v4_ja';"),
      ("const CFG_KEY = 'zupu_cfg_v1';", "const CFG_KEY = 'zupu_cfg_v1_ja';"),
    ])
    ok &= build_hant()
    sys.exit(0 if ok else 1)
