"""Command-line interface."""

from __future__ import annotations

import argparse
import os
import sys
import time

from . import __version__
from .converter import (
    QUALITY_PRESETS,
    ConversionError,
    Options,
    collect_inputs,
    convert,
    default_output_path,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="step2glb-cli",
        description="Convert STEP/STP files to GLB. Folders are scanned for .step/.stp files.",
    )
    p.add_argument("inputs", nargs="+", help="STEP files and/or folders")
    p.add_argument("-o", "--out-dir", help="write GLB files here (default: next to each STEP file)")
    p.add_argument("-q", "--quality", choices=list(QUALITY_PRESETS), default="normal",
                   help="mesh quality preset (default: normal)")
    p.add_argument("-d", "--deflection", type=float,
                   help="absolute linear deflection in model units (mm); overrides --quality")
    p.add_argument("-r", "--recursive", action="store_true", help="scan folders recursively")
    p.add_argument("--skip-existing", action="store_true", help="skip files whose GLB already exists")
    p.add_argument("--z-up", action="store_true", help="keep the STEP Z-up axis (glTF is normally Y-up)")
    p.add_argument("--mm", action="store_true", help="keep millimetres (glTF is normally metres)")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def run(argv) -> int:
    args = build_parser().parse_args(argv)
    files = collect_inputs(args.inputs, recursive=args.recursive)
    if not files:
        print("No .step/.stp files found.", file=sys.stderr)
        return 2

    opts = Options(quality=args.quality, deflection=args.deflection,
                   y_up=not args.z_up, metres=not args.mm)
    failed = 0
    t0 = time.time()
    for i, src in enumerate(files, 1):
        dst = default_output_path(src, args.out_dir)
        print(f"\n[{i}/{len(files)}] {src}")
        if args.skip_existing and os.path.exists(dst):
            print("  skipped (GLB already exists)")
            continue
        try:
            convert(src, dst, opts, log=lambda m: print("  " + m, flush=True))
        except ConversionError as e:
            failed += 1
            print(f"  ERROR: {e}", file=sys.stderr)
        except Exception as e:  # keep going with the remaining files
            failed += 1
            print(f"  ERROR: {type(e).__name__}: {e}", file=sys.stderr)
    print(f"\nFinished {len(files) - failed}/{len(files)} file(s) in {time.time() - t0:.1f}s")
    return 1 if failed else 0
