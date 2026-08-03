#!/usr/bin/env python3
"""容量探針:直接讀沙箱 validator + 模板包 manifest 的合併容量(產檔前健檢用)。

零規則重複——上限來自 validate_slide_spec_gpts.py 的 PAGE_TYPES 經
apply_capacity_overrides() 合併後的結果,與 spec 閘門永遠同步;計字語意
同閘門(len(str),含空白與標點)。先跑 prepare_env.py 準備 ppt_out 沙箱。

用法(單行、相對路徑、三種 shell 通用;沙箱省略即自動偵測):
  本機:  python ppt_out/tools/capacity_probe.py --list-caps cover
  GPTs:  python /mnt/data/tools/capacity_probe.py --list-caps cover
  python ppt_out/tools/capacity_probe.py --check cover main_title "候選主標題"
  python ppt_out/tools/capacity_probe.py --check agenda items 7
  python ppt_out/tools/capacity_probe.py --check data_three_number_kpis "kpis[].value" "12%"

槽位路徑用 page_types_registry.md 的寫法:清單項下探加 []、object 欄位用點
(例:items[].subtitle、before.points[]、kpis[].label)。--check 可接多個值,
逐一檢查;文字槽位驗字數,清單槽位給整數驗項數。
exit 0=全過、1=有超限、2=環境或用法錯誤。
"""
import argparse
import importlib.util
import sys
from pathlib import Path


def die(msg: str):
    print(msg, file=sys.stderr)
    sys.exit(2)


def load_validator(sandbox: Path):
    vpath = sandbox / "validate_slide_spec_gpts.py"
    if not vpath.exists():
        die(f"[E] 找不到 {vpath}——先跑 python .codex/skills/outline-to-ppt/prepare_env.py")
    spec = importlib.util.spec_from_file_location("gpts_validator", vpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_merged(sandbox: Path, template_id: str):
    mod = load_validator(sandbox)
    try:
        ctx = mod.load_pack_context(sandbox / "templates", template_id)
    except ValueError as e:
        die(f"[E] 模板包設定錯誤:{e}")
    if ctx is None:
        die(f"[E] 模板包 {template_id} 不存在於 {sandbox / 'templates'}")
    return ctx


def walk(slots: dict, prefix=""):
    """攤平槽位樹成 (registry 風格路徑, slot) 對;順序照契約宣告。"""
    for name, slot in slots.items():
        path = f"{prefix}{name}"
        kind = slot["kind"]
        if kind == "text":
            yield path, slot
        elif kind == "list":
            yield path, slot
            item = slot["item"]
            if item["kind"] == "object":
                yield from walk(item["fields"], prefix=f"{path}[].")
            else:
                yield f"{path}[]", item
        elif kind == "object":
            yield from walk(slot["fields"], prefix=f"{path}.")


def describe(slot) -> str:
    req = "必填" if slot.get("required", True) else "選填"
    if slot["kind"] == "text":
        return f"文字 ≤{slot['max_chars']} 字({req})"
    if slot["kind"] == "list":
        return f"清單 {slot['min']}–{slot['max']} 項({req})"
    return f"object({req})"


def resolve(slots: dict, path: str):
    """把 registry 風格路徑解析成 slot;找不到回 None。"""
    for p, slot in walk(slots):
        if p == path:
            return slot
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sandbox", help="沙箱根(省略=自動偵測:本檔所在 tools/ 的上一層,"
                                      "否則 ./ppt_out)")
    ap.add_argument("--template-pack", default="light")
    ap.add_argument("--list-caps", metavar="頁型")
    ap.add_argument("--check", nargs="+",
                    metavar=("頁型 槽位", "值"),
                    help="頁型 槽位 值 [值…];文字槽驗字數,清單槽給整數驗項數")
    args = ap.parse_args()
    if not args.list_caps and not args.check:
        ap.error("要 --list-caps 或 --check 其一")
    if args.check and len(args.check) < 3:
        ap.error("--check 需要:頁型 槽位 值 [值…]")

    # 本檔被複製進 <沙箱>/tools/ 後,上一層就是沙箱根(ppt_out/ 或 /mnt/data);
    # 在 repo 內直接執行時退回 ./ppt_out。
    sandbox = Path(args.sandbox) if args.sandbox else next(
        (c for c in (Path(__file__).resolve().parent.parent, Path("ppt_out"))
         if (c / "validate_slide_spec_gpts.py").exists()), Path("ppt_out"))
    ctx = load_merged(sandbox, args.template_pack)
    merged = ctx["page_types"]
    pt = args.list_caps or args.check[0]
    if pt not in merged:
        mode = ctx["modes"].get(pt)
        if mode:
            die(f"[E] 頁型 {pt} 在本包為 {mode}(非全自動),容量契約不在 validator,見 page_types.md")
        die(f"[E] 未註冊頁型 {pt!r}(全集跑 python {sandbox}/tools/make_skeleton.py --list)")
    mode = ctx["modes"].get(pt, "未收錄")
    print(f"模板包 {ctx['id']}@{ctx['version']} 頁型 {pt}(mode: {mode})")
    if mode != "fill":
        print(f"[W] 本包此頁型非全自動(fill),容量僅供參考;支援集合以 --list 為準")

    if args.list_caps:
        rows = [(p, describe(s)) for p, s in walk(merged[pt]["slots"])]
        width = max(len(p) for p, _ in rows)
        for p, d in rows:
            print(f"  {p:<{width}}  {d}")
        return

    slot_path, values = args.check[1], args.check[2:]
    slot = resolve(merged[pt]["slots"], slot_path)
    if slot is None:
        avail = ", ".join(p for p, _ in walk(merged[pt]["slots"]))
        die(f"[E] 頁型 {pt} 無槽位 {slot_path!r};可用:{avail}")
    failed = False
    for v in values:
        if slot["kind"] == "list":
            if not v.isdigit():
                die(f"[E] {slot_path} 是清單槽位,--check 請給整數項數(收到 {v!r})")
            n, lo, hi = int(v), slot["min"], slot["max"]
            if lo <= n <= hi:
                print(f"  PASS  {slot_path} = {n} 項(允許 {lo}–{hi})")
            else:
                failed = True
                print(f"  FAIL  {slot_path} = {n} 項,超出允許範圍 {lo}–{hi}")
        elif slot["kind"] == "text":
            n, mx = len(v), slot["max_chars"]
            if n <= mx:
                print(f"  PASS  {slot_path}「{v}」{n} 字 ≤ 上限 {mx}")
            else:
                failed = True
                print(f"  FAIL  {slot_path}「{v}」{n} 字,超過上限 {mx}(多 {n - mx} 字,要縮或換頁型)")
        else:
            die(f"[E] {slot_path} 是 object 容器,請檢查其下欄位(--list-caps {pt} 查路徑)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
