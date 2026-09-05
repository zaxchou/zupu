<div align="center">

[简体中文](README.md) | **繁體中文** | [English](README.en.md) | [日本語](README.ja.md)

<img src="docs/cover-zh-Hant.jpg" alt="家族族譜 · 傳代樹" width="100%">

# 家族族譜 · 傳代樹 (Zupu)

**雙擊就能用的電子族譜：錄入家人、自動算輩分、列印裝訂成冊**

[![Version](https://img.shields.io/badge/version-v15.33-b03a2e)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-53%20passing-2f6390)](tests)
[![Dependencies](https://img.shields.io/badge/dependencies-0-3c7a4e)]()
[![License](https://img.shields.io/badge/license-MIT-8a7d68)](LICENSE)
[![線上試用](https://img.shields.io/badge/線上試用-點擊演示-b03a2e)](https://zaxchou.github.io/zupu/)

*把修譜這件事，放回每個家庭的電腦裡。*

</div>

---

**一個 HTML 檔案就是全部**：雙擊開啟就能用，傳給家人也能用。
不連線、無帳號、免安裝，資料只存在你自己電腦的瀏覽器裡，改一個字就自動儲存一次。
本檔案為繁體中文版：`index-zh-Hant.html`。

| 常規傳代樹 | 譜書豎排（古法） |
| --- | --- |
| ![常規傳代樹](docs/preview-tree.png) | ![譜書豎排](docs/preview-vertical.png) |

**譜書豎排**按傳統修譜版式還原：世代成行、名字豎書（右→左）、行左標世數、墨字吊線——
列印 / 匯出 PDF 即可**裝訂成冊**。

## ✨ 它能幫你做什麼

- **像填表格一樣錄家人** — 點「＋」加人、雙擊改名、拖動卡片調長幼次序，
  拖到別人名下就是過繼；做錯了 Ctrl+Z 隨時復原
- **名字寫上，輩分自動算** — 把你家的字輩貼進去（如「德承傳世澤」），每個人是第幾代自動標出來；
  還能對齊老譜：老譜記「廿三世」，這裡也顯示「廿三世」
- **列印出來是一本老譜的樣子** — 豎排文字、世代成行、五代一張表，匯出 PDF 直接送印刷廠裝訂成冊；
  譜名、堂號、源流、始祖記都自動印在譜前
- **配偶寫法跟著老譜走** — 「丁嘉」顯示成「丁氏嘉」；
  配 / 繼配 / 嗣子 / 嗣出 / 兼祧 / 止，老譜的體例這裡都有
- **資料只在你自己手裡** — 不連線、無帳號、不上傳任何伺服器；
  一鍵匯出備份檔，換電腦或傳給親戚，雙擊匯入就回來
- **幾十年後也打得開** — 不依賴任何軟體和服務：一個 HTML 檔案，隨身碟存一份就能傳給下一代

## 🚀 快速開始

**方式〇（最快）**：直接開啟線上版 → **[https://zaxchou.github.io/zupu/](https://zaxchou.github.io/zupu/)**
（線上版為簡體介面；繁體請下載 `index-zh-Hant.html`）

**方式一（本機使用，推薦）**：到 [Releases](https://github.com/zaxchou/zupu/releases) 按語言下載——
繁體 `index-zh-Hant.html` / 簡體 `index.html` / English `index-en.html` / 日本語 `index-ja.html`，
一個檔案就是全部，下載雙擊即用。首次使用會彈出精靈：

- **先看看示例** — 用內建的演示譜熟悉操作
- **從空白開始** — 填上你的譜名（如「陳氏族譜」）和堂號，從第一代建起
- **匯入備份** — 已有本工具匯出的 json，直接還原

**方式二**：`git clone` 本倉庫後雙擊 `index-zh-Hant.html`。

錄入自己家族：雙擊名字改名、點「＋」新增成員、「檢視 ▾ → 譜序」設定譜名 / 堂號 /
字輩表 / 源流——全部改成你家的。

## ❓ 常見問題

**資料存在哪裡？會不會丟？**
存在你電腦的瀏覽器裡（localStorage），不上傳任何伺服器。定期用「檔案 ▾ → 備份到檔案」
匯出 json 即可萬無一失；換電腦用「還原備份」匯入。

**支援多人協作 / 線上同步嗎？**
不支援，這是刻意的設計選擇：族譜資料私密且低頻編輯，本機單檔案是最穩妥的形態。
多人協作請共享備份 json，各自匯入修改後再合併。

**介面文字 / 字輩 / 譜名都是別人家的？**
示例而已——譜序裡全部可改，字輩表貼上你自己家族的字輩即可。

**瀏覽器資料清了會怎樣？**
所以請備份。`data.json` 是倉庫內建的示例快照；你自己的備份在你手裡。

## 🤝 參與貢獻

Issue / PR 都歡迎：`handoff.md` 裡有完整的架構說明與踩坑記錄，改程式碼前建議先讀；
提交前請跑通 `tests/` 全部用例。見 [CONTRIBUTING.md](CONTRIBUTING.md)。
繁體版由 `tools/build_i18n.py` 以 OpenCC 從簡體母本轉換生成。

## 📄 License

[MIT](LICENSE) © zaxchou
