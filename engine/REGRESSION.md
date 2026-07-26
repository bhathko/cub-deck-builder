# REGRESSION — 引擎級發版前回歸

> **用途**:發版前的可執行回歸案例與預期結果,涵蓋 archive 完整性、閘門正反例、
> 稽核、QA、多模板與全包 lint。
> **讀者**:維護者。
> **何時讀**:任何 `engine/` 異動後、重新上傳 GPTs 前——**全部案例必須全綠**。
> 各模板包另有專屬案例(如 `engine/templates/light/REGRESSION.md`),
> 動到哪個包就跑哪個包 + 本檔共用案例。

**正式跑法是一鍵 runner**(2026-07-27 起;純標準庫 + subprocess,Windows 原樣可跑):

```bash
python3 engine/release/regress.py            # 全部案例;--list / --only / --skip 見 --help
```

任一案例紅即 exit 1;案例間相依(R3–R5 用 R2 的產物)由 runner 自動處理,
含 light 包的 R-L0/R-L1(R-L2 clone 抽測是唯一仍為人工的案例)。為什麼收進
工具:散文夾貼指令的回歸必然被跳過——R9 曾紅 11 個 commit 沒人發現。本檔
其餘內容是各案例的**規格與解說**(測什麼、為什麼、預期輸出的由來),手動
單跑或診斷時照下方指令;**新增/修改案例必須與 `regress.py` 同步**,只改
文件等於沒改(runner 才是被跑的那份)。

以下為手動單跑的前置:在 repo 根目錄執行;`$RT` 為全新暫存目錄(每次回歸重建,不得重用)。
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

預期:兩個 zip 都印 `OK`(每筆路徑正斜線);`$RT` 下有 `tools/` 腳本 +
README_TOOLS、`templates/light/`(模板包:template.pptx + manifest.json +
bindings.json + page_map.md + `assets/`)、validator。
**任何包都不得有 `bindings.py`**(builtin 繪製器的載體,2026-07-26 清零,
見該包 page_map.md)——解出來若有這支檔就是 zip 打錯了。載入期與 lint
兩處硬擋,反向測試見 R10。
素材與模板隨包出貨,
`$RT` 根**不再有** `assets/` 與 `light_template.pptx`(工具經 pack_loader
解析,素材檢查有包內兜底)。

## R1|examples 四份 validator 預期 exit

```bash
for f in 01_minimal_4p 02_full_8p 03_advanced_unregistered_6p 04_broken_should_fail; do
  python3 "$RT/validate_slide_spec_gpts.py" --spec "engine/examples/$f.json" --asset-dir "$RT" >/dev/null 2>&1
  echo "$f exit=$?"
done
```

預期:`01`/`02`/`03` exit=0(03 有未註冊頁型 WARN),`04` exit=1。

## R2|稽核閘門 + strict 全流程(用解出的工具)

(a) 原樣 02 + 已切頁 fixture → **必須停在階段 1**,證明 deck_name 閘門有效
(02 是直供模式範例,`deck_name: my_project` 本就不符 outline 模式規則,repo 不改它):

```bash
python3 "$RT/tools/run_pipeline.py" --spec engine/examples/02_full_8p.json \
  --slides engine/examples/02_full_8p.source_slides.md --asset-dir "$RT" --out "$RT/deck02.pptx"
```

預期:exit≠0,`[E] deck.deck_name「my_project」≠ 第一頁內容頁 slide[3] 的 title「年度工作總覽」`。

(b) 修 deck_name 後整條重跑 → 全流程 PASS:

```bash
python3 -c "
import json
s = json.load(open('engine/examples/02_full_8p.json'))
s['deck']['deck_name'] = '年度工作總覽'
json.dump(s, open('$RT/spec02_fixed.json','w'), ensure_ascii=False, indent=2)
"
python3 "$RT/tools/run_pipeline.py" --spec "$RT/spec02_fixed.json" \
  --slides engine/examples/02_full_8p.source_slides.md --asset-dir "$RT" --out "$RT/deck02.pptx"
```

預期:exit=0,末行 `管線結果:PASS(4/4 階段)`。

> **2026-07-27 已修復(政策決定:容量壓縮豁免)。** 本案例曾紅 —— `d6e6373`
> (誠實容量)把 light 容量收到版位實際值後,example 02 的槽位文字被壓成
> 摘要式改寫,strict 相似度 9 條掉到 0.55 門檻下。這不是 fixture 特例:
> 來源句 22 字、版位 17 字時,「改短就不像、像了就超容量」,真實 outline
> 使用者一樣會被卡死。使用者拍板的修法是雙管:
>
> - **機制**:validator 新增 `capacity_compressed()` 豁免——與該值相關的
>   來源句**全部**放不進版位上限、且值的內容字元 ≥90% 出自來源(刪字重排,
>   非造新詞)時,低相似度印「容量壓縮豁免」提示、不升級。**數字 token 與
>   標題逐字兩條硬線不經此路徑,完全不受影響**(R4/R5 仍驗)。
> - **fixture**:02 的 9 條改寫改成「來源連續片段」式壓縮(順帶修正 kpis
>   兩條標籤與數值配對錯誤——「自動化覆蓋率」配的值其實是「跨部門大型
>   專案:2 項」)。同義改寫(「版本差異」→「分歧」)不是被迫壓縮,
>   政策上就該擋。
>
> (c) 豁免機制雙向驗證(runner 的 R2 內建):core_mission(上限 11,相關
> 來源句 29 字)填「資料串流程」(刪字重排,cov 0.50)→ strict 下 exit 0
> 並印豁免提示;填「串接流程與資料」(「接」不在來源,containment 0.86)
> → 仍 exit 1。**豁免變寬鬆(同義改寫也放行)= 防幻覺被掏空**,任何調整
> containment 門檻的提案都要先過這條反向測試。

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
  --slides engine/examples/02_full_8p.source_slides.md; echo "exit=$?"
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
  --slides engine/examples/02_full_8p.source_slides.md; echo "exit=$?"
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

2026-07-26 基準值(**打包已可重現**:內容沒變重打包 sha 就不變,
所以本節 sha 變動 = zip 內容真的變了;Phase 2:tools.zip 十一支
腳本含 fills_engine,template_light.zip 增 bindings.json 等價素材。發佈時
Builder 端刪 assets.zip 與 light_template.pptx、上傳 template_light.zip 與
新 tools.zip,同步 instructions v2.0):

```
201b46c03c4d010b121d3b25d86edd6cd323e26ef249b7f6f9d3689638294c9d  tools.zip
74dc425c5d71eb250170300b183d6a2ee7795214f08b2041b94d98545582a881  template_light.zip
```

(2026-07-27 builtin 死碼清除:上一批把 light 的 builtin 降到 0,這批把**模式本身**
從引擎拆掉。支援等級只剩 fill/clone/unsupported;render_deck 的 plan `mode=builtin`
與 `pack.builders` 兩條分支、trace_page 的 builtin 路由、pack_loader 的 bindings.py
載入路徑與 BUILDERS 全部移除。`bindings.py` 從「可載入」變成**兩處硬擋**:
pack_loader 載入期 PackError + lint 報錯(反向測試見 R10)——留著載入路徑等於留著
沙箱幽靈檔事故的後門。template_admin 的 `MODES` 移除 builtin,遇到舊 manifest 會
指路「改綁 fill 或降級 clone」。tools.zip 因 pack_loader/render_deck/make_skeleton/
README_TOOLS/fill_helpers/pptx_toolkit 六檔變動而改 sha。順帶清掉三處只有 builtin
繪製器用過的死碼:`pptx_toolkit.add_blank_slide`、`fill_helpers.resolve_asset`
(活實作是 validator 的 `asset_exists`),以及 `pptx_toolkit` 並列的 6 個 accent
色常數——色碼是模板專屬知識,真相在各包 manifest 的 `style.colors`,留在模板無關的
引擎檔裡本身就違反架構原則;`FONT_ZH`/`COLOR_DARK` 因頁碼框仍在用而保留。**template_light.zip 也改 sha**:
`bindings.json` 的 `_note` 原本用現在式寫「剩餘 builtin 頁型在同目錄 bindings.py」,
那是整個出貨包裡唯一一句宣稱 builtin 仍在運作的文字,模型讀了會去找一支不存在的
檔;light@2026-07-26.4 → 2026-07-27.1。instructions 版本字串 v2.2-20260726 →
v2.3-20260727、roster 同步。產檔行為零變化:light 早已 0 builtin,
golden 仍 38 頁 PASS、冪等雙跑一致。)

(2026-07-26 builtin 清零(第二批,light@2026-07-26.4):`agenda` 綁 p9,
`story_chapter_statement` 與 `stage_dual_track_roadmap` **從共用契約整個移除**
(無模板頁可綁;此決定牴觸「不得為單一模板改共用契約」先例,理由見 WORKLOG)。
`bindings.py` **整檔刪除**——light 現在是純 bindings.json,與新註冊包同構;
`$RT/templates/light/` 不再有該檔(R0 預期已同步)。
**兩個 zip 都改 sha**:tools.zip 因 `fills_engine.py` 加 `item_template` 修飾詞
(詞彙表 v1.2,引擎版本事件);template_light.zip 因 manifest/bindings.json/
刪 bindings.py/page_map.md。PAGE_TYPES 21 → 19、golden fixtures 42 → 38、
light page_types 53 → 51。examples 的 `02_full_10p` 改名 `02_full_8p`
(移除兩頁後名實不符),連同 `.source_slides.md` 的 `## Slide N` 分節一併重編。
新增 1 條 agenda capacity_overrides(`subtitle` 28 字)——**手寫,非 fit 產出**:
fit 把整份清單映射到 `items.item`,那是**物件**節點,而
`fit_capacity.py:662` 只在 `kind == "text"` 時寫 `max_chars`,遇物件靜默跳過,
於是印出假的「零縮字」。實測 18pt 邊界:副標 30 字內單行、32 字折兩行就爆框,
取 28 留餘裕;R12 驗證腳本已確認被縮字 0。**要修這個盲點得讓 fit 會把物件清單
的容量分配到各文字子欄位**,在那之前 agenda 的容量不受 `fit --reset` 保護。)

(2026-07-26 builtin→fill 遷移第一批:`cover` 綁 p7、`closing` 綁 p59,
`bindings.py` 的 BUILDERS 移除這兩支(連同只有 build_cover 用的 `_em` 死碼),
light@2026-07-26.3。**tools.zip 未動,不需重傳**;template_light.zip 因
manifest/bindings.json/bindings.py/page_map.md 四檔變動而改 sha。
遷移後 cover 的行為改變:長主標由 shrink_to_fit 縮字級,不再把副標推到下一行。
新增 3 條 cover capacity_overrides——`subtitle` 只有 5 字,因為模板 p7 的副標框
(id=16)是 `spAutoFit` 且僅 3.24 吋寬,長文會讓框往下長並壓到 id=3 的日期列;
這是真碰撞不是誤報。剩餘 builtin(agenda/story/stage)待模板補頁,清單見
`engine/templates/light/page_map.md` 的遷移表。)

(2026-07-26 tools.zip 由 `c5737f13…` 換成 `596a036c…`:清掉 `README_TOOLS.md`
與 `render_deck.py` 檔頭寫死的「21 種註冊頁型」與其後**只列 10–11 個名字**的
清單——那是功能性缺陷,模型照著讀會誤以為其餘頁型不能用(同型缺陷見
commit `3f22aff`)。兩處都改成指向 `make_skeleton.py --list`。
template_light.zip 未動,不需重傳。)

(2026-07-26 碰撞判準:設計師目檢 p4/p10/p22/p30 指出「不是 autofit 沒超過,
是 autofit 後跑到了不該出現字的位置」。qa_check 新增文字碰撞檢查(FAIL 級),
判準為「不得比模板原本更侵入鄰欄」;容量重新收斂,32 頁零縮字、零新增碰撞。
另修 info_three_column_category 第三欄只有 4 格(另兩欄 6 格)造成的三欄不對稱。)

(2026-07-26 誠實容量:改採「字級是設計過的,塞不下要改稿或換頁型,不縮字」
原則。渲染器不再縮 autofit 框的字級;light 的 45 條 capacity_overrides 由
template_admin 依模板實際版位量測後產生(非人工填)。結果:contract 上限時
被縮字的框 99 → 0、qa 溢出警告 79 → 0。字體白名單補齊模板自用字型。)

(2026-07-26 目檢回饋修正:qa_check 溢出不再靜默只印前 5(舊版把 79 條顯示成
5 條)、estimate_overflow 修三處誤判(窄框不再無條件視為放得下、數學英數符號
𝟭𝟮𝟯𝟰 不再當全形、wrap="none" 框不按框寬折行)、golden 變體文字加序號前綴
(舊版每格都填一樣的字,看不出綁定有沒有把第 3 項填進第 1 格)。tools.zip 因
text_tools/qa_check 變動而改 sha;同一份 examples/02_full_8p.json(當時檔名 02_full_10p) 用新舊引擎
渲染字級零差異——估算器改動只在契約上限的極端情況生效。)

(2026-07-26 v2.1:一次註冊 10 種純文字頁型(p16/20/22/24/30/35/38/40/47/50),
light 支援矩陣由「全自動 11 / 半自動 42」變為「全自動 21 / 半自動 32」,
light@2026-07-26.2;tools.zip 變動僅 render_deck.py 註解的頁型數字,
template_light.zip 增 10 份 fill 綁定 + 重 freeze 的 inventory。)

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
m['capacity_overrides'] = src['capacity_overrides']   # 少這行 golden 必 FAIL,見下方註
json.dump(m, open(p, 'w'), ensure_ascii=False, indent=2)
shutil.copy2('engine/templates/light/bindings.json', '$PR/lightcopy/bindings.json')
shutil.copytree('engine/templates/light/assets_src', '$PR/lightcopy/assets_src', dirs_exist_ok=True)
"
python3 engine/release/template_admin.py freeze --id lightcopy --packs-root "$PR"
python3 engine/release/template_admin.py register --id lightcopy --packs-root "$PR"; echo "register exit=$?"
```

預期:register exit=0(lint → 自身 golden PASS(頁數 = 該包 fill 頁型數 ×
min/max,**不要寫死**——複製自 light 就跟著 light 當下的 fill 數走)含冪等雙跑
→ light 回歸 golden PASS → status=registered)。之後同一份 fill 頁型 spec 分別以
light 與 `deck.template:"lightcopy"`(帶 `--packs-root "$PR"`)各 render+qa
一次,兩者皆 PASS 且輸出行分別顯示 `模板包:light@…` 與 `模板包:lightcopy@…`。
(工作樹有模板目錄外的改動時,register 末尾會印 isolation 越界警告,那是預期的
提醒而非失敗——見 MAINTENANCE 第 5 節第 2 項。)

**`capacity_overrides` 必須一起複製**(2026-07-27 補):它不是可選的美化設定,
而是「這個版位真正裝得下多少字」的量測結果。少了它,golden 會用 `PAGE_TYPES` 的
跨模板契約上限產 max 變體——那個上限遠大於 light 版位的實際容量,於是 qa 直接
FAIL 在一堆溢出上(`[W] p10: 溢出疑慮 x6.0` 之類)。本案例自 `d6e6373`
(誠實容量:契約上限不再靠縮字掩蓋)起就一直是紅的,直到 2026-07-27 才被抓到
——**紅了 11 個 commit 沒人發現,因為沒有人真的跑過 R9**。

## R10|全包 lint

```bash
python3 engine/release/template_admin.py lint --all; echo "exit=$?"
```

預期:exit=0,每包一行 `✓ <id>: lint OK`。(light 原本那行 grandfather 提示已隨
2026-07-27 的 builtin 死碼清除一併收掉,不再出現。)

**反向測試——`bindings.py` 後門的兩道防線還活著嗎?** builtin 曾經能靠一支
`bindings.py` 悄悄蓋過 `bindings.json` 的 fill(2026-07-26 沙箱幽靈檔事故:
產出是舊版面,而所有訊息都顯示正常)。種一支進去,兩處都必須紅:

```bash
printf 'BUILDERS = {}\n' > engine/templates/light/bindings.py
python3 engine/release/template_admin.py lint --id light; echo "lint exit=$?"
python3 engine/tools/render_deck.py --spec engine/examples/01_minimal_4p.json \
  --asset-dir engine/templates/light/assets_src --out "$RT/_guard.pptx"; echo "render exit=$?"
rm -f engine/templates/light/bindings.py
```

預期:`lint exit=1` 且印 `包內不得有 bindings.py`;`render exit=2` 且印
`✗ 模板包載入失敗:模板包 light 內有 bindings.py`。任一 exit=0 = 後門又開了。
**跑完務必確認那支檔已刪**(`git status` 要乾淨)。

## R11|golden 契約快照與現行契約同步

`engine/golden/` 是**跨模板的契約快照**(不是實跑素材——實跑由 template_admin
依各包 merged 契約即時派生)。它的用途是「契約改動時 git diff 看得見形狀變化」,
所以必須與 `PAGE_TYPES` 保持同步:

```bash
python3 engine/release/template_admin.py golden --regen-specs
git diff --exit-code engine/golden/*.json; echo "exit=$?"
```

預期:`exit=0`(無差異)。**非 0 = 有人改了頁型契約卻沒重派生快照**
——修法是把重派生的結果一起 commit。
(Phase 4 加 chart 頁型時就漏過這步,靠稽核才發現;R11 就是為了不再靠人記得。)

## R12|誠實容量:contract 上限不得觸發縮字

```bash
python engine/release/template_admin.py golden --id light
```

golden 用每個 fill 頁型的 **contract 上限**產 max 變體。通過條件除了 PASS,
還要:**溢出警告為 0**、且**沒有「文字壓到別的元素」的 FAIL**。

設計師的原話:「有時候不是 autofit 沒超過,是 autofit 後跑到了不該出現字的
位置」。所以「裝得進自己的框」不是充分條件——`wrap="none"` 的框會往右長、
autofit 的框會往下長,結果壓到鄰欄。qa_check 用 `tt.text_collisions` 比對
文字實際佔用範圍,判準是**不得比模板原本更侵入鄰欄**(模板有幾處刻意疊在
一起,絕對零重疊會誤殺)。

原則(2026-07-26 設計師回饋):**字級是設計過的**,內容塞不下時正確做法是
改寫更短或換頁型,不是把字縮小一號。所以:

- `shrink_to_fit` 不動 autofit 框(交給 PowerPoint 長高,那是模板原本的排版方式)
- 各包用 `capacity_overrides` 宣告自己版位真正裝得下的量,閘門據此擋
- 重新量測**用工具,不要手做**:

```bash
python engine/release/template_admin.py fit --id light --reset
```

  它會反覆「跑 golden → 找出被縮字/侵入鄰欄的框 → 收緊上限」直到四個訊號
  全部歸零。演算法與 15 個已知量測陷阱見 `engine/release/fit_capacity.py` 檔頭。
  本節的數值即由它產生;手改 `capacity_overrides` 視為違規。

驗證有沒有退化。**頁序不要硬寫**——加開或降級頁型後就過期,會靜默對到錯的
模板頁而假 PASS(舊版腳本就是這樣):

```bash
python - <<'EOF'
import sys, json; sys.path.insert(0,'engine/tools'); sys.path.insert(0,'engine/rules')
from pptx import Presentation
import text_tools as tt
m = json.load(open('engine/templates/light/manifest.json'))
fills = list(json.load(open('engine/templates/light/bindings.json'))["fills"])
order = [pt for pt in m["page_types"] if pt in fills]      # = golden 的派生順序
seq = [pt for pt in order for _ in ("min", "max")]
page_of = {pt: e["template_page"] for pt, e in m["page_types"].items()
           if e.get("mode") == "fill"}
tpl = Presentation('engine/templates/light/template.pptx')
g = Presentation('ppt_out/golden_light.pptx')
assert len(g.slides) == len(seq), f"頁數不符:golden {len(g.slides)} vs 預期 {len(seq)}"
T = {pt: {s.shape_id: s for s in tt.iter_text_shapes(tpl.slides[pg-1].shapes)}
     for pt, pg in page_of.items()}
BASE = {pt: {frozenset((a.shape_id, b.shape_id)): ar
             for ar, a, b in tt.text_collisions(tpl.slides[pg-1])}
        for pt, pg in page_of.items()}
shr = worse = 0
for i, sl in enumerate(g.slides, 1):
    pt = seq[i-1]
    for s in tt.iter_text_shapes(sl.shapes):
        o = T[pt].get(s.shape_id)
        if o is not None and tt._first_run_size_pt(s) < tt._first_run_size_pt(o) - 0.5:
            shr += 1; print(f"  縮字 p{i} {pt} id{s.shape_id}")
    for ar, a, b in tt.text_collisions(sl):
        ref = BASE[pt].get(frozenset((a.shape_id, b.shape_id)), 0.0)
        if ar > max(ref * 1.10, 0.03):
            worse += 1; print(f"  侵入 p{i} {pt} id{a.shape_id}x{b.shape_id} {ar:.2f}in2")
print(f"被縮字 {shr} / 比模板更侵入鄰欄 {worse} — 兩者都必須是 0")
EOF
```

**反向測試也要做**,否則不知道偵測器還活著。做法是**改 spec 再直接渲染**
(繞過閘門,但內容與 spec 對得上——否則會先卡在「內容未出現」那條檢查,
證明不了碰撞偵測有沒有壞):

```bash
python - <<'EOF'
import json
s = json.load(open('ppt_out/golden_light.spec.json'))
for sl in s['slides']:
    if sl['page_type'] == 'data_three_number_kpis':
        for k in sl.get('slots', {}).get('kpis', []):
            k['detail'] = '刻意超長的說明文字用來驗證碰撞偵測會不會擋下來真的很長'
s['deck'].pop('template', None)
json.dump(s, open('ppt_out/_neg.json', 'w'), ensure_ascii=False, indent=2)
EOF
python engine/tools/render_deck.py --spec ppt_out/_neg.json \
  --template-pack engine/templates/light --asset-dir <素材根> --out ppt_out/_neg.pptx
python engine/tools/qa_check.py --spec ppt_out/_neg.json \
  --pptx ppt_out/_neg.pptx --template-pack engine/templates/light; echo "exit=$?"
```

預期 exit=1,且輸出含 `[F] p27/p28: 文字壓到別的元素 0.71 平方吋`
(頁號隨 fill 頁型增減而移動,2026-07-27 實測為 p27/p28;對不上先確認頁序而非判定壞掉)。
**exit=0 代表偵測器壞了**——那比破版本身更嚴重,所有後續驗收都會假綠。

**注意 `fit` 收斂後仍會有一堆 `estimate_overflow()['fits'] == False` 的框,
那是正確的。** 判準是「文字範圍不比模板更侵入鄰欄」,不是「每個框都裝得下
自己的文字」;`wrap="none"` 的標籤框文字往右長但仍在卡片底板內、沒碰到鄰欄
文字,就不算破版。稽核時不要拿 `fits=False` 當漏報。


## R13|派生檔與機器真相同步(pack 已內建,本項是人工複核)

`engine/rules/slide_spec.schema.json` 的 `page_type` enum 與
`engine/templates/INDEX.md` 的模板包表格,都是**從機器真相派生**的抄本
(前者來自 validator `PAGE_TYPES`,後者來自各包 `manifest.json`)。
抄本會漂,而且漂了沒有任何測試會紅——schema enum 尤其危險:**全 repo 沒有
任何程式消費它**(無 `jsonschema` import;整份刪掉管線照樣 exit 0),
它唯一的消費者是 GPTs 端模型的語意檢索,所以漏改在 repo 端 100% 測不到,
卻會讓線上模型拒用新頁型(同型缺陷見 commit `3f22aff`)。

```bash
python3 engine/release/template_admin.py sync-docs; echo "exit=$?"
```

預期:`exit=0`,輸出 `✓ sync-docs:2 個派生檔與機器真相一致`。
非 0 = 有人改了契約或 manifest 卻沒重生派生檔 —— 修法是
`sync-docs --write` 後把結果一起 commit。

**這一項平常不必手動跑**:`pack` 已經內建同一個檢查,漂移就打不出 zip
(掛載理由見 `engine/release/sync_docs.py` 檔頭——把同步規則寫進文件的做法,
本 repo 在 2026-07-26 一天之內被證偽兩次)。本項存在是為了讓回歸清單能
獨立複核閘門本身沒壞。驗證閘門真的會擋:

```bash
cp engine/templates/INDEX.md /tmp/INDEX.bak
python3 - <<'PY'
import pathlib
p = pathlib.Path("engine/templates/INDEX.md")
p.write_text(p.read_text(encoding="utf-8").replace("registered", "draft", 1), encoding="utf-8")
PY
python3 engine/release/template_admin.py pack --tools; echo "exit=$?"   # 預期 1,且 zip 未被改寫
cp /tmp/INDEX.bak engine/templates/INDEX.md && rm /tmp/INDEX.bak
```

**注意生成器刻意不涵蓋 `page_types_registry.md` 的契約節**(約 36% 是人寫語意,
且人寫段落在一節內有前/中/尾三種位置,機械生成會弄丟閱讀順序而機器測不出來)、
也不做「掃描文件裡的 N 種」regex 檢查(實測 1 真命中 : 2 假警報 : 1 漏報)。
那兩塊的正解是**讓數字消失**——文件不寫「共 N 種」,改指
`make_skeleton.py --list`,已於 2026-07-26 全面套用。理由詳見 `sync_docs.py` 檔頭。
