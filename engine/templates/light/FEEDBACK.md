# light 包回饋台帳

> 本包(模板/綁定/版面)專屬回饋;引擎級與跨模板回饋記 `docs/FEEDBACK.md`。
> 格式沿 `docs/FEEDBACK.md`:症狀 → 規則化 → 發版追蹤。fills 升級決策(同頁型 2 次
> clone+plan 使用即升級,docs/WORKLOG.md §8)以本檔計數。

| # | 日期 | 症狀/需求 | 處置 | 版本 |
| --- | --- | --- | --- | --- |
| 1 | 2026-08-01 | Hunter 目檢 golden p14(data_two_group_metric_comparison max 變體):KPI 大數字「%」折行疊到下一顆。值框 1.39 吋 @44pt 置中、wrap=square+spAutoFit,「19.9%」實寬 1.53 吋 → PowerPoint 開檔重排時折行、框長高壓到下顆。qa/fit 當時全綠(估算器未扣內文邊距,引擎級死角記 `docs/FEEDBACK.md`) | 綁定加 3 個 resize:值框 15/18/52 加寬 1.39→2.0 吋(置中軸不動),fit --reset 重量後 golden 全綠 | light@2026-08-01.2 |
