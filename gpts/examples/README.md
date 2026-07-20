# 試用範例集

四份可以直接貼給 GPTs 的 slide_spec.json,用來試成效與驗證閘門。
使用方式:打開 GPTs,貼上「這是我的 slide_spec.json,幫我產出 PPT」+ 檔案內容
(或直接上傳 .json 檔)。

| 檔案 | 測什麼 | 預期結果 |
|---|---|---|
| `01_minimal_4p.json` | 最小可用:封面、目錄、三欄說明、封底,全部是註冊頁型 | 驗證 PASS,產出 4 頁 pptx;適合第一次試跑與展示給主管 |
| `02_full_10p.json` | 完整 10 頁,涵蓋全部 10 種註冊頁型(同知識庫範例) | 驗證 PASS(可能有 WARN),**零 plan 全自動**產出 10 頁 |
| `03_advanced_unregistered_6p.json` | 混用未註冊頁型(`cycle_four_point_loop`、`vision_goal_hub_spoke`) | 驗證 PASS 但有 WARN;這兩頁需要 GPTs 寫 clone plan,重點看版面是否照模板第 35、13 頁重建 |
| `04_broken_should_fail.json` | 故意違規的 spec(結構/數量/字數問題) | 驗證 **FAIL**,GPTs 必須列出錯誤並「拒絕產檔」;如果它照樣產出 PPT,代表閘門沒守住,要回報 |

另附:
- `02_full_10p.source_slides.md` — 02 的內容原文(`## Slide N` 分節),
  測「內容模式」時把它當使用者貼的大綱,或驗證時加 `--slides` 開啟追溯比對。
- `demo_output_01_minimal.pptx`、`demo_output_02_full10p.pptx` —
  2026-07-20 本機實測的實際產出,開 PowerPoint 可眼見為憑。

## 驗收時看什麼

1. **閘門有沒有真的跑**:產檔前 GPTs 應貼出驗證器輸出(認「結果:PASS」那行);
   `04` 必須被擋下來。
2. **版面像不像模板**:對照 `light_template.pptx` 的參考頁(每種頁型第幾頁見
   `page_types.md`),看位置、配色、卡片樣式是否接近。
3. **可編輯性**:在 PowerPoint 裡點文字、卡片、圖形,確認都是原生物件不是圖片。
4. **文字有沒有溢出**:中文字在沙箱量不準,溢出是最常見毛病,要人工看。
5. **內容有沒有被改**:比對產出文字與 JSON 原文,GPTs 不該增刪改任何字。

試完把結果(含截圖與所用 JSON)回饋給 GPTs 管理者,見 `../README.md` 的
「回饋與版本更新流程」。
