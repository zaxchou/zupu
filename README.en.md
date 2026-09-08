<div align="center">

[简体中文](README.md) | [繁體中文](README.zh-Hant.md) | **English** | [日本語](README.ja.md)

<img src="docs/cover-en.jpg?v=15.37" alt="Zupu · Family Tree" width="100%">

# Zupu · Family Tree

**A double-click electronic genealogy: record your family, auto-number generations, print & bind**

[![Version](https://img.shields.io/badge/version-v15.37-b03a2e)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-52%20passing-2f6390)](tests)
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
| ![Standard tree](docs/preview-tree-en.png?v=15.37) | ![Profile editor](docs/preview-vertical-en.png?v=15.37) |

Every member has an **in-page profile editor** (name, dates, sex, adoption, courtesy /
art names, spouse terms, notes). A **vertical book layout** following the conventions
of traditional Chinese genealogy books is also built in: generations as rows, names
top-to-bottom (right to left) — print it / export it to PDF and **bind it into a book**.

## ✨ What it does for you

- **Fill in your family like a form** — click “＋” to add, double-click to rename, drag cards
  to reorder siblings; drop one onto another to adopt. Ctrl+Z undoes anything
- **Made for phones & tablets too** — drag to reorder, long-press for menus,
  double-tap to rename, pinch to zoom; the UI trims itself on small screens
- **Names in, generations out** — paste your generation-char list (e.g. the real Ming imperial poem “高瞻祁见祐”) and
  everyone's generation is numbered automatically; align it with your old book, so “the 23rd
  generation” there reads “the 23rd generation” here
- **Print a real genealogy book** — vertical text, generations as rows, five generations per
  table; export to PDF and take it straight to the print shop for binding. Tree name, hall
  name, lineage and founder record print up front
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

- **Explore the demo** — the real Ming imperial line (Zhu Yuanzhang’s family), auto-numbered by the generation poem
- **Start from scratch** — enter your family name and start with generation one
- **Import a previous backup** — restore json exported by this tool

**Option 2**: `git clone` this repo and double-click `index-en.html`.

To record your own family: double-click a name to rename, click “＋” to add members,
“View ▾ → Preface” sets the tree name / generation chars / lineage —
make it entirely yours.

## ❓ FAQ

**Where is my data stored? Can it be lost?**
In this browser on this computer (localStorage). Nothing is ever uploaded. Export a json
backup regularly via “File ▾ → Back up to file”; restore it anywhere via “Restore backup”.

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

[MIT](LICENSE) © zaxchou
