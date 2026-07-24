# AGENTS.md — ppt_ai2 流程契約(所有 agent 共用)

> 團隊共用、隨 repo 分享的流程契約。任何 agent 在本 repo 工作時**必須**遵循。
> 2026-07-20 起本 repo = **GPTs 簡報產生器建置包**,舊管線(.agents/fallback/
> my_project)已移除;歷史與決策脈絡見 [`gpts/WORKLOG.md`](gpts/WORKLOG.md)。

## 這個專案

維護一個 ChatGPT GPTs 建置包:使用者給 slide_spec.json(或大綱內容),GPTs 在
Code Interpreter 裡跑驗證閘門與確定性 renderer,產出 Cathay 淺色企業風、
繁體中文、16:9 的可編輯 .pptx。設定與流程見 [`gpts/README.md`](gpts/README.md)。

## 硬規則

1. **規則的單一真相來源 = `gpts/knowledge/`。** 驗證器 `PAGE_TYPES`、頁型庫、
   風格規範、模板都以該目錄為準;`gpts/instructions.md` 是 GPTs 指示的原稿。
2. **三處同步**:改頁型契約時,`gpts/knowledge/validate_slide_spec_gpts.py` 的
   `PAGE_TYPES`、`gpts/knowledge/slide_spec.schema.json` 的 enum、
   `gpts/knowledge/page_types_registry.md` 三處一起改。
3. **渲染層零隨機**:版面確定性是本專案的核心資產,不得在 renderer 加入任何
   隨機性或「AI 自由發揮」;多樣性只能來自頁型庫擴充。
4. **fills.py 與 light_template.pptx 硬耦合**:模板改版後必須重新盤點 shape id
   (`inspect_template.py`)、核對 `fills.py`、跑 examples 全綠才可發版,
   流程見 `gpts/WORKLOG.md` §9。
5. **工具改動要重打包**:改 `gpts/tools/*` → 重打包 `gpts/knowledge/tools.zip`;
   改 `gpts/assets_src/*` → 複製為名為 `assets` 的資料夾重打包
   `gpts/knowledge/assets.zip`;並更新 `gpts/instructions.md` 的版本字串。
6. **內容忠實**:任何路徑都嚴禁替使用者發明數字、指標、KPI、專案名、日期。
   GPTs 內容模式必須落地 slides.md 並帶 `--slides` 開啟捏造數字硬擋。
7. **生圖政策照舊**:本管線不生圖(全部 PowerPoint 可編輯物件);
   不得引入任何生圖工具。
8. **雙前端、單引擎**:`.codex/skills/outline-to-ppt/` 是同一條管線的本機
   Codex CLI 前端,只內聯環境差異(鐵律摘要 + 跨平台沙箱腳本
   `prepare_env.py`,把工具鏈複製成 `ppt_out/` 模擬 /mnt/data;命令全為單行
   python,PowerShell/cmd/bash 通用——團隊有 Windows 使用者且公司禁 WSL),
   規則本體仍指回 `gpts/knowledge/` 與 `gpts/tools/`,不得在 skill 裡另寫一份
   規則。改 gpts 規則或工具後,檢查該摘要是否需同步,並把 repo 版複製到
   `~/.codex/skills/outline-to-ppt/`(含重打同名 zip,POSIX 路徑)。
   本機產物一律進 gitignore 的 `ppt_out/`,嚴禁 commit。

## 常用指令(本機需 Python 3 + python-pptx)

```
python gpts/knowledge/validate_slide_spec_gpts.py --spec <spec.json> --asset-dir <素材根目錄>
python gpts/tools/render_deck.py --spec <spec> --template gpts/knowledge/light_template.pptx --asset-dir <素材根目錄> --out <out.pptx>
python gpts/tools/qa_check.py --spec <spec> --pptx <out.pptx>
python gpts/tools/inspect_template.py --pptx gpts/knowledge/light_template.pptx --summary
```

> 發版前必跑 `gpts/README.md` 的「驗收測試」與 examples 全綠;
> 回饋處理流程與版本紀律見同檔「回饋與版本更新流程」。
