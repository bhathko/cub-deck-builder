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
使用者不會寫 JSON 也沒關係:對 GPTs 要空白骨架、或直接貼內容文字請它代擬 JSON
(代擬稿須經使用者確認才會產檔,且會開啟防幻覺追溯)。

## 工具層(`tools/` → `knowledge/tools.zip`)

產檔的機械動作全部由七個預寫檔案執行,模型只在「未涵蓋頁型」時手產一份小小的
`render_plan.json`——這是「精準 + 省 token + 不進 QA 死循環」的核心設計:

| 腳本 | 角色 |
|---|---|
| `pptx_toolkit.py` | 投影片複製(含 rels 重映射,圖不破)/刪除/排序/清 Section |
| `text_tools.py` | 群組內層文字替換(保留原字級顏色)、CJK 溢出估算、縮字 |
| `fills.py` | **10 種註冊頁型的確定性填充引擎**:5 種自動填入模板頁(shape id 寫死) |
| `inspect_template.py` | 模板盤點:`--summary` 全冊一頁一行、`--page N` 單頁形狀樹(省 token) |
| `render_deck.py` | 主程式:spec(+選配 plan)→ pptx,**冪等整檔重生**;5 種頁型內建版面 |
| `qa_check.py` | 產檔後自檢:內容覆蓋/頁數/Section/字體/頁碼/溢出,只印問題 |
| `make_skeleton.py` | 依頁型清單產「保證過驗證器」的 spec 骨架 |
| `README_TOOLS.md` | 給模型的速查卡:標準三步指令 + plan 格式 + 鐵律 |

**10 種註冊頁型 = 純 script 產出,LLM 零參與**:使用者 JSON → 驗證 → render_deck
自動產檔 → qa_check,全程模型只負責跑指令和轉述結果。只有用到 page_types.md
其他 40+ 種頁型的頁,模型才需要寫一小段 render_plan(該頁的文字替換清單)。

反循環機制:render_deck 每次從模板重新生成整份檔,錯誤(UNMATCHED/qa FAIL)
永遠回到「改輸入的某一條」再整檔重跑——不存在「刪掉壞頁再補一頁」這種
會累積損傷的操作;同一份輸入跑一萬次結果都一樣。

實測產出可眼見為憑:`examples/demo_output_01_minimal.pptx`(4 頁)、
`examples/demo_output_02_full10p.pptx`(10 頁全自動、零 plan、qa 零警告)。

## 包內檔案

| 檔案 | 用途 | 放哪裡 |
|---|---|---|
| `instructions.md` | GPTs 系統指示全文(含版本代號) | 貼進 GPT Builder「Instructions」 |
| `knowledge/validate_slide_spec_gpts.py` | 驗證器(兩級閘門;PAGE_TYPES 單一真相來源) | 上傳到 Knowledge |
| `knowledge/page_types_registry.md` | slide_spec.json 撰寫指南 + 10 種註冊頁型契約 | 上傳到 Knowledge |
| `knowledge/page_types.md` | 完整頁型庫 40+ 種 | 上傳到 Knowledge |
| `knowledge/light_template.pptx` | 公司模板本體,產檔時複製頁改字 | 上傳到 Knowledge |
| `knowledge/style_guide.md` | 視覺規範 | 上傳到 Knowledge |
| `knowledge/slide_spec.schema.json` | spec 結構定義 | 上傳到 Knowledge |
| `knowledge/slide_spec.example.json` | 通過驗證的完整範例 | 上傳到 Knowledge |
| `knowledge/slide_spec.bad.example.json` | 會 FAIL 的範例(驗收測試用) | 上傳到 Knowledge |
| `knowledge/assets.zip` | 背景圖 ×3 + logo | 上傳到 Knowledge |
| `knowledge/tools.zip` | 工具腳本 ×7 + 速查卡(源碼在 `tools/`) | 上傳到 Knowledge |
| `examples/*.json` | 四份試用範例(最小/完整/未註冊頁型/故意違規) | 不上傳,發給使用者試 |
| `examples/02_full_10p.source_slides.md` | 內容模式(--slides 追溯)測試 fixture | 不上傳,測試用 |
| `examples/demo_output_*.pptx` | 本機實測產出,眼見為憑 | 不上傳 |
| `assets_src/` | 素材可編輯源檔;重打包 assets.zip 時需先把資料夾改名/複製為 `assets` 再壓 | 不上傳,留在 repo |
| `FEEDBACK.md` | 回饋台帳(症狀→規則化→發版的追蹤表) | 不上傳,留在 repo |
| `WORKLOG.md` | 決策紀錄:架構演進、取捨理由、已知風險,接手必讀 | 不上傳,留在 repo |

## 建置步驟(約 15 分鐘)

1. ChatGPT(需 Plus/Team/Enterprise)→ 頭像選單 → **My GPTs → Create a GPT**,
   切到 **Configure** 分頁(不要用左邊的對話式 Create,設定會比較精準)。
2. **Name / Description**:自訂,例如「簡報產生器(內部)」/「給我一份合規的
   slide_spec.json,產出公司規範的 16:9 繁中簡報;模板素材全內建」。
3. **Instructions**:貼上 `instructions.md` 分隔線以下的全文。
4. **Knowledge**:上傳上表 10 個檔案(`knowledge/` 內全部;GPTs 上限 20 個檔,
   還有餘裕)。
5. **Capabilities**:
   - ✅ **Code Interpreter & Data Analysis**(必開,整個流程靠它)
   - ❌ Web Browsing(關,避免內容混入外部資料)
   - ❌ DALL·E / 圖片生成(關;此流程完全不生圖)
6. **Conversation starters** 建議:
   - 「這是我的 slide_spec.json,幫我產出 PPT」
   - 「給我一份 slide_spec.json 空白骨架,頁型:封面、目錄、三欄說明、封底」
   - 「slide_spec.json 要怎麼寫?有哪些頁型可以用?」
   - 「驗證失敗了,幫我看錯誤怎麼修」
7. 儲存,分享範圍選「Anyone with the link」或 Team workspace。

## 驗收測試(建好後必做)

1. 對 GPTs 說:「執行環境準備,然後用知識庫的 slide_spec.bad.example.json 和
   slide_spec.example.json 各跑一次驗證器,貼出結果。」
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

## 誠實的限制(建議原文轉達給主管)

1. **閘門是「指示強制」不是「系統強制」。** 模型理論上可能偷懶跳過驗證。緩解:
   指示要求它貼出驗證器輸出,使用者驗收時認「結果:PASS」那行;沒看到就要求重跑。
   要 100% 系統強制,得改用 GPTs Actions 接自家 API(把驗證+渲染放伺服器端),
   工程量另計。
2. **視覺一致性:機械部分已確定化,判斷部分仍靠模型。** 複製頁、換字、刪頁、
   排序、頁碼、五種內建版面都由 tools 腳本固定執行,不再漂移;模型剩下的自由度
   只在未涵蓋頁型的 render_plan(哪個框填哪段字),錯了是改一條 plan 重跑。
   模型看不到知識庫裡的參考圖片(GPTs 對知識庫圖檔沒有視覺理解),精緻度仍需
   設計師收尾。
   另外:未註冊頁型(page_types.md 那 40+ 種)的槽位容量只靠模型自律,程式閘門
   對它們只驗基本結構與素材存在;需要嚴格保證的頁型,長期解是把它註冊進
   `PAGE_TYPES`(見下方維護節)。
   最後:JSON 直供模式沒有內容來源檔,驗證器的防幻覺追溯(捏造數字比對)自動
   關閉——內容正確性由寫 JSON 的人負責。若某次是請 GPTs 從原文代擬 JSON,
   內容模式會把原文存成 /mnt/data/slides.md 並在驗證時加 `--slides`,
   追溯就會重新開啟。
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
2. **版本代號。** 指示開頭埋了版本字串(目前 `v1.3-20260720`),每次同步時更新。
   使用者對 GPTs 問「你現在是哪一版?」就能確認自己用到的是不是最新版,
   回報問題時也請附上版本代號。
3. **回饋管道。** 開一個固定收集點(Slack/Teams 頻道或共用表單皆可),回報格式:
   版本代號 + 所用的 slide_spec.json + 產出檔或截圖 + 哪一頁哪裡不對。
   沒有 JSON 的回報很難重現,管理者可以直接退回補件。
4. **回饋分流。** 版面不像模板/文字溢出 → 改 `instructions.md` 的規則或
   `page_types.md` 描述;閘門漏擋或誤擋 → 改 `validate_slide_spec_gpts.py`
   (同步 schema 與 registry,見下方維護節);想要新頁型 → 走下方「維護」節的
   註冊流程。
5. **改完先驗收再發版。** 每次重新上傳後,跑一輪「驗收測試」節的四步 +
   `examples/` 四份範例,PASS 才通知團隊更新。

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

| 症狀 | 改哪裡 |
|---|---|
| 文字溢出、字級跑掉 | `instructions.md` 溢出規則,或調低 `page_types_registry.md` 該欄位字數上限 |
| 版面跟模板不像、元素亂跑 | `page_types.md` 該頁型的「視覺結構」描述補細節(位置、比例講死) |
| 配色、卡片樣式、logo/頁碼不對 | `style_guide.md` 補規則 |
| 明顯違規的 JSON 沒被擋 / 合規的被誤擋 | `validate_slide_spec_gpts.py`(同步 schema 與 registry,見下方維護節) |
| 破圖、頁序錯、Section 殘留、封面/目錄版面偏移等機械問題 | `tools/` 對應腳本,改完重打包 `tools.zip` 上傳 |
| 同一頁型每次產出長得不一樣 | 最強解:把該頁型註冊進 `PAGE_TYPES` + registry + fills,升級成全自動 |
| 它跳過驗證就產檔 | `instructions.md` 絕對規則區加重申;驗收時堅持要看 PASS 輸出 |

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
`assets` 的資料夾重打包 `assets.zip`。模板改版:照 `WORKLOG.md` §9 的
shape id 重盤點流程。改完把異動檔**重新上傳**到 GPTs 知識庫並刪掉舊檔;
「gpts/ 目錄有異動 → 重新上傳知識庫」寫進團隊的發版 checklist。
