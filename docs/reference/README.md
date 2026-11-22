# Demo Xây dựng Ngữ liệu Song hành Hán - Việt (CV03 - VPR_14)

**Học phần:** Xử lý Ngôn ngữ Tự nhiên (NLP)  
**Mã bài:** VPR_14  
**Tác phẩm:** *Văn sách thi Đình Thăng Long - Hà Nội (Tập 3)* — Bài 1: Trạng nguyên Lương Thế Vinh (Khoa Quý Mùi - Quang Thuận 4, 1463)  

---

### 1. Giới thiệu
Tài liệu này ghi nhận phương pháp, công cụ và kết quả thực nghiệm xây dựng tập ngữ liệu song hành Hán - Việt cho phạm vi 2 trang đầu của Bài 1. Toàn bộ các bước trích xuất, làm sạch và dóng hàng được quy chuẩn đồng bộ, phụ thuộc trực tiếp vào phạm vi nội dung của 2 trang scan chữ Hán gốc trong thư mục `01_nguon/han/` (`0001.png` và `0002.png`).

---

### 2. Phương pháp và Công cụ thực tế sử dụng (Tools & Methods)

* **Thu thập và Trích xuất nguồn dữ liệu (`01_nguon`):**
  * *Nguồn chữ Hán:* Trích xuất từ file scan PDF gốc độ phân giải cao bằng thư viện Python `PyMuPDF (fitz)` (lấy 2 trang đầu của Bài 1: `0001.png` - trang 102 sách và `0002.png` - trang 103 sách).
  * *Nguồn tiếng Việt:* Trích xuất trực tiếp từ tầng văn bản số nguyên gốc (Digital Text Layer) của NXB Hà Nội (`search_config.js` / `Searchable.pdf` / `Van_sach_thi_Dinh_Tap_3_FullText.txt`), đồng thời dùng `PyMuPDF` kết xuất 2 trang ảnh bản dịch tương ứng (`0001.png` - trang 91 sách và `0002.png` - trang 92 sách) để phục vụ đối chiếu trực quan.

* **Nhận dạng ký tự quang học (`02_ocr_tho`):**
  * *Môi trường thực thi:* Notebook trên nền tảng **Kaggle**.
  * *Engine OCR:* **Tesseract OCR** sử dụng gói ngôn ngữ `chi_tra_vert` (chuyên dụng cho chữ Hán phồn thể viết dạng **cột dọc** truyền thống của mộc bản).
  * *Kỹ thuật hỗ trợ:* Kết hợp tệp **Phiên âm Hán – Việt** trích xuất từ NXB Hà Nội làm **"Mỏ neo ngữ âm" (Phonetic Ground Truth Anchor)** để đối soát tọa độ và định hướng nhận diện các chữ mờ hoặc khắc nét cổ.
  * Kết quả OCR thô được lưu vào thư mục `02_ocr_tho/han/` và `02_ocr_tho/viet/`.

* **Tiền xử lý và Làm sạch văn bản (`03_text_sach`):**
  * *Công cụ:* Python (thư viện `re` - Biểu thức chính quy Regex) kết hợp bộ từ điển đối sánh ngữ liệu Hán - Việt (`hanViet.json` với hơn 200.000 mục từ Hán - Nôm).
  * *Phương pháp:*
    * Xây dựng script Python (`clean_vietnamese.py`, `clean_han.py`) tự động lọc bỏ header, footer, số trang và toàn bộ hệ thống cước chú chú thích `(1)`, `(2)`,...
    * Chuẩn hóa dấu ngoặc kép theo chuẩn Hán văn cổ (`「」`, `『』`) và dấu ngắt câu (`。，、：！？`).
    * Đối chiếu trực tiếp từng dòng với ảnh scan mộc bản gốc độ phân giải cao kết hợp tra từ điển ngữ liệu Hán - Việt để sửa triệt để các chữ bị nhòe nét hoặc nhận dạng sai do khắc gỗ cổ (ví dụ: chữ dị thể `伕` $\rightarrow$ `佛`, các từ cổ `愚陋`, `芻蕘`, `忝備科目`, `拜手稽首`).
    * Xuất văn bản sạch đồng bộ gồm đúng 15 câu vào `han.txt` và `viet.txt`.

* **Tách câu và Dóng hàng song ngữ (`04_dong_hang`):**
  * *Công cụ:* Python, thuật toán dóng hàng tự động (`align_engine.py`), thư viện xử lý bảng tính `openpyxl`.
  * *Phương pháp:*
    * Tách câu dựa trên dấu ngắt ngữ pháp của Hán văn (`。`, `？`, `！`, `：`) và dấu ngắt câu tiếng Việt (`.`, `?`, `!`, `:`) có xử lý giữ nguyên tên riêng và trích dẫn.
    * Áp dụng thuật toán **Quy hoạch động (Dynamic Programming - Monotonic Alignment)** kết hợp so khớp từ vựng đồng nguyên Hán - Việt (Cognate / Lexical Anchor Matching) và tỷ lệ độ dài câu.
    * Hậu kiểm và căn chỉnh thủ công để đảm bảo tỷ lệ tương ứng 1-1 tuyệt đối cho toàn bộ 15 cặp câu trong phạm vi 2 trang Hán nguồn.
    * Xuất dữ liệu dóng hàng ra 2 định dạng:
      - `VPR_14_parallel.xlsx`: Cấu trúc Sheet `Sheet1`, tiêu đề cột `han` và `vi`, màu nền tiêu đề `#93C47D`, font Calibri 11, chiều cao hàng 25.5pt, độ rộng cột 79.43 & 90.86, căn giữa dọc và tự động xuống dòng (`wrap_text=True`).
      - `VPR_14_parallel.tsv`: Dữ liệu phân tách bằng tab `\t`, không dòng tiêu đề, mã hóa UTF-8 chuẩn CRLF.

---

### 3. Dữ liệu thực hiện & Kết quả

1. **`01_nguon`:**
   - `han/`: 2 trang scan chữ Hán gốc gồm `0001.png` (trang 102 sách) và `0002.png` (trang 103 sách).
   - `viet/`: 2 trang bản dịch tiếng Việt tương ứng gồm `0001.png` (trang 91 sách) và `0002.png` (trang 92 sách).

2. **`02_ocr_tho`:**
   - 2 file OCR thô chữ Hán (`han/0001.txt`, `han/0002.txt`) trích xuất từ Kaggle bằng Tesseract `chi_tra_vert`.
   - 2 file văn bản thô tiếng Việt (`viet/0001.txt`, `viet/0002.txt`).

3. **`03_text_sach`:**
   - `han.txt`: 15 câu chữ Hán sạch, chuẩn hóa phồn thể và hiệu đính theo mộc bản.
   - `viet.txt`: 15 câu tiếng Việt chuẩn sạch tương ứng.

4. **`04_dong_hang`:**
   - Dóng hàng thành công **15 cặp câu song hành**, bắt đầu từ đề bài Chế sách của Vua Lê Thánh Tông đến hết câu cuối cùng ở đáy trang Hán thứ 2 (`且拜手稽首以對。` / `Thần chắp tay rập đầu xin thưa.`).
   - Gồm 2 file: `VPR_14_parallel.xlsx` và `VPR_14_parallel.tsv`.

---

### 4. Cấu trúc thư mục

```
CV03_VPR_14/
├── 01_nguon/           # Ảnh scan 2 trang gốc (han và viet)
├── 02_ocr_tho/         # Văn bản OCR thô ban đầu (han và viet)
├── 03_text_sach/       # Văn bản đã làm sạch và sửa lỗi theo ảnh gốc (han.txt, viet.txt)
├── 04_dong_hang/       # Dữ liệu dóng hàng song ngữ (file .xlsx và .tsv)
└── README.md           # Tài liệu phương pháp, công cụ và quy trình thực hiện
```
