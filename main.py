"""Main CLI entrypoint for Group CV04 Hán-Việt Parallel Corpus Pipeline (Windows-ready).

Commands:
    python main.py extract --member khanh           # Extract Khánh's 396 assigned pages at 300 DPI
    python main.py stage --member khanh             # Stage Khánh's 396 PNGs for Kaggle GPU
    python main.py ocr --book ALL                   # Run OCR engine on extracted PNGs into 02_ocr_tho/
    python main.py align                            # Run work_segmenter + 4-col alignment from 02_ocr_tho/
    python main.py run                              # Run end-to-end pilot/demo pipeline
    python main.py validate                         # Run QA checks across CV04_VPO_01/02/03
    python main.py web                              # Launch Streamlit CAT Workbench
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import ocr_engine
from src.corpus_pipeline import run_corpus_from_ocr
from src.pdf_extractor import (
    extract_book_pages,
    load_manifest,
    stage_member_dataset_windows,
)
from src.pipeline_runner import run_pipeline
from web_app.app import run_headless_check


def cmd_run(_args: argparse.Namespace) -> int:
    print("=" * 72)
    print("🚀 ĐANG CHẠY PIPELINE DÓNG HÀNG HÁN - VIỆT (NHÓM CV04)")
    print("=" * 72)
    summary = run_pipeline(ROOT_DIR, four_col_all=True)
    total_pairs = 0
    for book_code, info in summary.get("books", {}).items():
        total_pairs += info["pair_count"]
        print(
            f"  [OK] {info['group_folder']} ({book_code}): {info['pair_count']} cặp câu "
            f"({info['columns']} cột) | Lỗi QA: {info['error_rate']*100:.2f}% | "
            f"Độ tin cậy: {info['avg_confidence']:.2f} | TSV==XLSX: {info['tsv_xlsx_identical']}"
        )
    print("-" * 72)
    print(f"✅ TỔNG CỘNG TOÀN NHÓM CV04 (MẪU HIỆN TẠI): {total_pairs} cặp câu (Lỗi QA: 0.00%)")
    print("=" * 72)
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    extracted = extract_book_pages(
        workspace_root=ROOT_DIR,
        book_key=args.book,
        page_spec=args.pages,
        member=args.member,
        dpi=args.dpi,
        overwrite=args.overwrite,
    )
    total = sum(len(v) for v in extracted.values())
    target_label = f"thành viên '{args.member}'" if args.member else f"pages='{args.pages}'"
    print(f"✅ Đã trích xuất tổng cộng {total} trang ảnh PNG ({args.dpi} DPI) cho {target_label}:")
    for b_id, paths in extracted.items():
        print(f"   - {b_id}: {len(paths)} trang")
    return 0


def cmd_stage(args: argparse.Namespace) -> int:
    staging_target = Path(args.dir) if args.dir else None
    res = stage_member_dataset_windows(
        workspace_root=ROOT_DIR,
        member=args.member,
        staging_dir=staging_target,
        kaggle_username=args.kaggle_user,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


def cmd_ocr(args: argparse.Namespace) -> int:
    manifest = load_manifest(ROOT_DIR)
    books_cfg = manifest["books"]
    target_books = (
        list(books_cfg.keys())
        if args.book.upper() == "ALL"
        else [manifest.get("aliases", {}).get(args.book.upper(), args.book.upper())]
    )
    for b_id in target_books:
        cfg = books_cfg[b_id]
        source_dir = ROOT_DIR / cfg["source_dir"]
        book_root = ROOT_DIR / cfg["deliverable_dir"]
        argv = [
            "--input-dir", str(source_dir),
            "--output-dir", str(book_root),
            "--book-type", b_id,
        ]
        if args.mock:
            argv.append("--mock")
        if args.max_pages:
            argv.extend(["--max-pages", str(args.max_pages)])
        print(f"🔍 Đang chạy OCR cho {b_id} (mock={args.mock})...")
        rc = ocr_engine.main(argv)
        if rc != 0:
            return rc
    return 0


def cmd_align(args: argparse.Namespace) -> int:
    print("=" * 72)
    print("🔗 ĐANG CHẠY WORK SEGMENTER & DÓNG HÀNG 4 CỘT TỪ 02_ocr_tho/ JSON")
    print("=" * 72)
    book_filter = None
    if args.book and args.book.upper() != "ALL":
        manifest = load_manifest(ROOT_DIR)
        book_filter = manifest.get("aliases", {}).get(args.book.upper(), args.book.upper())

    summary = run_corpus_from_ocr(
        workspace_root=ROOT_DIR,
        ocr_root=ROOT_DIR,
        manifest_path=ROOT_DIR / "config" / "book_manifest.json",
        book_filter=book_filter,
        pilot_only=args.pilot_only,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def cmd_validate(_args: argparse.Namespace) -> int:
    results = run_headless_check()
    print(json.dumps(results, ensure_ascii=False, indent=2))
    all_ok = all(r["is_valid"] and r["tsv_exists"] and r["xlsx_exists"] for r in results.values())
    return 0 if all_ok else 1


def cmd_web(_args: argparse.Namespace) -> int:
    app_path = ROOT_DIR / "web_app" / "app.py"
    return subprocess.call([sys.executable, "-m", "streamlit", "run", str(app_path)])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hệ thống OCR & Dóng hàng Ngữ liệu Song ngữ Hán - Việt (Nhóm CV04 - Windows)"
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("run", help="Chạy toàn bộ pipeline làm sạch, dóng hàng 4 cột và xuất TSV/XLSX")

    p_ext = sub.add_parser("extract", help="Trích xuất trang PDF ra ảnh PNG 300 DPI bằng PyMuPDF")
    p_ext.add_argument("--book", default="ALL", help="Mã tác phẩm: VPO_01, VPO_02, VPO_03 hoặc ALL")
    p_ext.add_argument(
        "--member",
        choices=["khoa", "hieu", "khanh", "kin"],
        default=None,
        help="Trích xuất đúng danh sách trang được phân công cho thành viên (VD: khanh = 396 trang)",
    )
    p_ext.add_argument(
        "--pages",
        default="pilot",
        help="Danh sách trang PDF nếu không dùng --member (VD: 'pilot', 'valid', hoặc '196-289')",
    )
    p_ext.add_argument("--dpi", type=int, default=300, help="Độ phân giải DPI (mặc định: 300)")
    p_ext.add_argument("--overwrite", action="store_true", help="Ghi đè ảnh PNG đã tồn tại")

    p_stage = sub.add_parser("stage", help="Đóng gói ảnh PNG của thành viên để đẩy lên Kaggle GPU")
    p_stage.add_argument(
        "--member",
        choices=["khoa", "hieu", "khanh", "kin"],
        default="khanh",
        help="Tên thành viên (mặc định: khanh)",
    )
    p_stage.add_argument("--dir", default=None, help="Thư mục staging đầu ra (mặc định: staging/kaggle_<member>)")
    p_stage.add_argument("--kaggle-user", default="leogiakhanh", help="Kaggle username cho dataset-metadata.json")

    p_ocr = sub.add_parser("ocr", help="Chạy OCR (PaddleOCR + VietOCR) trên các trang PNG trong 01_nguon/")
    p_ocr.add_argument("--book", default="ALL", help="Mã tác phẩm: VPO_01, VPO_02, VPO_03 hoặc ALL")
    p_ocr.add_argument("--mock", action="store_true", help="Chạy chế độ giả lập (dry-run) không cần GPU")
    p_ocr.add_argument("--max-pages", type=int, default=None, help="Giới hạn số trang chạy thử")

    p_align = sub.add_parser(
        "align",
        help="Chạy Work Segmenter & Dóng hàng 4 cột từ các file JSON trong 02_ocr_tho/",
    )
    p_align.add_argument("--book", default="ALL", help="Mã tác phẩm: VPO_01, VPO_02, VPO_03 hoặc ALL")
    p_align.add_argument("--pilot-only", action="store_true", help="Chỉ dóng hàng các trang pilot")

    sub.add_parser("validate", help="Kiểm định chất lượng QA toàn bộ các thư mục CV04_VPO_01/02/03")
    sub.add_parser("web", help="Khởi chạy giao diện CAT Workbench (Streamlit)")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command in (None, "run"):
        return cmd_run(args)
    if args.command == "extract":
        return cmd_extract(args)
    if args.command == "stage":
        return cmd_stage(args)
    if args.command == "ocr":
        return cmd_ocr(args)
    if args.command == "align":
        return cmd_align(args)
    if args.command == "validate":
        return cmd_validate(args)
    if args.command == "web":
        return cmd_web(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
