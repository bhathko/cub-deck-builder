# ppt_ai2 — 確定性簡報產生器

把「合規的 slide_spec.json(或一段大綱)→ 公司規範的 16:9 繁中可編輯簡報」
做成可重複使用的**單引擎**,再以兩個前端交付:ChatGPT GPTs 與本機 Codex CLI。
版面零隨機、同一份輸入跑一萬次結果相同;模板以「模板包」註冊,設計師可自行新增。

```
engine/            主程序:產 pptx 的一切(工具、規則、模板包、golden、回歸)
gpts/              前端 1:ChatGPT GPTs 發佈包(建置手冊、instructions、上傳 zips)
.codex/skills/     前端 2:本機 CLI(outline-to-ppt 產檔、register-template 註冊模板)
docs/              文件(先看 docs/README.md 挑一份;架構/維護/決策史/回饋/設計師手冊)
```

## 我該讀哪一份?

| 你是誰 / 想做什麼 | 讀這個 |
| --- | --- |
| **第一次接手這個 repo** | ① 跑一次下方「本機產一份簡報」(眼見為憑)→ ② [`AGENTS.md`](AGENTS.md)(11 條硬規則,唯一必背)→ ③ [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)(現行結構) |
| **在這個 repo 工作的 agent** | [`AGENTS.md`](AGENTS.md) 是流程契約;Claude Code 另見 [`CLAUDE.md`](CLAUDE.md) |
| **要改規則 / 加模板 / 發新版** | [`docs/MAINTENANCE.md`](docs/MAINTENANCE.md)(三處同步、重打包、發佈 checklist) |
| **想一次看懂系統現在長什麼樣** | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)(目錄、管線、模板包、綁定、驗收——**只講現況**) |
| **要在 ChatGPT 建這個 GPT** | [`gpts/README.md`](gpts/README.md)(上傳什麼、怎麼設定、能力邊界) |
| **要發版 / 換裝 GPT Builder** | [`gpts/DEPLOY.md`](gpts/DEPLOY.md)(一頁操作稿:刪什麼、傳什麼、8 條驗收指令原文) |
| **設計師 / 非技術同事** | [`docs/給設計師/`](docs/給設計師/)(白話文件夾:先看該資料夾的 README 挑一份讀;含「自己動手註冊模板」的逐步指令) |
| **產出不如預期、想回報問題** | [`docs/FEEDBACK.md`](docs/FEEDBACK.md)(怎麼回饋才會真的變好 + 台帳) |
| **想知道某個設計當初為什麼這樣決定** | [`docs/WORKLOG.md`](docs/WORKLOG.md)(歷史檔;**不是現況說明**) |
| **發版前要跑回歸** | [`engine/REGRESSION.md`](engine/REGRESSION.md)(R0–R10 可執行案例) |
| **產檔被閘門擋下、看到 ERROR** | [`engine/tools/README_TOOLS.md`](engine/tools/README_TOOLS.md)(錯誤→修法對照表,每種錯只有一種修法) |
| **要寫 / 看懂 slide_spec.json** | [`engine/rules/page_types_registry.md`](engine/rules/page_types_registry.md)(11 種註冊頁型的槽位契約) |
| **想知道現在有哪些模板可用** | [`engine/templates/INDEX.md`](engine/templates/INDEX.md),或跑 `python engine/tools/make_skeleton.py --list` |

## 常用工作

**本機產一份簡報**(需 Python 3;渲染需 python-pptx,沒裝可用 `uv run --with python-pptx`):

```
python .codex/skills/outline-to-ppt/prepare_env.py                      # ① 建 ppt_out/ 沙箱(模擬 GPTs /mnt/data 佈局)
cp engine/examples/01_minimal_4p.json ppt_out/slide_spec.json           # ② 拿一份現成 spec(或用 make_skeleton 產骨架自己填)
python ppt_out/tools/run_pipeline.py --spec ppt_out/slide_spec.json --asset-dir ppt_out --out ppt_out/deck.pptx   # ③ 驗證→渲染→QA
```

(渲染階段需 python-pptx;沒裝就把 ③ 的 `python` 換成
`uv run --with python-pptx python`——prepare_env 會印出該用哪個前綴。)

流程細節見 [`.codex/skills/outline-to-ppt/SKILL.md`](.codex/skills/outline-to-ppt/SKILL.md);
所有命令都是單行 python,**macOS / Linux / Windows PowerShell / cmd 通用**。
spec 內的素材路徑(`assets/backgrounds/...`)一律以 `--asset-dir` 為根解析。

**註冊一個新模板**:在 Codex CLI 說「我有一個新模板要註冊」,由
[`.codex/skills/register-template/SKILL.md`](.codex/skills/register-template/SKILL.md)
引導完成(盤點→頁型映射→綁定→黃金驗收→註冊);工具鏈是
`engine/release/template_admin.py`。

**看引擎有哪些頁型可用**:`python engine/tools/make_skeleton.py --list`

## 引擎目錄速查

| 路徑 | 內容 |
| --- | --- |
| `engine/rules/` | 共用語意契約 SSOT:驗證器(`PAGE_TYPES`)、schema、頁型庫、風格規範 |
| `engine/tools/` | 引擎腳本 ×11 + `README_TOOLS.md`(模型速查卡與錯誤修法表);改完重打 `gpts/dist/tools.zip` |
| `engine/templates/<id>/` | 模板包:模板本體 + manifest + 綁定 + 素材(light 為第一個包) |
| `engine/release/` | 維護者工具:`template_admin.py`(註冊/驗收/打包)、`wireframe_preview.py` |
| `engine/golden/` | 黃金驗收 fixtures(自契約派生,對註冊流程唯讀) |
| `engine/examples/` | 試用範例 JSON ×4 + 大綱 fixture + 實測產出 pptx |
| `gpts/dist/` | 上傳 GPTs 的打包產物(tools.zip、template_*.zip) |

## 歷史

本 repo 原有兩條產 PPT 管線(Codex `baoyu-slide-deck` 圖生圖主力、`fallback/`
spec 閘門備援),2026-07-20 轉向 GPTs 建置包並移除舊管線目錄
(`.agents/`、`fallback/`、`my_project/`);2026-07-25 重構為「單引擎 + 兩前端」
並完成多模板架構(舊佈局對照見 `docs/WORKLOG.md` §21)。
