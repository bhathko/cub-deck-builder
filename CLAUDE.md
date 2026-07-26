# CLAUDE.md

> **單一真相來源是 [`AGENTS.md`](AGENTS.md)**。Claude Code 使用者請把 `AGENTS.md`
> 當完整指令並遵循;本檔只做指路 + 速覽。規則衝突時以 `AGENTS.md` 為準,
> 更新流程規則時**只改 `AGENTS.md`**。整體說明見 [`README.md`](README.md)。

## 速覽

- **本 repo = 簡報產生器:單引擎 + 兩個延伸應用**——主程序在 `engine/`
  (工具、規則、模板包),`gpts/`(ChatGPT GPTs 發佈包)與
  `.codex/skills/`(本機 CLI)是它的兩個前端。接手前先讀
  `docs/WORKLOG.md`(決策脈絡)與 `gpts/README.md`(GPTs 建置手冊)。
- **規則 SSOT = `engine/rules/`**;頁型契約唯一手寫真相是 validator 的
  `PAGE_TYPES`。改完跑 `template_admin.py sync-docs --write` 重生 schema enum
  (`pack` 會擋漂移),`page_types_registry.md` 仍須手改。
  文件**不寫「共 N 種頁型」**——過期的數字會讓模型拒用新頁型。
- **渲染層零隨機**;各包綁定(`engine/templates/<id>/bindings.json`)與該包
  模板 shape id 硬耦合,模板改版必重盤點(多模板架構見 `docs/ARCHITECTURE.md`)。
- 改 `engine/tools/*` → 重打 `tools.zip`;改 `engine/templates/<id>/*` → 重打
  `template_<id>.zip`;都要更新 instructions 版本字串。

## 常用指令

產檔三步,依序跑,前一步 exit 0 才進下一步(完整清單含模板盤點指令見
[`AGENTS.md`](AGENTS.md) 的「常用指令」節):

**1. spec 閘門**——擋結構/槽位/字數/頁碼/素材與捏造數字

```bash
python engine/rules/validate_slide_spec_gpts.py --spec <spec.json> --asset-dir <素材根>
```

**2. 產檔**(模板自動取自選定包:`deck.template`,預設 `light`)

```bash
python engine/tools/render_deck.py --spec <spec> --asset-dir <素材根> --out <out.pptx>
```

**3. 產檔後自檢**——比對產出 pptx 與 spec,擋內容遺漏與文字壓到鄰欄

```bash
python engine/tools/qa_check.py --spec <spec> --pptx <out.pptx>
```
