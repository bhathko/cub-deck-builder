# AGENTS.md — ppt_ai2 簡報生成流程（Codex / Claude Code 共用指令）

> 這份是**團隊共用、隨 repo 分享**的流程契約。任何 agent（Codex CLI、Claude Code）在本 repo 產生簡報時，**必須**照這裡的規則走。個人的 `~/.codex/` 設定不算數，會在此被覆蓋。

## 這個專案在做什麼
把單一內容來源 `my_project/source/slides.md` 渲染成 10 頁繁體中文、Cathay 淺色企業風簡報。核心設計：**內容與渲染分離**，中間隔一層可驗證的 `slide_spec.json`，並在燒任何圖 token 之前先過閘門。

## 標準流程（spec-first，禁止跳步）
```
slides.md  ──►  slide_spec.json  ──►  [validate 硬閘門]  ──►  逐頁 render  ──►  組成 deck
 (內容SSOT)     (中間層/選版型)      PASS 才放行            寫回 slide_jobs.json
```

1. **內容真相來源(SSOT)＝ `my_project/source/slides.md`。** 只能用裡面的事實。**嚴禁**發明任何 slides.md 沒有的數字、指標、KPI、標籤、專案名、日期。
2. **產出 / 更新 `my_project/slide_spec.json`：** 每頁選一個 `page_type`，把該頁的精確字串填進 slots。頁型與槽位規則以 `spec/validate_slide_spec.py` 的 `PAGE_TYPES` 註冊表為準。
3. **【硬閘門｜不可略過】** 產圖前一定先跑：
   ```
   python3 spec/validate_slide_spec.py
   ```
   - **exit 0 才准進入 render。** exit 1 就**停下來修 spec**，在文字層 repair（幾乎不花 token），不要拿 failing 的 spec 去燒圖。
   - 需要更嚴時用 `--strict`（把 provenance WARN 升級成 ERROR）。
4. **逐頁 render：** 依 render 契約產出每頁最終圖（見下）。
5. **狀態回寫：** 把 dispatch / result 寫回 `my_project/slide_jobs.json`，推進 `my_project/slide_run_state.json`。

## 硬性規則
- **閘門優先：** 沒跑過 `validate_slide_spec.py` 且 PASS，**不准**呼叫任何影像後端。
- **污染防護：** render 第 N 頁時，**只有該頁的 slots 是權威內容**。之前產出的圖與文字**只能當風格參考，嚴禁把它們的文字/版面複製過來**。若後端是「生成圖會回到同一對話」的 inline 模式，render 每頁前要顯式聲明前文僅供風格參考。
- **註冊表同步：** 改版型時，`spec/validate_slide_spec.py` 的 `PAGE_TYPES` 與 `spec/slide_spec.schema.json` 的 `page_type` enum **兩處都要改**。
- **不得靜默降級：** render 契約若要求某後端，缺該後端就回報 blocker，**不要**偷偷改用別的方式。

## Render 契約（目前）
- 正式路徑 A：依 `slide_jobs.json` 的 `sample_generation_method.handoff_rule` —— 用內建 `image_gen`（generate 模式）+ 本機輸入圖，樣張 `slide_05` 為全案視覺基準。
- 已知痛點：中文字在 image_gen 常出錯 → 重試燒 token。**若要讓文字錯字歸零**，改走 hybrid：image_gen 只出背景，用 repo 內既有的 Pillow 座標邏輯（`generate_preview_only.py`）把文字疊上去。（此為建議演進方向，未定案。）

## 本地預覽 / QA 路徑 B（不燒 token，非正式輸出）
- `python3 generate_preview_only.py` → Pillow 產 `my_project/qa_preview_v4/*.png`（需 Windows 字型 `C:/Windows/Fonts/msjh.ttc`）。
- `python3 generate_review_deck.py` → python-pptx 產可編輯 `.pptx`。
- 注意：路徑 B 是路徑 A 的 `generation_contract` 明令禁止拿來當**正式最終圖**的方法；它只用於本地審閱。

## 檔案地圖
| 路徑 | 角色 |
|---|---|
| `my_project/source/slides.md` | 內容 SSOT |
| `my_project/slide_spec.json` | 內容↔渲染中間層（agent 主要產出/維護的檔） |
| `spec/validate_slide_spec.py` | **硬閘門** + `PAGE_TYPES` 版型註冊表 |
| `spec/slide_spec.schema.json` | 結構層 schema（enum 要與註冊表同步） |
| `my_project/slide_spec.bad.example.json` | 注入故障的回歸樣本（驗證器自測用） |
| `my_project/deck_spec.json` / `prompts/*.json` | 路徑 A 的既有規格與每頁 prompt |
| `my_project/slide_jobs.json` / `slide_run_state.json` | 派工帳本 / 狀態機 |
| `my_project/style_reference/` | 風格與頁型庫（`page_types.md` 是選版型依據） |
| `my_project/assets/` | 背景、logo 等嚴格輸入素材 |

## 常用指令
```
python3 spec/validate_slide_spec.py                         # 驗正式 spec（燒圖前必跑）
python3 spec/validate_slide_spec.py --strict                # 嚴格模式
python3 spec/validate_slide_spec.py my_project/slide_spec.bad.example.json   # 看閘門如何抓錯
python3 generate_preview_only.py                            # 本地 PNG 預覽（Windows 字型）
```

> Claude Code 使用者：本專案的 `CLAUDE.md` 可直接指向或複製這份，讓兩種 agent 遵循同一套規則。
