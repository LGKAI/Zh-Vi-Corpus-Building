# Xây dựng Ngữ liệu Song hành Hán - Việt (CV04_VPO_01 - VPO_01)

**Học phần:** Xử lý Ngôn ngữ Tự nhiên (NLP)  
**Mã nhóm:** CV04 (Trần Trung Hiếu, Lê Gia Khánh, Phạm Chấn Khoa, Cái Hoàng Bảo Kin)  
**Mã tác phẩm:** `VPO_01` (`CV04_VPO_01`)  
**Tác phẩm:** *Hán Văn Tinh Túy* — Lãng Nhân (Phùng Tất Đắc)  

---

### 1. Phương pháp và Công cụ thực hiện (Tools & Methods)

* **Trích xuất nguồn dữ liệu (`01_nguon`):**
  * Trích xuất ảnh quét trang sách độ phân giải chuẩn **300 DPI** từ file PDF gốc bằng thư viện `PyMuPDF (fitz)` (`src/pdf_extractor.py`).
* **Nhận dạng ký tự quang học (`02_ocr_tho`):**
  * Chữ Hán phồn thể: **PaddleOCR (PP-OCRv5)** kết hợp hiệu chỉnh nhập nhằng thị giác qua neo ngữ âm Hán-Việt (`src/ocr_disambiguator.py`).
  * Chữ Quốc ngữ (Phiên âm, Dịch nghĩa, Dịch thơ): **VietOCR (Transformer Seq2Seq)**.
  * Các chữ Hán bị mờ nặng hoặc tàn khuyết trong bản in gốc được bảo toàn bằng ký hiệu **`[MASK]`**.
* **Làm sạch và Chuẩn hóa văn bản (`03_text_sach`):**
  * Chuẩn hóa bảng mã Unicode **UTF-8 NFC**, lọc bỏ header/footer, số trang và ký hiệu chú thích (`[1]`, `1*`, `(1)`).
  * Phóng chiếu dấu câu từ bản Dịch âm sang chữ Hán (`src/phonetic_verifier.py`) và ngăn cách các bài trong tuyển tập bằng tiêu đề `=== Tiêu đề bài ===`.
* **Dóng hàng song ngữ 4 cột (`04_dong_hang`):**
  * Mỗi bài thơ/văn bắt đầu bằng **1 dòng tiêu đề riêng** (gồm tiêu đề chữ Hán, Dịch âm, Dịch nghĩa, Dịch thơ đặt đúng cột), theo sau là các câu nội dung chính.
  * Dóng hàng **Hán – Dịch âm** bằng giải thuật **M.E.D. (Levenshtein)** kết hợp giao tập từ điển hình dáng & âm đọc ($S_1 \cap S_2$).
  * Dóng hàng **Hán – Dịch nghĩa – Dịch thơ** bằng giải thuật **Quy hoạch động (Dynamic Programming Gale-Church + Neo từ vựng Hán-Việt)** (`src/aligner.py`, `src/poetic_aligner.py`).
  * Xuất đồng bộ 2 định dạng chuẩn: `VPO_01_parallel.tsv` và `VPO_01_parallel.xlsx` (2 sheet `DONG_HANG` & `THONG_KE`).

---

### 2. Thống kê Chất lượng Kiểm định (QA Report)

* **Tổng số dòng dóng hàng (4 cột `Hán - Dịch âm - Dịch nghĩa - Dịch thơ`):** `32`
* **Số cặp hợp lệ:** `32`
* **Tỷ lệ lỗi QA:** `0.00%` (Đạt chuẩn nghiệm thu $\le 30\%$)
* **Độ bao phủ Hán tự trung bình:** `91.1%`
* **Điểm tin cậy dóng hàng trung bình:** `0.75 / 1.00`

---

### 3. Cấu trúc thư mục bàn giao

```text
CV04_VPO_01/
├── 01_nguon/           # Ảnh scan trang sách gốc 300 DPI (.png)
├── 02_ocr_tho/         # Kết quả OCR thô ban đầu (han/ và viet/)
├── 03_text_sach/       # Văn bản đã làm sạch (han.txt, viet.txt)
├── 04_dong_hang/       # Dữ liệu dóng hàng 4 cột (VPO_01_parallel.tsv & .xlsx)
└── README.md           # Tài liệu thuyết minh phương pháp & kết quả
```
