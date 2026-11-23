# Xây dựng Ngữ liệu Song hành Hán - Việt (CV04_VPO_03 - VPO_03)

**Học phần:** Xử lý Ngôn ngữ Tự nhiên (NLP)  
**Mã nhóm:** `CV04` (Trần Trung Hiếu, Lê Gia Khánh, Phạm Chấn Khoa, Cái Hoàng Bảo Kin)  
**Mã tác phẩm:** `VPO_03` (`CV04_VPO_03`)  
**Tác phẩm:** *Thơ văn Lý – Trần (Tập II – Quyển Thượng)* — Nguyễn Huệ Chi (chủ biên)  
**Phạm vi dữ liệu trên nhánh `khanh`:** `199` trang phân công của Khánh (`PDF 416..492, 526..647`, đã trừ 2 bài Chữ Nôm `493..525`) + `9` trang pilot (`PDF 19, 20, 22, 23, 24, 26, 38, 40, 42`) = `208` trang OCR GPU (kèm bản dịch nghĩa bổ sung trang 25 trắng tại `01_nguon/bai_03_thien_tong_chi_nam_tu_dich_nghia.txt`).

---

### 1. Phương pháp và Công cụ thực hiện (Tools & Methods)

* **Trích xuất nguồn dữ liệu (`01_nguon/`):**
  * Do bản Hán và bản dịch Việt nằm trong cùng file PDF (bố cục 2 cột song song cho thơ hoặc tuần tự cho văn xuôi), ảnh trang sách được trích xuất ở chuẩn **300 DPI** bằng `PyMuPDF (fitz)` (`src/pdf_extractor.py`) và lưu tại `01_nguon/<so_trang>.png` (các ảnh bulk được `.gitignore` loại trừ khỏi Git; chỉ track ảnh pilot trên Git), kèm file bổ sung trang 25 trắng `bai_03_thien_tong_chi_nam_tu_dich_nghia.txt`.
* **Nhận dạng ký tự quang học (`02_ocr_tho/`):**
  * Chữ Hán phồn thể: **PaddleOCR (`chinese_cht`)** kết hợp hiệu chỉnh nhập nhằng thị giác qua neo ngữ âm Hán–Việt (`src/ocr_disambiguator.py`).
  * Chữ Quốc ngữ (Phiên âm, Dịch nghĩa, Dịch thơ): **VietOCR (`vgg_transformer`)**, tự động dừng trước các mục `KHẢO ĐÍNH`, `CHÚ THÍCH`, `LỜI BÀN`.
  * Kết quả OCR thô từng trang lưu tại `02_ocr_tho/han/*.json`, `02_ocr_tho/viet/*.json`, kèm `ocr_results.jsonl` và `ocr_run_summary.json`.
* **Làm sạch và Chuẩn hóa văn bản (`03_text_sach/`):**
  * Chuẩn hóa bảng mã Unicode **UTF-8 NFC**, lọc bỏ header/footer, số trang và ký hiệu chú thích (`[1]`, `1*`, `(1)`), bảo toàn ký hiệu khuyết chữ `[MASK]` / `□` (`src/text_cleaner.py`). *(Lưu ý: OCR thô hiện vẫn còn ký hiệu `□`/`口` ở 1 dòng văn bia bị mờ chữ, cần đổi sang `[MASK]` ở bước hậu kiểm cuối.)*
  * Toàn bộ tác phẩm của cuốn sách lưu chung trong `han.txt` và `viet.txt`, xuất đồng bộ từng dòng với `04_dong_hang/VPO_03_parallel.tsv` (mở đầu mỗi bài bằng dòng tiêu đề riêng).
* **Dóng hàng song ngữ 4 cột (`04_dong_hang/`):**
  * Phân đoạn tác phẩm xuyên trang bằng `src/work_segmenter.py` (xử lý thơ 2 cột, văn xuôi, bài có kệ kèm theo, và *Niêm tụng kệ*), dóng hàng bằng Quy hoạch động Gale-Church + neo từ vựng (`src/aligner.py`, `src/corpus_pipeline.py`). Các bài văn xuôi không có bản dịch thơ để trống cột `Dịch thơ` (`""`).
  * Xuất đồng bộ 2 định dạng chuẩn: `VPO_03_parallel.tsv` (UTF-8, không header) và `VPO_03_parallel.xlsx` (2 sheet `DONG_HANG` & `THONG_KE`), kèm `qa_report.json` và `word_coverage_report.json`.

---

### 2. Thống kê Chất lượng Kiểm định (QA Report — Nhánh `khanh`)

* **Tổng số dòng dóng hàng (4 cột `Hán - Dịch âm - Dịch nghĩa - Dịch thơ`):** `856` *(gồm `76` dòng tiêu đề, `453` dòng có `Dịch thơ`)*
* **Số cặp hợp lệ:** `856`
* **Số cặp cảnh báo QA:** `89` (`OMISSION: 60`, `ADDITION: 19`, `NUMBER_MISMATCH: 18` trên `89` dòng; `MISSING = 0`, `FORMAT_ERROR = 0`, `LEFTOVER_MARKER = 0`)
* **Tỷ lệ lỗi QA:** `10.40%` (Đạt chuẩn nghiệm thu $\le 30\%$ và mục tiêu nội bộ $\le 20\%$)
* **Độ bao phủ Hán tự trung bình:** `43.49%`
* **Điểm tin cậy dóng hàng trung bình:** `0.48 / 1.00` (`0.4756`)
* **Khớp 100% `VPO_03_parallel.tsv` == `VPO_03_parallel.xlsx` (`DONG_HANG`):** Đạt

---

### 3. Cấu trúc thư mục bàn giao

```text
CV04_VPO_03/
├── 01_nguon/           # Ảnh scan trang sách gốc 300 DPI (.png) + file bổ sung trang 25 trắng
├── 02_ocr_tho/         # Kết quả OCR thô ban đầu (han/, viet/, ocr_results.jsonl, ocr_run_summary.json)
├── 03_text_sach/       # Văn bản đã làm sạch (han.txt, viet.txt)
├── 04_dong_hang/       # VPO_03_parallel.tsv, VPO_03_parallel.xlsx, qa_report.json, word_coverage_report.json
└── README.md           # Tài liệu thuyết minh phương pháp & kết quả
```
