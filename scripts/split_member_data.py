#!/usr/bin/env python3
"""Partition all 1,583 valid page images fairly across 4 team members (Khoa, Hieu, Khanh, Kin).

Ensures:
1. Balanced page counts (~394–397 pages per member across all 3 books).
2. HVTT facing even-odd pairs `(2k, 2k+1)` are never split apart across members.
3. Zero overlaps and 100% coverage of all extracted pages in `deliverables/*/01_nguon/*.png`.
4. One-command Kaggle staging per member (`--member <name> --stage`) and local shard export.

Usage:
    python3 scripts/split_member_data.py --verify
    python3 scripts/split_member_data.py --member khoa --stage
    python3 scripts/split_member_data.py --member hieu --stage
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.corpus_pipeline import load_book_manifest

MEMBERS: Tuple[Tuple[str, str], ...] = (
    ("khoa", "Khoa"),
    ("hieu", "Hiếu"),
    ("khanh", "Khánh"),
    ("kin", "Kin"),
)

BOOK_ORDER: Tuple[str, ...] = ("HVTT", "TVLT2", "TLTVN")


def _list_book_pages(source_dir: Path) -> List[int]:
    if not source_dir.is_dir():
        return []
    return sorted(int(p.stem) for p in source_dir.glob("*.png") if p.stem.isdigit())


def _chunk_list(items: List[int], num_parts: int) -> List[List[int]]:
    n = len(items)
    base, rem = divmod(n, num_parts)
    chunks: List[List[int]] = []
    idx = 0
    for i in range(num_parts):
        size = base + (1 if i < rem else 0)
        chunks.append(items[idx : idx + size])
        idx += size
    return chunks


def _chunk_hvtt_even_odd_pairs(pages: List[int], num_parts: int) -> List[List[int]]:
    """Keep `(even, odd)` facing page pairs together across member boundaries."""
    pairs: List[List[int]] = []
    i = 0
    while i < len(pages):
        if i + 1 < len(pages) and pages[i] % 2 == 0 and pages[i + 1] == pages[i] + 1:
            pairs.append([pages[i], pages[i + 1]])
            i += 2
        else:
            pairs.append([pages[i]])
            i += 1

    n = len(pairs)
    base, rem = divmod(n, num_parts)
    chunks: List[List[int]] = []
    idx = 0
    for part_idx in range(num_parts):
        size = base + (1 if part_idx < rem else 0)
        flat = [p for pair in pairs[idx : idx + size] for p in pair]
        chunks.append(flat)
        idx += size
    return chunks


def _pdf_to_book_page(book_key: str, pdf_page: int, book_cfg: Dict[str, Any]) -> int:
    offset = int(book_cfg.get("pdf_to_book_offset", 0))
    return pdf_page + offset


def build_member_splits(workspace_root: Path = ROOT_DIR) -> Dict[str, Any]:
    """Compute exact 4-member partition across HVTT, TVLT2, and TLTVN."""
    manifest = load_book_manifest(workspace_root / "config" / "book_manifest.json")
    books_cfg = manifest.get("books", {})

    per_book_chunks: Dict[str, List[List[int]]] = {}
    total_available_pages = 0

    for b_key in BOOK_ORDER:
        cfg = books_cfg[b_key]
        src_dir = workspace_root / cfg["source_dir"]
        pages = _list_book_pages(src_dir)
        total_available_pages += len(pages)
        if b_key == "HVTT":
            per_book_chunks[b_key] = _chunk_hvtt_even_odd_pairs(pages, len(MEMBERS))
        else:
            per_book_chunks[b_key] = _chunk_list(pages, len(MEMBERS))

    member_data: Dict[str, Any] = {}
    for m_idx, (m_id, m_display) in enumerate(MEMBERS):
        books_slice: Dict[str, Any] = {}
        member_total = 0
        for b_key in BOOK_ORDER:
            cfg = books_cfg[b_key]
            chunk = per_book_chunks[b_key][m_idx]
            member_total += len(chunk)
            pdf_start = chunk[0] if chunk else None
            pdf_end = chunk[-1] if chunk else None
            book_start = _pdf_to_book_page(b_key, pdf_start, cfg) if pdf_start is not None else None
            book_end = _pdf_to_book_page(b_key, pdf_end, cfg) if pdf_end is not None else None
            books_slice[b_key] = {
                "code": cfg["code"],
                "page_count": len(chunk),
                "pdf_page_start": pdf_start,
                "pdf_page_end": pdf_end,
                "book_page_start": book_start,
                "book_page_end": book_end,
                "pdf_pages": chunk,
            }
        member_data[m_id] = {
            "member_id": m_id,
            "display_name": m_display,
            "total_pages": member_total,
            "books": books_slice,
        }

    return {
        "project": "Hán–Việt Parallel Corpus (4-Member Workload Split)",
        "total_members": len(MEMBERS),
        "total_pages": total_available_pages,
        "members": member_data,
    }


def verify_splits(splits: Dict[str, Any], workspace_root: Path = ROOT_DIR) -> None:
    """Assert 100% coverage and zero overlap across all 4 members."""
    manifest = load_book_manifest(workspace_root / "config" / "book_manifest.json")
    books_cfg = manifest["books"]
    for b_key in BOOK_ORDER:
        expected = _list_book_pages(workspace_root / books_cfg[b_key]["source_dir"])
        seen: List[int] = []
        for m_id, _ in MEMBERS:
            seen.extend(splits["members"][m_id]["books"][b_key]["pdf_pages"])
        if len(seen) != len(set(seen)):
            raise AssertionError(f"Duplicate pages assigned in {b_key}!")
        if sorted(seen) != sorted(expected):
            raise AssertionError(
                f"Coverage mismatch in {b_key}: {len(seen)} assigned vs {len(expected)} expected."
            )


def write_splits_config_and_doc(splits: Dict[str, Any], workspace_root: Path = ROOT_DIR) -> Tuple[Path, Path]:
    cfg_path = workspace_root / "config" / "member_splits.json"
    cfg_path.write_text(json.dumps(splits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    notes_by_member = {
        "khoa": "- Gồm **Bài 3 `TVLT2`** (*Thiền tông chỉ nam tự*, PDF 25 trắng scan $\\rightarrow$ dùng file bổ sung GDrive).\n- `TLTVN`: Lưu ý PDF 138–140 (khuyết hạ phiến) & PDF 221–225 (khuyết 1 chữ `□`).",
        "hieu": "- `TLTVN`: Lưu ý PDF 303–304 (Phạm Nguyễn Du — khuyết hạ phiến trong bản gốc).",
        "khanh": "- `TVLT2`: Đã loại trừ sẵn 2 bài Chữ Nôm (*Cư trần lạc đạo phú*, *Đắc thú lâm tuyền*).\n- `TLTVN`: Lưu ý PDF 378–380 (4 bài Nôm Phạm Thái khuyết bản gốc Hán/Nôm — bỏ qua nếu chưa có bổ sung).",
        "kin": "- `HVTT`: Gồm **bài cuối** (*Thu dạ hoài ngâm*, PDF 368–381) $\\rightarrow$ giữ đủ 4 cột nhưng để trống cột `Dịch nghĩa`.\n- `TVLT2`: Đã loại trừ sẵn bài Chữ Nôm *Vịnh Vân-yên tự phú*.",
    }

    rows: List[str] = []
    detail_sections: List[str] = []
    for m_id, _ in MEMBERS:
        m = splits["members"][m_id]
        h = m["books"]["HVTT"]
        t2 = m["books"]["TVLT2"]
        tl = m["books"]["TLTVN"]
        rows.append(
            f"| **{m['display_name']}** (`{m_id}`) | "
            f"{h['page_count']} tr (`PDF {h['pdf_page_start']}–{h['pdf_page_end']}` / Sách `{h['book_page_start']}–{h['book_page_end']}`) | "
            f"{t2['page_count']} tr (`PDF {t2['pdf_page_start']}–{t2['pdf_page_end']}` / Sách `{t2['book_page_start']}–{t2['book_page_end']}`) | "
            f"{tl['page_count']} tr (`PDF {tl['pdf_page_start']}–{tl['pdf_page_end']}` / Sách `{tl['book_page_start']}–{tl['book_page_end']}`) | "
            f"**{m['total_pages']} trang** |"
        )
        detail_sections.append(
            f"### {m['display_name']} (`--member {m_id}` — {m['total_pages']} trang)\n"
            f"- **HVTT**: `PDF {h['pdf_page_start']:04d}..{h['pdf_page_end']:04d}` (Trang sách `{h['book_page_start']}..{h['book_page_end']}`, {h['page_count']} trang — tròn {h['page_count'] // 2} cặp chẵn/lẻ)\n"
            f"- **TVLT2**: `PDF {t2['pdf_page_start']:04d}..{t2['pdf_page_end']:04d}` (Trang sách `{t2['book_page_start']}..{t2['book_page_end']}`, {t2['page_count']} trang)\n"
            f"- **TLTVN**: `PDF {tl['pdf_page_start']:04d}..{tl['pdf_page_end']:04d}` (Trang sách `{tl['book_page_start']}..{tl['book_page_end']}`, {tl['page_count']} trang)\n"
            f"{notes_by_member[m_id]}\n\n"
            f"```bash\n"
            f"# Đóng gói đúng {m['total_pages']} trang của {m['display_name']} để đẩy lên Kaggle GPU chạy riêng:\n"
            f"python3 scripts/split_member_data.py --member {m_id} --stage /tmp/kaggle_{m_id}\n"
            f"bash kaggle_ocr/deploy_to_kaggle.sh --push-dataset /tmp/kaggle_{m_id} --push-kernel\n"
            f"```"
        )

    totals = [splits["members"][m_id]["total_pages"] for m_id, _ in MEMBERS]
    min_tp, max_tp = min(totals), max(totals)
    doc_content = f"""# BẢNG PHÂN CHIA DỮ LIỆU CHẠY SONG SONG CHO 4 THÀNH VIÊN
## Nhóm: Khoa – Hiếu – Khánh – Kin ({splits['total_pages']} trang hợp lệ / 3 bộ sách)

Để đảm bảo công bằng tuyệt đối về khối lượng (**{min_tp}–{max_tp} trang/người**, ước tính vượt ngưỡng **>= 2.000 cặp câu/người** theo Mục 1 của `Guideline.pdf`), đồng thời không cắt rời cặp trang đối diện trong *Hán Văn Tinh Túy* (`HVTT`), toàn bộ **1.583 trang PNG** được chia đều theo từng quyển như sau:

| Thành viên | `HVTT` (374 trang) | `TVLT2` (795 trang) | `TLTVN` (414 trang) | Tổng số trang |
| :--- | :--- | :--- | :--- | :---: |
{chr(10).join(rows)}

---

## Chi Tiết Phạm Vi & Lưu Ý Ngoại Lệ Cho Từng Thành Viên

{chr(10).join(detail_sections)}

---

## Quy Trình Tổng Hợp Sau Khi 4 Thành Viên Chạy Xong Kaggle

1. Tải kết quả OCR từ tài khoản Kaggle của từng thành viên (`bash kaggle_ocr/deploy_to_kaggle.sh --pull-output`) về `deliverables/<BOOK>/02_ocr_tho/{'{han,viet}'}/*.json`.
2. Gộp kiểm định và xuất toàn bộ `.tsv` + `.xlsx` 2 sheet cuối cùng chỉ bằng **1 lệnh**:
   ```bash
   python3 scripts/run_end_to_end.py --skip-ocr
   ```
"""
    doc_path = workspace_root / "docs" / "PHAN_CONG_4_THANH_VIEN.md"
    doc_path.write_text(doc_content, encoding="utf-8")
    return cfg_path, doc_path


def stage_member_dataset(
    member_id: str,
    staging_dir: Path,
    splits: Dict[str, Any],
    workspace_root: Path = ROOT_DIR,
) -> Path:
    """Stage exact member PNG subset + src/ + config/ into `staging_dir` for Kaggle upload."""
    if member_id not in splits["members"]:
        raise ValueError(f"Unknown member '{member_id}'. Expected one of: {list(splits['members'])}")

    member_info = splits["members"][member_id]
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    # Stage src/, config/, and metadata
    shutil.copytree(workspace_root / "src", staging_dir / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (staging_dir / "config").mkdir(parents=True, exist_ok=True)
    shutil.copy2(workspace_root / "config" / "book_manifest.json", staging_dir / "config" / "book_manifest.json")
    ds_meta = workspace_root / "kaggle_ocr" / "dataset-metadata.json"
    if ds_meta.is_file():
        meta = json.loads(ds_meta.read_text(encoding="utf-8"))
        meta["title"] = f"{meta.get('title', 'Han Viet Pages')} ({member_info['display_name']})"
        (staging_dir / "dataset-metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    # Copy Work 03 supplement for Khoa's TVLT2 shard
    supp_src = workspace_root / "deliverables" / "TVLT2_ThoVanLyTran2" / "01_nguon" / "bai_03_thien_tong_chi_nam_tu_dich_nghia.txt"
    if member_id == "khoa" and supp_src.is_file():
        supp_dst = staging_dir / "deliverables" / "TVLT2_ThoVanLyTran2" / "01_nguon" / supp_src.name
        supp_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(supp_src, supp_dst)

    linked_count = 0
    for b_key, b_slice in member_info["books"].items():
        code = b_slice["code"]
        src_dir = workspace_root / "deliverables" / code / "01_nguon"
        dst_dir = staging_dir / "deliverables" / code / "01_nguon"
        dst_dir.mkdir(parents=True, exist_ok=True)
        for p_num in b_slice["pdf_pages"]:
            src_file = src_dir / f"{int(p_num):04d}.png"
            if src_file.is_file():
                dst_file = dst_dir / src_file.name
                try:
                    os.link(src_file, dst_file)
                except OSError:
                    shutil.copy2(src_file, dst_file)
                linked_count += 1

    print(
        f"[split_member_data] Staged {linked_count} PNG page(s) for member '{member_info['display_name']}' "
        f"into {staging_dir}"
    )
    return staging_dir


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="4-Member Workload Splitter (Khoa, Hieu, Khanh, Kin).")
    parser.add_argument("--verify", action="store_true", help="Verify exact page coverage and zero overlap.")
    parser.add_argument("--member", choices=["khoa", "hieu", "khanh", "kin"], default=None, help="Target member shard.")
    parser.add_argument("--stage", nargs="?", const="", default=None, help="Stage member PNGs into folder for Kaggle.")
    args = parser.parse_args(argv)

    splits = build_member_splits(ROOT_DIR)
    verify_splits(splits, ROOT_DIR)
    cfg_path, doc_path = write_splits_config_and_doc(splits, ROOT_DIR)

    if args.member and args.stage is not None:
        target = Path(args.stage) if args.stage else Path(f"/tmp/kaggle_{args.member}")
        stage_member_dataset(args.member, target, splits, ROOT_DIR)
        return 0

    summary = {
        "status": "VERIFIED",
        "total_pages": splits["total_pages"],
        "config_file": str(cfg_path),
        "doc_file": str(doc_path),
        "members": {
            m_id: {
                "display_name": info["display_name"],
                "total_pages": info["total_pages"],
                "HVTT": f"{info['books']['HVTT']['pdf_page_start']}..{info['books']['HVTT']['pdf_page_end']} ({info['books']['HVTT']['page_count']}p)",
                "TVLT2": f"{info['books']['TVLT2']['pdf_page_start']}..{info['books']['TVLT2']['pdf_page_end']} ({info['books']['TVLT2']['page_count']}p)",
                "TLTVN": f"{info['books']['TLTVN']['pdf_page_start']}..{info['books']['TLTVN']['pdf_page_end']} ({info['books']['TLTVN']['page_count']}p)",
            }
            for m_id, info in splits["members"].items()
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
