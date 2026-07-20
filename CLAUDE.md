# CLAUDE.md

> **單一真相來源是 [`AGENTS.md`](AGENTS.md)**（Codex 原生讀取）。Claude Code 使用者請把
> `AGENTS.md` 當完整指令並遵循；本檔只做指路 + 速覽。規則衝突時以 `AGENTS.md` 為準，
> 更新流程規則時**只改 `AGENTS.md`**。整體說明見 [`README.md`](README.md)。

## 速覽

- **內容 SSOT ＝ `my_project/source/slides.md`。** 嚴禁發明其中沒有的數字/指標/KPI/標籤/專案名/日期。
- **兩條路徑：** 🟢 主力 `baoyu-slide-deck`（`.agents/skills/`，圖生圖、Codex）；🟡 fallback `fallback/`（native-pptx / hybrid）。
- **生圖只准用 Codex `imagegen`**；缺席回報 blocker，不得換其他工具、不得靜默降級。
- **污染防護：** 一次產多頁時只有當頁內容是權威，先前產出只能當風格參考、禁止複製。
- **fallback 硬閘門：** 產任何圖前先跑 `python3 fallback/validate_slide_spec.py`，**exit 0 才 render**；exit 1 就在文字層修 `my_project/slide_spec.json`。
- **註冊表同步：** 改版型時 `fallback/validate_slide_spec.py` 的 `PAGE_TYPES` 與 `fallback/slide_spec.schema.json` 的 enum 兩處都要改。

## 常用指令
```
python3 fallback/validate_slide_spec.py                                       # fallback 燒圖前必跑
python3 fallback/validate_slide_spec.py --strict                              # 嚴格模式
python3 fallback/validate_slide_spec.py my_project/slide_spec.bad.example.json # 看閘門抓錯
```
