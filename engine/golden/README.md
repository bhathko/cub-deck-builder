# engine/golden — 契約快照(不是實跑素材)

> **這些檔案不會被任何程式讀取。** 實際跑黃金驗收時,
> `template_admin.py golden --id <包>` 是依該包的 merged 契約**當場派生**的,
> 不讀這個目錄。

**那它們存在的意義?** 契約(`engine/rules/validate_slide_spec_gpts.py` 的
`PAGE_TYPES`)改動時,重跑 `--regen-specs` 後的 **git diff 會直接顯示
「哪些頁型的形狀變了」**——欄位增減、數量上下限、字數上限,一眼可見。
純讀程式碼的 diff 看不出這些。

- **檔數 = 註冊頁型數 × 2**(min/max 兩變體),線性,**與模板數無關**。
- **不含 `deck.template`**:這是跨模板的基準快照,綁模板就不通用了。
- **對註冊流程唯讀**:不得為了讓某個模板過驗收而修改這裡的檔案。
- 契約改動後必須重跑 `python engine/release/template_admin.py golden --regen-specs`
  並把結果一起 commit——`engine/REGRESSION.md` 的 **R11** 會檢查這件事。

`min` 變體測**刪格路徑**(多餘格位/分隔線要刪乾淨),
`max` 變體測**溢出與縮字路徑**(塞滿 max_chars)。
