# 模板包索引

> 多模板架構見 `docs/TEMPLATE_PACKS.md`;模板改版流程見同目錄
> `TEMPLATE_LIFECYCLE.md`。新增模板 = 新增一個子目錄(Phase 2 起由
> `.codex/skills/register-template/` 引導註冊),不改引擎、不碰其他包。

| template_id | 名稱 | manifest version | status | 支援(全自動/半自動/不支援) | Knowledge zip | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| light | Cathay 淺色企業風 | 2026-07-26.1 | registered | 11 / 42 / 0 | template_light.zip | 第一個包;fills 走宣告式 bindings.json,builtin 繪製器在 bindings.py(grandfather) |

維護提醒:

- 包內容異動 → 更新該包 manifest `version` + 本表;發佈另走
  `docs/MAINTENANCE.md` 的發佈 checklist(Phase 1 前 GPTs 端佈局不變)。
- `status=draft` 的包不得被任何產檔流程選中。
