#!/usr/bin/env python3
"""pack_loader — 模板包載入器(多模板架構的引擎入口,見 gpts/TEMPLATE_PACKS.md)。

模板包 = gpts/templates/<id>/(manifest.json + bindings + 素材)。本工具解析
「用哪個包」並載入其 manifest 與綁定;引擎(render_deck 等)只透過 Pack 物件
取用模板知識,不得寫死任何模板專屬常數。

解析優先序(並存且不同 → PackError,不靜默擇一):
  CLI 參數(--template-pack)→ spec 的 deck.template → 預設 "light"。
packs root 預設 = 本檔所在目錄的上一層 /templates(repo: gpts/templates;
沙箱: /mnt/data/templates 或 ppt_out/templates)。

綁定兩形式,可並存(合併語意):
  - bindings.py:BUILDERS(builtin 繪製器,僅 light grandfather)與選配 FILLS;
  - bindings.json:宣告式 fills(fills_engine 解譯,新模板唯一路徑)。
  FILLS 取用順序:py 匯出非空 FILLS → 以 py 為準(json 忽略);否則用 json。
  BUILDERS 只能來自 py。light 自 Phase 3 起 py 只剩 BUILDERS,fills 走 json。
"""
from __future__ import annotations

import hashlib
import importlib.util
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
    def __init__(self, pack_dir: Path, manifest: dict, bindings_module):
        self.dir = pack_dir
        self.manifest = manifest
        self.id = manifest.get("template_id", pack_dir.name)
        self.version = manifest.get("version", "?")
        self.template_sha256 = manifest.get("template_sha256")
        self.page_types = manifest.get("page_types", {})
        self.pack_first = manifest.get("asset_resolution", "pack_first") == "pack_first"
        self.builders = getattr(bindings_module, "BUILDERS", {}) if bindings_module else {}
        self.fills = getattr(bindings_module, "FILLS", {}) if bindings_module else {}

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


class _JsonBindings:
    """綁定合併結果:與 Python bindings 模組同介面(FILLS/BUILDERS)。"""

    def __init__(self, fills, builders=None):
        self.FILLS = fills
        self.BUILDERS = builders or {}  # builtin 只能來自 bindings.py(僅 light)


def _load_bindings(pack_dir: Path, pack_id: str, manifest: dict):
    if str(_HERE) not in sys.path:  # bindings 需 import fill_helpers/text_tools 等
        sys.path.insert(0, str(_HERE))
    py, bj = pack_dir / "bindings.py", pack_dir / "bindings.json"
    builders, fills = {}, {}
    if py.exists():
        spec = importlib.util.spec_from_file_location(f"pack_bindings_{pack_id}", py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        builders = getattr(mod, "BUILDERS", {})
        fills = getattr(mod, "FILLS", {})  # py FILLS 非空 → 優先(grandfather)
    if not fills and bj.exists():
        import fills_engine
        data = json.loads(bj.read_text(encoding="utf-8-sig"))
        try:
            fills = fills_engine.build_fills(data, manifest.get("style") or {})
        except Exception as e:
            raise PackError(f"模板包 {pack_id} 的 bindings.json 無法載入:{e}")
    if not builders and not fills:
        raise PackError(f"模板包 {pack_id} 缺 bindings(找不到 {py} 或 bindings.json)")
    return _JsonBindings(fills, builders)


def load_pack(pack_arg: str | None = None, spec_deck: dict | None = None,
              packs_root=None, load_bindings: bool = True) -> Pack:
    """解析並載入模板包。pack_arg 可為包 id 或包目錄路徑。

    load_bindings=False:只讀 manifest,不 exec 綁定模組——供純標準庫工具
    (make_skeleton/run_pipeline/qa_check)使用;bindings 會 import python-pptx,
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
    bindings = None
    if load_bindings:
        bindings = _load_bindings(pack_dir, manifest.get("template_id", pack_dir.name),
                                  manifest)
    return Pack(pack_dir, manifest, bindings)
