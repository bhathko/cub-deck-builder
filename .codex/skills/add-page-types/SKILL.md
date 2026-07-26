---
name: add-page-types
description: 設計師要「讓某個模板多支援幾種版型/頁面」時使用——模板已經註冊過,只是想把某幾頁從半自動升級成全自動。引導式完成:挑頁→定契約→寫綁定→量容量→黃金驗收(設計師目檢)→回歸。Triggers:「我想多加幾個版型」「這幾頁也要能自動產」「把 XX 頁變成自動的」「新增頁面」「註冊新頁型」「add page type」。
---

# add-page-types(既有模板加開頁型)

> **與 `register-template` 的分工**:那支是「拿到一個**新的 .pptx**,從零建一個模板包」;
> 本支是「模板**已經註冊過**,只是要讓它多支援幾種頁面」。
> 兩者最大差別:本支**允許並且必須**改共用契約(三處同步),那支明文禁止。

## 先看清楚使用者要的是哪一件事

| 使用者說 | 實際要做 | 用哪支 |
| --- | --- | --- |
| 「我有一個新模板」「這套新的 pptx 也要能用」 | 從零建模板包 | `register-template` |
| 「這幾頁也要能自動產」「多加幾個版型」 | 既有包內 clone → fill | **本支** |
| 「我要一種全新的版面,模板裡沒有」 | 設計師要先畫進 .pptx | 先請她改模板,再回本支 |

先跑 `python engine/tools/make_skeleton.py --list --template-pack <id>` 給她看
「目前全自動 N 種、半自動 M 種」,再問「你想把哪幾頁變成全自動?」
她可以用白話講(「那個三個大數字的」),你去 `page_map.md` 對頁碼。

## 鐵律

1. **零發明頁型**:候選只能來自 `engine/rules/page_types.md` 已有的 `###` 條目。
   模板裡有一頁但頁型庫沒有對應語意 → 停下來回報,那需要先擴頁型庫(工程師)。
2. **三處同步一個不能少**:`validate_slide_spec_gpts.py` 的 `PAGE_TYPES` /
   `slide_spec.schema.json` 的 `page_type` enum / `page_types_registry.md`。
   漏一處會出現「驗證器認得、schema 不認」的鬼打牆。改完立刻
   `python -c "import sys;sys.path.insert(0,'engine/rules');import validate_slide_spec_gpts"`
   確認匯入不炸。
3. **容量不准手填**:字數與清單長度一律由
   `template_admin.py fit --id <id>` 量測後寫進該包的 `capacity_overrides`。
   憑感覺填的下場是「閘門 PASS、版面壞掉」——2026-07-26 就是這樣,
   32 頁 golden 有 99 個框被靜默縮字,所有自動檢查全綠,設計師目檢才發現。
4. **字級是設計過的**:塞不下要改稿或換頁型,**不准縮字**。這條是設計師定的,
   已烙進工具(`shrink_to_fit` 不動 autofit 框、`fit` 以此為收斂條件)。
5. **golden 綠 + 目檢點頭才算完成**。qa 現在把「文字壓到別的元素」列為 FAIL,
   不是警告——那是設計師目檢抓出來的真實破版模式。
6. **零自由 Python、零手改 pptx**:綁定只能用 8 個 op
   (set/delete/keep/rows/list/add_textbox/resize/chart),詞彙表見
   `docs/ARCHITECTURE.md` §5。表達不了 → 該頁維持 clone。
7. **一次不要吃太多**:一批 3–5 個頁型。批次越大,目檢負擔越重、出錯定位越難。
   (2026-07-26 一次做 10 個,結果目檢揪出 4 頁問題,回頭修了三輪。)

## 步驟 0|環境準備

```
python .codex/skills/outline-to-ppt/prepare_env.py
```

印出的渲染前綴(如 `uv run --with python-pptx python`)套用在所有帶 pptx
操作的命令上;`lint` 與純 JSON 操作不需要。

## 步驟 1|挑頁與盤點

```
python engine/tools/make_skeleton.py --list --template-pack light
```

設計師選定後,對每一頁:

```
uv run --with python-pptx python engine/tools/inspect_template.py \
  --pptx engine/templates/light/template.pptx --page 30
```

**shape id 與座標的唯一來源就是這個輸出**,不得憑印象寫。同時讀
`engine/rules/page_types.md` 該頁型的「視覺結構」與「內容容量」——
契約的槽位與數量以它為依據,不要自己發明欄位。

## 步驟 2|定語意契約(三處同步)

寫進 `PAGE_TYPES`,格式照抄鄰居:

```python
    "data_three_number_kpis": {
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60, required=False),
            "kpis": {"kind": "list", "min": 2, "max": 3, "required": True,
                     "item": {"kind": "object", "fields": {
                         "value": T(6), "label": T(12), "detail": T(30)}}},
        },
    },
```

慣例:內容槽位預設要 provenance;結構性標籤才 `provenance=False`;
頁面標題一律用 spec 頂層 `title`,不放 slots;槽位名用語意化英文
(`heading`/`points`/`label`/`detail`/`name`/`value`)。

**字數先填 page_types.md 的量或寬鬆值就好——步驟 5 會量準。**
同步另外兩處:schema 的 enum、registry 加一節(適用情境 + 槽位說明)。

## 步驟 3|改 manifest + 寫綁定

**先改 manifest,順序不能顛倒。** `engine/templates/<id>/manifest.json` 的
`page_types.<頁型>` 由 `{"mode": "clone", ...}` 改成
`{"mode": "fill", "template_page": N}`,並確認 `template_page` 與 `page_map.md`
一致。**freeze 只快照 `mode == "fill"` 的頁**——沒先改 mode 就 freeze,
會拿到不完整的 inventory,然後 lint 報「缺第 N 頁快照(重跑 freeze)」而你
重跑幾次都一樣(真正的根因是 mode 還是 clone)。

再寫綁定:`engine/templates/<id>/bindings.json` 的 `fills` 是**以頁型名為 key
的 dict**,加一筆:

```json
"fills": {
  "<page_type>": {"template_page": 30, "ops": [ ... ]}
}
```

**全覆蓋原則**(lint 硬擋):該模板頁上所有含文字的 shape 都必須被
`set`/`rows`/`list`/`delete`/`keep` 之一覆蓋。
- 契約沒有的**內容性**元素(範例數字、裝飾標籤)→ `delete`。留著等於捏造。
- 不含數字的**固定結構字樣**(「優點」「目錄」)→ `keep` 並附 reason。
- `list` 的完整欄位:`align`(現行全部 `"head"`)、`sets`、`delete_always`
  (該格位固定要刪的裝飾框)、`delete_on_missing`(項目少於格位時刪這些)、
  `overflow.merge_into_id`(格位不夠時併入哪一格)。完整定義見
  `docs/ARCHITECTURE.md` §5 與 bindings schema。
- **格位大小不一致時先用 `resize` 統一**,再談上限。已註冊的 `info_card_grid`
  就用了 12 個 resize 把網格框寬統一成 2.75 吋之後才下 list op。
  底板寬度本身不同、統一不了(階梯卡那種),才退回「取最小值」。
- **`set` 沒有前綴修飾詞**。模板佔位字帶固定前綴(`# 標籤文字`、`❶`)而槽位是
  純文字清單時,那個前綴留不住;要嘛在 registry 告知使用者自己寫進值裡,
  要嘛把槽位改成單欄位物件配 `template`。
- 例外:清除窗內的純數字頁碼框(x>11.2 且 y>6.3)由引擎處理,不用管。

**平行欄位的格位數不一致會讓版面不對稱**(light p17 三欄是 6/6/4 格,
上限開到 5 只有第三欄會併格 → 設計師目檢 p4 就是抓到這個)。
這件事現在由 `fit` 自動處理(它從綁定算出各組格位數取最小值),
你不用手動算——但**綁定要讓它算得出來**:同一清單的各組請用
`columns[0]` / `columns[1]` / `columns[2]` 這種索引寫法,不要把三欄
寫成三個不同的槽位路徑,否則工具看不出它們是平行的。

## 步驟 4|重建盤點快照 + 靜態檢查

```
uv run --with python-pptx python engine/release/template_admin.py freeze --id light
python engine/release/template_admin.py lint --all
```

`freeze` 沒跑會紅在「inventory 缺第 N 頁快照」。

## 步驟 5|量容量(**不可跳過**)

```
uv run --with python-pptx python engine/release/template_admin.py fit --id light
```

它會反覆「跑 golden → 找出被縮字或壓到鄰欄的框 → 收緊上限」直到收斂,
把結果寫進 manifest 的 `capacity_overrides`,並重生 registry 的容量表。

旗標語意(**兩個不可併用,工具會擋**):

- `--dry-run`:只跑**第一輪**提案、不寫入。那份清單**不是收斂後的答案**,
  數量會比實際需要收緊的多。
- `--reset`:先清空現有上限再從零量。**改過版位大小(把框做大)之後必須加**
  ——本工具只會收緊不會放寬,不加 `--reset` 會直接回報收斂、上限維持舊值,
  設計師會以為改模板沒用。

它同時會處理兩個「幾何可直接算出、不需迭代」的前置修正:
**平行欄位格位數對稱**(三欄 6/6/4 格 → 上限取 4)與
**`add_textbox` 的跨槽位預算**(prefix + 多槽位串成一條字串,限制是總長度)。

演算法與 **15 個已知量測陷阱**寫在 `engine/release/fit_capacity.py` 檔頭。
**要改那支之前先讀完檔頭**——那 15 條每一個都真的踩過,包括「只會收緊不會
放寬」「qa 紅是預期的但 validator 紅要停」「量 footprint 必須傳設計字級」
這類會讓人白改一輪的。

它印出「某版位連 6 個中文字都放不下」= 那個頁型該降級 clone,
或請設計師把版位改大。不要硬填一個沒人能用的上限。

## 步驟 6|黃金驗收 + 目檢

```
uv run --with python-pptx python engine/release/template_admin.py golden --id light
python engine/release/template_admin.py golden --regen-specs   # 契約改過就要跑
```

通過條件:`golden PASS` 且 **qa 沒有 FAIL、溢出警告為 0**。
迭代單一頁型可加 `--page-types a,b` 省時,收尾必跑全量。

兩條指令沒有先後依賴:`golden` 是**當場依 merged 契約派生**變體、完全不讀
`engine/golden/`;`--regen-specs`(不吃 `--id`)只重寫供 git diff 檢視的契約
快照,由 R11 檢查它與契約同步。

**`fit` 收斂後仍會有一堆 `estimate_overflow()['fits'] == False` 的框,那是正確的。**
判準是「文字範圍不比模板更侵入鄰欄」,不是「每個框都裝得下自己的文字」;
`wrap="none"` 的標籤框文字往右長但仍在卡片底板內、沒碰到鄰欄文字,就不算破版。
不要拿 `fits=False` 當漏報。

然後交設計師,話這樣講:

> 驗收檔在 `ppt_out/golden_light.pptx`。每種頁型兩頁:**單數頁**塞最少內容
> (看有沒有留空格子、殘留範例字),**雙數頁**塞最滿(看有沒有爆框、
> 文字壓到隔欄)。清單項目的文字都帶編號(`1.`、`2.`、`1-1.`),
> 可以順便確認填入順序跟你設計的閱讀方向一致。
> 用 PowerPoint 開,**把不對的頁碼告訴我就好**。

## 步驟 7|收尾

```
python engine/release/template_admin.py pack --tools
python engine/release/template_admin.py pack --id light
shasum -a 256 gpts/dist/tools.zip gpts/dist/template_light.zip
```

同步更新(**手改的計數字串很容易漏,逐項對**):

- `page_map.md`:該列 clone→fill,**還有檔尾的統計句**
  (「共 N 筆:builtin x、fill y、clone z」——上一批就漏了這句)
- `page_types.md` 該節補「已註冊頁型」標記句
- `page_types_registry.md`:「本檔下列 N 種」「這 N 種由 render_deck.py 全自動
  產出」兩處(容量表由 `fit` 自動重生,不用手改)
- `gpts/instructions.md`:版本字串 + 兩處「N 種註冊頁型」
- `manifest.json` 的 `version` 進版
- `engine/REGRESSION.md` R7 的 sha 基準

掃一次確認沒漏:`grep -rn "種註冊頁型\|種全自動\|共 [0-9]* 筆" --include="*.md" .`
最後跑 `lint --all` + `golden` 確認沒改壞。

給設計師的交付摘要用白話:
「多加了 3 種全自動頁面(三大數字 KPI、四點循環、卡片網格),
現在全自動 24 種。之後產檔直接說要哪種版面就好。」

---

## 錯誤 → 修法對照表

| 現象 | 修法 |
| --- | --- |
| lint:全覆蓋原則違反,某 shape 未被覆蓋 | 那個框要嘛綁槽位、要嘛 `delete`、要嘛 `keep`+reason。三者選一,不能不理 |
| lint:inventory 缺第 N 頁快照 | **先確認 manifest 該頁型 mode 已改成 `fill`**,再跑 `freeze`。freeze 只認 mode=fill 的頁,mode 沒改的話重跑幾次都一樣 |
| lint:fill 級必須是已註冊語意頁型 | 三處同步漏了 `PAGE_TYPES`,或頁型名拼錯 |
| lint:圖表未被 chart op 覆蓋 / SmartArt | 補 `chart` op;補不了 → 該頁維持 clone / unsupported |
| validator:字數超過上限(golden 自己的派生) | 契約上限比 golden 派生的變體文字還短 → 跑 `fit` 重量,別手改 |
| golden FAIL:文字壓到別的元素 | 跑 `fit` 收緊;若 fit 說「放不下」= 版位真的不夠,降級或請設計師改版位 |
| golden:溢出警告 | 同上,跑 `fit` |
| fit:某版位連 6 個中文字都放不下 | 該頁型降級 clone,或請設計師把版位做大。不要硬填上限 |
| fit:N 輪仍未收斂 | 有版位在任何字數下都會撞到鄰居 → 降級,或檢查綁定是不是把槽位綁到錯的框 |
| fit:某框對應不到槽位 | 綁定用了工具不認識的 op 組合 → 回報維護者,順手擴充 `slot_shape_map` |
| 目檢:平行欄位長得不一樣 | 各欄格位數不同 → 上限取最少的那個 |
| 目檢:min 頁有空格子 / 斷頭分隔線 | `delete_on_missing` / `sep_ids` 沒配齊 |
| 目檢:編號變成 01 而且折行 | 編號徽章常只有一個字寬 → 契約 `number` 收成 `T(1)` |
| page_types.md 的容量在該模板無法平行表達(例:階梯卡四張分別只有 1/2/3/3 個說明框,而 page_types.md 寫「每張 2–4 個列點」) | 三選一,**不要偷偷放寬也不要硬填**:①砍掉該槽位並在契約與 registry 註明理由 ②整頁降級 clone ③回頭問設計師要不要改版位 |
| `add_textbox` 的框跑出頁面或壓到頁碼 | 那個框的 x/y/w/h 是綁定自己宣告的,**lint 不驗**。自己算:右緣不得進頁碼清除窗(x>11.2)、不得超出 13.33 吋 |
| register:light 回歸紅 / isolation 越界 | 不准註冊。多半動到共用檔 → 回報維護者 |

## 設計師回報 → 你要做什麼(對照表)

設計師只會給你頁碼和白話描述。翻譯規則:

| 她說 | 意思 | 你做 |
| --- | --- | --- |
| 「第 8 頁字疊在一起」 | 文字壓到鄰欄 | 跑 `fit`;仍不行 → 提議降級或改版位 |
| 「第 4 頁三欄不一樣」 | 平行欄位格位數不同 | 上限取最少欄的格位數 |
| 「第 3 頁有空白格子」 | min 變體刪格沒配齊 | 補 `delete_on_missing` |
| 「字變小了 / 大小不一致」 | 被縮字(不該再發生) | 跑 `fit`;若 fit 說收斂了 → 回報維護者,可能是新的量測死角 |
| 「這頁還留著範例文字」 | 契約外的內容性元素沒刪 | 補 `delete` |
| 「順序跑掉了」 | 綁定的格位順序與閱讀方向不符 | 用 golden 的 `1. 2. 3.` 前綴對照,重排 `list` 的 items 順序 |
| 「這頁我不要了」 | 降級 | manifest 改回 `clone`,三處同步的契約可留(無害)或一併移除 |

## 迭代與降級

- **同一頁型修三輪還不綠 → 停手,提議降級 clone。** 硬修下去只會越改越糟。
- **部分成功是合法結局**:支援矩陣本來就為此設計,不必逼全部頁型全綠。
- 中途停:改動都在檔案裡,下次觸發本 skill 從 `lint --all` 開始接續。
- **只有三類問題可以問設計師**:(a) 要加哪幾頁 (b) 目檢結果
  (c) 降級/中止決策。shape id、slot 名、JSON、op 細節一律不拋給她。
