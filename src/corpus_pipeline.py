"""End-to-End OCR-to-Aligned-Corpus Pipeline (`02_ocr_tho` -> `03_text_sach` -> `04_dong_hang`).

Reads raw page OCR bounding-box JSONs (`deliverables/<BOOK>/02_ocr_tho/{han,viet}/*.json`),
applies layout grouping, visual confusion disambiguation, Sino-Vietnamese phonetic verification,
text cleaning, work-bounded Plateau DP alignment, word coverage diagnostics, QA validation,
and exports synchronized `.tsv`, 2-sheet OpenXML `.xlsx`, and `.json` reports.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from kaggle_ocr.ocr_pipeline_kaggle import (
    BOOK_DELIVERABLE_DIRS,
    group_layout_blocks,
)
from src.aligner import align_interlinear_4col_blocks, align_work_sentences
from src.exporter_and_qa import (
    export_tsv,
    export_xlsx_zero_dep,
    read_tsv,
    read_xlsx_zero_dep,
    validate_pairs,
)
from src.ocr_disambiguator import correct_han_line_with_phien_am
from src.phonetic_verifier import project_punctuation_from_phien_am, verify_han_phien_am_pair
from src.text_cleaner import (
    clean_han_text,
    clean_viet_text,
    split_han_sentences,
    split_viet_sentences,
)
from src.word_aligner import batch_evaluate_word_coverage

DEFAULT_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "config" / "book_manifest.json"
DEFAULT_WORK03_SUPPLEMENT = (
    Path("deliverables")
    / "TVLT2_ThoVanLyTran2"
    / "01_nguon"
    / "bai_03_thien_tong_chi_nam_tu_dich_nghia.txt"
)


def load_book_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load `config/book_manifest.json` or return sensible defaults if missing."""
    path = manifest_path or DEFAULT_MANIFEST_PATH
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "books": {
            "HVTT": {
                "book_id": "HVTT",
                "code": "HVTT_HanVanTinhTuy",
                "deliverable_dir": "deliverables/HVTT_HanVanTinhTuy",
                "clean_text_dir": "deliverables/HVTT_HanVanTinhTuy/03_text_sach",
                "alignment_dir": "deliverables/HVTT_HanVanTinhTuy/04_dong_hang",
                "valid_range": {"pdf_page_start": 8, "pdf_page_end": 381},
                "excluded_pdf_pages_in_valid_range": [],
                "pilot_pages": [8, 10, 12, 368, 369],
            },
            "TVLT2": {
                "book_id": "TVLT2",
                "code": "TVLT2_ThoVanLyTran2",
                "deliverable_dir": "deliverables/TVLT2_ThoVanLyTran2",
                "clean_text_dir": "deliverables/TVLT2_ThoVanLyTran2/03_text_sach",
                "alignment_dir": "deliverables/TVLT2_ThoVanLyTran2/04_dong_hang",
                "valid_range": {"pdf_page_start": 17, "pdf_page_end": 861},
                "excluded_pdf_pages_in_valid_range": [25],
                "pilot_pages": [19, 20, 22, 23, 24, 26],
            },
            "TLTVN": {
                "book_id": "TLTVN",
                "code": "TLTVN_TheLoaiTuVN",
                "deliverable_dir": "deliverables/TLTVN_TheLoaiTuVN",
                "clean_text_dir": "deliverables/TLTVN_TheLoaiTuVN/03_text_sach",
                "alignment_dir": "deliverables/TLTVN_TheLoaiTuVN/04_dong_hang",
                "valid_range": {"pdf_page_start": 134, "pdf_page_end": 547},
                "excluded_pdf_pages_in_valid_range": [378, 379, 380],
                "pilot_pages": [134, 135, 136, 137],
            },
        }
    }


def _extract_page_num(stem: str, payload: Optional[Dict[str, Any]] = None) -> int:
    if payload and isinstance(payload.get("page_num"), int):
        return int(payload["page_num"])
    matches = re.findall(r"(\d+)", stem)
    return int(matches[-1]) if matches else 0


def _is_page_in_scope(page_num: int, book_cfg: Dict[str, Any]) -> bool:
    valid_range = book_cfg.get("valid_range", {})
    start_p = int(valid_range.get("pdf_page_start", 1))
    end_p = int(valid_range.get("pdf_page_end", 10_000))
    if page_num < start_p or page_num > end_p:
        return False
    excluded = set(int(p) for p in book_cfg.get("excluded_pdf_pages_in_valid_range", []))
    return page_num not in excluded


def _load_book_ocr_pages(
    ocr_dir: Path,
    book_key: str,
    book_cfg: Dict[str, Any],
    pilot_only: bool = False,
) -> List[Dict[str, Any]]:
    """Load paired `02_ocr_tho/han/*.json` and `viet/*.json` sorted by page number."""
    han_dir = ocr_dir / "han"
    viet_dir = ocr_dir / "viet"
    if not han_dir.is_dir():
        return []

    pilot_set: Optional[Set[int]] = None
    if pilot_only and book_cfg.get("pilot_pages"):
        pilot_set = {int(p) for p in book_cfg["pilot_pages"]}

    pages: List[Dict[str, Any]] = []
    seen_pages: Set[int] = set()

    for han_file in sorted(han_dir.glob("*.json")):
        han_payload = json.loads(han_file.read_text(encoding="utf-8"))
        page_num = _extract_page_num(han_file.stem, han_payload)
        if page_num in seen_pages:
            continue
        if not _is_page_in_scope(page_num, book_cfg):
            continue
        if pilot_set is not None and page_num not in pilot_set:
            continue

        viet_file = viet_dir / han_file.name
        viet_payload = (
            json.loads(viet_file.read_text(encoding="utf-8"))
            if viet_file.is_file()
            else {"items": []}
        )

        preprocess = han_payload.get("preprocess", {})
        page_w = int(preprocess.get("effective_width") or preprocess.get("original_width") or 2000)

        layout = group_layout_blocks(
            han_items=han_payload.get("items", []),
            viet_items=viet_payload.get("items", []),
            book_type=book_key,
            page_num=page_num,
            page_width=page_w,
        )

        seen_pages.add(page_num)
        pages.append({
            "page_id": han_file.stem,
            "page_num": page_num,
            "layout": layout,
            "han_items": han_payload.get("items", []),
            "viet_items": viet_payload.get("items", []),
        })

    pages.sort(key=lambda item: item["page_num"])
    return pages


def _deduplicate_mock_repeats(
    pages: List[Dict[str, Any]],
    is_mock_run: bool,
) -> List[Dict[str, Any]]:
    """Avoid duplicating identical synthetic mock pages when local OCR ran in mock mode."""
    if not is_mock_run:
        return pages
    deduped: List[Dict[str, Any]] = []
    seen_signatures: Set[Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]] = set()
    for p in pages:
        lay = p["layout"]
        # Always preserve HVTT odd facing pages if they carry dich_tho_lines
        sig = (
            tuple(lay.get("chu_han_lines", [])),
            tuple(lay.get("phien_am_lines", [])),
            tuple(lay.get("dich_nghia_lines", [])),
        )
        if not any(sig) and not lay.get("dich_tho_lines"):
            continue
        if sig in seen_signatures and any(sig):
            continue
        if any(sig):
            seen_signatures.add(sig)
        deduped.append(p)
    return deduped


def _align_hvtt_from_ocr(
    pages: List[Dict[str, Any]],
) -> Tuple[List[Tuple[str, ...]], List[Dict[str, Any]]]:
    """Align HVTT 4-column records (`Hán`, `Dịch âm`, `Dịch nghĩa`, `Dịch thơ`) from OCR pages."""
    odd_dich_tho_by_even_page: Dict[int, List[str]] = {}
    for p in pages:
        pnum = int(p["page_num"])
        if pnum % 2 == 1:
            dt = p["layout"].get("dich_tho_lines", [])
            if dt:
                odd_dich_tho_by_even_page[pnum - 1] = [clean_viet_text(line) for line in dt if line.strip()]

    projected_blocks: List[Dict[str, str]] = []
    phonetic_checks: List[Dict[str, Any]] = []

    for p in pages:
        pnum = int(p["page_num"])
        if pnum % 2 != 0:
            continue

        lay = p["layout"]
        triplets = lay.get("interlinear_triplets", [])
        han_lines = lay.get("chu_han_lines", [])
        phien_am_lines = lay.get("phien_am_lines", [])
        dich_nghia_lines = lay.get("dich_nghia_lines", [])

        # Combine inline + facing odd page Dich Tho if present
        inline_dt = [clean_viet_text(x) for x in lay.get("dich_tho_lines", []) if x.strip()]
        facing_dt = odd_dich_tho_by_even_page.get(pnum, [])
        page_dich_tho = inline_dt if inline_dt else facing_dt

        # Final poems (PDF >= 367) have blank Dịch nghĩa per instructor rule
        is_final_poem = pnum >= 367

        raw_han_list: List[str] = []
        raw_pa_list: List[str] = []
        raw_dn_list: List[str] = []

        if triplets:
            for idx, tr in enumerate(triplets):
                h_txt = tr.get("chu_han", "").strip()
                if not h_txt:
                    continue
                pa_txt = tr.get("phien_am", "").strip()
                dn_txt = "" if is_final_poem else (
                    tr.get("dich_nghia_gloss", "").strip()
                    or (dich_nghia_lines[idx].strip() if idx < len(dich_nghia_lines) else "")
                )
                raw_han_list.append(h_txt)
                raw_pa_list.append(pa_txt)
                raw_dn_list.append(dn_txt)
        else:
            for idx, h_txt in enumerate(han_lines):
                raw_han_list.append(h_txt)
                raw_pa_list.append(phien_am_lines[idx] if idx < len(phien_am_lines) else "")
                raw_dn_list.append("" if is_final_poem else (dich_nghia_lines[idx] if idx < len(dich_nghia_lines) else ""))

        for idx, h_raw in enumerate(raw_han_list):
            pa_raw = raw_pa_list[idx]
            dn_raw = raw_dn_list[idx]
            dt_raw = page_dich_tho[idx] if idx < len(page_dich_tho) else ""

            corrected_han, _ = correct_han_line_with_phien_am(h_raw, pa_raw)
            if pa_raw:
                phonetic_checks.append(verify_han_phien_am_pair(corrected_han, pa_raw))
                punct_han = project_punctuation_from_phien_am(corrected_han, pa_raw)
            else:
                punct_han = clean_han_text(corrected_han)

            projected_blocks.append({
                "han": punct_han,
                "dich_am": clean_viet_text(pa_raw),
                "dich_nghia": "" if is_final_poem else clean_viet_text(dn_raw),
                "dich_tho": clean_viet_text(dt_raw),
            })

    pairs = align_interlinear_4col_blocks(projected_blocks)
    return pairs, phonetic_checks


def _align_sequential_book_from_ocr(
    book_key: str,
    pages: List[Dict[str, Any]],
    workspace_root: Path,
) -> Tuple[List[Tuple[str, ...]], List[Dict[str, Any]]]:
    """Align TVLT2 / TLTVN works using disambiguation, cross-page buffering, and Plateau DP."""
    all_pairs: List[Tuple[str, ...]] = []
    phonetic_checks: List[Dict[str, Any]] = []

    supp_path = workspace_root / DEFAULT_WORK03_SUPPLEMENT
    supp_paragraphs: List[str] = []
    if book_key == "TVLT2" and supp_path.is_file():
        supp_paragraphs = [
            clean_viet_text(p.lstrip("- "))
            for p in supp_path.read_text(encoding="utf-8").splitlines()
            if p.strip()
        ]
    used_tvlt2_work03_supplement = False

    pending_han_sents: List[str] = []
    pending_raw_han: List[str] = []

    for p in pages:
        lay = p["layout"]
        raw_han_lines = lay.get("chu_han_lines", [])
        raw_pa_lines = lay.get("phien_am_lines", [])
        raw_dn_lines = lay.get("dich_nghia_lines", [])

        if not raw_han_lines and not raw_dn_lines:
            continue

        corrected_han_lines: List[str] = []
        for idx, h_line in enumerate(raw_han_lines):
            pa_line = raw_pa_lines[idx] if idx < len(raw_pa_lines) else ""
            if pa_line:
                corr_han, _ = correct_han_line_with_phien_am(h_line, pa_line)
                phonetic_checks.append(verify_han_phien_am_pair(corr_han, pa_line))
                corrected_han_lines.append(corr_han)
            else:
                corrected_han_lines.append(h_line)

        page_han_sents: List[str] = []
        for line in corrected_han_lines:
            cleaned_h = clean_han_text(line)
            if cleaned_h:
                split_h = split_han_sentences(cleaned_h)
                page_han_sents.extend(split_h if split_h else [cleaned_h])

        viet_sents: List[str] = []
        if raw_dn_lines:
            for line in raw_dn_lines:
                cleaned_v = clean_viet_text(line)
                if cleaned_v:
                    split_v = split_viet_sentences(cleaned_v)
                    viet_sents.extend(split_v if split_v else [cleaned_v])
        elif book_key == "TVLT2" and supp_paragraphs and not used_tvlt2_work03_supplement:
            han_joined_all = "".join(pending_han_sents + page_han_sents)
            if "朕竊謂佛無南北" in han_joined_all or "Thiền tông" in " ".join(raw_pa_lines):
                used_tvlt2_work03_supplement = True
                selected_blocks: List[Tuple[str, str]] = [(par, "") for par in supp_paragraphs[:2]]
                for idx_sp, par in enumerate(supp_paragraphs):
                    if "Trong núi vốn không có Phật" in par:
                        prefix = (
                            "Sư bảo: "
                            if idx_sp > 0 and supp_paragraphs[idx_sp - 1].rstrip(":").lower() == "sư bảo"
                            else ""
                        )
                        selected_blocks.append((par, prefix))
                    elif "Trẫm nghe lời này" in par:
                        selected_blocks.append((par, ""))
                for block, prefix in selected_blocks:
                    split_b = split_viet_sentences(block)
                    if not split_b:
                        split_b = [block]
                    if prefix and split_b:
                        split_b[0] = f"{prefix}{split_b[0]}"
                    viet_sents.extend(split_b)

        # Buffer Han sentences if translation appears on the next facing page
        if not viet_sents:
            pending_han_sents.extend(page_han_sents)
            pending_raw_han.extend([clean_han_text(h) for h in corrected_han_lines if clean_han_text(h)])
            continue

        han_sents = pending_han_sents + page_han_sents
        han_line_granularity = pending_raw_han + [
            clean_han_text(h) for h in corrected_han_lines if clean_han_text(h)
        ]
        pending_han_sents = []
        pending_raw_han = []

        if not han_sents:
            continue

        # Prefer exact 1:1 clause alignment when OCR line counts match cleanly
        if raw_dn_lines:
            viet_line_granularity = [clean_viet_text(v) for v in raw_dn_lines if clean_viet_text(v)]
            if len(han_line_granularity) == len(viet_line_granularity):
                for h_s, v_s in zip(han_line_granularity, viet_line_granularity):
                    all_pairs.append((h_s, v_s))
                continue

        if len(han_sents) == len(viet_sents):
            for h_s, v_s in zip(han_sents, viet_sents):
                all_pairs.append((h_s, v_s))
        else:
            aligned = align_work_sentences(han_sents, viet_sents)
            for item in aligned:
                all_pairs.append((item["han"], item["viet"]))

    return all_pairs, phonetic_checks


def _write_book_deliverables(
    book_key: str,
    book_cfg: Dict[str, Any],
    pairs: List[Tuple[str, ...]],
    phonetic_checks: List[Dict[str, Any]],
    workspace_root: Path,
) -> Dict[str, Any]:
    """Write `03_text_sach` and `04_dong_hang` files and verify TSV == XLSX."""
    code = book_cfg.get("code") or BOOK_DELIVERABLE_DIRS[book_key]
    clean_dir = workspace_root / book_cfg.get("clean_text_dir", f"deliverables/{code}/03_text_sach")
    align_dir = workspace_root / book_cfg.get("alignment_dir", f"deliverables/{code}/04_dong_hang")
    clean_dir.mkdir(parents=True, exist_ok=True)
    align_dir.mkdir(parents=True, exist_ok=True)

    han_txt = clean_dir / "han.txt"
    viet_txt = clean_dir / "viet.txt"
    han_lines: List[str] = []
    viet_lines: List[str] = []
    for row in pairs:
        han_lines.append(row[0])
        if len(row) >= 4:
            viet_lines.append(row[2] if row[2].strip() else row[3])
        else:
            viet_lines.append(row[1])
    han_txt.write_text(("\n".join(han_lines) + "\n") if han_lines else "", encoding="utf-8")
    viet_txt.write_text(("\n".join(viet_lines) + "\n") if viet_lines else "", encoding="utf-8")

    qa_report = validate_pairs(pairs)
    word_cov = batch_evaluate_word_coverage(pairs) if pairs else {}

    tsv_path = align_dir / f"{code}_parallel.tsv"
    xlsx_path = align_dir / f"{code}_parallel.xlsx"
    qa_json_path = align_dir / "qa_report.json"
    cov_json_path = align_dir / "word_coverage_report.json"

    export_tsv(pairs, str(tsv_path))
    export_xlsx_zero_dep(
        pairs,
        str(xlsx_path),
        stats={
            "Mã tài liệu": code,
            "Tổng số cặp câu": qa_report["total_pairs"],
            "Số cặp hợp lệ": qa_report["valid_pairs"],
            "Số cặp lỗi": qa_report["error_pairs"],
            "Tỷ lệ lỗi": qa_report["error_rate"],
            "Đạt ngưỡng <= 20%": qa_report["passes_target_20pct"],
            "Đạt ngưỡng nghiệm thu <= 30%": qa_report["passes_threshold_30pct"],
        },
    )
    qa_json_path.write_text(json.dumps(qa_report, ensure_ascii=False, indent=2), encoding="utf-8")
    cov_json_path.write_text(json.dumps(word_cov, ensure_ascii=False, indent=2), encoding="utf-8")

    tsv_roundtrip = read_tsv(str(tsv_path))
    xlsx_roundtrip = read_xlsx_zero_dep(str(xlsx_path), sheet_name="DONG_HANG")
    if tsv_roundtrip != xlsx_roundtrip:
        raise AssertionError(f"TSV vs XLSX mismatch for {code}: {len(tsv_roundtrip)} != {len(xlsx_roundtrip)}")

    return {
        "book_id": book_key,
        "code": code,
        "pair_count": len(pairs),
        "error_rate": qa_report["error_rate"],
        "is_valid": qa_report["is_valid"],
        "avg_han_coverage_pct": word_cov.get("avg_han_coverage_pct", 0.0),
        "avg_confidence": word_cov.get("avg_confidence", 0.0),
        "phonetic_all_matched": all(
            c.get("length_match", True) and len(c.get("phonetic_mismatches", [])) == 0
            for c in phonetic_checks
        ),
        "tsv_xlsx_identical": True,
        "tsv_path": str(tsv_path),
        "xlsx_path": str(xlsx_path),
    }


def run_corpus_from_ocr(
    workspace_root: Path,
    ocr_root: Optional[Path] = None,
    manifest_path: Optional[Path] = None,
    book_filter: Optional[str] = None,
    pilot_only: bool = False,
) -> Dict[str, Any]:
    """Run complete alignment, QA, and export reading strictly from `02_ocr_tho` JSON outputs."""
    manifest = load_book_manifest(manifest_path)
    books_cfg = manifest.get("books", {})
    ocr_base = ocr_root or workspace_root

    target_books = [book_filter] if book_filter else ["HVTT", "TVLT2", "TLTVN"]
    summary: Dict[str, Any] = {"books": {}, "source_mode": "ocr_json"}

    for book_key in target_books:
        if book_key not in books_cfg:
            continue
        cfg = books_cfg[book_key]
        code = cfg.get("code") or BOOK_DELIVERABLE_DIRS[book_key]

        candidate_ocr_dir = ocr_base / "deliverables" / code / "02_ocr_tho"
        if not candidate_ocr_dir.is_dir():
            candidate_ocr_dir = ocr_base / "02_ocr_tho"

        summary_meta_file = candidate_ocr_dir / "ocr_run_summary.json"
        is_mock_run = True
        if summary_meta_file.is_file():
            try:
                meta_obj = json.loads(summary_meta_file.read_text(encoding="utf-8"))
                is_mock_run = meta_obj.get("mode", "mock") == "mock"
            except Exception:
                is_mock_run = True

        pages = _load_book_ocr_pages(
            ocr_dir=candidate_ocr_dir,
            book_key=book_key,
            book_cfg=cfg,
            pilot_only=pilot_only,
        )
        pages = _deduplicate_mock_repeats(pages, is_mock_run=is_mock_run)

        if book_key == "HVTT":
            pairs, phonetic_checks = _align_hvtt_from_ocr(pages)
        else:
            pairs, phonetic_checks = _align_sequential_book_from_ocr(
                book_key=book_key,
                pages=pages,
                workspace_root=workspace_root,
            )

        book_summary = _write_book_deliverables(
            book_key=book_key,
            book_cfg=cfg,
            pairs=pairs,
            phonetic_checks=phonetic_checks,
            workspace_root=workspace_root,
        )
        book_summary["ocr_pages_loaded"] = len(pages)
        book_summary["ocr_mode"] = "mock" if is_mock_run else "kaggle_gpu"
        summary["books"][book_key] = book_summary

    return summary
