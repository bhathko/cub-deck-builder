# ppt_ai2 — GPTs 簡報產生器建置包

把「合規的 slide_spec.json(或大綱內容)→ 公司規範的 16:9 繁中簡報」做成
可重複使用的**單引擎**,再以兩個延伸應用交付:ChatGPT GPTs 與本機 Codex CLI。

```
engine/            ← 主程序:產 pptx 的一切(工具、規則、模板包、golden、回歸)
gpts/              ← 延伸應用 1:ChatGPT GPTs 發佈包(instructions、上傳 zips)
.codex/skills/     ← 延伸應用 2:本機 CLI(outline-to-ppt 產檔、register-template 註冊模板)
```

| 入口 | 內容 |
| --- | --- |
| [`WORKLOG.md`](WORKLOG.md) | 決策紀錄與已知風險,**接手維護必讀** |
| [`TEMPLATE_PACKS.md`](TEMPLATE_PACKS.md) | 多模板架構設計(模板包公式、註冊流程) |
| [`gpts/README.md`](gpts/README.md) | GPTs 建置手冊:上傳什麼、怎麼設定、驗收測試、回饋流程 |
| [`gpts/instructions.md`](gpts/instructions.md) | GPTs 系統指示(含版本代號與模板 roster) |
| `engine/rules/` | 共用規則 SSOT(驗證器、schema、頁型庫、風格規範) |
| `engine/tools/` | 引擎腳本 ×11(渲染、驗證、自檢;改完重打 `gpts/dist/tools.zip`) |
| `engine/templates/` | 模板包(一模板一目錄;light 為第一個包) |
| `engine/examples/` | 試用範例 JSON ×4 + 實測產出 pptx |
| `.codex/skills/outline-to-ppt/` | 本機產檔前端(貼大綱→pptx;產物在 gitignore 的 `ppt_out/`) |
| `.codex/skills/register-template/` | 設計師註冊新模板的引導前端 |

## 本機快速驗證(需 Python 3;渲染需 python-pptx,可 `uv run --with python-pptx`)

日常本機產檔照 [`.codex/skills/outline-to-ppt/SKILL.md`](.codex/skills/outline-to-ppt/SKILL.md):
先跑 `python .codex/skills/outline-to-ppt/prepare_env.py` 建 `ppt_out/` 沙箱
(自動複製工具鏈,模擬 /mnt/data 佈局),之後所有命令都是單行 python,
**macOS / Linux / Windows PowerShell / cmd 通用**。發版前的完整回歸見
[`engine/REGRESSION.md`](engine/REGRESSION.md)。spec 內的素材路徑
(`assets/backgrounds/...`)一律以 `--asset-dir` 為根解析。

## 歷史

本 repo 原有兩條產 PPT 管線(Codex `baoyu-slide-deck` 圖生圖主力、`fallback/`
spec 閘門備援),2026-07-20 轉向 GPTs 建置包並移除舊管線目錄
(`.agents/`、`fallback/`、`my_project/`)。舊管線的可用資產
(驗證器、頁型庫、模板、風格規範、素材)持續維護於 `engine/`
(2026-07-25 重構前位於 `gpts/`,見 WORKLOG §21)。
