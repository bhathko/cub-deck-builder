#!/usr/bin/env python3
"""make_skeleton — 依頁型清單產出「保證通過驗證器」的 slide_spec.json 骨架。

使用者要範本時一律用這支產,不要在對話裡手打 JSON(容易寫出違規骨架,
浪費一輪驗證循環)。

用法:
  python make_skeleton.py --types cover,agenda,info_three_column_category,closing \
      --out /mnt/data/slide_spec.json
  python make_skeleton.py --list          # 列出已註冊頁型

規則:
- 已註冊頁型:依 validate_slide_spec_gpts.py 的 PAGE_TYPES 契約生成——必填槽位
  全建、清單取下限數量、占位文字「【欄位名】待填」且必在字數上限內。
- 未註冊頁型(page_types.md 頁型庫):slots 只放一個提示欄位,容量請自行
  比照 page_types.md 填寫。
- assets / render_page_number / slide_count 自動按規則填好。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
# 候選:沙箱(工具旁/父層/mnt)與 repo 佈局(engine/rules)
for p in (_HERE, _HERE.parent, _HERE.parent / "rules", Path("/mnt/data")):
    sys.path.insert(0, str(p))

try:
    from validate_slide_spec_gpts import PAGE_TYPES, apply_capacity_overrides
except ImportError:
    print("✗ 找不到 validate_slide_spec_gpts.py(需與本工具同在 /mnt/data 或其父目錄)")
    sys.exit(2)

try:
    import pack_loader  # 模板包感知(選配;獨立部署時退回內建 light 預設)
except ImportError:
    pack_loader = None

# 內建預設 = light 包值(解不到模板包時的後備;正常路徑讀 manifest asset_defaults:
# cover/closing → background_cover,其餘 → background_content)
BG = {
    "cover": "assets/backgrounds/cover_bg.png",
    "closing": "assets/backgrounds/cover_bg.png",
}
DEFAULT_BG = "assets/backgrounds/content_bg.png"
LOGO = "assets/logos/cathay_logo.png"
FIXED = {  # 固定值槽位,直接填不留占位
    ("closing", "main_title"): "Thank you",
}


def placeholder(name: str, max_chars: int) -> str:
    text = f"【{name}】待填"
    if len(text) > max_chars:
        text = "待填"[:max_chars]
    return text


def build_slot(name, slot, page_type):
    kind = slot["kind"]
    if kind == "text":
        return FIXED.get((page_type, name), placeholder(name, slot["max_chars"]))
    if kind == "list":
        n = max(slot["min"], 1)
        return [build_slot(name, slot["item"], page_type) for _ in range(n)]
    if kind == "object":
        return {fn: build_slot(fn, fs, page_type)
                for fn, fs in slot["fields"].items() if fs.get("required", True)}
    raise ValueError(kind)


def build_slide(number: int, page_type: str, contracts=None,
                bg=None, default_bg=None, logo=None, asset_keys=None) -> dict:
    contracts = contracts or PAGE_TYPES
    bg, default_bg, logo = bg or BG, default_bg or DEFAULT_BG, logo or LOGO
    if page_type in contracts:
        contract = contracts[page_type]
        slide = {
            "number": number,
            "page_type": page_type,
            "title": placeholder("title", 30),
            "render_page_number": contract["page_number"] == "required",
            "assets": {},
            "slots": {},
        }
        required_assets = contract["assets"]
        if asset_keys is not None and asset_keys.get(page_type) is not None:
            required_assets = asset_keys[page_type]  # 包內 per-頁型素材鍵覆寫
        for key in required_assets:
            slide["assets"][key] = logo if key == "logo" else bg.get(page_type, default_bg)
        for sname, sspec in contract["slots"].items():
            if sspec.get("required", True):
                slide["slots"][sname] = build_slot(sname, sspec, page_type)
        return slide
    # 未註冊頁型:基本骨架 + 提示
    return {
        "number": number,
        "page_type": page_type,
        "title": "【title】待填",
        "render_page_number": True,
        "assets": {"background": default_bg, "logo": logo},
        "slots": {"note": f"未註冊頁型:槽位自訂,容量與使用限制見 page_types.md 的 {page_type}"},
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--types", help="逗號分隔的頁型清單,依簡報頁序")
    ap.add_argument("--out", help="輸出路徑(不給就印到 stdout)")
    ap.add_argument("--list", action="store_true", help="列出頁型(有模板包時按包列三級支援)")
    ap.add_argument("--template-pack", help="模板包 id 或目錄(省略=light)")
    ap.add_argument("--packs-root", help="模板包根目錄(預設=tools 上層的 templates/)")
    args = ap.parse_args(argv)

    # 模板包解析(解不到且未明確指定 → 退回內建 light 預設,不加 deck.template)
    pack = None
    if pack_loader is not None:
        try:
            pack = pack_loader.load_pack(pack_arg=args.template_pack,
                                         packs_root=args.packs_root,
                                         load_bindings=False)
        except pack_loader.PackError as e:
            if args.template_pack:
                print(f"✗ 模板包載入失敗:{e}")
                return 2
    contracts, bg, default_bg, logo, asset_keys, modes = None, None, None, None, None, {}
    if pack is not None:
        m = pack.manifest
        try:
            contracts = apply_capacity_overrides(PAGE_TYPES, m.get("capacity_overrides"))
        except ValueError as e:
            print(f"✗ 模板包設定錯誤:{e}")
            return 2
        ad = m.get("asset_defaults") or {}
        cover_bg = ad.get("background_cover", BG["cover"])
        bg = {"cover": cover_bg, "closing": cover_bg}
        default_bg = ad.get("background_content", DEFAULT_BG)
        logo = ad.get("logo", LOGO)
        asset_keys = {pt: e.get("assets") for pt, e in pack.page_types.items()}
        modes = {pt: e.get("mode") for pt, e in pack.page_types.items()}

    if args.list or not args.types:
        if pack is not None:
            print(f"模板包 {pack.id}@{pack.version} 的頁型支援:")
            auto = [pt for pt, md in modes.items() if md in ("builtin", "fill")]
            clone = [pt for pt, md in modes.items() if md == "clone"]
            unsup = [pt for pt, md in modes.items() if md == "unsupported"]
            print(f"  全自動({len(auto)} 種,完整契約檢查):")
            for name in auto:
                print(f"    {name}")
            print(f"  半自動({len(clone)} 種,需 render_plan;容量見 page_types.md):")
            for name in clone:
                print(f"    {name}")
            if unsup:
                print(f"  不支援({len(unsup)} 種):")
                for name in unsup:
                    print(f"    {name}")
            return 0
        print("已註冊頁型(完整契約檢查):")
        for name in PAGE_TYPES:
            print(f"  {name}")
        print("其他頁型見 page_types.md(基本檢查,容量自律)")
        return 0

    types = [t.strip() for t in args.types.split(",") if t.strip()]
    blocked = [t for t in types if modes.get(t) == "unsupported"]
    if blocked:
        print(f"✗ 頁型不受模板 {pack.id!r} 支援,拒產骨架:{', '.join(blocked)}"
              f"(換頁型/換模板,支援清單見 --list)")
        return 2
    deck = {
        "deck_name": "my_deck",
        "language": "Traditional Chinese",
        "slide_count": len(types),
    }
    if pack is not None:
        deck["template"] = pack.id  # 模板選擇隨 spec 冪等(ARCHITECTURE §6)
    spec = {
        "deck": deck,
        "slides": [build_slide(i + 1, t, contracts, bg, default_bg, logo, asset_keys)
                   for i, t in enumerate(types)],
    }
    text = json.dumps(spec, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"骨架已寫入 {args.out}(共 {len(types)} 頁;占位文字「待填」請全部換成實際內容)")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
