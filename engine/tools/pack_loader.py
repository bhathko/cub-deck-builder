#!/usr/bin/env python3
"""pack_loader — 模板包載入器(多模板架構的引擎入口,見 docs/ARCHITECTURE.md)。

模板包 = engine/templates/<id>/(manifest.json + bindings + 素材)。本工具解析
「用哪個包」並載入其 manifest 與綁定;引擎(render_deck 等)只透過 Pack 物件
取用模板知識,不得寫死任何模板專屬常數。

解析優先序(並存且不同 → PackError,不靜默擇一):
  CLI 參數(--template-pack)→ spec 的 deck.template → 預設 "light"。
packs root 預設 = 本檔所在目錄的上一層 /templates(repo: engine/templates;
沙箱: /mnt/data/templates 或 ppt_out/templates)。

綁定只有一種形式:`bindings.json` 的宣告式 fills(fills_engine 解譯)。
包內出現 `bindings.py` 一律 PackError——引擎不執行包內 Python,而這種殘留檔
在引擎還會載入它的年代能靜默蓋過 bindings.json:沙箱舊複本留了一支,
產出是舊版面而所有訊息都顯示正常。載入期硬擋,讓殘留吵鬧地失敗。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent


class PackError(Exception):
    pass


def default_packs_root() -> Path:
    return _HERE.parent / "templates"


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Pack:
    def __init__(self, pack_dir: Path, manifest: dict, fills: dict | None = None):
        self.dir = pack_dir
        self.manifest = manifest
        self.id = manifest.get("template_id", pack_dir.name)
        self.version = manifest.get("version", "?")
        self.template_sha256 = manifest.get("template_sha256")
        self.page_types = manifest.get("page_types", {})
        self.fills = fills or {}

    def template_hash_matches(self, pptx_path) -> bool:
        """比對實際模板檔與 manifest 雜湊;無宣告值時視為相符(不擋)。"""
        if not self.template_sha256:
            return True
        return sha256_file(pptx_path) == self.template_sha256

    def resolve_template(self, asset_dir=None):
        """模板檔解析:包目錄優先;找不到回 asset-dir 同名檔與 light 舊檔名
        (沙箱相容:/mnt/data 或 ppt_out 根曾放 light_template.pptx)。"""
        name = self.manifest.get("template_file", "template.pptx")
        candidates = [self.dir / name]
        if asset_dir:
            candidates += [Path(asset_dir) / name, Path(asset_dir) / "light_template.pptx"]
        for c in candidates:
            if c.exists():
                return c
        return None


def _load_bindings(pack_dir: Path, pack_id: str, manifest: dict) -> dict:
    if str(_HERE) not in sys.path:  # fills_engine 需 import fill_helpers/text_tools 等
        sys.path.insert(0, str(_HERE))
    py, bj = pack_dir / "bindings.py", pack_dir / "bindings.json"
    if py.exists():
        raise PackError(
            f"模板包 {pack_id} 內有 bindings.py({py})——引擎不執行包內 Python,"
            f"綁定一律走 bindings.json。這支檔是舊版殘留(最常見是沒清乾淨的沙箱"
            f"複本),它在的地方就代表這個包沒同步乾淨;請直接刪除它。")
    if not bj.exists():
        raise PackError(f"模板包 {pack_id} 缺綁定(找不到 {bj})")
    import fills_engine
    data = json.loads(bj.read_text(encoding="utf-8-sig"))
    try:
        return fills_engine.build_fills(data, manifest.get("style") or {})
    except Exception as e:
        raise PackError(f"模板包 {pack_id} 的 bindings.json 無法載入:{e}")


def load_pack(pack_arg: str | None = None, spec_deck: dict | None = None,
              packs_root=None, load_bindings: bool = True) -> Pack:
    """解析並載入模板包。pack_arg 可為包 id 或包目錄路徑。

    load_bindings=False:只讀 manifest,不解譯 bindings.json——供純標準庫工具
    (make_skeleton/run_pipeline/qa_check)使用;fills_engine 會 import python-pptx,
    只有 render_deck 真正需要。"""
    spec_id = (spec_deck or {}).get("template")
    if pack_arg and spec_id and Path(pack_arg).name != spec_id and pack_arg != spec_id:
        raise PackError(
            f"CLI 指定模板包 {pack_arg!r} 與 spec 的 deck.template={spec_id!r} 不一致:"
            "改一致後重跑(不靜默擇一,保確定性)")
    chosen = pack_arg or spec_id or "light"

    root = Path(packs_root) if packs_root else default_packs_root()
    pack_dir = Path(chosen) if Path(chosen).is_dir() else root / chosen
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.exists():
        raise PackError(
            f"找不到模板包 {chosen!r}(缺 {manifest_path});"
            f"packs root = {root}。可用包:"
            + (", ".join(sorted(p.name for p in root.iterdir() if (p / 'manifest.json').exists())
                         ) if root.is_dir() else "(packs root 不存在)"))
    # utf-8-sig:容忍 Windows 工具寫入的 BOM(同 repo 其他 JSON 讀取慣例)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    fills = {}
    if load_bindings:
        fills = _load_bindings(pack_dir, manifest.get("template_id", pack_dir.name),
                               manifest)
    return Pack(pack_dir, manifest, fills)
