# CV04_VPO_03 — Thơ Văn Lý – Trần (Tập II – Quyển Thượng)

- **Nhóm**: `CV04` | **Mã tác phẩm**: `VPO_03`
- **Phạm vi**: Sách `19..863` (`PDF 17..861`, **795 trang OCR GPU**, loại trang trắng `PDF 25` và 4 bài Chữ Nôm `493..525`, `688..703`, `862..873` — đủ 4 thành viên)

## 1. Quy Trình & Công Cụ
- **`01_nguon/`**: Ảnh PNG 300 DPI trích bằng `PyMuPDF` (`src/pdf_extractor.py`, lưu theo số trang PDF; ảnh bulk bỏ qua trong `.gitignore`), kèm file bổ sung trang 25 trắng `bai_03_thien_tong_chi_nam_tu_dich_nghia.txt` do chị Lưu Như cung cấp.
- **`02_ocr_tho/`**: `PaddleOCR (chinese_cht)` + `VietOCR (vgg_transformer)`, tự động dừng trước `KHẢO ĐÍNH`, `CHÚ THÍCH`, `LỜI BÀN` (`795` cặp `han/*.json`, `viet/*.json`, `ocr_results.jsonl`, `ocr_run_summary.json`).
- **`03_text_sach/`**: `han.txt`, `viet.txt` (`UTF-8 NFC`), lọc chú thích/header, bảo toàn `[MASK]`/`□`, xuất đồng bộ từng dòng với file `.tsv`.
- **`04_dong_hang/`**: Phân đoạn tác phẩm xuyên trang bằng `src/work_segmenter.py` (thơ 2 cột, văn xuôi/biền ngẫu, bài kèm kệ, *Niêm tụng kệ*), tách mệnh đề song hành và dóng hàng 4 cột (`Hán - Dịch âm - Dịch nghĩa - Dịch thơ`) kèm dòng tiêu đề mỗi bài; bài văn xuôi không có dịch thơ để trống cột `Dịch thơ`.

## 2. Thống Kê QA (Toàn Bộ 795 Trang)
- **Tổng dòng dóng hàng**: `4.663` (`284` dòng tiêu đề, `1.432` dòng có `Dịch thơ`)
- **Số cặp hợp lệ**: `4.663` (`MISSING = 0`, `FORMAT_ERROR = 0`, `LEFTOVER_MARKER = 0`)
- **Cảnh báo QA**: `396` (`OMISSION: 171`, `ADDITION: 137`, `NUMBER_MISMATCH: 100`) $\rightarrow$ **Tỷ lệ lỗi: `8.49%`** (đạt $\le 30\%$)
- **Độ phủ Hán tự**: `44.67%` | **Điểm tin cậy**: `0.49 / 1.00` (`0.4887`) | **`TSV == XLSX`**: Khớp 100%
