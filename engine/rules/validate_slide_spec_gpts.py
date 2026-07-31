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
  - 容量壓縮豁免(2026-07-27 政策決定):與該值相關的來源句**全部**放不進
    版位上限、且值的用詞幾乎全出自來源時,低相似度不警告也不受 --strict
    升級——誠實容量下的摘要式改寫是被迫的,不是幻覺。數字與標題兩條硬線
    不經此路徑,完全不受豁免影響。判定見 capacity_compressed()。
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
CONTAINMENT_THRESHOLD = 0.90  # 容量壓縮豁免:值的內容字元至少九成須出自來源

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

# ---------------------------------------------------------------------------
# 模板包感知(多模板架構,見 docs/ARCHITECTURE.md;stdlib-only 維持單檔可攜)
# PAGE_TYPES = 語意契約 + 預設容量(= light 現值);各包 manifest 的
# capacity_overrides 只能覆寫 min/max/max_chars,不得增刪槽位或改 kind。
# ---------------------------------------------------------------------------
import copy as _copy

_CAP_KEYS = {"min", "max", "max_chars"}


def apply_capacity_overrides(base: dict, overrides: dict) -> dict:
    """依扁平 dot-path 覆寫容量;結構性違規 raise ValueError(設定檔錯誤)。"""
    merged = _copy.deepcopy(base)
    for path, value in (overrides or {}).items():
        segs = path.split(".")
        if len(segs) < 3 or segs[-1] not in _CAP_KEYS:
            raise ValueError(f"capacity_overrides 路徑不合法(終端鍵限 {sorted(_CAP_KEYS)}):{path}")
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"capacity_overrides 值必須是正整數:{path}={value!r}")
        cur = merged
        for seg in segs[:-1]:
            if isinstance(cur, dict) and seg in cur:
                cur = cur[seg]
            elif isinstance(cur, dict) and cur.get("kind") == "object" and seg in cur.get("fields", {}):
                cur = cur["fields"][seg]
            else:
                raise ValueError(f"capacity_overrides 路徑不存在於語意契約:{path}(斷在 {seg!r})")
        key = segs[-1]
        if key not in cur:
            raise ValueError(f"capacity_overrides 目標槽位無 {key!r} 可覆寫:{path}")
        cur[key] = value
        if cur.get("kind") == "list" and cur["min"] > cur["max"]:
            raise ValueError(f"capacity_overrides 造成 min>max:{path}")
    return merged


def load_pack_context(packs_root: Path, template_id: str | None, allow_draft=False):
    """讀選定包 manifest,回傳 pack context dict;找不到回 None。

    context 鍵:id/version/dir/modes(page_type→mode)/auto(fill 集合)/
    reasons(unsupported 理由)/pack_first(素材解析順序)/page_types(merged 契約)。
    manifest 壞掉或覆寫違規 raise ValueError(前置錯誤,exit 2)。
    allow_draft 僅供註冊 harness(template_admin golden)使用。
    """
    target = template_id or "light"
    mpath = packs_root / target / "manifest.json"
    if not mpath.exists():
        return None
    manifest = json.loads(mpath.read_text(encoding="utf-8-sig"))
    if manifest.get("status") == "draft" and not allow_draft:
        raise ValueError(f"模板包 {target} 仍為 draft(註冊未完成),不得用於產檔")
    entries = manifest.get("page_types", {})
    modes = {pt: e.get("mode") for pt, e in entries.items()}
    return {
        "id": manifest.get("template_id", target),
        "version": manifest.get("version", "?"),
        "dir": mpath.parent,
        "modes": modes,
        "auto": {pt for pt, m in modes.items() if m == "fill"},
        "reasons": {pt: e.get("reason", "") for pt, e in entries.items()
                    if e.get("mode") == "unsupported"},
        "asset_keys": {pt: e.get("assets") for pt, e in entries.items()},
        "pack_first": manifest.get("asset_resolution", "pack_first") == "pack_first",
        "page_types": apply_capacity_overrides(PAGE_TYPES, manifest.get("capacity_overrides")),
    }


def asset_exists(rel: str, asset_base: Path, pack) -> bool:
    """素材存在性:asset_base 與包目錄二擇一命中(順序依包宣告;無包=僅 asset_base)。"""
    cands = [asset_base / rel]
    if pack:
        pc = pack["dir"] / rel
        cands = [pc, asset_base / rel] if pack["pack_first"] else [asset_base / rel, pc]
    return any(c.exists() for c in cands)

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
    "section_transition": {
        "page_number": "none",
        "assets": [],
        "slots": {
            # 結構頁例外(同 cover):版面主標框窄,需由 fit 量測槽位容量。
            # 頂層 title 仍是頁面語意標題；可保留較完整章節名稱。
            "main_title": T(20),
            "subtitle": T(40),
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
    "info_sidebar_grid": {
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "hashtags": {
                "kind": "list", "min": 3, "max": 4, "required": True,
                "item": {"kind": "object", "fields": {"label": T(12)}},
            },
            "topic": T(40),
            "paired_categories": {
                "kind": "list", "min": 2, "max": 2, "required": True,
                "item": {"kind": "object", "fields": {
                    "label": T(20),
                    "cards": {
                        "kind": "list", "min": 2, "max": 2, "required": True,
                        "item": {"kind": "object", "fields": {
                            "heading": T(20),
                            "detail": T(60),
                        }},
                    },
                }},
            },
            "flex_category": {"kind": "object", "fields": {
                "label": T(20),
                "cards": {
                    "kind": "list", "min": 1, "max": 3, "required": True,
                    "item": {"kind": "object", "fields": {
                        "heading": T(20),
                        "detail": T(60),
                    }},
                },
            }},
            "full_width_category": {"kind": "object", "fields": {
                "label": T(20),
                "card": {"kind": "object", "fields": {
                    "heading": T(20),
                    "detail": T(60),
                }},
            }},
        },
    },
    "data_line_trend_comparison": {
        # 折線趨勢比較(模板 p25):chart 數據由 fills_engine chart op 替換。
        # values 是「數字字串」(純數,禁單位/%——% 屬 label),故數字追溯照常;
        # 每系列 values 數必須等於 categories 數(渲染前 chart op 硬擋)。
        # 版面無副標位置 → 本頁型無 subtitle 槽位。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "categories": {"kind": "list", "min": 6, "max": 10, "required": True, "item": T(8)},
            "series": {
                "kind": "list", "min": 1, "max": 2, "required": True,
                "item": {"kind": "object", "fields": {
                    "name": T(8),
                    "values": {"kind": "list", "min": 6, "max": 10, "required": True, "item": T(8)},
                }},
            },
            "rows": {
                "kind": "list", "min": 2, "max": 3, "required": True,
                "item": {"kind": "object", "fields": {
                    "heading": T(8),
                    "cells": {"kind": "list", "min": 3, "max": 5, "required": True, "item": T(20)},
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
    "evaluation_vs_criteria_matrix": {
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "left_name": T(24),
            "right_name": T(24),
            "criteria": {
                "kind": "list", "min": 4, "max": 6, "required": True,
                "item": {"kind": "object", "fields": {
                    "label": T(16),
                    "left": T(60),
                    "right": T(60),
                }},
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
            # 這一列是「建議:A、B、C」的單行摘要,和 recommended 共用一個
                # add_textbox 框(總長度受限)。項目多 → 每項字數就被壓到
                # 寫不出完整句子(5 項時只剩 7 字)。3 項是語意上的合理上限,
                # 屬契約決定而非模板容量,所以寫在這裡而不是 capacity_overrides
                # (後者會被 fit --reset 重新推導)。
                "recommendation": {"kind": "list", "min": 0, "max": 3, "required": False, "item": T(40)},
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
    "data_three_number_kpis": {
        # 三大數字 KPI(模板 p30):中央橫向 3 組「大數字 + 短標題 + 1-2 行說明」,
        # 內容容量 2-3 個(page_types.md);只有 2 個時第 3 組整組刪除,不留空位。
        # subtitle 為選填:內容容量未列副標,但版面上方有副標框——缺值時由 bindings
        # 的 set.delete_if_missing 整框刪掉,不留佔位字。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60, required=False),
            "kpis": {
                "kind": "list", "min": 2, "max": 3, "required": True,
                "item": {"kind": "object", "fields": {
                    "value": T(6),      # 66pt 大數字框(w=1.33~1.76 吋),含單位/%
                    "label": T(12),     # 數字下方短標題(w=1.72 吋,單行)
                    "detail": T(30),    # 補充說明(w=2.56 吋 × 2 行 @14pt)
                }},
            },
        },
    },
    "info_horizontal_explanation_rows": {
        # 橫向說明列(模板 p22):上方淡綠主題帶 = subtitle;內容區 5 組
        # 「短標籤框 + 長說明框」橫列(label 框 w=2.78in、說明框 w=9.11in/14pt)。
        # 版面左側直排類別標示與右上子導覽為模板佔位字樣,契約無對應槽位 → 綁定端一律 delete。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "rows": {
                "kind": "list", "min": 4, "max": 5, "required": True,
                "item": {"kind": "object", "fields": {
                    "label": T(12),
                    "points": {"kind": "list", "min": 1, "max": 3, "required": True, "item": T(40)},
                }},
            },
        },
    },
    "cycle_four_point_loop": {
        # 四點循環(light p35):中央大型綠色循環箭頭 + 左右各 2 組步驟。
        # 容量依 page_types.md「內容容量」:副標 1 句、中央循環主題 1 個、
        # 步驟固定 4 組(編號 + 步驟名稱 + 1-2 句說明)。只有 3 步請改用
        # cycle_three_node_process(本頁型不接受 3 步,min=max=4)。
        # 中央圓內模板另有「副標文字 / 重點文字」兩個示範框,契約無對應槽位,
        # 綁定一律 delete(留著=捏造)。步驟名稱建議 4-8 字(循環頁型共通規則)。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "center_theme": T(10),
            "steps": {
                "kind": "list", "min": 4, "max": 4, "required": True,
                "item": {"kind": "object", "fields": {
                    # 模板 p35 的編號徽章只有 0.34 吋寬(原文是單一粗體數字 𝟭𝟮𝟯𝟰),
                    # 放兩位數會折成兩行破版 → 上限 1 字,不是 "01" 這種補零寫法。
                    "number": T(1, provenance=False),  # 循環序號,結構性標籤
                    "label": T(12),
                    "detail": T(40),
                }},
            },
        },
    },
    "phase_three_column_action_cards": {
        # 三欄行動卡(模板 p50):3 欄卡片,每欄 = 箭頭階段標題 + 上半列點
        # + 中間重點句(選填)+ 下半段落說明;左側兩個小方塊是「內容層級標籤」
        # (上=列點區、下=段落區),屬結構字樣故 provenance=False。
        # 版面標題下方到箭頭列僅 0.32 吋,page_types.md 容量亦無副標 → 本頁型無 subtitle 槽位。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "points_label": T(6, provenance=False),
            "detail_label": T(6, provenance=False),
            "phases": {
                "kind": "list", "min": 3, "max": 3, "required": True,
                "item": {"kind": "object", "fields": {
                    "heading": T(12),
                    "points": {"kind": "list", "min": 3, "max": 5, "required": True, "item": T(16)},
                    "highlight": T(16, required=False),
                    "detail": T(60),
                }},
            },
        },
    },
    "stage_year_cards": {
        # 年度策略卡(模板 p40):上方年度線 3 個節點 + 下方 3 欄卡片,
        # 每欄 = 深色重點區塊(highlights)+ 白色細項區塊(details);中欄有綠框強調
        # (強調位置烙在模板上,不開槽位)。版面標題下方直接是年度線,
        # **無副標位置 → 本頁型無 subtitle 槽位**(同 data_line_trend_comparison)。
        # 左側兩個列標籤框(id 42/43)在模板上是「標題」佔位字,page_types.md
        # 的內容容量未列此欄 → 綁定一律 delete(留著=捏造)。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "stages": {
                "kind": "list", "min": 3, "max": 3, "required": True,
                "item": {"kind": "object", "fields": {
                    "label": T(8),
                    "heading": T(16),
                    "highlights": {"kind": "list", "min": 2, "max": 4, "required": True, "item": T(20)},
                    "details": {"kind": "list", "min": 3, "max": 5, "required": True, "item": T(30)},
                }},
            },
        },
    },
    "info_card_grid": {
        # 卡片網格(light p20):2 列 × 4 欄共 8 格,每格 = 小標 + 1–3 條短說明。
        # 容量取自 page_types.md:卡片 6–8 張、每張「1 個小標 + 1-2 句說明或 2-3 個短列點」。
        # 字數上限由模板框反推(綁定端另有 resize 校正框寬/框高):
        #   heading 框 wrap="none" 單行不換行,加寬到 2.75 吋 / 18pt → 一行約 10 字;
        #   內文框 2.75 吋 / 14pt → 一行約 13 字、框高 4 行,points 以換行併入同一框,
        #   故每條 ≤12 字 × 至多 3 條(= 3 行)才保證不溢出卡片。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "cards": {
                "kind": "list", "min": 6, "max": 8, "required": True,
                "item": {"kind": "object", "fields": {
                    "heading": T(10),
                    "points": {"kind": "list", "min": 1, "max": 3, "required": True,
                               "item": T(12)},
                }},
            },
        },
    },
    "stage_timeline_progress": {
        # 單線時間軸(模板 p38):底部 4 個刻度膠囊 + 3 個里程碑(2 個在軸上、
        # 1 個在軸下)+ 右側「進行中 / 後續規劃」說明區。右側區塊的欄目標籤
        # 「進行中 / 後續規劃」由模板固定提供(keep),不佔槽位。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "axis_labels": {"kind": "list", "min": 4, "max": 4, "required": True, "item": T(8)},
            "milestones": {
                "kind": "list", "min": 3, "max": 3, "required": True,
                "item": {"kind": "object", "fields": {"label": T(8), "detail": T(40)}},
            },
            "current_status": {"kind": "object", "fields": {
                "heading": T(12),
                "points": {"kind": "list", "min": 1, "max": 2, "required": True, "item": T(60)},
            }},
        },
    },
    "info_before_after_item_compare": {
        # 前後/兩方案項目對照(light 模板 p24):左右各一塊圓角底板,每側 3 張
        # 項目卡(名稱徽章 + 短列點),中央箭頭示轉換。
        # 版面標題下方直接是兩區塊,**無副標位置** → 本頁型無 subtitle 槽位。
        # 左右項目固定各 3 項(page_types.md「左右各 3 個項目」+「數量應一致」,
        # 用固定長度在契約層強制對稱,驗證器無法跨槽位比長度)。
        # 字數上限對照 p24 框寬(縮字下限 12pt):
        #   heading  框 1.32in @20pt → 6 字(7 字起溢出)
        #   name     框 1.66×1.22in @18pt → 12 字(3 行)
        #   points   右側說明框 3.37in @14pt → 一行 16 字;4 點 = 4 行剛好填滿
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "before": {"kind": "object", "fields": {
                "heading": T(6, provenance=False),  # 「導入前」等結構性對照標籤
                "items": {
                    "kind": "list", "min": 3, "max": 3, "required": True,
                    "item": {"kind": "object", "fields": {
                        "name": T(12),
                        "points": {"kind": "list", "min": 2, "max": 4,
                                   "required": True, "item": T(16)},
                    }},
                },
            }},
            "after": {"kind": "object", "fields": {
                "heading": T(6, provenance=False),
                "items": {
                    "kind": "list", "min": 3, "max": 3, "required": True,
                    "item": {"kind": "object", "fields": {
                        "name": T(12),
                        "points": {"kind": "list", "min": 2, "max": 4,
                                   "required": True, "item": T(16)},
                    }},
                },
            }},
        },
    },
    "vision_goal_keyword_orbit": {
        # 願景關鍵詞環繞(light 模板 p16):中央深色圓 + 左右兩側關鍵詞雲。
        # 容量取自 page_types.md:中心主題 1 個、周圍關鍵詞 8–12 個。
        # 版面實有 16 個關鍵詞框,超出契約上限的 4 個輔助框由綁定固定刪除;
        # keywords 依「左右交錯、由主到輔」順序填,不足時從尾端刪格位,維持左右平衡。
        # 中心圓只承載一句 center_theme(模板圓內範例說明與圓上方範例標題一律刪除,
        # 契約沒有的內容性元素留著=捏造)。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "center_theme": T(14),   # 圓內 w=3.52 吋 @28pt,一行約 8.5 字,兩行以內
            "keywords": {"kind": "list", "min": 8, "max": 12, "required": True,
                         "item": T(8)},   # 框 w=2.21–2.62 吋 @20–28pt,一行約 6 字
        },
    },
    "phase_concept_three_column_explanation": {
        # 概念三欄展開(模板 p47):左側大圓 = 核心概念 + 3 個關鍵標籤;右側三欄
        # 各 4 個實體格位。容量取自 page_types.md「內容容量」節;第二欄(3–5)與
        # 第三欄(4–6)超出 4 格的項目由 rows op 併入該欄最後一格。
        # 版面無副標位置(標題下方即三欄欄標)→ 本頁型無 subtitle 槽位。
        # 字數上限為實測值(text_tools.estimate_overflow,shrink 下限 12pt):
        # detail 24 / caption 6 / column_two 40 即爆框,故壓在 20 / 4 / 36。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "concept": T(8),
            "concept_labels": {
                "kind": "list", "min": 0, "max": 3, "required": False,
                "item": {"kind": "object", "fields": {"name": T(8), "caption": T(4)}},
            },
            "column_one": {"kind": "object", "fields": {
                "heading": T(10),
                "items": {
                    "kind": "list", "min": 3, "max": 4, "required": True,
                    "item": {"kind": "object", "fields": {"label": T(12), "detail": T(20)}},
                },
            }},
            "column_two": {"kind": "object", "fields": {
                "heading": T(10),
                "points": {"kind": "list", "min": 3, "max": 5, "required": True, "item": T(36)},
            }},
            "column_three": {"kind": "object", "fields": {
                "heading": T(10),
                "points": {"kind": "list", "min": 4, "max": 6, "required": True, "item": T(24)},
            }},
        },
    },
    "vision_goal_rings": {
        # 三層同心圓(light p12):右側三層同心圓,每層 = 圓上短標(28pt)+
        # 圓上補充(14pt);左側每層 = 小標(20pt)+ 說明(14pt),導引線相連。
        # 三層的左側說明框高度不同(0.57/0.81/0.34 吋 = 2/3/1 行 @14pt),
        # 容量不對稱 → 比照 phase_concept 用具名槽位(level_one=最外圈/最上,
        # 依序向內)。副標 placeholder = 引言一句;同心圓與導引線為模板裝飾。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "level_one": {"kind": "object", "fields": {
                "label": T(6), "caption": T(24), "heading": T(12), "detail": T(26),
            }},
            "level_two": {"kind": "object", "fields": {
                "label": T(6), "caption": T(24), "heading": T(12), "detail": T(40),
            }},
            "level_three": {"kind": "object", "fields": {
                "label": T(6), "caption": T(16), "heading": T(12), "detail": T(20),
            }},
        },
    },
    "stage_phase_swimlane": {
        # 三欄泳道(light p39):3 個階段欄,每欄上方工作項目卡(單一多行文字框
        # 2.54 吋 @14pt ≈ 9 行,列點換行併入)+ 下方角色卡(三欄一致 = 單框內
        # 換行;欄 2 模板多出的第 2 格與列點圓飾由綁定一律刪除,維持三欄同構)。
        # 左側直排「執行項目/角色」row 標籤為結構字樣(provenance=False)。
        # 階段標籤是單一文字框「階段名␣␣時間範圍」→ 契約用單一 label 承載
        # (拆成物件欄位會落入 fit 的物件清單量測盲點,見 REGRESSION R10 註)。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(60),
            "items_label": T(6, provenance=False),
            "roles_label": T(4, provenance=False),
            "phases": {
                "kind": "list", "min": 3, "max": 3, "required": True,
                "item": {"kind": "object", "fields": {
                    "label": T(18),
                    "points": {"kind": "list", "min": 3, "max": 6, "required": True, "item": T(17)},
                    "roles": {"kind": "list", "min": 1, "max": 2, "required": True, "item": T(17)},
                }},
            },
        },
    },
    "stage_horizon_matrix": {
        # 短中長期矩陣(light p42):3 時程欄 × 4 分類列 = 12 格卡片,每格
        # 1-3 個短列點(換行併入同格,3.94 吋 @14pt × 3 行);左側直排分類
        # 標籤、上方 3 個欄標。標題下方橫帶 = 補充指標 1-2 個(自由短句如
        # 「現況  Concurrent User  10,000」,數字照常追溯);缺第 2 個刪右框,
        # 全缺連分隔線一起刪。版面無副標位置 → 本頁型無 subtitle 槽位。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "indicators": {"kind": "list", "min": 1, "max": 2, "required": False, "item": T(24)},
            "column_headings": {"kind": "list", "min": 3, "max": 3, "required": True, "item": T(8)},
            "rows": {
                "kind": "list", "min": 4, "max": 4, "required": True,
                "item": {"kind": "object", "fields": {
                    "label": T(6),
                    "cells": {
                        "kind": "list", "min": 3, "max": 3, "required": True,
                        "item": {"kind": "object", "fields": {
                            "points": {"kind": "list", "min": 1, "max": 3, "required": True, "item": T(17)},
                        }},
                    },
                }},
            },
        },
    },
    "stage_vertical_timeline_detail": {
        # 垂直時間軸重點說明(light p45):左側 5-6 個階段(名稱+日期區間,
        # 第 6 階段缺項從尾端整組刪);右側大框 2 組重點段落(上組 1.85 吋
        # ≈ 6 行、下組 1.09 吋 ≈ 3 行,容量不對稱 → 具名 section_one/two),
        # 底部一條補充結論帶。模板在第 2 階段旁的進度圓點是「目前進度」語意,
        # 契約無此槽位 → 綁定一律刪除(留著=捏造進度)。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "stages": {
                "kind": "list", "min": 5, "max": 6, "required": True,
                "item": {"kind": "object", "fields": {"label": T(8), "period": T(17)}},
            },
            "section_one": {"kind": "object", "fields": {
                "heading": T(8),
                "points": {"kind": "list", "min": 3, "max": 6, "required": True, "item": T(30)},
            }},
            "section_two": {"kind": "object", "fields": {
                "heading": T(8),
                "points": {"kind": "list", "min": 2, "max": 4, "required": True, "item": T(30)},
            }},
            "footnote": T(30),
        },
    },
    "phase_four_step_workflow_matrix": {
        # 四階段工作流矩陣(light p49):上方 4 段箭頭階段列 + 左側 3 個直排
        # row 標籤 + 每列內容格。第 1 列欄 4 區域是模板的 Y/N 決策分支:
        # 2 條分支各「條件小框 → 結果框」,Y/N 徽章為固定結構字樣(keep),
        # 故 row_one 只有 3 格 + branches;第 2/3 列各 4 格。每格 1-3 個短列點
        # 換行併入同格。底部補充說明一句;左下「輔助說明」示範標籤框契約無
        # 槽位 → 刪除。版面無副標位置 → 本頁型無 subtitle 槽位。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "stages": {"kind": "list", "min": 4, "max": 4, "required": True, "item": T(8)},
            "row_labels": {"kind": "list", "min": 3, "max": 3, "required": True, "item": T(6)},
            "row_one": {"kind": "object", "fields": {
                "cells": {
                    "kind": "list", "min": 3, "max": 3, "required": True,
                    "item": {"kind": "object", "fields": {
                        "points": {"kind": "list", "min": 1, "max": 2, "required": True, "item": T(20)},
                    }},
                },
                "branches": {
                    "kind": "list", "min": 2, "max": 2, "required": True,
                    "item": {"kind": "object", "fields": {"condition": T(8), "outcome": T(16)}},
                },
            }},
            "row_two": {"kind": "object", "fields": {
                "cells": {
                    "kind": "list", "min": 4, "max": 4, "required": True,
                    "item": {"kind": "object", "fields": {
                        "points": {"kind": "list", "min": 1, "max": 3, "required": True, "item": T(20)},
                    }},
                },
            }},
            "row_three": {"kind": "object", "fields": {
                "cells": {
                    "kind": "list", "min": 4, "max": 4, "required": True,
                    "item": {"kind": "object", "fields": {
                        "points": {"kind": "list", "min": 1, "max": 3, "required": True, "item": T(20)},
                    }},
                },
            }},
            "footnote": T(24),
        },
    },
    "phase_step_ladder_cards": {
        # 階梯行動卡(light p52):左下→右上 4 張階梯卡,卡高遞增、內文框數
        # 遞增(卡 1 僅 1 框 2 行,卡 2 有 2 框,卡 3/4 各 3 框)——容量不對稱
        # → 比照 phase_concept 用具名 step_one..step_four。每卡:箭頭下標題
        # (20pt)+ 內文列點(rows op 逐框填,溢出併入末框)+ 底部一句重點
        # (14pt 短框,選填缺值刪框)。編號徽章 1-4 烙在模板上(keep,結構
        # 序號不佔槽位)。左上 20pt 示範標題框契約無槽位 → 刪除;16pt 框 = subtitle。
        "page_number": "required",
        "assets": ["background", "logo"],
        "slots": {
            "subtitle": T(40),
            "step_one": {"kind": "object", "fields": {
                "heading": T(12),
                "points": {"kind": "list", "min": 1, "max": 2, "required": True, "item": T(26)},
                "highlight": T(8, required=False),
            }},
            "step_two": {"kind": "object", "fields": {
                "heading": T(12),
                "points": {"kind": "list", "min": 2, "max": 3, "required": True, "item": T(26)},
                "highlight": T(8, required=False),
            }},
            "step_three": {"kind": "object", "fields": {
                "heading": T(12),
                "points": {"kind": "list", "min": 2, "max": 4, "required": True, "item": T(26)},
                "highlight": T(8, required=False),
            }},
            "step_four": {"kind": "object", "fields": {
                "heading": T(12),
                "points": {"kind": "list", "min": 2, "max": 4, "required": True, "item": T(26)},
                "highlight": T(8, required=False),
            }},
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


def capacity_compressed(checked: str, max_chars: int, block: str) -> bool:
    """容量壓縮豁免判定(2026-07-27 政策決定,脈絡見 docs/WORKLOG.md §2.4.1)。

    誠實容量(上限=版位實測)與 strict 相似度會在窄槽位對撞:來源句 22 字、
    版位只裝得下 17 字時,唯一合法輸出就是摘要式改寫,而 bigram 覆蓋率必然
    掉到門檻下——改短就不像、像了就超容量,三輪修正也繞不出去。

    豁免僅在「壓縮是被迫的」時成立,兩個條件缺一不可:
    1. 與此值共享詞彙(至少一個 bigram)的**每一個**來源句都放不進
       max_chars——只要存在裝得下的來源句,就該逐字引用,不豁免。
    2. 值的內容字元幾乎全部出自來源區塊(≥ CONTAINMENT_THRESHOLD)——
       壓縮是「刪字重排」,捏造是「加新詞」,後者照常警告/升級。
    """
    sents = [s for s in re.split(r"[。;;!?!?\n]+", block) if norm(s)]
    vg = bigrams(checked)
    related = [s for s in sents if vg & bigrams(s)]
    if not related:
        return False
    if any(len(norm(s)) <= max_chars for s in related):
        return False
    nv = norm(checked)
    nb = norm(block)
    return bool(nv) and sum(1 for ch in nv if ch in nb) / len(nv) >= CONTAINMENT_THRESHOLD


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

    def info(self, path, msg):
        """不受 --strict 升級的提示——用於容量壓縮豁免這類「已判定合法,
        但要留下能見度」的紀錄;塞進 warnings 只是共用輸出格式。"""
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
                    if capacity_compressed(checked, slot["max_chars"], block):
                        rep.info(path, f"容量壓縮豁免:相似度 {cov:.2f} 低於門檻,"
                                       f"但相關來源句均超過版位上限 {slot['max_chars']} 字"
                                       f"且用詞皆出自來源(被迫壓縮,不升級):「{val}」")
                    else:
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


def validate_slide(slide, block, asset_base: Path, rep: Report, registered_only: bool = False,
                   pack=None, page_types=None):
    num = slide.get("number", "?")
    p = f"slide[{num}]"
    pt = slide.get("page_type")
    contracts = page_types or PAGE_TYPES

    # 模板包三級閘門(docs/ARCHITECTURE.md §6):unsupported 硬擋;語意契約有、
    # 但該包非全自動 → WARN(--registered-only 升級 ERROR),契約檢查照跑。
    if pack:
        mode = pack["modes"].get(pt)
        if mode == "unsupported":
            reason = pack["reasons"].get(pt) or "未註冊"
            rep.error(p, f"頁型 {pt!r} 不受模板 {pack['id']!r} 支援({reason})。"
                         f"全自動頁型:{', '.join(sorted(pack['auto']))}。"
                         f"修法(擇一):換頁型/換 deck.template/回註冊流程補註冊。")
            return
        if pt in contracts and mode != "fill":
            if registered_only:
                rep.error(p, f"頁型 {pt!r} 在模板 {pack['id']!r} 非全自動"
                             f"(需 render_plan),一鍵模式不允許")
                return
            rep.warn(p, f"頁型 {pt!r} 在模板 {pack['id']!r} 非全自動:渲染需"
                        f" render_plan(參考頁見該包 page_map.md)")

    if pt not in contracts:
        if registered_only:
            rep.error(p, f"未知 page_type {pt!r}（未在 PAGE_TYPES 註冊）")
            return
        # 兩級閘門：未註冊頁型 → 泛用防幻覺檢查（槽位契約不受檢）
        rep.warn(p, f"page_type {pt!r} 未在 PAGE_TYPES 註冊：僅做防幻覺追溯，"
                    f"槽位數量/字數請自行比照 page_types.md 的「內容容量」")
        for key, rel in (slide.get("assets") or {}).items():
            if rel and not asset_exists(rel, asset_base, pack):
                rep.error(f"{p}.assets.{key}", f"素材檔不存在：{rel}（相對於 {asset_base}）")
        slots = slide.get("slots")
        if not isinstance(slots, dict):
            rep.error(p, "缺少 slots 物件")
            return
        generic_provenance(slots, f"{p}.slots", block, rep)
        return
    spec = contracts[pt]

    # 頁碼規則
    rule = spec["page_number"]
    expected = (rule == "required")
    if "render_page_number" in slide:
        if slide["render_page_number"] != expected:
            rep.error(p, f"render_page_number={slide['render_page_number']} 與版型 {pt} 規則不符（應為 {expected}）")
    else:
        rep.warn(p, f"未設 render_page_number（版型 {pt} 預期 {expected}）")

    # 素材(必要鍵集:包內 page_types.<pt>.assets 覆寫優先,無則契約預設;
    # fill 頁 clone 模板實頁、背景已烙,新包可宣告 [] 免素材)
    required_assets = spec["assets"]
    if pack and pack["asset_keys"].get(pt) is not None:
        required_assets = pack["asset_keys"][pt]
    assets = slide.get("assets", {})
    for key in required_assets:
        if key not in assets or not assets[key]:
            rep.error(f"{p}.assets", f"缺少必要素材 {key!r}")
            continue
        if not asset_exists(assets[key], asset_base, pack):
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
    allow_draft = "--allow-draft" in argv  # 僅註冊 harness(golden)使用
    spec_path, slides_path, asset_base = DEFAULT_SPEC, DEFAULT_SLIDES, DEFAULT_ASSET_DIR

    args = [a for a in argv if a not in ("--strict", "--registered-only", "--allow-draft")]
    positional = []
    cli_pack = packs_root_arg = None
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
        elif a == "--template-pack":
            i += 1
            cli_pack = args[i]
        elif a == "--packs-root":
            i += 1
            packs_root_arg = Path(args[i])
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

    # 模板包解析(多模板架構,docs/ARCHITECTURE.md §6;解不到包且 spec 未指定
    # = 退回單模板現行為;spec 指定了卻找不到 = 前置缺檔 exit 2)
    deck_obj = spec.get("deck") if isinstance(spec.get("deck"), dict) else {}
    spec_template = deck_obj.get("template")
    cli_id = Path(cli_pack).name if cli_pack else None  # 允許 --template-pack 給包目錄路徑
    if cli_id and spec_template and cli_id != spec_template:
        print(f"✗ --template-pack {cli_pack!r} 與 spec 的 deck.template="
              f"{spec_template!r} 不一致:改一致後重跑(不靜默擇一,保確定性)")
        return 2
    chosen = cli_pack or spec_template
    if chosen and (Path(chosen) / "manifest.json").exists():
        packs_root, chosen = Path(chosen).parent, Path(chosen).name
    else:
        packs_root = packs_root_arg or (asset_base / "templates")
    try:
        pack = load_pack_context(packs_root, chosen, allow_draft=allow_draft)
    except ValueError as e:
        print(f"✗ 模板包設定錯誤:{e}")
        return 2
    if pack is None and chosen:
        print(f"✗ 找不到模板包 {chosen!r}(packs root: {packs_root})")
        return 2
    merged_page_types = pack["page_types"] if pack else None

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
        validate_slide(slide, block, asset_base, rep, registered_only,
                       pack=pack, page_types=merged_page_types)

    declared = spec.get("deck", {}).get("slide_count")
    if declared is not None and declared != len(slides):
        rep.error("deck.slide_count", f"宣告 {declared} 頁，實際 {len(slides)} 頁")

    # 輸出
    print(f"驗證：{spec_path}")
    if pack:
        print(f"模板包:{pack['id']}@{pack['version']}(全自動 {len(pack['auto'])} 種)")
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
