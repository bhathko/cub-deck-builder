# AGENTS.md — cub-deck-builder 流程契約(所有 agent 共用)

> 團隊共用、隨 repo 分享的流程契約。任何 agent 在本 repo 工作時**必須**遵循。
> 2026-07-25 起本 repo = **簡報產生器:單引擎(`engine/`)+ 兩個延伸應用**
> (`gpts/` GPTs 發佈包、`.codex/skills/` 本機 CLI);舊管線(.agents/fallback/
> my_project)已移除;歷史與決策脈絡見 [`docs/WORKLOG.md`](docs/WORKLOG.md)。

## 這個專案

維護一條確定性簡報管線:使用者給 slide_spec.json(或大綱內容),引擎跑
驗證閘門與確定性 renderer,產出公司規範、繁體中文、16:9 的可編輯 .pptx;
模板以「模板包」註冊(預設 light,見 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md))。
兩個前端:ChatGPT GPTs(建置手冊 [`gpts/README.md`](gpts/README.md))與
本機 Codex CLI(`.codex/skills/`)。

## 硬規則

1. **SSOT 分兩處**:語意契約與共用規範(驗證器 `PAGE_TYPES`、頁型語意庫、
   排版紀律)在 `engine/rules/`;**模板知識(模板本體、綁定、素材、視覺
   常數)在 `engine/templates/<id>/`,manifest.json 為機器真相**(多模板架構
   見 `docs/ARCHITECTURE.md`)。`gpts/instructions.md` 是 GPTs 指示的原稿。
2. **契約同步**:`engine/rules/validate_slide_spec_gpts.py` 的 `PAGE_TYPES` 是
   頁型契約**唯一手寫真相**。改完:①跑
   `python engine/release/template_admin.py sync-docs --write` 重生
   `slide_spec.schema.json` 的 enum(**機器強制**:漂移時 `pack` 會拒絕打包);
   ②`engine/rules/page_types_registry.md` **目前仍須手改**(它有約三分之一是
   人寫語意,尚未生成;刻意不生成的理由見 `engine/release/sync_docs.py` 檔頭)。
   文件一律**不寫「共 N 種頁型」**——寫死的數字會過期,而過期的數字會讓模型
   拒用新頁型(2026-07-26 實際發生過,見 commit `3f22aff`);要數量就指向
   `make_skeleton.py --list`。
3. **渲染層零隨機**:版面確定性是本專案的核心資產,不得在 renderer 加入任何
   隨機性或「AI 自由發揮」;多樣性只能來自頁型庫擴充。
4. **綁定與模板 pptx 硬耦合,以包為界**:每包填充綁定(shape id)住在
   `engine/templates/<id>/bindings.json`(宣告式,fills_engine 解譯;light 另有
   builders-only 的 bindings.py grandfather),只對同包模板檔有效,以
   manifest `template_sha256` + inventory.json 對照。模板改版必走
   `engine/templates/TEMPLATE_LIFECYCLE.md`(`inspect_template.py --verify`
   漂移偵測、核對 bindings、golden+examples 全綠才可發版)。
5. **改動即重打包,一包一鏡像**:改 `engine/tools/*` → 重打包
   `gpts/dist/tools.zip`;改 `engine/templates/<id>/`(含
   `assets_src/`,打包時映射為 `assets/`)→ 重打包
   `gpts/dist/template_<id>.zip`;並更新 `gpts/instructions.md` 的
   版本字串與模板 roster 行。zip 一律 Python zipfile、正斜線 arcname。
6. **內容忠實**:任何路徑都嚴禁替使用者發明數字、指標、KPI、專案名、日期。
   GPTs 內容模式必須落地 slides.md 並帶 `--slides` 開啟捏造數字硬擋。
7. **生圖政策照舊**:本管線不生圖(全部 PowerPoint 可編輯物件);
   不得引入任何生圖工具。
8. **雙前端、單引擎**:`.codex/skills/outline-to-ppt/` 是同一條管線的本機
   Codex CLI 前端,只內聯環境差異(鐵律摘要 + 跨平台沙箱腳本
   `prepare_env.py`,把工具鏈複製成 `ppt_out/` 模擬 /mnt/data;命令全為單行
   python,PowerShell/cmd/bash 通用——團隊有 Windows 使用者且公司禁 WSL),
   規則本體仍指回 `engine/rules/` 與 `engine/tools/`,不得在 skill 裡另寫一份
   規則。`.codex/skills/` 下**所有** skill(含 `register-template`)改動後,
   把 repo 版複製到 `~/.codex/skills/<名稱>/`(含重打同名 zip,POSIX 路徑)。
   本機產物一律進 gitignore 的 `ppt_out/`,嚴禁 commit。
9. **綁定準入**:新模板的填充綁定一律是宣告式 `bindings.json`(固定 op
   詞彙表,v1.1 為 7 op 含 chart;`fills_engine` 解譯;表達不了=該頁型降級 clone,嚴禁在註冊對話中擴詞彙表
   或改寫 Python);必過 `template_admin.py lint`(含全覆蓋原則)+ `golden`
   (min/max 渲染+qa+連跑兩次 shape 樹全等)才可 register。模板包無權新增
   語意頁型;golden fixtures(`engine/golden/`)對註冊流程唯讀。
10. **模板隔離與註冊入口**:註冊一律走 skill,不在對話裡手做——
    `.codex/skills/register-template/`(新模板從零建包)與
    `.codex/skills/add-page-types/`(既有模板加開頁型)是**兩個**入口,
    分工見各自檔頭;GPTs 端只消費模板包,沙箱無持久化。涉及模板 X 的 commit 只准
    觸碰 `engine/templates/X/**`、`gpts/dist/template_X.zip`、
    `engine/templates/INDEX.md`、`gpts/instructions.md`(版本字串/roster 行),
    以 `template_admin.py isolation` 機器驗證,越界改動拆 commit。
11. **Knowledge 檔數預算 ≤19**(上限 20 常備 1 空位):新模板上傳前先數檔;
    將觸頂依序 examples 併 docs.zip → 評估分 GPT。不得把模板包塞進 tools.zip。

## 常用指令(本機需 Python 3 + python-pptx)

### 產檔三步(依序跑,前一步 exit 0 才進下一步)

**1. spec 閘門**——產檔前擋結構/槽位數量/字數/頁碼/素材與防幻覺追溯

```bash
python engine/rules/validate_slide_spec_gpts.py --spec <spec.json> --asset-dir <素材根目錄>
```

**2. 產檔**——模板檔自動取自選定包(`deck.template`,預設 `light`)

```bash
python engine/tools/render_deck.py --spec <spec> --asset-dir <素材根目錄> --out <out.pptx>
```

**3. 產檔後自檢**——擋頁數不符/內容遺漏/文字壓到鄰欄,並警示溢出與字體

```bash
python engine/tools/qa_check.py --spec <spec> --pptx <out.pptx>
```

### 模板盤點(寫綁定或模板改版時)

**盤點形狀樹**——一頁一行的概覽,拿 shape id 當替換錨點前先跑

```bash
python engine/tools/inspect_template.py --pptx engine/templates/light/template.pptx --summary
```

**漂移偵測**——模板改版必跑,sha 不符 = 盤點未完成,不得發版

```bash
python engine/tools/inspect_template.py --verify engine/templates/light
```

> 維護與發佈的操作步驟(契約同步、重打包、發佈 checklist)見
> [`docs/MAINTENANCE.md`](docs/MAINTENANCE.md);回饋處理見
> [`docs/FEEDBACK.md`](docs/FEEDBACK.md)。
