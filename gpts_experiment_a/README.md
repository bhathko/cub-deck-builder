# gpts_experiment_a — 實驗A(守門版)

給設計師 A/B 試用的兩個實驗 GPT 之一。**實驗A = 現行守門流程**:
封面/目錄/封底三頁固定走公司模板,中間頁由系統從內建頁型庫(33 種全自動
+ 半自動 clone)選版,產檔前後都有程式閘門把關。引擎工具與規則與正式版
`gpts/` 完全相同;**模板為 content_bg 底圖改版**——中間內容頁一律以
`content_bg.png` 為滿版背景+左下角 logo,與實驗B 產出外觀一致,所以設計師
比的是「守門流程 vs 自由發揮」的品質差異,不是兩種視覺風格。

底圖改版做法(可重現):在 light@2026-08-03.1 的 template.pptx 上,把內容頁
layout「只有標題」與「空白(白底)」設 `showMasterSp=0`(隱藏母片原底圖
「圖形 4」與角落裝飾「矩形 23/24」),鋪上 `assets/backgrounds/content_bg.png`
滿版為背景,再把母片同一顆 logo(「圖片 22」,位置 0.31", 6.98", 1.86"×0.4",
與封面/目錄的 logo 同位)補回這兩個 layout;封面/目錄/封底 layout 與所有
頁面形狀都未動,綁定 shape id 不受影響。版本 `light@2026-08-03.2-expA`,
manifest sha 已同步。

## 兩個實驗版在比什麼

| | 實驗A(本包,守門版) | 實驗B(`../gpts_experiment_b`,自由版) |
| --- | --- | --- |
| 封面/目錄/封底 | 公司模板,引擎產 | 公司模板,引擎產(相同) |
| 中間頁外觀 | content_bg 底圖 + logo 左下(模板 layout 統一給) | content_bg 底圖 + logo 左下(同一 layout,相同) |
| 中間頁版面 | 內建頁型庫選版,渲染零隨機 | GPT 用 python-pptx 自由設計 |
| 版面品質保證 | validator + qa_check 全程把關 | 僅 QA-lite(溢出/重疊掃描)+人工目檢 |
| 內容不捏造 | 程式稽核(字數/數字/追溯) | 只靠 prompt 自律,**無程式稽核** |
| 版面多樣性 | 受頁型庫限制 | 不受限,但品質隨模型發揮浮動 |
| 同一輸入重跑 | 結果完全相同 | 每次版面可能不同 |

## 試用方式

1. 照 [`DEPLOY.md`](DEPLOY.md) 把本包上到 GPT Builder(獨立新 GPT,別動正式版)。
2. 設計師把 `examples/sample_outline.md` **同一份大綱**分別餵給實驗A 與實驗B。
3. 並排開檔目檢:版面美感、品牌一致性、文字溢出、可編輯性、內容忠實。
4. 回饋記到 `../docs/FEEDBACK.md`。

## 檔案

- `instructions.md` — 貼進 Builder 的指示全文(自 `gpts/instructions.md` v2.21 衍生)
- `DEPLOY.md` — 發版操作稿
- `dist/tools.zip` — 與 `gpts/dist/` 完全相同
- `dist/template_light.zip` — content_bg 底圖改版 `light@2026-08-03.2-expA`(與實驗B 相同)
- `examples/sample_outline.md` — 設計師試用的共同輸入大綱
- `examples/demo_deck_expA.pptx` — 本流程實測樣張(6 頁:封面/目錄/三欄/KPI/時程/封底,
  qa_check 全綠、中間頁 content_bg 底圖+左下 logo);`examples/demo_spec.json` 是它的 spec
