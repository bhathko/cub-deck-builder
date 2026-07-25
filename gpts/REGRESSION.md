# 發版前本機回歸

> 取代從未進版控的 `docs/superpowers/plans/2026-07-21-outline-to-ppt-knowledge-skill.md`
> 懸空引用;下列所有命令與預期結果於 **2026-07-24 全數實測通過**。
> 任何 knowledge/tools/assets 異動後、重新上傳 GPTs 前,全部案例必須全綠。

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
for z, dest in [('gpts/knowledge/tools.zip','$RT/tools'),
                ('gpts/knowledge/template_light.zip','$RT/templates/light')]:
    bad=[i.orig_filename for i in zipfile.ZipFile(z).infolist() if '\\\\' in i.orig_filename]
    print(z, 'OK' if not bad else f'含反斜線路徑:{bad}')
    zipfile.ZipFile(z).extractall(dest)
"
cp gpts/knowledge/validate_slide_spec_gpts.py "$RT/"
```

預期:兩個 zip 都印 `OK`(每筆路徑正斜線);`$RT` 下有 `tools/` 十支腳本 +
README_TOOLS、`templates/light/`(模板包:template.pptx + manifest.json +
bindings.py + page_map.md + `assets/`)、validator。素材與模板隨包出貨,
`$RT` 根**不再有** `assets/` 與 `light_template.pptx`(工具經 pack_loader
解析,素材檢查有包內兜底)。

## R1|examples 四份 validator 預期 exit

```bash
for f in 01_minimal_4p 02_full_10p 03_advanced_unregistered_6p 04_broken_should_fail; do
  python3 "$RT/validate_slide_spec_gpts.py" --spec "gpts/examples/$f.json" --asset-dir "$RT" >/dev/null 2>&1
  echo "$f exit=$?"
done
```

預期:`01`/`02`/`03` exit=0(03 有未註冊頁型 WARN),`04` exit=1。

## R2|稽核閘門 + strict 全流程(用解出的工具)

(a) 原樣 02 + 已切頁 fixture → **必須停在階段 1**,證明 deck_name 閘門有效
(02 是直供模式範例,`deck_name: my_project` 本就不符 outline 模式規則,repo 不改它):

```bash
python3 "$RT/tools/run_pipeline.py" --spec gpts/examples/02_full_10p.json \
  --slides gpts/examples/02_full_10p.source_slides.md --asset-dir "$RT" --out "$RT/deck02.pptx"
```

預期:exit≠0,`[E] deck.deck_name「my_project」≠ 第一頁內容頁 slide[3] 的 title「年度工作總覽」`。

(b) 修 deck_name 後整條重跑 → 全流程 PASS:

```bash
python3 -c "
import json
s = json.load(open('gpts/examples/02_full_10p.json'))
s['deck']['deck_name'] = '年度工作總覽'
json.dump(s, open('$RT/spec02_fixed.json','w'), ensure_ascii=False, indent=2)
"
python3 "$RT/tools/run_pipeline.py" --spec "$RT/spec02_fixed.json" \
  --slides gpts/examples/02_full_10p.source_slides.md --asset-dir "$RT" --out "$RT/deck02.pptx"
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
  --slides gpts/examples/02_full_10p.source_slides.md; echo "exit=$?"
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
  --slides gpts/examples/02_full_10p.source_slides.md; echo "exit=$?"
```

預期:exit=1,`[E] slide[5].slots.kpis[2].value:數字 token「9」在來源區塊無精確對應:「9%」`。

**測資選擇注意**:token 比對是「該頁來源區塊的精確數字集合」;例如把 `50%` 改
`5%` 在此 fixture 會**合法通過**,因為 Slide 5 區塊本就有「月報整理時間:5 天」。
README 驗收測試 6 的 50→5 案例需要「來源僅含 50」的迷你測資。另:validator 的
相似度檢查在 strict 下也會擋「整格皆為無來源數值」的案例,但數字嵌在高相似句中
的子字串限制仍存在,不可宣稱 validator 完整硬擋(同 README「誠實的限制」)。

## R6|fixture 05 純淨度(真未切頁、無頁型指示)

```bash
grep -cE '## Slide|page_type' gpts/examples/05_outline_to_ppt_source.md
```

預期:輸出 `0`(grep exit=1)。

## R7|knowledge 清單與 archive hash

```bash
ls gpts/knowledge | grep -v __pycache__ | wc -l     # 預期 10
shasum -a 256 gpts/knowledge/tools.zip gpts/knowledge/template_light.zip
```

2026-07-25 基準值(**重打包 zip 後必須更新本節**;Phase 1 Knowledge 換裝:
assets.zip 與 light_template.pptx 併入 template_light.zip,tools.zip 十支
腳本含 pack_loader/fill_helpers。發佈時 Builder 端刪 assets.zip 與
light_template.pptx、上傳 template_light.zip 與新 tools.zip,同步 instructions
v2.0):

```
4e8f332d575ee72926def91803742137dcb0303a73b31b199f7be1611734d328  tools.zip
54681e4bbdf102f9a438b33c577c32409d794bb0146acd924b9ea470aa8c9a96  template_light.zip
```

## R8|直供 JSON 模式全流程(追溯關)

```bash
cp gpts/examples/01_minimal_4p.json "$RT/spec01.json"
python3 "$RT/tools/run_pipeline.py" --spec "$RT/spec01.json" \
  --asset-dir "$RT" --out "$RT/deck01.pptx"; echo "exit=$?"
```

預期:exit=0,驗證階段顯示「來源追溯:關」+ 缺來源 WARN,末行
`管線結果:PASS(3/3 階段)`。
