# BẢNG PHÂN CHIA DỮ LIỆU CHẠY SONG SONG CHO 4 THÀNH VIÊN
## Nhóm: Khoa – Hiếu – Khánh – Kin (1583 trang hợp lệ / 3 bộ sách)

Để đảm bảo công bằng tuyệt đối về khối lượng (**393–397 trang/người**, ước tính vượt ngưỡng **>= 2.000 cặp câu/người** theo Mục 1 của `Guideline.pdf`), đồng thời không cắt rời cặp trang đối diện trong *Hán Văn Tinh Túy* (`HVTT`), toàn bộ **1.583 trang PNG** được chia đều theo từng quyển như sau:

| Thành viên | `HVTT` (374 trang) | `TVLT2` (795 trang) | `TLTVN` (414 trang) | Tổng số trang |
| :--- | :--- | :--- | :--- | :---: |
| **Khoa** (`khoa`) | 94 tr (`PDF 8–101` / Sách `2–95`) | 199 tr (`PDF 17–216` / Sách `19–218`) | 104 tr (`PDF 134–237` / Sách `127–230`) | **397 trang** |
| **Hiếu** (`hieu`) | 94 tr (`PDF 102–195` / Sách `96–189`) | 199 tr (`PDF 217–415` / Sách `219–417`) | 104 tr (`PDF 238–341` / Sách `231–334`) | **397 trang** |
| **Khánh** (`khanh`) | 94 tr (`PDF 196–289` / Sách `190–283`) | 199 tr (`PDF 416–647` / Sách `418–649`) | 103 tr (`PDF 342–444` / Sách `335–437`) | **396 trang** |
| **Kin** (`kin`) | 92 tr (`PDF 290–381` / Sách `284–375`) | 198 tr (`PDF 648–861` / Sách `650–863`) | 103 tr (`PDF 445–547` / Sách `438–540`) | **393 trang** |

---

## Chi Tiết Phạm Vi & Lưu Ý Ngoại Lệ Cho Từng Thành Viên

### Khoa (`--member khoa` — 397 trang)
- **HVTT**: `PDF 0008..0101` (Trang sách `2..95`, 94 trang — tròn 47 cặp chẵn/lẻ)
- **TVLT2**: `PDF 0017..0216` (Trang sách `19..218`, 199 trang)
- **TLTVN**: `PDF 0134..0237` (Trang sách `127..230`, 104 trang)
- Gồm **Bài 3 `TVLT2`** (*Thiền tông chỉ nam tự*, PDF 25 trắng scan $\rightarrow$ dùng file bổ sung GDrive).
- `TLTVN`: Lưu ý PDF 138–140 (khuyết hạ phiến) & PDF 221–225 (khuyết 1 chữ `□`).

```bash
# Đóng gói đúng 397 trang của Khoa để đẩy lên Kaggle GPU chạy riêng:
python3 scripts/split_member_data.py --member khoa --stage /tmp/kaggle_khoa
bash kaggle_ocr/deploy_to_kaggle.sh --push-dataset /tmp/kaggle_khoa --push-kernel
```
### Hiếu (`--member hieu` — 397 trang)
- **HVTT**: `PDF 0102..0195` (Trang sách `96..189`, 94 trang — tròn 47 cặp chẵn/lẻ)
- **TVLT2**: `PDF 0217..0415` (Trang sách `219..417`, 199 trang)
- **TLTVN**: `PDF 0238..0341` (Trang sách `231..334`, 104 trang)
- `TLTVN`: Lưu ý PDF 303–304 (Phạm Nguyễn Du — khuyết hạ phiến trong bản gốc).

```bash
# Đóng gói đúng 397 trang của Hiếu để đẩy lên Kaggle GPU chạy riêng:
python3 scripts/split_member_data.py --member hieu --stage /tmp/kaggle_hieu
bash kaggle_ocr/deploy_to_kaggle.sh --push-dataset /tmp/kaggle_hieu --push-kernel
```
### Khánh (`--member khanh` — 396 trang)
- **HVTT**: `PDF 0196..0289` (Trang sách `190..283`, 94 trang — tròn 47 cặp chẵn/lẻ)
- **TVLT2**: `PDF 0416..0647` (Trang sách `418..649`, 199 trang)
- **TLTVN**: `PDF 0342..0444` (Trang sách `335..437`, 103 trang)
- `TVLT2`: Đã loại trừ sẵn 2 bài Chữ Nôm (*Cư trần lạc đạo phú*, *Đắc thú lâm tuyền*).
- `TLTVN`: Lưu ý PDF 378–380 (4 bài Nôm Phạm Thái khuyết bản gốc Hán/Nôm — bỏ qua nếu chưa có bổ sung).

```bash
# Đóng gói đúng 396 trang của Khánh để đẩy lên Kaggle GPU chạy riêng:
python3 scripts/split_member_data.py --member khanh --stage /tmp/kaggle_khanh
bash kaggle_ocr/deploy_to_kaggle.sh --push-dataset /tmp/kaggle_khanh --push-kernel
```
### Kin (`--member kin` — 393 trang)
- **HVTT**: `PDF 0290..0381` (Trang sách `284..375`, 92 trang — tròn 46 cặp chẵn/lẻ)
- **TVLT2**: `PDF 0648..0861` (Trang sách `650..863`, 198 trang)
- **TLTVN**: `PDF 0445..0547` (Trang sách `438..540`, 103 trang)
- `HVTT`: Gồm **bài cuối** (*Thu dạ hoài ngâm*, PDF 368–381) $\rightarrow$ giữ đủ 4 cột nhưng để trống cột `Dịch nghĩa`.
- `TVLT2`: Đã loại trừ sẵn bài Chữ Nôm *Vịnh Vân-yên tự phú*.

```bash
# Đóng gói đúng 393 trang của Kin để đẩy lên Kaggle GPU chạy riêng:
python3 scripts/split_member_data.py --member kin --stage /tmp/kaggle_kin
bash kaggle_ocr/deploy_to_kaggle.sh --push-dataset /tmp/kaggle_kin --push-kernel
```

---

## Quy Trình Tổng Hợp Sau Khi 4 Thành Viên Chạy Xong Kaggle

1. Tải kết quả OCR từ tài khoản Kaggle của từng thành viên (`bash kaggle_ocr/deploy_to_kaggle.sh --pull-output`) về `deliverables/<BOOK>/02_ocr_tho/{han,viet}/*.json`.
2. Gộp kiểm định và xuất toàn bộ `.tsv` + `.xlsx` 2 sheet cuối cùng chỉ bằng **1 lệnh**:
   ```bash
   python3 scripts/run_end_to_end.py --skip-ocr
   ```
