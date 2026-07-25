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

1. **已註冊頁型(本檔下列 10 種)**:驗證器有完整槽位契約——槽位名稱、數量與
   字數上限必須完全符合,否則以 ERROR 擋下、不會產檔。字數上限以「字元數」計
   (含標點與空白)。**這 10 種由 render_deck.py 全自動產出**(內建版面或
   自動填入模板頁),版面不經過任何 AI 判斷,同一份 JSON 產一萬次結果相同。
2. **頁型庫其他頁型(知識庫 `page_types.md` 的 40+ 種)**:允許使用,`page_type` 填
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

---

## 頁型選擇原則
- 不確定用哪個頁型時(或 GPTs 替使用者代擬 JSON 時),依內容結構選最貼近的頁型:
  先看本檔 10 種,沒有合適的再翻 `page_types.md` 的「版型選擇原則」節挑選。
  **不可發明兩份文件都沒有的頁型**,也不可發明模板外的視覺風格。
- 內容裝不進任何頁型(例如 4 欄對照、7 層金字塔)→ 優先「刪減或拆頁」讓內容符合
  頁型容量,而不是撐爆槽位;真的不行就回報使用者這頁需要人工處理。
- 槽位數量比內容多時,填實際數量即可(在 min–max 區間內),渲染時要重新置中/等距,
  不可留空位。
