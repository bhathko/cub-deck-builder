# ppt_ai2 — GPTs 簡報產生器建置包

把「合規的 slide_spec.json(或大綱內容)→ 公司規範的 16:9 繁中簡報」做成
ChatGPT GPTs,讓團隊直接使用。**一切都在 [`gpts/`](gpts/) 目錄**:

| 入口 | 內容 |
|---|---|
| [`gpts/README.md`](gpts/README.md) | 建置手冊:上傳什麼、怎麼設定、驗收測試、回饋流程 |
| [`gpts/WORKLOG.md`](gpts/WORKLOG.md) | 決策紀錄與已知風險,**接手維護必讀** |
| [`gpts/instructions.md`](gpts/instructions.md) | GPTs 系統指示(含版本代號) |
| `gpts/knowledge/` | 上傳 GPTs 的 10 個知識檔(規則、模板、素材、工具包)——**規則的單一真相來源** |
| `gpts/tools/` | 工具腳本源碼(渲染、驗證、自檢;改完要重打包 tools.zip) |
| `gpts/examples/` | 試用範例 JSON ×4 + 實測產出 pptx |
| `gpts/assets_src/` | 素材源檔(背景/logo;改完重打包 knowledge/assets.zip) |

## 本機快速驗證(需 Python 3 + python-pptx)

照 `gpts/WORKLOG.md` §7.1 的沙箱做法:建一個模擬 /mnt/data 的暫存目錄,
把 `gpts/assets_src` 複製進去改名為 `assets`、連同 `gpts/tools/`、
`gpts/knowledge/validate_slide_spec_gpts.py`、`light_template.pptx` 一起放入,
然後跑 `gpts/tools/README_TOOLS.md` 的三步指令(驗證 → 產檔 → 自檢)。
spec 內的素材路徑(`assets/backgrounds/...`)是以該目錄為根解析的。

## 歷史

本 repo 原有兩條產 PPT 管線(Codex `baoyu-slide-deck` 圖生圖主力、`fallback/`
spec 閘門備援),2026-07-20 轉向 GPTs 建置包並移除舊管線目錄
(`.agents/`、`fallback/`、`my_project/`)。舊管線的可用資產
(驗證器、頁型庫、模板、風格規範、素材)都已收進 `gpts/` 持續維護。
