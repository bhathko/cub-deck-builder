#!/usr/bin/env python3
"""make_skeleton — 依頁型清單或契約先行規劃產出 slide_spec.json 骨架。

使用者要範本時一律用這支產,不要在對話裡手打 JSON(容易寫出違規骨架,
浪費一輪驗證循環)。

用法:
  python make_skeleton.py --types cover,agenda,info_three_column_category,closing \
      --out /mnt/data/slide_spec.json
  python make_skeleton.py --plan /mnt/data/page_type_candidates.json \
      --source /mnt/data/outline_source_current.txt \
      --selected-plan-out /mnt/data/page_type_plan.json \
      --slides-out /mnt/data/slides.md --out /mnt/data/slide_spec.json
  python make_skeleton.py --list          # 列出已註冊頁型
  python make_skeleton.py --describe info_card_grid,stage_timeline_progress

規則:
- --plan(大綱模式):模型只列「來源逐字片段 + 語意同樣合適的候選頁型 +
  來源實際清單數量」;本工具先用模板包合併契約排除容量不合候選,再以確定性
  全局選型減少相鄰重複與單一版型集中。選定後才產骨架與 slides.md。
  plan 頂層另需 not_nominated 整庫覆蓋審視:每個非結構全自動頁型,不提名
  就要給語意不合理由(同族可用「字首_*」一筆涵蓋),缺漏即 exit 1——候選
  廣度是工具稽核的不變式。同分決勝用來源片段 hash(零隨機、同輸入必同輸出,
  不同 deck 不會永遠收斂到同一版型)。
- 已註冊頁型:依 validate_slide_spec_gpts.py 的 PAGE_TYPES 契約生成——必填槽位
  全建、清單取下限數量、占位文字「【欄位名】待填」且必在字數上限內。
- 未註冊頁型(page_types.md 頁型庫):slots 只放一個提示欄位,容量請自行
  比照 page_types.md 填寫。
- assets / render_page_number / slide_count 自動按規則填好。
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import re
import sys
import unicodedata
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
FIT_RANK = {"exact": 0, "acceptable": 1}
STRUCTURAL_PAGES = {"cover", "agenda", "section_transition", "closing"}
PLAN_VERSION = 2
BEAM_WIDTH = 4096


def placeholder(name: str, max_chars: int) -> str:
    text = f"【{name}】待填"
    if len(text) > max_chars:
        text = "待填"[:max_chars]
    return text


def _count_path_present(counts, path):
    return any(k == path or k.startswith(path + ".") or k.startswith(path + "[]")
               for k in counts)


def build_slot(name, slot, page_type, counts=None, path=None, parent_occurrence=0):
    counts = counts or {}
    path = path or name
    kind = slot["kind"]
    if kind == "text":
        return FIXED.get((page_type, name), placeholder(name, slot["max_chars"]))
    if kind == "list":
        raw = counts.get(path)
        if isinstance(raw, list):
            n = raw[parent_occurrence]
        elif isinstance(raw, int) and not isinstance(raw, bool):
            n = raw
        else:
            n = max(slot["min"], 1)
        return [build_slot(name, slot["item"], page_type, counts,
                           f"{path}[]", i) for i in range(n)]
    if kind == "object":
        return {
            fn: build_slot(fn, fs, page_type, counts, f"{path}.{fn}", parent_occurrence)
            for fn, fs in slot["fields"].items()
            if fs.get("required", True)
            or _count_path_present(counts, f"{path}.{fn}")
        }
    raise ValueError(kind)


def build_slide(number: int, page_type: str, contracts=None,
                bg=None, default_bg=None, logo=None, asset_keys=None,
                counts=None) -> dict:
    contracts = contracts or PAGE_TYPES
    counts = counts or {}
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
            if sspec.get("required", True) or _count_path_present(counts, sname):
                slide["slots"][sname] = build_slot(
                    sname, sspec, page_type, counts, sname, 0)
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


def squash(text: str) -> str:
    """NFKC + 空白壓縮,與 audit_provenance 的來源逐字判定一致。"""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip()


def _list_specs(node, path, parent_list=None, required=True, out=None):
    """把契約內清單節點展平成 counts 路徑(父清單先於子清單)。"""
    out = out if out is not None else []
    required = required and node.get("required", True)
    kind = node.get("kind")
    if kind == "list":
        out.append({
            "path": path,
            "parent": parent_list,
            "required": required,
            "min": node["min"],
            "max": node["max"],
        })
        _list_specs(node["item"], f"{path}[]", path, required, out)
    elif kind == "object":
        for name, child in node.get("fields", {}).items():
            child_path = f"{path}.{name}" if path else name
            _list_specs(child, child_path, parent_list, required, out)
    return out


def contract_list_specs(contract):
    out = []
    for name, node in contract.get("slots", {}).items():
        _list_specs(node, name, None, True, out)
    return out


def _count_values(raw, occurrences, path):
    if isinstance(raw, bool):
        return None, f"counts.{path} 必須是整數或整數清單"
    if isinstance(raw, int):
        values = [raw] * occurrences
    elif isinstance(raw, list) and all(isinstance(v, int) and not isinstance(v, bool)
                                       for v in raw):
        if len(raw) != occurrences:
            return None, (f"counts.{path} 需有 {occurrences} 筆(對應父層每一項),"
                          f"實得 {len(raw)}")
        values = raw
    else:
        return None, f"counts.{path} 必須是整數或整數清單"
    return values, None


def validate_candidate_counts(page_type, candidate, contract):
    """驗證來源實際項目數是否放得進選定模板包的 merged 契約。"""
    counts = candidate.get("counts")
    if counts is None:
        counts = {}
    if not isinstance(counts, dict):
        return ["counts 必須是物件"]

    specs = contract_list_specs(contract)
    known = {s["path"] for s in specs}
    errors = [f"counts.{p} 不是頁型 {page_type} 的清單槽位"
              for p in counts if p not in known]
    actual = {}
    for spec in specs:
        path, parent = spec["path"], spec["parent"]
        raw = counts.get(path)
        if raw is None:
            if spec["required"]:
                errors.append(f"counts 缺少必填清單 {path}")
            continue
        if parent is None:
            occurrences = 1
        elif parent not in actual:
            errors.append(f"counts.{path} 的父清單 {parent} 尚未提供有效數量")
            continue
        else:
            occurrences = sum(actual[parent])
        values, err = _count_values(raw, occurrences, path)
        if err:
            errors.append(err)
            continue
        actual[path] = values
        for i, value in enumerate(values):
            if value < spec["min"] or value > spec["max"]:
                suffix = f"[{i}]" if occurrences > 1 else ""
                errors.append(
                    f"counts.{path}{suffix}={value} 不符 {spec['min']}–{spec['max']}")
    if page_type == "data_line_trend_comparison":
        categories = actual.get("categories", [None])[0]
        series_values = actual.get("series[].values", [])
        for i, value in enumerate(series_values):
            if categories is not None and value != categories:
                errors.append(
                    f"counts.series[].values[{i}]={value} 必須等於 categories={categories}")
    return errors


def _source_excerpts(slide):
    raw = slide.get("source_excerpt", [])
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list) or not all(isinstance(v, str) for v in raw):
        raise ValueError("source_excerpt 必須是文字或文字清單")
    return [v for v in raw if v.strip()]


def _composition_cost(sequence):
    """多樣性成本;末位決勝用來源片段 hash(跨 deck 打散、同輸入必同輸出),
    不再用候選列出順序——否則每份 deck 都收斂到模型慣性排第一的頁型。"""
    content = [c for c in sequence if c["page_type"] not in STRUCTURAL_PAGES]
    adjacent = 0
    for left, right in zip(sequence, sequence[1:]):
        if (left["page_type"] not in STRUCTURAL_PAGES
                and right["page_type"] not in STRUCTURAL_PAGES
                and left["_layout"] == right["_layout"]):
            adjacent += 1
    counts = Counter(c["_layout"] for c in content)
    max_use = max(counts.values(), default=0)
    repeat_pairs = sum(n * (n - 1) // 2 for n in counts.values())
    tie_key = tuple(c["_tie"] for c in sequence)
    order_key = tuple(c["_order"] for c in sequence)
    return adjacent, max_use, repeat_pairs, tie_key, order_key


def _tie_break(excerpts, page_type):
    """該頁來源片段 + 頁型的確定性決勝值;只依內容,不依候選順序。"""
    key = squash(" ".join(excerpts)) + "|" + page_type
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")


def _list_envelope(contract):
    """頂層必填清單的數量包絡,給漏提名錯誤訊息用(例:criteria 4–6)。"""
    tops = [s for s in contract_list_specs(contract)
            if s["parent"] is None and s["required"]]
    if not tops:
        return "無清單結構"
    return "、".join(f"{s['path']} {s['min']}–{s['max']}" for s in tops)


def check_library_review(plan, contracts, pack):
    """整庫覆蓋審視:每個非結構全自動頁型,必須被提名過或列入 not_nominated
    附語意理由。候選廣度從此是工具稽核的不變式,不靠模型自律。"""
    universe = {pt for pt, e in pack.page_types.items()
                if e.get("mode") == "fill" and pt not in STRUCTURAL_PAGES
                and pt in contracts}
    nominated = set()
    for slide in plan.get("slides") or []:
        if isinstance(slide, dict):
            for cand in slide.get("candidates") or []:
                if isinstance(cand, dict) and isinstance(cand.get("page_type"), str):
                    nominated.add(cand["page_type"])
    raw = plan.get("not_nominated")
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        raise ValueError("not_nominated 必須是清單")
    covered = {}
    for i, ent in enumerate(raw, 1):
        if (not isinstance(ent, dict) or not isinstance(ent.get("page_type"), str)
                or not isinstance(ent.get("reason"), str) or not ent["reason"].strip()):
            raise ValueError(
                f"not_nominated[{i}] 必須是 {{page_type, reason}},reason 不可空白")
        pat = ent["page_type"]
        if pat.endswith("_*"):
            hits = {pt for pt in universe if pt.startswith(pat[:-1])}
            if not hits:
                raise ValueError(f"not_nominated[{i}] 字首 {pat} 沒有對應任何全自動頁型")
            # 萬用字元只涵蓋未提名者:提名了 info_x 仍可用 info_* 說明其餘同族
            hits -= nominated
        else:
            if pat not in universe:
                raise ValueError(
                    f"not_nominated[{i}] {pat} 不是本包非結構全自動頁型(全集見 --list)")
            if pat in nominated:
                raise ValueError(
                    f"not_nominated[{i}] {pat} 已被提名,不可同時列為未提名")
            hits = {pat}
        for pt in hits:
            covered.setdefault(pt, ent["reason"].strip())
    missing = sorted(universe - nominated - set(covered))
    if missing:
        lines = [f"  {pt}({_list_envelope(contracts[pt])})" for pt in missing]
        raise ValueError(
            "整庫覆蓋審視不完整,以下全自動頁型未提名也未給理由:\n"
            + "\n".join(lines)
            + "\n  → 語意合適就加入該頁 candidates;不合適就在頂層 not_nominated"
              " 補 {page_type, reason}(同族可用「字首_*」一筆涵蓋)")
    review = {
        "nominated": sorted(nominated & universe),
        "not_nominated": [{"page_type": pt, "reason": covered[pt]}
                          for pt in sorted(covered)],
    }
    return review


def select_page_type_plan(plan, contracts, pack, source_text):
    """驗契約後在同等語意候選中做確定性全局選型。"""
    if not isinstance(plan, dict):
        raise ValueError(f"page type plan.version 必須是 {PLAN_VERSION}")
    if plan.get("version") == 1:
        raise ValueError(
            "plan version 2 起需要頂層 not_nominated 整庫覆蓋審視:"
            "未提名的全自動頁型逐一給語意不合理由(同族可用「字首_*」),"
            "補齊後把 version 改為 2")
    if plan.get("version") != PLAN_VERSION:
        raise ValueError(f"page type plan.version 必須是 {PLAN_VERSION}")
    slides = plan.get("slides")
    if not isinstance(slides, list) or not slides:
        raise ValueError("page type plan.slides 必須是非空清單")
    library_review = check_library_review(plan, contracts, pack)
    source_squashed = squash(source_text)
    choices_by_slide = []
    excerpts_by_slide = []
    breadth_by_slide = []
    warnings = []

    for number, slide in enumerate(slides, 1):
        if not isinstance(slide, dict):
            raise ValueError(f"plan slide[{number}] 必須是物件")
        candidates = slide.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise ValueError(f"plan slide[{number}].candidates 必須是非空清單")
        try:
            excerpts = _source_excerpts(slide)
        except ValueError as e:
            raise ValueError(f"plan slide[{number}]:{e}") from e
        all_closing = all(isinstance(c, dict) and c.get("page_type") == "closing"
                          for c in candidates)
        if not excerpts and not all_closing:
            raise ValueError(f"plan slide[{number}] 缺 source_excerpt(不可先寫內容再補來源)")
        for excerpt in excerpts:
            if squash(excerpt) not in source_squashed:
                preview = squash(excerpt)
                if len(preview) > 30:
                    preview = preview[:30] + "…"
                raise ValueError(
                    f"plan slide[{number}] source_excerpt 不是原文逐字片段:「{preview}」")
        excerpts_by_slide.append(excerpts)

        feasible = []
        seen = set()
        for order, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                warnings.append(f"slide[{number}] 候選 {order + 1} 排除:必須是物件")
                continue
            pt = candidate.get("page_type")
            fit = candidate.get("fit")
            requested = candidate.get("requested_by_user", False)
            reasons = []
            if not isinstance(pt, str) or not pt:
                reasons.append("缺 page_type")
            elif pt in seen:
                reasons.append("同頁候選 page_type 重複")
            else:
                seen.add(pt)
            if fit not in FIT_RANK:
                reasons.append("fit 必須是 exact 或 acceptable")
            if not isinstance(requested, bool):
                reasons.append("requested_by_user 必須是布林值")
            if pt not in contracts:
                reasons.append("不是已註冊頁型")
            pack_entry = pack.page_types.get(pt) if pt else None
            if pack_entry is None or pack_entry.get("mode") != "fill":
                reasons.append(f"不是模板包 {pack.id} 的全自動頁型")
            if pt in contracts:
                reasons.extend(validate_candidate_counts(pt, candidate, contracts[pt]))
            if reasons:
                warnings.append(
                    f"slide[{number}] 候選 {pt or order + 1} 排除:" + ";".join(reasons))
                continue
            ent = dict(candidate)
            ent["_order"] = order
            ent["_fit_rank"] = FIT_RANK[fit]
            ent["_layout"] = pack_entry.get("template_page", pt)
            ent["_tie"] = _tie_break(excerpts, pt)
            feasible.append(ent)

        if not feasible:
            details = [w for w in warnings if w.startswith(f"slide[{number}] ")]
            raise ValueError(
                f"plan slide[{number}] 沒有任何契約可行的全自動候選"
                + ("\n  " + "\n  ".join(details) if details else ""))
        best_fit = min(c["_fit_rank"] for c in feasible)
        feasible = [c for c in feasible if c["_fit_rank"] == best_fit]
        choices_by_slide.append(feasible)
        breadth_by_slide.append((len(candidates), len(feasible)))

    # 同等語意候選才進多樣性最佳化。beam 固定排序、無隨機。
    states = [[]]
    for choices in choices_by_slide:
        expanded = [seq + [choice] for seq in states for choice in choices]
        expanded.sort(key=_composition_cost)
        states = expanded[:BEAM_WIDTH]
    selected = min(states, key=_composition_cost)

    selected_slides = []
    for number, (choice, excerpts) in enumerate(zip(selected, excerpts_by_slide), 1):
        selected_slides.append({
            "number": number,
            "source_excerpt": excerpts,
            "page_type": choice["page_type"],
            "fit": choice["fit"],
            "counts": choice.get("counts", {}),
        })
        if choice.get("requested_by_user"):
            selected_slides[-1]["requested_by_user"] = True
    content_types = [s["page_type"] for s in selected_slides
                     if s["page_type"] not in STRUCTURAL_PAGES]
    content_breadth = [b for s, b in zip(selected_slides, breadth_by_slide)
                       if s["page_type"] not in STRUCTURAL_PAGES]
    single_nominated = sum(1 for nom, _ in content_breadth if nom == 1)
    single_equal_fit = sum(1 for _, eq in content_breadth if eq == 1)
    if len(content_breadth) >= 2 and single_nominated * 2 > len(content_breadth):
        warnings.append(
            f"候選池過窄:{single_nominated}/{len(content_breadth)} 個內容頁只提名"
            "一個候選,多樣性無從決勝——請回頭為語意同等的頁補提候選")
    composition = {
        "content_slide_count": len(content_types),
        "unique_page_types": len(set(content_types)),
        "page_type_usage": dict(Counter(content_types)),
        "adjacent_repeats": _composition_cost(selected)[0],
        "content_slides_single_candidate": single_nominated,
        "content_slides_single_equal_fit": single_equal_fit,
    }
    output = {
        "version": PLAN_VERSION,
        "deck": {"template": pack.id},
        "slides": selected_slides,
        "library_review": library_review,
        "composition": composition,
    }
    return output, warnings


def write_slides_md(selected_plan, path):
    blocks = []
    for slide in selected_plan["slides"]:
        excerpts = slide.get("source_excerpt") or []
        if not excerpts and slide["page_type"] == "closing":
            excerpts = ["Thank you"]
        blocks.append(f"## Slide {slide['number']}\n" + "\n".join(excerpts))
    Path(path).write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--types", help="逗號分隔的頁型清單,依簡報頁序")
    ap.add_argument("--plan", help="契約先行候選規劃 JSON(大綱模式)")
    ap.add_argument("--source", help="原始大綱檔(--plan 必填,逐字驗證 source_excerpt)")
    ap.add_argument("--selected-plan-out", help="寫出確定性選型結果 page_type_plan.json")
    ap.add_argument("--slides-out", help="依選型結果與 source_excerpt 寫出 slides.md")
    ap.add_argument("--out", help="輸出路徑(不給就印到 stdout)")
    ap.add_argument("--list", action="store_true", help="列出頁型(有模板包時按包列三級支援)")
    ap.add_argument("--describe", help="逗號分隔頁型,印選定模板包 merged 契約(JSON)")
    ap.add_argument("--template-pack", help="模板包 id 或目錄(省略=light)")
    ap.add_argument("--packs-root", help="模板包根目錄(預設=tools 上層的 templates/)")
    args = ap.parse_args(argv)
    if args.types and args.plan:
        print("✗ --types 與 --plan 只能擇一")
        return 2
    if args.plan and not args.source:
        print("✗ --plan 必須同時提供 --source,不可關閉來源逐字驗證")
        return 2

    raw_plan = None
    plan_template = None
    if args.plan:
        try:
            raw_plan = json.loads(Path(args.plan).read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"✗ page type plan 讀取失敗:{e}")
            return 2
        if not isinstance(raw_plan, dict) or not isinstance(raw_plan.get("deck", {}), dict):
            print("✗ page type plan 根節點與 deck 必須是物件")
            return 2
        plan_template = (raw_plan.get("deck") or {}).get("template")

    # 模板包解析(解不到且未明確指定 → 退回內建 light 預設,不加 deck.template)
    pack = None
    if pack_loader is not None:
        try:
            pack = pack_loader.load_pack(pack_arg=args.template_pack or plan_template,
                                         packs_root=args.packs_root,
                                         load_bindings=False)
        except pack_loader.PackError as e:
            if args.template_pack or plan_template:
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

    if args.describe:
        names = [n.strip() for n in args.describe.split(",") if n.strip()]
        unknown = [n for n in names if n not in contracts]
        if unknown:
            print("✗ 找不到已註冊頁型:" + ", ".join(unknown))
            return 2
        payload = {
            "template": pack.id if pack is not None else "light",
            "page_types": {},
        }
        for name in names:
            ent = (pack.page_types.get(name, {}) if pack is not None else {})
            payload["page_types"][name] = {
                "mode": ent.get("mode", "fill"),
                "template_page": ent.get("template_page"),
                "contract": contracts[name],
            }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.list or (not args.types and not args.plan):
        if pack is not None:
            print(f"模板包 {pack.id}@{pack.version} 的頁型支援:")
            auto = [pt for pt, md in modes.items() if md == "fill"]
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

    selected_plan = None
    if raw_plan is not None:
        if pack is None:
            print("✗ --plan 需要可載入的模板包(才能判定全自動支援與實際容量)")
            return 2
        if plan_template and plan_template != pack.id:
            print(f"✗ plan 指定模板 {plan_template!r},實際載入 {pack.id!r}")
            return 2
        try:
            source_text = Path(args.source).read_text(encoding="utf-8-sig")
            selected_plan, warnings = select_page_type_plan(
                raw_plan, contracts, pack, source_text)
        except (OSError, ValueError) as e:
            print(f"✗ 契約先行選型失敗:{e}")
            return 1
        for warning in warnings:
            print(f"[W] {warning}")
        types = [s["page_type"] for s in selected_plan["slides"]]
        comp = selected_plan["composition"]
        print("選型結果:" + " → ".join(types))
        print(f"內容頁:{comp['content_slide_count']}；"
              f"使用頁型:{comp['unique_page_types']}；"
              f"相鄰重複:{comp['adjacent_repeats']}；"
              f"單一候選內容頁:{comp['content_slides_single_candidate']}")
        if args.selected_plan_out:
            Path(args.selected_plan_out).write_text(
                json.dumps(selected_plan, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"選型計畫已寫入 {args.selected_plan_out}")
        if args.slides_out:
            write_slides_md(selected_plan, args.slides_out)
            print(f"來源映射已寫入 {args.slides_out}")
    elif args.types:
        types = [t.strip() for t in args.types.split(",") if t.strip()]
    else:
        ap.print_help()
        return 2

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
    count_plans = ([s.get("counts", {}) for s in selected_plan["slides"]]
                   if selected_plan else [{} for _ in types])
    spec = {
        "deck": deck,
        "slides": [
            build_slide(i + 1, t, contracts, bg, default_bg, logo, asset_keys,
                        count_plans[i])
            for i, t in enumerate(types)
        ],
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
