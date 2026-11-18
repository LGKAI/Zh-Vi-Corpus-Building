"""Integration & unit tests for the End-to-End OCR-to-Alignment Pipeline."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from kaggle_ocr.ocr_pipeline_kaggle import group_layout_blocks, resolve_ocr_output_dirs
from scripts.run_end_to_end import run_end_to_end
from src.corpus_pipeline import run_corpus_from_ocr
from src.exporter_and_qa import read_tsv, read_xlsx_zero_dep


class TestEndToEndCorpusPipeline(unittest.TestCase):
    """Verify full end-to-end orchestration strictly from OCR JSON outputs."""

    def test_hvtt_four_column_and_facing_dich_tho_grouping(self) -> None:
        han_items = [
            {"bbox": [[100, 100], [900, 100], [900, 140], [100, 140]], "text": "鄭子產有疾"}
        ]
        viet_items = [
            {"bbox": [[100, 150], [900, 150], [900, 190], [100, 190]], "text": "Trịnh Tử Sản hữu tật", "role": "phien_am"},
            {"bbox": [[100, 200], [900, 200], [900, 240], [100, 240]], "text": "Trịnh Tử Sản ốm", "role": "dich_nghia_gloss"},
            {"bbox": [[100, 300], [900, 300], [900, 340], [100, 340]], "text": "DỊCH THƠ : Tử Sản lâm bệnh"},
        ]
        res_even = group_layout_blocks(han_items, viet_items, book_type="HVTT", page_num=12)
        self.assertEqual(res_even["dich_tho_lines"], ["Tử Sản lâm bệnh"])
        self.assertEqual(res_even["dich_nghia_lines"], ["Trịnh Tử Sản ốm"])

        # Final poem pages (>= 367) must strip Dich nghia while keeping Dich tho
        res_final = group_layout_blocks(han_items, viet_items, book_type="HVTT", page_num=368)
        self.assertEqual(res_final["dich_nghia_lines"], [])
        self.assertEqual(res_final["dich_tho_lines"], ["Tử Sản lâm bệnh"])

    def test_resolve_ocr_output_dirs_prevents_double_nesting(self) -> None:
        book_root = Path("/tmp/deliverables/HVTT_HanVanTinhTuy")
        han_dir, viet_dir = resolve_ocr_output_dirs(book_root, book_folder="HVTT_HanVanTinhTuy")
        self.assertEqual(han_dir, book_root / "02_ocr_tho" / "han")
        self.assertEqual(viet_dir, book_root / "02_ocr_tho" / "viet")

    def test_cross_page_buffering_in_sequential_alignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            ocr_han = tmp_root / "deliverables" / "TVLT2_ThoVanLyTran2" / "02_ocr_tho" / "han"
            ocr_viet = tmp_root / "deliverables" / "TVLT2_ThoVanLyTran2" / "02_ocr_tho" / "viet"
            ocr_han.mkdir(parents=True)
            ocr_viet.mkdir(parents=True)

            # Page 17 has only Classical Chinese; Page 18 has the Dịch nghĩa translation
            (ocr_han / "0017.json").write_text(json.dumps({
                "page_num": 17,
                "book_type": "TVLT2",
                "preprocess": {"effective_width": 2000},
                "items": [{"bbox": [[100, 100], [900, 100], [900, 140], [100, 140]], "text": "風打松關月照庭。"}],
            }), encoding="utf-8")
            (ocr_viet / "0017.json").write_text(json.dumps({
                "page_num": 17,
                "book_type": "TVLT2",
                "items": [],
            }), encoding="utf-8")

            (ocr_han / "0018.json").write_text(json.dumps({
                "page_num": 18,
                "book_type": "TVLT2",
                "preprocess": {"effective_width": 2000},
                "items": [],
            }), encoding="utf-8")
            (ocr_viet / "0018.json").write_text(json.dumps({
                "page_num": 18,
                "book_type": "TVLT2",
                "items": [
                    {"bbox": [[100, 200], [500, 200], [500, 240], [100, 240]], "text": "DỊCH NGHĨA :"},
                    {"bbox": [[100, 260], [1600, 260], [1600, 300], [100, 300]], "text": "Gió đập cổng thông, trăng chiếu trước sân."},
                ],
            }), encoding="utf-8")

            summary = run_corpus_from_ocr(
                workspace_root=tmp_root,
                ocr_root=tmp_root,
                book_filter="TVLT2",
                pilot_only=False,
            )
            tvlt_info = summary["books"]["TVLT2"]
            self.assertEqual(tvlt_info["pair_count"], 1)
            self.assertTrue(tvlt_info["is_valid"])
            self.assertTrue(tvlt_info["tsv_xlsx_identical"])
            rows = read_tsv(tvlt_info["tsv_path"])
            self.assertEqual(rows[0][0], "風打松關月照庭。")
            self.assertEqual(rows[0][1], "Gió đập cổng thông, trăng chiếu trước sân.")

    def test_run_end_to_end_pilot_mode(self) -> None:
        res = run_end_to_end(
            workspace_root=ROOT_DIR,
            pilot_only=True,
            run_downstream=False,
        )
        self.assertEqual(res["status"], "SUCCESS")
        books = res["alignment_stage"]["books"]
        for b_key in ("HVTT", "TVLT2", "TLTVN"):
            self.assertIn(b_key, books)
            self.assertTrue(books[b_key]["is_valid"])
            self.assertEqual(books[b_key]["error_rate"], 0.0)
            self.assertTrue(books[b_key]["tsv_xlsx_identical"])
            self.assertGreater(books[b_key]["pair_count"], 0)
            tsv_rows = read_tsv(books[b_key]["tsv_path"])
            xlsx_rows = read_xlsx_zero_dep(books[b_key]["xlsx_path"], sheet_name="DONG_HANG")
            self.assertEqual(tsv_rows, xlsx_rows)


if __name__ == "__main__":
    unittest.main()
