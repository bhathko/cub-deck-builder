# engine/devtools — 讀碼／除錯輔助(不出貨)

本目錄的工具**只在本機讀程式碼與除錯時用**:不入 `tools.zip`、不被
`prepare_env.py` 複製進 `ppt_out/` 沙箱、不參與 `engine/REGRESSION.md` 的
發版回歸。改本目錄不需要重打包、不需要更新 instructions 版本字串。

> 判準:模型在產檔流程裡會用到的 → `engine/tools/`(出貨);維護者用來看懂或
> 盤查引擎的 → 這裡。維護者的**模板註冊工具鏈**另有去處(`engine/release/`)。

渲染相關指令一律加前綴 `uv run --with python-pptx==1.0.2 python`(本機無 python-pptx;
以 `.codex/skills/outline-to-ppt/prepare_env.py` 印出的「渲染指令前綴」為準)。

## trace_page.py — 攤開一頁的填充資料流

```bash
uv run --with python-pptx==1.0.2 python engine/devtools/trace_page.py \
    --spec engine/examples/01_minimal_4p.json --page 3
```

印出每個 op:讀了 spec 的哪個槽位路徑、解析到什麼值、動到模板哪個 shape id、
那個框的文字**從什麼變成什麼**。

```
p3  page_type = info_three_column_category
  路徑:fill —— clone 模板第 17 頁,再照 ops 換字
  ops[3] set        $.slots.columns[0].heading         → 品牌視覺
      id=6   「標題文字」 → 「品牌視覺」
  ops[6] list       $.slots.columns[0].points[2:]      → []
      id=45  刪除   (模板原本:「」)
```

**為什麼需要它**:`engine/tools/fills_engine.py` 刻意不含任何模板知識(shape id、
座標、色碼一律不寫死),它是解譯器,語意全在 `engine/templates/<id>/bindings.json`
的資料裡。單讀 `fills_engine.py` 只看到空殼;要理解一個 fill 頁型在做什麼,必須
把「binding 資料 + 模板現況 + 執行結果」三者並排。

它繼承正式的 `fill_helpers.Ctx`、逐 op 呼叫正式的 `fills_engine._HANDLERS`,
所以走的是與 `render_deck.py` 完全相同的路徑(不是另寫的模擬版,不會行為漂移)。

適合用來看懂難讀的分支——例如把 6 個 points 塞進只有 3 個列位的欄,就能直接
看到 `_op_list` 的 `overflow.merge_into_id` 承接了第 4 筆:

```
  ops[6] list  $.slots.columns[0].points[2:] → ['第三點','第四點','第五點','第六點']
      id=49 「列點標題」 → 「第五點」
      id=50 「列點說明文字,列點說明文字」 → 「第六點」   ← 溢出併入,delete_always 被跳過
```

## 相關(不在本目錄)

| 想做的事 | 用什麼 |
| --- | --- |
| 看模板某頁有哪些 shape(id／座標／假字) | `engine/tools/inspect_template.py --pptx <檔> --page N` |
| 看產出 pptx 的實際內容 | 同上,`--pptx` 指向產出檔 |
| 看引擎支援哪些頁型 | `python engine/tools/make_skeleton.py --list` |
| 量某個版位塞得下多少字 | `engine/release/template_admin.py fit` |
| 頁型的槽位契約與容量表 | `engine/rules/page_types_registry.md` |
