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
  字數/頁碼/素材。
- `page_types_registry.md` 改寫成使用者導向的「slide_spec.json 撰寫指南」。
- 絕對規則:GPT 不可增刪改使用者 JSON 的任何文字/數字;修正需展示差異取得同意。
- **v1.3 內容模式**(使用者給大綱/段落):GPT 切頁選頁型 → 原文逐字存
  slides.md → 產 spec → 驗證帶 `--slides` **重新開啟捏造數字硬擋** →
  每頁摘要確認後才產檔。三條入口(合規 JSON/不合規 JSON 修正循環/內容模式)
  收斂到同一個確定性出口。

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
   (有 slides.md 時仍擋捏造數字;純 JSON 模式下實際只驗素材存在 + slots 為
   dict)。`--registered-only` 可恢復嚴格行為。
   **動機**:不 fork 的話 40+ 種頁型全不能用。**代價**:未註冊頁型容量靠模型
   自律,長期正解是把常用頁型補進 `PAGE_TYPES`。
3. JSON 讀取用 utf-8-sig(容忍 Windows BOM,使用者上傳常見)。

## 4. 檔案清單與角色

見 `README.md` 的表格。特別說明:
- `knowledge/`(10 檔)= 要上傳 GPTs 的;其餘留在 repo。
- 檔案形式的判斷準則:**模型要讀的 → 獨立文件(走檢索);程式要讀的 →
  可打包 zip(走沙箱檔案系統)**。assets.zip/tools.zip 因此打包(省檔位、
  保留目錄結構、更新原子性),規則文件因此散放。
- instructions 開頭埋版本字串(目前 `v1.3-20260720`),發版時更新。

## 5. 早期風險(2026-07-20 實測後全數解除)

1. ~~本機沒有 Python,可攜版驗證器從未實跑過~~ **已解除**:見 §7.1。
2. ~~兩份手寫 example 未經驗證器實跑~~ **已解除**:01/03 皆 PASS。
3. ~~light_template.pptx 內部結構未逐頁檢視~~ **已解除**:59 頁無 SmartArt;
   25-27、31 頁含 chart(文字可換、圖表數據不可)。
4. ~~deepcopy 複製投影片是最可能翻車的環節~~ **已解除**:固化成
   `tools/pptx_toolkit.py` 的 `clone_slide()`,帶圖頁複製實測通過。
5. **閘門是指示強制,非系統強制**:模型可能跳過驗證。緩解=要求貼 PASS 輸出;
   終極解=GPTs Actions 接自家 API(工程量另計)。
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
  1. 純文字版型 ~28 種 → 標準套路可直接做;先做設計師圈選的高頻 5-8 種,
     其餘看 FEEDBACK.md,同頁型出現 2 次 clone+plan 使用就升級成 fills。
  2. 含 chart 的 4 種(模板 p25-27、31)→ 需 `chart.replace_data` 支援 +
     spec 定義數據系列格式,獨立排程。
  3. 含照片的頁型(p11 等)→ assets 機制已可載使用者上傳圖,需定義上傳流程。
- 使用者計畫:2026-07-21 先實測目前版本(10 種自動頁型)的成效再決定批次。

其他:
- [ ] 第一次實際部署到 GPT Builder + 跑完驗收(工具鏈本機已全數實測通過,
      但 ChatGPT 沙箱環境尚未驗過)。
- [ ] 評估 GPTs Actions 方案(伺服器端驗證+渲染,100% 系統強制閘門)。
- [ ] 選配:wireframe_preview.py(PIL+OFL 中文字型畫線框示意,緩解無預覽痛點)。
- [ ] **裝 git + 首次 commit(最高優先,見 §11 的教訓)。**

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
