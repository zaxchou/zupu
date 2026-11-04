# ZupuRareSupport

A small, renamed subset of **Plangothic P1 Regular**, bundled as a separate PDF fallback font. It contains U+20000 (𠀀), U+20BB7 (𠮷), U+212A8 (𡊨), and U+28EE7 (𨻧). It does not provide full CJK Extension B coverage.

The PDF writer embeds this font independently from the Apache-licensed DroidSansFallbackFull font. Common characters keep the default font, and supported rare characters use this fallback with their original Unicode values and searchable text. An optional local static TrueType font can provide other missing characters.

- Upstream: [Plangothic Project](https://github.com/Fitzgerald-Porthmouth-Koenigsegg/Plangothic_Project).
- Pinned release: [V2.9.5795 / PlangothicP1-Regular.ttf](https://github.com/Fitzgerald-Porthmouth-Koenigsegg/Plangothic_Project/releases/download/V2.9.5795/PlangothicP1-Regular.ttf).
- Upstream commit: `51485203670f18b6f5fa40913ffcde55027ddcb1`.
- Upstream SHA-256: `550b5d0775b15405946b18f4843df439a51e69508d7e6778d94c1f7a53dc5ad6`.
- License: [SIL Open Font License 1.1](OFL.txt). Copyright notices are preserved in the font's name table and the bundled license.
- Changes: subset to the four code points above; family/full/PostScript names changed to `ZupuRareSupport`; modification notice and full OFL text retained inside the font. Original reserved font names are not used as the derivative's family name.
- Bundled font SHA-256: `3dd8511d502ea3aa537a8ce0c91a18ebbcdd59e2595d550a46df57110475b92a`.

The main application remains usable offline as a single HTML file. The Xiaohongshu package strips both PDF fonts and the PDF engine because the container does not expose PDF saving.
