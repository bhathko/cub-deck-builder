#!/usr/bin/env python3
"""fills_engine — 宣告式 bindings.json 解譯器(docs/ARCHITECTURE.md §5)。

新模板的填充綁定一律是固定 op 詞彙表的 JSON,由本引擎逐 op 執行;
註冊時 LLM 只產 JSON、不產 Python。詞彙表(6 個填充 op + keep 覆蓋宣告)
自 light fills 全部特例歸納;**表達不了 = 該頁型降級 clone**,
詞彙表擴充是引擎版本事件(改本檔 + 對全部已註冊包跑回歸),
不得在註冊對話中發生。

bindings.json 結構:
{
  "engine": 1,
  "fills": {
    "<page_type>": {"template_page": N, "ops": [ <op>, ... ]},
    ...
  }
}

op 詞彙(欄位細節見各 _op_* docstring 與 docs/ARCHITECTURE.md §5 表):
  set / delete / keep / rows / list / add_textbox / resize / chart

槽位路徑:"$.title"、"$.slots.a.b"、支援索引 "[0]" 與切片 "[2:]";
list op 的項目內用 "@"(元素本身)與 "@.field"(元素欄位)。

詞彙表版本紀事(擴充=引擎版本事件,對全部已註冊包跑回歸後才發):
  v1.1(2026-07-25,Phase 4):+`chart` op(圖表數據替換;WORKLOG §8 第二級)
  與 set 的 `delete_if_missing` 修飾詞(選填槽位缺值時刪框)。
"""
from __future__ import annotations

from pptx.chart.data import CategoryChartData
from pptx.util import Inches

import fill_helpers

_MISSING = object()

OPS = ("set", "delete", "keep", "rows", "list", "add_textbox", "resize", "chart")


def resolve_path(spec_slide, path):
    """解析 "$.xxx[i][a:b]" 槽位路徑;不存在回 _MISSING。"""
    if not path.startswith("$."):
        raise fill_helpers.FillError(f"槽位路徑必須以 $. 開頭:{path!r}")
    cur = spec_slide
    for raw in path[2:].split("."):
        name, subs = raw, []
        while name.endswith("]"):
            name, _, sub = name.rpartition("[")
            subs.insert(0, sub[:-1])
        if name:
            if not isinstance(cur, dict) or name not in cur:
                return _MISSING
            cur = cur[name]
        for sub in subs:
            if ":" in sub:
                a, _, b = sub.partition(":")
                if not isinstance(cur, list):
                    return _MISSING
                cur = cur[int(a) if a else None:int(b) if b else None]
            else:
                if not isinstance(cur, list) or int(sub) >= len(cur):
                    return _MISSING
                cur = cur[int(sub)]
    return cur


def _render_value(value, mod, where):
    """依修飾詞把槽位值轉成字串:template(dict 格式化)/ join(list 併接)。"""
    if "template" in mod:
        if not isinstance(value, dict):
            raise fill_helpers.FillError(f"{where}: template 修飾詞需要物件槽位")
        return mod["template"].format(**value)
    if isinstance(value, list):
        return mod.get("join", "\n").join(str(x) for x in value)
    return str(value)


def _item_value(item, slot, where):
    """list 項目內取值:"@" = 元素本身;"@.field" = 元素欄位。"""
    if slot == "@":
        return item
    if slot.startswith("@."):
        key = slot[2:]
        if not isinstance(item, dict) or key not in item:
            return _MISSING
        return item[key]
    raise fill_helpers.FillError(f"{where}: list 項目槽位必須以 @ 開頭:{slot!r}")


def _apply_set(ctx, sid, value, mod, where):
    if value is _MISSING:
        raise fill_helpers.FillError(f"{where}: 槽位缺值(id={sid})")
    text = _render_value(value, mod, where)
    limit = mod.get("max_len_or_delete")
    if limit is not None and len(text) > limit:
        ctx.delete(sid)  # 放不下的小框整框刪除(如金字塔帶上標籤)
    else:
        ctx.set(sid, text)


def _op_set(ctx, spec_slide, op, style, where):
    value = resolve_path(spec_slide, op["slot"])
    if value is _MISSING and op.get("delete_if_missing"):
        ctx.delete(op["id"])  # 選填槽位缺值 → 整框刪除(不留佔位)
        return
    _apply_set(ctx, op["id"], value, op, where)


def _op_delete(ctx, spec_slide, op, style, where):
    ctx.delete(*op["ids"])


def _op_keep(ctx, spec_slide, op, style, where):
    pass  # 覆蓋宣告:明示保留的結構性字樣,lint 用,執行期無動作


def _op_rows(ctx, spec_slide, op, style, where):
    values = resolve_path(spec_slide, op["slot"])
    if values is _MISSING:
        raise fill_helpers.FillError(f"{where}: 槽位缺值 {op['slot']!r}")
    fill_helpers.fill_rows(ctx, [str(v) for v in values], op["row_ids"],
                           op.get("sep_ids", []),
                           merge_height_in=op.get("merge_height_in", 0.80))


def _op_resize(ctx, spec_slide, op, style, where):
    shp = ctx.shape(op["id"])
    for attr in ("left", "top", "width", "height"):
        if attr in op:
            setattr(shp, attr, Inches(op[attr]))


def _op_list(ctx, spec_slide, op, style, where):
    values = resolve_path(spec_slide, op["slot"])
    values = [] if values is _MISSING or values is None else list(values)
    defs = op["items"]
    n = min(len(values), len(defs))
    if op.get("align") == "tail":  # 尾端對齊:項目少時從「頭」刪(金字塔刪頂層)
        active, missing = defs[len(defs) - n:], defs[:len(defs) - n]
    else:
        active, missing = defs[:n], defs[n:]
    extra = values[len(active):]
    overflow = op.get("overflow")
    if extra and not overflow:
        raise fill_helpers.FillError(f"{where}: 項目數 {len(values)} 超出格位且無 overflow 宣告")

    for i, (d, v) in enumerate(zip(active, values)):
        for s in d.get("sets", []):
            _apply_set(ctx, s["id"], _item_value(v, s["slot"], where), s, where)
        last_with_overflow = overflow and extra and i == len(active) - 1
        for did in d.get("delete_always", []):
            if last_with_overflow and did == overflow["merge_into_id"]:
                continue  # 溢出承接框不刪,改收合併文字
            ctx.delete(did)
    if extra:
        ctx.set(overflow["merge_into_id"],
                overflow.get("join", "\n").join(str(x) for x in extra))
    for d in missing:
        ctx.delete(*d.get("delete_on_missing", []))
    if not values and op.get("delete_when_empty"):
        ctx.delete(*op["delete_when_empty"])


def _op_add_textbox(ctx, spec_slide, op, style, where):
    parts = []
    for sp in op["slots"]:
        v = resolve_path(spec_slide, sp)
        if v is _MISSING or v in (None, "", []):
            continue
        parts.extend(str(x) for x in v) if isinstance(v, list) else parts.append(str(v))
    if not parts:
        if op.get("skip_if_empty"):
            return
        raise fill_helpers.FillError(f"{where}: add_textbox 槽位全空且未宣告 skip_if_empty")
    text = op.get("prefix", "") + op.get("join", "、").join(parts)
    fill_helpers.add_styled_textbox(ctx.slide, text, op["x"], op["y"], op["w"], op["h"],
                                    font=style.get("font_zh", "Microsoft JhengHei"),
                                    size_pt=op["pt"], bold=op.get("bold", False))


def _num(raw, where):
    """圖表數值:spec 以數字字串承載(維持 validator 數字追溯),此處嚴格轉數;
    不接受單位/百分號——% 屬 label/軸文字,值一律純數。"""
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise fill_helpers.FillError(f"{where}: 圖表數值必須是純數字字串,得到 {raw!r}")


def _op_chart(ctx, spec_slide, op, style, where):
    """圖表數據替換(chart.replace_data):categories + 1..N 系列。
    每系列 values 數必須等於 categories 數,否則 FillError(渲染前硬擋)。"""
    shp = ctx.shape(op["id"])
    if not getattr(shp, "has_chart", False):
        raise fill_helpers.FillError(f"{where}: shape id {op['id']} 不是圖表")
    cats = resolve_path(spec_slide, op["categories"])
    series = resolve_path(spec_slide, op["series"])
    if cats is _MISSING or series is _MISSING:
        raise fill_helpers.FillError(f"{where}: 圖表槽位缺值(categories/series)")
    data = CategoryChartData()
    data.categories = [str(c) for c in cats]
    for s in series:
        vals = s.get("values", [])
        if len(vals) != len(cats):
            raise fill_helpers.FillError(
                f"{where}: 系列「{s.get('name', '?')}」有 {len(vals)} 個值,"
                f"時間點有 {len(cats)} 個——兩者必須相等")
        data.add_series(str(s.get("name", "")), [_num(v, where) for v in vals])
    shp.chart.replace_data(data)


_HANDLERS = {"set": _op_set, "delete": _op_delete, "keep": _op_keep,
             "rows": _op_rows, "list": _op_list, "add_textbox": _op_add_textbox,
             "resize": _op_resize, "chart": _op_chart}


def run_ops(ctx, spec_slide, ops, style, page_type):
    for i, op in enumerate(ops):
        kind = op.get("op")
        if kind not in _HANDLERS:
            raise fill_helpers.FillError(
                f"{page_type} ops[{i}]: 未知 op {kind!r}(詞彙表固定,表達不了請降級 clone)")
        _HANDLERS[kind](ctx, spec_slide, op, style, f"{page_type} ops[{i}]")


def build_fills(bindings: dict, style: dict) -> dict:
    """把 bindings.json 轉成 pack_loader 的 FILLS 介面:pt → (模板頁, fill_fn)。"""
    if bindings.get("engine") != 1:
        raise fill_helpers.FillError(
            f"bindings.json engine 版本不符:{bindings.get('engine')!r}(本引擎=1)")
    fills = {}
    for pt, ent in bindings.get("fills", {}).items():
        page, ops = ent["template_page"], ent["ops"]

        def make(ops=ops, pt=pt):
            def fill(ctx, spec_slide):
                run_ops(ctx, spec_slide, ops, style, pt)
            return fill
        fills[pt] = (page, make())
    return fills
