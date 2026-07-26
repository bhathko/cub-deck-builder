#!/usr/bin/env python3
"""產檔管線單一入口:稽核 → spec 閘門 → 渲染 → QA,一個指令跑完全部。

設計目的:把「模型照文件串多步」塌縮成「跑一個指令、轉述報告」——步驟數是
卡死率的分母。任一階段非 0 即停,不會產出半成品;整條冪等,重跑即重生。

模式(由參數自動判定):
  outline 模式(帶 --slides):先跑 audit_provenance.py(帶 --source 時含來源
    完整性檢查),validator 自動帶 --slides --registered-only --strict。
  直供 JSON 模式(不帶 --slides):不稽核;validator 以本次獨一且不存在的
    路徑關閉來源追溯,不帶 --strict/--registered-only(缺來源 WARN 是預期)。

用法:
  # outline 一鍵(/outline-to-ppt)
  python /mnt/data/tools/run_pipeline.py \
      --spec /mnt/data/slide_spec.json \
      --slides /mnt/data/slides.md \
      --source /mnt/data/outline_source_current.txt \
      --asset-dir /mnt/data --out /mnt/data/deck.pptx

  # 直供 JSON(未涵蓋頁型先寫 plan 再加 --plan;或先 --validate-only 過閘門)
  python /mnt/data/tools/run_pipeline.py --spec /mnt/data/slide_spec.json \
      --asset-dir /mnt/data --out /mnt/data/deck.pptx [--plan render_plan.json]

模板選擇(ARCHITECTURE §6):spec 的 deck.template(省略=light)或
--template-pack <id>;模板檔預設=選定包的 template.pptx,--template 為
顯式覆寫(試模板工作流)。--packs-root 預設=tools 上層的 templates/。

exit = 首個失敗階段的 exit code(0 = 全部通過);exit 2 = 前置缺檔。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pack_loader


def parse_args(argv):
    args = {"--validate-only": False}
    it = iter(argv)
    for a in it:
        if a == "--validate-only":
            args[a] = True
        elif a.startswith("--"):
            args[a] = next(it, None)
    return args


def run_stage(idx, total, name, cmd):
    print(f"\n== 階段 {idx}/{total}:{name} ==", flush=True)
    print("  $ " + " ".join(str(c) for c in cmd[1:]), flush=True)
    rc = subprocess.run([sys.executable] + [str(c) for c in cmd[1:]]).returncode
    if rc != 0:
        print(f"\n管線停止於階段 {idx}/{total}「{name}」(exit {rc})。"
              f"修正輸入後整條重跑本指令;不得跳過此階段或手改產出。", flush=True)
        sys.exit(rc)


def main(argv):
    a = parse_args(argv)
    asset_dir = Path(a.get("--asset-dir") or "/mnt/data")
    spec = Path(a.get("--spec") or asset_dir / "slide_spec.json")
    slides = Path(a["--slides"]) if a.get("--slides") else None
    source = Path(a["--source"]) if a.get("--source") else None
    out = Path(a.get("--out") or asset_dir / "deck.pptx")
    plan = Path(a["--plan"]) if a.get("--plan") else None
    validator = Path(a.get("--validator") or asset_dir / "validate_slide_spec_gpts.py")

    # 模板包解析(ARCHITECTURE §6):一次解析,四階段共用同一結果
    spec_deck = {}
    if spec.exists():
        try:
            spec_deck = (json.loads(spec.read_text(encoding="utf-8-sig")) or {}).get("deck") or {}
        except (json.JSONDecodeError, OSError):
            spec_deck = {}  # 壞 JSON 交給 validator 階段回報
    try:
        pack = pack_loader.load_pack(pack_arg=a.get("--template-pack"),
                                     spec_deck=spec_deck,
                                     packs_root=a.get("--packs-root"),
                                     load_bindings=False)
    except pack_loader.PackError as e:
        print(f"[E] 模板包載入失敗:{e}")
        sys.exit(2)
    if a.get("--template"):
        template = Path(a["--template"])  # 顯式覆寫(試模板工作流)
    else:
        template = pack.resolve_template(asset_dir) or pack.dir / pack.manifest.get(
            "template_file", "template.pptx")

    outline_mode = slides is not None
    required = {
        "spec": spec, "validator": validator, "template": template,
        "render_deck": HERE / "render_deck.py", "qa_check": HERE / "qa_check.py",
        "模板包 manifest": pack.dir / "manifest.json",
    }
    # 素材目錄:asset_dir/assets 或包內 assets(新佈局素材隨包出貨)擇一即可
    if not (asset_dir / "assets").exists() and not (pack.dir / "assets").exists():
        required["素材目錄 assets/"] = asset_dir / "assets"
    if outline_mode:
        required["slides.md"] = slides
        required["audit_provenance"] = HERE / "audit_provenance.py"
    if source is not None:
        required["source 原文檔"] = source
    if plan is not None:
        required["render_plan"] = plan
    missing = [f"{k}:{v}" for k, v in required.items() if not v.exists()]
    if missing:
        print("[E] 前置缺檔(先重做環境準備/重新解壓,不得憑此宣稱工具鏈無法執行):")
        for m in missing:
            print(f"  - {m}")
        sys.exit(2)

    total = (2 if outline_mode else 1) + (0 if a["--validate-only"] else 2)
    idx = 0
    mode = "outline(稽核+strict)" if outline_mode else "直供 JSON(追溯關)"
    print(f"管線模式:{mode}    模板包:{pack.id}@{pack.version}    共 {total} 階段",
          flush=True)
    pk_args = []
    if a.get("--template-pack"):
        pk_args += ["--template-pack", a["--template-pack"]]
    if a.get("--packs-root"):
        pk_args += ["--packs-root", a["--packs-root"]]

    if outline_mode:
        idx += 1
        cmd = [sys.executable, HERE / "audit_provenance.py",
               "--spec", spec, "--slides", slides]
        if source is not None:
            cmd += ["--source", source]
        run_stage(idx, total, "工作流稽核(audit_provenance)", cmd)

    idx += 1
    if outline_mode:
        vcmd = [sys.executable, validator, "--spec", spec, "--slides", slides,
                "--asset-dir", asset_dir, "--registered-only", "--strict"]
    else:
        no_slides = Path(tempfile.mkdtemp(prefix="direct_json_")) / "run.no-slides"
        vcmd = [sys.executable, validator, "--spec", spec,
                "--slides", no_slides, "--asset-dir", asset_dir]
    run_stage(idx, total, "spec 閘門(validator)", vcmd + pk_args)

    if a["--validate-only"]:
        print(f"\n管線結果:PASS({idx}/{total} 階段,--validate-only 到此為止)")
        return 0

    idx += 1
    rcmd = [sys.executable, HERE / "render_deck.py", "--spec", spec,
            "--template", template, "--asset-dir", asset_dir, "--out", out]
    if plan is not None:
        rcmd += ["--plan", plan]
    run_stage(idx, total, "渲染(render_deck)", rcmd + pk_args)

    idx += 1
    run_stage(idx, total, "產檔後自檢(qa_check)",
              [sys.executable, HERE / "qa_check.py", "--spec", spec, "--pptx", out] + pk_args)

    print(f"\n管線結果:PASS({total}/{total} 階段)— 交付 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
