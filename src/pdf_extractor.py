"""Cross-platform (Windows/macOS/Linux) 300 DPI PDF page renderer & member shard stager.

Replaces macOS-only `extract_pages.swift` and `deploy_to_kaggle.sh` with pure Python
+ PyMuPDF (`fitz`) so any member on Windows can:
1. Render their assigned shard (`--member khanh`, `khoa`, `hieu`, `kin`) or any page range
   from `raw_data/*.pdf` into `CV04_VPO_0*/01_nguon/*.png` at 300 DPI.
2. Stage their assigned PNGs + `src/` + `config/` into `staging/kaggle_<member>/` for
   Kaggle GPU execution.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union


def load_manifest(workspace_root: Path) -> Dict[str, Any]:
    """Load `config/book_manifest.json`."""
    manifest_path = workspace_root / "config" / "book_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def load_member_splits(workspace_root: Path) -> Dict[str, Any]:
    """Load `config/member_splits.json`."""
    splits_path = workspace_root / "config" / "member_splits.json"
    if not splits_path.is_file():
        raise FileNotFoundError(f"Member splits not found at {splits_path}")
    return json.loads(splits_path.read_text(encoding="utf-8"))


def resolve_book_id(book_key: str, manifest: Dict[str, Any]) -> str:
    """Resolve any book alias (`HVTT`, `VPO_01`, `CV04_VPO_01`, etc.) to canonical `VPO_01/02/03`."""
    aliases = manifest.get("aliases", {})
    key_upper = book_key.upper().strip()
    if key_upper in aliases:
        return aliases[key_upper]
    if key_upper in manifest.get("books", {}):
        return key_upper
    raise ValueError(
        f"Unknown book code: {book_key!r}. Valid codes: VPO_01, VPO_02, VPO_03 (or HVTT, TLTVN, TVLT2)"
    )


def parse_page_spec(page_spec: str, book_cfg: Dict[str, Any]) -> List[int]:
    """Parse a page specification string (`'pilot'`, `'valid'`, or `'8,10,12-20'`) into 1-based PDF pages."""
    spec = page_spec.strip().lower()
    if spec == "pilot":
        return sorted(int(p) for p in book_cfg.get("pilot_pages", []))

    valid_range = book_cfg.get("valid_range", {})
    excluded_set = set(int(p) for p in book_cfg.get("excluded_pdf_pages_in_valid_range", []))
    if spec in ("valid", "all"):
        start = int(valid_range.get("pdf_page_start", 1))
        end = int(valid_range.get("pdf_page_end", book_cfg.get("total_pdf_pages", 1)))
        step = int(valid_range.get("step", 1))
        return [p for p in range(start, end + 1, step) if p not in excluded_set]

    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part or ".." in part:
            sep = ".." if ".." in part else "-"
            bounds = part.split(sep, 1)
            p_start, p_end = int(bounds[0].strip()), int(bounds[1].strip())
            for p in range(min(p_start, p_end), max(p_start, p_end) + 1):
                if p not in excluded_set:
                    pages.add(p)
        else:
            pages.add(int(part))
    return sorted(pages)


def render_pdf_pages_to_png(
    pdf_path: Union[str, Path],
    output_dir: Union[str, Path],
    pages_1based: Sequence[int],
    dpi: int = 300,
    overwrite: bool = False,
) -> List[Path]:
    """Render 1-based PDF pages to 4-digit PNG files (`0008.png`) using PyMuPDF (`fitz`)."""
    import fitz  # PyMuPDF

    pdf_file = Path(pdf_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_file.is_file():
        raise FileNotFoundError(f"PDF file not found: {pdf_file}")

    doc = fitz.open(str(pdf_file))
    total_pages = len(doc)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    saved_paths: List[Path] = []
    try:
        for p_num in pages_1based:
            if p_num < 1 or p_num > total_pages:
                continue
            out_png = out_dir / f"{p_num:04d}.png"
            if out_png.is_file() and out_png.stat().st_size > 10_000 and not overwrite:
                saved_paths.append(out_png)
                continue
            page = doc[p_num - 1]
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pix.save(str(out_png))
            saved_paths.append(out_png)
    finally:
        doc.close()

    return saved_paths


def extract_book_pages(
    workspace_root: Path,
    book_key: str = "ALL",
    page_spec: str = "pilot",
    member: Optional[str] = None,
    dpi: int = 300,
    overwrite: bool = False,
) -> Dict[str, List[str]]:
    """Render requested pages (or a member's assigned shard) from `raw_data/` into `CV04_VPO_0*/01_nguon/`."""
    manifest = load_manifest(workspace_root)
    books_cfg = manifest["books"]

    if book_key.upper().strip() == "ALL":
        target_books = list(books_cfg.keys())
    else:
        target_books = [resolve_book_id(book_key, manifest)]

    member_books: Optional[Dict[str, Any]] = None
    if member:
        splits = load_member_splits(workspace_root)
        m_key = member.lower().strip()
        if m_key not in splits.get("members", {}):
            raise ValueError(f"Unknown member: {member!r}. Expected one of: khoa, hieu, khanh, kin")
        member_books = splits["members"][m_key]["books"]

    extracted: Dict[str, List[str]] = {}
    for b_id in target_books:
        cfg = books_cfg[b_id]
        pdf_path = workspace_root / cfg["pdf_path"]
        out_dir = workspace_root / cfg["source_dir"]

        if member_books is not None:
            legacy_id = cfg.get("legacy_id", b_id)
            b_slice = member_books.get(b_id) or member_books.get(legacy_id) or {}
            pages = [int(p) for p in b_slice.get("pdf_pages", [])]
        else:
            pages = parse_page_spec(page_spec, cfg)

        paths = render_pdf_pages_to_png(
            pdf_path=pdf_path,
            output_dir=out_dir,
            pages_1based=pages,
            dpi=dpi,
            overwrite=overwrite,
        )
        extracted[b_id] = [str(p.relative_to(workspace_root)) for p in paths]

    return extracted


def stage_member_dataset_windows(
    workspace_root: Path,
    member: str = "khanh",
    staging_dir: Optional[Path] = None,
    kaggle_username: str = "leogiakhanh",
) -> Dict[str, Any]:
    """Stage a member's extracted PNGs + src/ + config/ into a Kaggle dataset folder on Windows."""
    splits = load_member_splits(workspace_root)
    m_key = member.lower().strip()
    if m_key not in splits.get("members", {}):
        raise ValueError(f"Unknown member: {member!r}. Expected one of: khoa, hieu, khanh, kin")

    m_info = splits["members"][m_key]
    target_dir = staging_dir or (workspace_root / "staging" / f"kaggle_{m_key}")
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy src/ and config/
    shutil.copytree(
        workspace_root / "src",
        target_dir / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (target_dir / "config").mkdir(parents=True, exist_ok=True)
    shutil.copy2(workspace_root / "config" / "book_manifest.json", target_dir / "config" / "book_manifest.json")

    # 2. Write Kaggle dataset-metadata.json
    dataset_slug = f"{kaggle_username}/han-viet-parallel-corpus-pages-{m_key}"
    kernel_slug = f"{kaggle_username}/han-viet-parallel-corpus-ocr-{m_key}"
    ds_meta = {
        "title": f"Han Viet Parallel Corpus Pages ({m_info['display_name']})",
        "id": dataset_slug,
        "licenses": [{"name": "CC0-1.0"}],
    }
    (target_dir / "dataset-metadata.json").write_text(
        json.dumps(ds_meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # 2b. Also prepare Kaggle GPU kernel directory next to dataset staging directory
    kernel_dir = target_dir.parent / f"kaggle_{m_key}_kernel"
    if kernel_dir.exists():
        shutil.rmtree(kernel_dir)
    kernel_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(workspace_root / "src" / "ocr_engine.py", kernel_dir / "ocr_pipeline_kaggle.py")
    kn_meta = {
        "id": kernel_slug,
        "title": f"Han Viet Parallel Corpus OCR Pipeline ({m_info['display_name']})",
        "code_file": "ocr_pipeline_kaggle.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "dataset_sources": [dataset_slug],
        "competition_sources": [],
        "kernel_sources": [],
    }
    (kernel_dir / "kernel-metadata.json").write_text(
        json.dumps(kn_meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # 3. Link/copy member PNG pages into CV04_VPO_0*/01_nguon/ inside staging_dir
    manifest = load_manifest(workspace_root)
    per_book_counts: Dict[str, int] = {}
    total_staged = 0

    for b_id, cfg in manifest["books"].items():
        legacy_id = cfg.get("legacy_id", b_id)
        b_slice = m_info["books"].get(b_id) or m_info["books"].get(legacy_id) or {}
        pdf_pages = [int(p) for p in b_slice.get("pdf_pages", [])]

        src_dir = workspace_root / cfg["source_dir"]
        dst_dir = target_dir / cfg["source_dir"]
        dst_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        for p_num in pdf_pages:
            src_png = src_dir / f"{p_num:04d}.png"
            if src_png.is_file():
                dst_png = dst_dir / src_png.name
                try:
                    os.link(src_png, dst_png)
                except OSError:
                    shutil.copy2(src_png, dst_png)
                count += 1
                total_staged += 1
        per_book_counts[b_id] = count

    return {
        "member": m_key,
        "display_name": m_info["display_name"],
        "staging_dir": str(target_dir),
        "kernel_dir": str(kernel_dir),
        "dataset_slug": dataset_slug,
        "kernel_slug": kernel_slug,
        "expected_pages": m_info["total_pages"],
        "staged_pages": total_staged,
        "per_book_counts": per_book_counts,
    }
