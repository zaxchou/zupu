<div align="center">

**中文** | [English](README.en.md) | [日本語](README.ja.md)

<img src="docs/cover.png" alt="家族族谱 · 传代树" width="100%">

# 家族族谱 · 传代树 (Zupu)

**单文件 · 零依赖 · 本地优先的开源族谱应用**

[![Version](https://img.shields.io/badge/version-v15.32-b03a2e)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-52%20passing-2f6390)](tests)
[![Dependencies](https://img.shields.io/badge/dependencies-0-3c7a4e)]()
[![License](https://img.shields.io/badge/license-MIT-8a7d68)](LICENSE)
[![在线试用](https://img.shields.io/badge/在线试用-点击演示-b03a2e)](https://zaxchou.github.io/zupu/)

*把修谱这件事，放回每个家庭的电脑里。*

</div>

---

一个 **HTML 文件**就是全部：双击打开，为你的家族建一棵传代树。
不联网、无账号、无服务器，数据只存在你自己的浏览器里，编辑即自动保存。

| 常规传代树 | 谱书竖排（古法） |
| --- | --- |
| ![常规传代树](docs/preview-tree.png) | ![谱书竖排](docs/preview-vertical.png) |

**谱书竖排**按传统修谱版式还原：世代成行、名字竖书（右→左）、行左标世数、墨字吊线——
打印 / 导出 PDF 即可**装订成册**。

## ✨ 功能

- **两种视图** — 常规传代树 / 谱书竖排（古法），打印跟随视图模式
- **三种语言** — 中文 `index.html` / English `index-en.html` / 日本語 `index-ja.html`，
  界面与示例谱各自本地化，备份 json 三语通用
- **编辑齐全** — 添加 / 删除 / 改名 / 档案（性别、过继嗣子·嗣出·兼祧、字、号、止）、
  拖拽排序、拖动过继（防成环）、撤销重做
- **字辈定代** — 自定义字辈表，按名字自动推算每人世代，支持谱书世数基准对齐
- **谱序** — 谱名、堂号、源流世系、始祖记、家族来源，导出自动带上
- **配偶体例** — 谱书式显示（丁嘉 → 丁氏嘉）、按人指定 配 / 继配 / 娶 / 聘 / 侧室
- **导出** — PNG / PDF / **世系录（欧式五世一表）** / Markdown / 装订打印
- **无感保存** — 编辑即存（浏览器本地），换机用备份 json 一键恢复

## 🚀 快速开始

**方式〇（最快）**：直接打开在线版 → **[https://zaxchou.github.io/zupu/](https://zaxchou.github.io/zupu/)**

**方式一（本地使用，推荐）**：到 [Releases](https://github.com/zaxchou/zupu/releases) 下载 zip，
解压后按你的语言双击 `index.html`（中文）/ `index-en.html`（English）/ `index-ja.html`（日本語）。
首次使用会弹出向导：

- **先看看示例** — 用内置的赵钱孙李演示谱熟悉操作
- **从空白开始** — 填上你的谱名（如「李氏族谱」）和堂号，从第一代建起
- **导入备份** — 已有本工具导出的 json，直接恢复

**方式二**：`git clone` 本仓库后双击 `index.html`。

录入自己家族：双击名字改名、点「＋」添加成员、「视图 ▾ → 谱序」设置谱名 / 堂号 /
字辈表 / 源流——全部改成你家的。`samples/` 里有真实家族的使用示例可以导入参考。

## ❓ 常见问题

**数据存在哪里？会不会丢？**
存在你电脑的浏览器里（localStorage），不上传任何服务器。定期用「文件 ▾ → 备份到文件」
导出 json 即可万无一失；换电脑用「恢复备份」导入。

**支持多人协作 / 在线同步吗？**
不支持，这是刻意的设计选择：族谱数据私密且低频编辑，本地单文件是最稳妥的形态。
多人协作请共享备份 json，各自导入修改后再合并。

**界面文字 / 字辈 / 谱名都是别人家的？**
示例而已——谱序里全部可改，字辈表粘贴你自己家族的字辈即可。

**浏览器数据清了会怎样？**
所以请备份。`data.json` 是仓库内置的示例快照；你自己的备份在你手里。

## 🤝 参与贡献

Issue / PR 都欢迎：`handoff.md` 里有完整的架构说明与踩坑记录，改代码前建议先读；
提交前请跑通 `tests/` 全部用例。见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 License

[MIT](LICENSE) © zaxchou
