# AGENTS.md — ppt_ai2 簡報流程契約（Codex / Claude Code 共用）

> 團隊共用、隨 repo 分享的流程契約。任何 agent（Codex CLI、Claude Code）在本 repo
> 產簡報時**必須**遵循。速覽見 [`README.md`](README.md)；本檔是完整規則。

## 這個專案
把 `my_project/source/slides.md` 產成 Cathay 淺色企業風、繁體中文、16:9 的簡報。兩條路徑：

- 🟢 **主力**：`baoyu-slide-deck`（`.agents/skills/`）—— 圖生圖，跑在 Codex。
- 🟡 **Fallback**：`fallback/`（`python-pptx` / `Pillow` + spec 閘門）—— native-pptx / hybrid，備援。

## 硬規則（兩條路徑都適用）
1. **內容 SSOT ＝ `my_project/source/slides.md`。** 嚴禁發明其中沒有的數字、指標、KPI、標籤、專案名、日期。
2. **生圖只准用 Codex `imagegen`。** 缺席就回報 blocker，**不得**改用 Cursor `GenerateImage`、`baoyu-image-gen` 或任何非 Codex 工具，也**不得靜默降級**成 SVG/HTML/canvas/截圖。（公司政策）
3. **污染防護：** 一次產多頁時，**只有當頁內容是權威**；先前產出的圖與文字**只能當風格參考、禁止複製**。

## 🟢 主力流程（baoyu，Codex）
- **前置**：Codex 有 `imagegen`；Node.js v18+（合併用；skill 首次會自動 `npm install`）。
- **觸發**：自然語言請求（「做簡報 / slide deck / PPT」），帶**參考圖 + 內容 + 繁體中文**。
- 逐頁生 PNG →（Node 腳本）合併成 `.pptx` / `.pdf`。
- **驗收**：看 PNG 的繁中字/數字是否清楚正確。若糊 → 改走 fallback。
- 細節：`.agents/skills/baoyu-slide-deck/SKILL.md`（已鎖 Codex-only）。

## 🟡 Fallback 流程（native-pptx，本機 Python）
spec-first：`slides.md → my_project/slide_spec.json →〔validate 閘門〕→ render`。

- **【硬閘門｜不可略過】** 燒圖前一定先跑，**exit 0（PASS）才准 render**：
  ```
  python3 fallback/validate_slide_spec.py
  ```
  exit 1 就停下來在文字層修 `my_project/slide_spec.json`（不花圖 token）。
- 產原生可編輯 pptx：`python3 fallback/generate_review_deck.py`
- **註冊表同步**：改版型時，`fallback/validate_slide_spec.py` 的 `PAGE_TYPES` 與
  `fallback/slide_spec.schema.json` 的 `page_type` enum **兩處都要改**。
- fallback 腳本一律**從專案根目錄**執行。

## 檔案地圖
| 路徑 | 角色 |
|---|---|
| `my_project/source/slides.md` | 內容 SSOT |
| `my_project/{outline,speech}.md` | 大綱、講稿 |
| `my_project/assets/`、`style_reference/` | 品牌素材、風格/頁型庫、模板 |
| `my_project/slide_spec.json` | 內容↔渲染中間層（fallback 用） |
| `my_project/deck_spec.json` | 舊管線遺留（保留待萃取） |
| `.agents/skills/baoyu-slide-deck/` | 🟢 主力 skill（Codex-only、node 化） |
| `fallback/` | 🟡 native-pptx / 閘門工具（備援） |

> Claude Code 使用者：本檔為單一真相來源，`CLAUDE.md` 已指向這裡。
