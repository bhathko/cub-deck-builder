# CLAUDE.md

> **單一真相來源是 [`AGENTS.md`](AGENTS.md)**。Claude Code 使用者請把 `AGENTS.md`
> 當完整指令並遵循;本檔只做指路 + 速覽。規則衝突時以 `AGENTS.md` 為準,
> 更新流程規則時**只改 `AGENTS.md`**。整體說明見 [`README.md`](README.md)。

## 速覽

- **本 repo = GPTs 簡報產生器建置包**,一切在 `gpts/`;接手前先讀
  `gpts/WORKLOG.md`(決策脈絡)與 `gpts/README.md`(建置手冊)。
- **規則 SSOT = `gpts/knowledge/`**;改頁型契約要三處同步(validator
  `PAGE_TYPES` / schema enum / registry)。
- **渲染層零隨機**;light 綁定(`gpts/templates/light/bindings.py`)與模板
  shape id 硬耦合,模板改版必重盤點(多模板架構見 `gpts/TEMPLATE_PACKS.md`)。
- 改 `gpts/tools/*` 或 `gpts/assets_src/*` → 重打包對應 zip + 更新
  instructions 版本字串。

## 常用指令
```
python gpts/knowledge/validate_slide_spec_gpts.py --spec <spec.json> --asset-dir <素材根>   # spec 閘門
python gpts/tools/render_deck.py --spec <spec> --template gpts/knowledge/light_template.pptx --asset-dir <素材根> --out <out.pptx>
python gpts/tools/qa_check.py --spec <spec> --pptx <out.pptx>                                # 產檔後自檢
```
