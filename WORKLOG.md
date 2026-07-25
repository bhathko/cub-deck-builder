# WORKLOG — gpts/ 建置包的來龍去脈

> 給接手的 agent / 維護者:這份文件記錄 gpts/ 目錄從無到有的決策過程、
> 每次方向修正的原因、已知風險與未驗證項。改東西前先讀這份 + `README.md`。
> 產出日期:2026-07-20,產出者:Claude Code(與使用者逐輪對話迭代)。
> ⚠ 2026-07-20 深夜曾發生誤刪與重建,見 §11。

## 0. 需求背景

使用者的主管希望:設計師透過 ChatGPT 給 spec 就能產出 PPT,而且要包成 GPTs
讓大家直接用。本 repo 原有一套 spec-first 管線(branch `feat/slide-spec-gate`):

- 內容 SSOT `my_project/source/slides.md` → `my_project/slide_spec.json`
  →〔`fallback/validate_slide_spec.py` 硬閘門,exit 0 才 render〕→ native-pptx。
- 主力路徑(baoyu-slide-deck,Codex imagegen 圖生圖)**無法**搬進 GPTs:
  公司政策生圖只准 Codex imagegen,且 GPTs 沒有等價工具。
- 所以 GPTs 版移植的是 **fallback 路徑**(不生圖、全部 PowerPoint 可編輯物件,
  不觸犯生圖政策)。

## 1. 核心洞察(整個設計的支點)

1. `validate_slide_spec.py` **只用 Python 標準庫** → 可以搬進 GPTs 知識庫,
   由 Code Interpreter 實際執行。閘門因此是「真的會跑的程式」,不是 prompt 約束。
   這是 GPTs 版與一般「叫 ChatGPT 做 PPT」的本質差異,對主管簡報時的賣點。
2. `fallback/generate_review_deck.py` 是**寫死 10 頁的一次性腳本,不是通用
   renderer**(甚至含硬編碼內容)。渲染端無現成資產可搬 → 先靠規則文件框住
   模型現寫程式碼(v1.1),後來全面工具化(v1.2,見 §7)。
3. repo 現狀:`page_types.md` 頁型庫有 40+ 種,但驗證器 `PAGE_TYPES` 只註冊 10 種。
   這個落差是 repo 本來就有的,GPTs 版用「兩級閘門」處理(見 §3)。
4. GPTs 的限制,影響設計的三條:
   - 知識庫圖檔**沒有視覺理解** → `rendered_examples/` 58 張參考圖不上傳(無效),
     版面保真改靠「用 python-pptx 讀 light_template.pptx 的形狀幾何/複製頁」。
   - Code Interpreter 沙箱**沒有中文字體** → 無法產可靠預覽圖;pptx 本身沒問題
     (檔案只存字體名稱,在使用者機器上正常)。
   - GPTs **沒有跨對話記憶** → 回饋必須「規則化」寫回 instructions/knowledge
     才會永久生效(README 回饋流程節的理論基礎)。

## 2. 演進史

### v0:slides.md 全流程版(已廢棄)
照搬 repo 流程:使用者貼內容 → GPT 寫 slides.md → 產 spec → 驗證(含 provenance)
→ 產檔。**廢棄原因**:使用者明確聲明定位——「所有檔案隨 GPTs 內建,使用者只給
一份合規 JSON 就產出 PPT」。slides.md 是多餘的中間層。

### v1:JSON 直供版(現行架構)
- 輸入 = 使用者的 slide_spec.json,其他全部內建。
- **取捨**:沒有 slides.md,provenance 追溯自動關閉(程式行為:找不到 → WARN +
  略過)。合理化:JSON 是人寫的,內容正確性由撰寫者負責;閘門仍硬擋結構/數量/
  字數/頁碼/素材。v1.4 起直供 JSON 必須以 `--slides` 明確指向本次獨一且已確認
  不存在的路徑,不可因沙箱殘留 `/mnt/data/slides.md` 而誤開追溯。
- `page_types_registry.md` 改寫成使用者導向的「slide_spec.json 撰寫指南」。
- 絕對規則:GPT 不可增刪改使用者 JSON 的任何文字/數字;修正需展示差異取得同意。
- **v1.3 內容模式**(使用者給大綱/段落):GPT 切頁選頁型 → 原文逐字存
  slides.md → 產 spec → 驗證帶 `--slides` **重新開啟已註冊 slots 的來源比對** →
  每頁摘要確認後才產檔。三條入口(合規 JSON/不合規 JSON 修正循環/內容模式)
  收斂到同一個確定性出口。
- **v1.4 一鍵大綱模式**(2026-07-21):`/outline-to-ppt` 將內容模式改成單次授權,
  不再要求切頁或產檔確認;由獨立繁中 Knowledge workflow 使用 make_skeleton、
  `--slides --registered-only --strict`、render 與 QA 一次完成。只允許十種註冊頁型,
  來源不足時安全停止。

### v1 內的兩次重要修正
1. **模板生成方式**:light_template.pptx + 完整 page_types.md 加入知識庫;
   版面以模板為準。
2. **複製頁而非直接改模板頁**(使用者抓到的 bug):同一參考頁可能被多個 spec 頁
   使用。規則:對每頁 spec 先 deepcopy 參考頁成新投影片(relationships 一併複製,
   否則圖破),只在複本上改字;最後刪除所有模板原頁、清 Section、按 number 排序。

## 3. 兩級閘門設計(為什麼驗證器要 fork)

`knowledge/validate_slide_spec_gpts.py` 相對原 repo 版的刻意差異:
1. 路徑改為 CLI 參數(`--spec/--slides/--asset-dir`,預設 /mnt/data)。
2. **兩級閘門**:`page_type` 在 `PAGE_TYPES` 註冊(10 種)→ 完整槽位契約檢查;
   未註冊但在 page_types.md 頁型庫 → 降級為 `generic_provenance()` 泛用檢查
   (有 slides.md 時比對 slots 數字與文字;純 JSON 模式下實際只驗素材存在 + slots 為
   dict)。數字實作是子字串查找,例如來源 `50` 可能誤讓輸出 `5` 通過;
   `--registered-only` 可恢復嚴格頁型行為,但不會改變這個數字限制。
   **動機**:不 fork 的話 40+ 種頁型全不能用。**代價**:未註冊頁型容量靠模型
   自律,長期正解是把常用頁型補進 `PAGE_TYPES`。
3. JSON 讀取用 utf-8-sig(容忍 Windows BOM,使用者上傳常見)。

## 4. 檔案清單與角色

見 `README.md` 的表格。特別說明:
- `knowledge/`(11 檔)= 要上傳 GPTs 的;其餘留在 repo。
- 檔案形式的判斷準則:**模型要讀的 → 獨立文件(走檢索);程式要讀的 →
  可打包 zip(走沙箱檔案系統)**。assets.zip/tools.zip 因此打包(省檔位、
  保留目錄結構、更新原子性),規則文件因此散放。
- instructions 開頭埋版本字串(目前 `v1.11-20260721`),發版時更新。

## 5. 早期風險(2026-07-20 實測後全數解除)

1. ~~本機沒有 Python,可攜版驗證器從未實跑過~~ **已解除**:見 §7.1。
2. ~~兩份手寫 example 未經驗證器實跑~~ **已解除**:01/03 皆 PASS。
3. ~~light_template.pptx 內部結構未逐頁檢視~~ **已解除**:59 頁無 SmartArt;
   25-27、31 頁含 chart(文字可換、圖表數據不可)。
4. ~~deepcopy 複製投影片是最可能翻車的環節~~ **已解除**:固化成
   `tools/pptx_toolkit.py` 的 `clone_slide()`,帶圖頁複製實測通過。
5. **閘門是指示強制,非系統強制**:模型可能跳過驗證。緩解=要求貼 PASS 輸出;
   ~~終極解=GPTs Actions 接自家 API~~(2026-07-21 確認 **Actions 因公司政策
   禁用**,強制上限=沙箱內確定性腳本;v1.8 以 run_pipeline 單一入口緩解)。
6. bad example 的違規點在「無 slides.md + 兩級閘門」下仍會 FAIL(實測 7 ERROR)。

## 6. 同步鐵律(改規則時)

> `gpts/knowledge/` 即單一真相來源,**三處同步**:

1. `gpts/knowledge/validate_slide_spec_gpts.py` 的 `PAGE_TYPES`(真相來源)
2. `gpts/knowledge/slide_spec.schema.json` 的 enum
3. `gpts/knowledge/page_types_registry.md`(1 的人類可讀版)

素材改版:改 `gpts/assets_src/` → 複製為名為 `assets` 的資料夾重打包
`knowledge/assets.zip`(zip 內根目錄必須叫 assets,spec 路徑才成立)。
工具改版:改 `gpts/tools/` → 重打包 `knowledge/tools.zip`。
改完 → 重新上傳知識庫 → 更新 instructions 版本字串 → 跑驗收 → 記入
FEEDBACK.md 發版。

## 7. 工具層(v1.1,2026-07-20)

六支腳本 + 速查卡放 `gpts/tools/`,打包成 `knowledge/tools.zip`。設計目標=
「精準產出 + 省 token + 不進 QA 死循環」:

- **模型唯一手產物 = render_plan.json**(v1.2 起僅未涵蓋頁型需要)。所有機械
  動作(clone 含 rels 重映射、換字保留樣式、刪頁、排序、清 Section、頁碼、
  內建版面)都在腳本裡。
- **反循環機制**:render_deck 冪等——每次從模板整檔重生,錯誤一律回到
  「改輸入的某一條」再重跑;不存在「刪壞頁補一頁」的累積損傷路徑。
  qa_check 是產檔後第二道程式閘門,只印問題。
- **省 token**:inspect_template 只准 --summary(一頁一行)或 --page N;
  全量 dump 進檔案不進對話。README_TOOLS.md 是模型速查卡,鐵律寫死。
- cover/agenda/closing 的 builtin 版面座標移植自 repo `generate_review_deck.py`
  (頁碼改依 style_guide 用 28pt,repo 腳本的 14pt 與 style_guide 牴觸,
  以 style_guide 為準)。
- make_skeleton 從 validate_slide_spec_gpts import PAGE_TYPES(單一來源);
  兩檔必須同在 /mnt/data 或父目錄。

### 7.1 本機實測結果(2026-07-20,Python 3.14.6 + python-pptx 1.0.2)

在 scratchpad 搭了模擬 /mnt/data 的沙箱,**整條工具鏈實測通過**:

- 驗證器:repo 正例 PASS(追溯開)、壞例 FAIL(7 ERROR,含捏造數字);
  examples 01/03 PASS;兩級閘門 WARN 如設計;make_skeleton 混合骨架直接 PASS。
- 全流程:example 01(4 頁)→ render_plan(p3 clone 模板 17 頁,11 edits +
  16 deletes)→ render_deck 一次 OK → qa_check PASS 零警告。逐頁驗過:
  頁序/16:9/替換全中/佔位元素清空/模板頁碼清掉補 28pt/Section 移除。
- clone 帶圖頁:模板第 11 頁(6 張圖)clone 兩次,重開後圖片 blob 完整可讀。
- 錯誤路徑:UNMATCHED 與 AMBIGUOUS(撞 11 筆)都被抓住、訊息可操作、exit 1。
- **模板事實**:共 59 頁,**全部無 SmartArt**;25-27、31 頁含 chart 物件
  (工具只換文字,圖表數據替換未支援,用到時要回報使用者)。
- 實測修掉的三個 bug:builtin 文字框漏設 0.06" 內距(補 `_tight_margins`);
  estimate_overflow 誤報單行文字(改僅多行判溢出);JSON 帶 BOM 會炸
  (三處讀取改 utf-8-sig)。

### 7.2 fills 自動填充層(v1.2,2026-07-20)

使用者確認「填入應由 script 而非 LLM 做」後實作:

- **`tools/fills.py`**:10 種註冊頁型全部確定化。5 種(vision/info/data/
  evaluation/pyramid)clone 對應模板頁(p14/17/29/33/54)後把 spec 槽位填進
  **寫死的 shape id**(clone 保留原模板 id);5 種(cover/agenda/closing/
  story/stage)為 render_deck 內建版面(story/stage 座標移植自 repo 腳本
  Slide 7/9)。plan 從必要變**選配**。LLM 在註冊頁型的產檔流程中歸零。
- 選 Python 填充函式而非 JSON DSL 對照表:刪元素、溢出併列、加高框這些邏輯
  用程式碼表達自然得多,且對照表也是人工寫,DSL 只是多一層間接。
- **實測**:10 頁完整範例(全部 10 種頁型)零 plan 一次 render OK,qa_check
  PASS 零警告;4 頁 plan 路徑回歸通過。產出存 examples/demo_output_*.pptx。
- 過程再修四件:qa 字體白名單(微軟正黑體=JhengHei 中文名、`+mn-ea` 等主題
  參照、Noto Sans TC 模板原生);溢出估算跳過窄框直排設計(cap<1.6em);
  vision 中心圓文字框加高;pyramid 帶上標籤 >6 字時刪框(右列仍呈現全文)。

**最重要的維護風險——硬耦合**:fills.py 寫死了模板五頁的 shape id,與
light_template.pptx 綁定。**模板改版(哪怕只是重存)可能改變 shape id** →
FillError 或填錯框。設計上 FillError 會 exit 1,不會靜默產出錯檔。

已知取捨(fills.py docstring 也有記):evaluation 2 方案時第三欄刪除但不
重新置中;pyramid 4 層時刪頂層;模板分數籤/縮圖(契約無此欄位)一律刪除;
recommended/recommendation 以底部一行呈現。

## 8. 尚未做、可能的下一步

**【已決策、待執行】fills 全面耦合計畫(2026-07-20 註記,等首輪實測後啟動):**
- 決策一:渲染層**永不加隨機性**。多樣性來自頁型選擇,不來自 renderer;
  隨機性會毀掉可重現性與回饋規則化。
- 決策二:剩餘 ~34 種頁型分三級耦合,不一次做完:
  (2026-07-25 註:多模板架構落地後,升級一律「按包」執行——寫該包
  bindings.json 的 fill 條目 + 過 golden,以各包 FEEDBACK.md 分別計數;
  見 §20.3/§20.4 與 TEMPLATE_PACKS.md。)
  1. 純文字版型 ~28 種 → 標準套路可直接做;先做設計師圈選的高頻 5-8 種,
     其餘看 FEEDBACK.md,同頁型出現 2 次 clone+plan 使用就升級成 fills。
  2. 含 chart 的 4 種(模板 p25-27、31)→ 需 `chart.replace_data` 支援 +
     spec 定義數據系列格式,獨立排程。
  3. 含照片的頁型(p11 等)→ assets 機制已可載使用者上傳圖,需定義上傳流程。
- 使用者計畫:2026-07-21 先實測目前版本(10 種自動頁型)的成效再決定批次。

其他:
- [ ] 第一次實際部署到 GPT Builder + 跑完驗收(工具鏈本機已全數實測通過,
      但 ChatGPT 沙箱環境尚未驗過)。
- ~~評估 GPTs Actions 方案~~(2026-07-21 否決:公司政策禁用 Actions,不再提議)。
- [ ] 選配:wireframe_preview.py(PIL+OFL 中文字型畫線框示意,緩解無預覽痛點)。
- ~~裝 git + 首次 commit~~(已完成:2026-07-21 起以 git 保護,見 commit 歷史)。

## 9. 維護提醒(工具層)

改 `gpts/tools/*` 之後必須重打包:
`Compress-Archive -Path gpts\tools\* -DestinationPath gpts\knowledge\tools.zip -Force`
再重新上傳 tools.zip 到 GPTs 知識庫 + 更新 instructions 版本字串。

**light_template.pptx 改版時(最容易踩的雷)**:fills.py 寫死了 p14/17/29/33/54
的 shape id。改版後必跑:
1. `inspect_template.py --page N` 重盤點五頁,核對 fills.py 內的 id 常數
2. 本機跑 examples 01 + 02(零 plan)→ render + qa 全綠
3. 重打包 tools.zip、連同新模板一起重新上傳、更新版本字串

## 10. repo 瘦身(2026-07-20)

使用者確認全面轉向 GPTs 路線後,移除舊管線目錄:
- 刪除:`.agents/`(baoyu Codex skill)、`fallback/`、`my_project/`。
- 搬移:`my_project/assets` → `gpts/assets_src/`;`my_project/source/slides.md`
  → `gpts/examples/02_full_10p.source_slides.md`(provenance fixture)。
- 其餘可用資產已複製進 `gpts/knowledge/`。rendered_examples 參考圖隨
  my_project 刪除(GPTs 對知識庫圖檔無視覺理解,無用途)。
- 根目錄 `README.md`/`AGENTS.md`/`CLAUDE.md` 改寫為 GPTs 建置包定位;
  同步鐵律由四處簡化為三處(見 §6)。

## 11. 誤刪事故與重建(2026-07-20 深夜)

- 事故:瘦身完成後,使用者誤按 Shift+Delete,`gpts/` 全數消失(繞過資源回收筒);
  同時 repo 被還原成原始狀態(舊管線目錄回來了),連同瘦身前備份 zip 一起遺失。
- 重建來源:①scratchpad 測試沙箱(AppData 下,未被波及)保有**全部 7 支工具
  的實測最終版**、驗證器(缺 BOM/docstring 三個小修正,已補)、範例 01/02 spec、
  兩份 demo 產出、模板頁盤點 JSON;②還原回來的 repo 提供 knowledge 所有源檔;
  ③文件類(README/WORKLOG/instructions/registry/速查卡/FEEDBACK/範例 03)
  由 Claude Code 從對話脈絡重寫。
- 重建後已重跑完整回歸(validator 正反例 + 10 頁零 plan + 4 頁 plan + qa)確認
  與事故前行為一致。
- **教訓(必執行)**:①立刻裝 git(`winget install Git.Git`)並 commit;
  ②每次重大變更後重做備份 zip 且放到 repo 外;③scratchpad 沙箱意外成為
  第三份備份——但它是暫存目錄,不可依賴。

## 12. 一鍵大綱轉簡報(v1.4,2026-07-21)

實際使用發現,原本 v1.3 內容模式藏在長 Instructions 中,模型仍可能漏存
`slides.md`、手寫錯 `render_page_number`,且使用者取得 JSON 後還要再下指令產 PPT。

本版新增 `knowledge/outline_to_ppt_skill.md`、`/outline-to-ppt` 與未切頁測試來源
`examples/05_outline_to_ppt_source.md`:

- 使用者一次貼大綱即授權 JSON、validator、render、QA 與雙檔交付,不再中途確認。
- 先用 `make_skeleton.py` 取得契約正確的頁碼、素材與槽位結構,再填入來源內容;
  `PAGE_TYPE_LIST` 指定與呼叫放在同一個可執行區塊,每次替換範例 literal。
- 強制 `--slides --registered-only --strict`,只用十種完整註冊頁型。每次 outline run
  都覆寫本次完整來源與 `/mnt/data/slides.md`,禁止附加或沿用舊內容。
- 直供 JSON 則以 `--slides` 指向本次獨一且確認不存在的路徑,搭配
  既不加 `--registered-only` 也不加 `--strict` 的一般模式,刻意關閉追溯,避免
  outline→JSON 混合模式繼承舊 `slides.md`,並保留兩級頁型與未註冊頁型 render plan
  流程。缺來源與未註冊頁型 WARN 在此模式是預期結果；錯加 `--strict` 會把缺來源
  WARN 升級成 ERROR,錯加 `--registered-only` 會硬擋未註冊頁型。
- 缺少封面日期或報告人時省略 cover,不補值;來源不足就停止。
- `assets.zip` 內含 `assets/`,所以解到 `/mnt/data`;`tools.zip` 的工具在 archive root,
  所以先建立 `/mnt/data/tools` 再解到該目錄。封裝回歸必須使用解出的 renderer/QA。
- validator 最多自動修正三輪,且只能改結構或來源支援的縮字/拆頁。QA 的成功條件
  是 exit 0 且完整輸出**包含一行**以 `結果:PASS` 開頭;WARN 可以出現在 PASS 前。

### 12.1 忠實度邊界

validator 會程式化追溯已註冊頁型契約中啟用 provenance 的 `slots`,但不追溯頂層
`slides[].title` 或 `deck.deck_name`;數字比對也有 `5` 可被來源 `50` 子字串誤滿足的
限制。因此 v1.4 在 validator 前另做 prompt/workflow audit:

- 每頁頂層 title 必須逐字來自本次對應來源區塊;closing 的 `Thank you` 例外。
- `deck.deck_name` 等於第一頁非 closing 的來源支援 title,不再要求來源另列簡報名稱。
- 遞迴盤點 deck name、title、slots 的數字 token 並做精確比對,`5` 不等於 `50`。
- 唯一可獨立於來源的結構值是 agenda 順序編號、固定比較標題「改善前/改善後」與
  closing 的 `Thank you`。`recommended`、`recommendation` 等語意建議不得豁免。

這是工作流稽核,不是 validator 新增的程式保證;本版刻意遵守「不改 validator」約束,
文件也不再宣稱完整 programmatic provenance 或所有捏造數字都由 validator 硬擋。

### 12.2 驗收與發版狀態

本機驗收必須包含:Knowledge 11 檔、archive 固定 hash、從僅複製 Knowledge packages/
files 與測試輸入開始的正確路徑 bootstrap + strict validator/render/QA、QA WARN→PASS、
既有 examples 預期 exits、outline→直供 JSON 隔離、title/deck 注入、精確數字與子字串
限制,以及 fixture 05 不含 `## Slide` 或頁型/視覺方向指示。

GPT Builder 則用 fixture 05 跑完整一鍵案例,並另跑缺封面欄位、封裝 bootstrap、
QA 警告、mixed mode、title/deck 注入、精確數字、未註冊頁型壓力與來源不足案例。
完成後才把日期、model/runtime、validator、QA、頁數與 warnings 寫回此節。

2026-07-21 本機證據:靜態契約、Knowledge 11 檔與固定 archive hash 通過;全新暫存
runtime 只放 Knowledge packages/files 與測試輸入後,依實際封裝層級解壓,strict
validator、解出的 renderer 與 QA 完成 10 頁全流程。暫存頁碼 mismatch 讓 QA 先印
1 個 WARN 再印 `結果:PASS`,exit 仍為 0。既有 examples exits 為 0/0/0/1;
outline→直供 JSON 以不帶 `--strict` 或 `--registered-only` 的直供參數 exit 0 並顯示
追溯關閉,未註冊直供正例 exit 0、`--registered-only` 負對照 exit 1;title/deck
注入、`5` 對來源 `50` 的子字串限制與
完全不存在的 `88` 皆依預期呈現 validator/workflow audit 邊界。這些都是本機證據,
不取代 GPT Builder 驗收。

**狀態:已在本機實作;GPT Builder 驗收待執行;尚未發布。**

未修改 validator、schema、registry、renderer、template、tools 或 assets,因此不用重打包
`tools.zip`/`assets.zip`;fixture 05 也不是 Knowledge,上傳數仍是 11。

## 13. 草稿模式 + 環境自癒(v1.7,2026-07-21)

### 13.1 背景:首輪實測失敗的診斷

使用者實測 GPT 常在 `/outline-to-ppt` 中途宣稱「無法用你的工具產生」「腳本都在
但沒有穩定的工具鏈」。診斷結論:**v1.5/v1.6 的修正(反拒絕規則 7、省略並繼續、
正斜線重打包的 assets.zip、outline_to_ppt_skill.md)全部只存在本機工作區,從未
commit、也未同步到 GPT Builder**;Builder 端跑的是舊版指示,失敗行為與舊版一致。
GPT Builder 驗收始終未執行——踩到的正是唯一沒驗過的一環。同步 + 驗收是一切
修正生效的先決條件;驗收前先問 GPT「你現在是哪一版?」核對版本字串。

### 13.2 草稿模式(使用者定案的設計修正)

使用者實務工作流是「先做出簡報結構、之後再補資料」,並明確定案:**補齊規格內容
可以,硬底線是不能用提供的模板/頁型以外的東西**。原規則把「不得捏造事實」與
「不得出現占位文字」綁在一起,導致缺日期/報告人/KPI 就省略頁面甚至整體停止。
v1.7 拆開這兩件事:

- **validator**:新增 `PLACEHOLDER_RE`(待補充/待確認/待定/TBD,不分大小寫)與
  `strip_placeholders()`;兩條 provenance 路徑(註冊槽位 `validate_value`、未註冊
  `generic_provenance`)都先剔除佔位符再做數字與 bigram 檢查,整格皆佔位符
  (norm 後為空)則跳過追溯。字數上限、空值、結構檢查不變;佔位符以外的殘餘
  文字照常嚴查,佔位符本身無數字,捏造實值仍被硬擋。
- **skill**:「省略並繼續」改為「佔位並繼續」——cover 有主標題即可用,缺欄填
  「待補充」;點名要求的圖表改以語意最接近的註冊頁型建頁、缺料欄填佔位符;
  來源沒提及也沒點名的頁不得憑空建立;交付摘要必列「待補清單」。來源不足停止
  收窄為「擠不出任何一頁有來源標題的內容頁」。`待填`(骨架記號,不得殘留)與
  「待補充」(合法佔位符)明確區分。稽核例外清單加入佔位符。
- **instructions v1.7**:新增規則 8(草稿優先、佔位不捏造、版型無例外);規則 7
  加封殺「沒有穩定的工具鏈」話術;Step 0 改為**每次產檔前**檢查關鍵檔案,
  沙箱中途重置導致檔案消失時重解壓即可,不得當成工具鏈故障。

### 13.3 同步影響(v1.7 部分)

validator 有改(佔位符白名單)→ 需重新上傳 `validate_slide_spec_gpts.py`;
PAGE_TYPES 契約未動 → schema enum 與 registry 頁型節不需改,但 registry 補了
佔位符使用說明。tools/assets 未動,不需重打包(assets.zip 稍早已因正斜線
重打包,Builder 端仍需刪舊傳新)。發版時 Builder 需更新:instructions 全文 +
validate_slide_spec_gpts.py + outline_to_ppt_skill.md + page_types_registry.md +
assets.zip,共 11 檔照清單核對。

## 14. 管線單一入口 + page_types 清理(v1.8,2026-07-21)

前提:使用者確認 **GPTs Actions 因公司政策禁用**——伺服器端系統強制閘門永久
出局,強制上限=Code Interpreter 內的確定性腳本。因此把「模型串多步」壓到最低:

- **`tools/run_pipeline.py`(產檔單一入口)**:一條指令依序跑
  audit_provenance → validator → render_deck → qa_check,任一階段非 0 即停。
  模式自動判定:帶 `--slides` = outline 模式(自動 `--registered-only --strict`,
  帶 `--source` 加開來源完整性檢查);不帶 = 直供 JSON(自動以 tempfile 產生的
  獨一不存在路徑關閉追溯,不帶 strict)。`--validate-only` 供未涵蓋頁型先過
  閘門再寫 plan;`--plan` 透傳給 render_deck。模型的工作塌縮成
  「填 JSON → 跑一個指令 → 轉述報告」。
- **`tools/audit_provenance.py`(稽核程式化)**:skill §4 原本靠模型自律的四項
  稽核變成硬閘門——slides.md 逐行是原文逐字片段、頂層 title 逐字、deck_name=
  第一內容頁 title、精確數字 token(實測「來源 50/輸出 5」validator 子字串放行、
  本工具 exit 1 硬擋)。佔位符規則 import 自 validator(單一來源,同 make_skeleton
  慣例:兩檔需同在 /mnt/data 或父目錄)。
- **page_types.md 大掃除**:刪 49 行不存在的 `style_reference/rendered_examples`
  參考圖引用;49 行來源模板改指向知識庫 `light_template.pptx` + inspect/plan 用法;
  6 個已註冊頁型加「容量以 registry/validator 為準」標記防雙源漂移;**刪除
  「可拼湊模板元素組新版面」舊管線授權**(牴觸規則 5 與使用者硬底線),改為
  「選最接近頁型→仍不合就回報使用者」,並明寫工具只支援改字與刪除、不支援重排。
- instructions v1.8:規則 6 要求用 CI 讀 skill **全文**(防知識檢索只回片段);
  Step 2-5 併為管線入口流程。README_TOOLS 標準流程改為 run_pipeline 單指令;
  skill §4/§5/§6 改為腳本稽核 + 管線執行。

本機驗證:audit 正例 PASS;5-vs-50 與 title/deck_name 注入 exit 1;pipeline
outline 模式 4/4 PASS(佔位符 spec 產出 3 頁)、直供模式 examples 01 3/3 PASS、
04 停於 validator exit 1。tools.zip 需重打包(9 支腳本),Builder 需重傳
tools.zip + page_types.md + outline_to_ppt_skill.md + instructions。

**狀態:本機完成;GPT Builder 同步與驗收仍待執行。**

## 15. 免指令觸發 + 修正循環防失智(v1.9,2026-07-21)

使用者實測回報兩個體驗問題:

1. **要記得打 `/outline-to-ppt` 本身就是失敗點**:忘了打就掉進逐步確認的內容
   模式,體驗又變成「卡住」。v1.9 把路由反轉:貼大綱/段落文字=預設一鍵產檔,
   `/outline-to-ppt` 降級為同義觸發詞;逐步內容模式改為「使用者明講要逐步確認」
   才走。貼 JSON 與問問題的路由不變。
2. **「一被擋下來就失智」的根因是規則自己寫的**:instructions 與 skill 都把
   「閘門 FAIL」列為合法停止條件(「只有環境缺檔、來源不足或閘門 FAIL 才停止」),
   模型看到 FAIL 就有理由直接停,三輪修正形同虛設。v1.9 修法:
   - 停止條件改為「**三輪修正後**閘門仍 FAIL」;新增規則 8:FAIL 是修正循環的
     入口,三輪內嚴禁宣稱無法繼續、跳關、把問題丟回使用者。
   - README_TOOLS 新增「**錯誤→修法對照表**」:12 類常見錯誤(字數超限、項目數
     不符、捏造數字、相似度低、缺必填、頁碼、素材路徑、audit 三類、UNMATCHED、
     FillError)各對應唯一允許修法,模型照表操課,不必自己發明修法。
     FillError 是表中唯一「不修、回報維護者」的錯。
   - skill §5 修正輪要求逐條對照修法表;失敗回報的「閘門失敗」加註
     「僅限已跑滿三輪」並要求列出各輪已嘗試修法。

README 驗收新增:免指令貼大綱案例(與 /outline-to-ppt 前綴行為必須相同)、
修正循環案例(刻意超字數 → 應自動縮短/拆頁重跑,不得宣稱無法繼續)。
README_TOOLS 有改 → tools.zip 重打包;版本 v1.9-20260721。

**狀態:本機完成;GPT Builder 同步與驗收仍待執行。**

## 16. 首次 GPT Builder 實測與 v1.10 補丁(2026-07-21)

首份真實對話證據(repo `gpts/feedback_evidence/2026-07-21-feedback01-builder-chat.txt`,餵 fixture 06 職場禮儀):

**三個失敗行為**:①開場即拒絕——「我無法如實聲稱已完成那些專用內部流程」,
然後**自行用 python-pptx 手寫程式碼產了一份簡報**(違反規則 2);②被使用者
質問「妳沒有用腳本產嗎」後才完整背出正確流程;③「請照我們的流程生產」後
又拋 A/B 選單問滿意度圖表頁怎麼處理——skill 早已定案(最接近註冊頁型+待補充),
不該問。

**三個好消息**:模型背得出 run_pipeline.py/audit_provenance.py(v1.8+ 知識檔
上傳成功且可檢索);自述「已確認工具已成功解壓」(沙箱環境正常);手產內容
保留全部數字並用了待補充(內容規則有讀入)。

**診斷**:模型措辭「你所描述的內部工具流程」「你這個 GPT 所要求的那套」
把流程當外部要求而非自身系統指示 → 強烈指向 Builder Instructions 欄位仍是
舊版(知識檔有更新、指示沒貼)。驗證法:問「你現在是哪一版?」。
新發現的拒絕變體:把「執行腳本」曲解成「被要求**謊稱**已執行」的誠信框架。

**v1.10 補丁**(全部是指示層,工具未動、tools.zip 不需重打包):
- 規則 7:明寫「真的執行+如實轉述輸出=沒有誠信問題」,封殺「無法如實聲稱」
  拒絕框架。
- 規則 2:手產簡報(python-pptx 等)=未經閘門的違規產物,一律不得交付;
  「正要手寫產檔程式碼」本身就是漏跑流程的訊號。
- 規則 6 + skill:一鍵流程禁拋 A/B 選項選單;規則已決定的事直接執行
  (圖表無數據案例明寫「這是固定規則,不得詢問」)。
- FEEDBACK.md 記入第一筆真實回饋(#1)。

**狀態:待使用者確認 Builder 指示版本後,同步 v1.10 全套重測。**

## 17. 第二次實測與 v1.11 補丁(2026-07-21)

第二份對話證據(repo `gpts/feedback_evidence/2026-07-21-feedback02-builder-chat.txt`,FEEDBACK #2)暴露 v1.10 沒堵到的
兩個新失敗簽名:

1. **模型不知道知識庫檔案已掛載**:被要求用腳本時,反過來要使用者
   「把工具資料夾上傳到這個對話」——run_pipeline.py 等就在它的知識庫;
   直到使用者說「我有給妳呀」它才實際去 /mnt/data 看,然後全部找到。
   → 根因:模型 context 裡看不到檔案清單,不實際 ls 就斷言「沒有」。
2. **「缺 outline→spec 腳本」新藉口**:確認工具都在後,又以 tools.zip
   沒有大綱轉 spec 的腳本為由,要使用者自己提供 slide_spec.json——
   填骨架本來就是流程分配給模型的工作(規則 2 明列「代擬的 spec」),
   它沒把兩件事連起來。

**v1.11 補丁**(指示層,工具未動):
- 開場段落前置鐵律(利用模型對開頭的注意力權重):所有工具自動掛載於
  /mnt/data、使用者永遠不需上傳、嚴禁開口要求上傳;**說第一句話之前
  必須先跑完 Step 0 貼輸出**,Step 0 前對可行性下任何結論一律違規。
- 新規則 10:大綱→slide_spec.json 是模型份內工作,不存在也不需要
  轉換腳本,嚴禁以此卡住或反要使用者提供 spec。
- skill:環境節加「自動掛載/嚴禁要求上傳/先 ls 再說」;§3 開頭加
  「填骨架=你的工作,沒有專用腳本」。

**觀察**:兩輪實測的開場拒絕一模一樣,而 v1.10 規則 7 明文禁止該句式
——若 Builder 已貼 v1.10 仍如此,下一步該查 GPT 是否跑在較弱模型、
或 Builder 預覽視窗與已發布版本的指示不同步;若根本沒貼,先貼再測。
驗證法不變:問「你現在是哪一版?」。

**狀態:待確認 Builder 指示版本 → 同步 v1.11 全套 → 重測 fixture 06。**

### 17.1 根因確認(2026-07-21,兩筆回饋結案)

使用者把 GPT Builder 的 Recommended Model 指定為 **GPT-5.6 Pro** 後,fixture 06
全流程「跑得很完美」。結論:FEEDBACK #1/#2 的失敗根因是**模型等級**——未指定
模型時使用者端路由到輕量模型,其指令遵循與工具使用能力不足,產生整套失敗簽名
(不看 /mnt/data 就宣稱做不到、誠信框架拒絕、手產替代、拋選單)。

處置:README 建置步驟加「Recommended Model 務必指定最強可用模型」;
v1.7–v1.11 的指示防線**保留不撤**——分享出去的 GPT 管不住每個使用者實際
跑到的模型(降級/低階方案情境),這些規則是弱模型情境的防線,且指示總長
僅 ~4.8k 字元,離 8000 上限尚遠,強模型帶著零成本。

## 18. 第二前端:本機 Codex CLI skill(2026-07-24)

需求:除了 ChatGPT GPTs,也要能在 Codex CLI 聊天窗貼大綱直接本機產 pptx。
做法是**雙前端、單引擎**:新增 `.codex/skills/outline-to-ppt/SKILL.md`
(repo 版為真相來源;同步安裝到 `~/.codex/skills/outline-to-ppt/` + 同名 zip),
skill 只內聯環境差異與鐵律摘要,規則本體全部指回 `gpts/knowledge/` 與
`gpts/tools/`——沒有第二份規則,GPTs 建置包(instructions、11 個知識檔、
兩個 zip)一個位元組都沒動,對 GPTs 功能零影響。

本機環境與 /mnt/data 的差異(已實測全綠:01_minimal 直供模式 3/3 PASS):

- 工作/輸出目錄 = repo 根的 `ppt_out/`(gitignore),素材由 `gpts/assets_src`
  複製為 `ppt_out/assets`;run_pipeline 以 `--template`/`--validator` 顯式指向
  `gpts/knowledge/`,不需搬檔模擬 /mnt/data。
- 系統 python3 沒有 python-pptx → skill 自動改用
  `uv run --with python-pptx python`;make_skeleton 需
  `PYTHONPATH=gpts/knowledge` 才 import 得到 validator 的 PAGE_TYPES。

同步紀律入 AGENTS.md 硬規則 8:改 gpts 規則/工具 → 檢查 skill 摘要 →
複製到 ~/.codex 並重打 zip。

## 19. 文件結構整理(2026-07-24)

結構評審(懸空引用/重複檔/命名)後的衛生修正,不動任何規則與工具:

- **補回發版回歸**:README 引用的 `docs/superpowers/plans/2026-07-21-*.md`
  從未進版控(規劃工具留在本機的檔案),新增 `gpts/REGRESSION.md` 取代,
  R0–R8 全案例 2026-07-24 實測重建。過程中的發現:①02 範例
  `deck_name=my_project` 會被 audit 擋——它是直供模式範例,保留原樣,回歸
  改寫成「先驗稽核會擋、修 deck_name 後走完 4/4」;②數字 token 測資要挑
  該頁區塊沒有的數字(50→5 在 fixture 02 會因「5 天」合法通過,改用 95→9)。
- **刪除第三份範例副本**:`gpts/examples/slide_spec.example.json` 與 knowledge
  正本 byte-identical 且 examples/README 未記載(`02_full_10p.json` 為有記載的
  刻意複本,保留)。
- **證據檔搬家**:`chat-output*.txt` → `gpts/feedback_evidence/2026-07-21-feedback0N-builder-chat.txt`,
  FEEDBACK/WORKLOG 四處引用同步更新。
- **根 README 本機驗證改指 .codex skill 與 REGRESSION.md**,消除與 skill 的
  同工雙譜(配合 §18 的雙前端單引擎原則)。

### 18.1 Windows(無 WSL)對策(2026-07-24)

團隊 Windows 機器公司禁 WSL,只有 PowerShell/cmd。原本「bash 命令 + PowerShell
轉換規則」的做法翻譯面太大,改為**把 shell 膠水也 Python 化**:skill 自帶跨平台
`prepare_env.py`(標準庫),把工具鏈複製成 `ppt_out/` 沙箱(模擬 /mnt/data
佈局,冪等覆蓋、排除 __pycache__),於是 make_skeleton 免 PYTHONPATH、
run_pipeline 免 --template/--validator,**所有命令收斂成單行相對路徑 python
呼叫,三種 shell 原樣可跑**,唯二差異(python/python3 名稱、uv 渲染前綴)由
prepare_env 輸出提示。macOS 端全流程實測綠;原生 PowerShell 尚未實機驗證,
首位 Windows 使用者回報即定案。

## 20. 多模板架構設計定稿(2026-07-25,設計階段、未實作)

使用者需求(§8 的延伸):設計師會持續加新模板、每次產檔只指定一種,
且要能在本機 CLI「透過 prompt」註冊新模板。經全 repo 耦合盤點
(約 76 處 light 專屬耦合,分四類:shape id 綁定/主題 token/幾何常數/容量數字;
其中 render_deck 清除窗 11.2" 與 qa_check 偵測窗 11.0" 已互相不一致,
證明模板知識散落程式碼不可持續)+ 三視角獨立提案(引擎重構/設計師體驗/
打包營運)綜合定稿,設計全文見 **`gpts/TEMPLATE_PACKS.md`**(多模板架構的
單一真相來源),配套 skill 草稿見 `.codex/skills/register-template/SKILL.md`
(**未啟用**,其引用的工具是 Phase 2 交付物,Phase 2 落地且等價驗證
全綠前不得安裝 ~/.codex)。

核心決策(細節與否決理由見 TEMPLATE_PACKS.md):

- **模板包公式**:模板知識全部收進 `gpts/templates/<id>/` 自足目錄
  (manifest.json + bindings + page_map.md + inventory + assets);
  語意契約(槽位結構)維持三處同步共用,容量以 manifest
  `capacity_overrides`(扁平 dot-path,僅 min/max/max_chars)按包覆寫;
  新增模板 = 加目錄,不改引擎。
- **綁定表示法**:新模板一律固定 6-op 宣告式 bindings.json
  (set/delete/rows/list/add_textbox/resize + keep 覆蓋宣告,自 fills.py
  特例逐條歸納;表達力最終以 Phase 2 的 light 等價驗證為裁決),
  由 fills_engine 解譯;表達不了 → 該頁型降級 clone,絕不在註冊對話中
  擴詞彙表、絕不讓 LLM 現寫 Python。light 的 fills.py/BUILDERS 原封
  grandfather 進包。
- **支援矩陣三級**:fill(全自動)/clone(半自動)/unsupported;
  部分支援是合法結局;builtin 僅 light 保留,新模板 cover/agenda/closing
  必須是模板實頁走 fill。
- **spec 選模板**:`deck.template`(省略=light,零破壞);CLI 與 spec
  衝突 exit 2 硬錯。含 chart 頁禁註冊為 fill(lint 硬擋)。
- **驗收公式**:golden fixtures(每頁型 min/max 兩變體,自 PAGE_TYPES
  確定性派生、唯讀)+ 連跑兩次 shape 樹全等(冪等實證)+ 設計師目檢,
  機器綠與人點頭缺一不可;註冊器原子性內含 light 回歸與 git diff
  隔離白名單。
- **打包**:每模板一包 template_<id>.zip;Knowledge 重整後 10 檔、
  ≤19 紀律,容量約再 9 個模板;GPTs 端零註冊(沙箱無持久化),
  註冊只在本機 skill。
- **遷移**:Phase 0 light 包化零行為變(shape 樹 diff 為空;tools.zip
  repo 端重打但 Phase 1 前禁上傳 Builder)→ Phase 1 引擎 manifest 化 +
  Knowledge 換裝(含 prepare_env 擴充)→ Phase 2 fills_engine + golden +
  雙 skill 上線(register-template 與 outline-to-ppt 多模板化同 Phase,
  含 light 5 頁型 bindings.json 等價驗證)→ Phase 3 治理常態化。
  AGENTS.md 條文草稿(SSOT 兩處/兩層同步/隔離/準入/檔數預算)隨對應
  Phase 落地時才改。

**狀態:設計完成;Phase 0 已執行,見 §20.1。**

### 20.1 Phase 0 執行:light 包化(2026-07-25,零行為改變)

- **新引擎件**(進 tools.zip):`fill_helpers.py`(自 fills.py 抽出
  FillError/index_shapes/Ctx/fill_rows,+新整併 add_styled_textbox)、
  `pack_loader.py`(包解析:CLI→spec deck.template→light,衝突即錯;
  importlib 載入包 bindings)。
- **light 包**:`gpts/templates/light/`——bindings.py(fills.py 全部 +
  render_deck BUILDERS 及繪製小工具**原封搬入**)、manifest.json(53 筆
  page_types:builtin 5/fill 5/clone 43,自 page_types.md 49 行來源模板行
  程式化抽取;收編 style/asset_defaults/page_number 常數)、inventory.json
  (五個綁定頁 shape 樹快照+sha256)、page_map.md、REGRESSION.md(R-L0~L2)、
  FEEDBACK.md、examples/smoke_spec.json(=02 範例,10 頁全頁型)。
- **render_deck.py**:刪 BUILDERS/import fills → pack dispatch;保留頁碼與
  clone/plan 引擎;輸出加「模板包:light@版本」行;fills.py 刪除。
- **設計偏差(已回寫 TEMPLATE_PACKS.md)**:①sha 不符在 freeze 工具
  (Phase 2)落地前僅警告不硬擋(否則堵死 §9 試模板工作流);
  ②prepare_env 擴充自 Phase 1 提前(REQUIRED+同步 gpts/templates →
  ppt_out/templates;$RT 回歸環境同步補 templates 複製)。
- **驗收全綠**:examples 01/02 重構前後 `inspect_template --all` shape 樹
  **diff 為空**(等價實證)+ qa PASS;根 REGRESSION R0–R8 全符(R2a 停稽核、
  R2b 4/4、R3 WARN 後 PASS、R4/R5 exit 1、R8 3/3);R-L0/R-L1 綠;
  ppt_out 沙箱經 prepare_env 後渲染正常。tools.zip 重打
  (−fills.py、+2 支,R7 基準已更新);**紅線:Phase 1 Knowledge 換裝前
  不得上傳新 tools.zip 到 Builder**。~/.codex outline-to-ppt 已同步重打 zip;
  register-template 依閘門未安裝。
- 文件同步:AGENTS 規則 4 改指 bindings.py+lifecycle、CLAUDE 速覽、
  README(十支腳本/維護節)、README_TOOLS、REGRESSION R0/R7。

**下一步 = Phase 1(其餘工具接 manifest + deck.template + Knowledge 換裝)。**

### 20.2 Phase 1 執行:引擎模板感知 + Knowledge 換裝(2026-07-25)

- **檔案歸位**:`git mv` knowledge/light_template.pptx → templates/light/
  template.pptx、gpts/assets_src → templates/light/assets_src。Knowledge 換裝:
  −assets.zip −light_template.pptx +template_light.zip(pptx+manifest+bindings+
  page_map+assets;assets_src 以 arcname assets/ 映射),共 10 檔(≤19 紀律,
  餘 9 個模板位)。新沙箱佈局 = tools.zip → /mnt/data/tools、
  template_<id>.zip → /mnt/data/templates/<id>,根目錄不再有 assets/ 與模板檔。
- **五支工具模板感知**:validator(deck.template 解析、CLI/spec 衝突 exit 2、
  capacity_overrides merge(dot-path 白名單 min/max/max_chars)、三級閘門
  (unsupported ERROR 附支援清單/非全自動 WARN、--registered-only 升級)、
  per-頁型 assets 鍵覆寫、素材存在性走包兜底、draft 包拒用);qa_check
  (allowed_fonts+偵測窗讀 manifest,退回內建常數);make_skeleton(asset_defaults
  /merged 容量/骨架寫入 deck.template/--list 三級/unsupported 拒產);
  run_pipeline(單次解析四階段共用、模板檔預設=包內、前置檢查含 manifest、
  pk 參數透傳);inspect_template --verify(inventory 漂移偵測 exit 1);
  render_deck 頁碼幾何讀 manifest + --template-pack/--packs-root。
  schema 加 deck.template。pack_loader 增 resolve_template(包優先、asset-dir
  兜底)、fill_helpers.resolve_asset(順序由 manifest asset_resolution 宣告:
  light=asset_dir 優先保相容,非 light 預設包優先防跨包遮蔽)、
  load_bindings=False manifest-only 模式(make_skeleton 等純標準庫工具用,
  修掉「載 bindings 即 import pptx」的隱性相依)。
- **文件同步**:instructions v2.0-20260725(Step 0 解模板包+自證 id@version、
  roster 行、page_map 查頁碼);outline_to_ppt_skill 環境清單新佈局;
  page_types.md 結構拆分(49 行來源模板行移除,hex 描述以 light 基準註記
  保留,逐句去品牌化延後 Phase 3);style_guide 兩層註記+修掉三處
  style_reference 懸空路徑與「拼湊版面」舊授權(牴觸 v1.8 規則的殘留);
  registry 加 deck.template 說明;README(包內檔案 10 檔/驗收/維護節)、
  REGRESSION R0 改鏡射 GPTs 佈局、R7 換雙 zip 基準;AGENTS 規則 1(SSOT
  兩處)/4/5 改寫與常用指令、CLAUDE 同步;白話說明與 examples/README 更新;
  prepare_env 新源路徑(模板隨包,ppt_out 根不再放模板副本)。
- **驗收全綠(2026-07-25 實測)**:新佈局 R0–R8 全符;examples 01/02 產出
  shape 樹與 Phase 0 前基準**全等**(素材/模板全靠包解析,含無 assets/ 根
  目錄的新佈局);顯式 "template":"light" 與省略全等;manifest 假值讀取證明
  ×3(qa 假白名單 66 字體 WARN、make_skeleton 假 logo 路徑、validator 假容量
  上限 3>2 ERROR,還原後 PASS);unsupported 拒產/拒驗、不存在包與 CLI/spec
  衝突 exit 2;ppt_out 沙箱全流程 PASS;R-L0/R-L1 綠;inspect --verify 一致。
- **狀態:本機完成;GPT Builder 換裝與驗收(README 驗收 1–8)待執行。**
  發佈時 Builder 端:貼 v2.0 instructions、刪 assets.zip 與
  light_template.pptx、上傳 template_light.zip 與新 tools.zip。

**下一步 = Phase 2(fills_engine + golden + template_admin + 雙 skill 上線)。**

### 20.3 Phase 2 執行:註冊工具鏈 + 雙 skill 上線(2026-07-25)

- **fills_engine.py**(進 tools.zip):6-op 宣告式 bindings.json 解譯器
  (set/delete/rows/list/add_textbox/resize + keep 覆蓋宣告;槽位路徑支援
  索引/切片,list 支援 head/tail 對齊、成組刪除、overflow merge_into、
  delete_when_empty)。pack_loader 接上:無 bindings.py 的包自動走宣告式。
- **等價驗證(詞彙表最強實證)全數通過**:light 五種 fill 頁型以
  bindings.json 重寫(存包內,與 bindings.py 並存、.py 生效),與 fills.py
  產出 shape 樹**全等**——含 example 02 典型內容與 golden 全變體
  (min 刪格路徑 + max 溢出路徑)。無頁型需留 grandfather 缺口;
  light 是否切換宣告式留 Phase 3。過程中的兩個設計驗證:①lint 全覆蓋原則
  抓出 p33「優點/待改善」隱含保留的結構標籤 → keep op 第一個實例;
  ②模板頁碼框(清除窗內純數字)屬引擎 _finalize 職責 → lint 引擎豁免。
- **template_admin.py**(gpts/release/,不入 tools.zip):註冊單一入口
  new/freeze/lint(--all)/golden(--regen-specs)/register/pack(--tools)/
  isolation/list。golden = merged 契約即時派生 min/max 每 fill 頁型兩變體
  → validator(--allow-draft,新增旗標解 draft 雞生蛋)→ 渲染連跑兩次
  shape 樹全等(冪等實證)→ qa → 目檢檔 ppt_out/golden_<id>.pptx;
  register 原子性含 light 回歸與 isolation 白名單。
  gpts/golden/ 存 20 份基準契約 fixtures(--regen-specs 派生,對註冊唯讀)。
- **端到端演練(R9)**:lightcopy 假新模板從 new→manifest→freeze→register
  全流程 exit 0(自身 golden 10 頁 PASS、light 回歸綠),同 spec 換
  deck.template 兩包各 render+qa PASS。真實設計師模板待首位使用者。
- **雙 skill 上線**:register-template 啟用並安裝 ~/.codex(banner 改
  已啟用);outline-to-ppt 多模板化(指名模板 → make_skeleton
  --template-pack、頁型候選按包全自動集合收斂、模式 B 由 deck.template
  自動生效),GPTs 端 outline_to_ppt_skill.md 同步。README_TOOLS 錯誤表
  加「頁型不受模板支援」列;README 新增「多模板發佈 checklist」節;
  AGENTS 新增規則 9(綁定準入)/10(隔離與註冊入口)/11(Knowledge ≤19),
  規則 8 擴及所有 skill;REGRESSION 新增 R9/R10。
- **狀態:本機完成。**Builder 端仍待 Phase 1 的 v2.0 換裝驗收;
  Phase 3(FEEDBACK 分模板營運、light 切換宣告式、fills 三級升級按包執行)
  依 TEMPLATE_PACKS §8 常態進行。

### 20.4 Phase 3 執行:治理常態化(2026-07-25)

- **light 切換宣告式綁定**:pack_loader 合併語意定稿——BUILDERS 只能來自
  bindings.py;FILLS 取 py 匯出非空者優先(grandfather),否則用
  bindings.json。light 的 bindings.py 瘦身為 builders-only(五個 fill 函式
  與 _P17/_P33/_P54 對照表移除,~300 行 Python 退役),fills 正式由
  bindings.json 經 fills_engine 生效。驗收:examples 01/02 切換後 shape 樹
  仍與 Phase 0 前基準**全等**;golden 10 頁 PASS(冪等雙跑);lint 完整性
  檢查改為 bindings.json 存在即查(訊息同步改寫)。light 版本 bump
  2026-07-25.2(manifest/INDEX/instructions roster 三處同步)。
- **FEEDBACK 分模板營運**:根台帳加「模板」欄(light/<包id>/引擎/指示),
  既有 #1/#2 歸「指示」;模板專屬回饋謄入各包 FEEDBACK.md,fills 升級
  計數按包;§8 三級升級計畫加按包執行註記。
- **pre-commit(選配)決策:不裝 hook**——isolation/lint 已入
  README 發佈 checklist 與 REGRESSION R10,git hook 屬本機配置不進版控,
  維持手跑紀律。
- 多模板架構 Phase 0–3 至此全部落地;常態工作=按包升級 fills、
  處理分模板回饋、等首位設計師真實模板走 register-template。
  Builder 端 v2.0 換裝驗收仍待執行(README 驗收 1–8)。

## 21. repo 重構:單引擎 + 兩個延伸應用(2026-07-25)

使用者指出結構問題:引擎(工具/規則/模板包)全在 `gpts/` 底下,彷彿是 GPTs
的附屬品——但「雙前端、單引擎」早是鐵律,目錄應反映它。重構對照:

| 舊 | 新 |
| --- | --- |
| gpts/tools/ | engine/tools/ |
| gpts/knowledge/(8 個散檔) | engine/rules/ |
| gpts/knowledge/(2 個 zip) | gpts/dist/ |
| gpts/templates/、golden/、examples/、release/ | engine/ 同名目錄 |
| gpts/REGRESSION.md | engine/REGRESSION.md |
| gpts/{WORKLOG,FEEDBACK,TEMPLATE_PACKS,白話說明} | repo 根 |
| gpts/(保留) | README(建置手冊)、instructions.md、dist/、feedback_evidence/ |

- **沙箱佈局(/mnt/data、ppt_out、$RT)完全不變**,GPTs 端零影響;
  上傳清單同 10 檔(engine/rules 8 散檔 + gpts/dist 2 zip)。
- 程式修正:make_skeleton 與 audit_provenance 的 sys.path 候選加
  `_HERE.parent/"rules"`(repo 直跑免 PYTHONPATH,舊痛點正式消失);
  template_admin 常數改 ENGINE/RULES/DIST + isolation 白名單改
  engine/templates 與 gpts/dist;prepare_env 源路徑改 engine/。
- 文件:機械掃替(特定路徑優先)+ 手改定位敘述(根 README/CLAUDE/AGENTS
  改為「單引擎+兩延伸應用」;gpts/README 改為「引擎的 GPTs 延伸應用」);
  WORKLOG 歷史章節路徑**不改寫**(如實保留當時狀態),以本節對照表為準。
- tools.zip 因兩支腳本補路徑重打(R7 已更新);template_light.zip 內容未變。
- 驗收:新佈局 R0–R10 全符;repo 直跑 audit/make_skeleton OK;
  R2b 產出 vs 原始基準 shape 樹**仍全等**;prepare_env/ppt_out 正常。
