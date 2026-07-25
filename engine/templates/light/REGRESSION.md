# light 包回歸(發版前必跑)

> 引擎級/共用案例見 `engine/REGRESSION.md`(R0–R10 本就以 light 為測物,
> 其中 R2/R3/R8 = 本包的渲染/QA 回歸)。本檔補包專屬案例;
> `$RT` 沿根檔定義。渲染需 python-pptx(沒裝時 `python3` 換
> `uv run --with python-pptx python`)。

## R-L0|包完整性

```bash
python3 -c "
import json, hashlib
m = json.load(open('engine/templates/light/manifest.json'))
sha = hashlib.sha256(open('engine/templates/light/template.pptx','rb').read()).hexdigest()
print('manifest sha', 'OK' if sha == m['template_sha256'] else f'不符:重跑盤點(TEMPLATE_LIFECYCLE.md)')
print('page_types', len(m['page_types']), '筆(預期 53:builtin 5 / fill 6 / clone 42)')
"
```

預期:`manifest sha OK`、53 筆。

## R-L1|smoke spec 直供模式全流程

```bash
python3 "$RT/tools/run_pipeline.py" --spec engine/templates/light/examples/smoke_spec.json \
  --asset-dir "$RT" --out "$RT/deck_light_smoke.pptx"; echo "exit=$?"
```

預期:exit=0,末行 `管線結果:PASS(3/3 階段)`(等同根 R8,測物固定為本包
smoke spec;10 頁註冊頁型(第 11 種 data_line 由 golden 覆蓋))。

## R-L2|clone 抽測(半自動路徑)

從 `page_map.md` 挑 1 個 clone 頁型(如 `cycle_four_point_loop` p35),
`inspect_template.py --page 35` 取一個文字框 id,寫最小 plan(改一字)走
`render_deck --plan` + `qa_check`。預期:PASS。此案例驗證「clone 級頁型 +
本包模板頁」的通路,不驗內容品質。
