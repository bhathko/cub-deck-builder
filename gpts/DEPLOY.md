# DEPLOY — v2.0 換裝操作稿(一頁照著做)

> **用途**:把 repo 目前狀態推上 GPT Builder 的**逐步操作稿**,含可直接貼給
> GPT 的驗收指令原文。
> **讀者**:GPT 擁有者/管理者(只有你有 Builder 權限)。
> **何時讀**:要發版時。日常維護規則見 [`../docs/MAINTENANCE.md`](../docs/MAINTENANCE.md);
> 建置背景與能力說明見 [`README.md`](README.md)。

**本次是「換裝」而非新建**:Knowledge 的佈局變了(模板改成「模板包」zip),
所以有**刪除**動作,別只上傳不刪。

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

## Step 1|Builder → Instructions

貼上 [`instructions.md`](instructions.md) **分隔線以下的全文**(整段取代舊的,
不要只補幾句)。開頭第一行應該是「你是公司內部的『簡報產生器』(版本
v2.3-20260727…)」,並含「可用模板包:light@2026-07-27.1」。

## Step 2|Builder → Knowledge:先刪、再傳

**刪掉這兩個舊檔**(v2.0 已不用,留著會讓 GPT 走錯路徑):

- `assets.zip`
- `light_template.pptx`

**上傳/覆蓋這 10 個檔**(同名檔一律「刪舊再傳新」,Builder 不會自動覆蓋):

| 來源路徑 | 檔名 |
| --- | --- |
| `engine/rules/` | `validate_slide_spec_gpts.py` |
| `engine/rules/` | `slide_spec.schema.json` |
| `engine/rules/` | `page_types_registry.md` |
| `engine/rules/` | `page_types.md` |
| `engine/rules/` | `style_guide.md` |
| `engine/rules/` | `outline_to_ppt_skill.md` |
| `engine/rules/` | `slide_spec.example.json` |
| `engine/rules/` | `slide_spec.bad.example.json` |
| `gpts/dist/` | `tools.zip` |
| `gpts/dist/` | `template_light.zip` |

傳完數一次:**Knowledge 應該剛好 10 個檔**(上限 20;每加一個新模板 +1)。

## Step 3|Capabilities 與 Model(確認,不要動錯)

- ✅ Code Interpreter & Data Analysis(**必開**,整條流程靠它)
- ❌ Web Browsing(關)
- ❌ 圖片生成(關;本流程不生圖)
- ⚠ **Recommended Model 指定最強可用模型**——這是 FEEDBACK #1/#2 的根因:
  未指定時會被路由到輕量模型,出現「不看 /mnt/data 就說做不到」「反過來要你
  上傳工具」「改用 python-pptx 手產」等整套失敗行為。

---

## Step 4|驗收:9 條可直接貼給 GPT 的指令

> 每條都要看到「預期」才算過。任何一條沒過就先別通知團隊。

**① 版本自證**

```
你現在是哪一版?本次會用哪個模板包?
```

預期:回答 `v2.3-20260727` 與 `light@2026-07-27.1`。**版本不對就是 Step 1/2
沒生效**,回頭重做。

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

預期:列出模板頁摘要(59 頁)與第 35 頁形狀樹;骨架驗證直接 PASS。

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

預期:GPT 自動走一鍵產檔,中途不問你確認、不拋 A/B 選單,最後同時給
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

---

## Step 5|收尾

- [ ] 9 條全過 → 通知團隊可以用了,附上版本代號 `v2.3-20260727`
- [ ] 任何一條沒過 → 記進 [`../docs/FEEDBACK.md`](../docs/FEEDBACK.md)
      (附版本、你貼的指令、GPT 的實際輸出),回報給維護者
- [ ] 之後每次發版,重跑 ①②④ 當快速回歸;改過模板就加 ⑤

> 完整能力邊界與已知限制(要向主管說明時)見 [`README.md`](README.md)
> 的「誠實的限制」節。
