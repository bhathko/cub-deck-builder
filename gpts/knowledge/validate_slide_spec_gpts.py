#!/usr/bin/env python3
"""Slide-spec 驗證器（GPTs 可攜版）—— 產出 pptx 之前的便宜文字閘門。

以 repo 內 fallback/validate_slide_spec.py 為基底移植，兩點刻意差異：
  1. 路徑改為命令列參數，讓它能在 ChatGPT Code Interpreter（/mnt/data）或任意目錄執行。
  2. 兩級閘門：page_type 在 PAGE_TYPES 註冊者 → 完整槽位契約檢查（同 repo 版）；
     未註冊但存在於 page_types.md 頁型庫者 → 降級為「泛用防幻覺檢查」——
     捏造數字仍是 ERROR、低相似度仍是 WARN，但槽位名稱/數量/字數不受檢
     （容量請自行比照 page_types.md 的「內容容量」節）。
     加 --registered-only 可恢復 repo 版行為（未註冊 = ERROR）。
2026-07-20 repo 瘦身後本檔即 PAGE_TYPES 的**單一真相來源**(原 repo 版
fallback/validate_slide_spec.py 已移除);改契約時同步 slide_spec.schema.json
的 enum 與 page_types_registry.md,共三處。

檢查分兩級：
  ERROR(硬擋)  結構缺漏 / 槽位數量不符版型 / 字數爆表 / 頁碼規則違反 / 捏造數字
  WARN(標記)   文字與 slides.md 來源相似度過低（可能是幻覺，但容忍換句話說）

抗幻覺核心 = provenance 追溯：
  - 數字：內容槽位裡的每個數字都必須在該頁原文出現（高精準抓捏造 KPI）→ ERROR
  - 文字：字元 bigram 覆蓋率 < 門檻 → WARN（寬鬆，容忍改寫）
  - 草稿佔位符（「待補充」「待確認」「待定」「TBD」）不視為內容事實，
    先剔除再追溯：整格只有佔位符 → 直接通過；佔位符以外的殘餘文字照常檢查。
    支援「先出草稿、之後補資料」的工作流；佔位符本身不含數字，捏造實值仍會被擋。

用法（在 Code Interpreter 中）：
  python /mnt/data/validate_slide_spec_gpts.py \
      --spec /mnt/data/slide_spec.json \
      --slides /mnt/data/slides.md \
      --asset-dir /mnt/data
  加 --strict 可把 provenance WARN 升級成 ERROR。

exit 0 = PASS（才准產 pptx）；exit 1 = FAIL（回到文字層修 spec）。
只用標準庫，無外部依賴。
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

DEFAULT_SPEC = Path("/mnt/data/slide_spec.json")
DEFAULT_SLIDES = Path("/mnt/data/slides.md")
DEFAULT_ASSET_DIR = Path("/mnt/data")

COVERAGE_THRESHOLD = 0.55  # 文字 bigram 覆蓋率低於此值 → 疑似未依來源

# 草稿佔位符：使用者授權「先出結構、之後補資料」。這些字串不算內容事實，
# provenance 追溯前先剔除。改動清單時同步 outline_to_ppt_skill.md 與
# page_types_registry.md 的佔位符說明。
PLACEHOLDER_RE = re.compile(r"待補充|待確認|待定|TBD", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Page-type registry：每種版型的槽位契約。新增版型 = 在此加一筆 + 更新 schema enum。
# ※ 本表即單一真相來源;改動時同步 schema enum 與 page_types_registry.md。
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


def strip_placeholders(s: str) -> str:
    """剔除草稿佔位符後回傳殘餘文字；殘餘為空代表整格都是佔位符，免追溯。"""
    return PLACEHOLDER_RE.sub("", _nfkc(s))


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
            checked = strip_placeholders(val)
            if norm(checked):
                bd = block_digits(block)
                for num in numbers(checked):
                    if num not in bd:
                        rep.error(path, f"疑似捏造數字 {num!r}（來源頁原文找不到）：「{val}」")
                cov = coverage(checked, block)
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


def generic_provenance(val, path, block, rep: Report):
    """未註冊頁型的泛用防幻覺檢查：走遍 slots 裡所有字串。
    捏造數字 → ERROR；bigram 覆蓋率過低 → WARN。不檢查槽位形狀/數量/字數。
    注意：結構性標號（"01"、"Q1" 等）若未出現在 slides.md 原文會被誤判成捏造，
    請把這類標號也寫進 slides.md，或改用已註冊頁型。"""
    if isinstance(val, str):
        if block is None or val.strip() == "":
            return
        checked = strip_placeholders(val)
        if not norm(checked):
            return
        bd = block_digits(block)
        for num in numbers(checked):
            if num not in bd:
                rep.error(path, f"疑似捏造數字 {num!r}（來源頁原文找不到）：「{val}」")
        cov = coverage(checked, block)
        if cov < COVERAGE_THRESHOLD:
            rep.warn(path, f"文字與來源相似度低 {cov:.2f} < {COVERAGE_THRESHOLD}，可能未依 slides.md：「{val}」")
    elif isinstance(val, list):
        for i, item in enumerate(val):
            generic_provenance(item, f"{path}[{i}]", block, rep)
    elif isinstance(val, dict):
        for k, v in val.items():
            generic_provenance(v, f"{path}.{k}", block, rep)


def validate_slide(slide, block, asset_base: Path, rep: Report, registered_only: bool = False):
    num = slide.get("number", "?")
    p = f"slide[{num}]"
    pt = slide.get("page_type")

    if pt not in PAGE_TYPES:
        if registered_only:
            rep.error(p, f"未知 page_type {pt!r}（未在 PAGE_TYPES 註冊）")
            return
        # 兩級閘門：未註冊頁型 → 泛用防幻覺檢查（槽位契約不受檢）
        rep.warn(p, f"page_type {pt!r} 未在 PAGE_TYPES 註冊：僅做防幻覺追溯，"
                    f"槽位數量/字數請自行比照 page_types.md 的「內容容量」")
        for key, rel in (slide.get("assets") or {}).items():
            if rel and not (asset_base / rel).exists():
                rep.error(f"{p}.assets.{key}", f"素材檔不存在：{rel}（相對於 {asset_base}）")
        slots = slide.get("slots")
        if not isinstance(slots, dict):
            rep.error(p, "缺少 slots 物件")
            return
        generic_provenance(slots, f"{p}.slots", block, rep)
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
        fpath = asset_base / assets[key]
        if not fpath.exists():
            rep.error(f"{p}.assets.{key}", f"素材檔不存在：{assets[key]}（相對於 {asset_base}）")

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
    registered_only = "--registered-only" in argv
    spec_path, slides_path, asset_base = DEFAULT_SPEC, DEFAULT_SLIDES, DEFAULT_ASSET_DIR

    args = [a for a in argv if a not in ("--strict", "--registered-only")]
    positional = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--spec":
            i += 1
            spec_path = Path(args[i])
        elif a == "--slides":
            i += 1
            slides_path = Path(args[i])
        elif a == "--asset-dir":
            i += 1
            asset_base = Path(args[i])
        elif a.startswith("--"):
            print(f"✗ 未知參數：{a}")
            return 2
        else:
            positional.append(a)
        i += 1
    if positional:  # 兼容 repo 版的「位置參數 = spec 路徑」用法
        spec_path = Path(positional[0])

    rep = Report(strict=strict)

    try:
        # utf-8-sig:容忍 Windows 工具寫入的 BOM(使用者上傳的 JSON 常見)
        spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"✗ 找不到 spec 檔：{spec_path}")
        return 2
    except json.JSONDecodeError as e:
        print(f"✗ JSON 解析失敗：{e}")
        return 2

    blocks = {}
    if slides_path.exists():
        blocks = parse_slides(slides_path.read_text(encoding="utf-8"))
    else:
        rep.warn("deck", f"找不到來源 {slides_path}，略過 provenance 追溯")

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
        validate_slide(slide, block, asset_base, rep, registered_only)

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
        print(f"結果：FAIL — {len(rep.errors)} 個錯誤需修正（此 spec 不得產出 pptx）")
        return 1
    print(f"結果：PASS{'（有 ' + str(len(rep.warnings)) + ' 個警告，建議人工確認）' if rep.warnings else ''} — 可進入渲染")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
