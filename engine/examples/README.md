# 試用範例集(engine/examples)

> 這是**範例目錄的說明**,不是 repo 說明(那在 repo 根的 `README.md`)。

四份可以直接貼給 GPTs 的 slide_spec.json,用來試成效與驗證閘門。
使用方式:打開 GPTs,貼上「這是我的 slide_spec.json,幫我產出 PPT」+ 檔案內容
(或直接上傳 .json 檔)。

| 檔案 | 測什麼 | 預期結果 |
|---|---|---|
| `01_minimal_4p.json` | 最小可用:封面、目錄、三欄說明、封底,全部是註冊頁型 | 驗證 PASS,產出 4 頁 pptx;適合第一次試跑與展示給主管 |
| `02_full_8p.json` | 多頁型混合(同知識庫範例;其餘註冊頁型由 golden 覆蓋) | 驗證 PASS(可能有 WARN),**零 plan 全自動**產出 8 頁 |
| `03_advanced_unregistered_6p.json` | 混用未註冊頁型(`cycle_four_point_loop`、`vision_goal_hub_spoke`) | 驗證 PASS 但有 WARN;這兩頁需要 GPTs 寫 clone plan,重點看版面是否照模板第 35、13 頁重建 |
| `04_broken_should_fail.json` | 故意違規的 spec(結構/數量/字數問題) | 驗證 **FAIL**,GPTs 必須列出錯誤並「拒絕產檔」;如果它照樣產出 PPT,代表閘門沒守住,要回報 |

另附:
- `02_full_8p.source_slides.md` — 02 的內容原文(`## Slide N` 分節),
  測「內容模式」時把它當使用者貼的大綱,或驗證時加 `--slides` 開啟追溯比對。
- `06_workplace_etiquette_source.md` — 職場禮儀新人訓練大綱(未切頁),
  GPT Builder 實測用的第二份 fixture;FEEDBACK #1/#2 兩次失敗實測餵的就是它。
- `demo_output_01_minimal.pptx`、`demo_output_02_full10p.pptx` —
  2026-07-20 本機實測的實際產出,開 PowerPoint 可眼見為憑。
  **注意 `demo_output_02_full10p.pptx` 是 10 頁的舊產出**:2026-07-26 移除
  `story_chapter_statement` 與 `stage_dual_track_roadmap` 兩個頁型後,對應的
  spec 已改名 `02_full_8p.json` 並降為 8 頁(見 `docs/WORKLOG.md`);
  這個 pptx 保留為當時的歷史快照,不重新產生。

## 驗收時看什麼

1. **閘門有沒有真的跑**:產檔前 GPTs 應貼出驗證器輸出(認「結果:PASS」那行);
   `04` 必須被擋下來。
2. **版面像不像模板**:對照 `templates/light/template.pptx` 的參考頁(每種
   頁型第幾頁見 `templates/light/page_map.md`),看位置、配色、卡片樣式是否接近。
3. **可編輯性**:在 PowerPoint 裡點文字、卡片、圖形,確認都是原生物件不是圖片。
4. **文字有沒有溢出**:中文字在沙箱量不準,溢出是最常見毛病,要人工看。
5. **內容有沒有被改**:比對產出文字與 JSON 原文,GPTs 不該增刪改任何字。

試完把結果(含截圖與所用 JSON)回饋給管理者,回饋方法與台帳見
[`../../docs/FEEDBACK.md`](../../docs/FEEDBACK.md)。
