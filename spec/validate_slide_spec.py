#!/usr/bin/env python3
"""Slide-spec 驗證器 —— 燒圖 token 之前的便宜文字閘門。

用途：LLM 產出 my_project/slide_spec.json 後，先跑這支收斂 AI 發散。
通過(exit 0)才進 image_gen；不通過(exit 1)在文字層 repair 重跑，成本近乎零。

只用標準庫，無外部依賴。

檢查分兩級：
  ERROR(硬擋)  結構缺漏 / 槽位數量不符版型 / 字數爆表 / 頁碼規則違反 / 捏造數字
  WARN(標記)   文字與 slides.md 來源相似度過低（可能是幻覺，但容忍換句話說）

抗幻覺核心 = provenance 追溯：
  - 數字：內容槽位裡的每個數字都必須在該頁原文出現（高精準抓捏造 KPI）→ ERROR
  - 文字：字元 bigram 覆蓋率 < 門檻 → WARN（寬鬆，容忍改寫）

用法：
  python3 spec/validate_slide_spec.py                         # 預設驗 my_project/slide_spec.json
  python3 spec/validate_slide_spec.py path/to/spec.json       # 指定檔案
  python3 spec/validate_slide_spec.py --strict                # 把 provenance WARN 升級成 ERROR
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSET_BASE = ROOT / "my_project"
SLIDES_MD = ASSET_BASE / "source" / "slides.md"
DEFAULT_SPEC = ASSET_BASE / "slide_spec.json"

COVERAGE_THRESHOLD = 0.55  # 文字 bigram 覆蓋率低於此值 → 疑似未依來源

# ---------------------------------------------------------------------------
# Page-type registry：每種版型的槽位契約。新增版型 = 在此加一筆 + 更新 schema enum。
#
# slot 文法（可遞迴）：
#   {"kind": "text",   "max_chars": N, "required": bool, "provenance": bool}
#   {"kind": "list",   "min": N, "max": M, "required": bool, "item": <slot>}
#   {"kind": "object", "required": bool, "fields": {name: <slot>, ...}}
# provenance 預設 True（內容槽位都追溯來源）；結構性標籤明確設 False。
# page_number: "required" | "none"
# assets: 必要的素材鍵清單
# ---------------------------------------------------------------------------
T = lambda mx, required=True, provenance=True: {
    "kind": "text", "max_chars": mx, "required": required, "provenance": provenance
}

PAGE_TYPES = {
    "cover": {
        "page_number": "none",
        "assets": ["background", "logo"],
        "slots": {
            "main_title": T(20),
            "subtitle": T(20),
            "date": T(20),
            "presenters": T(40),
        },
    },
    "closing": {
        "page_number": "none",
        "assets": ["background"],
        "slots": {
            "main_title": T(20, provenance=False),  # "Thank you" 為結構性收尾字
        },
    },
    "agenda": {
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "items": {
                "kind": "list", "min": 3, "max": 6, "required": True,
                "item": {"kind": "object", "fields": {
                    "number": T(4, provenance=False),
                    "title": T(20),
                    "subtitle": T(60, required=False),
                }},
            },
        },
    },
    "vision_goal_center_balance": {
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "core_mission": T(60),
            "annual_goal": T(60),
            "projects": {"kind": "list", "min": 2, "max": 3, "required": True, "item": T(40)},
            "kpis": {
                "kind": "list", "min": 2, "max": 4, "required": True,
                "item": {"kind": "object", "fields": {"label": T(30), "value": T(12)}},
            },
        },
    },
    "info_three_column_category": {
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "columns": {
                "kind": "list", "min": 3, "max": 3, "required": True,
                "item": {"kind": "object", "fields": {
                    "heading": T(20),
                    "points": {"kind": "list", "min": 2, "max": 6, "required": True, "item": T(40)},
                }},
            },
        },
    },
    "data_two_group_metric_comparison": {
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "before": {"kind": "object", "fields": {
                "heading": T(12, provenance=False),
                "points": {"kind": "list", "min": 2, "max": 6, "required": True, "item": T(40)},
            }},
            "after": {"kind": "object", "fields": {
                "heading": T(12, provenance=False),
                "points": {"kind": "list", "min": 2, "max": 6, "required": True, "item": T(40)},
            }},
            "kpis": {
                "kind": "list", "min": 2, "max": 3, "required": True,
                "item": {"kind": "object", "fields": {"label": T(30), "value": T(12)}},
            },
        },
    },
    "evaluation_option_score_pros_cons": {
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "recommended": T(20, required=False, provenance=False),
            "options": {
                "kind": "list", "min": 2, "max": 3, "required": True,
                "item": {"kind": "object", "fields": {
                    "name": T(24),
                    "pros": {"kind": "list", "min": 1, "max": 4, "required": True, "item": T(60)},
                    "cons": {"kind": "list", "min": 1, "max": 3, "required": True, "item": T(60)},
                }},
            },
            "recommendation": {"kind": "list", "min": 0, "max": 5, "required": False, "item": T(40)},
        },
    },
    "story_chapter_statement": {
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "background_points": {"kind": "list", "min": 2, "max": 4, "required": True, "item": T(40)},
            "story": {
                "kind": "list", "min": 3, "max": 3, "required": True,
                "item": {"kind": "object", "fields": {"phase": T(8), "text": T(60)}},
            },
            "outcomes": {"kind": "list", "min": 2, "max": 4, "required": True, "item": T(40)},
        },
    },
    "pyramid_layered_maturity_detail": {
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "levels": {
                "kind": "list", "min": 4, "max": 5, "required": True,
                "item": {"kind": "object", "fields": {"label": T(20), "detail": T(40)}},
            },
            "side_cards": {
                "kind": "list", "min": 1, "max": 2, "required": False,
                "item": {"kind": "object", "fields": {
                    "heading": T(16),
                    "points": {"kind": "list", "min": 2, "max": 4, "required": True, "item": T(30)},
                }},
            },
        },
    },
    "stage_dual_track_roadmap": {
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "quarters": {"kind": "list", "min": 4, "max": 4, "required": True, "item": T(12)},
            "lanes": {
                "kind": "list", "min": 2, "max": 2, "required": True,
                "item": {"kind": "object", "fields": {
                    "name": T(40),
                    "cells": {"kind": "list", "min": 4, "max": 4, "required": True, "item": T(40)},
                }},
            },
            "annual_cycle": {"kind": "list", "min": 3, "max": 6, "required": True, "item": T(12)},
        },
    },
}


# ---------------------------------------------------------------------------
# 文字正規化 / 追溯工具
# ---------------------------------------------------------------------------
def _nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s)


def norm(s: str) -> str:
    """NFKC + 去空白 + 去標點/符號，保留字母數字與 CJK。用於文字覆蓋率比對。"""
    out = []
    for ch in _nfkc(s):
        if ch.isspace():
            continue
        if unicodedata.category(ch)[0] in ("P", "S"):  # 標點 / 符號（含 、：。｜%）
            continue
        out.append(ch)
    return "".join(out)


def bigrams(s: str) -> set:
    s = norm(s)
    if len(s) <= 1:
        return {s} if s else set()
    return {s[i:i + 2] for i in range(len(s) - 1)}


def coverage(spec_str: str, block: str) -> float:
    """spec 字串的 bigram 有多少比例出現在來源頁 block 中。1.0 = 完全可追溯。"""
    sb = bigrams(spec_str)
    if not sb:
        return 1.0
    return len(sb & bigrams(block)) / len(sb)


NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def numbers(s: str) -> list:
    return NUM_RE.findall(_nfkc(s))


def block_digits(block: str) -> str:
    return _nfkc(block)


# ---------------------------------------------------------------------------
# 解析 slides.md（沿用專案既有規則）
# ---------------------------------------------------------------------------
def parse_slides(text: str) -> dict:
    pattern = re.compile(r"^## Slide\s+(\d+)\s*$", re.M)
    matches = list(pattern.finditer(text))
    result = {}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        result[int(m.group(1))] = text[start:end]
    return result


# ---------------------------------------------------------------------------
# 報告收集器
# ---------------------------------------------------------------------------
class Report:
    def __init__(self, strict: bool):
        self.strict = strict
        self.errors = []
        self.warnings = []

    def error(self, path, msg):
        self.errors.append((path, msg))

    def warn(self, path, msg):
        if self.strict:
            self.errors.append((path, msg + "  [--strict 升級]"))
        else:
            self.warnings.append((path, msg))


# ---------------------------------------------------------------------------
# 遞迴槽位驗證
# ---------------------------------------------------------------------------
def validate_value(val, slot, path, block, rep: Report):
    kind = slot["kind"]

    if kind == "text":
        if not isinstance(val, str):
            rep.error(path, f"應為文字，實得 {type(val).__name__}")
            return
        if val.strip() == "":
            rep.error(path, "文字為空")
            return
        n = len(val)
        if n > slot["max_chars"]:
            rep.error(path, f"字數 {n} 超過上限 {slot['max_chars']}：「{val[:24]}…」")
        if slot.get("provenance", True) and block is not None:
            bd = block_digits(block)
            for num in numbers(val):
                if num not in bd:
                    rep.error(path, f"疑似捏造數字 {num!r}（來源頁原文找不到）：「{val}」")
            cov = coverage(val, block)
            if cov < COVERAGE_THRESHOLD:
                rep.warn(path, f"文字與來源相似度低 {cov:.2f} < {COVERAGE_THRESHOLD}，可能未依 slides.md：「{val}」")

    elif kind == "list":
        if not isinstance(val, list):
            rep.error(path, f"應為陣列，實得 {type(val).__name__}")
            return
        n = len(val)
        if n < slot["min"] or n > slot["max"]:
            rep.error(path, f"項目數 {n} 不符版型規定（{slot['min']}–{slot['max']}）")
        for i, item in enumerate(val):
            validate_value(item, slot["item"], f"{path}[{i}]", block, rep)

    elif kind == "object":
        if not isinstance(val, dict):
            rep.error(path, f"應為物件，實得 {type(val).__name__}")
            return
        fields = slot["fields"]
        for fname, fspec in fields.items():
            required = fspec.get("required", True)
            present = fname in val and val[fname] not in (None, "", [])
            if not present:
                if required:
                    rep.error(f"{path}.{fname}", "缺少必填欄位")
                continue
            validate_value(val[fname], fspec, f"{path}.{fname}", block, rep)
        for k in val:
            if k not in fields:
                rep.warn(f"{path}.{k}", "非預期欄位（版型未定義，將被忽略）")


def validate_slide(slide, block, rep: Report):
    num = slide.get("number", "?")
    p = f"slide[{num}]"
    pt = slide.get("page_type")

    if pt not in PAGE_TYPES:
        rep.error(p, f"未知 page_type {pt!r}（未在 PAGE_TYPES 註冊）")
        return
    spec = PAGE_TYPES[pt]

    # 頁碼規則
    rule = spec["page_number"]
    expected = (rule == "required")
    if "render_page_number" in slide:
        if slide["render_page_number"] != expected:
            rep.error(p, f"render_page_number={slide['render_page_number']} 與版型 {pt} 規則不符（應為 {expected}）")
    else:
        rep.warn(p, f"未設 render_page_number（版型 {pt} 預期 {expected}）")

    # 素材
    assets = slide.get("assets", {})
    for key in spec["assets"]:
        if key not in assets or not assets[key]:
            rep.error(f"{p}.assets", f"缺少必要素材 {key!r}")
            continue
        fpath = ASSET_BASE / assets[key]
        if not fpath.exists():
            rep.error(f"{p}.assets.{key}", f"素材檔不存在：{assets[key]}")

    # 槽位
    slots = slide.get("slots")
    if not isinstance(slots, dict):
        rep.error(p, "缺少 slots 物件")
        return
    validate_value(slots, {"kind": "object", "fields": spec["slots"]}, f"{p}.slots", block, rep)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main(argv):
    strict = "--strict" in argv
    args = [a for a in argv if not a.startswith("--")]
    spec_path = Path(args[0]) if args else DEFAULT_SPEC

    rep = Report(strict=strict)

    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"✗ 找不到 spec 檔：{spec_path}")
        return 2
    except json.JSONDecodeError as e:
        print(f"✗ JSON 解析失敗：{e}")
        return 2

    blocks = {}
    if SLIDES_MD.exists():
        blocks = parse_slides(SLIDES_MD.read_text(encoding="utf-8"))
    else:
        rep.warn("deck", f"找不到來源 {SLIDES_MD}，略過 provenance 追溯")

    # 結構層
    if not isinstance(spec.get("deck"), dict):
        rep.error("deck", "缺少 deck 物件")
    slides = spec.get("slides")
    if not isinstance(slides, list) or not slides:
        rep.error("slides", "缺少 slides 陣列或為空")
        slides = []

    seen = set()
    for idx, slide in enumerate(slides):
        if not isinstance(slide, dict):
            rep.error(f"slides[{idx}]", "投影片應為物件")
            continue
        n = slide.get("number")
        if n in seen:
            rep.error(f"slides[{idx}]", f"投影片編號重複：{n}")
        seen.add(n)
        for f in ("number", "page_type", "title", "slots"):
            if f not in slide:
                rep.error(f"slides[{idx}]", f"缺少必填欄位 {f!r}")
        block = blocks.get(n)
        if block is None and blocks:
            rep.warn(f"slide[{n}]", "在 slides.md 找不到對應頁，略過該頁 provenance")
        validate_slide(slide, block, rep)

    declared = spec.get("deck", {}).get("slide_count")
    if declared is not None and declared != len(slides):
        rep.error("deck.slide_count", f"宣告 {declared} 頁，實際 {len(slides)} 頁")

    # 輸出
    print(f"驗證：{spec_path}")
    print(f"頁數：{len(slides)}    來源追溯：{'開' if blocks else '關(找不到 slides.md)'}    strict：{strict}")
    print("-" * 72)
    if rep.errors:
        print(f"✗ ERROR ({len(rep.errors)})")
        for path, msg in rep.errors:
            print(f"   [E] {path}: {msg}")
    if rep.warnings:
        print(f"⚠ WARN ({len(rep.warnings)})")
        for path, msg in rep.warnings:
            print(f"   [W] {path}: {msg}")
    print("-" * 72)
    if rep.errors:
        print(f"結果：FAIL — {len(rep.errors)} 個錯誤需修正（此 spec 不得進入 image_gen）")
        return 1
    print(f"結果：PASS{'（有 ' + str(len(rep.warnings)) + ' 個警告，建議人工確認）' if rep.warnings else ''} — 可進入渲染")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
