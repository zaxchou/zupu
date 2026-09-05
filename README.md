<div align="center">

**中文（简体）** | [繁體中文](README.zh-Hant.md) | [English](README.en.md) | [日本語](README.ja.md)

<img src="docs/cover.jpg" alt="家族族谱 · 传代树" width="100%">

# 家族族谱 · 传代树 (Zupu)

**双击就能用的电子族谱：录入家人、自动算辈分、打印装订成册**

[![Version](https://img.shields.io/badge/version-v15.33-b03a2e)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-53%20passing-2f6390)](tests)
[![Dependencies](https://img.shields.io/badge/dependencies-0-3c7a4e)]()
[![License](https://img.shields.io/badge/license-MIT-8a7d68)](LICENSE)
[![在线试用](https://img.shields.io/badge/在线试用-点击演示-b03a2e)](https://zaxchou.github.io/zupu/)

*把修谱这件事，放回每个家庭的电脑里。*

</div>

---

**一个 HTML 文件就是全部**：双击打开就能用，发给家人也能用。
不联网、无账号、不用安装，数据只存在你自己电脑的浏览器里，改一个字就自动保存一次。

## ✨ 它能帮你做什么

- **像填表格一样录家人** — 点「＋」加人、双击改名字、拖动卡片调长幼次序，
  拖到别人名下就是过继；做错了 Ctrl+Z 随时撤销
- **名字写上，辈分自动算** — 把你家的字辈贴进去（如“德承传世泽”），每个人是第几代自动标出来；
  还能对齐老谱：老谱记“廿三世”，这里也显示“廿三世”
- **打印出来是一本老谱的样子** — 竖排文字、世代成行、五代一张表，导出 PDF 直接送打印店装订成册；
  谱名、堂号、源流、始祖记都自动印在谱前
- **配偶写法跟着老谱走** — 「丁嘉」显示成「丁氏嘉」；
  配 / 继配 / 嗣子 / 嗣出 / 兼祧 / 止，老谱的体例这里都有
- **数据只在你自己手里** — 不联网、无账号、不上传任何服务器；
  一键导出备份文件，换电脑或传给亲戚，双击导入就回来
- **几十年后也打得开** — 不依赖任何软件和服务：一个 HTML 文件，U 盘里存一份就能传给下一代

| 常规传代树 | 谱书竖排（古法） |
| --- | --- |
| ![常规传代树](docs/preview-tree.png) | ![谱书竖排](docs/preview-vertical.png) |

**谱书竖排**按传统修谱版式还原：世代成行、名字竖书（右→左）、行左标世数、墨字吊线——
打印 / 导出 PDF 即可**装订成册**。

## 🚀 快速开始

**方式〇（最快）**：直接打开在线版 → **[https://zaxchou.github.io/zupu/](https://zaxchou.github.io/zupu/)**

**方式一（本地使用，推荐）**：到 [Releases](https://github.com/zaxchou/zupu/releases) 按语言下载——
简体 `index.html` / 繁體 `index-zh-Hant.html` / English `index-en.html` / 日本語 `index-ja.html`，
一个文件就是全部，下载双击即用。首次使用会弹出向导：

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
