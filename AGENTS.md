# AGENTS.md — ppt_ai2 流程契約(所有 agent 共用)

> 團隊共用、隨 repo 分享的流程契約。任何 agent 在本 repo 工作時**必須**遵循。
> 2026-07-20 起本 repo = **GPTs 簡報產生器建置包**,舊管線(.agents/fallback/
> my_project)已移除;歷史與決策脈絡見 [`gpts/WORKLOG.md`](gpts/WORKLOG.md)。

## 這個專案

維護一個 ChatGPT GPTs 建置包:使用者給 slide_spec.json(或大綱內容),GPTs 在
Code Interpreter 裡跑驗證閘門與確定性 renderer,產出 Cathay 淺色企業風、
繁體中文、16:9 的可編輯 .pptx。設定與流程見 [`gpts/README.md`](gpts/README.md)。

## 硬規則

1. **SSOT 分兩處**:語意契約與共用規範(驗證器 `PAGE_TYPES`、頁型語意庫、
   排版紀律)在 `gpts/knowledge/`;**模板知識(模板本體、綁定、素材、視覺
   常數)在 `gpts/templates/<id>/`,manifest.json 為機器真相**(多模板架構
   見 `gpts/TEMPLATE_PACKS.md`)。`gpts/instructions.md` 是 GPTs 指示的原稿。
2. **三處同步**:改頁型契約時,`gpts/knowledge/validate_slide_spec_gpts.py` 的
   `PAGE_TYPES`、`gpts/knowledge/slide_spec.schema.json` 的 enum、
   `gpts/knowledge/page_types_registry.md` 三處一起改。
3. **渲染層零隨機**:版面確定性是本專案的核心資產,不得在 renderer 加入任何
   隨機性或「AI 自由發揮」;多樣性只能來自頁型庫擴充。
4. **light 綁定與 light_template.pptx 硬耦合**:填充綁定(shape id)住在
   `gpts/templates/light/bindings.py`(多模板架構 Phase 0,設計見
   `gpts/TEMPLATE_PACKS.md`)。模板改版必走
   `gpts/templates/TEMPLATE_LIFECYCLE.md`:重新盤點 shape id
   (`inspect_template.py`)、核對 bindings、examples 全綠才可發版。
5. **改動即重打包,一包一鏡像**:改 `gpts/tools/*` → 重打包
   `gpts/knowledge/tools.zip`;改 `gpts/templates/<id>/`(含
   `assets_src/`,打包時映射為 `assets/`)→ 重打包
   `gpts/knowledge/template_<id>.zip`;並更新 `gpts/instructions.md` 的
   版本字串與模板 roster 行。zip 一律 Python zipfile、正斜線 arcname。
6. **內容忠實**:任何路徑都嚴禁替使用者發明數字、指標、KPI、專案名、日期。
   GPTs 內容模式必須落地 slides.md 並帶 `--slides` 開啟捏造數字硬擋。
7. **生圖政策照舊**:本管線不生圖(全部 PowerPoint 可編輯物件);
   不得引入任何生圖工具。
8. **雙前端、單引擎**:`.codex/skills/outline-to-ppt/` 是同一條管線的本機
   Codex CLI 前端,只內聯環境差異(鐵律摘要 + 跨平台沙箱腳本
   `prepare_env.py`,把工具鏈複製成 `ppt_out/` 模擬 /mnt/data;命令全為單行
   python,PowerShell/cmd/bash 通用——團隊有 Windows 使用者且公司禁 WSL),
   規則本體仍指回 `gpts/knowledge/` 與 `gpts/tools/`,不得在 skill 裡另寫一份
   規則。`.codex/skills/` 下**所有** skill(含 `register-template`)改動後,
   把 repo 版複製到 `~/.codex/skills/<名稱>/`(含重打同名 zip,POSIX 路徑)。
   本機產物一律進 gitignore 的 `ppt_out/`,嚴禁 commit。
9. **綁定準入**:新模板的填充綁定一律是宣告式 `bindings.json`(6-op 詞彙表,
   `fills_engine` 解譯;表達不了=該頁型降級 clone,嚴禁在註冊對話中擴詞彙表
   或改寫 Python);必過 `template_admin.py lint`(含全覆蓋原則)+ `golden`
   (min/max 渲染+qa+連跑兩次 shape 樹全等)才可 register。模板包無權新增
   語意頁型;golden fixtures(`gpts/golden/`)對註冊流程唯讀。
10. **模板隔離與註冊入口**:`.codex/skills/register-template/` 是唯一註冊
    入口(GPTs 端只消費模板包,沙箱無持久化);涉及模板 X 的 commit 只准
    觸碰 `gpts/templates/X/**`、`gpts/knowledge/template_X.zip`、
    `gpts/templates/INDEX.md`、`gpts/instructions.md`(版本字串/roster 行),
    以 `template_admin.py isolation` 機器驗證,越界改動拆 commit。
11. **Knowledge 檔數預算 ≤19**(上限 20 常備 1 空位):新模板上傳前先數檔;
    將觸頂依序 examples 併 docs.zip → 評估分 GPT。不得把模板包塞進 tools.zip。

## 常用指令(本機需 Python 3 + python-pptx)

```
python gpts/knowledge/validate_slide_spec_gpts.py --spec <spec.json> --asset-dir <素材根目錄>
python gpts/tools/render_deck.py --spec <spec> --asset-dir <素材根目錄> --out <out.pptx>   # 模板檔自動取自選定包(deck.template,預設 light)
python gpts/tools/qa_check.py --spec <spec> --pptx <out.pptx>
python gpts/tools/inspect_template.py --pptx gpts/templates/light/template.pptx --summary
python gpts/tools/inspect_template.py --verify gpts/templates/light                        # 模板改版漂移偵測
```

> 發版前必跑 `gpts/README.md` 的「驗收測試」與 examples 全綠;
> 回饋處理流程與版本紀律見同檔「回饋與版本更新流程」。
