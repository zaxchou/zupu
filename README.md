<div align="center">

<img src="docs/cover.png" alt="潮阳泗水周氏族谱" width="100%">

# 潮阳泗水周氏族谱 · 传代树

**单文件 · 零依赖 · 谱书竖排（古法） · 无感自动保存**

[![Version](https://img.shields.io/badge/version-v15.29-b03a2e)](https://github.com/zaxchou/zupu)
[![Tests](https://img.shields.io/badge/tests-45%20passing-2f6390)](tests)
[![Dependencies](https://img.shields.io/badge/dependencies-0-3c7a4e)]()
[![License](https://img.shields.io/badge/license-MIT-8a7d68)](LICENSE)

*濂溪周氏 · 潮阳泗水 · 申锡堂*

</div>

---

双击 **`index.html`** 即可使用——不需要安装、不需要联网、不需要数据库。
数据自动保存在本浏览器，像 Gmail 草稿一样无感，没有保存按钮。

## 界面预览

| 常规传代树 | 谱书竖排（古法） |
| --- | --- |
| ![常规传代树](docs/preview-tree.png) | ![谱书竖排](docs/preview-vertical.png) |

**谱书竖排**：世代成行、名字竖书（右→左）、行左标世数——按参考谱书版式还原，
打印 / 导出 PDF 即可**装订成册**。

## ✨ 功能

- **两种视图** — 常规传代树 / 谱书竖排（古法），打印跟随视图模式
- **谱书竖排** — 世代成行、名字竖书、行左标世数、墨字吊线
- **编辑齐全** — 添加 / 删除 / 改名 / 档案（性别、过继嗣子·嗣出·兼祧、字、号、止）、
  拖拽排序、拖动过继（防成环）、撤销重做
- **字辈定代** — 40 代字辈表自动推算每人世代，支持谱书世数基准对齐（如勤字辈 = 廿三世）
- **谱序** — 堂号（申锡堂）、源流世系、始祖记、家族来源，随导出自动带上
- **配偶体例** — 谱书式显示（丁嘉 → 丁氏嘉）、按人指定 配 / 继配 / 妻 / 聘 / 侧室
- **导出** — PNG / PDF / **世系录（欧式五世一表）** / Markdown / 装订打印
- **无感保存** — 编辑即存（浏览器本地），换机用备份 json 一键恢复

## 🚀 快速开始

```bash
git clone https://github.com/zaxchou/zupu.git
# 双击打开 index.html
```

换电脑：旧机「文件 ▾ → 备份到文件」→ 新机「恢复备份」导入即可。

## 🧪 开发与测试

```bash
python -m http.server 8931        # 起本地服务
cd tests
python runner.py                  # 10 模块 45 用例（Playwright）
```

## 📁 结构

```
index.html            # 应用本体（单文件，含谱序与字辈种子数据）
data.json             # 数据快照（随仓库同步）
docs/                 # 封面与界面截图
tests/                # Playwright 测试套件
handoff.md            # 架构、踩坑记录、版本时间线（v1 → v15.29）
```

## 📄 License

[MIT](LICENSE) © zaxchou
