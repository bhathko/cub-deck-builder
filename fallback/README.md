# fallback — native-pptx / hybrid 產出路徑

**這是備援，不是主力。** 主力是 `.agents/skills/baoyu-slide-deck/`（圖生圖，跑在 Codex）。

## 什麼時候用這裡
當 baoyu 的圖生圖把**繁體中文字弄糊**、無法接受時，改走這條：用程式（`python-pptx` / `Pillow`）
畫版面與文字，**中文零錯字、原生可編輯**。代價是視覺較樸素、版面座標要自己維護。

## 內容
| 檔案 | 用途 |
|---|---|
| `validate_slide_spec.py` | 內容收斂**閘門**：驗 `my_project/slide_spec.json`（數量/字數/頁碼/**捏造數字**）。ERROR 硬擋、WARN 標記；`--strict` 升級 WARN。 |
| `slide_spec.schema.json` | slide_spec 的結構 schema（給編輯器/文件；驗證器本身不讀它） |
| `generate_review_deck.py` | 解析 `slides.md` → `python-pptx` → 原生可編輯 `.pptx` |
| `generate_preview_only.py` | 解析 `slides.md` → `Pillow` → 預覽 PNG（需 Windows 字型 `msjh.ttc`） |

## 執行
一律**從專案根目錄**跑（腳本用相對路徑找 `my_project/`）：
```bash
python3 fallback/validate_slide_spec.py     # 先過閘門
python3 fallback/generate_review_deck.py    # 再產 pptx
```

## 維護註記
改版型時，`validate_slide_spec.py` 的 `PAGE_TYPES` 與 `slide_spec.schema.json` 的
`page_type` enum **兩處都要同步**。
