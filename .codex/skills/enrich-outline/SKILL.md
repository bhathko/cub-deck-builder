---
name: enrich-outline
description: 使用者要求「豐富/擴充/強化大綱」,或想在產 PPT 前把大綱補到能撐起多樣版型時使用。照 cub-deck-builder repo 的豐富訪談流程在本機執行:存原稿→對照版型庫結構詞彙提案(結構增補標明解鎖頁型;數字事實只能問使用者)→使用者核准→產出含 [補] 標記的核准版大綱→交給 outline-to-ppt 產檔(管線帶 --original 驗豐富鏈)。Triggers:「幫我豐富大綱」「大綱太單薄」「enrich outline」「先幫我把大綱補好再做簡報」。
---

# enrich-outline(Codex 本機版大綱豐富訪談)

產檔**前**的訪談步驟:陪使用者把大綱補到能撐起多樣版型,核准後才交給
`outline-to-ppt` skill 產檔。完整規則的單一真相來源是
`engine/rules/enrich_outline_skill.md`(把 `/mnt/data` 路徑換成 `ppt_out/`,
其餘照用);本檔只列本機執行的路徑與交接點。

## 為什麼有這步

版型庫大多數頁型需要特定語意結構(時序、循環、對比、層級、數據),平鋪直敘
的大綱在「不捏造」原則下只能映射到少數通用版型。解法不是放鬆防捏造,而是把
內容創作移到使用者仍是作者的階段——由使用者核准的增補,才成為新的內容來源。

## 鐵律(詳見 engine/rules/enrich_outline_skill.md)

1. 數字與事實只能來自原稿或使用者本次對話的明確回覆;你可以問「有改善前後的
   數據嗎?」,嚴禁自己寫「效率提升 30%」。缺料用「待補充」。
2. 核准版裡凡非原稿逐字的行,**行首標 `[補] `**(可保留縮排,標記在項目符號
   之前)。稽核工具會硬驗:未標記行必須逐字出現在原稿。
3. 原稿先落檔、不可事後改動。
4. 每個增補標明解鎖哪個頁型(全集跑
   `python ppt_out/tools/make_skeleton.py --list`,先跑一次
   `python .codex/skills/outline-to-ppt/prepare_env.py` 準備沙箱)。
5. 唯一確認關卡=核准豐富後大綱全文;使用者拒絕就用原稿直接產檔,不糾纏。

## 本機流程

1. 收到原文先覆寫 `ppt_out/outline_original.txt`(逐字,不得沿用前次)。
2. 跑 `--list` 盤點結構詞彙,在聊天中提出增補提案(結構增補/資料提問/佔位
   增補三類,逐項標明解鎖頁型),等使用者逐項回覆。
3. 整合核准版:原稿行逐字保留(可調順序),新增/改寫行行首標 `[補] `,
   缺料處「待補充」。全文貼給使用者做最終確認。
4. 確認後覆寫 `ppt_out/outline_source_current.txt`,接著走 `outline-to-ppt`
   skill 的大綱模式;唯一差別是 `run_pipeline.py` **必加**
   `--original ppt_out/outline_original.txt`(稽核驗豐富鏈並回報增補統計)。
