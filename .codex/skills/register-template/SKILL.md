---
name: register-template
description: 設計師提供新的 .pptx 簡報模板、要求「註冊新模板/新增模板/讓產生器支援這個模板」時使用。引導式完成:盤點→頁型映射(設計師確認)→填充綁定→黃金驗收(設計師目檢)→正式註冊+回歸。Triggers:「我有一個新模板」「註冊這個 pptx」「新增一套版型」「register template」。
---

# register-template(新模板註冊精靈)

> **狀態:已啟用(2026-07-25,Phase 2 落地)。** 架構與工具鏈規格見
> `docs/ARCHITECTURE.md`;工具鏈 = `engine/release/template_admin.py`
> (new/freeze/lint/golden/register/pack/isolation/list)+
> `engine/tools/fills_engine.py`(op 解譯器;詞彙表版本與可用修飾詞見該檔檔頭的
> 紀事,目前 v1.2)。light 最早的五種 fill 頁型的宣告式重寫已通過 shape 樹全等
> 驗證(含 min 刪格與 max 溢出路徑);light 當下的 fill 全集跑 `make_skeleton.py --list`。
> 帶 pptx 操作的子命令(new/freeze/golden/register)依 prepare_env
> 提示加渲染前綴(如 `uv run --with python-pptx python`)。

這是 `cub-deck-builder` repo 多模板架構的註冊前端:所有機械動作由 repo 腳本完成,
你只負責五件事——**盤點轉述、提映射草案、依確認寫 bindings.json、
跑驗收指令並如實轉述、把設計師的目檢意見翻成綁定修正**。版面與規則你零創作。

使用者是**設計師**(半技術/非技術,語氣沿用 `docs/給設計師/` 的文件)。
她只做三件事:丟一個新 .pptx 並取名;用嘴確認「這頁是三欄說明」;
打開你產的驗收 pptx 說哪頁不對。**shape id、slot 名、JSON、op 細節
絕不拋給設計師。**

規則本體的單一真相來源(相對 repo 根;本檔只留摘要,不複製規則):

- `docs/ARCHITECTURE.md` — 模板包結構、manifest 欄位、op 詞彙表、驗收與發佈規則
- `engine/rules/validate_slide_spec_gpts.py` `PAGE_TYPES` — fill 級頁型候選集
- `engine/rules/page_types.md` — clone 級頁型候選集(語意分類與容量)
- `engine/tools/README_TOOLS.md` — 工具鐵律與錯誤修法慣例

## 鐵律(違反任一條即整段作廢)

1. **零發明**:頁型候選只能來自 validator `PAGE_TYPES`(fill 級)與
   `page_types.md`(clone 級)。比對不到就回報「無對應,建議跳過或降級」,
   禁止發明新頁型名;`PAGE_TYPES`/schema/registry/page_types.md/golden fixtures
   /qa 規則/引擎程式碼對本 skill **全部唯讀**。需要動它們 = 停止並回報,
   那是工程師的契約同步流程,不在本 skill 內。
2. **零隨機、零自由 Python**:shape id 與座標唯一來源 = `inspect_template.py`
   輸出;綁定只能用 7 個填充 op(set/delete/rows/list/add_textbox/resize/
   chart)加 `keep` 覆蓋宣告,詞彙表與全覆蓋原則見 docs/ARCHITECTURE.md §5。
   表達不了 → 該頁型降級 clone,不是變通、不寫 Python、不擴詞彙表。
3. **golden 才算數**:任何 bindings/manifest 改動,必須重跑
   `template_admin.py golden` 綠了才能宣稱完成。「看起來應該對了」不是完成;
   唯一完成證據 = golden PASS 行 + 設計師目檢點頭,缺一不可。
4. **裝不下就降級**:golden max 變體溢出修不掉 = 該模板該頁裝不下契約容量 →
   降級 clone 或 unsupported。禁止為單一模板改共用契約字數
   (容量覆寫只能寫本包 manifest 的 `capacity_overrides`,且不得增刪槽位)。
5. **不改產出**:驗收 pptx 不對 → 只改 bindings/manifest 重跑;
   禁止手改 pptx、禁止改 golden fixtures。
6. **回歸紅 = 不准註冊**:`template_admin.py register` 內含 light 回歸與
   隔離檢查;它不綠,新模板再漂亮也不發。本 skill 全程不得觸碰
   `templates/<其他 id>/` 與任何共用檔(isolation 白名單機器驗證)。
7. **提問配額**:只有三類問題可以問設計師——(a) 映射確認/修正
   (b) 目檢結果 (c) 降級/中止決策。技術細節不問;除高信心批次確認外,
   一次訊息不超過一個決策點。
8. **含 chart 的模板頁要 fill 就必須每個圖表綁 `chart` op**(lint 硬擋未
   覆蓋者;spec 的 values 是純數字字串、數量須等於 categories),做不到就
   降級 clone;SmartArt 頁一律 unsupported——固定規則,不得詢問、不得繞過。

## 跨平台約定

同 outline-to-ppt:命令全部單行、相對路徑、正斜線,bash/PowerShell/cmd
原樣可跑(**禁 `&&` 串接與反斜線續行**:PowerShell 5.1 不支援 `&&`,
續行三種 shell 都會壞)。兩個代換:

1. **直譯器名稱**:macOS/Linux 用 `python3`(mac 的 `python` 常只是 shell
   alias,在腳本裡叫不到);Windows 用 `python`。
2. **pptx 前綴**:碰 PowerPoint 檔的子命令(`new`/`freeze`/`golden`/`register`,
   以及 inspect_template / render_deck / qa_check / wireframe_preview)要加
   `uv run --with python-pptx python`(wireframe_preview 另需 `--with pillow`);
   `lint`/`list`/`pack`/`isolation` 純標準庫,直接 `python3` 即可。
   本機該用哪個,以 prepare_env 印出的「渲染指令前綴」那行為準。

路徑含空格一律用**雙引號**(cmd.exe 不認單引號);zip 一律 Python zipfile
(POSIX 路徑),禁 `Compress-Archive`/檔案總管。

## 步驟 0:環境準備(每次 session 先跑)

```
python .codex/skills/outline-to-ppt/prepare_env.py
```

用途:環境自證(python-pptx 可用性、渲染指令前綴)與建立 `ppt_out/`
(golden 產出的落點)。**註冊流程本身直接操作 repo 端 `engine/templates/`
與 `engine/tools/`,不經 ppt_out 沙箱副本**(沙箱是 outline-to-ppt 產檔用的)。
exit 0 才算就緒,未跑前不得對可行性下任何結論。
若 `engine/templates/<id>/registration_state.json` 已存在 → 問設計師:
「上次『<display_name>』註冊到一半(映射已確認 N/M 頁),要接續還是重來?」

## 步驟 1:收件建檔

問齊三樣(一次問完,唯一的表單式提問):模板檔路徑、中文名稱、英文代號。
順帶說明:**fill 頁用的是模板自己的版面,背景已在頁裡,不需要另交素材**;
只有設計師想支援 clone 參考頁專用背景或 logo 檔時才收(選配,放進包內
`assets/` 並記入 manifest `asset_defaults`)。

```
uv run --with python-pptx python engine/release/template_admin.py new --pptx "<設計師給的路徑>" --id corp_dark --name 企業深色風
```

(路徑一律用雙引號包住——檔名含空格時不加引號會噴
`unrecognized arguments`,訊息看不出是空格造成的。)

## 步驟 2:盤點與體檢報告

```
uv run --with python-pptx python engine/release/template_admin.py freeze --id corp_dark
uv run --with python-pptx python engine/tools/inspect_template.py --pptx engine/templates/corp_dark/template.pptx --summary
```

把摘要翻成設計師語言的體檢報告(不貼原始輸出),例:
「共 42 頁。可自動化候選 31 頁;6 頁含 SmartArt(程式動不了,只能跳過,
或請你在 PowerPoint 對它按右鍵→轉換成圖形後重傳);2 頁含圖表(可全自動,
圖表數據會由程式替換;數據格式=時間點+1-2 組數列);3 頁純裝飾章節頁
(建議跳過)。」
品質閘門:SmartArt/圖表頁占內容頁過半 → 走降級章的「模板品質不佳」路徑。

## 步驟 3:映射提案與確認(唯一的多輪問答環節)

逐候選頁跑 `inspect_template.py --page N`,以「形狀結構 vs 契約槽位」比對出
候選頁型與信心。提問節奏(寫死):

a. 先一次貼出【高信心批次表】(模板頁碼|頁型中文名|一句視覺理由),
   問一句:「這批我打算照表登記,要改的直接說頁碼,沒有請回 OK。」
b. 中低信心頁逐頁問,一次一頁,至多 3 個候選 +「跳過」:
   「第 18 頁:左邊一個大圓、右邊 4 個小標籤——比較像『願景目標(中心平衡)』
   還是『核心與支援』?不確定可以開 pptx 看一眼,或回『跳過』。」
c. 全部確認後貼【最終映射總表】總確認一次,寫入 registration_state.json。

每頁結局三選一:fill 頁型 / 降級 clone / 跳過(unsupported,記 reason)。
同一頁型有多個候選模板頁時,請設計師選一頁做 fill,其餘登記 clone。

## 步驟 4:綁定草稿(全自動,不問設計師)

對每個 fill 頁型:依 inventory 快照寫 `bindings.json` 條目。硬規則:
**全覆蓋原則**——模板頁上所有含文字的 shape 必須被 set/rows/list/delete/keep
之一覆蓋(lint 會硬擋);每個必填槽位必有 set/rows/list 綁定;契約沒有的
內容性元素(分數籤、縮圖、範例數字、子導覽)必須 delete,留著=捏造;
**不含數字的固定結構字樣**(欄目標籤、「目錄」之類的章節字)用 keep 明示
保留並附 reason——刪了版面語意會殘缺,但任何可能被誤讀為內容事實的字樣
不得 keep;清單槽位必配 underflow 刪除與 overflow 策略;
模板頁碼框不在 manifest 宣告的清除窗內 → 加 delete。
同步填 manifest:`page_types` 支援矩陣、`asset_defaults`、`style.allowed_fonts`
(模板正式字型)、`page_number` 幾何(從 inventory 座標推,轉述給設計師確認
頁碼位置即可,不問數字)。

## 步驟 5:黃金驗收(迭代到綠)

```
python engine/release/template_admin.py lint --id corp_dark
uv run --with python-pptx python engine/release/template_admin.py golden --id corp_dark
```

(lint 純標準庫、不需前綴;golden 會 subprocess 起 render/qa,**前綴要加在最外層**。)

FAIL → 對照下方錯誤表修 bindings → 重跑;迭代單一頁型可加
`--page-types a,b` 省時,收尾必跑一次全量。可選配產線框示意輔助自查
(`uv run --with python-pptx --with pillow python engine/release/wireframe_preview.py --pptx ppt_out/golden_corp_dark.pptx --out ppt_out/wf`),
但交付目檢仍以 PowerPoint 開檔為準。全綠後交設計師目檢:
「驗收檔在 `ppt_out/golden_corp_dark.pptx`,每種頁型兩頁:第一頁塞最少內容
(看有沒有殘留空框),第二頁塞最滿內容(看有沒有爆框)。用 PowerPoint 開,
把不對的頁碼告訴我。」設計師回報 → 翻成綁定修正 → 重跑 golden → 再目檢,
直到點頭。修正循環最多三輪/頁型;三輪修不掉 → 提議降級 clone。

## 錯誤→修法對照表(註冊情境,唯一修法)

| 錯誤特徵 | 唯一修法 |
| --- | --- |
| FillError: shape id X 不存在 | 重跑 inspect --page N 核對(多半頁碼填錯或 id 抄錯),改 bindings |
| lint: sha 不符 | 模板檔被換過 → 重跑 freeze 再 lint(盤點未完成前禁止其他步驟) |
| lint: 圖表未被 chart op 覆蓋 / SmartArt 頁 | 補 chart op(id=圖表 shape);補不了或 SmartArt → 該頁改 clone/unsupported |
| chart op: 系列值數 ≠ 時間點數 | 修 spec/golden 派生無此問題;實際內容缺值 → 該格「待補充」不適用於數值,改少列時間點 |
| qa: 內容未出現「…」 | 該槽位沒綁或綁錯框 → 補/改 set;禁止改 golden |
| qa: 溢出疑慮(max 變體) | ①rows 補 overflow=merge_last ②確認 shrink 生效 ③仍爆=裝不下 → 降級 clone |
| min 變體目檢見空框/斷頭分隔線 | list/rows 的 delete_on_missing / sep_ids 沒配齊 → 補 ids |
| qa: 不該有頁碼卻有數字框 | 模板頁碼位置特殊 → manifest page_number 窗修正或 bindings 加 delete |
| qa: 字體 WARN | 模板正式字型 → 加 manifest allowed_fonts;雜字體 → 回報設計師清模板 |
| 驗收頁圖片破圖 | clone 工具層問題 → 停止並回報維護者(不是綁定問題) |
| 同頁型三輪仍紅 | 停止硬修,向設計師提議降級 clone 或跳過,記 reason |
| register: light 回歸紅 / isolation 越界 | 不准註冊;多半是共用檔被動到 → 回報維護者,本次註冊掛起 |

## 步驟 6:正式註冊 + 發佈提醒

```
uv run --with python-pptx python engine/release/template_admin.py register --id corp_dark
```

成功輸出 = status 翻 registered + 支援矩陣摘要。之後如實轉述腳本印出的
發佈清單(打包 `template_admin.py pack`、instructions 版本字串與 roster、
Builder 刪舊傳新、light 抽測——詳見 docs/MAINTENANCE.md 發佈 checklist;
Builder 上傳是維護者人工步驟,不在本 skill 內代行)。
最後給設計師白話交付摘要:
「『企業深色風』註冊完成:全自動 9 種、半自動 14 種、不支援 3 種(原因:…)。
之後產檔時說『用企業深色風』即可(outline-to-ppt 的模板指定與本 skill
同 Phase 上線;若尚未上線,先用直供 JSON 模式加 `--template-pack corp_dark`
產檔)。」

## 降級與中止路徑

- 單頁降級隨時可做:clone(仍可用,產檔走複製改字)或 unsupported(記 reason)。
- **部分註冊是合法結局**:支援矩陣就是為部分支援設計的,不逼全頁型全綠。
- 中途放棄:進度在 registration_state.json,直接說「先到這裡」,下次觸發
  自動偵測續作;draft 狀態的模板不會被任何產檔流程選中。
- 模板品質不佳(SmartArt 過半/群組混亂/字體雜):不硬做。給設計師修模板 SOP
  (SmartArt 右鍵→轉換成圖形、統一字體後重存,回步驟 2 重跑);
  不想修 → 只註冊乾淨的頁,其餘 unsupported。
- FillError 以外的工具層異常(clone 破圖、qa 誤報)→ 停止回報維護者,不得繞過。
