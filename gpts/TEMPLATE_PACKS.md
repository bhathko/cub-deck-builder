# TEMPLATE_PACKS.md — 多模板架構設計(模板包公式 + 註冊流程)

> **狀態:設計定稿,尚未實作。**(2026-07-25,由 WORKLOG §8 需求延伸)
> 未實作前一律以 `AGENTS.md` 現行條文為準;每個 Phase 落地時依 §7 草稿
> 同步修訂 AGENTS.md,修訂後仍以 AGENTS.md 為準(本檔僅為設計藍圖與
> 實作依據,不另立裁決權)。
> 配套 skill 草稿 `.codex/skills/register-template/SKILL.md`:其引用的
> `template_admin.py` 等工具是 **Phase 2 交付物**;Phase 2 工具鏈落地且
> 等價驗證全綠前,該 skill **不得安裝到 `~/.codex/skills/`**。

## 0. 需求與公式總綱

需求:設計師會持續新增模板(新 .pptx),每次產檔只指定一種模板;
設計師要能「透過 prompt」(本機 Claude Code / Codex CLI 對話)註冊新模板,
不需要工程師逐模板寫程式。

**公式(一句話):把「模板知識」從引擎與共用文件中全部抽離,收進
「一模板一目錄」的自足模板包(template pack);引擎只認 manifest,
語意契約跨模板共用,綁定資料每包各自持有,新增模板 = 加一個目錄,不改引擎。**

依據:對全 repo 的耦合盤點(2026-07-25,約 76 處 light 專屬耦合),
模板耦合實分四類:

| 類 | 內容 | 現況位置(代表例) | 未來歸屬 |
| --- | --- | --- | --- |
| (a) 綁定 | 頁型→模板頁碼、shape id、填充特例 | `fills.py` FILLS 全檔;`page_types.md` 49 行「來源模板第 N 頁」(含 5 種 fill 頁型條目) | 模板包 `bindings.json` + `page_map.md` |
| (b) 主題 token | 品牌色、字型、字體白名單 | `pptx_toolkit.py` COLOR_*/FONT_*;`qa_check.py` ALLOWED_FONTS;`style_guide.md` 色票 | 模板包 `manifest.json` `style` |
| (c) 幾何常數 | 頁碼框/偵測窗、logo 位置、header 座標、16:9 假設 | `render_deck.py` `_page_number`(12.30,6.72)/清除窗 >11.2";`qa_check.py` 偵測窗 >11.0"(**兩者已不一致**,必須收斂單一宣告) | 模板包 `manifest.json` `page_number` 等 |
| (d) 容量 | max_chars、清單 min/max(照 light 框大小調的) | validator `PAGE_TYPES` 數值;`page_types.md` 內容容量節 | 語意契約當預設值 + 模板包 `capacity_overrides` |

真正跨模板可共用的**語意契約**只有:頁型名稱、槽位名稱與巢狀結構、
kind/required/provenance、來源追溯規則。這層維持現行三處同步不動。
(現行契約裡的 assets 必要鍵與 page_number 取值屬 light 工法,
降為「預設值」,包可覆寫,見 §2。)

## 1. 模板包結構

```
gpts/templates/<template_id>/        ← 一模板一目錄,id 格式 ^[a-z][a-z0-9_]{2,31}$
  template.pptx                      ← 模板本體(檔名固定,身分由目錄名決定)
  manifest.json                      ← 機器可讀真相來源(§2)
  bindings.json                      ← 填充綁定(宣告式 op,§3;light 例外為 bindings.py)
  page_map.md                        ← 人類可讀:語意頁型→模板頁+支援等級(含 unsupported 明列)
  inventory.json                     ← freeze 產物:綁定頁 shape 樹快照 + pptx sha256
  assets/                            ← backgrounds/*.png、logos/*.png(隨包出貨;fill 頁通常不需要,見 §2)
  assets_src/                        ← 可編輯素材源檔(不入 zip)
  examples/smoke_spec.json           ← 至少一份保證 PASS 的 spec(不入 zip)
  REGRESSION.md / FEEDBACK.md        ← 每模板回歸與回饋台帳(不入 zip)
  registration_state.json            ← 註冊進度存檔(僅 draft 期存在,支援中斷續作)
```

- **light 是第一個包**:`gpts/templates/light/`,現行 `fills.py` 的 FILLS 與
  `render_deck.py` 的 BUILDERS **原封搬入** `bindings.py`(grandfather,零行為改變);
  `light_template.pptx` 與 `assets.zip` 內容併入包內。
- **新模板不得有 builtin**:cover/agenda/closing 等 5 種 builtin 頁型在新模板
  一律要求模板 pptx 內含對應頁,以 fill 模式綁定(設計師在 PowerPoint 改版面,
  不在 Python 調座標);模板缺頁 → 該頁型 unsupported。builtin 僅 light 保留。
- **新模板的 fill 頁預設免素材**:fill 模式是 clone 模板實頁,背景/logo 已
  烙在頁面裡,不需要 spec 提供 assets(這正是 builtin「空白頁+貼背景圖+貼 logo」
  工法與 fill 工法的本質差異)。素材檔只在 clone 參考頁需求或未來照片頁型時
  才進包。

## 2. manifest.json(欄位定義)

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
  render_plan 複製改字(= 現行 page_types.md 40+ 種的體驗,也是綁定失敗的
  **內建降級層**);`unsupported` = validator 硬擋(附 reason)。
  部分支援是合法結局,不逼全頁型全綠。`builtin` 模式僅 light 允許。
- **per-頁型素材鍵覆寫**:語意契約的 assets 必要鍵(background/logo)降為
  **預設值**;包內 `page_types.<pt>.assets` 可覆寫必要鍵集(新包 fill 頁
  一律 `[]` = 免素材,§1)。validator 取「包覆寫,無則契約預設」;
  素材存在性檢查經 pack 的 `resolve_asset`(§3)。light 包不覆寫,
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
  多數 FillError 因此提前到載入期。

## 3. 綁定表示法:固定 op 詞彙表的宣告式 bindings.json(核心決策)

**決策:新模板的填充綁定一律是宣告式 JSON(固定 op 詞彙表,引擎
`fills_engine.py` 解譯執行);註冊時 LLM 只產 JSON,不產 Python。
light 的 fills.py/BUILDERS 原封 grandfather,不重寫。**

評估過的替代方案:

- **每模板一個 Python bindings.py**(表達力最強、除錯 traceback 直指行號、
  與 fills.py 慣例連續):否決。理由:(1) repo 治理哲學一貫是「封閉 LLM 輸出
  空間 + 機器可驗」——validator 契約、make_skeleton 禁手打 JSON、outline skill
  鐵律 4「禁止現寫 Python 取代管線腳本」;註冊對話中讓 LLM 寫 per-template
  Python 正面牴觸這條精神,且審查成本(每模板一份自由程式碼)隨 N 線性成長。
  (2) bindings 隨 zip 進 GPTs 沙箱執行,JSON 是資料、Python 是可執行碼,
  信任面完全不同。(3) AST lint 白名單只是淺層防護。
- **混合(宣告式+Python hook 逃生口)**:否決——現有 5 個 fill 函式每個都含
  至少一項特例,逃生口使用率會是 100%,等於 Python 加一層儀式。

op 詞彙表固定 6 個,自 fills.py 現有特例逐條歸納(**下表形式欄位為節錄,
完整欄位以 Phase 2 的 bindings schema 為準**;p17 溢出與 p33 建議列
需要的修飾詞已列入,見表後註):

| op | 對應 fills.py 既有特例 | 形式(關鍵欄位) |
| --- | --- | --- |
| `set` | `ctx.set(51, title)`;KPI `f'{label} {value}'`;pros `"\n".join`;金字塔帶標籤 ≤6 字才填否則刪框 | `{"op":"set","slot":"$.title","id":51}`;修飾詞 `"template":"{label} {value}"`、`"join":"\n"`、`"max_len_or_delete":6` |
| `delete` | p17 刪直排/標籤/子導覽;p29 單位框、p33 分數籤/縮圖一律刪(契約無此欄位,留著=捏造) | `{"op":"delete","ids":[7,28,29]}` |
| `keep` | (新增,見表後註「全覆蓋原則」)模板頁上的結構性字樣明示保留 | `{"op":"keep","ids":[17],"reason":"欄目標籤『目錄』,固定結構字樣"}` |
| `rows` | `_fill_rows`:固定列+分隔線,不足刪列刪線、溢出併入最後一列並加高 | `{"op":"rows","slot":"$.slots.before.points","row_ids":[21,22,23],"sep_ids":[24,47],"overflow":"merge_last","merge_height_in":0.80}` |
| `list` | p14 (文字框,底圖) 成對刪;p33 每方案成組刪;p54 四層時**從頂端刪**(尾端對齊);p17 rest 溢出併入最後一組的 desc 框 | `{"op":"list","slot":"$.slots.options","align":"head 或 tail","items":[{"sets":[{"slot":"@.name","id":9}],"delete_always":[3,7],"delete_on_missing":[12,29,64]}],"overflow":{"merge_into_id":50,"join":"\n"}}`(`@`=清單元素相對路徑;slot 支援切片如 `points[2:]`;`overflow.merge_into_id` 指定的框在無溢出時刪除) |
| `add_textbox` | p54 無副標佔位→動態補建;p33 建議列(recommended+recommendation 串接、前綴「建議:」、皆空不建框) | `{"op":"add_textbox","slots":["$.slots.recommended","$.slots.recommendation"],"prefix":"建議:","join":"、","skip_if_empty":true,"x":0.85,"y":6.42,"w":11.8,"h":0.36,"pt":14,"bold":true}`(字型取 manifest `style.font_zh`) |
| `resize` | p14 中心圓文字框加高讓長句留在圓內 | `{"op":"resize","id":37,"top":3.25,"height":1.00}` |

(`keep` 不算填充 op,是覆蓋宣告;詞彙表計數仍以 6 個填充 op 為準。)

三個配套原則:

- **全覆蓋原則**:每個 fill 頁的綁定,模板頁上**所有含文字的 shape** 必須被
  set/rows/list/delete/keep 之一覆蓋,lint 硬檢查。`keep` 僅限不含數字、
  非內容語意的固定結構字樣(欄目標籤、章節字、「目錄」之類——對應 light
  builtin 主動畫上的 Contents/背景/預期成果等字樣,新模板該類字烙在模板頁上,
  刪了版面語意反而殘缺);qa/audit 不追溯 keep 字樣。判準:含任何數字或
  可能被誤讀為內容事實的字樣不得 keep,只能 delete。
- **表達力的最終裁決是等價驗證,不是本表**:表已逐條對照 fills.py 歸納
  (含 p17 溢出、p33 雙槽串接兩個最刁的案例),但以 Phase 2「light 5 種
  fill 頁型以 bindings.json 重寫、與 fills.py 產出 shape 樹全等」為實證;
  個別頁型驗不過 → 該頁型明文留在 light 的 bindings.py grandfather,
  缺口記錄供 op 擴充評估,**不阻斷 Phase 2**,也不影響新模板(新模板遇到
  表達不了的頁直接降級 clone)。
- **鐵則:表達不了 = 降級 clone,絕不在註冊對話中擴詞彙表、絕不讓 LLM
  現寫 Python。** 詞彙表擴充是「引擎版本事件」:由工程師加 op、補 schema、
  對全部已註冊包跑回歸。

先例佐證:validator 的槽位文法(kind/min/max 遞迴結構)本來就是
「宣告式迷你語言 + 解譯器」,fills_engine 與其架構對稱,不是新發明。

新增引擎件(`gpts/tools/`,隨 tools.zip 出貨):

- `fill_helpers.py`:自 fills.py 抽出 `FillError`/`index_shapes`/`Ctx`/
  `_fill_rows`(公開化為 `fill_rows`),並把 p33/p54 兩處**內聯** add_textbox
  樣板整併為新 helper `add_styled_textbox`(light 的 bindings.py 與
  fills_engine 共用)。
- `fills_engine.py`:bindings.json 解譯器(op 執行器 + bindings schema 驗證;
  op 依序執行、`shrink_to_fit` 收尾 min 12pt 同現行、shape id 不存在即
  FillError,訊息格式同現行並加註包 id/version)。
- `pack_loader.py`:`load_pack(cli_arg, spec_deck, packs_root, asset_dir) -> Pack`,
  提供 `.manifest .template_path(驗雜湊) .fills .builders .merged_page_types
  .style .asset_defaults`;素材解析 `resolve_asset`:**light 包 = asset_dir
  優先、包目錄兜底(舊 spec 的 `assets/...` 路徑不變);非 light 包 =
  包目錄優先、asset_dir 兜底**(防跨包遮蔽:本機沙箱 asset_dir 永遠有
  light 的 assets/,若 asset_dir 優先,新包素材檢查會靜默解到 light 的檔)。

含 chart 的模板頁(如 light p25-27/31)**禁止註冊為 fill**(lint 硬擋):
fills_engine 無 `chart.replace_data` 原語,smoke 會綠但圖表數據不會被替換,
是靜默捏造源。chart 支援屬 WORKLOG §8 第二級,另案排程;現階段一律 `clone`
或 `unsupported`。SmartArt 頁一律 `unsupported`。

## 4. 產檔管線的模板感知

- **spec 選模板:`deck.template`(字串 id,省略 = `"light"`)**。
  deck 已 `additionalProperties: true`,新舊 schema 互驗皆過,零破壞。
  `page_type` enum 維持語意契約鍵集不動。
- **CLI:`--template-pack <id|dir>` + `--packs-root <dir>`**(五支工具一致);
  與 `deck.template` 並存且不同 → **exit 2 硬錯**,不靜默擇一
  (兩處來源沉默優先=同輸入不同跑法產不同結果,牴觸確定性)。
  `--template <pptx路徑>` 保留為相容別名(= light 包 + 覆寫模板檔,
  支撐 WORKLOG §9「拿新版模板檔試跑」);都不帶 → spec → `"light"`,
  現有 spec 與命令零改動照跑。
- **v1 範圍鐵則:模板包只能把既有語意頁型映射到自己的模板頁,不能發明新語意
  頁型。** 新增語意頁型(新槽位結構)仍走三處同步,由工程師把關。這讓
  「同一份 spec 換 `deck.template` 就換皮」在結構層永遠成立,也讓註冊 skill
  的輸出空間封閉可驗。
- **outline 一鍵模式的按包收斂**(部分支援包的死路防範):outline 模式
  現行由 run_pipeline 硬帶 `--registered-only --strict`,且鐵律禁 render_plan
  ——若切頁選到該包非 fill 的頁型即 ERROR 死路。因此明定:**outline 模式的
  頁型候選 = 該包 fill 級集合**(切頁前先跑 `make_skeleton --list
  --template-pack <id>` 取支援矩陣,選型規則按包過濾;該包 cover/agenda/
  closing 非 fill 時,對應規則為「略過該頁」)。README_TOOLS 錯誤→修法表
  新增一列:「頁型不受此模板支援 → 換該包 fill 頁型,或換 deck.template,
  或回註冊流程補註冊」。

逐支工具改動:

| 工具 | 改動 | 向後相容 |
| --- | --- | --- |
| render_deck | 刪檔內 BUILDERS 與 `import fills` → `pack.builders/pack.fills` dispatch;fill 模式經 fills_engine;頁碼框/清除窗讀 manifest;輸出行加 `模板包:<id>@<version>` | 不帶參數行為位元組級同現行 |
| validator | 讀 `deck.template`;merge capacity_overrides 與 per-頁型 assets 覆寫;素材存在性經 resolve_asset;三級閘門:`fill`=完整契約檢查(merged 容量);語意契約有、但該包非 fill → WARN「此模板需 render_plan」(`--registered-only` 下升級 ERROR);`unsupported` → ERROR 附支援清單與修法(換頁型/換模板/回註冊流程補) | 無 template 時同現行 |
| qa_check | ALLOWED_FONTS ← manifest;頁碼偵測窗 ← manifest;其餘(槽位覆蓋/頁數/Section/溢出)模板無關不動 | 解不到包 → 內建 light 常數 |
| make_skeleton | BG/LOGO ← `asset_defaults`(映射慣例見 §2);容量 ← merged 契約;assets 鍵 ← per-頁型覆寫;`--list` 按包列三級支援;骨架一律寫入 `deck.template`;`--types` 含 unsupported 頁型直接拒產 | 不帶參數 → light |
| run_pipeline | 參數透傳四階段;前置缺檔檢查加 manifest/bindings/模板檔 | 預設鏈 CLI→spec→light |
| inspect_template | 加 `--verify`:比對 inventory.json 與現 pptx,列 shape id 增刪/幾何漂移,有 drift exit 1 | `--pptx` 原用法不動 |
| audit_provenance | **不動**(決策,非遺漏:STRUCTURAL_PAGES/EXEMPT_PATHS/closing 固定 Thank you 屬頁型層語意契約,與模板無關) | 同現行 |
| prepare_env(.codex) | REQUIRED 清單加 `templates/`;同步 `gpts/templates/` → `ppt_out/templates/`(outline 前端的 packs_root);連帶重裝 `~/.codex/skills/outline-to-ppt` + 重打 zip | 無新模板時行為同現行 |

## 5. 黃金驗收與註冊器

新資產 `gpts/golden/`:每個註冊頁型兩份固定 spec fixture,由
`PAGE_TYPES` 契約**確定性派生**(零隨機、進版控、對註冊流程唯讀)。

**派生規則**(與 make_skeleton **共用同一套**契約走訪/FIXED/placeholder
實作——import 同一模組,不重寫,確保「保證通過驗證器」的既有性質):

- `<page_type>.min.json`:清單取下限、選填槽位省略 → 測**刪格路徑**
  (多餘格/分隔線/群組必須刪乾淨,不留空框)。
- `<page_type>.max.json`:清單取上限、**選填槽位一律取上限**(否則測不到
  side_cards 等選填綁定與其刪除路徑)、文字槽位填滿 max_chars、value 類
  槽位填固定樣本 `"99.9%"` → 測**溢出併入與縮字路徑**。
- 共通:`render_page_number` 依契約 page_number 規則填;assets 鍵依
  merged 必要鍵集填(新包 fill 頁鍵集為 `[]` 即不填;需要時填 manifest
  `asset_defaults` 路徑,經 resolve_asset 解析);頁型特例沿 make_skeleton
  現規則(closing `main_title` 固定 "Thank you"、agenda `items[].number`
  序號、placeholder 截斷)。
- 直供 JSON 模式驗(無 --slides,追溯關),契約改動時重新派生,
  git diff 即契約漂移證據。**LLM 與設計師都不得為了過驗收改 golden。**

註冊工具鏈單一入口 `gpts/release/template_admin.py`(**不入 tools.zip**,
僅本機;直接操作 repo 端 `gpts/templates/` 與 `gpts/tools/`,不經 ppt_out
沙箱副本;命令全單行 python,三 shell 原樣可跑):

| 子命令 | 內容 |
| --- | --- |
| `new --pptx <路徑> --id <id> --name <名>` | 建包骨架、複製 pptx、manifest 草稿(status=draft)、初始化 registration_state |
| `freeze --id <id>` | 重建 inventory.json + 寫入 template_sha256 |
| `lint --id <id>`(`--all` 跑全部包) | manifest schema、覆寫 path 存在性與白名單、bindings schema、shape id 全部存在於 inventory、**全覆蓋原則**(頁上文字 shape 必被 set/rows/list/delete/keep 覆蓋)、asset_defaults 指到的檔案存在(僅當有頁型要求該鍵)、chart/SmartArt 頁未被註冊為 fill |
| `golden --id <id> [--page-types a,b]` | 對每個 fill 頁型跑 min+max:validator → render(fills_engine)→ qa(帶包字體白名單);**連跑兩次比對 shape 樹全等**(冪等實證);產 `ppt_out/golden_<id>.pptx` 供目檢 |
| `register --id <id>` | 原子性:lint → golden all(不信任舊戳記)→ **light 回歸**(light golden + examples 01/02 走 run_pipeline)→ isolation 檢查 → 全綠才翻 status=registered;任一紅 → 留 draft |
| `pack --id <id>`(`--tools` 打 tools.zip) | 打 `gpts/knowledge/template_<id>.zip`(或 tools.zip;一律 Python zipfile、正斜線 arcname、打包後 infolist 反斜線檢查 + sha 核對,任一不符 exit 1) |
| `isolation` | 讀 `git diff --name-only` 對照白名單(§7) |
| `golden --regen-specs` | 從 PAGE_TYPES 重新派生 golden fixtures(契約改版時用,工程師專用) |

驗收判準:**機器綠(golden all PASS)+ 設計師目檢點頭,缺一不可**
(qa 溢出是 CJK 啟發式 WARN,機器綠不保證視覺不爆框)。

## 6. 打包與 GPTs 發佈

- **每模板一包 `template_<id>.zip`**(pptx + manifest + bindings + page_map +
  assets;zip 檔名穩定不帶版本,版本記在 manifest,Builder 端刪舊傳新)。
  否決:全塞 tools.zip(工具/模板版本耦合、包膨脹、回歸面全開)、
  每模板一個 GPT(instructions ×N 同步爆炸;保留為觸頂備案)。
- **Knowledge 檔數推演**:重整後 10 檔(`light_template.pptx`+`assets.zip`
  併入 `template_light.zip`,反而 -1),≤19 紀律(上限 20 常備 1 空位),
  容量 = light 外還可加 9 個模板;觸頂依序:examples 併 docs.zip → 分 GPT。
- **instructions.md**:Step 0 改為「依 `deck.template`(預設 light)解壓對應
  一包 → `/mnt/data/templates/<id>/`,一次只解需要的模板」;自證輸出必含
  manifest 的 template_id+version(「你現在是哪一版?」同時驗模板版);
  新增「可用模板 roster」行,任何模板包重傳都 bump instructions 版本字串。
- **GPTs 端零註冊**:沙箱無持久化、Knowledge 唯讀,註冊本質是 repo commit +
  重打包 + Builder 重傳,只可能在本機發生。instructions 加一行:使用者要求
  新模板時說明流程並引導聯繫管理者,不嘗試在對話中註冊。
- **發佈 checklist**(寫進 gpts/README.md 新節):該模板 REGRESSION 綠 →
  isolation diff 白名單過 → `pack` 重打包(tools 沒改就不動 tools.zip)→
  instructions 版本+roster → 檔數 ≤19 → Builder 刪舊傳新(只傳異動檔)→
  問版本驗收 + 該模板 smoke_spec 產檔 PASS + light 抽測不受影響。

## 7. 同步鐵律 v2 與 AGENTS.md 條文草稿(隨對應 Phase 落地時採用)

同步分兩層,**不隨模板數變成 N 處**:

- **語意契約(共用)**:三處同步照舊(validator `PAGE_TYPES` / schema enum /
  page_types_registry.md),與模板數無關;此三檔**不得含任何模板頁碼或 shape id**。
- **模板綁定(各自)**:一包自洽——只動 `templates/<id>/` 包內檔 + 重打該包 zip,
  不碰任何共用檔;**槽位契約不得寫進模板包**。跨層改動必須拆 commit。
  跨層一致性由 `template_admin.py lint` 機器檢查(manifest 頁型鍵必須存在於
  語意契約或 page_types.md 語意庫)。

`page_types.md`(734 行)拆分:語意分類/容量/選型原則留共用 Knowledge;
49 行「來源模板第 N 頁」與品牌色 hex 描述全數搬進 light 包 `page_map.md`。
`style_guide.md` 同理拆:共用排版紀律(可編輯物件/不生圖/Section 禁令)留檔,
light 視覺常數(色票/字級表/素材指名)進包。

條文草稿(取代/新增 AGENTS.md 硬規則):

1. **規則 1 改寫(SSOT 分兩處)**:語意契約與共用規範的 SSOT 仍在
   `gpts/knowledge/`;**模板知識的 SSOT 在 `gpts/templates/<id>/`
   (manifest 為機器真相)**。AGENTS.md/CLAUDE.md「常用指令」段的模板路徑
   (`--template gpts/knowledge/light_template.pptx`)於 Phase 1 同步改為
   pack 寫法。
2. **規則 2 改寫(兩層同步)**:改語意頁型契約 → 三處同步(共用,禁模板資訊);
   改模板綁定 → 只動 `gpts/templates/<id>/` 並重打 `template_<id>.zip`
   (禁槽位契約);容量與素材鍵覆寫只住各包 manifest,單檔即真相。
3. **規則 4 改寫(耦合以包為界)**:每包 bindings 只對同包 template.pptx 有效,
   以 `template_sha256` + inventory 機器強制;模板改版走 lifecycle:換檔 →
   `freeze` → inventory diff 核對 bindings → `lint` → **`golden` all 綠**
   (id 沒變但幾何漂移的視覺壞版只有 golden+目檢抓得到)→ 該模板 REGRESSION
   綠 → manifest version bump → `pack`。sha 不符 = 盤點未完成,拒發版。
4. **規則 5 改寫**:改 `gpts/tools/*` → tools.zip(`template_admin.py pack
   --tools`);改 `templates/<id>/` → `template_<id>.zip`(`pack --id`);
   打包一律經 template_admin(內建正斜線與 sha 檢查)。
5. **新規則(模板隔離)**:涉及模板 X 的 commit 只准觸碰
   `gpts/templates/X/**`、`gpts/knowledge/template_X.zip`、
   `gpts/templates/INDEX.md`、`gpts/instructions.md`(版本字串/roster 行);
   越界即違規,以 `template_admin.py isolation` 機器驗證。
6. **新規則(綁定準入)**:bindings 必過 `lint`(含全覆蓋原則)+ `golden`
   (含連跑兩次全等)才可 register;模板包無權新增語意頁型;
   golden fixtures 對註冊流程唯讀。
7. **新規則(註冊只在本機)**:`.codex/skills/register-template/` 是唯一註冊
   入口(啟用門檻見本檔頭部);GPTs 端只消費模板包。
8. **新規則(Knowledge 預算)**:檔數 ≤19;觸頂依序 examples 併 docs.zip →
   評估分 GPT;不得把模板包塞進 tools.zip。
9. **規則 8 補一句**:`.codex/skills/` 下所有 skill(含 register-template)
   同步安裝 `~/.codex/skills/` + 同名 zip。

## 8. 遷移計畫(每階段可獨立 commit/發版,light 全程零行為變化)

- **Phase 0|light 包化(不發佈,GPTs 端不動)**:抽 `fill_helpers.py`;建
  `gpts/templates/light/`(manifest / bindings.py grandfather / page_map.md /
  inventory / REGRESSION / FEEDBACK / smoke_spec);render_deck 改 pack 載入;
  建 INDEX.md 與 lifecycle 文件。**tools.zip 需重打包(repo 端)且
  REGRESSION R7 hash 基準同步更新,但紅線:Phase 1 Knowledge 換裝前
  禁止把新 tools.zip 上傳 Builder**(pack 化的 render_deck 依賴
  templates/light/,Knowledge 要到 Phase 1 才有 template_light.zip,
  提早上傳 GPTs 端直接壞掉;「GPTs 不動」= 不發佈,非 repo zip 不動)。
  驗收:REGRESSION R0–R8 預期 exit 全符(01–03 類 PASS、04 類預期 FAIL,
  即現行 R1 口徑;測物 = 重打後的新 tools.zip);遷移前後產出以
  `inspect_template --all` 導出 shape 樹 diff 為空(pptx 二進位含 zip 時戳
  不可比,以 shape 樹+qa+文字 dump 為準)。
- **Phase 1|引擎模板感知 + Knowledge 換裝**:七支工具接 pack_loader/manifest
  (§4 表,含 prepare_env 擴充與 outline-to-ppt skill 重裝 ~/.codex);
  schema 加 `deck.template`;page_types.md / style_guide.md 拆分;
  instructions Step 0 + roster;Knowledge 換裝 template_light.zip。
  驗收:舊 spec 行為不變;顯式 `"template":"light"` 與省略產出全等;
  **manifest 讀取證明**(暫改 manifest 假值確認 qa/make_skeleton 行為跟著變,
  改回);Builder 端 README 驗收 1–8 全過;.codex outline-to-ppt 本機全綠
  (含 ppt_out/templates/ 沙箱佈局)。
- **Phase 2|註冊工具鏈 + 雙 skill 上線**:fills_engine + golden fixtures +
  template_admin;**等價驗證:light 5 種 fill 頁型以 bindings.json 重寫,
  fills_engine 產出與 fills.py 產出 shape 樹全等**(詞彙表最強實證;
  驗不過的頁型明文留 grandfather 並記錄缺口,不阻斷;驗完 light 仍跑
  fills.py,切換與否留 Phase 3);register-template SKILL.md 啟用並安裝
  ~/.codex;**outline-to-ppt skill 多模板化**(對話指定模板 →
  `make_skeleton --template-pack` → 骨架寫入 `deck.template`,候選頁型
  按包 fill 集合收斂,§4)——與 register skill 同 Phase 上線,否則
  「註冊完成 → 產第一份簡報」是斷點;用一個真實新模板端到端走完註冊+發佈。
  驗收:新模板 REGRESSION 綠;isolation 證明 light 與共用檔零觸碰;
  Builder 上兩模板各產一份 qa PASS;REGRESSION 新增 R9(同 spec 換
  deck.template 產兩份)與 R10(`template_admin.py lint --all`)。
- **Phase 3|治理常態化**:FEEDBACK 台帳分模板(根檔加「模板」欄,模板專屬
  回饋謄入包內);WORKLOG §8 fills 三級升級計畫改按包執行、按包計數;
  light 切換 bindings.json 並退役 fills.py(選配,需 golden+examples 雙綠);
  選配 pre-commit 跑 isolation/lint。

## 9. 風險與開放問題

風險(接受並帶緩解):

- op 詞彙表對未見過的版面結構可能表達不足(如動態置中重排——現行 fills 對
  2 方案刪第三欄也「不重新置中」)。緩解:降級 clone 兜住可用性;Phase 2 用
  第一個真實模板實測覆蓋率,高頻降級頁型進 FEEDBACK 統計再議擴 op。
- 頁碼不在右下的模板:清除/偵測窗已 manifest 化可宣告,但設計師易漏填;
  註冊 skill 步驟 4 對「模板頁碼框不在宣告窗內」自動加 delete 綁定。
- golden 機器綠不保證視覺不爆框(CJK 估算啟發式)——已以設計師目檢補位;
  選配 wireframe_preview.py(WORKLOG §8)可再降風險。
- Phase 1 是結構大挪移,GPTs 沙箱與本機 prepare_env 兩環境都要重驗,
  路徑歧異會複發 FEEDBACK #1/#2 的「宣稱工具鏈無法執行」;Step 0 自證輸出
  含 manifest id+version 是主要偵測手段。
- 契約(PAGE_TYPES)改版 → golden 重派生 → **全部已註冊包 golden 重跑**,
  可能有包由綠轉紅(該模板裝不下新容量)→ 該頁型降級並記 FEEDBACK,
  不得為單一模板改共用契約。此條寫進 lifecycle 文件。
- Windows PowerShell 全流程未實機驗證(沿用既有風險);register 流程命令更多,
  首位 Windows 使用者實走前不宣稱跨平台定案。

開放問題(留到對應 Phase 定案):

1. GPTs 端多模板何時跟進發佈(本機雙 skill 已列 Phase 2;Builder 換裝與
   roster 屬 Phase 1/2 的發佈動作,實際時點由使用者定)。
2. page_number 政策(cover/closing 無頁碼)目前在語意契約:是否開放包覆寫
   (某模板封面要頁碼)?v1 不開放,等真實需求。
3. clone 級頁型要不要最小 smoke(clone+改一字+qa)?v1 不做,量大且低險。
4. Builder 對同名 Knowledge 檔刪舊傳新後 CI 端是否立即讀到新版:
   Phase 1 發佈時以 Step 0 印 manifest version 實測一次。
5. 含照片頁型(WORKLOG §8 第三級)的使用者上傳圖與包 assets 的關係
   (resolve_asset 的包優先順序已為此預留,歸檔位置未定)。
