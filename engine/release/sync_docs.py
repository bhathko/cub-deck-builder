#!/usr/bin/env python3
"""sync_docs — 把「派生自機器真相的文件片段」重新生成,並在打包時擋漂移。

為什麼存在
----------
`PAGE_TYPES`(validator)與各包 `manifest.json` 是機器真相,但同一份事實被抄在
文件裡好幾份。抄本會漂,而且漂了沒人知道——2026-07-26 的證據鏈:

  9a9516d 00:22  把「掃 N 種註冊頁型」寫進 MAINTENANCE 發佈 checklist 第 0 項
  a5fe30f 12:48  頁型 11 → 21,照樣漂(checklist 存在後 12 小時 26 分)
  4223ef4 20:32  「完整性稽核——12 個漏掉的引用」
  3f22aff 20:34  又補 3 處(稽核 commit 的 2 分鐘後)

結論:**「寫進文件的同步規則」在本 repo 已被證偽兩次**。所以本工具的重點不是
「多一條可以跑的指令」,而是**掛在 `pack` 上**——漂移就產不出 zip,沒有交付物。
掛載點見 template_admin.py 的 cmd_pack。

刻意不做的事(每一條都有理由,不要「順便補上」)
------------------------------------------------
1. **不生成 page_types_registry.md 的契約節**。該檔約 36% 是人寫語意,而且
   人寫段落在一節內有「前置/中段/尾」三種位置(例:info_card_grid 的
   「版面共 8 格卡片」必須在讀槽位**之前**看到)。機械生成產不出這種順序,
   而且退化「機器測不出來」。要做得先設計 prose side-car,另案處理。
2. **不做「掃描文件裡的 N 種」這種 regex 檢查**。實測命中率 1 真 : 2 假警報 :
   1 漏報(中文數字「十一種」掃不到;WORKLOG 的歷史數字會誤報)。一半是雜訊的
   紅燈會訓練出無視紅燈的習慣,比沒有檢查更糟。正解是**讓數字消失**——文件不要
   寫「共 N 種」,改成指向 `make_skeleton.py --list`。已於 2026-07-26 全面套用。
3. **不碰 engine/templates/<id>/page_map.md**。它在 PACK_WHITELIST 內,改它會
   強制重打該模板 zip;而它的統計句與同檔表格自洽、實測沒漂。成本高、收益零。
4. **不碰 fit_capacity.py 擁有的「light 實際容量」表**。那段已有生成器,
   而且它用**裸字串**定位(`_TABLE_HEAD = "\\n---\\n\\n## light 模板的實際容量"`),
   錨點的第一個字元就是契約區最後一行的換行符。在該處插 marker 會讓 fit 靜默
   產出**兩張**容量表(實測 326 → 381 行、零警告)。要動得先把 fit 也改成具名
   marker,順序不能反。

用法
----
    python engine/release/template_admin.py sync-docs           # 只檢查(預設)
    python engine/release/template_admin.py sync-docs --write   # 重新生成

exit 0 = 一致;exit 1 = 有漂移(--write 模式下 = 已修正,回報改了哪些檔)。
只用標準庫。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SCHEMA = REPO / "engine" / "rules" / "slide_spec.schema.json"
INDEX = REPO / "engine" / "templates" / "INDEX.md"
PACKS = REPO / "engine" / "templates"

# 上傳到 GPTs Knowledge 的檔(清單見 gpts/DEPLOY.md)。本工具改到這些檔時
# 必須大聲提醒——repo 改完不等於線上生效,Builder 端要「刪舊傳新」。
KNOWLEDGE = {SCHEMA}

_ENUM_DESC = (
    "必須是 validate_slide_spec_gpts.py 之 PAGE_TYPES 註冊表中的鍵。"
    "本 enum 由 `template_admin.py sync-docs --write` 從 PAGE_TYPES 生成,"
    "不要手改——手改會在下次 sync-docs 被蓋掉,而且 pack 會先擋下來。"
)


def _page_types() -> list[str]:
    sys.path.insert(0, str(REPO / "engine" / "rules"))
    from validate_slide_spec_gpts import PAGE_TYPES
    return list(PAGE_TYPES)  # 保留宣告順序,diff 才讀得出「新增了哪一種」


# ---------------------------------------------------------------------------
# 目標 1:slide_spec.schema.json 的 page_type enum
# ---------------------------------------------------------------------------
def _gen_schema(text: str) -> str:
    """回傳應有的 schema 全文。

    用 json round-trip 而非字串替換:實測 `json.loads → json.dumps(
    ensure_ascii=False, indent=2) + "\\n"` 對現行檔案位元完全相同,所以生成
    不會引入格式雜訊,diff 只會是真正的內容差異。
    """
    doc = json.loads(text)
    node = doc["$defs"]["slide"]["properties"]["page_type"]
    node["enum"] = _page_types()
    node["description"] = _ENUM_DESC
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


# ---------------------------------------------------------------------------
# 目標 2:engine/templates/INDEX.md 的模板包表格
# ---------------------------------------------------------------------------
_INDEX_HEADER = "| template_id |"


def _pack_rows() -> dict[str, list[str]]:
    """由各包 manifest 算出前 6 欄(與 cmd_list 同源)。備註欄不碰。"""
    rows = {}
    for p in sorted(PACKS.iterdir()):
        mp = p / "manifest.json"
        if not mp.exists():
            continue
        m = json.loads(mp.read_text(encoding="utf-8-sig"))
        modes = [e.get("mode") for e in m.get("page_types", {}).values()]
        tid = m.get("template_id", p.name)
        rows[tid] = [
            tid,
            m.get("display_name", ""),
            m.get("version", "?"),
            m.get("status", "?"),
            f"{sum(x == 'fill' for x in modes)}"
            f" / {sum(x == 'clone' for x in modes)}"
            f" / {sum(x == 'unsupported' for x in modes)}",
            f"template_{tid}.zip",
        ]
    return rows


def _gen_index(text: str) -> str:
    """重寫表格的機械欄位,保留每列最後的「備註」欄(人寫)。"""
    want = _pack_rows()
    lines = text.split("\n")
    try:
        h = next(i for i, l in enumerate(lines) if l.startswith(_INDEX_HEADER))
    except StopIteration:
        raise SystemExit(f"✗ {INDEX.name} 找不到表頭 {_INDEX_HEADER!r}(格式被改過?)")

    i, seen = h + 2, set()          # h+1 是 |---| 分隔列
    while i < len(lines) and lines[i].startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        tid = cells[0]
        if tid in want:
            note = cells[6] if len(cells) > 6 else ""
            lines[i] = "| " + " | ".join(want[tid] + [note]) + " |"
            seen.add(tid)
        i += 1
    missing = sorted(set(want) - seen)
    if missing:
        raise SystemExit(f"✗ {INDEX.name} 缺這些包的列(請先手動加列再跑):{missing}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
TARGETS = [(SCHEMA, _gen_schema), (INDEX, _gen_index)]


def run(write: bool = False) -> int:
    drift = []
    for path, gen in TARGETS:
        cur = path.read_text(encoding="utf-8")
        new = gen(cur)
        if cur != new:
            drift.append(path)
            if write:
                path.write_text(new, encoding="utf-8")

    rel = [str(p.relative_to(REPO)) for p in drift]
    if not drift:
        print(f"✓ sync-docs:{len(TARGETS)} 個派生檔與機器真相一致")
        return 0

    if write:
        print(f"✓ sync-docs:已重新生成 {len(drift)} 個檔")
        for r in rel:
            print(f"   {r}")
        know = [p for p in drift if p in KNOWLEDGE]
        if know:
            print("⚠ 其中是 GPTs Knowledge 檔,**發版時必須刪舊傳新**:")
            for p in know:
                print(f"   {p.relative_to(REPO)}")
        return 0

    print(f"✗ sync-docs:{len(drift)} 個派生檔與機器真相不符")
    for r in rel:
        print(f"   {r}")
    print("   修法:python engine/release/template_admin.py sync-docs --write")
    return 1
