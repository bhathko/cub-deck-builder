#!/usr/bin/env python3
"""驗證前工作流稽核(程式版)—— 補 validator 刻意不管的三個缺口。

validator 只追溯已註冊頁型契約內開 provenance 的 slots,且數字用子字串比對;
本工具把 outline 模式原本靠模型自律的稽核變成硬閘門:
  1. slides.md 完整性(帶 --source 時):每個 Slide 區塊的每一行都必須是
     本次原文檔的逐字片段(容忍空白差異)→ 防改寫/補寫/混入舊回合。
  2. 頂層 slides[].title 逐字出現在該頁區塊;deck.deck_name 等於第一頁
     真正內容頁(非 cover/agenda/closing)的 title。closing 固定 Thank you 豁免。
  3. 精確數字 token:deck_name、每頁 title 與 slots 所有字串,先剔除草稿
     佔位符,再以 token 精確比對(來源 50 不得支援輸出 5)。
豁免:agenda 順序編號(slots.items[*].number)、數據比較頁固定標題
(slots.before/after.heading)、closing 全頁、佔位符(待補充/待確認/待定/TBD)。

用法:
  python /mnt/data/tools/audit_provenance.py \
      --spec /mnt/data/slide_spec.json \
      --slides /mnt/data/slides.md \
      [--source /mnt/data/outline_source_current.txt]

exit 0 = PASS;exit 1 = FAIL(逐條列出問題);exit 2 = 環境/輸入錯誤。
只用標準庫;佔位符與數字規則 import 自 validate_slide_spec_gpts.py(單一來源,
兩檔需同在 /mnt/data 或父目錄,同 make_skeleton 慣例)。
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _cand in (_HERE.parent, _HERE, Path("/mnt/data"), Path.cwd()):
    if (_cand / "validate_slide_spec_gpts.py").exists():
        sys.path.insert(0, str(_cand))
        break
try:
    from validate_slide_spec_gpts import (  # noqa: E402
        NUM_RE, PLACEHOLDER_RE, parse_slides, strip_placeholders,
    )
except ImportError:
    print("[E] 找不到 validate_slide_spec_gpts.py(需與本工具同在 /mnt/data 或父目錄)")
    sys.exit(2)

STRUCTURAL_PAGES = {"cover", "agenda", "closing"}
# path 規則 → 該欄位為結構值,免稽核(與 validator 契約的 provenance=False 對齊)
EXEMPT_PATHS = [
    ("agenda", re.compile(r"^slots\.items\[\d+\]\.number$")),
    ("data_two_group_metric_comparison", re.compile(r"^slots\.(before|after)\.heading$")),
]


def nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s)


def squash(s: str) -> str:
    """NFKC + 空白壓縮,供「逐字片段」比對(容忍換行/縮排差異)。"""
    return re.sub(r"\s+", " ", nfkc(s)).strip()


def tokens(s: str) -> list:
    return NUM_RE.findall(nfkc(s))


def walk_strings(val, path, out):
    if isinstance(val, str):
        out.append((path, val))
    elif isinstance(val, list):
        for i, item in enumerate(val):
            walk_strings(item, f"{path}[{i}]", out)
    elif isinstance(val, dict):
        for k, v in val.items():
            walk_strings(v, f"{path}.{k}", out)


def is_exempt(page_type: str, path: str) -> bool:
    if page_type == "closing":
        return True
    return any(pt == page_type and pat.match(path) for pt, pat in EXEMPT_PATHS)


def main(argv):
    args = {}
    it = iter(argv)
    for a in it:
        if a in ("--spec", "--slides", "--source"):
            args[a] = next(it, None)
    spec_path = Path(args.get("--spec") or "/mnt/data/slide_spec.json")
    slides_path = Path(args.get("--slides") or "/mnt/data/slides.md")
    source_path = Path(args["--source"]) if args.get("--source") else None

    for p, label in ((spec_path, "spec"), (slides_path, "slides.md")):
        if not p.exists():
            print(f"[E] 找不到 {label}:{p}")
            return 2
    spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    blocks = parse_slides(slides_path.read_text(encoding="utf-8-sig"))
    problems = []

    # 1) slides.md 完整性:區塊每一行都是本次原文的逐字片段
    if source_path is not None:
        if not source_path.exists():
            print(f"[E] 找不到 --source:{source_path}")
            return 2
        src = squash(source_path.read_text(encoding="utf-8-sig"))
        for n, block in sorted(blocks.items()):
            for line in block.splitlines():
                frag = squash(line)
                if not frag or frag.startswith("#"):
                    continue
                if PLACEHOLDER_RE.fullmatch(frag):
                    continue
                if frag == "Thank you":
                    continue
                if frag not in src:
                    problems.append(
                        f"slides.md Slide {n}:「{frag[:30]}…」不是本次原文的逐字片段"
                        if len(frag) > 30 else
                        f"slides.md Slide {n}:「{frag}」不是本次原文的逐字片段")

    slides = spec.get("slides", [])
    deck_name = spec.get("deck", {}).get("deck_name", "")

    # 2) 頂層 title 逐字 + deck_name 規則
    first_content = None
    for s in slides:
        n = s.get("number")
        pt = s.get("page_type", "")
        title = s.get("title", "")
        block = blocks.get(n)
        if pt not in STRUCTURAL_PAGES and first_content is None:
            first_content = s
        if pt == "closing":
            if title != "Thank you":
                problems.append(f"slide[{n}] closing 的 title 應為固定值 Thank you,實得「{title}」")
            continue
        if block is None:
            problems.append(f"slide[{n}] 在 slides.md 找不到「## Slide {n}」區塊")
            continue
        if title and squash(title) not in squash(block):
            problems.append(f"slide[{n}] 頂層 title「{title}」未逐字出現在該頁來源區塊")

    if first_content is None:
        problems.append("整份 spec 沒有任何真正內容頁(非 cover/agenda/closing)")
    elif deck_name != first_content.get("title", ""):
        problems.append(
            f"deck.deck_name「{deck_name}」≠ 第一頁內容頁 slide[{first_content.get('number')}] "
            f"的 title「{first_content.get('title', '')}」")

    # 3) 精確數字 token(剔除佔位符後)
    def check_tokens(text, block, where):
        block_tokens = set(tokens(block)) if block else set()
        for tk in tokens(strip_placeholders(text)):
            if tk not in block_tokens:
                problems.append(f"{where}:數字 token「{tk}」在來源區塊無精確對應:「{text}」")

    if first_content is not None:
        check_tokens(deck_name, blocks.get(first_content.get("number")), "deck.deck_name")
    for s in slides:
        n = s.get("number")
        pt = s.get("page_type", "")
        block = blocks.get(n)
        if pt == "closing" or block is None:
            continue
        check_tokens(s.get("title", ""), block, f"slide[{n}].title")
        strings = []
        walk_strings(s.get("slots", {}), "slots", strings)
        for path, val in strings:
            if is_exempt(pt, path):
                continue
            check_tokens(val, block, f"slide[{n}].{path}")

    print(f"稽核:{spec_path}")
    print(f"來源完整性:{'開' if source_path else '關(未帶 --source)'}    "
          f"頁數:{len(slides)}")
    print("-" * 72)
    for msg in problems:
        print(f"  [E] {msg}")
    print("-" * 72)
    if problems:
        print(f"結果:FAIL — {len(problems)} 個問題(修 spec/slides.md 後重跑;不得補寫來源)")
        return 1
    print("結果:PASS — 可進入 validator")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
