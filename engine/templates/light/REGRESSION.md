# light 包回歸(發版前必跑)

> 引擎級/共用案例見 `engine/REGRESSION.md`(全部 R 案例本就以 light 為測物,
> 其中 R2/R3/R8 = 本包的渲染/QA 回歸)。本檔補包專屬案例;
> `$RT` 沿根檔定義。渲染需 python-pptx(沒裝時 `python3` 換
> `uv run --with python-pptx python`)。

## R-L0|包完整性

```bash
python3 -c "
import json, hashlib
from collections import Counter
m = json.load(open('engine/templates/light/manifest.json'))
sha = hashlib.sha256(open('engine/templates/light/template.pptx','rb').read()).hexdigest()
print('manifest sha', 'OK' if sha == m['template_sha256'] else f'不符:重跑盤點(TEMPLATE_LIFECYCLE.md)')
c = Counter(v.get('mode') for v in m['page_types'].values())
print('page_types', len(m['page_types']), '筆', dict(c))
print('自洽檢查', 'OK' if len(m['page_types']) == sum(c.values()) else '不符')
"
```

預期:`manifest sha OK`、`自洽檢查 OK`、53 筆。

**mode 分佈刻意不寫死預期值**——builtin 正在逐步遷往 fill(進度見
`page_map.md` 的遷移表),寫死的比例會過期。要對照當下分佈跑
`python engine/tools/make_skeleton.py --list`;`page_map.md` 的統計句與同檔
表格互為校驗。

## R-L1|smoke spec 直供模式全流程

```bash
python3 "$RT/tools/run_pipeline.py" --spec engine/templates/light/examples/smoke_spec.json \
  --asset-dir "$RT" --out "$RT/deck_light_smoke.pptx"; echo "exit=$?"
```

預期:exit=0,末行 `管線結果:PASS(3/3 階段)`(等同根 R8,測物固定為本包
smoke spec;10 頁註冊頁型(其餘註冊頁型由 golden 覆蓋))。

## R-L2|clone 抽測(半自動路徑)

從 `page_map.md` 挑 1 個 clone 頁型(如 `cycle_four_point_loop` p35),
`inspect_template.py --page 35` 取一個文字框 id,寫最小 plan(改一字)走
`render_deck --plan` + `qa_check`。預期:PASS。此案例驗證「clone 級頁型 +
本包模板頁」的通路,不驗內容品質。
