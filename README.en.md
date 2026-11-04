<div align="center">

[简体中文](README.md) | [繁體中文](README.zh-Hant.md) | **English** | [日本語](README.ja.md)

<img src="docs/cover-en.jpg?v=15.52" alt="Zupu · Family Tree" width="100%">

# Zupu · Family Tree

**A double-click electronic genealogy: record family, number generations by lineage, print & bind**

[![Version](https://img.shields.io/badge/version-v15.52-b03a2e)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-115%20passing-2f6390)](tests)
[![Dependencies](https://img.shields.io/badge/dependencies-0-3c7a4e)]()
[![License](https://img.shields.io/badge/license-MIT-8a7d68)](LICENSE)
[![Try online](https://img.shields.io/badge/try%20it-online-b03a2e)](https://zaxchou.github.io/zupu/)

*Put family-tree keeping back on every family's own computer.*

</div>

---

**One HTML file is all there is**: double-click it and it works — send it to family and it
works for them too. No network, no account, nothing to install; your data lives in your own
browser, and every change is saved automatically.

| Standard tree | In-page profile editor |
| --- | --- |
| ![Standard tree](docs/preview-tree-en.png?v=15.42) | ![Profile editor](docs/preview-vertical-en.png?v=15.42) |

Every member has an **in-page profile editor** (name, dates, sex, adoption, courtesy /
art names, spouse terms, notes). A **vertical book layout** following the conventions
of traditional Chinese genealogy books is also built in: generations as rows, names
top-to-bottom (right to left) — print it / export it to PDF and **bind it into a book**.

## ✨ What it does for you

- **Fill in your family like a form** — click “＋” to add, double-click to rename, drag cards
  to reorder siblings; drop one onto another to adopt. Ctrl+Z undoes anything
- **Made for phones & tablets too** — drag to reorder, long-press for menus,
  double-tap to rename, pinch to zoom; the UI trims itself on small screens
- **Put a face to every name** — click “Add photo” in the profile and the card instantly
  shows a round avatar; click the avatar to see it large. “File ▾ → Import photo folder…”
  matches a whole folder of photos by file name, backups can carry the originals, and
  exports to PNG / PDF include the avatars
- **Make it look the way you want** — “View ▾ → Visual settings…” gathers it all in one
  place: four growth directions (top to bottom / bottom to top / left to right / right to
  left), three color themes (Parchment / Sky / Dark), horizontal or vertical book layout —
  every change applies on the spot, no reload
- **Scroll to zoom, drag to pan** — the wheel zooms straight in and out, and grabbing any
  empty spot pans the tree, like a map app; prefer the old way? Turn direct zoom off in
  Visual settings (wheel scrolls the page, Ctrl+scroll zooms)
- **Count generations and generation names separately** — the founding ancestor is generation 1;
  each child is one generation after their parent. The tree-title container does not count,
  and names never change the numbers. Numbers appear even without a generation-name list.
  In Visual settings, set “Generation at which generation names begin” to 10: generations
  1–9 have no sequence badge, generation 10 uses the first character, and 11 the second.
  Generation numbers and generation-name sequence badges appear separately
- **Print a real genealogy book** — vertical text, generations as rows, five generations per
  table; export to PDF and take it straight to the print shop for binding. Tree name, hall
  name, lineage and founder record print up front
- **Keep the whole tree on one searchable page** — “File ▾ → Export PDF” defaults to a vector
  PDF: text, connectors and shapes stay sharp as you zoom, and text is searchable. Choose A4
  landscape pages for printing. The main export keeps current folds; “Export this branch…”
  in a member’s context menu includes all descendants, including folded ones
- **Bring Markdown back in** — “File ▾ → Export Markdown (re-importable)” produces readable
  preface, generation-char and member information; import this tool’s `.md` format through
  “Restore backup”. Use JSON with original photos for a complete backup
- **Spouse terms follow the old books** — first spouse / remarried, adopted heir / adopted
  out / dual heir, no-issue mark — the classic conventions are all here
- **Your data stays yours** — offline, no account, nothing uploaded; one-click json backup,
  and restoring on another computer is a double-click away
- **Still opens decades from now** — no dependencies, no services: one file on a USB stick
  is an heirloom

## 🚀 Quick start

**Option 0 (fastest)**: open the online version → **[https://zaxchou.github.io/zupu/](https://zaxchou.github.io/zupu/)**
(Chinese UI; use `index-en.html` from a release for English).

**Option 1 (local, recommended)**: from [Releases](https://github.com/zaxchou/zupu/releases),
download the single file for your language — English: `index-en.html`
(简体中文 `index.html`, 繁體中文 `index-zh-Hant.html`, 日本語 `index-ja.html`).
One file is everything —
double-click it; a first-run wizard appears:

- **Explore the demo** — the real Ming imperial line (Zhu Yuanzhang’s family), with generations counted by parent–child relationships and generation names shown separately
- **Start from scratch** — enter your family name and start with generation one
- **Import a previous backup** — restore json exported by this tool

**Option 2**: `git clone` this repo and double-click `index-en.html`.

To record your own family: double-click a name to rename, click “＋” to add members,
“File ▾ → Preface…” sets the tree name / generation chars / lineage —
make it entirely yours.

## ❓ FAQ

**Where is my data stored? Can it be lost?**
Tree data stays in this browser’s localStorage; original photos stay in its IndexedDB.
Nothing is uploaded. Use “File ▾ → Backup (with original photos)” regularly for a complete
JSON backup; “Back up to file” includes only photo thumbnails. Import on another computer
via “Restore backup”. The user data structure is unchanged; existing JSON backups still work.

**How do generation numbers and generation names work? What happens to old settings?**
Generation numbers follow parent–child relationships: the founding ancestor is generation 1,
children are one generation later, and the tree-title container does not count. Numbers appear
without a generation-name list, and matching a name to that list never changes the numbers.
Under “View ▾ → Visual settings…”, set “Generation at which generation names begin”. For a
list such as Gao, Zhan, Qi, Jian, You starting at 10, generations 1–9 show only their generation
number and leave the sequence badge empty. Generation 10 shows generation 10 and sequence 1 · Gao;
generation 11 shows generation 11 and sequence 2 · Zhan, in separate badges.
The old local `genBase` setting migrates to the generation-name starting generation; it no
longer shifts generation numbers. The setting stays in this browser. The user tree structure
is unchanged, with no new JSON or Markdown schema.

**Can I zoom and search a PDF? What if it reports U+28EE7 (𨻧) missing?**
The dialog always defaults to a single-page vector PDF, even for large trees. Choose A4
landscape pages yourself when needed. Apache-2.0 DroidSansFallbackFull supplies common
characters; a separate SIL OFL 1.1 ZupuRareSupport fallback (about 16 KB) supplies 𨻧, 𠮷, 𡊨,
and 𠀀, including the reported U+28EE7. Each font embeds its own subset of used glyphs,
preserving original Unicode text that remains searchable, vector-based and available offline.
Connectors and shapes remain vectors too. Photos remain images; sharpness depends on the source.
For other missing characters, choose a local TTF with the required glyphs and legal permission
to embed it. It can supply just the missing glyphs while default fonts remain available for
common characters; one custom TTF no longer has to cover the whole tree. It is used only for
this single-page export, never uploaded or saved in the tree. If no available font contains a
required glyph, export still fails explicitly. Neither full Unicode nor full CJK Extension B
coverage is guaranteed. Paged output is a continuous slice: a card crossing a page edge is split
across the two pages and is complete once the pages are joined. In single-page PDFs, horizontal
layouts are searchable by full name; vertical layouts set each character separately, so a
full-name search may match only single characters.
The Xiaohongshu mini-tool cannot save PDFs; its package omits both PDF fonts and the backend
but includes the new generation-number and generation-name sequence rules.

**Does Markdown replace a complete backup?**
Use “Restore backup” to re-import `.md` files exported by this tool. This does not promise
lossless preservation of every field in arbitrary Markdown text. Markdown excludes photos
and fold state; use JSON from “Backup (with original photos)” for a complete backup.

**Multi-user editing / online sync?**
No — by design. Genealogy data is private and edited rarely; a local single file is the
most dependable shape. To collaborate, share a backup json and merge edits by hand.

**The demo names are not mine?**
Just a sample — everything is editable under “Preface”, and you can paste your
own generation-char table.

**What if browser data gets cleared?**
That's what backups are for. `data.json` in the repo is a sample snapshot; your own
backups are in your hands.

## 🤝 Contributing

Issues / PRs welcome: `handoff.md` documents the architecture and hard-won lessons —
please read it before changing code; run the full test suite in `tests/` before
submitting. See [CONTRIBUTING.md](CONTRIBUTING.md).
The English and Japanese builds are generated from the Chinese master via
`tools/build_i18n.py` — change `index.html`, then re-run the script.

## 📄 License

[MIT](LICENSE) © zaxchou. The bundled DroidSansFallbackFull PDF font for common characters
is licensed under Apache-2.0; see its [source and NOTICE](third_party/droid-sans/README.md).
The separate ZupuRareSupport fallback uses SIL OFL 1.1; see its
[source, modifications and license](third_party/zupu-rare-font/README.md).
