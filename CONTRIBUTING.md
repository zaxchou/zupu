# 贡献指南

感谢关注！这是一个刻意保持「单文件、零依赖、本地优先」的项目，贡献前请先认同这个边界：
**不引入服务器、构建步骤、外部依赖与在线功能。**

## 开发环境

- 任意现代浏览器（Chrome / Edge）
- 跑测试需要：Python 3.10+ 与 `pip install playwright`（Chromium 用本机缓存）

## 改代码

1. 先读 `handoff.md`——里面有完整架构说明、数据约定与历史踩坑（§8），能避免重复踩坑；
2. 主文件是 `index.html`（单文件应用），数据真源在浏览器 localStorage，
   `data.json` 只是仓库快照；英文/日文版（`index-en.html` / `index-ja.html`）
   由 `tools/build_i18n.py` 从母本生成——改完母本重跑一次，失配会逐条报告；
3. 保持三个不引入：不加构建工具、不加运行时依赖、不加网络请求。

## 跑测试

```bash
python -m http.server 8931     # 仓库根目录起服务
cd tests
python runner.py               # 全部用例必须绿
```

测试全部基于 Playwright 无头浏览器，跑在 `tests/_out/fixture*.html` 夹具上，
不会触碰 `index.html` 的真实数据。

## 提交

- 一个 PR 聚焦一件事，附截图（改了视觉的话）
- commit message 用一句中文说明「做了什么」
