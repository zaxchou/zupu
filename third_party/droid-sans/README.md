# DroidSansFallbackFull

`DroidSansFallbackFull.ttf` is bundled for offline, searchable single-page vector PDF exports. The bundled font file is unchanged; exported PDFs embed a subset of the glyphs they use. This font supplies common characters and does not cover all Unicode characters.

A separate [ZupuRareSupport fallback font](../zupu-rare-font/README.md), licensed under SIL OFL 1.1, supplies U+28EE7 (𨻧), U+20BB7 (𠮷), U+212A8 (𡊨), and U+20000 (𠀀). The two fonts are embedded independently with their original Unicode text preserved; the Droid font remains under Apache-2.0. This is not full CJK Extension B or full Unicode coverage.

The export dialog also lets the user select a local TrueType font with permission to embed it for that export. It can supply missing glyphs while the default fonts remain available for other characters; one custom TTF no longer needs to cover the entire tree. If none of the available fonts contains a required glyph, export fails with an explicit missing-character error. Photos remain images.

- Source: Android Open Source Project, [`platform/frameworks/base`, tag `android-4.4_r1`, `data/fonts/DroidSansFallbackFull.ttf`](https://android.googlesource.com/platform/frameworks/base/+/android-4.4_r1/data/fonts/DroidSansFallbackFull.ttf).
- Copyright: (c) 2005–2008, The Android Open Source Project.
- License: [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
- Attribution and license text: local [NOTICE](NOTICE), matching the [upstream NOTICE](https://android.googlesource.com/platform/frameworks/base/+/android-4.4_r1/data/fonts/NOTICE).
- Font SHA-256: `97320619b0f1ce4a7cda74cf064a0ce44ef3091287bc42755597e177cccf94c2`.

The Xiaohongshu mini-tool package omits both bundled PDF fonts and the PDF backend because its container cannot save PDFs. It includes the updated generation-number and generation-name sequence rules.
