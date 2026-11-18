# BÁO CÁO TỔNG HỢP ĐỒ ÁN: SỐ HÓA, OCR & DÓNG HÀNG NGỮ LIỆU SONG NGỮ HÁN – VIỆT

- **Nhóm thực hiện (04 thành viên)**: **Khoa**, **Hiếu**, **Khánh**, **Kin**
- **Ngày lập báo cáo**: `2026-11-18`
- **Kho mã nguồn**: [github.com/pckhoa206/OCR_NLP](https://github.com/pckhoa206/OCR_NLP)
- **Quy chuẩn áp dụng**: [`Guideline.pdf`](../Guideline.pdf) & chỉ đạo cụ thể của Giảng viên hướng dẫn

---

## 1. Mục tiêu đề tài & Quy chuẩn nghiệm thu

Theo [`Guideline.pdf`](../Guideline.pdf) (Mục 1–8):
- **Chỉ tiêu khối lượng nhóm 4 thành viên (tài liệu PDF Scan cần OCR)**: Tối thiểu **2.000 cặp câu hợp lệ/thành viên** ($\ge$ **8.000 cặp hợp lệ/nhóm**).
- **Quy cách tệp nộp chuẩn**: Xuất đồng thời `.tsv` (UTF-8 NFC, phân cách bằng ký tự Tab `\t`) và `.xlsx` (sheet chính `DONG_HANG` + sheet thống kê `THONG_KE`); dữ liệu hai tệp phải khớp nhau **100%**.
- **Ngưỡng chất lượng**: Tỷ lệ lỗi tối đa cho phép $\le \mathbf{30.0\%}$ (mục tiêu biên an toàn $\le \mathbf{20.0\%}$), kiểm tra theo 3 nhóm lỗi: `MISSING`, `OMISSION`, `ADDITION` (cùng `FORMAT_ERROR`, `LEFTOVER_MARKER`, `NUMBER_MISMATCH`).
- **Quy tắc bảo toàn văn bản**: Không tự ý hiện đại hóa chữ cổ/dị thể, bảo toàn chữ khuyết (`□`), chuẩn hóa `UTF-8 NFC`.

---

## 2. Kiểm kê nguồn tài liệu & Phạm vi xử lý (03 bộ cổ thư)

Từ **1.996 trang PDF scan gốc** trong thư mục `data/`, hệ thống đã tách ảnh 300 DPI bằng [`scripts/extract_pages.swift`](../scripts/extract_pages.swift), loại trừ toàn bộ các trang bìa/mục lục/khảo đính/Chữ Nôm/scan trắng để giữ lại chính xác **1.583 trang nội dung hợp lệ** trong `deliverables/*/01_nguon/*.png`:

| Mã sách | Tên tác phẩm | Tổng trang PDF | Số trang PNG hợp lệ | Công thức quy đổi trang | Phạm vi & Yêu cầu đặc thù từ Giảng viên |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **`HVTT`** | *Hán Văn Tinh Túy* (Lãng Nhân) | 386 | **374** (`0008..0381`) | `pdf_page = book_page + 6` | Xuất **4 cột**: `Hán \| Dịch âm \| Dịch nghĩa \| Dịch thơ`. Riêng bài cuối (*Thu dạ hoài ngâm*, `PDF 368..381`) chỉ có Hán – Dịch âm – Dịch thơ, **cột `Dịch nghĩa` để trống**. |
| **`TVLT2`** | *Thơ văn Lý – Trần, Tập II* (Nguyễn Huệ Chi chủ biên) | 965 | **795** (`0017..0861`) | `book_page = pdf_page + 2` *(từ PDF $\ge$ 7)* | Đã loại trang scan trắng `PDF 25` và **4 tác phẩm Chữ Nôm** (`PDF 493..525`, `688..703`, `862..873`). Tích hợp bản dịch bổ sung bài số 3 (*Thiền tông chỉ nam tự*) từ Google Drive Giảng viên (`deliverables/TVLT2_ThoVanLyTran2/01_nguon/bai_03_thien_tong_chi_nam_tu_dich_nghia.txt`). |
| **`TLTVN`** | *Thể loại từ Việt Nam thời trung đại* (Nguyễn Xuân Diện – Nguyễn Quảng Tuân) | 645 | **414** (`0134..0547`) | `pdf_page = book_page + 7` *(sách 1..593)* | Chỉ dóng hàng **Phần Ba: Tuyển tập từ Việt Nam thời trung đại** (sách `127..540`). Bỏ Phần Một, Phần Hai (lý thuyết tiếng Việt); liệt kê các bài khuyết gốc & các tập chữ Hán Phụ lục 3 gửi Giảng viên. |
| **Tổng** | **03 bộ cổ thư** | **1.996** | **1.583 trang PNG** | — | Phủ 100% phạm vi hợp lệ đã nghiệm thu kiểm kê. |

---

## 3. Phân chia dữ liệu cho 4 thành viên (Khoa – Hiếu – Khánh – Kin)

Để cân bằng tuyệt đối cả **số lượng trang (~393–397 trang/người)** lẫn **tỷ trọng thể loại** (tránh dồn toàn bộ `TVLT2` 795 trang cho một người), đồng thời **không cắt rời cặp trang đối diện `(chẵn, lẻ)` trong `HVTT`**, toàn bộ **1.583 trang PNG** được chia đều theo từng quyển (cấu hình lưu tại [`config/member_splits.json`](../config/member_splits.json)):

| Thành viên | Mã shard | `HVTT` (374 trang) | `TVLT2` (795 trang) | `TLTVN` (414 trang) | Tổng số trang | Tỷ lệ |
| :--- | :---: | :--- | :--- | :--- | :---: | :---: |
| **Khoa** | `khoa` | **94 trang** (`PDF 8–101` / Sách `2–95`, 47 cặp) | **199 trang** (`PDF 17–216` / Sách `19–218`) | **104 trang** (`PDF 134–237` / Sách `127–230`) | **397 trang** | 25.08% |
| **Hiếu** | `hieu` | **94 trang** (`PDF 102–195` / Sách `96–189`, 47 cặp) | **199 trang** (`PDF 217–415` / Sách `219–417`) | **104 trang** (`PDF 238–341` / Sách `231–334`) | **397 trang** | 25.08% |
| **Khánh** | `khanh` | **94 trang** (`PDF 196–289` / Sách `190–283`, 47 cặp) | **199 trang** (`PDF 416–647` / Sách `418–649`) | **103 trang** (`PDF 342–444` / Sách `335–437`) | **396 trang** | 25.02% |
| **Kin** | `kin` | **92 trang** (`PDF 290–381` / Sách `284–375`, 46 cặp) | **198 trang** (`PDF 648–861` / Sách `650–863`) | **103 trang** (`PDF 445–547` / Sách `438–540`) | **393 trang** | 24.83% |
| **Cộng** | **4 người** | **374 trang** (187 cặp) | **795 trang** | **414 trang** | **1.583 trang** | **100%** |

### Lưu ý kỹ thuật riêng cho phần việc từng thành viên
1. **Khoa (`khoa`)**:
   - Xử lý **Bài 3 `TVLT2`** (*Thiền tông chỉ nam tự*, `PDF 25` bị scan trắng) bằng bản dịch bổ sung đã đính kèm sẵn.
   - Trong `TLTVN`: lưu ý 2 bài tàn khuyết một phần chữ Hán tại `PDF 138–140` (Lý Đạo Tái mất hạ phiến 25 chữ) và `PDF 221–225` (Nguyễn Huy Oánh khuyết 1 chữ `□`).
2. **Hiếu (`hieu`)**:
   - Trong `TLTVN`: lưu ý bài của Phạm Nguyễn Du tại `PDF 303–304` bị mất hạ phiến trong văn bản gốc.
3. **Khánh (`khanh`)**:
   - Trong `TVLT2`: 2 bài Chữ Nôm dài của Trần Nhân Tông (`PDF 493–525`) đã được loại bỏ sẵn khỏi thư mục ảnh nguồn.
   - Trong `TLTVN`: `PDF 378–380` chứa 4 bài Nôm của Phạm Thái (*Sơ kính tân trang*) khuyết hoàn toàn chữ gốc Hán/Nôm và Dịch nghĩa $\rightarrow$ bỏ qua trừ khi Giảng viên tìm được bản bổ sung.
4. **Kin (`kin`)**:
   - Trong `HVTT`: phụ trách đoạn cuối sách (`PDF 368–381`, bài *Thu dạ hoài ngâm*) $\rightarrow$ kiểm tra kỹ cấu trúc **4 cột với cột `Dịch nghĩa` để trống `""`**.
   - Trong `TVLT2`: bài Chữ Nôm *Vịnh Vân-yên tự phú* (`PDF 688–703`) đã được loại bỏ sẵn khỏi thư mục ảnh nguồn.

---

## 4. Kiến trúc hệ thống & Quy trình vận hành End-to-End

### 4.1. Các module kỹ thuật đã xây dựng
1. **Tách ảnh PDF 300 DPI**: [`scripts/extract_pages.swift`](../scripts/extract_pages.swift) (Apple PDFKit/CoreGraphics).
2. **OCR đa động cơ & Phân tách layout**: [`kaggle_ocr/ocr_pipeline_kaggle.py`](../kaggle_ocr/ocr_pipeline_kaggle.py)
   - `KaggleDualOCREngine`: Kết hợp `PaddleOCR` (`chinese_cht` + `vi`) và `VietOCR` (`vgg_transformer`); tự động cài đặt gói khi chạy trên môi trường Kaggle GPU.
   - Tiền xử lý: cắt running header 7% (`crop_running_header`), phát hiện đường kẻ ngang chú thích chân trang (`detect_footnote_separator`), gom cụm theo quy luật riêng từng sách (`group_layout_blocks`, hỗ trợ cả `dich_tho_lines` đối diện của `HVTT`).
3. **Khử nhầm lẫn & Đối soát âm học**:
   - [`src/ocr_disambiguator.py`](../src/ocr_disambiguator.py): Sửa tự động **105+ cụm chữ Hán dễ nhầm nét** (257 ký tự, 24 chữ đa âm như `戊/戌/戍`, `己/已/巳`, `日/曰`, `侯/候`, `祇/祗`) bằng âm đọc Hán–Việt đối chiếu.
   - [`src/phonetic_verifier.py`](../src/phonetic_verifier.py): Kiểm tra khớp âm $1:1$ và phóng chiếu dấu câu từ phiên âm sang Hán văn.
4. **Làm sạch, Dóng hàng & Đánh giá từ vựng**:
   - [`src/text_cleaner.py`](../src/text_cleaner.py): Chuẩn hóa `UTF-8 NFC`, giữ nguyên chữ khuyết `□`, tách câu tránh chữ viết tắt.
   - [`src/aligner.py`](../src/aligner.py) & [`src/poetic_aligner.py`](../src/poetic_aligner.py): Quy hoạch động **Plateau Prior DP** với khoảng tỷ lệ phẳng $[0.80, 2.40]$, hỗ trợ đầy đủ các hạt `1:1, 1:2, 2:1, 1:3, 3:1, 2:2, 1:4, 4:1, 2:3, 3:2`, neo từ vựng + điểm ngữ nghĩa [`src/semantic_scorer.py`](../src/semantic_scorer.py).
   - [`src/word_aligner.py`](../src/word_aligner.py): Đo độ phủ từ vựng (`han_coverage_pct`, `viet_coverage_pct`) và điểm tin cậy để gắn cờ các câu nghi ngờ sót/thừa nghĩa.
5. **Cầu nối End-to-End, Xuất chuẩn & CAT Workbench**:
   - [`src/corpus_pipeline.py`](../src/corpus_pipeline.py): Đọc trực tiếp JSON từ `02_ocr_tho/{han,viet}/*.json`, gộp câu qua ranh giới trang, nạp bản dịch bổ sung bài 3 `TVLT2`, chạy toàn bộ hậu xử lý + dóng hàng + kiểm định.
   - [`src/exporter_and_qa.py`](../src/exporter_and_qa.py): Kiểm tra lỗi QA và xuất đồng thời `.tsv` + `.xlsx` 2 sheet (`DONG_HANG` + `THONG_KE`) không cần `openpyxl`/`pandas`.
   - [`web_app/app.py`](../web_app/app.py) & [`src/workbench_editor.py`](../src/workbench_editor.py): Giao diện Streamlit hỗ trợ đối chiếu ảnh scan gốc và sửa/tách/gộp/chèn/xóa trực tiếp.

### 4.2. Lệnh chạy thực tế cho từng thành viên & Tổng hợp nhóm

**Bước 1 — Đóng gói và đẩy phần ảnh riêng của từng thành viên lên Kaggle GPU**:
```bash
# Thay <ten_thanh_vien> bằng một trong 4 giá trị: khoa | hieu | khanh | kin
python3 scripts/split_member_data.py --member <ten_thanh_vien> --stage /tmp/kaggle_<ten_thanh_vien>
bash kaggle_ocr/deploy_to_kaggle.sh --push-dataset /tmp/kaggle_<ten_thanh_vien> --push-kernel
```

**Bước 2 — Theo dõi tiến độ & Tải JSON OCR từ Kaggle về chung thư mục `deliverables/<BOOK>/02_ocr_tho/`**:
```bash
bash kaggle_ocr/deploy_to_kaggle.sh --status
bash kaggle_ocr/deploy_to_kaggle.sh --pull-output
```

**Bước 3 — Hợp nhất toàn bộ 1.583 trang thành kết quả `.tsv` / `.xlsx` chuẩn chỉnh**:
```bash
python3 scripts/run_end_to_end.py --skip-ocr
```

---

## 5. Kết quả kiểm thử & thực nghiệm hiện tại

### 5.1. Kiểm thử toàn trình End-to-End (`python3 scripts/run_end_to_end.py --pilot-only`)

> **Ghi chú minh bạch**: Do máy local hiện tại chưa cài `paddleocr`/`vietocr`/CUDA, kết quả `02_ocr_tho` đi kèm trong lần chạy cục bộ được sinh ở chế độ `--mock` cho **26 trang pilot** (thời gian toàn trình `0.722s`), sau đó chạy thật qua toàn bộ chuỗi khử nhầm lẫn, làm sạch, dóng hàng DP, kiểm định QA, đóng gói Hugging Face, chẩn đoán từ vựng và benchmark. Để sinh OCR thật cho toàn bộ 1.583 trang cần chạy bước Kaggle GPU ở Mục 4.2.

| Bộ sách | Chế độ cấu trúc | Số cặp đã dóng hàng | Tỷ lệ lỗi QA | Phủ chữ Hán TB | Điểm tin cậy TB | Khớp âm Hán–Việt | TSV = XLSX |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`HVTT`** | 4 cột (`Hán \| Dịch âm \| Dịch nghĩa \| Dịch thơ`, bài cuối trống `Dịch nghĩa`) | **26** | **0.00%** | **98.08%** | **0.813** | 100% | Khớp 100% |
| **`TVLT2`** | 2 cột (`Hán \| Việt`, đã gồm Bài 3 *Thiền tông chỉ nam tự* GDrive) | **17** | **0.00%** | **51.30%** | **0.5973** | 100% | Khớp 100% |
| **`TLTVN`** | 2 cột (`Hán \| Việt`, Phần Ba tuyển tập từ) | **4** | **0.00%** | **76.14%** | **0.7544** | 100% | Khớp 100% |

- Các tác vụ đầu ra tiếp theo đều hoàn tất với mã thoát `0`: đóng gói Hugging Face (`dataset_export/{train,validation,test}.jsonl`), xuất báo cáo chẩn đoán ([`docs/BAO_CAO_CHAN_DOAN_CHAT_LUONG.md`](BAO_CAO_CHAN_DOAN_CHAT_LUONG.md)), đánh giá benchmark, và tạo gói demo giảng viên ([`demo_giang_vien/`](../demo_giang_vien)).

### 5.2. Kiểm thử tự động & Kiểm tra phân chia nhóm
- **Unit & Integration Tests** (`./.venv/bin/pytest tests/ -q`): **43 / 43 bài kiểm tra PASS** trong `1.481s`.
- **Kiểm tra chia shard 4 thành viên** (`python3 scripts/split_member_data.py --verify`): Trả về `"status": "VERIFIED"`, xác nhận `0` trang trùng lặp và phủ đủ `1.583 / 1.583` trang.

---

## 6. Thống kê các phần cần Giảng viên hỗ trợ bổ sung (`TLTVN`)

Chi tiết đầy đủ xem tại [`docs/THONG_KE_BO_SUNG_GIANG_VIEN.md`](THONG_KE_BO_SUNG_GIANG_VIEN.md); tóm tắt 2 nhóm cần bổ sung:
1. **Bài khuyết văn bản gốc trong Phần Ba**:
   - **04 bài Nôm của Phạm Thái** (*Sơ kính tân trang*, `tr. 371–373` / `PDF 378–380`): chỉ có Quốc ngữ, khuyết hoàn toàn chữ gốc Hán/Nôm và Dịch nghĩa.
   - **03 bài tàn khuyết một phần chữ Hán**: Lý Đạo Tái (`tr. 131–133` / `PDF 138–140`, mất hạ phiến), Nguyễn Huy Oánh (`tr. 214–218` / `PDF 221–225`, khuyết 1 chữ `□`), Phạm Nguyễn Du (`tr. 296–297` / `PDF 303–304`, mất hạ phiến).
2. **Các quyển chỉ có chữ Hán trong Phụ lục 3 (`tr. 545–596` / `PDF 552–604`)**:
   - *Thạc Đình di cảo* (9/9 bài từ đã dịch), *Hoa thiều ngâm lục* (8/8 bài từ đã dịch, còn 9 bài thơ thất ngôn kèm theo chưa dịch), *Lưu Hương kí* (4/4 bài từ đã dịch, còn bài *Thu tứ ca* chưa dịch).
   - Trọng tâm là tập ***Cổ duệ từ*** của Nguyễn Phúc Miên Thẩm (`tr. 572–596` / `PDF 579–604`): gồm 114 bài từ nhưng Phần Ba mới dịch 6 bài, còn **108 bài từ (98 đề mục) chỉ có nguyên bản chữ Hán chưa có bản dịch**.
