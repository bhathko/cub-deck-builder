# ppt_ai2 — 年度工作簡報產生器

把 `my_project/source/slides.md` 的內容，產出 **Cathay 淺色企業風、繁體中文、16:9** 的簡報。

內容單一真相來源（SSOT）＝ `my_project/source/slides.md`。**嚴禁發明其中沒有的數字、指標、KPI、標籤、專案名、日期。**

---

## 兩條產出路徑

### 🟢 主力：`baoyu-slide-deck`（圖生圖，跑在 Codex）

給**參考圖 + 內容** → Codex 內建 `imagegen` 逐頁生圖 → 合併成 `.pptx` / `.pdf`。
適合設計師做「簡單、視覺化」的簡報，設計師只需維護內容與參考圖。
**已鎖定只用 Codex 生圖**（公司政策，不允許 Codex 以外的工具）。

### 🟡 Fallback：native-pptx / hybrid（跑在本機 Python）

若 baoyu 的**繁體中文字糊掉**，改走這條：用 `python-pptx` / `Pillow` 以程式畫版面與文字
→ 中文零錯字、原生可編輯。**目前為備援**，待 baoyu 繁中實測過關前保留、不刪。

---

## 檔案結構

```text
ppt_ai2/
├── README.md                         # 本檔
├── AGENTS.md                         # agent 流程契約（單一真相；Codex 原生讀取）
├── CLAUDE.md                         # → 指向 AGENTS.md（Claude Code 讀取）
├── .agents/skills/
│   └── baoyu-slide-deck/             # 🟢 主力：圖生圖簡報 skill（Codex-only、已 node 化）
├── my_project/                       # 簡報本體：內容 + 品牌
│   ├── source/slides.md              #   內容 SSOT
│   ├── outline.md  speech.md         #   大綱、講稿
│   ├── slide_spec.json               #   內容↔渲染中間層（fallback 用）
│   ├── slide_spec.bad.example.json   #   驗證器回歸樣本
│   ├── deck_spec.json                #   舊管線遺留（保留待萃取）
│   ├── assets/                       #   品牌素材：背景、logo
│   └── style_reference/              #   風格指南、頁型庫、模板、範例圖
└── fallback/                         # 🟡 native-pptx / 閘門工具（備援）
    ├── generate_review_deck.py       #   python-pptx → 可編輯 pptx
    ├── generate_preview_only.py      #   Pillow → 預覽 PNG（需 Windows 字型）
    ├── validate_slide_spec.py        #   spec 收斂閘門（燒圖前先跑）
    └── slide_spec.schema.json
```

---

## 怎麼用（主力：Codex）

**前置**：Codex CLI（要有 `imagegen`）+ Node.js v18+（合併用；skill 首次會自動 `npm install`）。

在專案目錄開 Codex，貼一段自然語言請求觸發 skill，例如：

```text
用 baoyu-slide-deck 產生 2 頁簡報，語言繁體中文，16:9。
風格參考圖：my_project/assets/backgrounds/content_bg.png
內容只能用下列文字，不可自行發明數字或標籤：
- 第 1 頁：主標「年度工作總覽」，副標「年度工作從穩定交付轉向可衡量改善」。
- 第 2 頁 KPI：跨部門大型專案 2 項、年度里程碑 12 個、報表處理時間節省 40%、服務回應一致性提升 30%。
生圖用 Codex 內建 imagegen。
```

產完檢查 `outputs/…/*.png` 的**繁中字/數字**是否清楚正確。

---

## 怎麼用（fallback：本機 Python）

```bash
# 1) 燒圖前先過閘門，exit 0（PASS）才續
python3 fallback/validate_slide_spec.py
python3 fallback/validate_slide_spec.py --strict                              # 嚴格模式
python3 fallback/validate_slide_spec.py my_project/slide_spec.bad.example.json # 看閘門抓錯

# 2) 產原生可編輯 pptx
python3 fallback/generate_review_deck.py

# 3) 產預覽 PNG（需 Windows 字型 msjh.ttc）
python3 fallback/generate_preview_only.py
```

> fallback 腳本請從 **專案根目錄** 執行（內部用相對路徑找 `my_project/`）。

---

## 硬規則（完整見 [`AGENTS.md`](AGENTS.md)）

- **內容 SSOT ＝ `my_project/source/slides.md`**，不可發明其中沒有的事實。
- **生圖只准用 Codex `imagegen`**；缺席就回報 blocker，不得偷換 Cursor / baoyu-image-gen 等工具。
- **污染防護**：一次產多頁時，只有當頁內容是權威，前面的產出只能當風格參考、禁止複製。
- **fallback 硬閘門**：跑 `validate_slide_spec.py` PASS 才可 render。
