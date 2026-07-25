# TEMPLATE_LIFECYCLE — 模板改版(同 id 換 pptx)標準流程

> WORKLOG §9「light_template.pptx 改版時」流程的泛化版;light 是第一個實例。
> 適用:同一個 template_id 換入新版 .pptx。新增模板另走 register-template
> skill(Phase 2);改語意契約(槽位/容量)走三處同步,不在本檔範圍。

1. **換檔**:以新 pptx 取代該包的模板檔(light 特例:模板檔在
   `gpts/knowledge/light_template.pptx`,見 manifest `template_file` 解析規則)。
2. **重盤點**:重建 inventory 快照與 manifest `template_sha256`
   (Phase 2 起用 `template_admin.py freeze`;之前用
   `inspect_template.py --page N` 逐綁定頁盤點 + 手動更新 manifest sha)。
3. **核對綁定**:比對新舊 inventory,逐項核對 bindings 引用的 shape id
   (id 消失/新增/幾何漂移都要處理);同步更新 `page_map.md` 的頁碼。
4. **驗收**:
   - Phase 2 起:`template_admin.py lint` + `golden --id <id>` 全綠
     (id 沒變但幾何漂移造成的視覺壞版,只有 golden+目檢抓得到);
   - 之前(light 現行):本機跑根 REGRESSION R2/R3/R8 + 包內 R-L0~R-L2,
     產出開檔目檢五個 fill 頁型。
5. **版本**:manifest `version` bump(`YYYY-MM-DD.N`)+ `INDEX.md` 更新。
6. **打包發佈**:照 `gpts/README.md` 維護節重打對應 zip、更新 instructions
   版本字串、Builder 刪舊傳新。sha 不符 = 盤點未完成,不得發版。

**契約改版連動**(PAGE_TYPES 改動時):golden fixtures 重派生 →
**全部已註冊包 golden 重跑**;有包由綠轉紅(裝不下新容量)→ 該頁型降級
並記該包 FEEDBACK,不得為單一模板改共用契約。
