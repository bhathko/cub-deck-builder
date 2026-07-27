# 模板包索引

> 多模板架構見 `docs/ARCHITECTURE.md`;模板改版流程見同目錄
> `TEMPLATE_LIFECYCLE.md`。新增模板 = 新增一個子目錄(Phase 2 起由
> `.codex/skills/register-template/` 引導註冊),不改引擎、不碰其他包。

| template_id | 名稱 | manifest version | status | 支援(全自動/半自動/不支援) | Knowledge zip | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| light | Cathay 淺色企業風 | 2026-07-27.4 | registered | 19 / 32 / 0 | template_light.zip | 第一個包;純宣告式 bindings.json,無任何專屬例外 |

維護提醒:

- **上表前 6 欄由 manifest 生成,不要手改**——跑
  `python engine/release/template_admin.py sync-docs --write` 重生;`pack` 會先
  檢查,漂了就打不出 zip。最後的「備註」欄是人寫的,生成器不碰。
  (2026-07-26 這一列漂過:寫 `2026-07-26.1 / 11 / 42 / 0`,實際是 `.2 / 21 / 32 / 0`
  ——那次沒有任何機器會發現,所以才把它接上生成器。)
- **新增模板包**要先在上表手動加一列(生成器只重寫已存在的列,不會憑空插列;
  缺列會直接報錯提醒)。
- 包內容異動 → 更新該包 manifest `version`(表格跟著重生);發佈另走
  `docs/MAINTENANCE.md` 的發佈 checklist(Phase 1 前 GPTs 端佈局不變)。
- `status=draft` 的包不得被任何產檔流程選中。
