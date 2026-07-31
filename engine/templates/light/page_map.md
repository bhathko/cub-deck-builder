# light 包頁型映射(page_map)

> 本檔為 light 模板包的「語意頁型 → 模板頁 + 支援等級」人類可讀版;
> 機器真相在同目錄 `manifest.json` 的 `page_types`。頁型的**語意與容量**
> 見共用文件 `engine/rules/page_types.md` 與 `page_types_registry.md`;
> 那邊已不含模板頁碼(Phase 1 拆分完成),**頁碼對照以本檔為唯一來源**。

支援等級只有兩級:fill = 全自動(spec 直接產出);clone = 半自動
(走 render_plan 複製改字)。**每個頁型都對應模板 pptx 裡的一頁實頁**;
本包無 unsupported 頁型。

| 語意頁型 | 支援等級 | 模板頁 | 備註 |
| --- | --- | --- | --- |
| cover | fill(全自動,clone+填充) | 7 | 背景/logo 在 layout「封面(有小標)」內,不吃 spec 的 assets;長主標由 `shrink_to_fit` 縮字級 |
| agenda | fill(全自動,clone+填充) | 9 | layout「目錄」自帶左側色塊與標題,整份 items 用 `item_template` 併進單一內容框(id=2);編號是行內文字(單一文字框畫不出圓形) |
| vision_goal_center_balance | fill(全自動,clone+填充) | 14 | shape id 見 bindings.json 與 inventory.json |
| info_three_column_category | fill(全自動,clone+填充) | 17 | shape id 見 bindings.json 與 inventory.json |
| data_two_group_metric_comparison | fill(全自動,clone+填充) | 29 | shape id 見 bindings.json 與 inventory.json |
| evaluation_option_score_pros_cons | fill(全自動,clone+填充) | 33 | shape id 見 bindings.json 與 inventory.json |
| pyramid_layered_maturity_detail | fill(全自動,clone+填充) | 54 | shape id 見 bindings.json 與 inventory.json |
| story_photo_icon_takeaways | clone(半自動,需 render_plan) | 11 | 寫 plan 前先 `inspect_template.py --page 11` |
| vision_goal_rings | clone(半自動,需 render_plan) | 12 | 寫 plan 前先 `inspect_template.py --page 12` |
| vision_goal_hub_spoke | clone(半自動,需 render_plan) | 13 | 寫 plan 前先 `inspect_template.py --page 13` |
| vision_goal_pyramid | clone(半自動,需 render_plan) | 15 | 寫 plan 前先 `inspect_template.py --page 15` |
| vision_goal_keyword_orbit | fill(全自動) | 16 | 綁定見 bindings.json;契約見 page_types_registry.md |
| info_sidebar_grid | fill(全自動) | 18 | 綁定見 bindings.json;契約見 page_types_registry.md |
| info_icon_bubble_cluster | clone(半自動,需 render_plan) | 19 | 寫 plan 前先 `inspect_template.py --page 19` |
| info_card_grid | fill(全自動) | 20 | 綁定見 bindings.json;契約見 page_types_registry.md |
| info_center_hub_support | clone(半自動,需 render_plan) | 21 | 寫 plan 前先 `inspect_template.py --page 21` |
| info_horizontal_explanation_rows | fill(全自動) | 22 | 綁定見 bindings.json;契約見 page_types_registry.md |
| info_dual_column_detail_matrix | clone(半自動,需 render_plan) | 23 | 寫 plan 前先 `inspect_template.py --page 23` |
| info_before_after_item_compare | fill(全自動) | 24 | 綁定見 bindings.json;契約見 page_types_registry.md |
| data_line_trend_comparison | fill(全自動,clone+填充+圖表數據) | 25 | shape id 見 bindings.json 與 inventory.json |
| data_table_kpi_chart_insights | clone(半自動,需 render_plan) | 26 | 寫 plan 前先 `inspect_template.py --page 26` |
| data_kpi_bar_callout_dashboard | clone(半自動,需 render_plan) | 27 | 寫 plan 前先 `inspect_template.py --page 27` |
| data_dual_percentage_balance | clone(半自動,需 render_plan) | 28 | 寫 plan 前先 `inspect_template.py --page 28` |
| data_three_number_kpis | fill(全自動) | 30 | 綁定見 bindings.json;契約見 page_types_registry.md |
| data_three_radar_score_comparison | clone(半自動,需 render_plan) | 31 | 寫 plan 前先 `inspect_template.py --page 31` |
| evaluation_vs_criteria_matrix | fill(全自動) | 32 | 綁定見 bindings.json;契約見 page_types_registry.md;皇冠/獎盃於填充時移除 |
| cycle_three_node_process | clone(半自動,需 render_plan) | 34 | 寫 plan 前先 `inspect_template.py --page 34` |
| cycle_four_point_loop | fill(全自動) | 35 | 綁定見 bindings.json;契約見 page_types_registry.md |
| cycle_dual_core_feedback | clone(半自動,需 render_plan) | 36 | 寫 plan 前先 `inspect_template.py --page 36` |
| cycle_multi_step_loop | clone(半自動,需 render_plan) | 37 | 寫 plan 前先 `inspect_template.py --page 37` |
| stage_timeline_progress | fill(全自動) | 38 | 綁定見 bindings.json;契約見 page_types_registry.md |
| stage_phase_swimlane | clone(半自動,需 render_plan) | 39 | 寫 plan 前先 `inspect_template.py --page 39` |
| stage_year_cards | fill(全自動) | 40 | 綁定見 bindings.json;契約見 page_types_registry.md |
| stage_period_cards | clone(半自動,需 render_plan) | 41 | 寫 plan 前先 `inspect_template.py --page 41` |
| stage_horizon_matrix | clone(半自動,需 render_plan) | 42 | 寫 plan 前先 `inspect_template.py --page 42` |
| stage_year_transition_architecture | clone(半自動,需 render_plan) | 43 | 寫 plan 前先 `inspect_template.py --page 43` |
| stage_multi_year_gantt_summary | clone(半自動,需 render_plan) | 44 | 寫 plan 前先 `inspect_template.py --page 44` |
| stage_vertical_timeline_detail | clone(半自動,需 render_plan) | 45 | 寫 plan 前先 `inspect_template.py --page 45` |
| stage_monthly_gantt | clone(半自動,需 render_plan) | 46 | 寫 plan 前先 `inspect_template.py --page 46` |
| phase_concept_three_column_explanation | fill(全自動) | 47 | 綁定見 bindings.json;契約見 page_types_registry.md |
| phase_before_now_future_transition | clone(半自動,需 render_plan) | 48 | 寫 plan 前先 `inspect_template.py --page 48` |
| phase_four_step_workflow_matrix | clone(半自動,需 render_plan) | 49 | 寫 plan 前先 `inspect_template.py --page 49` |
| phase_three_column_action_cards | fill(全自動) | 50 | 綁定見 bindings.json;契約見 page_types_registry.md |
| phase_input_process_output_flow | clone(半自動,需 render_plan) | 51 | 寫 plan 前先 `inspect_template.py --page 51` |
| phase_step_ladder_cards | clone(半自動,需 render_plan) | 52 | 寫 plan 前先 `inspect_template.py --page 52` |
| pyramid_three_level_center_explanation | clone(半自動,需 render_plan) | 53 | 寫 plan 前先 `inspect_template.py --page 53` |
| structure_system_overview_table | clone(半自動,需 render_plan) | 55 | 寫 plan 前先 `inspect_template.py --page 55` |
| structure_hierarchy_matrix | clone(半自動,需 render_plan) | 56 | 寫 plan 前先 `inspect_template.py --page 56` |
| structure_org_chart_roles | clone(半自動,需 render_plan) | 57 | 寫 plan 前先 `inspect_template.py --page 57` |
| structure_relation_map | clone(半自動,需 render_plan) | 58 | 寫 plan 前先 `inspect_template.py --page 58` |
| closing | fill(全自動,clone+填充) | 59 | 滿版背景與遮罩是 p59 頁面自帶 shape,不吃 spec 的 assets |
| section_transition | fill(全自動,clone+填充) | 60 | 章節過渡頁；layout 自帶背景與置中樣式，不顯示頁碼、不吃 spec 的 assets |

共 52 筆:fill 22、clone 30。

## 附:幾個吃過虧的版位限制(容量真相仍在 manifest `capacity_overrides`)

- **cover 副標只給 5 字**:p7 副標框是 `spAutoFit` 且僅 3.24 吋寬,
  長文會往下長、壓到日期列。主標則相反——由 `shrink_to_fit` 縮字級,不推擠鄰位。
- **agenda 是單一文字框**:p9 頁面上只有一個內容框(id=2,7.84x4.89 吋),
  整份 items 由 `item_template` 套版成「編號␣␣標題 ⏎ 副標」後併進去,
  所以編號畫不出圓形,只能是行內文字。

## 附:light 語意色名對照(page_types.md 視覺描述用;機器真相在 manifest style)

| 語意色名 | light 色碼 |
| --- | --- |
| 主色(綠) | #58D494 |
| 輔色(紫) | #848BF2 |
| 輔色(藍) | #4AB7F9 |
| 深色(主文字色) | #344252 |
| 次文字色 | #68727E |
| 分隔線色 | #D8DEE4 |
