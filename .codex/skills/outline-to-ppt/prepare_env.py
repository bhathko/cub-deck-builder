#!/usr/bin/env python3
"""建立/刷新本機產檔沙箱 ppt_out/(跨平台:macOS / Linux / Windows,只用標準庫)。

把 repo 的工具鏈複製成模擬 GPTs /mnt/data 的佈局,讓後續命令不需要
PYTHONPATH、--template、--validator 等 shell 差異:

    ppt_out/
      assets/            ← engine/templates/light/assets_src(冪等覆蓋;素材源檔隨包)
      tools/             ← engine/tools(冪等覆蓋,排除 __pycache__)
      templates/         ← engine/templates(模板包,含模板本體;pack_loader 載入)
      validate_slide_spec_gpts.py

每次產檔 session 先跑本腳本;exit 0 = 沙箱就緒。副本一律以 repo 為準覆蓋,
不存在「ppt_out 裡的工具比 repo 新」的情境——改工具請改 engine/ 再重跑本腳本。
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
    # bindings.json(非 .py):填充綁定一律是宣告式 json,bindings.py 已於
    # 2026-07-26 廢除,pack_loader 現在遇到它會直接 PackError(見下方 rmtree 註解)。
    "templates/light/bindings.json",
    "templates/light/template.pptx",
    "validate_slide_spec_gpts.py",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".", help="cub-deck-builder repo 根目錄(預設=目前目錄)")
    repo = Path(ap.parse_args().repo).resolve()
    engine = repo / "engine"
    if not engine.is_dir():
        print(f"[E] {repo} 不是 cub-deck-builder repo(找不到 engine/):先 cd 到 repo 根目錄或加 --repo")
        return 1

    work = repo / "ppt_out"
    work.mkdir(exist_ok=True)
    ignore = shutil.ignore_patterns("__pycache__")
    # 先砍再複製,不用 copytree(dirs_exist_ok=True) 就地覆蓋。
    # 原因(2026-07-26 實地踩到):copytree 只覆蓋、**從不刪除**,所以 engine 端
    # 刪掉的檔案會在沙箱裡變成幽靈。light 刪掉 bindings.py 後,ppt_out 的舊複本
    # 仍被 pack_loader 讀到,BUILDERS 於是悄悄蓋過 bindings.json 的 fill——
    # 產出是舊 builtin 版面,而所有訊息都顯示正常。沙箱是**衍生物**,
    # 一律重建才能保證與 engine/ 等價。(pack_loader 現已對 bindings.py 硬擋,
    # 同型殘留會吵鬧地失敗;但那是第二道防線,重建仍是第一道。)
    for sub in ("assets", "tools", "templates"):
        shutil.rmtree(work / sub, ignore_errors=True)
    shutil.copytree(engine / "templates" / "light" / "assets_src", work / "assets",
                    ignore=ignore)
    shutil.copytree(engine / "tools", work / "tools", ignore=ignore)
    shutil.copytree(engine / "templates", work / "templates", ignore=ignore)
    shutil.copy2(engine / "rules" / "validate_slide_spec_gpts.py", work)

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
