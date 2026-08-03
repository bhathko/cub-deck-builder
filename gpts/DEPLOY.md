# DEPLOY — 發版操作稿(一頁照著做)

> **用途**:把 repo 目前狀態推上 GPT Builder 的**逐步操作稿**,含可直接貼給
> GPT 的驗收指令原文。
> **讀者**:GPT 擁有者/管理者(只有你有 Builder 權限)。
> **何時讀**:要發版時。日常維護規則見 [`../docs/MAINTENANCE.md`](../docs/MAINTENANCE.md);
> 建置背景與能力說明見 [`README.md`](README.md)。

**含刪除動作,別只上傳不刪**:v2.0 起 Knowledge 佈局改為「模板包」zip,
舊檔留著會讓 GPT 走錯路徑;佈局已換過的部署,刪除步驟略過即可。

---

## Step 0|先在本機確認要上傳的東西是最新的

```
python engine/release/template_admin.py pack --tools
python engine/release/template_admin.py pack --id light
python engine/release/template_admin.py lint --all
shasum -a 256 gpts/dist/tools.zip gpts/dist/template_light.zip
```

最後一行的兩個 sha 要跟 [`../engine/REGRESSION.md`](../engine/REGRESSION.md)
R7 的基準值一致(打包是可重現的,內容沒變 sha 就不會變)。不一致代表 repo
有未打包的改動,先處理完再上傳。

## Step 1|Builder → 名稱、描述、開場白、Instructions

**① Instructions**:貼上 [`instructions.md`](instructions.md) **分隔線以下的全文**
(整段取代舊的,不要只補幾句)。開頭第一行是「你是公司內部的『簡報產生器』
(版本 …)」並含「可用模板包:light@…」——**版本代號一律以 `instructions.md`
當下的內容為準**(本檔刻意不抄那兩個數字:抄了就會過期,而過期的數字會讓人
誤判發版失敗)。

**② Name**(GPT 名稱):

```
簡報產生器
```

**③ Description**(卡片上的一句話介紹;**不要寫版本號**,會過期):

```
把大綱或 slide_spec.json 變成符合公司視覺規範的 16:9 繁體中文簡報。模板、背景、
logo 與頁型規則全部內建,你不需要上傳任何檔案;產檔前後都有閘門把關,內容只用
你給的文字,不自己編數字。
```

**④ Conversation starters**(對話開場白,就是使用者看到的四個提示按鈕。
四支入口各一條,順序照使用頻率;斜線指令只是同義觸發詞,使用者不打也能用):

```
貼上大綱,直接幫我產一份簡報
```

```
先幫我看看這份大綱能做出什麼、要怎麼改
```

```
幫我把大綱補豐富一點再產檔
```

```
我有 slide_spec.json,幫我驗證並產檔
```

對應關係(改開場白時要對得上 instructions 的四種模式,不要自創第五種):

| 開場白 | 進入的模式 | 特性 |
| --- | --- | --- |
| 直接產一份簡報 | 一鍵產檔(`/outline-to-ppt`) | 預設路徑;中途不確認、不拋選單 |
| 看看能做出什麼 | 健檢(`/check-outline`) | **唯讀**:出報告不改稿不產檔,結尾集中提問 |
| 補豐富再產檔 | 豐富訪談(`/enrich-outline`) | 增補行標 `[補]`,核准後才產檔 |
| 有 slide_spec.json | 直供 JSON 模式 | 追溯關閉,內容正確性由 JSON 作者負責 |

## Step 2|Builder → Knowledge:先刪、再傳

**刪掉這兩個舊檔**(v2.0 已不用,留著會讓 GPT 走錯路徑):

- `assets.zip`
- `light_template.pptx`

**上傳/覆蓋這 12 個檔**(同名檔一律「刪舊再傳新」,Builder 不會自動覆蓋):

| 來源路徑 | 檔名 |
| --- | --- |
| `engine/rules/` | `validate_slide_spec_gpts.py` |
| `engine/rules/` | `slide_spec.schema.json` |
| `engine/rules/` | `page_types_registry.md` |
| `engine/rules/` | `page_types.md` |
| `engine/rules/` | `style_guide.md` |
| `engine/rules/` | `outline_to_ppt_skill.md` |
| `engine/rules/` | `enrich_outline_skill.md` |
| `engine/rules/` | `check_outline_skill.md` |
| `engine/rules/` | `slide_spec.example.json` |
| `engine/rules/` | `slide_spec.bad.example.json` |
| `gpts/dist/` | `tools.zip` |
| `gpts/dist/` | `template_light.zip` |

傳完數一次:**Knowledge 應該剛好 12 個檔**(上限 20;每加一個新模板 +1)。
GPTs 只有三支流程需要規則本體(健檢/豐富/產檔);`register-template` 與
`add-page-types` 是維護者本機專用,**不上傳**。

## Step 3|Capabilities 與 Model(確認,不要動錯)

- ✅ Code Interpreter & Data Analysis(**必開**,整條流程靠它)
- ❌ Web Browsing(關)
- ❌ 圖片生成(關;本流程不生圖)
- ⚠ **Recommended Model 指定最強可用模型**——這是 FEEDBACK #1/#2 的根因:
  未指定時會被路由到輕量模型,出現「不看 /mnt/data 就說做不到」「反過來要你
  上傳工具」「改用 python-pptx 手產」等整套失敗行為。

---

## Step 4|驗收:可直接貼給 GPT 的指令(逐條跑完)

> 每條都要看到「預期」才算過。任何一條沒過就先別通知團隊。

**① 版本自證**

```
你現在是哪一版?本次會用哪個模板包?
```

預期:回答的兩個代號與 `instructions.md` 第一行完全一致(模板包版本同時要對得上
`engine/templates/INDEX.md` 的 manifest version)。**對不上就是 Step 1/2 沒生效**,
回頭重做。

**② 環境準備 + 閘門正反例**

```
執行環境準備,然後用知識庫的 slide_spec.bad.example.json 和 slide_spec.example.json
各跑一次驗證器,貼出完整輸出。
```

預期:先建 `/mnt/data/tools` 解 tools.zip、建 `/mnt/data/templates/light` 解
template_light.zip,並印出 manifest 的 template_id 與 version;bad example
**FAIL** 並列出一串 ERROR,example **PASS**(可有 WARN)。

**③ 模板讀取 + 骨架**

```
跑 inspect_template.py --summary,再 --page 35 給我看。
然後用 make_skeleton.py 產一份 cover,agenda,closing 骨架並跑驗證器。
```

預期:列出模板頁摘要(頁數與 `engine/templates/light/manifest.json` 的
`page_count` 一致——本檔刻意不抄數字,抄了就會過期)與第 35 頁形狀樹;
骨架驗證直接 PASS。

**④ 直供 JSON 產檔**

```
用知識庫的 slide_spec.example.json 直接產出 PPT。
```

預期:管線 PASS 並給下載連結。**開 PowerPoint 檢查**:背景/logo 正確、
版面貼近模板、文字可編輯、沒有殘留 Section。

**⑤ 圖表頁(圖表數據替換能力)**

```
產一份只有一頁的簡報,頁型用 data_line_trend_comparison,
時間點 1-6 月,兩組數列(方案A: 12.5/14.2/15.8/17.1/19.4/22.0、
方案B: 11.0/11.8/12.1/13.0/13.6/14.2),下面兩列說明各三格自己編。
```

預期:PASS;開檔確認**折線圖的數據真的換成你給的數字**(不是模板原本的
示範數據),圖例是「方案A/方案B」。這是 Phase 4 的核心能力,務必驗。

**⑤b 容量閘門與碰撞檢查(v2.1 新增,務必驗)**

```
用 data_three_number_kpis 產一頁,三個 KPI 的說明文字各寫 30 個中文字。
```

預期:**驗證器 FAIL**,訊息類似 `字數 30 超過上限 12`。這是對的——
light 那個版位在設計字級下只裝得下 12 字。**它不該幫你縮字後放行**。
接著要求它照上限改寫並重跑,應該一次就 PASS 且開檔字級與模板一致。

> 這條在驗「不縮字」原則有沒有生效。舊版會靜默把字縮到 12pt 然後宣告 PASS,
> 產出的頁面一頁三種字級。詳見 `../engine/REGRESSION.md` R12。

**⑥ 一鍵大綱(不打任何指令)**

```
(直接貼上 engine/examples/05_outline_to_ppt_source.md 全文,前面什麼都不加)
```

預期:GPT 自動走一鍵產檔,中途不問你確認、不拋 A/B 選單;過程先出現
`page_type_candidates.json`(含 `not_nominated` 整庫覆蓋審視)與
`make_skeleton --plan` 的選型結果,之後才填內容;最後同時給
slide_spec.json 與 .pptx。再用 `/outline-to-ppt` 前綴重測一次,行為必須相同。

**⑦ 內容忠實邊界**

```
(把 ⑥ 的大綱刪掉日期與報告人後重貼)
```

預期:封面保留,缺的欄位填「待補充」而**不是捏造**;交付摘要列出待補清單。

**⑧ 修正循環(反「一擋就停」)**

```
(在大綱裡塞一段刻意超過字數上限的長句後重貼)
```

預期:被閘門擋下後**自動縮短/拆頁並整條重跑**,三輪內修好照常交付,
並回報修了什麼——**不可以**宣稱「無法繼續」或把問題丟回給你。

**⑨ 豐富訪談(/enrich-outline)**

```
/enrich-outline(接著貼一份只有三四句、平鋪直敘的單薄大綱)
```

預期:先存 `/mnt/data/outline_original.txt`,在聊天中逐項提案並標明「解鎖哪個
頁型」;數據類只提問、**不代填數字**。核准後產出的核准版裡,新增/改寫行都有
行首 `[補] ` 標記,管線帶 `--original`,稽核報告印「豐富鏈:開(增補 N 行,
其中含數字 M 行)」。接著要求它「不帶 --original 重跑」——稽核必須 FAIL 並
指出來源含 `[補]` 標記卻缺原稿鏈。

---

**⑪ 容量問答(數字只有一個來源)**

```
data_three_number_kpis 的 value 上限是幾個字?你是從哪裡查到的?
```

預期:答 **5 字**,並說明查自 `page_types_registry.md` 檔尾容量表(或跑
`tools/capacity_probe.py --list-caps`)。**若它從各節散文報一個數字就是錯的**
——散文已不寫數字,報得出來代表它在編。

**⑫ 產檔後自檢的兩條硬線**

```
產一份 3 頁的簡報(封面+一頁三大數字 KPI+封底),KPI 那頁的數字請故意寫超過上限,
然後照常跑完整管線,把每一階段輸出貼出來。
```

預期:**停在 validator**(字數超限 ERROR),不會硬產。接著請它改回合法值重跑,
應 4/4 PASS。重點看它**沒有**自己把字級改小遷就——qa 現在把「字級被縮小」與
「形狀跑出投影片」都列為 FAIL。

**⑬ 健檢入口**

```
幫我看看這份大綱能做出什麼(貼一段 5-6 行、其中一行明顯超長的內容)
```

預期:走健檢模式出六節報告、**不產檔**;字數判斷引用 `capacity_probe.py` 的
實測輸出(看得到 PASS/FAIL 行),超長那行給出不動數字的縮寫示範;結尾集中問
`【NEED HUMAN】`(≤5 題)並給三選一下一步。

## Step 5|收尾

- [ ] 驗收全過 → 通知團隊可以用了,附上 `instructions.md` 第一行的版本代號
- [ ] Name / Description / 四條開場白與 Step 1 的文字一致(改過 instructions
      的模式就要回頭對一次,開場白不得指向不存在的模式)
- [ ] 任何一條沒過 → 記進 [`../docs/FEEDBACK.md`](../docs/FEEDBACK.md)
      (附版本、你貼的指令、GPT 的實際輸出),回報給維護者
- [ ] 之後每次發版,重跑 ①②④⑪ 當快速回歸;改過模板就加 ⑤、改過容量就加 ⑫

> 完整能力邊界與已知限制(要向主管說明時)見 [`README.md`](README.md)
> 的「誠實的限制」節。
