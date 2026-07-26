#!/usr/bin/env python3
"""trace_page — 把一頁的「spec 槽位 → binding op → 模板 shape」整條縫攤開印出來。

**閱讀輔助工具,不是產檔工具**(住 engine/devtools/,不入 tools.zip、不進沙箱)。
它不存 pptx、不改任何檔案,只印:每個 op 讀了 spec 的哪個路徑、拿到什麼值、
動到模板的哪個 shape id、那個框的文字從什麼變成什麼。

為什麼需要它:`engine/tools/fills_engine.py` 刻意不含任何模板知識——它是解譯器,
語意全在 `engine/templates/<id>/bindings.json` 的資料裡。所以單讀程式碼只看到空殼;
要理解一個 fill 頁型在做什麼,得把「資料 + 模板現況 + 執行結果」三者並排看。

實作原則:繼承正式的 `fill_helpers.Ctx` 並只多記一筆 log,**走跟 render_deck
完全同一條路**(不另寫模擬版,否則會與引擎行為漂移)。

用法:
  uv run --with python-pptx python engine/devtools/trace_page.py \
      --spec engine/examples/01_minimal_4p.json --page 3
  uv run --with python-pptx python engine/devtools/trace_page.py \
      --spec engine/examples/02_full_10p.json --all
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
TOOLS = _HERE.parent / "tools"          # engine/devtools → engine/tools
sys.path.insert(0, str(TOOLS))

from pptx import Presentation  # noqa: E402

import fill_helpers  # noqa: E402
import fills_engine  # noqa: E402
import pack_loader  # noqa: E402
import pptx_toolkit as tk  # noqa: E402
import text_tools as tt  # noqa: E402

MISSING = fills_engine._MISSING


def short(x, n=44):
    s = str(x).replace("\n", "⏎")
    return s if len(s) <= n else s[: n - 1] + "…"


class TraceCtx(fill_helpers.Ctx):
    """跟正式 Ctx 行為一致,只是每次 set/delete 都留一筆紀錄。"""

    def __init__(self, slide):
        super().__init__(slide)
        self.trace = []

    def set(self, sid, text):
        before = tt.shape_text(self.idx[sid]) if sid in self.idx else "<id 不存在>"
        super().set(sid, text)
        self.trace.append(("set", sid, before, text))

    def delete(self, *sids):
        for sid in sids:  # 先記再刪:Ctx.delete 會把 sid 從 idx 移除
            hit = sid in self.idx
            self.trace.append(
                ("del", sid, tt.shape_text(self.idx[sid]) if hit else "", None))
        super().delete(*sids)


def trace_slide(prs, pack, raw_fills, spec_slide):
    num, pt = spec_slide["number"], spec_slide["page_type"]
    print(f"\n{'=' * 78}\np{num}  page_type = {pt}")

    # 三條路由與 render_deck.py 的主迴圈一致(builtin / fill / 需要 plan)
    if pt in pack.builders:
        fn = pack.builders[pt]
        print("  路徑:builtin —— 由程式從空白頁畫出來")
        print(f"  實作:engine/templates/{pack.id}/bindings.py  →  {fn.__name__}()")
        print(f"  讀到的 spec 槽位:{list((spec_slide.get('slots') or {}).keys())}")
        print("  (builtin 沒有宣告式 op 可攤開,要看座標請直接讀那支函式)")
        return

    if pt not in raw_fills:
        print("  路徑:無自動支援 → 需要 render_plan.json 的 clone 條目")
        return

    ent = raw_fills[pt]
    tpl_page = ent["template_page"]
    print(f"  路徑:fill —— clone 模板第 {tpl_page} 頁,再照 ops 換字")
    print(f"  綁定:engine/templates/{pack.id}/bindings.json  →  fills.{pt}.ops")

    ctx = TraceCtx(tk.clone_slide(prs, tpl_page - 1))
    style = pack.manifest.get("style") or {}

    for i, op in enumerate(ent["ops"]):
        kind = op["op"]
        mark = len(ctx.trace)
        slot = op.get("slot")
        val = fills_engine.resolve_path(spec_slide, slot) if slot else None

        head = f"  ops[{i}] {kind:<11}"
        if slot:
            head += f"{slot:<34} → {'<缺值>' if val is MISSING else short(val, 34)}"
        elif kind == "delete":
            head += f"ids={op['ids']}"
        else:
            head += f"id={op.get('id')}"
        print(head)

        try:
            fills_engine._HANDLERS[kind](ctx, spec_slide, op, style, f"{pt} ops[{i}]")
        except fill_helpers.FillError as e:
            print(f"      ✗ FillError: {e}")
            continue

        for what, sid, before, after in ctx.trace[mark:]:
            if what == "set":
                print(f"      id={sid:<3} 「{short(before, 30)}」 → 「{short(after, 30)}」")
            else:
                print(f"      id={sid:<3} 刪除   (模板原本:「{short(before, 26)}」)")
        if len(ctx.trace) == mark:
            print("      (本 op 沒動任何文字框)")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--page", type=int, help="只追一頁(spec 的 number)")
    ap.add_argument("--all", action="store_true", help="追全部頁")
    args = ap.parse_args(argv)

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8-sig"))
    pack = pack_loader.load_pack(spec_deck=spec.get("deck"))
    bj = pack.dir / "bindings.json"
    raw_fills = json.loads(bj.read_text(encoding="utf-8-sig")).get("fills", {}) \
        if bj.exists() else {}

    tpl = pack.resolve_template()
    if not tpl:
        print(f"✗ 找不到模板檔(模板包 {pack.id})")
        return 2

    print(f"spec        : {args.spec}")
    print(f"模板包      : {pack.id}@{pack.version}   ({pack.dir})")
    print(f"模板檔      : {tpl}")
    print(f"builtin 頁型: {sorted(pack.builders)}")
    print(f"fill 頁型   : {len(raw_fills)} 種")

    targets = spec["slides"]
    if args.page:
        targets = [s for s in targets if s["number"] == args.page]
        if not targets:
            print(f"✗ spec 裡沒有 number={args.page} 的頁")
            return 2
    elif not args.all:
        targets = targets[:1]
        print("\n(未指定 --page / --all,只追第一頁)")

    prs = Presentation(str(tpl))
    for s in targets:
        trace_slide(prs, pack, raw_fills, s)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
