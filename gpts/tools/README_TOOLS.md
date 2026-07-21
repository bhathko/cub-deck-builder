# tools 速查卡(給 GPTs:照這個流程跑,不要現寫等價程式碼)

前置:tools.zip 已解壓到 /mnt/data/tools/,validate_slide_spec_gpts.py 與
light_template.pptx 在 /mnt/data/,assets.zip 已解壓。

## ★ 關鍵事實:10 種註冊頁型完全自動,不需要你寫任何計畫

cover / agenda / closing / story_chapter_statement / stage_dual_track_roadmap
→ 內建版面;vision_goal_center_balance / info_three_column_category /
data_two_group_metric_comparison / evaluation_option_score_pros_cons /
pyramid_layered_maturity_detail → 自動填入模板頁(fills.py 寫死 shape id)。
**整份 spec 都是註冊頁型時,流程只有三條指令,你不產任何中間檔。**

## 標準流程 = 一條指令(run_pipeline 依序跑 稽核→驗證→渲染→QA,任一 FAIL 即停)

```bash
# 內容/outline 模式(帶 --slides 自動啟用 audit_provenance + --registered-only --strict)
python /mnt/data/tools/run_pipeline.py --spec /mnt/data/slide_spec.json \
  --slides /mnt/data/slides.md --source /mnt/data/outline_source_current.txt \
  --asset-dir /mnt/data --out /mnt/data/deck.pptx

# 純 JSON 直供模式(不帶 --slides → 自動以獨一不存在路徑關閉追溯,不帶 strict)
python /mnt/data/tools/run_pipeline.py --spec /mnt/data/slide_spec.json \
  --asset-dir /mnt/data --out /mnt/data/deck.pptx
```

- 出錯就看「管線停止於階段 N」那一段輸出,修對應輸入後**整條重跑同一指令**(冪等)。
- 含未涵蓋頁型:先加 `--validate-only` 過閘門 → 寫 render_plan → 加 `--plan` 完整重跑。
- 個別工具(validator / render_deck / qa_check)仍可單獨執行除錯,指令同管線輸出的
  `$` 行;但正式產檔一律走 run_pipeline,不要手動串步驟。

使用者要骨架:`python /mnt/data/tools/make_skeleton.py --types cover,agenda,...,closing --out ...`

## 只有「未涵蓋頁型」(page_types.md 其他 40+ 種)才需要 plan

寫該頁 plan 前先查參考頁形狀(省 token:只用 --summary / --page N,不要 --all 印出):
```bash
python /mnt/data/tools/inspect_template.py --pptx /mnt/data/light_template.pptx --page 35
```
render_plan.json 只放未涵蓋的頁,其餘頁不用列:
```json
{"slides":[
  {"number":5,"mode":"clone","template_page":35,
   "edits":[{"match":{"id":23},"text":"spec 的文字"},
            {"match":{"contains":"模板現有文字"},"text":"..."}],
   "delete":[{"match":{"id":45}}]}
]}
```
- 錨點優先 `id`(inspect 查),`contains` 次之,撞多筆加 `nth`(由上而下 0-based)。
- `text` 逐字取自 slide_spec.json,禁止改寫。內容比模板少 → `delete` 多餘形狀。
- 產檔時加上 `--plan /mnt/data/render_plan.json`。

## 錯誤→修法對照表(FAIL 不是終點:對照修正 → 整條重跑,最多三輪)

| 錯誤訊息特徵 | 允許的修法 |
| --- | --- |
| `字數 N 超過上限 M` | 縮短該欄文字(不改原意、數字原樣保留)或拆頁 |
| `項目數 N 不符版型規定(min–max)` | 超出→依原文重要性刪到上限;不足→用「待補充」補到下限,不得捏造 |
| `疑似捏造數字 'X'` | 多半是縮寫時動到數字:恢復來源原句,或整句移除/改「待補充」 |
| `文字與來源相似度低` | 放棄改寫,改回原文逐字摘錄後再必要縮短 |
| `缺少必填欄位` | 來源有→填來源原文;來源沒有→填「待補充」;整頁無來源→刪頁或換頁型 |
| 頁碼 / `slide_count` / 連續頁號錯 | 重跑 make_skeleton 產骨架再搬內容,或直接修 number/slide_count |
| 素材檔找不到 | 改回骨架預設的內建素材路徑(assets/backgrounds、assets/logos) |
| audit:title 未逐字 / deck_name 不等 | title 改用該頁來源區塊的原句;deck_name 設為第一內容頁 title |
| audit:slides.md 某行非逐字片段 | 該行從 outline_source_current.txt 重新逐字摘錄(不得改原文檔) |
| audit:數字 token 無精確對應 | 同捏造數字處理;禁止改 slides.md 來遷就 spec |
| render:UNMATCHED / AMBIGUOUS | inspect --page N 重查,只改該條 plan 的 match(id 優先,撞多筆加 nth) |
| render:FillError(註冊頁型) | 唯一不修的錯:停止並回報維護者(模板改版問題) |

每輪 = 修正 → 整條重跑 run_pipeline。三輪內禁止宣稱「無法繼續」、禁止跳過失敗
階段、禁止退回手動逐步執行;三輪後仍 FAIL 才停止並白話回報。

## 鐵律(避免無謂循環)

1. **修輸入不修產出**:render_deck 每次整檔重生。UNMATCHED/AMBIGUOUS/qa FAIL
   → 只改 spec 或 plan 的對應條目 → 重跑。禁止對 deck.pptx 手動修補。
2. 註冊頁型出問題(FillError、版面不對)→ 那是工具或模板改版問題,回報使用者
   轉交管理者,**不要**自己改用 clone plan 硬繞。
3. qa_check 印出的才需要處理;PASS 就交付,不要自己加戲重驗。
4. inspect 只用 --summary / --page N,不要把整份模板 dump 進對話。
