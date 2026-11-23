# Kiểm Kê Nguồn Dữ Liệu Song Ngữ Hán – Việt (Nhóm CV04 — Bước 1 & 2)

Đối chiếu theo [`Hướng dẫn dóng hàng Hán-Việt.pdf`](H%C6%B0%E1%BB%9Bng%20d%E1%BA%ABn%20d%C3%B3ng%20h%C3%A0ng%20H%C3%A1n-Vi%E1%BB%87t.pdf) và phân công `CV04` (`raw_data/Thông tin dữ liệu.png`).

## 1. Bảng Kiểm Kê 3 Bộ Sách

| Trường | `CV04_VPO_01` (`VPO_01`) | `CV04_VPO_02` (`VPO_02`) | `CV04_VPO_03` (`VPO_03`) |
| :--- | :--- | :--- | :--- |
| **Tên tài liệu** | *Hán Văn Tinh Túy* (Lãng Nhân) | *Thể loại từ VN thời trung đại* (Phạm Văn Ánh / Nguyễn Xuân Diện – Nguyễn Quảng Tuân) | *Thơ văn Lý – Trần Tập II* (Nguyễn Huệ Chi chủ biên) |
| **Tệp gốc (`raw_data/`)** | `Hán văn tinh tuý - Lãng Nhân.pdf` | `Thể loại từ VN thời trung đại - Phạm Văn Ánh.pdf` | `Thơ văn Lý-Trần tập 2 - Nguyễn Huệ Chi.pdf` |
| **Định dạng** | PDF Scan (`386` tr) | PDF Scan (`645` tr, text layer lỗi chữ Hán) | PDF Scan (`965` tr) |
| **Phạm vi hợp lệ** | Sách `1..375` (`PDF 7..381`, **`375` tr**, gồm trang chẵn Hán–âm–nghĩa & trang lẻ tiêu đề/Dịch thơ) | Phần Ba, sách `127..540` (`PDF 134..547`, **`414` tr**; trừ `378..380` khuyết gốc còn `411` tr dóng hàng) | Sách `19..863` (`PDF 17..861`, **`795` tr**, loại trang trắng `PDF 25` & 4 bài Chữ Nôm `493..525`, `688..703`, `862..873`) |
| **Công thức lệch trang** | `pdf_page = book_page + 6` | `pdf_page = book_page + 7` *(sách `1..593`)* | `book_page = pdf_page + 2` *(từ `PDF 7`)* |
| **Ghi chú xử lý** | Bài *Thạch Hào lại* (`PDF 100`) & *Thu dạ hoài ngâm* (`PDF 367..381`) để trống cột `Dịch nghĩa` | Bỏ Phần 1–2 (`PDF 8..133`) & Phụ lục (`PDF 548..645`); chi tiết khuyết gốc ở [`2_THONG_KE_BO_SUNG.md`](2_THONG_KE_BO_SUNG.md) | Bổ sung bản dịch nghĩa bài 3 (*Thiền tông chỉ nam tự*) bù trang 25 trắng từ file của chị Lưu Như |

## 2. Quy Chuẩn Đầu Ra Đã Thống Nhất
- **Cấu trúc 4 cột**: `Hán` – `Dịch âm` – `Dịch nghĩa` – `Dịch thơ`, có dòng tiêu đề riêng trước mỗi bài; cột khuyết để `""`.
- **Chữ mờ/khuyết**: Bảo toàn `[MASK]` / `□`.
- **Cấu trúc mỗi thư mục `CV04_VPO_01..03/`**: `01_nguon/` (ảnh 300 DPI), `02_ocr_tho/{han,viet}/` (JSON OCR thô), `03_text_sach/{han,viet}.txt` (UTF-8 NFC, toàn bộ bài trong 1 file), `04_dong_hang/<MA>_parallel.{tsv,xlsx}` + `qa_report.json` + `word_coverage_report.json`, và `README.md`.
