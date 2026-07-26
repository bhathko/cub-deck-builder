# MAINTENANCE — 維護與發佈手冊

> **用途**:改規則、改工具、加模板、發新版時照這份做。
> **讀者**:維護者(改 repo 的人)。
> **何時讀**:動 `engine/` 任何東西之前;要把改動推到 GPTs 之前。
> 硬規則以 [`AGENTS.md`](../AGENTS.md) 為準,本檔是它的操作版。

## 1. 改頁型契約 → 三處同步

`engine/rules/` 是共用語意契約的單一真相來源,改頁型契約時**三處一起改**:

1. `engine/rules/validate_slide_spec_gpts.py` 的 `PAGE_TYPES`(真相來源)
2. `engine/rules/slide_spec.schema.json` 的 `page_type` enum
3. `engine/rules/page_types_registry.md`(1 的人類可讀版)

新頁型若要全自動產出,另需在該包 `engine/templates/<id>/bindings.json` 加
fill 條目(宣告式 op 詞彙表;builtin 僅 light 的 `bindings.py`)→ 過
`template_admin.py golden` → 重打包該模板 zip。架構見
[`ARCHITECTURE.md`](ARCHITECTURE.md)。

**契約改版的連動**:golden fixtures 重派生
(`template_admin.py golden --regen-specs`)→ **全部已註冊模板包重跑 golden**;
有包由綠轉紅(該模板裝不下新容量)→ 該頁型降級並記該包 FEEDBACK,
不得為單一模板改共用契約。

## 2. 改工具 / 改模板 → 重打包

| 改了什麼 | 重打包 | 指令 |
| --- | --- | --- |
| `engine/tools/*` | `gpts/dist/tools.zip` | `python engine/release/template_admin.py pack --tools` |
| `engine/templates/<id>/*`(含 `assets_src/`) | `gpts/dist/template_<id>.zip` | `python engine/release/template_admin.py pack --id <id>` |

打包後同步更新 `gpts/instructions.md` 的版本字串與模板 roster 行,
以及 [`engine/REGRESSION.md`](../engine/REGRESSION.md) R7 的 sha 基準。

**打包鐵律:zip 一律正斜線(POSIX)路徑**——不要用 PowerShell
`Compress-Archive` 或檔案總管「壓縮資料夾」(會塞 Windows 反斜線,
Linux `unzip` 會警告並回非零 exit,誘發 GPTs 誤判環境壞掉)。
`template_admin.py pack` 已內建正斜線與反斜線檢查;驗證指令:

```
python -c "import zipfile; [print(i.orig_filename) for i in zipfile.ZipFile('gpts/dist/template_light.zip').infolist()]"
```

每筆都必須是正斜線。

## 3. 模板改版(同 id 換 pptx)

照 [`engine/templates/TEMPLATE_LIFECYCLE.md`](../engine/templates/TEMPLATE_LIFECYCLE.md):
換檔 → `freeze` → `inspect_template.py --verify` 漂移偵測 → 核對 bindings →
`lint` → `golden` 全綠 → 該模板 REGRESSION 綠 → manifest version bump → `pack`。
sha 不符 = 盤點未完成,不得發版。

## 4. 新增模板

由 `.codex/skills/register-template/` 引導完成(設計師提供 pptx,
skill 帶著跑盤點→映射→綁定→黃金驗收→註冊)。
`template_admin.py register` exit 0 = 註冊成功,接著走下方發佈 checklist。

## 5. 發佈 checklist(推到 GPT Builder)

> 註冊/改動在 repo 端完成後,發佈是**人工步驟**,逐項勾;
> Builder 端的逐步操作與驗收指令原文見 [`../gpts/DEPLOY.md`](../gpts/DEPLOY.md)。

0. □ 頁型數量若有變動,掃一次文件內的「N 種註冊頁型」數字
   (`grep -rn "種註冊頁型\|種全自動" --include="*.md" .`)
1. □ 該模板包 REGRESSION 綠 + `engine/REGRESSION.md` R0–R10 全符
2. □ `python engine/release/template_admin.py isolation` 白名單過
   (模板目錄外的改動已拆 commit)
3. □ `python engine/release/template_admin.py pack --id <id>` 重打包
   (tools 沒改就不動 tools.zip);R7 hash 基準同步
4. □ `gpts/instructions.md` 版本字串 bump + 模板 roster 行更新
5. □ Knowledge 檔數 ≤19 確認
6. □ Builder:貼新 instructions;上傳異動的知識檔(共用檔沒改就不重傳,
   同名檔要**刪舊傳新**)
7. □ Builder 驗收:問「你現在是哪一版?」核對 instructions 版與 roster;
   用該模板 golden/smoke spec 產一份 qa PASS;light 抽測一份確認不受影響
8. □ `engine/templates/INDEX.md` 狀態更新;通知團隊

## 6. 版控紀律

- **真相來源永遠是 repo**:先改 repo、commit,再由管理者同步到 GPT Builder。
  不要直接在 Builder 裡改完就算——下次同步會被 repo 版蓋掉。
- **模板隔離**:白名單四項以 [`AGENTS.md`](../AGENTS.md) 硬規則 10 為準
  (本檔不複述,避免漂移);越界改動拆 commit,
  以 `python engine/release/template_admin.py isolation` 機器驗證。
- **本機產物**(`ppt_out/`)一律進 gitignore,嚴禁 commit。
