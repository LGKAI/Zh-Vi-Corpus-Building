#!/usr/bin/env python3
"""Master End-to-End Pipeline Orchestrator for Sino-Vietnamese OCR & Parallel Alignment.

Executes all stages sequentially:
1. Source Image Verification (`01_nguon/*.png`, optional Swift extraction from `data/*.pdf`).
2. OCR Stage (`kaggle_ocr/ocr_pipeline_kaggle.py`: real GPU PaddleOCR+VietOCR when available,
   or skips cleanly when consuming downloaded Kaggle `02_ocr_tho/*.json`, or local `--mock`).
3. End-to-End Corpus Alignment (`src/corpus_pipeline.py`: reads strictly from `02_ocr_tho/*.json`
   -> Disambiguation -> Cleaning -> Plateau DP Alignment -> QA -> TSV & 2-sheet XLSX).
4. Hugging Face Dataset Packaging (`scripts/package_hf_dataset.py`).
5. Quality Diagnostics (`scripts/diagnose_corpus_quality.py`).
6. Downstream NMT Evaluation (`scripts/eval_translation_benchmark.py`).
7. Instructor Demo Package (`scripts/demo_1_2_pages.py`).

Usage:
    python3 scripts/run_end_to_end.py
    python3 scripts/run_end_to_end.py --skip-ocr        # Run alignment directly from downloaded Kaggle 02_ocr_tho/
    python3 scripts/run_end_to_end.py --gpu             # Force real PaddleOCR+VietOCR inference
    python3 scripts/run_end_to_end.py --pilot-only      # Process verified pilot pages only
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from kaggle_ocr import ocr_pipeline_kaggle
from src.corpus_pipeline import load_book_manifest, run_corpus_from_ocr


def _has_live_ocr_packages() -> bool:
    return all(
        importlib.util.find_spec(pkg) is not None
        for pkg in ("paddleocr", "vietocr", "cv2")
    )


def _has_real_gpu_ocr_outputs(workspace_root: Path, book_cfg: Dict[str, Any]) -> bool:
    ocr_dir = workspace_root / book_cfg.get("ocr_raw_dir", "")
    summary_file = ocr_dir / "ocr_run_summary.json"
    if not summary_file.is_file():
        return False
    try:
        meta = json.loads(summary_file.read_text(encoding="utf-8"))
        return meta.get("mode") == "kaggle_gpu" and meta.get("pages_processed", 0) > 0
    except Exception:
        return False


def run_end_to_end(
    workspace_root: Path = ROOT_DIR,
    book_filter: Optional[str] = None,
    use_gpu: bool = False,
    skip_ocr: bool = False,
    pilot_only: bool = False,
    max_pages: Optional[int] = None,
    run_downstream: bool = True,
) -> Dict[str, Any]:
    """Execute the full end-to-end pipeline cleanly from images/OCR JSONs to final deliverables."""
    t_start = time.perf_counter()
    manifest = load_book_manifest(workspace_root / "config" / "book_manifest.json")
    books_cfg = manifest.get("books", {})
    target_books = [book_filter] if book_filter else ["HVTT", "TVLT2", "TLTVN"]

    live_ocr_available = _has_live_ocr_packages()
    ocr_reports: Dict[str, Any] = {}

    # Stage 1 & 2: Source Verification + OCR
    for book_key in target_books:
        if book_key not in books_cfg:
            continue
        cfg = books_cfg[book_key]
        source_dir = workspace_root / cfg["source_dir"]
        deliverable_dir = workspace_root / cfg["deliverable_dir"]
        png_count = len(list(source_dir.glob("*.png"))) if source_dir.is_dir() else 0

        if skip_ocr:
            ocr_reports[book_key] = {"status": "skipped_using_existing_ocr_json", "png_count": png_count}
            continue

        # Preserve real Kaggle GPU outputs if already present and caller didn't force overwrite
        if not use_gpu and _has_real_gpu_ocr_outputs(workspace_root, cfg):
            ocr_reports[book_key] = {"status": "preserved_kaggle_gpu_ocr", "png_count": png_count}
            continue

        run_mock = not (use_gpu or live_ocr_available)
        if use_gpu and not live_ocr_available:
            raise RuntimeError(
                "--gpu requested, but paddleocr/vietocr/cv2 are not installed locally. "
                "Deploy to Kaggle via `./kaggle_ocr/deploy_to_kaggle.sh` or omit `--gpu` for local mode."
            )

        argv = [
            "--input-dir", str(source_dir),
            "--output-dir", str(deliverable_dir),
            "--book-type", book_key,
        ]
        if run_mock:
            argv.append("--mock")
        if pilot_only or (run_mock and max_pages is None):
            argv.append("--pilot-only")
        if max_pages is not None and max_pages > 0:
            argv.extend(["--max-pages", str(max_pages)])

        rc = ocr_pipeline_kaggle.main(argv)
        if rc != 0:
            raise RuntimeError(f"OCR stage failed for {book_key} (exit {rc})")
        ocr_reports[book_key] = {
            "status": "mock_ocr" if run_mock else "live_gpu_ocr",
            "png_count": png_count,
        }

    # Stage 3: End-to-End Alignment & Export strictly from 02_ocr_tho JSONs
    corpus_summary = run_corpus_from_ocr(
        workspace_root=workspace_root,
        ocr_root=workspace_root,
        manifest_path=workspace_root / "config" / "book_manifest.json",
        book_filter=book_filter,
        pilot_only=pilot_only,
    )

    downstream_reports: Dict[str, Any] = {}
    if run_downstream and book_filter is None:
        # Stage 4: Package Hugging Face Dataset
        pkg_proc = subprocess.run(
            [sys.executable, str(workspace_root / "scripts" / "package_hf_dataset.py")],
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
        )
        downstream_reports["hf_packaging_rc"] = pkg_proc.returncode

        # Stage 5: Corpus Quality Diagnosis
        diag_proc = subprocess.run(
            [sys.executable, str(workspace_root / "scripts" / "diagnose_corpus_quality.py")],
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
        )
        downstream_reports["diagnosis_rc"] = diag_proc.returncode

        # Stage 6: Translation Benchmark
        eval_proc = subprocess.run(
            [sys.executable, str(workspace_root / "scripts" / "eval_translation_benchmark.py")],
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
        )
        downstream_reports["benchmark_rc"] = eval_proc.returncode

        # Stage 7: Instructor Demo Package
        demo_proc = subprocess.run(
            [sys.executable, str(workspace_root / "scripts" / "demo_1_2_pages.py")],
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
        )
        downstream_reports["demo_rc"] = demo_proc.returncode

    return {
        "status": "SUCCESS",
        "elapsed_seconds": round(time.perf_counter() - t_start, 3),
        "live_ocr_installed": live_ocr_available,
        "ocr_stage": ocr_reports,
        "alignment_stage": corpus_summary,
        "downstream_stage": downstream_reports,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run full end-to-end OCR & Alignment pipeline.")
    parser.add_argument("--book", choices=["HVTT", "TVLT2", "TLTVN"], default=None, help="Target a single book.")
    parser.add_argument("--gpu", action="store_true", help="Force real PaddleOCR + VietOCR inference.")
    parser.add_argument("--skip-ocr", action="store_true", help="Skip OCR and build corpus directly from existing `02_ocr_tho` JSONs.")
    parser.add_argument("--pilot-only", action="store_true", help="Restrict alignment strictly to manifest pilot pages.")
    parser.add_argument("--max-pages", type=int, default=None, help="Limit OCR pages per book.")
    parser.add_argument("--no-downstream", action="store_true", help="Skip Hugging Face / diagnosis / benchmark / demo steps.")
    args = parser.parse_args(argv)

    summary = run_end_to_end(
        workspace_root=ROOT_DIR,
        book_filter=args.book,
        use_gpu=args.gpu,
        skip_ocr=args.skip_ocr,
        pilot_only=args.pilot_only,
        max_pages=args.max_pages,
        run_downstream=not args.no_downstream,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
