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
for p in (_HERE, _HERE.parent, Path("/mnt/data")):
    sys.path.insert(0, str(p))

try:
    from validate_slide_spec_gpts import PAGE_TYPES
except ImportError:
    print("✗ 找不到 validate_slide_spec_gpts.py(需與本工具同在 /mnt/data 或其父目錄)")
    sys.exit(2)

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


def build_slide(number: int, page_type: str) -> dict:
    if page_type in PAGE_TYPES:
        contract = PAGE_TYPES[page_type]
        slide = {
            "number": number,
            "page_type": page_type,
            "title": placeholder("title", 30),
            "render_page_number": contract["page_number"] == "required",
            "assets": {},
            "slots": {},
        }
        for key in contract["assets"]:
            slide["assets"][key] = LOGO if key == "logo" else BG.get(page_type, DEFAULT_BG)
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
        "assets": {"background": DEFAULT_BG, "logo": LOGO},
        "slots": {"note": f"未註冊頁型:槽位自訂,容量與使用限制見 page_types.md 的 {page_type}"},
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--types", help="逗號分隔的頁型清單,依簡報頁序")
    ap.add_argument("--out", help="輸出路徑(不給就印到 stdout)")
    ap.add_argument("--list", action="store_true", help="列出已註冊頁型")
    args = ap.parse_args(argv)

    if args.list or not args.types:
        print("已註冊頁型(完整契約檢查):")
        for name in PAGE_TYPES:
            print(f"  {name}")
        print("其他頁型見 page_types.md(基本檢查,容量自律)")
        return 0

    types = [t.strip() for t in args.types.split(",") if t.strip()]
    spec = {
        "deck": {
            "deck_name": "my_deck",
            "language": "Traditional Chinese",
            "slide_count": len(types),
        },
        "slides": [build_slide(i + 1, t) for i, t in enumerate(types)],
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
