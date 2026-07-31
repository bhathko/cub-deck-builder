# tools 速查卡(給 GPTs:照這個流程跑,不要現寫等價程式碼)

前置:tools.zip 已解壓到 /mnt/data/tools/,validate_slide_spec_gpts.py 與
模板包已解壓在 /mnt/data/templates/<模板id>/(預設 light;含 template.pptx、
manifest.json、bindings.json、page_map.md、assets/)。

## ★ 關鍵事實:註冊頁型完全自動,不需要你寫任何計畫

**這個模板包支援哪些頁型、哪些是全自動,跑 `make_skeleton.py --list` 會印出來**——
它直接讀模板包 manifest,是當下的唯一真相。**不要**依本卡或任何文件寫死的頁型
清單/數量判斷:那些會過期,而過期的清單會讓你誤以為某個可用的頁型不能用。

全自動 = 自動填入模板頁:clone 模板實頁再依模板包 `bindings.json` 填字
(由 fills_engine 解譯),不需要 plan。
直供 JSON 且整份 spec 都是註冊頁型時不需要任何中間檔。大綱模式則先用
`make_skeleton.py --plan` 做契約先行選版；那是頁型決策檔,不是 render_plan。

## 大綱模式:先驗容量再鎖版型

先把原文存成 `outline_source_current.txt`;跑 `make_skeleton.py --list` 取全自動
候選,縮小候選後以
`make_skeleton.py --describe info_card_grid,stage_timeline_progress`
讀選定模板包的 merged 字數/數量契約,再建立 `page_type_candidates.json`：

```json
{
  "version": 2,
  "deck": {"template": "light"},
  "not_nominated": [
    {"page_type": "data_*", "reason": "來源未提供任何數值資料"},
    {"page_type": "info_sidebar_grid", "reason": "來源分組非 2+2 配對結構"}
  ],
  "slides": [{
    "source_excerpt": ["原文逐字片段"],
    "candidates": [{
      "page_type": "info_three_column_category",
      "fit": "exact",
      "counts": {"columns": 3, "columns[].points": [2, 3, 2]}
    }]
  }]
}
```

- `source_excerpt` 必須逐字出自本次原文。
- `counts` 是來源實際清單數量,不把「待補充」算進去；鍵直接照契約槽位路徑。
- **`not_nominated` 整庫覆蓋審視(必填)**:每個非結構全自動頁型(全集見
  `--list`),不提名就要在此逐一給「語意不合」的理由;同字首一族可用
  `字首_*` 一筆涵蓋(已提名者自動略過)。缺漏 exit 1 並列出缺哪些——這是擋
  「只提名最熟兩型」的閘門;理由會寫進 page_type_plan.json 供人工稽核,
  不得敷衍,更不得為了省事把語意合適的頁型寫進 not_nominated。
- 使用者明確點名該頁但缺結構資料時,候選標 `requested_by_user:true`,counts
  才可計入之後要放的「待補充」。
- `fit=exact` 永遠優先於 `acceptable`;工具只在同等 fit 候選間減少重複,
  不會為多樣性犧牲語意。同分決勝用來源片段 hash——零隨機、同輸入必同輸出,
  但不同內容的 deck 不會永遠收斂到同一版型。
- 輸出 composition 含 `content_slides_single_candidate`;過半內容頁只提名
  單一候選會出 WARN(候選池過窄),請回頭補提語意同等候選再重跑。

一條命令先驗模板包全自動支援與 merged 容量,再確定性全局選版,並同時產出
最終選型、`slides.md` 與 spec 骨架：

```bash
python /mnt/data/tools/make_skeleton.py --plan /mnt/data/page_type_candidates.json --source /mnt/data/outline_source_current.txt --selected-plan-out /mnt/data/page_type_plan.json --slides-out /mnt/data/slides.md --out /mnt/data/slide_spec.json
```

所有候選都被排除時,先修候選規劃；來源確實沒有任何合約可行頁型才回報
「全自動頁型缺口」。禁止改寫內容硬套、禁止手寫最終頁型序列或 slides.md。

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

純 JSON 使用者只要骨架時仍可用:
`python /mnt/data/tools/make_skeleton.py --types cover,agenda,...,closing --out ...`

## 只有「未涵蓋頁型」(page_types.md 裡未註冊的那些)才需要 plan

寫該頁 plan 前先查參考頁形狀(省 token:只用 --summary / --page N,不要 --all 印出):
```bash
python /mnt/data/tools/inspect_template.py --pptx /mnt/data/templates/light/template.pptx --page 35
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
| `頁型 'X' 不受模板 'Y' 支援` / 非全自動 | 換該包全自動頁型(`make_skeleton.py --list --template-pack Y` 查),或整份換 deck.template,或請管理者回註冊流程補;禁止硬用 clone 繞過 |
| `契約先行選型失敗` / `候選 ... 排除` | 依輸出修正 `source_excerpt`、fit 或來源實際 `counts`;不得用待補充虛增數量。所有語意合適候選都不合才是頁型庫缺口 |
| `整庫覆蓋審視不完整`(列出缺漏頁型) | 逐一判斷:語意合適→加入該頁 candidates;不合→在頂層 `not_nominated` 補 `{page_type, reason}`(同族可用 `字首_*`)。不得為省事把合適頁型寫成不合 |
| `[W] 候選池過窄` | 過半內容頁只提名單一候選。回候選規劃為語意同等的頁補提候選再重跑;確實只有一型合適則保留並如實交付 |
| qa FAIL:`文字壓到別的元素` | 該槽位內容太長,文字跑出自己的框壓到隔欄(訊息會給頁碼與 shape id)。**縮短那個槽位**再整條重跑。這是 FAIL 不是 WARN,不可交付;也**不要**改成別的頁型繞過 |
| qa WARN:`溢出疑慮共 N 條` | 沙箱估算,先看它列的最嚴重幾條;真的過長就縮短。這是 WARN,PASS 仍可交付但要提醒使用者開檔確認 |
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
