# CV04_VPO_02 — Thể Loại Từ Việt Nam Thời Trung Đại (Phần Ba)

- **Nhóm**: `CV04` | **Mã tác phẩm**: `VPO_02`
- **Phạm vi**: Phần Ba, sách `127..540` (`PDF 134..547`, **414 trang OCR GPU**, **408 trang dóng hàng** sau khi loại 3 trang khuyết gốc `378..380` và 3 trang bảng Phụ lục đầu mục lục `545..547` — đủ 4 thành viên)

## 1. Quy Trình & Công Cụ
- **`01_nguon/`**: Ảnh PNG 300 DPI trích bằng `PyMuPDF` (`src/pdf_extractor.py`) do lớp text PDF bị mất chữ Hán; lưu theo số trang PDF (`0134.png`...; ảnh bulk bỏ qua trong `.gitignore`).
- **`02_ocr_tho/`**: `PaddleOCR (chinese_cht)` + `VietOCR (vgg_transformer)` có cắt 7% running header và phát hiện đường kẻ ngang tách chú thích chân trang (`414` cặp `han/*.json`, `viet/*.json`, `ocr_results.jsonl`, `ocr_run_summary.json`).
- **`03_text_sach/`**: `han.txt`, `viet.txt` (`UTF-8 NFC`), lọc chú thích/header, bảo toàn `[MASK]`/`□`, xuất đồng bộ từng dòng với file `.tsv`.
- **`04_dong_hang/`**: Phân đoạn bài & chùm liên hoàn từ bằng `src/work_segmenter.py`, dóng hàng 4 cột (`Hán` – `Dịch âm` – `Dịch nghĩa` – `Dịch thơ` [*Dịch theo nguyên điệu*]) kèm dòng tiêu đề mỗi bài (`src/corpus_pipeline.py`).

## 2. Thống Kê QA (Toàn Bộ Phần Ba)
- **Tổng dòng dóng hàng**: `2.170` (`175` dòng tiêu đề, `1.326` dòng có `Dịch thơ`, `2.164` dòng có `Dịch nghĩa`/`Dịch thơ`)
- **Số cặp hợp lệ**: `2.170` (`MISSING = 0`, `FORMAT_ERROR = 0`, `LEFTOVER_MARKER = 0`)
- **Cảnh báo QA**: `97` (`OMISSION: 74`, `ADDITION: 12`, `NUMBER_MISMATCH: 15`) $\rightarrow$ **Tỷ lệ lỗi: `4.47%`** (đạt $\le 30\%$)
- **Độ phủ Hán tự**: `48.12%` | **Điểm tin cậy**: `0.51 / 1.00` (`0.5104`) | **`TSV == XLSX`**: Khớp 100%
