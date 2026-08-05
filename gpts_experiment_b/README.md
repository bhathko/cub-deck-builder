# gpts_experiment_b — 實驗B(自由版)

給設計師 A/B 試用的兩個實驗 GPT 之一。**實驗B = 需求方想要的「自由發揮」方向**:
只有封面/目錄/封底走公司模板與工具鏈,中間內容頁由 GPT 用 python-pptx 自由設計
——制式 content_bg 底圖與左下角 logo 由 layout 自帶,品牌六色、微軟正黑體與
**字級層級表**照 [`freeform_playbook.md`](freeform_playbook.md) 的硬規範。

工具 zip 與正式版完全相同(本包不改任何工具);模板 zip 為 content_bg 底圖
改版(`light@2026-08-03.2-expA`,**與實驗A 共用同一份**,改版細節見
`../gpts_experiment_a/README.md`)。結構三頁仍有 validator + qa_check 守門;
中間頁只有 QA-lite(溢出/重疊掃描),**版面品質與內容忠實主要靠模型自律與
人工目檢**。

## 兩個實驗版在比什麼

| | 實驗A(`../gpts_experiment_a`,守門版) | 實驗B(本包,自由版) |
| --- | --- | --- |
| 封面/目錄/封底 | 公司模板,引擎產 | 公司模板,引擎產(相同) |
| 中間內容頁 | 內建頁型庫選版,渲染零隨機 | GPT 用 python-pptx 自由設計 |
| 中間頁外觀 | content_bg 底圖 + logo 左下(模板 layout 統一給) | content_bg 底圖 + logo 左下(同一 layout,相同) |
| 版面品質保證 | validator + qa_check 全程把關 | QA-lite(溢出/重疊/字級/字體/品牌色/頁碼)+人工目檢 |
| 內容不捏造 | 程式稽核(字數/數字/追溯) | 只靠 prompt 自律,**無程式稽核** |
| 版面多樣性 | 受頁型庫限制 | 不受限,但品質隨模型發揮浮動 |
| 同一輸入重跑 | 結果完全相同 | 每次版面可能不同 |

## 本機實測已驗證的部分

`examples/demo_deck_expB.pptx` 是本機照本包流程實測的樣張(6 頁:模板封面/
目錄/封底 + 三張自由頁:並列卡片、大數字 KPI、水平時間軸),**2026-08-05
依設計師視覺規範重產**,內容與 08-03 初版逐字相同,只換視覺:

- 結構三頁 spec(`spec_structural.example.json`)validator + qa_check PASS
- 三張自由頁新版 QA-lite(溢出/重疊/字級/字體/品牌色/頁碼/安全區)零紅字
- 頁碼 p2–p5 全部 28pt 粗體 `344252` @6.72"、單位數不補零,自由頁與工具鏈
  產的目錄頁完全一致
- qa_check 對自由頁**無法把關**(會誤判成量錯的模板槽位)——這是實驗B 的
  已知限制,也是兩版的本質差異,所以流程規定 qa_check 只在插入自由頁前的
  結構檔上跑

重產時抓到兩個舊版沒發現的破版(新版 QA-lite 打在 08-03 初版是 `FAIL(33)`):
三欄卡片欄寬 3.95"×3 撞出右邊界、卡片底邊與時間軸現況卡侵入右下頁碼淨空區。
舊版 11pt@6.95" 的頁碼遮不到所以看不出來,換成 28pt@6.72" 就會撞。安全區檢查
已併進 playbook 第四節的 QA-lite,三欄實測安全值寫進第三節。

> ⚠ 沙箱無中文字型,**這份樣張的人眼目檢尚未做**;交給設計師前請先在
> PowerPoint 開檔確認標題區(32pt 大標 + 綠豎條)與 28pt 頁碼的視覺比重。

## 試用方式

1. 照 [`DEPLOY.md`](DEPLOY.md) 把本包上到 GPT Builder(獨立新 GPT,別動正式版)。
2. 設計師把 `examples/sample_outline.md` **同一份大綱**分別餵給實驗A 與實驗B;
   實驗B 建議同一份大綱跑兩次,順便看版面穩定度。
3. 並排開檔目檢:版面美感、品牌一致性、文字溢出、可編輯性、內容忠實。
4. 回饋記到 `../docs/FEEDBACK.md`。

## 檔案

- `instructions.md` — 貼進 Builder 的指示全文(v1.1-expB-20260805)
- `freeform_playbook.md` — 自由頁設計手冊(硬規範+字級表+可照抄程式範式+QA-lite),上傳 Knowledge
- `spec_structural.example.json` — 三頁結構 spec 範例,上傳 Knowledge
- `DEPLOY.md` — 發版操作稿
- `dist/` — tools.zip + template_light.zip(與 `gpts/dist/` 完全相同)
- `examples/sample_outline.md` — 設計師試用的共同輸入大綱(與實驗A 同一份)
- `examples/demo_deck_expB.pptx` — 本流程實測樣張
