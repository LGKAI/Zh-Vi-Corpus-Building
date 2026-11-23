# CV04_VPO_01 — Hán Văn Tinh Túy (Lãng Nhân)

- **Nhóm**: `CV04` | **Mã tác phẩm**: `VPO_01`
- **Phạm vi**: Sách `1..375` (`PDF 7..381`, **375 trang OCR GPU** — đủ 4 thành viên)

## 1. Quy Trình & Công Cụ
- **`01_nguon/`**: Ảnh PNG 300 DPI trích bằng `PyMuPDF` (`src/pdf_extractor.py`). Sách song ngữ in chung file PDF (trang chẵn `Hán + Phiên âm + Dịch nghĩa`, trang lẻ `Dịch thơ` đối diện hoặc trang tiêu đề) nên lưu chung theo số trang PDF (`0007.png`...; ảnh bulk bỏ qua trong `.gitignore`).
- **`02_ocr_tho/`**: `PaddleOCR (chinese_cht)` cho chữ Hán + `VietOCR (vgg_transformer)` cho chữ Quốc ngữ (`375` cặp `han/*.json`, `viet/*.json`, `ocr_results.jsonl`, `ocr_run_summary.json`).
- **`03_text_sach/`**: `han.txt`, `viet.txt` (`UTF-8 NFC`), khử nhầm nét Hán theo `Phiên âm` (`src/ocr_disambiguator.py`), phóng chiếu dấu câu (`src/phonetic_verifier.py`), xuất đồng bộ từng dòng với file `.tsv`.
- **`04_dong_hang/`**: Dóng hàng 4 cột (`Hán - Dịch âm - Dịch nghĩa - Dịch thơ`) kèm dòng tiêu đề mỗi bài (`src/aligner.py`, `src/corpus_pipeline.py`); các bài không có dịch nghĩa (như *Thạch Hào lại*, *Thu dạ hoài ngâm*) để trống cột `Dịch nghĩa`.

## 2. Thống Kê QA (Toàn Bộ 375 Trang)
- **Tổng dòng dóng hàng**: `1.377` (`36` dòng tiêu đề, `1.111` dòng có `Dịch thơ`)
- **Số cặp hợp lệ**: `1.377` (`MISSING = 0`, `FORMAT_ERROR = 0`, `LEFTOVER_MARKER = 0`)
- **Cảnh báo QA**: `132` (`OMISSION: 40`, `ADDITION: 90`, `NUMBER_MISMATCH: 6`) $\rightarrow$ **Tỷ lệ lỗi: `9.59%`** (đạt $\le 30\%$)
- **Độ phủ Hán tự**: `55.07%` | **Điểm tin cậy**: `0.53 / 1.00` (`0.5325`) | **`TSV == XLSX`**: Khớp 100%
