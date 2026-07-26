# slide_spec.json 撰寫指南(頁型註冊表)

使用者只需提供這一份 JSON,GPTs 就會驗證並用內建模板產出 PPT——模板、背景、logo
都已內建,不需要上傳任何檔案。完整可跑的範例見知識庫 `slide_spec.example.json`。

## 整體結構

```json
{
  "deck": {
    "deck_name": "my_deck",
    "language": "Traditional Chinese",
    "slide_count": 10
  },
  "slides": [
    {
      "number": 1,
      "page_type": "cover",
      "title": "頁面標題",
      "render_page_number": false,
      "assets": {
        "background": "assets/backgrounds/cover_bg.png",
        "logo": "assets/logos/cathay_logo.png"
      },
      "slots": { "...": "依頁型而定,見下方各頁型表" }
    }
  ]
}
```

- `deck.template`(選填)= 模板包 id,**省略等同 `"light"`**;整份簡報只用一種
  模板。指定的模板不支援某頁型時驗證器會擋下並列出該模板的支援清單。
- `deck.slide_count` 必須等於 `slides` 的實際頁數;`number` 從 1 連續編號、不可重複。
- 每頁必填:`number`、`page_type`、`title`、`slots`,並依頁型設定
  `render_page_number` 與 `assets`。
- `assets` 一律填內建素材路徑:背景用 `assets/backgrounds/cover_bg.png`(封面/封底)、
  `assets/backgrounds/cover_bg_context.png`(情境封面)或
  `assets/backgrounds/content_bg.png`(內容頁);logo 固定 `assets/logos/cathay_logo.png`。

## 頁型分兩級,選擇時優先用第一級

1. **已註冊頁型(本檔下列 21 種)**:驗證器有完整槽位契約——槽位名稱、數量與
   字數上限必須完全符合,否則以 ERROR 擋下、不會產檔。字數上限以「字元數」計
   (含標點與空白)。**這 21 種由 render_deck.py 全自動產出**(內建版面或
   自動填入模板頁),版面不經過任何 AI 判斷,同一份 JSON 產一萬次結果相同。
2. **頁型庫其他頁型(知識庫 `page_types.md` 的 30+ 種)**:允許使用,`page_type` 填
   `page_types.md` 中的英文頁型名(如 `cycle_four_point_loop`),`slots` 欄位名
   可依內容自訂(建議語意化,如 `steps`、`center_theme`)。驗證器對這些頁型只做
   基本檢查,**容量與使用限制必須自行比照 `page_types.md` 該頁型的「內容容量」節**。
   版面依選定模板包的 `template.pptx` 對應頁重建(「頁型→模板第幾頁」查該包
   `page_map.md`;模板不支援的頁型該檔標 unsupported)。

> 內容正確性由撰寫 JSON 的人負責:此模式沒有內容來源檔可回溯比對,驗證器擋的是
> 結構、數量、字數、頁碼與素材;GPTs 被禁止改寫你 JSON 裡的任何文字與數字。

**草稿佔位符**:資料還沒到位的欄位可以先填固定字串「待補充」(也接受「待確認」
「待定」「TBD」),先產出簡報結構、之後補資料重跑。佔位符不做來源追溯,但它以外
的文字與數字照常嚴查;版面與頁型不因缺料而改變,永遠只用內建模板。

---

## cover — 封面
頁碼:無(`render_page_number: false`)。素材:background(用 `assets/backgrounds/cover_bg.png` 或 `cover_bg_context.png`)、logo。
| 槽位 | 型別 | 上限 |
|---|---|---|
| main_title | 文字 | 20 字 |
| subtitle | 文字 | 20 字 |
| date | 文字 | 20 字 |
| presenters | 文字 | 40 字 |

## closing — 封底
頁碼:無。素材:background(用 `assets/backgrounds/cover_bg.png`)。
| 槽位 | 型別 | 上限 |
|---|---|---|
| main_title | 文字 | 20 字(固定 "Thank you") |

## agenda — 目錄
頁碼:必須(`render_page_number: true`)。素材:background、logo。
- `items`:清單 3–6 項,每項物件:
  - `number` 文字 ≤4 字(如 "01")
  - `title` 文字 ≤20 字
  - `subtitle` 文字 ≤60 字(選填)

## vision_goal_center_balance — 願景目標(中心平衡)
適用:一個核心目標 + 左右支撐重點 + KPI。頁碼:必須。素材:background、logo。
- `subtitle` ≤60 字
- `core_mission` ≤60 字
- `annual_goal` ≤60 字
- `projects`:清單 2–3 項,每項文字 ≤40 字
- `kpis`:清單 2–4 項,每項 `{label ≤30 字, value ≤12 字}`

## info_three_column_category — 資訊說明(三欄分類)
適用:3 個並列面向/模組的對照說明。頁碼:必須。素材:background、logo。
- `subtitle` ≤60 字
- `columns`:清單固定 3 欄,每欄:
  - `heading` ≤20 字
  - `points`:清單 2–6 項,每項 ≤40 字

## data_line_trend_comparison — 數據比較(折線趨勢)
適用:1–2 組指標在多個時間點上的趨勢比較。頁碼:必須。素材:background、logo。
**本頁型無 subtitle**(版面上方為圖表,無副標位置)。
- `categories`:清單 6–10 項(時間點標籤),每項 ≤8 字
- `series`:清單 1–2 組,每組:
  - `name` ≤8 字(圖例名)
  - `values`:清單 6–10 項,每項為**純數字字串**(如 `"42.5"`;禁單位與 %,
    百分比語意寫進 label/標題)。**每組 values 數必須等於 categories 數**。
- `rows`:下方說明列 2–3 列,每列 `{heading ≤8 字, cells 3–5 項 × ≤20 字}`

## data_two_group_metric_comparison — 數據比較(兩組前後對照)
適用:改善前後、兩方案的數字比較。頁碼:必須。素材:background、logo。
- `subtitle` ≤60 字
- `before`:`{heading ≤12 字(如 "改善前"), points 2–6 項 × ≤40 字}`
- `after`:同 before
- `kpis`:清單 2–3 項,每項 `{label ≤30 字, value ≤12 字}`

## evaluation_option_score_pros_cons — 方案評估(優缺點)
適用:2–3 個方案的優缺點評比。頁碼:必須。素材:background、logo。
- `subtitle` ≤60 字
- `recommended` ≤20 字(選填,如 "方案 B")
- `options`:清單 2–3 項,每項:
  - `name` ≤24 字
  - `pros`:1–4 項 × ≤60 字
  - `cons`:1–3 項 × ≤60 字
- `recommendation`:0–5 項 × ≤40 字(選填)

## story_chapter_statement — 故事情節(章節敘事)
適用:專案背景 + 過去/現在/未來敘事 + 預期成果。頁碼:必須。素材:background、logo。
- `subtitle` ≤60 字
- `background_points`:2–4 項 × ≤40 字
- `story`:清單固定 3 項,每項 `{phase ≤8 字, text ≤60 字}`
- `outcomes`:2–4 項 × ≤40 字

## pyramid_layered_maturity_detail — 金字塔(成熟度分層)
適用:4–5 層由下而上的能力/成熟度堆疊。頁碼:必須。素材:background、logo。
- `subtitle` ≤60 字
- `levels`:4–5 層,每層 `{label ≤20 字, detail ≤40 字}`
- `side_cards`:0–2 張(選填),每張 `{heading ≤16 字, points 2–4 項 × ≤30 字}`

## stage_dual_track_roadmap — 時程(雙軌 Roadmap)
適用:4 個季度 × 2 條工作軌 + 年度循環。頁碼:必須。素材:background、logo。
- `subtitle` ≤60 字
- `quarters`:固定 4 項 × ≤12 字
- `lanes`:固定 2 條,每條 `{name ≤40 字, cells 固定 4 格 × ≤40 字}`
- `annual_cycle`:3–6 項 × ≤12 字

## data_three_number_kpis — 數據摘要(三大數字 KPI)
適用:2–3 個最重要的 KPI、成果數字、規模指標或管理摘要。頁碼:必須。素材:background、logo。
- `subtitle` ≤60 字(**選填**;不給整框刪除,版面上方只留主標題)
- `kpis`:清單 2–3 項,每項:
  - `value` ≤6 字 — 大數字本體,可含單位或百分號(如 `"99.9%"`、`"1,200"`、`"3.5x"`);
    以 66pt 顯示,超過 4 個字元會自動縮字級,建議控制在 5 字內
  - `label` ≤12 字 — 數字下方的短標題(單行)
  - `detail` ≤30 字 — 補充說明 1–2 行
- 只有 2 個 KPI 時第 3 組(數字 + 標題 + 說明)整組刪除,不留空位;超過 3 個請拆頁,
  或改用 `data_table_kpi_chart_insights` / `data_kpi_bar_callout_dashboard`。

## info_horizontal_explanation_rows — 資訊說明(橫向說明列)
適用:同一主題下 4–5 條並列條目的逐條說明(規範、條件、欄位定義、常見問題)。
頁碼:必須。素材:background、logo。
- `subtitle` ≤60 字(頁面上方淡綠色主題帶,一句話點出本頁主題)
- `rows`:橫向說明列 4–5 條,每條:
  - `label` ≤12 字(左側短標籤,寫不下會自動縮字)
  - `points`:清單 1–3 項,每項 ≤40 字;1 項 = 一段說明,2–3 項 = 列點
    (同一列的多項會以換行併入同一個說明框,建議控制在 1–2 行)
- 模板左側直排類別標示與右上子導覽標籤會在渲染時移除(契約無此槽位,留著=捏造)。

## cycle_four_point_loop — 循環(四點閉環)
適用:PDCA、管理閉環、迭代改善、服務循環等**固定 4 步驟**的週期性流程。頁碼:必須。素材:background、logo。
- `subtitle` ≤60 字
- `center_theme` ≤10 字(中央循環箭頭內的循環主題,建議 4-8 字)
- `steps`:**固定 4 組**(左上 → 左下 → 右下 → 右上,依模板編號徽章順序),每組
  `{number ≤1 字(結構性序號,模板編號徽章僅 0.34 吋寬,只放單一數字 1-4,**不要寫 "01"** 會折行破版), label ≤12 字(步驟名稱,建議 4-8 字), detail ≤40 字(1-2 句說明)}`
- 中央圓內的示範「副標文字 / 重點文字」兩框由綁定刪除(契約無此槽位);`center_theme` 文字框會下移置中於循環箭頭。
- 若只有 3 步驟改用 `cycle_three_node_process`;6-10 步驟改用 `cycle_multi_step_loop`。四步文字量要接近,避免單側過重。

## phase_three_column_action_cards — 階段推進(三欄行動卡)
適用:3 個階段/3 種作法/3 個推進策略,每欄都要「列點 + 重點句 + 段落說明」。頁碼:必須。素材:background、logo。
**本頁型無 subtitle**(標題列下方直接接三欄箭頭標題,版面無副標位置)。
- `points_label` ≤6 字(左側上方層級標籤,如 "重點";結構字樣不追溯)
- `detail_label` ≤6 字(左側下方層級標籤,如 "說明";結構字樣不追溯)
- `phases`:清單固定 3 欄,每欄:
  - `heading` ≤12 字(箭頭式階段標題)
  - `points`:清單 3–5 項 × ≤16 字(卡片上半列點)
  - `highlight` ≤16 字(選填,卡片中段的一句重點強調;不填則整框刪除)
  - `detail` ≤60 字(卡片下半段落說明)

## stage_year_cards — 時程(年度策略卡)
適用:3 個年度 / 3 個策略階段 / 3 個版本演進的並列比較,中欄為當前年度或主推階段。頁碼:必須。素材:background、logo。
**本頁型無 subtitle**(主標題下方即年度線,版面無副標位置)。
- `stages`:清單固定 3 欄(左→中→右,中欄為模板上綠框強調欄),每欄:
  - `label` ≤8 字(年度或階段名,如 "2026";中欄字級較大,建議 ≤6 字)
  - `heading` ≤16 字(該年度短標題)
  - `highlights`:深色重點區塊 2–4 項 × ≤20 字
  - `details`:白色細項區塊 3–5 項 × ≤30 字

## info_card_grid — 資訊說明(卡片網格)
適用:6–8 個資訊點、規則、功能、風險或檢核項的平鋪說明。頁碼:必須。素材:background、logo。
版面為 2 列 × 4 欄共 8 格卡片(列優先填);卡片不足 8 張時從尾端刪格(連同卡片底框一併移除)。
- `subtitle` ≤60 字
- `cards`:清單 6–8 張,每張:
  - `heading` ≤10 字(卡片小標;模板框不換行,超過會擠到隔壁卡片)
  - `points`:清單 1–3 項,每項 ≤12 字(對應「1–2 句短說明」或「2–3 個短列點」;
    渲染時以換行併入同一個內文框,每項各佔一行)

**卡片文字必須短**:內文框一行約 13 字、至多 4 行,3 × 12 字已用滿 3 行;
需要長段落請改用 `info_three_column_category` 或 `info_horizontal_explanation_rows`。
頁面標題走 spec 頂層 `title`(標題中的重點字由模板既有 run 樣式承接)。

## stage_timeline_progress — 時程(單線時間軸進度)
適用:單一路線的時間軸、重要里程碑、目前進度與後續規劃(線性時程;多工作流併行請改用 `stage_phase_swimlane`)。頁碼:必須。素材:background、logo。
頁面標題用 slide 的頂層 `title`;右側「進行中 / 後續規劃」欄目標籤由模板固定提供,不佔槽位。
- `subtitle` ≤60 字
- `axis_labels`:時間軸刻度**固定 4 項** × ≤8 字(如 "2026 年"、"3 月"、"6 - 8 月");由左至右排列
- `milestones`:**固定 3 個**,每個 `{label ≤8 字, detail ≤40 字}`;
  順序 = 版面由左至右(第 1、2 個在時間軸上方,第 3 個在時間軸下方),
  `label` 要短(節點文字過長會讓時間軸擁擠)
- `current_status`:右側說明區 1 組,`{heading ≤12 字, points 1–2 段 × ≤60 字}`
  (points 兩段會以換行併入同一個說明框)

## info_before_after_item_compare — 資訊說明(前後項目對照)
適用:轉換前後、兩方案、兩群受眾、兩個系統的左右項目對照。頁碼:必須。素材:background、logo。
**本頁型無 subtitle**(標題下方即左右兩區塊,版面無副標位置)。
- `before`(左區塊,主色綠)與 `after`(右區塊,輔色藍)結構相同,各為:
  - `heading` ≤6 字(區塊標籤,如 "導入前"/"導入後";標籤框僅 1.32 吋寬 @20pt,7 字起爆框)
  - `items`:清單**固定 3 項**(左右數量必須一致 = 版面規定),每項:
    - `name` ≤12 字(項目名稱徽章)
    - `points`:清單 2–4 項,每項 ≤16 字(短列點;右欄說明框 3.37 吋 @14pt,一行 16 字、最多 4 行)
- 中央箭頭、左右底板、列間分隔線由模板提供,不佔槽位;右上子項目導覽標籤一律移除。

## vision_goal_keyword_orbit — 願景目標(關鍵詞環繞)
適用:一個願景中心 + 8–12 個環繞關鍵詞、價值主張或設計原則。頁碼:必須。素材:background、logo。
- `subtitle` ≤60 字
- `center_theme` ≤14 字(圓心願景短句;版面圓內只放這一句,**沒有中心補充說明欄位**)
- `keywords`:清單 8–12 項,每項 ≤8 字
  - **只放關鍵詞,不放句子**:版位字級 20–28pt、框寬約 2.2 吋,一行約 6 字,
    超過會自動縮字(最低 12pt),與鄰框字級不一致。
  - 填充順序為左右交錯(先左右兩個主要關鍵詞,再由上而下配對次要、最後輔助),
    項目少於 12 時從尾端刪格位,左右仍保持平衡;少於 8 個關鍵詞請改選
    `vision_goal_hub_spoke`(4–6 個並列目標)。

## phase_concept_three_column_explanation — 階段說明(概念三欄展開)
適用:一個核心概念展開成 3 個階段/面向/推進主軸,左側概念圖引導、右側三欄說明。
頁碼:必須。素材:background、logo。
**本頁型無 subtitle**(標題下方直接是三欄欄標,版面無副標位置)。
- `concept` ≤8 字(左側大圓內的核心概念)
- `concept_labels`:0–3 個(**選填**,左側品牌/關鍵標籤),每個 `{name ≤8 字, caption ≤4 字}`;
  給幾個就留幾個,沒給的標籤整組(圓形+文字)刪除
- `column_one`:`{heading ≤10 字, items 3–4 組}`,每組 `{label ≤12 字, detail ≤20 字}`
  (label 與 detail 同框兩行,故兩者字數上限偏緊)
- `column_two`:`{heading ≤10 字, points 3–5 項 × ≤36 字}`,只有 4 個格位,
  **第 5 項自動併入第 4 格**(該格加高至 1.10 吋)
- `column_three`:`{heading ≤10 字, points 4–6 項 × ≤24 字}`,只有 4 個格位,
  **第 5–6 項自動併入第 4 格**(該格加高至 1.45 吋)
- 三欄內容量應接近;欄標建議 4–10 字。若要精準流程或日期,改用時程說明頁型。
---

## light 模板的實際容量(**以本表為準**)

上方各節的字數是「語意契約的預設值」。**實際可寫多少,由選定的模板包決定**——
版位大小是設計師定的,字級也是設計過的,塞不下時請**改寫更短或換頁型**,
系統不會偷偷縮小字級來遷就。下表列出 light 包與預設值不同的槽位;
沒列出的槽位沿用上方數字。閘門依本表擋,寫超過會被退回。

| 頁型 | 槽位 | 預設 | light 實際 |
| --- | --- | --- | --- |
| cycle_four_point_loop | `steps[].detail` | ≤40 字 | **≤34 字** |
| cycle_four_point_loop | `subtitle` | ≤60 字 | **≤50 字** |
| data_line_trend_comparison | `rows[].cells[]` | ≤20 字 | **≤13 字** |
| data_three_number_kpis | `subtitle` | ≤60 字 | **≤50 字** |
| data_two_group_metric_comparison | `after.points` | 2–6 項 | **2–4 項** |
| data_two_group_metric_comparison | `after.points[]` | ≤40 字 | **≤16 字** |
| data_two_group_metric_comparison | `before.points` | 2–6 項 | **2–4 項** |
| data_two_group_metric_comparison | `before.points[]` | ≤40 字 | **≤16 字** |
| data_two_group_metric_comparison | `kpis[].label` | ≤30 字 | **≤8 字** |
| data_two_group_metric_comparison | `subtitle` | ≤60 字 | **≤50 字** |
| evaluation_option_score_pros_cons | `options[].cons` | 1–3 項 | **1–2 項** |
| evaluation_option_score_pros_cons | `options[].cons[]` | ≤60 字 | **≤17 字** |
| evaluation_option_score_pros_cons | `options[].name` | ≤24 字 | **≤9 字** |
| evaluation_option_score_pros_cons | `options[].pros` | 1–4 項 | **1–2 項** |
| evaluation_option_score_pros_cons | `options[].pros[]` | ≤60 字 | **≤17 字** |
| evaluation_option_score_pros_cons | `recommendation` | 0–5 項 | **0–3 項** |
| evaluation_option_score_pros_cons | `recommendation[]` | ≤40 字 | **≤13 字** |
| evaluation_option_score_pros_cons | `recommended` | ≤20 字 | **≤13 字** |
| evaluation_option_score_pros_cons | `subtitle` | ≤60 字 | **≤50 字** |
| info_card_grid | `subtitle` | ≤60 字 | **≤50 字** |
| info_horizontal_explanation_rows | `rows[].points` | 1–3 項 | **1–2 項** |
| info_horizontal_explanation_rows | `subtitle` | ≤60 字 | **≤49 字** |
| info_three_column_category | `columns[].heading` | ≤20 字 | **≤13 字** |
| info_three_column_category | `columns[].points` | 2–6 項 | **2–5 項** |
| info_three_column_category | `columns[].points[]` | ≤40 字 | **≤14 字** |
| info_three_column_category | `subtitle` | ≤60 字 | **≤50 字** |
| phase_concept_three_column_explanation | `concept` | ≤8 字 | **≤4 字** |
| phase_three_column_action_cards | `phases[].detail` | ≤60 字 | **≤54 字** |
| pyramid_layered_maturity_detail | `side_cards[].heading` | ≤16 字 | **≤9 字** |
| pyramid_layered_maturity_detail | `side_cards[].points` | 2–4 項 | **2–2 項** |
| pyramid_layered_maturity_detail | `side_cards[].points[]` | ≤30 字 | **≤18 字** |
| pyramid_layered_maturity_detail | `subtitle` | ≤60 字 | **≤56 字** |
| stage_timeline_progress | `subtitle` | ≤60 字 | **≤50 字** |
| stage_year_cards | `stages[].details[]` | ≤30 字 | **≤15 字** |
| stage_year_cards | `stages[].heading` | ≤16 字 | **≤7 字** |
| vision_goal_center_balance | `annual_goal` | ≤60 字 | **≤15 字** |
| vision_goal_center_balance | `core_mission` | ≤60 字 | **≤11 字** |
| vision_goal_center_balance | `kpis[].label` | ≤30 字 | **≤9 字** |
| vision_goal_center_balance | `kpis[].value` | ≤12 字 | **≤9 字** |
| vision_goal_center_balance | `projects[]` | ≤40 字 | **≤9 字** |
| vision_goal_center_balance | `subtitle` | ≤60 字 | **≤50 字** |
| vision_goal_keyword_orbit | `center_theme` | ≤14 字 | **≤8 字** |
| vision_goal_keyword_orbit | `subtitle` | ≤60 字 | **≤50 字** |

(共 43 個槽位;由 `template_admin.py` 依模板實際版位量測後寫入
`engine/templates/light/manifest.json` 的 `capacity_overrides`,非人工填寫。)

---

## 頁型選擇原則
- 不確定用哪個頁型時(或 GPTs 替使用者代擬 JSON 時),依內容結構選最貼近的頁型:
  先看本檔 21 種,沒有合適的再翻 `page_types.md` 的「版型選擇原則」節挑選。
  **不可發明兩份文件都沒有的頁型**,也不可發明模板外的視覺風格。
- 內容裝不進任何頁型(例如 4 欄對照、7 層金字塔)→ 優先「刪減或拆頁」讓內容符合
  頁型容量,而不是撐爆槽位;真的不行就回報使用者這頁需要人工處理。
- 槽位數量比內容多時,填實際數量即可(在 min–max 區間內),渲染時要重新置中/等距,
  不可留空位。
