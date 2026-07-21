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

## 鐵律(避免無謂循環)

1. **修輸入不修產出**:render_deck 每次整檔重生。UNMATCHED/AMBIGUOUS/qa FAIL
   → 只改 spec 或 plan 的對應條目 → 重跑。禁止對 deck.pptx 手動修補。
2. 註冊頁型出問題(FillError、版面不對)→ 那是工具或模板改版問題,回報使用者
   轉交管理者,**不要**自己改用 clone plan 硬繞。
3. qa_check 印出的才需要處理;PASS 就交付,不要自己加戲重驗。
4. inspect 只用 --summary / --page N,不要把整份模板 dump 進對話。
