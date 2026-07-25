# CLAUDE.md

> **單一真相來源是 [`AGENTS.md`](AGENTS.md)**。Claude Code 使用者請把 `AGENTS.md`
> 當完整指令並遵循;本檔只做指路 + 速覽。規則衝突時以 `AGENTS.md` 為準,
> 更新流程規則時**只改 `AGENTS.md`**。整體說明見 [`README.md`](README.md)。

## 速覽

- **本 repo = 簡報產生器:單引擎 + 兩個延伸應用**——主程序在 `engine/`
  (工具、規則、模板包),`gpts/`(ChatGPT GPTs 發佈包)與
  `.codex/skills/`(本機 CLI)是它的兩個前端。接手前先讀
  `docs/WORKLOG.md`(決策脈絡)與 `gpts/README.md`(GPTs 建置手冊)。
- **規則 SSOT = `engine/rules/`**;改頁型契約要三處同步(validator
  `PAGE_TYPES` / schema enum / registry)。
- **渲染層零隨機**;各包綁定(`engine/templates/<id>/bindings.json`)與該包
  模板 shape id 硬耦合,模板改版必重盤點(多模板架構見 `docs/TEMPLATE_PACKS.md`)。
- 改 `engine/tools/*` → 重打 tools.zip;改 `engine/templates/<id>/*` → 重打
  template_<id>.zip;都要更新 instructions 版本字串。

## 常用指令
```
python engine/rules/validate_slide_spec_gpts.py --spec <spec.json> --asset-dir <素材根>   # spec 閘門
python engine/tools/render_deck.py --spec <spec> --asset-dir <素材根> --out <out.pptx>         # 模板自動取自選定包(deck.template,預設 light)
python engine/tools/qa_check.py --spec <spec> --pptx <out.pptx>                                # 產檔後自檢
```
