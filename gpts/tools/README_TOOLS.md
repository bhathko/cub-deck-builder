# tools 速查卡(給 GPTs:照這個流程跑,不要現寫等價程式碼)

前置:tools.zip 已解壓到 /mnt/data/tools/,validate_slide_spec_gpts.py 與
light_template.pptx 在 /mnt/data/,assets.zip 已解壓。

## ★ 關鍵事實:10 種註冊頁型完全自動,不需要你寫任何計畫

cover / agenda / closing / story_chapter_statement / stage_dual_track_roadmap
→ 內建版面;vision_goal_center_balance / info_three_column_category /
data_two_group_metric_comparison / evaluation_option_score_pros_cons /
pyramid_layered_maturity_detail → 自動填入模板頁(fills.py 寫死 shape id)。
**整份 spec 都是註冊頁型時,流程只有三條指令,你不產任何中間檔。**

## 標準流程(每一步 exit 0 才走下一步)

```bash
# 1) spec 閘門(內容模式:GPT 從使用者原文代擬 spec 時,必須另存 slides.md
#    並加 --slides /mnt/data/slides.md,啟動捏造數字硬擋)
python /mnt/data/validate_slide_spec_gpts.py --spec /mnt/data/slide_spec.json --asset-dir /mnt/data

# 2) 產檔(全註冊頁型 → 不需要 --plan)
python /mnt/data/tools/render_deck.py --spec /mnt/data/slide_spec.json \
  --template /mnt/data/light_template.pptx --asset-dir /mnt/data --out /mnt/data/deck.pptx

# 3) 產檔後自檢,PASS 才交付
python /mnt/data/tools/qa_check.py --spec /mnt/data/slide_spec.json --pptx /mnt/data/deck.pptx
```

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
