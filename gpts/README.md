# GPTs 建置包 — 把 spec 閘門流程搬進 ChatGPT

這個資料夾是給「想在 ChatGPT 建一個團隊共用簡報產生器 GPTs」用的完整素材包。
設計原則:**所有檔案隨 GPTs 內建**——模板(light_template.pptx)、背景、logo、
頁型規則、驗證器、工具腳本全部放在知識庫;終端使用者**只需提供一份合規的
slide_spec.json**(貼上或上傳皆可),不需要準備任何其他檔案。流程:

> 使用者給 JSON → GPTs **在 Code Interpreter 裡實際執行驗證器,PASS 才產檔**
> → 用 tools 腳本依模板產出可編輯的 .pptx → qa_check 自檢 PASS 才交付。

因為驗證器只用 Python 標準庫,閘門(字數/槽位數量/頁碼規則/素材檢查)在 GPTs 裡
是**真的會執行**的程式,不是只靠 prompt 約束。

閘門分兩級:`page_types_registry.md` 裡的 **10 種註冊頁型**走完整槽位契約檢查;
`page_types.md` 頁型庫的**其他 40+ 種頁型**也可以用,驗證器對它們只做基本檢查,
容量由模型比照 page_types.md 自律。
使用者不會寫 JSON 也沒關係:**直接貼上段落大綱就會自動走一鍵產檔**(`/outline-to-ppt` 是同義觸發詞,可打可不打;想逐步確認要明講)。一鍵流程會保存來源、只選完整註冊頁型、產生並嚴格驗證 JSON,接著直接渲染與 QA;缺個別資料以「待補充」佔位繼續,只有來源不足或三輪修正後閘門仍失敗才停止。

## 工具層(`tools/` → `knowledge/tools.zip`)

產檔的機械動作全部由九支預寫腳本執行,模型只在「未涵蓋頁型」時手產一份小小的
`render_plan.json`——這是「精準 + 省 token + 不進 QA 死循環」的核心設計:

| 腳本                  | 角色                                                                |
| --------------------- | ------------------------------------------------------------------- |
| `run_pipeline.py`     | **產檔單一入口**:稽核→驗證→渲染→QA 一條指令跑完,任一階段 FAIL 即停  |
| `audit_provenance.py` | 程式化工作流稽核:title/deck_name 逐字、精確數字 token、來源完整性    |
| `pptx_toolkit.py`     | 投影片複製(含 rels 重映射,圖不破)/刪除/排序/清 Section              |
| `text_tools.py`       | 群組內層文字替換(保留原字級顏色)、CJK 溢出估算、縮字                |
| `fills.py`            | **10 種註冊頁型的確定性填充引擎**:5 種自動填入模板頁(shape id 寫死) |
| `inspect_template.py` | 模板盤點:`--summary` 全冊一頁一行、`--page N` 單頁形狀樹(省 token)  |
| `render_deck.py`      | 主程式:spec(+選配 plan)→ pptx,**冪等整檔重生**;5 種頁型內建版面     |
| `qa_check.py`         | 產檔後自檢:內容覆蓋/頁數/Section/字體/頁碼/溢出,只印問題            |
| `make_skeleton.py`    | 依頁型清單產「保證過驗證器」的 spec 骨架                            |
| `README_TOOLS.md`     | 給模型的速查卡:標準三步指令 + plan 格式 + 鐵律                      |

**10 種註冊頁型 = 純 script 產出,LLM 零參與**:使用者 JSON → 驗證 → render_deck
自動產檔 → qa_check,全程模型只負責跑指令和轉述結果。只有用到 page_types.md
其他 40+ 種頁型的頁,模型才需要寫一小段 render_plan(該頁的文字替換清單)。

反循環機制:render_deck 每次從模板重新生成整份檔,錯誤(UNMATCHED/qa FAIL)
永遠回到「改輸入的某一條」再整檔重跑——不存在「刪掉壞頁再補一頁」這種
會累積損傷的操作;同一份輸入跑一萬次結果都一樣。

實測產出可眼見為憑:`examples/demo_output_01_minimal.pptx`(4 頁)、
`examples/demo_output_02_full10p.pptx`(10 頁全自動、零 plan、qa 零警告)。

## 包內檔案

| 檔案                                    | 用途                                                                     | 放哪裡                           |
| --------------------------------------- | ------------------------------------------------------------------------ | -------------------------------- |
| `instructions.md`                       | GPTs 系統指示全文(含版本代號)                                            | 貼進 GPT Builder「Instructions」 |
| `knowledge/validate_slide_spec_gpts.py` | 驗證器(兩級閘門;PAGE_TYPES 單一真相來源)                                 | 上傳到 Knowledge                 |
| `knowledge/page_types_registry.md`      | slide_spec.json 撰寫指南 + 10 種註冊頁型契約                             | 上傳到 Knowledge                 |
| `knowledge/outline_to_ppt_skill.md`     | 段落大綱一鍵產生合規 JSON、渲染 PPT 與 QA 的繁中工作流                   | 上傳到 Knowledge                 |
| `knowledge/page_types.md`               | 完整頁型庫 40+ 種                                                        | 上傳到 Knowledge                 |
| `knowledge/light_template.pptx`         | 公司模板本體,產檔時複製頁改字                                            | 上傳到 Knowledge                 |
| `knowledge/style_guide.md`              | 視覺規範                                                                 | 上傳到 Knowledge                 |
| `knowledge/slide_spec.schema.json`      | spec 結構定義                                                            | 上傳到 Knowledge                 |
| `knowledge/slide_spec.example.json`     | 通過驗證的完整範例                                                       | 上傳到 Knowledge                 |
| `knowledge/slide_spec.bad.example.json` | 會 FAIL 的範例(驗收測試用)                                               | 上傳到 Knowledge                 |
| `knowledge/assets.zip`                  | 背景圖 ×3 + logo                                                         | 上傳到 Knowledge                 |
| `knowledge/tools.zip`                   | 工具腳本 ×9 + 速查卡(源碼在 `tools/`)                                    | 上傳到 Knowledge                 |
| `examples/01_*.json`–`04_*.json`        | 四份試用範例(最小/完整/未註冊頁型/故意違規)                              | 不上傳,發給使用者試              |
| `examples/02_full_10p.source_slides.md` | 已切頁的 validator provenance 測試 fixture                               | 不上傳,測試用                    |
| `examples/05_outline_to_ppt_source.md`  | 真正未切頁、無頁型指示的一鍵大綱輸入 fixture                             | 不上傳,測試用                    |
| `examples/demo_output_*.pptx`           | 本機實測產出,眼見為憑                                                    | 不上傳                           |
| `assets_src/`                           | 素材可編輯源檔;重打包 assets.zip 時需先把資料夾改名/複製為 `assets` 再壓 | 不上傳,留在 repo                 |
| `FEEDBACK.md`                           | 回饋台帳(症狀→規則化→發版的追蹤表)                                       | 不上傳,留在 repo                 |
| `WORKLOG.md`                            | 決策紀錄:架構演進、取捨理由、已知風險,接手必讀                           | 不上傳,留在 repo                 |

## 建置步驟(約 15 分鐘)

1. ChatGPT(需 Plus/Team/Enterprise)→ 頭像選單 → **My GPTs → Create a GPT**,
   切到 **Configure** 分頁(不要用左邊的對話式 Create,設定會比較精準)。
2. **Name / Description**:自訂,例如「簡報產生器(內部)」/「給我一份合規的
   slide_spec.json,產出公司規範的 16:9 繁中簡報;模板素材全內建」。
3. **Instructions**:貼上 `instructions.md` 分隔線以下的全文。
4. **Knowledge**:上傳上表 11 個檔案(`knowledge/` 內全部;GPTs 上限 20 個檔,
   還有餘裕)。
5. **Capabilities**:
   - ✅ **Code Interpreter & Data Analysis**(必開,整個流程靠它)
   - ❌ Web Browsing(關,避免內容混入外部資料)
   - ❌ DALL·E / 圖片生成(關;此流程完全不生圖)
6. **Conversation starters** 建議:
   - 「直接貼上段落大綱,一次產出 JSON 與 PPT(不需任何指令)」
   - 「這是我的 slide_spec.json,幫我產出 PPT」
   - 「給我一份 slide_spec.json 空白骨架,頁型:封面、目錄、三欄說明、封底」
   - 「slide_spec.json 要怎麼寫?有哪些頁型可以用?」
   - 「驗證失敗了,幫我看錯誤怎麼修」
7. 儲存,分享範圍選「Anyone with the link」或 Team workspace。

## 驗收測試(建好後必做)

> **v1.11 狀態(2026-07-21):已在本機實作;GPT Builder 驗收待執行;尚未發布。**
> 下列 GPT Builder 項目是發版閘門,不是已通過紀錄。
> ⚠ 實測回報「卡在一半說無法用工具產生/沒有穩定的工具鏈/請上傳工具」的第一
> 檢查點:問 GPT「你現在是哪一版?」——不是 `v1.11-20260721` 就代表 Builder 端
> 還在跑舊版,先同步 instructions 與 11 個知識檔(特別是 outline_to_ppt_skill.md、
> tools.zip 與重打包的 assets.zip)再測。兩次實測失敗紀錄見 FEEDBACK #1、#2。

1. 對 GPTs 說:「執行環境準備,然後用知識庫的 slide_spec.bad.example.json 和
   slide_spec.example.json 各跑一次驗證器,貼出結果。」
   - `assets.zip` 必須解到 `/mnt/data`,形成 `/mnt/data/assets/`
   - 必須先建立 `/mnt/data/tools`,再把 archive root 是工具檔的 `tools.zip` 解到該目錄
   - bad example 必須 **FAIL** 並列出一串 ERROR
   - example 必須 **PASS**(可能有 WARN)
   - ✅ 2026-07-20 已在本機(Python 3.14 + python-pptx 1.0.2)完整實測:驗證器
     正反例、兩級閘門、工具鏈全流程(含帶圖頁複製、錯誤路徑)全數通過,
     詳見 WORKLOG.md §7.1。沙箱環境仍建議跑一次此步驟確認版本差異無影響。
2. 對 GPTs 說:「跑 inspect_template.py --summary,然後 --page 35 給我看。」
   能列出 → 模板讀取與工具解壓都正常。
   再說:「用 make_skeleton.py 產一份 cover,agenda,closing 骨架並跑驗證器」,
   應該直接 PASS——這同時測工具鏈與驗證器。
3. 對 GPTs 說:「用知識庫的 slide_spec.example.json 直接產出 PPT」,在 PowerPoint
   開啟確認:背景/logo 正確、版面貼近模板參考頁、文字可編輯、沒有溢出、
   沒有殘留模板 Section。
4. 再測一份自己寫的 JSON(建議刻意包含一頁未註冊頁型,如 `cycle_four_point_loop`,
   以及一個故意超字數的欄位),確認:超字數那頁被驗證器擋下並回報清楚的修正建議;
   修正後能產檔,且未註冊頁型的版面有按模板對應頁重建。
5. 測試一鍵大綱流程:**不打任何指令**,直接貼上真正未切頁的
   `examples/05_outline_to_ppt_source.md` 全文(另用 `/outline-to-ppt` 前綴重測一次,
   行為必須相同)。確認 GPTs 不要求中途確認,且:
   - 環境先出現 `/mnt/data/assets/` 與 `/mnt/data/tools/`
   - 驗證命令同時含 `--slides --registered-only --strict`
   - 本次原文與 `slides.md` 都覆寫舊檔,沒有混入前次執行內容
   - `slides.md` 每頁區塊內的每一段來源摘錄都是
     `/mnt/data/outline_source_current.txt` 的逐字片段,沒有改寫或補寫
   - 至少有一頁真正內容頁;`cover`、`agenda`、`closing` 都不計入,所以只有這三種頁型
     不能滿足來源充分性
   - 驗證前工作流稽核涵蓋頂層 `slides[].title`、`deck.deck_name` 與全部內容欄位的
     精確數字 token
   - `slide_spec.json` 驗證 PASS
   - `deck.pptx` 的 qa_check exit 0,且完整輸出包含一行以 `結果:PASS` 開頭；前面即使有
     WARN 也算 PASS,但警告必須如實回報
   - 最後同時提供 JSON 與 PPTX
6. 測試內容忠實邊界:
   - 移除來源中的日期與報告人重跑,確認保留 `cover` 且缺欄填「待補充」而非捏造
     實值;交付摘要含待補清單
   - 來源標「待補充」的 KPI 與只有名稱沒有數據的圖表(如甘特圖、KPI 儀表板),
     確認以最接近的已註冊頁型建頁、缺料欄位填「待補充」,不生成示意圖、不捏造
     數據、不改用未註冊頁型
   - 在頂層 `slides[].title` 或 `deck.deck_name` 注入來源沒有的文字,確認工作流稽核在
     validator 前停止
   - 在來源未出現的槽位加入 `88%`,確認稽核與 validator 都拒絕且不交付 PPTX
   - 用暫存測資讓來源只有 `50`、輸出為 `5`,確認精確 token 稽核拒絕；validator 目前
     的子字串比對可能通過此例,這是已知限制,不可宣稱 validator 完整硬擋
7. 測試修正循環(反「一擋就停」):在來源塞一段刻意超過欄位字數上限的長句重跑,
   確認 GPT 被閘門擋下後**對照 README_TOOLS 修法表自動縮短/拆頁並整條重跑管線**,
   而不是宣稱「無法繼續」;三輪內修好照常交付,並回報修了什麼。
8. 測試模式隔離:先完成一次 outline 流程並保留 `/mnt/data/slides.md`,接著直供 JSON。
   直供模式必須產生本次獨一且已確認不存在的 `direct_json_<run-id>.no-slides` 路徑,
   只以 `--slides` 指向它,不得加 `--registered-only` 或 `--strict`,並確認 exit 0、
   顯示「來源追溯:關」與缺來源 WARN；不得誤用舊 `slides.md`。若加 `--strict`,該 WARN
   會升級為 ERROR；若加 `--registered-only`,未註冊頁型會被硬擋,兩者都不屬於純 JSON
   模式的合法指令。

### 發版前本機回歸

本機另以全新暫存目錄跑下列案例；完整命令與預期結果見
`docs/superpowers/plans/2026-07-21-outline-to-ppt-knowledge-skill.md`:

- 從複製的 Knowledge archives/檔案與測試輸入開始,把 `assets.zip` 解到暫存根目錄、
  `tools.zip` 解到明確建立的 `tools/`,再以**解出的** validator、renderer、QA 完成
  strict 全流程。
- 對有效 deck 使用暫存 spec 製造頁碼 WARN,證明 QA 先印 WARN、後印
  `結果:PASS` 時 exit 仍為 0。
- 跑 outline→直供 JSON 混合模式、title/deck 注入、精確數字 token 與子字串限制案例。
- 跑 `examples/` 既有四份 validator 預期 exit、Knowledge 11 檔清單、兩個 archive hash,
  並確認 fixture 05 沒有 `## Slide` 或頁型/視覺方向指示。

## 誠實的限制(建議原文轉達給主管)

1. **閘門是「指示強制」不是「系統強制」。** 模型理論上可能偷懶跳過驗證。
   GPTs Actions(伺服器端 100% 系統強制)**因公司政策禁用**,所以強制上限就是
   Code Interpreter 內的確定性腳本。緩解:產檔一律走單一入口 `run_pipeline.py`
   (稽核/驗證/渲染/QA 綁在一條指令裡,跳過閘門=連唯一指令都沒跑,極易察覺);
   使用者驗收時認完整輸出末尾的「管線結果:PASS」行,沒看到就要求重跑。
2. **視覺一致性:機械部分已確定化,判斷部分仍靠模型。** 複製頁、換字、刪頁、
   排序、頁碼、五種內建版面都由 tools 腳本固定執行,不再漂移;模型剩下的自由度
   只在未涵蓋頁型的 render_plan(哪個框填哪段字),錯了是改一條 plan 重跑。
   模型看不到知識庫裡的參考圖片(GPTs 對知識庫圖檔沒有視覺理解),精緻度仍需
   設計師收尾。
   另外:未註冊頁型(page_types.md 那 40+ 種)的槽位容量只靠模型自律,程式閘門
   對它們只驗基本結構與素材存在;需要嚴格保證的頁型,長期解是把它註冊進
   `PAGE_TYPES`(見下方維護節)。
   若使用 `/outline-to-ppt`,每次都以本次原文覆寫 /mnt/data/slides.md,再以
   `--slides --registered-only --strict` 啟用已註冊 `slots` 的程式追溯,並只在工作流稽核、
   validator 與 QA 都 PASS 後交付 JSON 與 PPTX。validator 不會追溯頂層
   `slides[].title` 或 `deck.deck_name`,而且數字目前用子字串比對；這兩項由驗證前
   prompt/workflow audit 補強,不是 validator 的硬保證。可不依來源產生的值只限
   agenda 順序編號、固定比較標題「改善前/改善後」與 closing 的 `Thank you`；語意性
   建議內容仍須有來源。純 JSON 直供模式由 JSON 作者負責內容正確性,且必須把
   `--slides` 指向本次獨一、已確認不存在的路徑,且不加 `--registered-only` 或
   `--strict`,刻意關閉追溯、避開舊 slides.md 並保留兩級頁型行為；缺來源與未註冊
   頁型 WARN 是預期結果。
3. **沙箱沒有中文字體。** 產出的 .pptx 在使用者電腦開啟時字體正確(檔案裡只存
   字體名稱),但 GPTs 無法先渲染可靠的中文預覽圖,驗收要開 PowerPoint 看。
4. **知識庫檔案是靜態副本。** repo 更新規則時,GPTs 不會自動同步,要手動重新
   上傳(見下節)。
5. **資安。** 上傳到 GPTs 的樣板、素材與使用者貼入的內容都會經過 OpenAI。
   免費/Plus 個人版對話預設可能用於訓練(可關閉);Team/Enterprise 預設不用於
   訓練。內容敏感的簡報請確認公司政策允許後再用。

## 回饋與版本更新流程

GPTs 只有**擁有者**能編輯,所以要指定一位管理者(建議就是維護本 repo 的人),
並讓修改走 repo:

1. **真相來源在 repo 的 `gpts/` 目錄。** 指示改 `gpts/instructions.md`、規則改
   `gpts/knowledge/*`,一律先改 repo、commit,再由管理者同步到 GPT Builder
   (貼指示/重傳知識檔)。不要直接在 GPT Builder 裡改完就算——下次同步會被
   repo 版蓋掉。
2. **版本代號。** 指示開頭埋了版本字串(目前 `v1.11-20260721`),每次同步時更新。
   使用者對 GPTs 問「你現在是哪一版?」就能確認自己用到的是不是最新版,
   回報問題時也請附上版本代號。
3. **回饋管道。** 開一個固定收集點(Slack/Teams 頻道或共用表單皆可),回報格式:
   版本代號 + 所用的 slide_spec.json + 產出檔或截圖 + 哪一頁哪裡不對。
   沒有 JSON 的回報很難重現,管理者可以直接退回補件。
4. **回饋分流。** 版面不像模板/文字溢出 → 改 `instructions.md` 的規則或
   `page_types.md` 描述;閘門漏擋或誤擋 → 改 `validate_slide_spec_gpts.py`
   (同步 schema 與 registry,見下方維護節);想要新頁型 → 走下方「維護」節的
   註冊流程。
5. **改完先驗收再發版。** 每次重新上傳後,跑完「驗收測試」節的全部項目 +
   `examples/` 的 01–04 四份既有 validator 範例,PASS 才通知團隊更新。

### 「產出不如預期」要怎麼回饋才會真的變好

先理解一個關鍵:**GPTs 沒有跨對話記憶**。你在對話裡罵它、糾正它,只對當次有效,
對話關掉就忘了。所以回饋分兩層,終點永遠是「變成一條寫進檔案的規則」:

**第一層|使用者當場修(救這一次):**
產出不對就直接在同一個對話裡下修正指令,例如「第 3 頁的卡片間距太擠,參考模板
第 17 頁重排」「第 5 頁 KPI 數字要用主色」。修到滿意後,把三樣東西交給管理者:
①原始 JSON ②你下過的修正指令 ③修正前後截圖。**你下的那句修正指令特別值錢**——
它往往就是可以直接寫進規則的句子。

**第二層|管理者規則化(讓以後都對):**
把回饋翻譯成規則寫進對應檔案,再重新上傳。對照表:

| 症狀                                                    | 改哪裡                                                                    |
| ------------------------------------------------------- | ------------------------------------------------------------------------- |
| 文字溢出、字級跑掉                                      | `instructions.md` 溢出規則,或調低 `page_types_registry.md` 該欄位字數上限 |
| 版面跟模板不像、元素亂跑                                | `page_types.md` 該頁型的「視覺結構」描述補細節(位置、比例講死)            |
| 配色、卡片樣式、logo/頁碼不對                           | `style_guide.md` 補規則                                                   |
| 明顯違規的 JSON 沒被擋 / 合規的被誤擋                   | `validate_slide_spec_gpts.py`(同步 schema 與 registry,見下方維護節)       |
| 破圖、頁序錯、Section 殘留、封面/目錄版面偏移等機械問題 | `tools/` 對應腳本,改完重打包 `tools.zip` 上傳                             |
| 同一頁型每次產出長得不一樣                              | 最強解:把該頁型註冊進 `PAGE_TYPES` + registry + fills,升級成全自動        |
| 它跳過驗證就產檔                                        | `instructions.md` 絕對規則區加重申;驗收時堅持要看 PASS 輸出               |

**回饋單格式**(記錄在 `gpts/FEEDBACK.md`,或貼到回饋頻道由管理者謄入):
版本代號/日期/回報人/所用 JSON/頁碼與元素/期望(附模板參考頁)/實際(附截圖)/
當場下了什麼修正指令、有沒有效/狀態(待處理→已規則化→已發版)。

一個判斷準則:如果你能用一句話說出「以後應該怎樣」,那句話就是規則,直接交給
管理者寫進檔案;如果說不出來(只覺得醜),就附上模板參考頁和產出的並排截圖,
讓管理者判斷差在哪。重複出現兩次以上的問題,一律規則化,不要每次都當場修。

## 維護:改頁型時要同步幾個地方

> `gpts/knowledge/` 即單一真相來源,同步鐵律為**三處**:

1. `gpts/knowledge/validate_slide_spec_gpts.py` 的 `PAGE_TYPES`(真相來源)
2. `gpts/knowledge/slide_spec.schema.json` 的 enum
3. `gpts/knowledge/page_types_registry.md`(1 的人類可讀版)

新頁型若要全自動產出,另需在 `tools/fills.py`(或 render_deck 的 BUILDERS)
加填充實作 → 重打包 `tools.zip`。素材改版:改 `assets_src/` → 複製為名為
`assets` 的資料夾重打包 `assets.zip`。**打包 zip 一律用正斜線(POSIX)路徑分隔符**
——不要用 PowerShell `Compress-Archive` 或檔案總管「壓縮資料夾」(會塞 Windows
反斜線,Linux `unzip` 會警告並回非零 exit,誘發 GPTs 誤判環境壞掉);用
`python -c "import zipfile; ..."`(arcname 帶 `/`)或 `zip -r` 打包。驗證:
`python -c "import zipfile; [print(i.orig_filename) for i in zipfile.ZipFile('gpts/knowledge/assets.zip').infolist()]"`
每筆都必須是正斜線。模板改版:照 `WORKLOG.md` §9 的
shape id 重盤點流程。改完把異動檔**重新上傳**到 GPTs 知識庫並刪掉舊檔;
「gpts/ 目錄有異動 → 重新上傳知識庫」寫進團隊的發版 checklist。
