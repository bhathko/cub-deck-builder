# DEPLOY — 實驗B(自由版)發版操作稿

> **用途**:把「實驗B|自由版」推上 GPT Builder 的逐步操作稿,給設計師試用比對。
> **定位**:封面/目錄/封底走公司模板與工具鏈,中間內容頁由 GPT 用 python-pptx
> 自由設計(content_bg 底圖 + logo 固定左下角)。與實驗A 的差異見 [`README.md`](README.md)。
> **注意**:這是**獨立新建的 GPT**,不要動到正式的「簡報產生器」。

---

## Step 0|本機確認 dist 內容

- `tools.zip` 直接複製自 `gpts/dist/`(實驗B 不改任何工具),sha 應與正式版一致。
- `template_light.zip` 是 **content_bg 底圖改版**(`light@2026-08-03.2-expA`,
  **與實驗A 共用同一份**):內容頁 layout「只有標題」「空白(白底)」改為
  content_bg 滿版底圖+左下角 logo,封面/目錄/封底未動;改版細節見
  `../gpts_experiment_a/README.md`。

```
shasum -a 256 gpts_experiment_b/dist/tools.zip gpts/dist/tools.zip
shasum -a 256 gpts_experiment_b/dist/template_light.zip gpts_experiment_a/dist/template_light.zip
```

第一組兩行相同、第二組兩行相同即可。

## Step 1|Builder → 名稱、描述、開場白、Instructions

**① Instructions**:貼上本資料夾 [`instructions.md`](instructions.md)
**分隔線以下的全文**。第一行版本代號應為 `v1.0-expB-20260803` 開頭。

**② Name**:

```
簡報產生器(實驗B|自由版)
```

**③ Description**:

```
【設計師試用版B】封面/目錄/封底用公司模板,中間頁由 AI 自由設計:公司制式
內容底圖、logo 固定左下角、品牌色與字體照規範。版面不受頁型庫限制,但僅有
輕量自檢,請務必人工目檢。
```

**④ Conversation starters**(三支入口):

```
貼上大綱,幫我產一份簡報(中間頁自由設計)
```

```
先講你打算怎麼排這份大綱的中間頁,再產檔
```

```
我有三頁結構的 slide_spec.json,幫我先產結構頁
```

## Step 2|Builder → Knowledge(5 個檔)

| 來源路徑 | 檔名 |
| --- | --- |
| `engine/rules/` | `validate_slide_spec_gpts.py` |
| `gpts_experiment_b/` | `freeform_playbook.md` |
| `gpts_experiment_b/` | `spec_structural.example.json` |
| `gpts_experiment_b/dist/` | `tools.zip` |
| `gpts_experiment_b/dist/` | `template_light.zip` |

實驗B 不上傳頁型庫規則(page_types*.md、style_guide.md、三支 skill 檔)——
中間頁不走頁型庫,傳了反而讓模型走錯路徑。

## Step 3|Capabilities 與 Model

- ✅ Code Interpreter & Data Analysis(必開)
- ❌ Web Browsing、❌ 圖片生成
- ⚠ Recommended Model 指定最強可用模型(自由版對模型能力更敏感——版面品質
  完全取決於模型發揮,輕量模型會直接把版面畫壞)

## Step 4|驗收(逐條貼給 GPT)

**① 版本自證**

```
你現在是哪一版?本次會用哪個模板包?
```

預期:`v1.0-expB-20260803` + `light@2026-08-03.1`。

**② 環境準備**

```
執行環境準備,貼出輸出。
```

預期:解 tools.zip 到 /mnt/data/tools、解 template_light.zip 到
/mnt/data/templates/light,印出 manifest 的 template_id 與 version。

**③ 一鍵大綱(設計師比對用的同一份輸入)**

```
(直接貼上 examples/sample_outline.md 全文,前面什麼都不加)
```

預期:列章節與版面構想後直接續跑;結構三頁 validator + qa_check PASS 的輸出
可見;自由頁畫完有 QA-lite 輸出;交付附頁面清單、待補清單與目檢提醒。
**開 PowerPoint 逐頁檢查**:每張中間頁背景都要是 content_bg 底圖(與實驗A
中間頁相同)、logo 在左下角、頁碼右下、只用品牌色、中文字是微軟正黑體
(不是明體 fallback)、文字都可編輯。

**④ 結構頁閘門仍有效**

```
封面主標題請用「智慧客服平台優化與升級提案」這個完整名稱產一份
```

預期:cover 主標超過容量上限時 validator **FAIL**,GPT 回報並提出縮短建議,
不硬產。(結構三頁的守門在實驗B 仍然存在,只有中間頁是自由的。)

**⑤ 內容忠實邊界**

```
(把 sample_outline.md 刪掉日期與報告人後重貼)
```

預期:缺的欄位填「待補充」而不是捏造;交付摘要列出待補清單。
**注意**:實驗B 的中間頁忠實只靠 prompt 約束,驗收時抽 2–3 頁把頁面文字
與大綱原文對一遍,有自行加料就記進回饋。

## Step 5|交給設計師

- [ ] 五條驗收全過 → 把 GPT 連結給設計師,附 `examples/sample_outline.md`
      (請他同一份大綱各餵 實驗A 與 實驗B 一次,並排目檢比對)
- [ ] `examples/demo_deck_expB.pptx` 是本流程預期產出的實測樣張,可先給設計師開檔
- [ ] 提醒設計師:實驗B **每次重跑版面都可能不同**,建議同一份大綱跑兩次,
      看穩定度也是評估項目
- [ ] 試用回饋記進 [`../docs/FEEDBACK.md`](../docs/FEEDBACK.md)(附版本、指令、實際輸出)
