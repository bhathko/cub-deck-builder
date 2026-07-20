# CLAUDE.md

> **單一真相來源是 [`AGENTS.md`](AGENTS.md)。** 本專案的 agent 流程契約統一寫在 `AGENTS.md`，
> 讓 **Codex CLI（原生讀 `AGENTS.md`）** 與 **Claude Code（讀本檔）** 遵循**同一套規則**、不分歧。
>
> **Claude Code 使用者：請把 `AGENTS.md` 當成完整指令並完整遵循。** 本檔只做指路 + 速覽，
> 規則有衝突時以 `AGENTS.md` 為準；更新流程規則時**只改 `AGENTS.md`**，不要在此另寫一份以免飄移。

## 速覽（完整內容見 `AGENTS.md`）

- **內容 SSOT ＝ `my_project/source/slides.md`。** 嚴禁發明其中沒有的數字、指標、KPI、標籤、專案名、日期。
- **硬閘門，不可略過：** 產任何圖之前一定先跑 `python3 spec/validate_slide_spec.py`，
  **exit 0（PASS）才准 render**；exit 1 就停下來在文字層修 `my_project/slide_spec.json`。
- **spec-first 流程：** `slides.md → slide_spec.json →〔validate 閘門〕→ 逐頁 render → 回寫 slide_jobs.json`。
- **污染防護：** render 第 N 頁時，只有該頁 slots 是權威內容；先前產出的圖與文字**只能當風格參考，禁止複製**。
- **註冊表同步：** 改版型時，`spec/validate_slide_spec.py` 的 `PAGE_TYPES` 與
  `spec/slide_spec.schema.json` 的 `page_type` enum **兩處都要改**。
- **不得靜默降級：** render 契約要求的後端缺席時回報 blocker，不要偷換方法。

## 常用指令
```
python3 spec/validate_slide_spec.py                                          # 燒圖前必跑
python3 spec/validate_slide_spec.py --strict                                 # 嚴格模式
python3 spec/validate_slide_spec.py my_project/slide_spec.bad.example.json   # 看閘門抓錯
```
