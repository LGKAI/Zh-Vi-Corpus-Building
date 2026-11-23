# Dóng Hàng Hán – Việt (Nhóm CV04)

Xây dựng kho ngữ liệu song ngữ văn học Hán – Việt (thơ ca & văn xuôi) cấp câu/đoạn cho đồ án giữa kỳ môn **Xử lý Ngôn ngữ Tự nhiên (NLP)**.

- **Mã nhóm**: `CV04` — Trần Trung Hiếu *(Nhóm trưởng)*, Lê Gia Khánh, Phạm Chấn Khoa, Cái Hoàng Bảo Kin
- **Hướng dẫn**: Chị **Lưu Như** | **Hạn nộp**: `30/11`

---

## 1. Kết Quả Hợp Nhất Toàn Nhóm (`main` — Đủ 4 Thành Viên)

Toàn bộ **1.584 trang hợp lệ** từ 3 bộ PDF scan gốc (`1.996` trang PDF) đã được 4 thành viên OCR GPU (`PaddleOCR chinese_cht` + `VietOCR vgg_transformer`), gộp chung vào `CV04_VPO_01..03/` và dóng hàng 4 cột (`Hán` – `Dịch âm` – `Dịch nghĩa` – `Dịch thơ`):

| Thư mục / Tác phẩm | Trang OCR GPU | Trang dóng hàng | Tổng dòng | Dòng tiêu đề | Dòng có `Dịch thơ` | Lỗi QA *(ngưỡng $\le 30\%$)* | `MISSING` / `FORMAT_ERROR` | `TSV == XLSX` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| [`CV04_VPO_01`](CV04_VPO_01/README.md) — *Hán Văn Tinh Túy* | `375` (`PDF 7..381`) | `375` | `1.377` | `36` | `1.111` | `9.59%` (`132`) | `0` / `0` | 100% |
| [`CV04_VPO_02`](CV04_VPO_02/README.md) — *Thể loại từ VN trung đại* | `414` (`PDF 134..547`) | `411` *(trừ `378..380`)* | `1.925` | `178` | `1.213` | `6.18%` (`119`) | `0` / `0` | 100% |
| [`CV04_VPO_03`](CV04_VPO_03/README.md) — *Thơ văn Lý – Trần Tập II* | `795` (`PDF 17..861`) | `795` | `4.334` | `318` | `1.250` | `9.67%` (`419`) | `0` / `0` | 100% |
| **Tổng toàn nhóm `CV04`** | **`1.584`** | **`1.581`** | **`7.636`** | **`532`** | **`3.574`** | **`8.77%` (`670/7.636`)** | **`0` / `0`** | **100%** |

> **Phân công đóng góp**: Khoa `398` trang (`origin/khoa`), Hiếu `397` trang (`origin/hieu`), Khánh `396` trang (`khanh`), Kin `393` trang (`kin`). Chi tiết tại [`docs/3_PHAN_CONG_4_NGUOI.md`](docs/3_PHAN_CONG_4_NGUOI.md).

---

## 2. Cấu Trúc Thư Mục

```text
.
├── main.py                           # CLI: extract, stage, ocr, align, run, validate, web
├── requirements.txt                  # PyMuPDF, openpyxl, Pillow, streamlit (+ tùy chọn GPU)
├── config/
│   ├── book_manifest.json            # Ánh xạ VPO_01..03, lệch trang, phạm vi hợp lệ & loại trừ
│   └── member_splits.json            # Bảng chia 1.583 trang cho 4 thành viên (+ PDF 7 ở VPO_01)
├── raw_data/                         # (git-ignored) 3 PDF gốc, Thông tin dữ liệu.png, Thiền Tông Chỉ Nam Tự.txt
├── CV04_VPO_01/                      # 01_nguon/, 02_ocr_tho/, 03_text_sach/, 04_dong_hang/, README.md
├── CV04_VPO_02/                      # (tương tự, Phần Ba PDF 134..547)
├── CV04_VPO_03/                      # (tương tự + bai_03_thien_tong_chi_nam_tu_dich_nghia.txt bù trang 25)
├── src/                              # 14 module pipeline: pdf_extractor, ocr_engine, ocr_disambiguator,
│                                     # text_cleaner, phonetic_verifier, work_segmenter, aligner,
│                                     # poetic_aligner, semantic_scorer, word_aligner, exporter_and_qa,
│                                     # workbench_editor, corpus_pipeline, pipeline_runner
├── web_app/app.py                    # Streamlit CAT Workbench (xem tiến độ, sửa/ghép/xóa, đối soát ảnh)
├── docs/                             # 1_KIEM_KE_NGUON.md, 2_THONG_KE_BO_SUNG.md, 3_PHAN_CONG_4_NGUOI.md,
│                                     # Hướng dẫn dóng hàng Hán-Việt.pdf, Hướng dẫn dóng hàng dịch âm.docx, reference/
└── tests/test_suite.py               # 8 unit & integration tests
```

---

## 3. Quy Chuẩn Kỹ Thuật & 5 Tiêu Chí Phương Pháp (Mục 9)

- **Định dạng 4 cột chuẩn**: `Hán` | `Dịch âm` | `Dịch nghĩa` | `Dịch thơ`. Mỗi bài có **1 dòng tiêu đề riêng** trước thân bài; cột khuyết ở nguyên bản để `""` (như *Thu dạ hoài ngâm* thiếu `Dịch nghĩa`, văn xuôi thiếu `Dịch thơ`).
- **Đồng bộ tệp bàn giao**: `.tsv` (UTF-8, không header, phân tách `\t`) khớp 100% với sheet `DONG_HANG` (hàng 1 là tiêu đề 4 cột) của `.xlsx` kèm sheet `THONG_KE`. `03_text_sach/{han,viet}.txt` chuẩn `UTF-8 NFC`, đồng bộ 1-1 theo dòng với `.tsv` (khi chạy `align`).
- **5 tiêu chí phương pháp đề xuất**:
  1. *Lý do chọn*: `PyMuPDF` (300 DPI đa nền tảng), `PaddleOCR chinese_cht` + `VietOCR vgg_transformer`, khử nhầm nét Hán bằng `Phiên âm` (`M.E.D. Levenshtein` $S_1 \cap S_2$, `105` cụm nhầm nét, `764` mục từ điển Hán–Việt lõi) và DP Gale-Church + neo từ vựng/số đếm.
  2. *Đầu vào / Đầu ra*: 3 PDF scan (`raw_data/`) + bản dịch trang 25 `VPO_03` $\rightarrow$ 3 thư mục `CV04_VPO_01..03/` (`01_nguon`, `02_ocr_tho`, `03_text_sach`, `04_dong_hang`).
  3. *Kiểm chứng*: `validate_pairs` (6 loại cờ lỗi, tỷ lệ lỗi tổng `8.77% <= 30%`), kiểm tra `TSV == XLSX`, độ phủ Hán tự (`word_aligner.py`), `tests/test_suite.py` (`8/8` pass) và hậu kiểm trực quan trên `web_app/app.py`.
  4. *Rủi ro & dự phòng*: Cắt header 7%, lọc đường kẻ chú thích (`VPO_02`), bù trang trắng `PDF 25` (`VPO_03`), hỗ trợ bảo toàn `[MASK]`/`□` và chỉnh sửa tay qua CAT Workbench.
  5. *Tái lập*: Cấu hình tập trung ở `config/`, xuất `.xlsx` thuần thư viện chuẩn Python (zero-dependency), chạy lại qua `main.py`.

---

## 4. Lệnh Chạy Nhanh

```powershell
python main.py extract --member khanh --dpi 300   # Trích xuất ảnh 300 DPI theo thành viên (khoa/hieu/khanh/kin)
python main.py align --book ALL                   # Dóng hàng 4 cột từ toàn bộ JSON trong 02_ocr_tho/
python main.py validate                           # Kiểm định QA & đối chiếu TSV == XLSX trên CV04_VPO_01..03
python -m unittest discover -s tests -v           # Chạy 8 bài test tự động (cô lập trong thư mục tạm)
python main.py web                                # Mở giao diện Streamlit CAT Workbench
```

> **Lưu ý**: Không chạy `python main.py run` trên thư mục gốc vì lệnh này ghi đè `CV04_VPO_01..03/` bằng bộ dữ liệu mẫu Pilot (`32/8/15` dòng).
