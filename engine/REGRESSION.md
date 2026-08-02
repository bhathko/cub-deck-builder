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
把下方 `python3` 換成 `uv run --with python-pptx==1.0.2 python`(zsh 注意:存成變數
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
ls engine/rules | grep -v __pycache__ | wc -l     # 預期 9(散檔)
ls gpts/dist | wc -l                              # 預期 2(zip)
shasum -a 256 gpts/dist/tools.zip gpts/dist/template_light.zip
```

上傳 GPTs 的 Knowledge = 這 9 + 2 = **11 個檔**(上限 20,守 ≤19 紀律;
2026-07-31 增 `enrich_outline_skill.md`)。

2026-07-26 基準值(**打包已可重現**:內容沒變重打包 sha 就不變,
所以本節 sha 變動 = zip 內容真的變了;Phase 2:tools.zip 十一支
腳本含 fills_engine,template_light.zip 增 bindings.json 等價素材。發佈時
Builder 端刪 assets.zip 與 light_template.pptx、上傳 template_light.zip 與
新 tools.zip,同步 instructions v2.0):

```
9eb8449f87f9b798e02ee827a17c2d4d1cdc0432ca611f8acd2df7175fe8179b  tools.zip
1ed266d593293231e2cda7c5b733705c2b713e3b02828137037a48e7c5ca33b4  template_light.zip
```

**這個區塊是「當下」基準,不是歷史快照**——`regress.py` 的 R7 直接解析這兩行
(`^64 hex + 檔名$`),重打包後沒同步就紅燈。下方括號註記是變更軌跡,
不要在註記裡再抄一份完整 sha,以免出現第二個真相。

(2026-08-02 結構級修法:封掉「機器全綠但版面壞掉」整鏈,**兩個 zip 都改 sha**。
①golden max 變體改**足額全形壓力文字**(舊變體 `tag+name+測…` 是半形前綴,
199 個槽位有 116 個實寬不到上限的 75%,壓不到寬度 → 估算器不起疑 → 該槽位
從未被量過);序號前綴改全形數字以保住「看得出填入順序」。②fit 從「估算器
起疑才量」改**全量式**(max 變體頁每個對得到槽位的框都量一次)。③qa 新增
**字級被縮小即 FAIL**——渲染器仍保留 shrink_to_fit 當最後手段,但它一縮就是
靜默的(2026-07-26 事故同型)。
壓測暴露並修掉的量測鏈缺陷:**頁面標題(spec 頂層 title)完全沒有容量契約**
(每頁都被 32pt→28pt 靜默縮字,fit 因契約無節點而無處可寫)→ PAGE_TYPES 加
頁型級 `title`,覆寫路徑 `<頁型>.title.max_chars`;`_clean_cap` 判準對齊渲染器
(零寬容,不再留 10% 帶);**互相溢出死鎖**(鄰居也脹出框 → 雙方 cap=0 → 舊版
靜默 continue → 印收斂而版面是壞的)改用「鄰居的框」量測退路並記錄;`list` op
的 `template` 字面前綴(`# {label}`)計入開銷;add_textbox 反查改用綁定宣告的
幾何(不再靠文字裡的 ASCII 槽位名);`date` 與 `value` 變體與半形量測假設對齊、
value 塞滿上限。
結果:light 全包 `fit --reset` 重量,capacity_overrides 91 → 167 條,80 個槽位
收緊(50 個 ≤20%、29 個 21-50%)、2 個放寬;golden 66 頁 PASS。
**已知未解**:`data_three_number_kpis` 的 value 版位三框寬 1.76/1.43/1.33 吋
@66pt → 上限取最小值 2 字,連模板自己的示範「150」都放不下——版位問題,
待設計師決定改版位或降級。)

(2026-08-02 全系統診斷速修,**僅 tools.zip 改 sha**:①qa_check 預設包後備
路徑 UnboundLocalError 修復 ②模板 sha 不符由警告升 FAIL(--template 明示
指定者除外)③spec 的 deck.template 鎖包 id、路徑形式僅限 CLI(rogue 包
三閘門全綠的洞)。同批 repo 側:fit subprocess 補 encoding、--reset 失敗
復原備份、python-pptx 釘 1.0.2、新增 R16(instructions roster 機器檢查)。
validator 散檔同步改,發版要重傳。)

(2026-08-01.2 目檢回饋修正:golden p14 兩組對照頁 KPI 44pt 數字「%」折行
疊到下一顆——值框僅 1.39 吋,PowerPoint 開檔時 spAutoFit 長高互疊;綁定加
resize 把三個值框加寬到 2.0 吋。估算器沒抓到是因為未扣內文邊距(量測死角,
記 docs/FEEDBACK.md)。僅 template_light.zip 改 sha。)

(2026-08-01 第二梯隊五頁型升格,**僅 template_light.zip 改 sha**:
p15 目標金字塔/p34 三節點循環/p37 多步閉環/p41 期間卡/p53 三層金字塔
clone→fill(light@2026-08-01.1)。契約收在 validator 散檔(不入 zip),
tools.zip 內容未動、sha 不變。fit 以 --reset 全量重測(resize 統一 p41
四個時間框與 NEW 徽章、p34 中心主題框加寬),capacity_overrides 92 條。)

(2026-07-31 第一梯隊六頁型升格,**兩個 zip 都改 sha**:template_light.zip 收
bindings/manifest/inventory/page_map 六頁型 clone→fill(light@2026-07-31.1);
tools.zip 收 `text_tools.estimate_overflow` 直排框補齊 `fits_w` 鍵——p42/p39
的直排標籤是**第一批**進 fill 量測的直排文字,踩到既有缺鍵 KeyError。)

(2026-07-27 出貨包文字清理——**把 `builtin` 這個已不存在的模式名,從所有描述
「現況」的文字裡拿掉**。§10.6 那批只修了「宣稱 builtin 仍在運作」的那一句;
這批的判準更嚴:**用過去式提到它也一樣有害**——模型讀到會去推敲一個不存在的
模式,人讀到會以為支援等級還有第三種。出貨端:`page_map.md`(表頭、
cover/agenda/closing 三列備註、整節「builtin 清零紀錄」)與 `bindings.json`
四段 `_note`;tools.zip 端:`pack_loader` 檔頭與 PackError 訊息、`pptx_toolkit`
的常數註解。repo 端:ARCHITECTURE 三處(「沒有 builtin 這個模式」改寫為「引擎
沒有從零繪製版面這條路」)、WORKLOG §5.3 那條**已被推翻卻還寫成現行規則**的
「新模板不得有 builtin」加刪除線與指路、INDEX 備註欄、light REGRESSION R-L0
註記、`regress.py` 與 `prepare_env.py` 註解。
**留下的界線:現況文字零 builtin,歷史紀錄(WORKLOG §10.5/§10.6、本檔)照原樣
保留**——那裡才是「為什麼沒有 builtin」的答案,刪了等於刪掉推翻先例的證據。
另刻意保留 `template_admin` 的 `mode == "builtin"` 指路 hint(只在有人真的寫了
builtin 時觸發,那正是最需要它的時刻)與 pack 裡「刪檔漏四份」的事故註解。
`page_map.md` 刪掉的遷移表在 WORKLOG §10.5;兩條仍有效的版位限制(cover 副標
5 字、agenda 單一文字框)改寫成現況說明續留檔內。**兩個 zip 都改 sha,產檔行為
零變化**(異動全是註記與文件字串,上方基準區塊已同步);
light@2026-07-27.3 → .4、instructions v2.5 → v2.6-20260727。
同批修掉 DEPLOY.md/gpts README 三處寫死的舊版本代號(`v2.3-20260727`、
`light@2026-07-27.1`)——那是驗收步驟自己的預期值,過期後會讓人誤判發版失敗;
改成指向 `instructions.md` 第一行,不再複製數字。)

(2026-07-27 量測說謊修復,**兩個 zip 都改 sha**:`text_tools._first_run_size_pt`
在 run 沒寫字級時直接回退 `DEFAULT_FONT_PT`(18pt),但 placeholder 的真值寫在
layout/master 的 `<a:lstStyle><a:lvlNpPr><a:defRPr sz=…>`——**全模板 218 個文字框
都靠繼承取字級**,一律被當成 18pt。症狀:封面主標(4.21 吋框、真值 40pt)填 8 個字,
估算器以為佔 2.0 吋(實際 4.44 吋)判「裝得下」,fit 不收緊、qa 不報警,
PowerPoint 一開檔主標就折兩行壓到副標與日期列。**這是實跑產檔時目檢抓到的,
所有機器檢查全綠。** 同批修 `fit_capacity` 偵測端的陷阱 11:`wrap="none"` 單行框
在 suspect 迴圈被 `lines<=1` 提前 continue,橫向檢查只在 `_clean_cap` 內部,
於是那種框「連候選都選不進來」——KPI 大數字框(1.43 吋 @66pt)填「48 小時」
右邊爆出 0.96 吋而 fit 印收斂,因為它沒撞到任何有文字的鄰居。
重量測後 light 新增 5 條 override:`cover.main_title` 20→**7**、
`data_three_number_kpis.value`→**2**(模板原文就是「04」「25」兩位數)、
同頁 `label`→6、`stage_timeline_progress.axis_labels`→**2**、
`data_line_trend_comparison.series.name`→3。light@2026-07-27.2 → .3、
instructions v2.4 → v2.5-20260727。)

(2026-07-27 fit 盲點修復後重量測:agenda/cover 的 4 條**手寫**容量換成工具
量測值(subtitle 28→30、date 12→13、presenters 20→15、cover.subtitle 5 不變),
自此全部 49 條 overrides 皆 `fit` 產出,`--reset` 保護完整——2026-07-26 註記
的「agenda 容量不受 --reset 保護」例外已消除。**template_light.zip 改 sha**
(manifest 容量 + version 2026-07-27.1 → .2);tools.zip 未動。instructions
v2.3 → v2.4-20260727(同日 validator 加容量壓縮豁免,該散檔要刪舊傳新)。)

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
`docs/WORKLOG.md` §10.5 的遷移表(當時放在 `page_map.md`,2026-07-27 隨
出貨包文字清理移走)。)

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
src = json.load(open('engine/templates/light/manifest.json', encoding='utf-8'))
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
(Phase 4 加 chart 頁型時就漏過這步,靠稽核才發現;R11 就是為了不再靠人記得。
2026-07-27 起 `--regen-specs` 會**刪除**契約集合外的過期 fixture——以前只寫
不刪,頁型移除後殭屍檔內容沒變,本案例的 diff 檢查永遠查不出來,builtin
清零那批就漏了四份靠人工 git rm。)

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
m = json.load(open('engine/templates/light/manifest.json', encoding='utf-8'))
fills = list(json.load(open('engine/templates/light/bindings.json', encoding='utf-8'))["fills"])
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

## R14|大綱契約先行選版正反向測試

本案例驗五個不變式：候選來源逐字、選定模板 merged 容量先驗、語意同等候選
全局降低重複、選定 counts 直接形成骨架清單數量、**整庫覆蓋審視**(2026-07-31
起:plan v2 頂層 `not_nominated` 必須讓「提名 ∪ 有理由的未提名」涵蓋全部
非結構全自動頁型,擋「只提名最熟兩型」的候選池窄化)。fixture:
`engine/examples/06_page_type_candidates.json` 搭配未切頁原文 05。

```bash
python3 "$RT/tools/make_skeleton.py" \
  --plan engine/examples/06_page_type_candidates.json \
  --source engine/examples/05_outline_to_ppt_source.md \
  --selected-plan-out "$RT/page_type_plan.json" \
  --slides-out "$RT/slides_plan.md" \
  --out "$RT/spec_plan.json"
```

預期 exit=0,序列為
`cover → info_horizontal_explanation_rows → info_three_column_category → closing`
(同分決勝是**來源片段 hash**,不是候選列出順序——否則每份 deck 都收斂到
模型慣性排第一的頁型;零隨機,同輸入必同輸出),輸出 `相鄰重複:0` 與
`單一候選內容頁:0`;selected plan 含 `library_review`(nominated 兩個 info 型
+ not_nominated 展開理由);spec 的橫列數為 4、三欄 points 數為 2/2/2,
`slides.md` 逐字來自 source_excerpt 且 closing 固定 `Thank you`。

runner 另驗「語意優先」：前一頁只有三欄 exact、下一頁三欄 exact/橫列 acceptable
時,即使會相鄰重複也必須選三欄,證明多樣性不能越權蓋過 fit。

反向測試兩條:①把第二頁兩個候選分別改成 columns=2、rows=3(都低於契約下限);
預期 exit=1 且輸出 `沒有任何契約可行的全自動候選`。這證明不能用
「待補充」虛增系統自行選型的結構數量,也不會先產一份資料與版型不合的骨架。
②刪掉 fixture 的 `info_*` 未提名理由;預期 exit=1 且 `整庫覆蓋審視不完整`
逐一列出缺漏頁型(含結構包絡)——候選廣度是工具稽核的不變式,不靠模型自律。
另:內容頁過半只提名單一候選時工具印 `[W] 候選池過窄`(WARN 不擋;理由與
廣度統計寫進 selected plan 供設計師稽核)。

## R15|enrich-outline 豐富鏈稽核正反向測試

`/enrich-outline` 把「使用者核准的增補」變成新的內容來源;本案例驗豐富鏈的
三個工具強制不變式(增補品質本身是人審,不在此測):

1. **未標記行 ⊆ 原稿**:核准版大綱(`--source`)裡凡不是行首 `[補]` 標記的行,
   必須逐字出現在 `--original` 原稿——沒標記的改寫/新增在稽核階段被擋,
   豐富流程洗不掉「原文逐字」防線。
2. **標記存在必有鏈**:來源含 `[補]` 卻沒帶 `--original` 一律 FAIL,
   不得移除標記繞過。
3. **管線透傳**:`run_pipeline.py --original` 傳進稽核階段;鏈不完整停在
   階段 1,鏈完整 `--validate-only` 走到 PASS。

runner 以 02 fixture 為原稿,附加三行 `[補]` 增補(一行含數字、一行含
「待補充」)作核准版;正向預期 exit=0 且報告印
`豐富鏈:開(增補 3 行,其中含數字 1 行)`(增補統計是給設計師稽核 `[補]`
行的入口——標記行內容是否真來自使用者回覆,工具驗不了,所以要讓它顯眼)。
反向:①附加一行未標記的非原文行 → exit=1
`未標記 [補] 也不是原稿逐字行`;②同輸入不帶 `--original` → exit=1
`未帶 --original`;③管線同組輸入缺 `--original` 停在稽核、補上後
`--validate-only` PASS(2/2 階段)。

## R16|instructions 版本 roster 同步

```bash
python3 engine/release/regress.py --only R16
```

預期:`gpts/instructions.md` 含每個 registered 模板包的
`<template_id>@<version>`(讀各包 manifest 現值)。這是發佈鏈唯一的
手抄版本字串;pack 完成後忘了連動 instructions,這關就紅。
