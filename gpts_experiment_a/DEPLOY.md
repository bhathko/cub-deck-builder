# DEPLOY — 實驗A(守門版)發版操作稿

> **用途**:把「實驗A|守門版」推上 GPT Builder 的逐步操作稿,給設計師試用比對。
> **定位**:現行守門流程的對照組——封面/目錄/封底三頁固定,中間頁從內建頁型庫
> 自動選版,全程閘門把關。與實驗B 的差異見 [`README.md`](README.md)。
> **注意**:這是**獨立新建的 GPT**,不要動到正式的「簡報產生器」。

---

## Step 0|本機確認 dist 內容

- `tools.zip` 直接複製自 `gpts/dist/`(實驗A 不改任何工具),sha 應與正式版一致。
- `template_light.zip` 是**content_bg 底圖改版**(`light@2026-08-03.2-expA`):
  在正式版 light@2026-08-03.1 上把內容頁 layout「只有標題」「空白(白底)」設
  `showMasterSp=0`(藏母片原底圖與角落裝飾),鋪上
  `assets/backgrounds/content_bg.png` 滿版為背景,再補回母片同一顆 logo 於
  左下角(0.31", 6.98",與封面/目錄同位);封面/目錄/封底 layout 未動。
  manifest 的 version 與 template_sha256 已同步。
  **與實驗B 的 template_light.zip 完全相同**。

```
shasum -a 256 gpts_experiment_a/dist/tools.zip gpts/dist/tools.zip
shasum -a 256 gpts_experiment_a/dist/template_light.zip gpts_experiment_b/dist/template_light.zip
```

第一組兩行相同、第二組兩行相同即可。

## Step 1|Builder → 名稱、描述、開場白、Instructions

**① Instructions**:貼上本資料夾 [`instructions.md`](instructions.md)
**分隔線以下的全文**。第一行版本代號應為 `v2.21-expA-20260803` 開頭。

**② Name**:

```
簡報產生器(實驗A|守門版)
```

**③ Description**:

```
【設計師試用版A】把大綱變成公司視覺規範的 16:9 簡報。封面/目錄/封底固定,
中間頁由系統從內建頁型庫自動選版;產檔前後都有閘門把關,內容只用你給的文字。
```

**④ Conversation starters**(與正式版相同的四支入口):

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

## Step 2|Builder → Knowledge(12 個檔)

與正式版相同的 12 檔;dist 兩包從**本資料夾**取:

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
| `gpts_experiment_a/dist/` | `tools.zip` |
| `gpts_experiment_a/dist/` | `template_light.zip` |

## Step 3|Capabilities 與 Model

- ✅ Code Interpreter & Data Analysis(必開)
- ❌ Web Browsing、❌ 圖片生成
- ⚠ Recommended Model 指定最強可用模型(未指定會被路由到輕量模型,
  出現整套「說做不到」的失敗行為,見 `docs/FEEDBACK.md` #1/#2)

## Step 4|驗收(快速版,逐條貼給 GPT)

**① 版本自證**

```
你現在是哪一版?本次會用哪個模板包?
```

預期:`v2.21-expA-20260803` + `light@2026-08-03.2-expA`(以 instructions.md 第一行為準)。

**② 環境準備 + 閘門正反例**

```
執行環境準備,然後用知識庫的 slide_spec.bad.example.json 和 slide_spec.example.json
各跑一次驗證器,貼出完整輸出。
```

預期:bad **FAIL** 列出 ERROR;example **PASS**(可有 WARN)。

**③ 一鍵大綱(設計師比對用的同一份輸入)**

```
(直接貼上 examples/sample_outline.md 全文,前面什麼都不加)
```

預期:自動走一鍵產檔,不問確認、不拋選單,最後同時給 slide_spec.json 與 .pptx。
**開 PowerPoint 目檢**:封面/目錄/封底維持公司模板原樣;**每張中間頁背景
都要是 content_bg 底圖、logo 在左下角**,版位與卡片樣式貼近模板對應頁。

**④ 閘門有效性**

```
用 data_three_number_kpis 產一頁,三個 KPI 的說明文字各寫 30 個中文字。
```

預期:驗證器 **FAIL**(字數超上限),不硬產、不縮字放行。

> 完整驗收電池(圖表數據、豐富訪談、健檢等)見 [`../gpts/DEPLOY.md`](../gpts/DEPLOY.md)
> Step 4;實驗包跑完上面四條即可交給設計師。

## Step 5|交給設計師

- [ ] 四條驗收全過 → 把 GPT 連結給設計師,附 `examples/sample_outline.md`
      (請他同一份大綱各餵 實驗A 與 實驗B 一次,並排目檢比對)
- [ ] `examples/demo_deck_expA.pptx` 是本包預期產出的實測樣張,可先給設計師開檔
- [ ] 試用回饋記進 [`../docs/FEEDBACK.md`](../docs/FEEDBACK.md)(附版本、指令、實際輸出)
