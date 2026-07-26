# MAINTENANCE — 維護與發佈手冊

> **用途**:改規則、改工具、加模板、發新版時照這份做。
> **讀者**:維護者(改 repo 的人)。
> **何時讀**:動 `engine/` 任何東西之前;要把改動推到 GPTs 之前。
> 硬規則以 [`AGENTS.md`](../AGENTS.md) 為準,本檔是它的操作版。

## 1. 改頁型契約 → 契約同步

`engine/rules/` 是共用語意契約的單一真相來源。改頁型契約時:

1. **改 `engine/rules/validate_slide_spec_gpts.py` 的 `PAGE_TYPES`**
   ——唯一手寫真相,只有這一處要動腦。
2. **跑 `python engine/release/template_admin.py sync-docs --write`**
   ——重生 `slide_spec.schema.json` 的 `page_type` enum。
   **這一步不靠人記得**:`pack` 會先跑同一個檢查,漂移就打不出 zip
   (掛載理由見 `engine/release/sync_docs.py` 檔頭)。
3. **手改 `engine/rules/page_types_registry.md`**(1 的人類可讀版)
   ——目前唯一還要手動同步的一處。它約三分之一是人寫語意(適用情境、版面
   限制、閱讀順序),機械生成會弄丟而且**機器測不出來**,所以刻意不生成;
   要收斂得先設計 prose side-car,理由與已知陷阱見 `sync_docs.py` 檔頭。

**文件裡一律不要寫「共 N 種頁型」。** 寫死的數字會過期,而過期的數字是
功能性缺陷——2026-07-26 `engine/rules/outline_to_ppt_skill.md` 寫「十一種」
讓 GPT 拒用另外 10 種可用頁型(同型缺陷見 commit `3f22aff`)。要數量就指向
`make_skeleton.py --list`。**不要**寫 regex 去掃這些數字:實測命中率
1 真 : 2 假警報 : 1 漏報,一半是雜訊的紅燈只會訓練出無視紅燈的習慣。

新頁型若要全自動產出,另需在該包 `engine/templates/<id>/bindings.json` 加
fill 條目(宣告式 op 詞彙表)→
**`template_admin.py fit --id <id>` 量容量** → 過 `template_admin.py golden`
→ 重打包該模板 zip。架構見 [`ARCHITECTURE.md`](ARCHITECTURE.md)。

**字數與清單長度不准手填。** `PAGE_TYPES` 裡的值只是跨模板的預設,
各包真正裝得下多少由 `fit` 量測後寫進該包 `capacity_overrides`。
憑感覺填的下場是「閘門 PASS、版面壞掉」:2026-07-26 發現 light 有 43 個
槽位超額(`core_mission` 宣告 60 字、版位只放得下 11 字),渲染器靜默把字
縮到 12pt,32 頁 golden 有 99 個框被縮而所有自動檢查全綠。
原則(設計師定調):**字級是設計過的,塞不下要改稿或換頁型,不是縮字。**
演算法與 15 個已知量測陷阱見 `engine/release/fit_capacity.py` 檔頭。

**設計師自助加開頁型**走 `.codex/skills/add-page-types/SKILL.md`
(設計師版說明在 `docs/給設計師/03-路線B-自己動手.md` 的 A10 節);
那條路徑允許動契約同步,與「註冊全新模板」的 `register-template` 分工不同。

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

0. □ `python engine/release/template_admin.py sync-docs` exit 0
   (派生檔與機器真相一致;`pack` 也會擋,這裡先跑只是早點知道)
1. □ `python3 engine/release/regress.py` exit 0(引擎級全部 R 案例 + light
   R-L0/R-L1 一鍵跑完;案例規格見 `engine/REGRESSION.md`)+ 動到的模板包
   自身 REGRESSION 綠(R-L2 類人工案例)
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
8. □ `engine/templates/INDEX.md` 表格已由 `sync-docs --write` 重生
   (新包要先手動加一列);通知團隊

## 6. 版控紀律

- **真相來源永遠是 repo**:先改 repo、commit,再由管理者同步到 GPT Builder。
  不要直接在 Builder 裡改完就算——下次同步會被 repo 版蓋掉。
- **模板隔離**:白名單四項以 [`AGENTS.md`](../AGENTS.md) 硬規則 10 為準
  (本檔不複述,避免漂移);越界改動拆 commit,
  以 `python engine/release/template_admin.py isolation` 機器驗證。
- **本機產物**(`ppt_out/`)一律進 gitignore,嚴禁 commit。
