# REGRESSION — 引擎級發版前回歸(R0–R10)

> **用途**:發版前的可執行回歸案例與預期結果,涵蓋 archive 完整性、閘門正反例、
> 稽核、QA、多模板與全包 lint。
> **讀者**:維護者。
> **何時讀**:任何 `engine/` 異動後、重新上傳 GPTs 前——**全部案例必須全綠**。
> 各模板包另有專屬案例(如 `engine/templates/light/REGRESSION.md`),
> 動到哪個包就跑哪個包 + 本檔共用案例。

前置:在 repo 根目錄執行;`$RT` 為全新暫存目錄(每次回歸重建,不得重用)。
命令為 POSIX shell 語法(macOS/Linux)。Windows 維護者(公司禁 WSL,僅
PowerShell/cmd):多行 `python3 -c "..."` 區塊請存成 `.py` 檔執行以避開引號
地獄,`for` 迴圈與 `$RT` 自行改寫;日常產檔不受此限——skill 的命令全平台通用。
validator/audit/make_skeleton 只用標準庫;渲染與 QA 需 python-pptx,系統沒裝時
把下方 `python3` 換成 `uv run --with python-pptx python`(zsh 注意:存成變數
不會自動分詞,直接寫全命令)。

```bash
RT="$(mktemp -d)"
```

## R0|archive 完整性與環境建置(鏡射 GPTs Step 0 佈局)

```bash
python3 -c "
import zipfile, os
os.makedirs('$RT/tools', exist_ok=True)
os.makedirs('$RT/templates/light', exist_ok=True)
for z, dest in [('gpts/dist/tools.zip','$RT/tools'),
                ('gpts/dist/template_light.zip','$RT/templates/light')]:
    bad=[i.orig_filename for i in zipfile.ZipFile(z).infolist() if '\\\\' in i.orig_filename]
    print(z, 'OK' if not bad else f'含反斜線路徑:{bad}')
    zipfile.ZipFile(z).extractall(dest)
"
cp engine/rules/validate_slide_spec_gpts.py "$RT/"
```

預期:兩個 zip 都印 `OK`(每筆路徑正斜線);`$RT` 下有 `tools/` 十一支腳本 +
README_TOOLS、`templates/light/`(模板包:template.pptx + manifest.json +
bindings.py + page_map.md + `assets/`)、validator。素材與模板隨包出貨,
`$RT` 根**不再有** `assets/` 與 `light_template.pptx`(工具經 pack_loader
解析,素材檢查有包內兜底)。

## R1|examples 四份 validator 預期 exit

```bash
for f in 01_minimal_4p 02_full_10p 03_advanced_unregistered_6p 04_broken_should_fail; do
  python3 "$RT/validate_slide_spec_gpts.py" --spec "engine/examples/$f.json" --asset-dir "$RT" >/dev/null 2>&1
  echo "$f exit=$?"
done
```

預期:`01`/`02`/`03` exit=0(03 有未註冊頁型 WARN),`04` exit=1。

## R2|稽核閘門 + strict 全流程(用解出的工具)

(a) 原樣 02 + 已切頁 fixture → **必須停在階段 1**,證明 deck_name 閘門有效
(02 是直供模式範例,`deck_name: my_project` 本就不符 outline 模式規則,repo 不改它):

```bash
python3 "$RT/tools/run_pipeline.py" --spec engine/examples/02_full_10p.json \
  --slides engine/examples/02_full_10p.source_slides.md --asset-dir "$RT" --out "$RT/deck02.pptx"
```

預期:exit≠0,`[E] deck.deck_name「my_project」≠ 第一頁內容頁 slide[3] 的 title「年度工作總覽」`。

(b) 修 deck_name 後整條重跑 → 全流程 PASS:

```bash
python3 -c "
import json
s = json.load(open('engine/examples/02_full_10p.json'))
s['deck']['deck_name'] = '年度工作總覽'
json.dump(s, open('$RT/spec02_fixed.json','w'), ensure_ascii=False, indent=2)
"
python3 "$RT/tools/run_pipeline.py" --spec "$RT/spec02_fixed.json" \
  --slides engine/examples/02_full_10p.source_slides.md --asset-dir "$RT" --out "$RT/deck02.pptx"
```

預期:exit=0,末行 `管線結果:PASS(4/4 階段)`。

## R3|QA 先 WARN 後 PASS,exit 仍 0

刪掉 deck02 一個右下角頁碼框再跑 QA:

```bash
python3 -c "
from pptx import Presentation
from pptx.util import Inches
p = Presentation('$RT/deck02.pptx'); done = False
for sl in p.slides:
    if done: break
    for shp in list(sl.shapes):
        if shp.has_text_frame and shp.text_frame.text.strip().isdigit() \
           and (shp.top or 0) > Inches(6.3) and (shp.left or 0) > Inches(11.0):
            shp._element.getparent().remove(shp._element); done = True; break
p.save('$RT/deck02_warn.pptx')
"
python3 "$RT/tools/qa_check.py" --spec "$RT/spec02_fixed.json" --pptx "$RT/deck02_warn.pptx"; echo "exit=$?"
```

預期:exit=0,輸出含 `[W] p2: 找不到右下角頁碼 2` 且有一行以 `結果:PASS` 開頭。

## R4|title 注入 → 稽核擋

```bash
python3 -c "
import json
s = json.load(open('$RT/spec02_fixed.json'))
s['slides'][5]['title'] = '來源沒有的注入標題'
json.dump(s, open('$RT/spec02_inject.json','w'), ensure_ascii=False)
"
python3 "$RT/tools/audit_provenance.py" --spec "$RT/spec02_inject.json" \
  --slides engine/examples/02_full_10p.source_slides.md; echo "exit=$?"
```

預期:exit=1,`[E] slide[6] 頂層 title「來源沒有的注入標題」未逐字出現在該頁來源區塊`。

## R5|精確數字 token → 稽核擋

把 `95%` 改成 `9%`(Slide 5 來源區塊沒有獨立的 9):

```bash
python3 -c "
raw = open('$RT/spec02_fixed.json').read().replace('\"95%\"','\"9%\"')
open('$RT/spec02_token.json','w').write(raw)
"
python3 "$RT/tools/audit_provenance.py" --spec "$RT/spec02_token.json" \
  --slides engine/examples/02_full_10p.source_slides.md; echo "exit=$?"
```

預期:exit=1,`[E] slide[5].slots.kpis[2].value:數字 token「9」在來源區塊無精確對應:「9%」`。

**測資選擇注意**:token 比對是「該頁來源區塊的精確數字集合」;例如把 `50%` 改
`5%` 在此 fixture 會**合法通過**,因為 Slide 5 區塊本就有「月報整理時間:5 天」。
README 驗收測試 6 的 50→5 案例需要「來源僅含 50」的迷你測資。另:validator 的
相似度檢查在 strict 下也會擋「整格皆為無來源數值」的案例,但數字嵌在高相似句中
的子字串限制仍存在,不可宣稱 validator 完整硬擋(同 README「誠實的限制」)。

## R6|fixture 05 純淨度(真未切頁、無頁型指示)

```bash
grep -cE '## Slide|page_type' engine/examples/05_outline_to_ppt_source.md
```

預期:輸出 `0`(grep exit=1)。

## R7|Knowledge 清單與 archive hash

```bash
ls engine/rules | grep -v __pycache__ | wc -l     # 預期 8(散檔)
ls gpts/dist | wc -l                              # 預期 2(zip)
shasum -a 256 gpts/dist/tools.zip gpts/dist/template_light.zip
```

上傳 GPTs 的 Knowledge = 這 8 + 2 = **10 個檔**(上限 20,守 ≤19 紀律)。

2026-07-25 基準值(**重打包 zip 後必須更新本節**;Phase 2:tools.zip 十一支
腳本含 fills_engine,template_light.zip 增 bindings.json 等價素材。發佈時
Builder 端刪 assets.zip 與 light_template.pptx、上傳 template_light.zip 與
新 tools.zip,同步 instructions v2.0):

```
45d9bd8cf0d8a0dbb0a16eec8b419bb2afb413de374563ace78bd5e5426c099a  tools.zip
a8813219312dc92fbfa144110b855a0ee3d9ee2ebfe745deeb83fd60f3eebc46  template_light.zip
```

(2026-07-25 Phase 3:light fills 切換宣告式 bindings.json,bindings.py 瘦身為
builders-only;light 包版本 2026-07-25.2。同日 repo 重構:引擎移至 engine/、zips 移至
gpts/dist/(WORKLOG §21);Phase 4 chart 頁型:tools.zip 增 chart op/qa 圖表
讀取/clone chart part 深複製,template_light.zip 增 data_line fill 綁定,
light@2026-07-25.3,見 WORKLOG §22。)

## R8|直供 JSON 模式全流程(追溯關)

```bash
cp engine/examples/01_minimal_4p.json "$RT/spec01.json"
python3 "$RT/tools/run_pipeline.py" --spec "$RT/spec01.json" \
  --asset-dir "$RT" --out "$RT/deck01.pptx"; echo "exit=$?"
```

預期:exit=0,驗證階段顯示「來源追溯:關」+ 缺來源 WARN,末行
`管線結果:PASS(3/3 階段)`。

## R9|多模板:同 spec 換 deck.template 產兩份

以 light 複本當第二個包(端到端註冊演練;渲染需 python-pptx 前綴):

```bash
PR="$(mktemp -d)"
python3 engine/release/template_admin.py new --pptx engine/templates/light/template.pptx --id lightcopy --name 淺色複本測試 --packs-root "$PR"
python3 -c "
import json, shutil
src = json.load(open('engine/templates/light/manifest.json'))
p = '$PR/lightcopy/manifest.json'; m = json.load(open(p))
m['style'], m['asset_defaults'], m['page_number'] = src['style'], src['asset_defaults'], src['page_number']
m['page_types'] = {pt: e for pt, e in src['page_types'].items() if e['mode'] == 'fill'}
json.dump(m, open(p, 'w'), ensure_ascii=False, indent=2)
shutil.copy2('engine/templates/light/bindings.json', '$PR/lightcopy/bindings.json')
shutil.copytree('engine/templates/light/assets_src', '$PR/lightcopy/assets_src', dirs_exist_ok=True)
"
python3 engine/release/template_admin.py freeze --id lightcopy --packs-root "$PR"
python3 engine/release/template_admin.py register --id lightcopy --packs-root "$PR"; echo "register exit=$?"
```

預期:register exit=0(lint → 自身 golden 10 頁 PASS 含冪等雙跑 → light
回歸 golden PASS → status=registered)。之後同一份 fill 頁型 spec 分別以
light 與 `deck.template:"lightcopy"`(帶 `--packs-root "$PR"`)各 render+qa
一次,兩者皆 PASS 且輸出行分別顯示 `模板包:light@…` 與 `模板包:lightcopy@…`。

## R10|全包 lint

```bash
python3 engine/release/template_admin.py lint --all; echo "exit=$?"
```

預期:exit=0,每包一行 `✓ <id>: lint OK`(light 另有 grandfather 提示行)。
