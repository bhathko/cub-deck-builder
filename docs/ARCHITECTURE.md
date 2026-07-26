# ARCHITECTURE — 現行架構

> **用途**:這套系統**現在**長什麼樣——目錄怎麼分、產檔怎麼跑、模板包怎麼組成、
> 綁定怎麼寫、驗收怎麼把關。**只描述現況,不含設計辯論與演進史**
> (那些在 [`WORKLOG.md`](WORKLOG.md))。
> **讀者**:要改引擎、加模板、或想快速看懂全貌的人。
> **何時讀**:動 `engine/` 之前;接手時想一次搞懂結構。
> 日常操作步驟見 [`MAINTENANCE.md`](MAINTENANCE.md);硬規則以
> [`../AGENTS.md`](../AGENTS.md) 為準。

## 1. 一句話與三層結構

把「slide_spec.json(或一段大綱)→ 公司規範的 16:9 繁中可編輯簡報」做成
**單引擎**,以兩個前端交付。**版面零隨機**:同一份輸入跑一萬次結果相同。

```
engine/     主程序——產 pptx 的一切
  rules/       共用語意契約(驗證器 PAGE_TYPES、schema、頁型語意庫、排版紀律)
  tools/       引擎腳本 ×11(渲染、驗證、自檢、盤點;打包成 tools.zip 出貨)
  templates/   模板包(一模板一目錄;light 為第一個包)
  golden/      契約快照(全頁型 × min/max;非實跑素材,見 §7.1)
  release/     維護者工具(template_admin.py 註冊工具鏈、fit_capacity.py 容量量測、wireframe_preview.py)
  examples/    試用範例與 fixture
gpts/       前端 1:ChatGPT GPTs(instructions + dist/ 上傳 zips + 建置手冊)
.codex/skills/  前端 2:本機 CLI(outline-to-ppt 產檔、register-template 註冊新模板、add-page-types 加開頁型)
docs/       文件
```

**兩個前端共用同一個引擎**,規則不複製:skill 只內聯環境差異
(沙箱佈局、指令前綴),規則本體一律指回 `engine/rules/` 與 `engine/tools/`。

## 2. 產檔管線(單一入口)

```
slide_spec.json ──► audit_provenance ──► validator ──► render_deck ──► qa_check ──► deck.pptx
   (或大綱)          內容忠實稽核       產檔前閘門     確定性渲染      產檔後自檢
```

由 `engine/tools/run_pipeline.py` 一條指令跑完,**任一階段非 0 即停**,
不產半成品;整條冪等,重跑即重生。

三個設計支點:

- **修計畫,不修產出**:每次從模板整檔重生。結果不對就改輸入(spec 或
  render_plan)再跑,禁止對產出 pptx 局部修補。
- **兩道程式閘門**:產檔前驗規格(槽位、字數、頁碼、素材),產檔後驗結果
  (內容覆蓋、頁數、Section、字體、溢出)。任一沒過不得交付。
- **內容忠實**:大綱模式下,標題必須逐字取自來源、數字必須在原文出現過;
  缺料填「待補充」,絕不捏造。

## 3. 頁型的兩級與模板的三級

**語意層(跨模板共用)**:`engine/rules/validate_slide_spec_gpts.py` 的
`PAGE_TYPES` 定義每種頁型的槽位契約(名稱、巢狀、數量、字數、頁碼規則)。
註冊頁型的當下全集跑 `make_skeleton.py --list`(刻意不在文件寫死數量);
另有 `page_types.md` 的語意頁型只做基本檢查。

**模板層(每包各自)**:每個模板包宣告自己對每種頁型的支援等級——

| 等級 | 意思 | 產檔行為 |
| --- | --- | --- |
| `fill` | 全自動 | clone 模板實頁 + 依 `bindings.json` 填字 |
| `clone` | 半自動 | 走 render_plan(AI 寫一張「哪個框換什麼字」的小抄) |
| `unsupported` | 不支援 | validator 硬擋,附原因 |

**部分支援是合法結局**——新模板不必支援全部頁型。

## 4. 模板包


```
engine/templates/<template_id>/        ← 一模板一目錄,id 格式 ^[a-z][a-z0-9_]{2,31}$
  template.pptx                      ← 模板本體(檔名固定,身分由目錄名決定)
  manifest.json                      ← 機器可讀真相來源(§2)
  bindings.json                      ← 填充綁定(宣告式 op,§3;唯一形式,不得改用 .py)
  page_map.md                        ← 人類可讀:語意頁型→模板頁+支援等級(含 unsupported 明列)
  inventory.json                     ← freeze 產物:綁定頁 shape 樹快照 + pptx sha256
  assets/                            ← backgrounds/*.png、logos/*.png(隨包出貨;fill 頁通常不需要,見 §2)
  assets_src/                        ← 可編輯素材源檔(不入 zip)
  examples/smoke_spec.json           ← 至少一份保證 PASS 的 spec(不入 zip)
  REGRESSION.md / FEEDBACK.md        ← 每模板回歸與回饋台帳(不入 zip)
  registration_state.json            ← 註冊進度存檔(僅 draft 期存在,支援中斷續作)
```

- **light 是第一個包**:`engine/templates/light/`,`light_template.pptx` 與
  `assets.zip` 內容併入包內。它曾有一支 builders-only 的 `bindings.py`
  (grandfather),2026-07-26 builtin 清零後整檔刪除——light 現在是純
  `bindings.json`,與新註冊的包同構,不再有任何專屬例外。
- **沒有 builtin 這個模式**:cover/agenda/closing 這類「版面內建」頁型一律要求
  模板 pptx 內含對應頁,以 fill 模式綁定(設計師在 PowerPoint 改版面,
  不在 Python 調座標);模板缺頁 → 該頁型 unsupported。引擎已無從零繪製的路徑,
  包內出現 `bindings.py` 由 `pack_loader` 與 `lint` 兩處硬擋。
- **新模板的 fill 頁預設免素材**:fill 模式是 clone 模板實頁,背景/logo 已
  烙在頁面裡,不需要 spec 提供 assets(已廢除的 builtin 工法是「空白頁+貼背景圖
  +貼 logo」,才需要 spec 交素材——這是兩種工法的本質差異)。素材檔只在 clone
  參考頁需求或未來照片頁型時才進包。
```json
{
  "template_id": "corp_dark",
  "display_name": "企業深色風",
  "version": "2026-08-01.1",
  "status": "draft",
  "template_file": "template.pptx",
  "template_sha256": "…",
  "page_count": 42,
  "aspect": "16:9",
  "language": "zh-TW",
  "style": {
    "font_zh": "Noto Sans TC", "font_en": "Helvetica",
    "allowed_fonts": ["Noto Sans TC", "Helvetica"],
    "colors": {"dark": "1A2233", "muted": "8892A6", "accent": "F2C94C", "line": "2E3A52"}
  },
  "asset_defaults": {
    "background_cover": "assets/backgrounds/cover_bg.png",
    "background_content": "assets/backgrounds/content_bg.png",
    "logo": "assets/logos/corp_logo.png"
  },
  "page_number": {
    "box_in": [12.30, 6.72, 0.70, 0.50], "size_pt": 28, "color": "1A2233",
    "clear_zone_in": {"left": 11.2, "top": 6.3},
    "detect_zone_in": {"left": 11.0, "top": 6.3}
  },
  "page_types": {
    "cover":                       {"mode": "fill", "template_page": 1, "assets": [], "status": "golden_green"},
    "info_three_column_category":  {"mode": "fill", "template_page": 5, "assets": [], "status": "golden_green"},
    "cycle_four_point_loop":       {"mode": "clone", "template_page": 12},
    "pyramid_layered_maturity_detail": {"mode": "unsupported", "reason": "SmartArt,程式無法填字"}
  },
  "capacity_overrides": {
    "info_three_column_category.slots.columns.item.points.max": 5,
    "vision_goal_center_balance.slots.core_mission.max_chars": 80
  },
  "registered_by": "設計師名", "registered_at": "2026-08-01",
  "golden": {"last_pass": "2026-08-01T10:12:00+08:00"}
}
```

要點:

- **支援矩陣三級**(設計師語言:全自動/半自動/不支援):
  `fill` = 有綁定、過黃金驗收,產檔全自動;`clone` = 只有頁碼映射,產檔走
  render_plan 複製改字(= 現行 page_types.md 未註冊頁型的體驗,也是綁定失敗的
  **內建降級層**);`unsupported` = validator 硬擋(附 reason)。
  部分支援是合法結局,不逼全頁型全綠。
- **per-頁型素材鍵覆寫**:語意契約的 assets 必要鍵(background/logo)降為
  **預設值**;包內 `page_types.<pt>.assets` 可覆寫必要鍵集(新包 fill 頁
  一律 `[]` = 免素材,§1)。validator 取「包覆寫,無則契約預設」;
  素材存在性檢查經 validator 的 `asset_exists`(同序:pack_first)。light 包不覆寫,
  行為同現行。
- **主題與幾何收編**:`style.allowed_fonts` 取代 qa_check 寫死的 ALLOWED_FONTS;
  `asset_defaults` 取代 make_skeleton 寫死的 BG/LOGO(**映射慣例明訂**:
  cover/closing → `background_cover`,其餘 → `background_content`,
  與現行 make_skeleton `BG`/`DEFAULT_BG` 完全一致,light 零行為變);
  `page_number` 取代 render_deck 頁碼框/清除窗與 qa_check 偵測窗
  (clear/detect 兩鍵分列,精確保存現行 11.2/11.0 的不一致行為,不趁改制偷改)。
- **capacity_overrides**:扁平 dot-path,終端鍵白名單 `{min, max, max_chars}`,
  值必為正整數且 min≤max。**不得增刪槽位、不得改 kind/required/provenance**
  ——merge 函式硬性拒絕,違者 exit 2(設定檔錯誤,非 spec 錯誤)。
  語意契約(validator `PAGE_TYPES`)現值兼作預設容量;merge 實作放 validator
  檔內(stdlib,約 40 行)維持單檔可攜,工具層循 make_skeleton 慣例 import 取用。
- **`template_sha256` + `inventory.json`**:把「模板改版必重盤點」(WORKLOG §9)
  從人工紀律變成機器強制——載入時驗雜湊,不符 exit 2 並指示重跑 freeze;
  多數 FillError 因此提前到載入期。(現行行為:sha 不符時**印警告不硬擋**——硬擋會堵死「拿新版模板檔試跑」
  的工作流;正式發版前必須照 `TEMPLATE_LIFECYCLE.md` 重跑 `freeze`。)

## 5. 綁定:bindings.json 與 op 詞彙表

填充綁定是**宣告式 JSON**(`bindings.json`),由 `engine/tools/fills_engine.py`
逐 op 執行;註冊時 AI 只產 JSON、不產 Python。**op 詞彙表固定**——目前
7 個填充 op(含 chart)加 `keep` 覆蓋宣告,下表形式欄位為節錄,
完整欄位以 bindings schema 為準:

| op | 用途 | 形式(關鍵欄位) |
| --- | --- | --- |
| `set` | `ctx.set(51, title)`;KPI `f'{label} {value}'`;pros `"\n".join`;金字塔帶標籤 ≤6 字才填否則刪框 | `{"op":"set","slot":"$.title","id":51}`;修飾詞 `"template":"{label} {value}"`、`"join":"\n"`、`"max_len_or_delete":6` |
| `delete` | p17 刪直排/標籤/子導覽;p29 單位框、p33 分數籤/縮圖一律刪(契約無此欄位,留著=捏造) | `{"op":"delete","ids":[7,28,29]}` |
| `keep` | (新增,見表後註「全覆蓋原則」)模板頁上的結構性字樣明示保留 | `{"op":"keep","ids":[17],"reason":"欄目標籤『目錄』,固定結構字樣"}` |
| `rows` | `_fill_rows`:固定列+分隔線,不足刪列刪線、溢出併入最後一列並加高 | `{"op":"rows","slot":"$.slots.before.points","row_ids":[21,22,23],"sep_ids":[24,47],"overflow":"merge_last","merge_height_in":0.80}` |
| `list` | p14 (文字框,底圖) 成對刪;p33 每方案成組刪;p54 四層時**從頂端刪**(尾端對齊);p17 rest 溢出併入最後一組的 desc 框 | `{"op":"list","slot":"$.slots.options","align":"head 或 tail","items":[{"sets":[{"slot":"@.name","id":9}],"delete_always":[3,7],"delete_on_missing":[12,29,64]}],"overflow":{"merge_into_id":50,"join":"\n"}}`(`@`=清單元素相對路徑;slot 支援切片如 `points[2:]`;`overflow.merge_into_id` 指定的框在無溢出時刪除) |
| `add_textbox` | p54 無副標佔位→動態補建;p33 建議列(recommended+recommendation 串接、前綴「建議:」、皆空不建框) | `{"op":"add_textbox","slots":["$.slots.recommended","$.slots.recommendation"],"prefix":"建議:","join":"、","skip_if_empty":true,"x":0.85,"y":6.42,"w":11.8,"h":0.36,"pt":14,"bold":true}`(字型取 manifest `style.font_zh`) |
| `resize` | p14 中心圓文字框加高讓長句留在圓內 | `{"op":"resize","id":37,"top":3.25,"height":1.00}` |

(`keep` 不算填充 op,是覆蓋宣告;填充 op 計數 v1.0=6、v1.1=7(+chart);
v1.2 沒有加 op,加的是 `set` 的 `item_template` 修飾詞。詞彙表紀事以
`fills_engine.py` 檔頭為準。)

三個配套原則:

- **全覆蓋原則**:每個 fill 頁的綁定,模板頁上**所有含文字的 shape** 必須被
  set/rows/list/delete/keep 之一覆蓋,lint 硬檢查。`keep` 僅限不含數字、
  非內容語意的固定結構字樣(欄目標籤、章節字、「目錄」之類——已廢除的 builtin
  是由程式主動畫上 Contents/背景/預期成果這類字,改 fill 後它們烙在模板頁上,
  刪了版面語意反而殘缺);qa/audit 不追溯 keep 字樣。判準:含任何數字或
  可能被誤讀為內容事實的字樣不得 keep,只能 delete。
- **表達力的驗證方式**:light 最早的 5 種 fill 頁型有一份等價的宣告式重寫,
  與原 Python 實作產出的 shape 樹**全等**(含最少/最滿兩種變體),
  這是詞彙表夠用的實證。個別頁型若真的表達不了,該頁型降級 clone,
  並把缺口記錄下來供未來評估擴 op。

- **鐵則:表達不了 = 降級 clone,絕不在註冊對話中擴詞彙表、絕不讓 LLM
  現寫 Python。** 詞彙表擴充是「引擎版本事件」:由工程師加 op、補 schema、
  對全部已註冊包跑回歸。

先例佐證:validator 的槽位文法(kind/min/max 遞迴結構)本來就是
「宣告式迷你語言 + 解譯器」,fills_engine 與其架構對稱,不是新發明。

新增引擎件(`engine/tools/`,隨 tools.zip 出貨):

- `fill_helpers.py`:自 fills.py 抽出 `FillError`/`index_shapes`/`Ctx`/
  `_fill_rows`(公開化為 `fill_rows`),並把 p33/p54 兩處**內聯** add_textbox
  樣板整併為新 helper `add_styled_textbox`(供 fills_engine 的
  `add_textbox` op 使用)。
- `fills_engine.py`:bindings.json 解譯器(op 執行器 + bindings schema 驗證;
  op 依序執行、`shrink_to_fit` 收尾 min 12pt 同現行、shape id 不存在即
  FillError,訊息格式同現行並加註包 id/version)。
- `pack_loader.py`:`load_pack(cli_arg, spec_deck, packs_root, asset_dir) -> Pack`,
  提供 `.manifest .template_path(驗雜湊) .fills .merged_page_types
  .style .asset_defaults`;素材解析(validator `asset_exists`):**light 包 = asset_dir
  優先、包目錄兜底(舊 spec 的 `assets/...` 路徑不變);非 light 包 =
  包目錄優先、asset_dir 兜底**(防跨包遮蔽:本機沙箱 asset_dir 永遠有
  light 的 assets/,若 asset_dir 優先,新包素材檢查會靜默解到 light 的檔)。

含 chart 的模板頁:**可註冊為 fill(詞彙表 v1.1 起),
但每個圖表 shape 必須被 `chart` op 覆蓋**(lint 硬擋未覆蓋者——文字換了、
圖表數據沒換是靜默捏造源)。`chart` op:
`{"op":"chart","id":7,"categories":"$.slots.categories","series":"$.slots.series"}`
——以 `chart.replace_data` 替換 categories + 1..N 系列;spec 端 values 為
**純數字字串**(維持 validator 數字追溯),每系列 values 數必須等於
categories 數(渲染前硬擋);clone_slide 對 chart part 深複製(含內嵌
xlsx),同參考頁多次 clone 不互相覆寫。v1.1 同時新增 set 的
`delete_if_missing` 修飾詞(選填槽位缺值 → 刪框)。目前唯一的 chart fill 頁型是 light 的
`data_line_trend_comparison`(模板 p25);其餘三種 chart 頁(p26/27/31)
依同模式按需升級。SmartArt 頁一律 `unsupported`。

## 6. 產檔時怎麼選模板

- **spec 裡選**:`deck.template`(模板包 id,**省略 = `"light"`**)。
  舊 spec 不寫這個欄位照跑,零破壞。
- **命令列選**:`--template-pack <id|目錄>`(七支工具一致),
  搭配 `--packs-root <目錄>` 指定模板包根。
- **兩處並存且不同 → exit 2 硬錯**,不靜默擇一(沉默優先會讓同一份輸入
  在不同跑法產出不同結果,牴觸確定性)。
- `--template <pptx 路徑>` 是相容別名(= light 包 + 覆寫模板檔),
  用於「拿新版模板檔試跑」。
- **範圍鐵則:模板包只能把既有語意頁型映射到自己的模板頁,不能發明新語意
  頁型。** 新增語意頁型走契約同步、由工程師把關——這讓「同一份 spec 換
  `deck.template` 就換皮」在結構層永遠成立。
- **outline 一鍵模式按包收斂**:該模式硬帶 `--registered-only --strict`
  且禁 render_plan,所以切頁時**頁型候選 = 該包的全自動集合**
  (先跑 `make_skeleton --list --template-pack <id>` 取支援矩陣);
  該包 cover/agenda/closing 非全自動時,對應規則是「略過該頁」。

各工具的模板感知行為:

| 工具 | 從模板包讀什麼 | 解不到包時 |
| --- | --- | --- |
| `render_deck` | 綁定(fills)、模板檔、頁碼框與清除窗 | 退回 light |
| `validator` | 合併容量覆寫、per-頁型素材鍵、三級閘門(unsupported 擋、非全自動 WARN) | 退回單模板行為 |
| `qa_check` | 字體白名單、頁碼偵測窗 | 內建 light 常數 |
| `make_skeleton` | 素材預設、合併容量、`--list` 三級支援;骨架寫入 `deck.template` | 退回 light |
| `run_pipeline` | 解析一次、四階段共用;前置檢查含 manifest/綁定/模板檔 | 預設鏈 CLI→spec→light |
| `inspect_template` | `--verify` 比對 inventory 與現模板,漂移 exit 1 | `--pptx` 原用法不受影響 |
| `prepare_env`(前端) | 把 `engine/templates/` 同步進 `ppt_out/templates/` | — |
| `audit_provenance` | **不讀**(它管的是內容忠實,與模板無關) | — |

## 7. 驗收與註冊工具鏈

### 7.1 兩種 golden,別搞混

| | **實跑的 golden** | **`engine/golden/` 的快照** |
| --- | --- | --- |
| 誰產生 | `template_admin.py golden --id <包>` **當場派生** | `golden --regen-specs` 寫檔 |
| 依據的契約 | 該包的 **merged 契約**(含它的 capacity_overrides) | **共用基準契約** `PAGE_TYPES`,不綁任何模板 |
| 涵蓋範圍 | 該包的 **fill 頁型** × min/max | **全部註冊頁型** × min/max |
| 有沒有被程式讀 | — (產生後直接送 validator/render/qa) | **沒有**,只寫不讀 |
| 用途 | 驗這個模板包做對了沒 | **契約改動時,git diff 看得見形狀變化** |

**所以 `engine/golden/` 的檔案數 = 註冊頁型數 × 2(線性,與模板數無關)**
——不會因為多了幾個模板就爆增,因為各包實跑時是當場派生、不落檔。
它們刻意**不寫 `deck.template`**(綁模板就不通用了),
並由 [`../engine/REGRESSION.md`](../engine/REGRESSION.md) 的 **R11** 檢查
它與現行契約同步(改契約沒重派生 → R11 紅)。

### 7.2 派生規則與工具鏈

實跑與快照共用同一套派生邏輯,由 `PAGE_TYPES` 契約**確定性派生**
(零隨機、對註冊流程唯讀)。

**派生規則**(與 make_skeleton **共用同一套**契約走訪/FIXED/placeholder
實作——import 同一模組,不重寫,確保「保證通過驗證器」的既有性質):

- `<page_type>.min.json`:清單取下限、選填槽位省略 → 測**刪格路徑**
  (多餘格/分隔線/群組必須刪乾淨,不留空框)。
- `<page_type>.max.json`:清單取上限、**選填槽位一律取上限**(否則測不到
  side_cards 等選填綁定與其刪除路徑)、文字槽位填滿 max_chars、value 類
  槽位填固定樣本 `"99.9%"` → 測**溢出併入與縮字路徑**。
- 共通:`render_page_number` 依契約 page_number 規則填;assets 鍵依
  merged 必要鍵集填(新包 fill 頁鍵集為 `[]` 即不填;需要時填 manifest
  `asset_defaults` 路徑,經 validator `asset_exists` 解析);頁型特例沿 make_skeleton
  現規則(closing `main_title` 固定 "Thank you"、agenda `items[].number`
  序號、placeholder 截斷)。
- 直供 JSON 模式驗(無 --slides,追溯關),契約改動時重新派生,
  git diff 即契約漂移證據。**LLM 與設計師都不得為了過驗收改 golden。**

註冊工具鏈單一入口 `engine/release/template_admin.py`(**不入 tools.zip**,
僅本機;直接操作 repo 端 `engine/templates/` 與 `engine/tools/`,不經 ppt_out
沙箱副本;命令全單行 python,三 shell 原樣可跑):

| 子命令 | 內容 |
| --- | --- |
| `new --pptx <路徑> --id <id> --name <名>` | 建包骨架、複製 pptx、manifest 草稿(status=draft)、初始化 registration_state |
| `freeze --id <id>` | 重建 inventory.json + 寫入 template_sha256 |
| `lint --id <id>`(`--all` 跑全部包) | manifest schema、覆寫 path 存在性與白名單、bindings schema、shape id 全部存在於 inventory、**全覆蓋原則**(頁上文字 shape 必被 set/rows/list/delete/keep 覆蓋)、asset_defaults 指到的檔案存在(僅當有頁型要求該鍵)、chart/SmartArt 頁未被註冊為 fill |
| `golden --id <id> [--page-types a,b]` | 對每個 fill 頁型跑 min+max:validator → render(fills_engine)→ qa(帶包字體白名單);**連跑兩次比對 shape 樹全等**(冪等實證);產 `ppt_out/golden_<id>.pptx` 供目檢 |
| `register --id <id>` | 原子性:lint → golden all(不信任舊戳記)→ **light 回歸**(light golden + examples 01/02 走 run_pipeline)→ isolation 檢查 → 全綠才翻 status=registered;任一紅 → 留 draft |
| `pack --id <id>`(`--tools` 打 tools.zip) | 打 `gpts/dist/template_<id>.zip`(或 tools.zip;一律 Python zipfile、正斜線 arcname、打包後 infolist 反斜線檢查 + sha 核對,任一不符 exit 1) |
| `isolation` | 讀 `git status --porcelain`(含未追蹤檔)對照白名單(§7) |
| `golden --regen-specs` | 從 PAGE_TYPES 重新派生 golden fixtures(契約改版時用,工程師專用) |
| `fit --id <id>` | 量測版位真正裝得下多少字/幾項,寫入該包 `capacity_overrides`(見 §7.3) |

驗收判準:**機器綠(golden all PASS)+ 設計師目檢點頭,缺一不可**
(qa 溢出是 CJK 啟發式 WARN,機器綠不保證視覺不爆框)。

### 7.3 容量誠實化:上限由量測決定,不由手填

**原則(設計師 2026-07-26 定調)**:

> 字級是被設計過的。內容塞不下時正確做法是改寫更短或換頁型,不是用小一號的字體。

`PAGE_TYPES` 的字數/長度只是**跨模板預設值**;各包真正裝得下多少寫在自己的
`capacity_overrides`,由 `template_admin.py fit` 量測後產生(**不得手填**)。

為什麼:憑感覺填的上限會讓「閘門 PASS、版面壞掉」。實例——light 宣告
`core_mission` 60 字,版位是 2.10×0.50 吋 24pt(模板原文 4 字);塞滿時渲染器
靜默把字縮到 12pt,32 頁 golden 有 **99 個框被縮**,validator/qa 全綠,
設計師目檢才發現。修正後同一批頁型:被縮字 0、qa 警告 0。

配套的三個機制:

1. **`shrink_to_fit` 不動 autofit 框**(`spAutoFit` 會長高、`normAutofit` 由
   PowerPoint 自行縮字,那是模板原本的排版方式)。字級不再被引擎偷改。
2. **qa 檢查「文字壓到別的元素」並列為 FAIL**(不是警告)。判準是
   **不得比模板原本更侵入鄰欄**——模板本身就有刻意疊在一起的設計
   (light p47 的徽章與副字、p29 的 44pt 數字),絕對零重疊會誤殺。
   幾何工具在 `text_tools.walk_absolute / text_footprint / text_collisions`。
3. **`fit` 的四個收斂訊號**:①框被縮字 ②文字侵入鄰欄且比模板更糟
   ③autofit 框長得比設計師自己那份還高 ④`add_textbox` 新增框裝不進自己的框。
   全部歸零才收斂;兩個旋鈕是 `max_chars` 與清單 `max`。

**「裝得進自己的框」不是充分條件**。設計師的原話:「有時候不是 autofit 沒超過,
是 autofit 後跑到了不該出現字的位置」——`wrap="none"` 的框往右長、autofit 的框
往下長,結果壓到鄰欄。這是 2026-07-26 目檢 p4/p10/p22/p30 抓出來的失效模式。

改 `fit_capacity.py` 前**先讀該檔檔頭的「15 個已知量測陷阱」**(清單路徑的
`.item`、索引 vs 切片語意、併格框的長度公式、一框多欄位、`add_textbox` 的
跨槽位預算、探測字元要用中文、群組座標換算、碰撞基準取自模板、
只收「範圍會隨文字變大」的那一方)。每一個都真的踩過。
## 8. 已知限制與未定案

**限制(接受並帶緩解)**:

- **op 詞彙表可能表達不了某些版面**(如動態置中重排)。緩解:該頁型降級
  `clone` 仍可用;高頻降級的頁型進 FEEDBACK 統計,再評估擴 op
  (擴充是**引擎版本事件**:改 fills_engine + 對全部已註冊包跑回歸,
  不在註冊對話中發生)。
- **qa 的溢出偵測是 CJK 啟發式**,機器綠不保證視覺不爆框——所以驗收一定要
  設計師開檔目檢(`wireframe_preview.py` 可產線框輔助,但不能取代)。
- **契約(PAGE_TYPES)改版會連動全部模板**:golden 重派生 → 全包重跑 →
  有包由綠轉紅代表該模板裝不下新容量,該頁型降級並記該包 FEEDBACK,
  **不得為單一模板改共用契約**。
- **GPTs Knowledge 20 檔上限**:目前 10 檔,守 ≤19 紀律,約可再容 9 個模板包。
- **閘門是指示強制,非系統強制**(公司政策禁 GPTs Actions):模型仍可能跳過
  驗證,緩解是要求貼出 PASS 輸出 + run_pipeline 單一入口把步驟數壓到最低。
- **Windows PowerShell 全流程尚未實機驗證**(團隊有 Windows 使用者且公司禁
  WSL);所有命令已寫成單行 python、無 shell 專屬語法,首位使用者回報即定案。

**未定案**:

- 頁碼政策(cover/closing 無頁碼)目前寫在共用語意契約,是否開放各包覆寫,
  等真實需求。
- clone 級頁型要不要也做最小 smoke(clone + 改一字 + qa),目前不做。
- 含照片頁型的「使用者上傳圖」歸檔位置(素材解析順序已預留)。
