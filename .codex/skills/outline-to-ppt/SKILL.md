---
name: outline-to-ppt
description: 使用者在聊天窗貼上簡報大綱(段落文字)或 slide_spec.json、要求產出 PPT/簡報時使用。照 ppppai repo 的 GPTs 確定性管線在本機執行:大綱→slides.md→make_skeleton→slide_spec.json→run_pipeline(稽核→驗證→渲染→QA)→交付 Cathay 淺色風 16:9 繁中可編輯 .pptx。Triggers:「幫我把大綱轉成簡報/PPT」「產出 PPT」「outline to ppt」「這是我的 slide_spec.json 幫我產檔」。
---

# outline-to-ppt(Codex 本機版 GPTs 簡報產生器)

這是 `ppppai` repo GPTs 建置包的本機執行版:所有機械動作由 repo 既有腳本完成,
你只負責四件事——**切頁、選頁型、把來源文字填入骨架槽位、跑指令並如實轉述結果**。
渲染層零隨機且冪等:同一份輸入重跑一萬次結果都一樣,所以修錯永遠是
「改輸入的某一條 → 整條重跑」。

規則細節的單一真相來源在 repo(以下皆相對 repo 根目錄):

- `engine/rules/outline_to_ppt_skill.md` — 大綱模式完整規則(GPTs 版;把
  `/mnt/data` 路徑換成本文的 `ppt_out/`,其餘規則照用)
- `engine/rules/page_types_registry.md` — 11 種註冊頁型的槽位契約(填槽前必讀)
- `engine/tools/README_TOOLS.md` — 錯誤→修法對照表 + 工具鐵律(FAIL 時必讀)

## 鐵律

1. **內容忠實**:使用者原文是唯一內容來源。嚴禁發明數字、KPI、日期、專案名、
   報告人、結論。缺料欄位一律填固定字串「待補充」(來源已標「待補充/待確認/
   待定/TBD」者原樣沿用)。可不依來源產生的值只有:agenda 順序編號、比較頁
   固定標題「改善前/改善後」、closing 的 `Thank you`。
2. **大綱模式只用 11 種註冊頁型**(validator `PAGE_TYPES` 為準),禁止未註冊
   頁型、禁止 render_plan。缺資料不是換版面的理由——照樣建頁、缺欄填「待補充」。
3. **骨架必用 `make_skeleton.py`**,禁止徒手建 JSON 結構、頁碼、素材路徑。
4. **禁止現寫 Python 取代管線腳本**;禁止手動修補 `deck.pptx` 產出。
5. **不生圖**:全部是 PowerPoint 可編輯物件。
6. **FAIL 是修正循環的入口,不是停止條件**:最多自動修三輪,三輪內不得宣稱
   「無法繼續」或把問題丟回使用者。唯一例外:註冊頁型出現 `FillError` →
   立即停止並回報(模板改版問題,不得用 clone plan 硬繞)。
7. **交付判準**:`run_pipeline.py` 完整輸出最後一行是 `管線結果:PASS` 才算成功;
   qa 階段允許先有 WARN(有一行以 `結果:PASS` 開頭即可),警告必須如實回報。

## 跨平台約定(macOS / Linux / Windows PowerShell / cmd 通用)

本文所有命令都是**單行 `python` 呼叫、相對路徑、不用任何 shell 變數與續行**,
在 bash、PowerShell、cmd 原樣可執行,唯二差異:

1. **直譯器名稱**:Windows 通常是 `python`(或 `py -3`);macOS/Linux 沒有
   `python` 就用 `python3`。下文一律寫 `python`,自行代換。
2. **渲染前綴**:步驟 0 的 prepare_env 會印出「渲染指令前綴」。若印的是
   `uv run --with python-pptx python`,則**含渲染/QA 的命令**(run_pipeline、
   qa_check、inspect_template)開頭的 `python` 換成該前綴(此語法三種 shell
   相同);make_skeleton、audit_provenance 只用標準庫,一般直譯器即可。

路徑一律正斜線,Python 在 Windows 也吃。另沿用 repo 鐵律:任何 zip 打包禁用
`Compress-Archive`/檔案總管(反斜線路徑會弄壞 GPTs 沙箱解壓),一律用 Python
`zipfile`——本 skill 流程不打包,僅提醒。

## 步驟 0:環境準備(每次 session 先跑)

在 repo 根目錄執行(不在時先 cd,或加 `--repo <repo路徑>`):

```
python .codex/skills/outline-to-ppt/prepare_env.py
```

腳本會把工具鏈複製成 `ppt_out/` 沙箱(模擬 GPTs /mnt/data 佈局:`assets/`、
`tools/`、`templates/`(模板包,含模板本體)、validator;副本一律以 repo 為準
冪等覆蓋),逐項列出檔案檢查,
並印出「渲染指令前綴」。**環境是否就緒只以本腳本 exit 0 判定**,不得未執行
先宣稱做不到。`ppt_out/` 已 gitignore,嚴禁 commit。

## 模式 A:大綱模式(預設——使用者貼的是段落文字)

中途不要求使用者確認切頁、頁型或 JSON,不拋 A/B 選單;只有環境缺檔、來源不足、
或三輪修正後仍 FAIL 才停止。

1. **保存來源**:把本次收到的完整原文逐字覆寫 `ppt_out/outline_source_current.txt`
   (不得沿用或附加前一次內容)。
2. **切頁**:以來源逐字摘錄覆寫 `ppt_out/slides.md`,每頁一個 `## Slide N` 區塊。
   可調整段落順序、同段可支援多頁,但每一行都必須是原文的逐字片段,不得改寫
   補寫。頁型選擇規則(詳見 `outline_to_ppt_skill.md` §2),重點:
   - 至少一頁真內容頁(`page_type` 非 cover/agenda/closing)且其標題有來源支持;
     整份來源擠不出任何一頁才算「來源不足」而停止。
   - `agenda` 只在原文可形成 3–6 項時使用;`cover` 有主標題即可用,缺副標/日期/
     報告人填「待補充」;`closing` 的 `main_title` 與頂層 `title` 固定 `Thank you`。
   - KPI/數據比較/雙軌時程頁型:原文有對應數值或時間標籤時優先用;使用者點名
     但缺數據時仍可用,缺值填「待補充」。個別缺料一律「佔位並繼續」,不整體停止。
3. **產骨架**(把頁型清單換成本次實際頁序;使用者指名「用○○模板」時加
   `--template-pack <模板id>`,骨架自動寫入 `deck.template`,頁型候選改為
   該包全自動集合——先 `--list --template-pack <模板id>` 查;未指名=light):

   ```
   python ppt_out/tools/make_skeleton.py --types cover,agenda,info_three_column_category,closing --out ppt_out/slide_spec.json
   ```

4. **填槽**:對照 `page_types_registry.md` 的槽位契約,把每個 `【欄位名】待填`
   換成來源支援的內容;缺料欄位換成「待補充」。完成後搜尋 JSON 確認零殘留
   `待填`。`deck.deck_name` 必須完全等於第一頁真內容頁的頂層 `title`,且該
   `title` 逐字出現在對應 `slides.md` 區塊(不得保留骨架預設 `my_deck`)。
   為符合字數上限可縮短,但不得改原意、不得動到數字。
5. **一條指令跑完管線**(稽核→驗證(自動帶 `--slides --registered-only --strict`)
   →渲染→QA,任一階段 FAIL 即停,不產半成品):

   ```
   python ppt_out/tools/run_pipeline.py --spec ppt_out/slide_spec.json --slides ppt_out/slides.md --source ppt_out/outline_source_current.txt --asset-dir ppt_out --out ppt_out/deck.pptx
   ```

6. **FAIL 時**:讀「管線停止於階段 N」該段輸出,逐條對照
   `engine/tools/README_TOOLS.md` 的錯誤→修法表**修對應輸入**,然後整條重跑同一
   指令。最多三輪;稽核 FAIL 時刪除不受支持的內容或重新切頁,禁止把新文字補進
   `slides.md` 來遷就 spec。三輪後仍 FAIL 才停止,白話列出剩餘錯誤,不交付產物。
7. **交付**:給出 `ppt_out/deck.pptx` 與 `ppt_out/slide_spec.json` 路徑;摘要只列
   頁數、驗證通過、QA 通過、如實列出 WARN、以及「待補清單」(仍為佔位符的頁
   與欄位,沒有就寫無)。不要把整份 JSON 貼進對話。提醒使用者用 PowerPoint
   開啟檢查文字溢出(中文寬度估算不準,溢出要人工看)。

## 模式 B:直供 JSON 模式(使用者給的是 slide_spec.json)

內容正確性由 JSON 作者負責。存成 `ppt_out/slide_spec.json` 後,跑同一條管線但
**不帶** `--slides`/`--source`(追溯自動關閉,缺來源 WARN 是預期結果,兩級頁型
行為保留)。spec 的 `deck.template` 自動生效(省略=light),不需任何額外參數;
指定模板不支援某頁型時 validator 會擋下並列出該包支援清單:

```
python ppt_out/tools/run_pipeline.py --spec ppt_out/slide_spec.json --asset-dir ppt_out --out ppt_out/deck.pptx
```

此模式允許 `page_types.md` 的未註冊頁型:先加 `--validate-only` 過閘門,再照
`README_TOOLS.md` 寫該頁的 `render_plan.json`(查參考頁形狀用
`inspect_template.py --page N`,不要 dump 整份模板),加 `--plan` 完整重跑。

## 快速除錯(單獨執行,正式產檔仍一律走 run_pipeline)

```
python ppt_out/tools/audit_provenance.py --spec ppt_out/slide_spec.json --slides ppt_out/slides.md --source ppt_out/outline_source_current.txt
python ppt_out/tools/inspect_template.py --pptx ppt_out/templates/light/template.pptx --summary
```

第一條在填槽迭代時快跑稽核(標題逐字/deck_name/精確數字 token);第二條做模板
盤點(省 token:只用 `--summary` 或 `--page N`)。
