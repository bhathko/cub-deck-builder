# GPTs 建置包 — 把 spec 閘門流程搬進 ChatGPT

這個資料夾是**引擎(`engine/`)的 ChatGPT GPTs 延伸應用**:把引擎打包上傳
GPT Builder 的建置手冊與發佈物(instructions + `dist/` zips)。
設計原則:**所有檔案隨 GPTs 內建**——模板包(template_light.zip:模板本體+
背景+logo+綁定)、頁型規則、驗證器、工具腳本全部放在知識庫;終端使用者
**只需提供一份合規的 slide_spec.json**(貼上或上傳皆可),不需要準備任何其他
檔案。多模板架構見 [`docs/TEMPLATE_PACKS.md`](../docs/TEMPLATE_PACKS.md)(spec 以
`deck.template` 選模板,省略=light)。流程:

> 使用者給 JSON → GPTs **在 Code Interpreter 裡實際執行驗證器,PASS 才產檔**
> → 用 tools 腳本依模板產出可編輯的 .pptx → qa_check 自檢 PASS 才交付。

因為驗證器只用 Python 標準庫,閘門(字數/槽位數量/頁碼規則/素材檢查)在 GPTs 裡
是**真的會執行**的程式,不是只靠 prompt 約束。

閘門分兩級:`page_types_registry.md` 裡的 **11 種註冊頁型**走完整槽位契約檢查;
`page_types.md` 頁型庫的**其他 40+ 種頁型**也可以用,驗證器對它們只做基本檢查,
容量由模型比照 page_types.md 自律。
使用者不會寫 JSON 也沒關係:**直接貼上段落大綱就會自動走一鍵產檔**(`/outline-to-ppt` 是同義觸發詞,可打可不打;想逐步確認要明講)。一鍵流程會保存來源、只選完整註冊頁型、產生並嚴格驗證 JSON,接著直接渲染與 QA;缺個別資料以「待補充」佔位繼續,只有來源不足或三輪修正後閘門仍失敗才停止。

## 工具層(`engine/tools/` → `dist/tools.zip`)

產檔的機械動作全部由十一支預寫腳本執行,模型只在「未涵蓋頁型」時手產一份小小的
`render_plan.json`——這是「精準 + 省 token + 不進 QA 死循環」的核心設計:

| 腳本                  | 角色                                                                |
| --------------------- | ------------------------------------------------------------------- |
| `run_pipeline.py`     | **產檔單一入口**:稽核→驗證→渲染→QA 一條指令跑完,任一階段 FAIL 即停  |
| `audit_provenance.py` | 程式化工作流稽核:title/deck_name 逐字、精確數字 token、來源完整性    |
| `pptx_toolkit.py`     | 投影片複製(含 rels 重映射,圖不破)/刪除/排序/清 Section              |
| `text_tools.py`       | 群組內層文字替換(保留原字級顏色)、CJK 溢出估算、縮字                |
| `pack_loader.py`      | 模板包載入器:解析 `deck.template` → 載入 `templates/<id>/` 綁定       |
| `fill_helpers.py`     | 填充共用件(Ctx/fill_rows/素材解析);builtin 繪製器在 light 包 bindings.py  |
| `fills_engine.py`     | bindings.json 解譯器:宣告式 op(v1.1 共 7 個含 chart)驅動各包的 fill 填充 |
| `inspect_template.py` | 模板盤點:`--summary` 全冊一頁一行、`--page N` 單頁形狀樹(省 token)  |
| `render_deck.py`      | 主程式:spec(+選配 plan)→ pptx,**冪等整檔重生**;5 種頁型內建版面     |
| `qa_check.py`         | 產檔後自檢:內容覆蓋/頁數/Section/字體/頁碼/溢出,只印問題            |
| `make_skeleton.py`    | 依頁型清單產「保證過驗證器」的 spec 骨架                            |
| `README_TOOLS.md`     | 給模型的速查卡:標準三步指令 + plan 格式 + 鐵律                      |

**11 種註冊頁型 = 純 script 產出,LLM 零參與**(含折線趨勢頁圖表數據):使用者 JSON → 驗證 → render_deck
自動產檔 → qa_check,全程模型只負責跑指令和轉述結果。只有用到 page_types.md
其他 40+ 種頁型的頁,模型才需要寫一小段 render_plan(該頁的文字替換清單)。

反循環機制:render_deck 每次從模板重新生成整份檔,錯誤(UNMATCHED/qa FAIL)
永遠回到「改輸入的某一條」再整檔重跑——不存在「刪掉壞頁再補一頁」這種
會累積損傷的操作;同一份輸入跑一萬次結果都一樣。

實測產出可眼見為憑:`engine/examples/demo_output_01_minimal.pptx`(4 頁)、
`engine/examples/demo_output_02_full10p.pptx`(10 頁全自動、零 plan、qa 零警告)。

## 包內檔案

| 檔案                                    | 用途                                                                     | 放哪裡                           |
| --------------------------------------- | ------------------------------------------------------------------------ | -------------------------------- |
| `instructions.md`                       | GPTs 系統指示全文(含版本代號)                                            | 貼進 GPT Builder「Instructions」 |
| `engine/rules/validate_slide_spec_gpts.py` | 驗證器(兩級閘門;PAGE_TYPES 單一真相來源)                                 | 上傳到 Knowledge                 |
| `engine/rules/page_types_registry.md`   | slide_spec.json 撰寫指南 + 11 種註冊頁型契約                             | 上傳到 Knowledge                 |
| `engine/rules/outline_to_ppt_skill.md`  | 段落大綱一鍵產生合規 JSON、渲染 PPT 與 QA 的繁中工作流                   | 上傳到 Knowledge                 |
| `engine/rules/page_types.md`            | 完整頁型庫 40+ 種(跨模板語意庫;頁碼對照在各模板包 page_map.md)           | 上傳到 Knowledge                 |
| `engine/rules/style_guide.md`           | 視覺規範(排版紀律共用;視覺常數以 light 包 manifest 為機器真相)           | 上傳到 Knowledge                 |
| `engine/rules/slide_spec.schema.json`   | spec 結構定義                                                            | 上傳到 Knowledge                 |
| `engine/rules/slide_spec.example.json`  | 通過驗證的完整範例                                                       | 上傳到 Knowledge                 |
| `engine/rules/slide_spec.bad.example.json` | 會 FAIL 的範例(驗收測試用)                                               | 上傳到 Knowledge                 |
| `dist/template_light.zip`               | light 模板包:template.pptx + manifest + bindings + page_map + 素材(源碼在 `engine/templates/light/`) | 上傳到 Knowledge                 |
| `dist/tools.zip`                        | 工具腳本 ×11 + 速查卡(源碼在 `engine/tools/`)                                   | 上傳到 Knowledge                 |
| `engine/examples/01_*.json`–`04_*.json` | 四份試用範例(最小/完整/未註冊頁型/故意違規)                              | 不上傳,發給使用者試              |
| `engine/examples/02_full_10p.source_slides.md` | 已切頁的 validator provenance 測試 fixture                               | 不上傳,測試用                    |
| `engine/examples/05_outline_to_ppt_source.md` | 真正未切頁、無頁型指示的一鍵大綱輸入 fixture                             | 不上傳,測試用                    |
| `engine/examples/demo_output_*.pptx`    | 本機實測產出,眼見為憑                                                    | 不上傳                           |
| `engine/templates/light/assets_src/`    | 素材可編輯源檔(隨包;打包 template_light.zip 時以 arcname `assets/` 映射) | 不上傳,留在 repo                 |
| `engine/templates/`(其餘檔案)           | 模板包源碼與治理文件(INDEX、TEMPLATE_LIFECYCLE、各包 REGRESSION/FEEDBACK) | 不上傳,留在 repo                 |
| `../docs/給設計師/`                     | 非技術版說明(4 份:入口 + 專案說明 + 路線 A/B),整包發給設計師           | 不上傳,直接發給人看              |
| `../docs/FEEDBACK.md`                   | 回饋台帳(症狀→規則化→發版的追蹤表)                                       | 不上傳,留在 repo                 |
| `feedback_evidence/`                    | GPT Builder 實測對話逐字稿(FEEDBACK 台帳引用的證據)                       | 不上傳,留在 repo                 |
| `../engine/REGRESSION.md`               | 發版前本機回歸:R0–R10 可執行案例與預期結果                                | 不上傳,留在 repo                 |
| `../docs/WORKLOG.md`                    | 決策紀錄:架構演進、取捨理由、已知風險,接手必讀                           | 不上傳,留在 repo                 |

> 已經建好、只是要發新版?直接用 [`DEPLOY.md`](DEPLOY.md)(一頁操作稿)。

## 建置步驟(約 15 分鐘)

1. ChatGPT(需 Plus/Team/Enterprise)→ 頭像選單 → **My GPTs → Create a GPT**,
   切到 **Configure** 分頁(不要用左邊的對話式 Create,設定會比較精準)。
2. **Name / Description**:自訂,例如「簡報產生器(內部)」/「給我一份合規的
   slide_spec.json,產出公司規範的 16:9 繁中簡報;模板素材全內建」。
3. **Instructions**:貼上 `instructions.md` 分隔線以下的全文。
4. **Knowledge**:上傳上表 10 個檔案(engine/rules 的 8 個散檔 + dist/ 的
   2 個 zip;GPTs 上限 20 個檔,
   維持 ≤19 紀律,約可再容 9 個模板包)。
5. **Capabilities 與 Model**:
   - ✅ **Code Interpreter & Data Analysis**(必開,整個流程靠它)
   - ❌ Web Browsing(關,避免內容混入外部資料)
   - ❌ DALL·E / 圖片生成(關;此流程完全不生圖)
   - ⚠ **Recommended Model 務必指定最強可用模型**(2026-07-21 實測:指定
     GPT-5.6 Pro 後全流程完美)。未指定時使用者端可能路由到輕量模型,會出現
     FEEDBACK #1/#2 的整套失敗行為:不看 /mnt/data 就宣稱做不到、反要使用者
     上傳工具、改用 python-pptx 手產、拋選項選單。instructions 的 v1.10/v1.11
     防線就是為弱模型情境保留的,不可因強模型表現好而移除。
6. **Conversation starters** 建議:
   - 「直接貼上段落大綱,一次產出 JSON 與 PPT(不需任何指令)」
   - 「這是我的 slide_spec.json,幫我產出 PPT」
   - 「給我一份 slide_spec.json 空白骨架,頁型:封面、目錄、三欄說明、封底」
   - 「slide_spec.json 要怎麼寫?有哪些頁型可以用?」
   - 「驗證失敗了,幫我看錯誤怎麼修」
7. 儲存,分享範圍選「Anyone with the link」或 Team workspace。

## 驗收測試(建好後必做)

> **v2.0 狀態(2026-07-25):多模板架構 Phase 1 已在本機實作;GPT Builder
> 驗收待執行;尚未發布。** 下列 GPT Builder 項目是發版閘門,不是已通過紀錄。
> ⚠ 實測回報「卡在一半說無法用工具產生/沒有穩定的工具鏈/請上傳工具」的第一
> 檢查點:問 GPT「你現在是哪一版?」——不是 `v2.0-20260725` 就代表 Builder 端
> 還在跑舊版,先同步 instructions 與 10 個知識檔(特別是 outline_to_ppt_skill.md、
> tools.zip 與 template_light.zip;**並刪除舊的 assets.zip 與
> light_template.pptx**)再測。兩次實測失敗紀錄見 FEEDBACK #1、#2。

1. 對 GPTs 說:「執行環境準備,然後用知識庫的 slide_spec.bad.example.json 和
   slide_spec.example.json 各跑一次驗證器,貼出結果。」
   - 必須先建立 `/mnt/data/tools`,再把 archive root 是工具檔的 `tools.zip` 解到該目錄
   - 必須先建立 `/mnt/data/templates/light`,再把 `template_light.zip` 解到該目錄,
     並印出 manifest 的 template_id 與 version(環境自證)
   - bad example 必須 **FAIL** 並列出一串 ERROR
   - example 必須 **PASS**(可能有 WARN)
   - ✅ 2026-07-20 已在本機(Python 3.14 + python-pptx 1.0.2)完整實測:驗證器
     正反例、兩級閘門、工具鏈全流程(含帶圖頁複製、錯誤路徑)全數通過,
     詳見 docs/WORKLOG.md §7.1。沙箱環境仍建議跑一次此步驟確認版本差異無影響。
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
   - 環境先出現 `/mnt/data/tools/` 與 `/mnt/data/templates/light/`
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

本機以全新暫存目錄跑 [`engine/REGRESSION.md`](../engine/REGRESSION.md) 的
R0–R10 全部案例(archive 完整性、examples 預期 exit、稽核/title 注入/數字 token
閘門、QA WARN 仍 PASS、strict 與直供全流程、fixture 純淨度、Knowledge 清單與
hash、多模板雙包、全包 lint),全綠才發版;重打包 zip 後同步更新該檔的 hash 基準。

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
   `PAGE_TYPES`(流程見 [`docs/MAINTENANCE.md`](../docs/MAINTENANCE.md) §1)。
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

## 同步紀律(GPTs 端)

GPTs 只有**擁有者**能編輯,所以要指定一位管理者(建議就是維護本 repo 的人),
並讓所有修改走 repo:

1. **真相來源永遠是 repo**:指示改 `gpts/instructions.md`、規則改
   `engine/rules/*`,一律先改 repo、commit,再由管理者同步到 GPT Builder
   (貼指示 / 刪舊傳新知識檔)。不要直接在 Builder 裡改完就算——下次同步會被
   repo 版蓋掉。
2. **版本代號**:指示開頭埋了版本字串與可用模板 roster,每次同步都要更新
   (模板包重傳也算)。使用者問 GPT「你現在是哪一版?」就能確認手上是不是最新版,
   回報問題時也請附上版本代號。
3. **回饋管道**:開一個固定收集點(Slack/Teams 頻道或共用表單),回報格式與
   規則化流程見 [`docs/FEEDBACK.md`](../docs/FEEDBACK.md)。
4. **改完先驗收再發版**:完整步驟見 [`docs/MAINTENANCE.md`](../docs/MAINTENANCE.md)
   的「發佈 checklist」;上傳前跑本檔「驗收測試」全部項目 +
   [`engine/REGRESSION.md`](../engine/REGRESSION.md) R0–R10。

> 改頁型契約、加模板、重打包 zip 的操作細節,一律見
> [`docs/MAINTENANCE.md`](../docs/MAINTENANCE.md)——那些是**引擎級**維護,
> 不限於 GPTs 前端。
