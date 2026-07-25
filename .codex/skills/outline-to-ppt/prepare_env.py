#!/usr/bin/env python3
"""建立/刷新本機產檔沙箱 ppt_out/(跨平台:macOS / Linux / Windows,只用標準庫)。

把 repo 的工具鏈複製成模擬 GPTs /mnt/data 的佈局,讓後續命令不需要
PYTHONPATH、--template、--validator 等 shell 差異:

    ppt_out/
      assets/            ← gpts/templates/light/assets_src(冪等覆蓋;素材源檔隨包)
      tools/             ← gpts/tools(冪等覆蓋,排除 __pycache__)
      templates/         ← gpts/templates(模板包,含模板本體;pack_loader 載入)
      validate_slide_spec_gpts.py

每次產檔 session 先跑本腳本;exit 0 = 沙箱就緒。副本一律以 repo 為準覆蓋,
不存在「ppt_out 裡的工具比 repo 新」的情境——改工具請改 gpts/ 再重跑本腳本。
"""
import argparse
import importlib.util
import shutil
import sys
from pathlib import Path

REQUIRED = [
    "assets/backgrounds/content_bg.png",
    "assets/backgrounds/cover_bg.png",
    "assets/backgrounds/cover_bg_context.png",
    "assets/logos/cathay_logo.png",
    "tools/run_pipeline.py",
    "tools/make_skeleton.py",
    "tools/audit_provenance.py",
    "tools/render_deck.py",
    "tools/qa_check.py",
    "templates/light/manifest.json",
    "templates/light/bindings.py",
    "templates/light/template.pptx",
    "validate_slide_spec_gpts.py",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".", help="ppppai repo 根目錄(預設=目前目錄)")
    repo = Path(ap.parse_args().repo).resolve()
    gpts = repo / "gpts"
    if not gpts.is_dir():
        print(f"[E] {repo} 不是 ppppai repo(找不到 gpts/):先 cd 到 repo 根目錄或加 --repo")
        return 1

    work = repo / "ppt_out"
    work.mkdir(exist_ok=True)
    ignore = shutil.ignore_patterns("__pycache__")
    shutil.copytree(gpts / "templates" / "light" / "assets_src", work / "assets",
                    dirs_exist_ok=True, ignore=ignore)
    shutil.copytree(gpts / "tools", work / "tools", dirs_exist_ok=True, ignore=ignore)
    shutil.copytree(gpts / "templates", work / "templates", dirs_exist_ok=True, ignore=ignore)
    shutil.copy2(gpts / "knowledge" / "validate_slide_spec_gpts.py", work)

    missing = [rel for rel in REQUIRED if not (work / rel).exists()]
    for rel in REQUIRED:
        print(("OK  " if (work / rel).exists() else "缺  ") + f"ppt_out/{rel}")
    if missing:
        print(f"[E] 缺 {len(missing)} 個檔案,沙箱未就緒(檢查 repo 是否完整)")
        return 1

    print("-" * 40)
    py = Path(sys.executable).name
    if importlib.util.find_spec("pptx") is not None:
        print(f"渲染指令前綴:{py}(本直譯器已有 python-pptx)")
    elif shutil.which("uv"):
        print("渲染指令前綴:uv run --with python-pptx python(本直譯器缺 python-pptx,改用 uv)")
    else:
        print(f"[W] 本直譯器缺 python-pptx 且找不到 uv:先執行 {py} -m pip install python-pptx")
    print("沙箱就緒:ppt_out/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
