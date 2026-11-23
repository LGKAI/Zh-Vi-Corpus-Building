# BẢNG PHÂN CHIA KHỐI LƯỢNG CHẠY SONG SONG CHO 4 THÀNH VIÊN (NHÓM CV04)

Để đảm bảo kịp hạn nộp **30/11** và vượt chỉ tiêu **$\ge 8.000$ cặp câu toàn nhóm** ($\ge 2.000$ cặp câu/người), toàn bộ **1.583 trang hợp lệ** của 3 bộ sách (`CV04_VPO_01`, `CV04_VPO_02`, `CV04_VPO_03`) được chia đều công bằng cho 4 thành viên (**393–397 trang/người**), đồng thời giữ nguyên cặp trang chẵn–lẻ đối diện `(2k, 2k+1)` của cuốn `VPO_01` (*Hán Văn Tinh Túy*) để lấy trọn vẹn cả 4 cột (`Hán` – `Dịch âm` – `Dịch nghĩa` – `Dịch thơ`):

| Thành viên | `CV04_VPO_01` (*Hán Văn Tinh Túy*, 374 tr) | `CV04_VPO_02` (*Thể loại từ VN*, 414 tr) | `CV04_VPO_03` (*Thơ văn Lý–Trần 2*, 795 tr) | Tổng số trang |
| :--- | :--- | :--- | :--- | :---: |
| **1. Phạm Chấn Khoa** (`khoa`) | 94 tr (`PDF 8–101` / Sách `2–95`) | 104 tr (`PDF 134–237` / Sách `127–230`) | 199 tr (`PDF 17–216` / Sách `19–218`) | **397 trang** |
| **2. Trần Trung Hiếu** (`hieu`) | 94 tr (`PDF 102–195` / Sách `96–189`) | 104 tr (`PDF 238–341` / Sách `231–334`) | 199 tr (`PDF 217–415` / Sách `219–417`) | **397 trang** |
| **3. Lê Gia Khánh** (`khanh`) | 94 tr (`PDF 196–289` / Sách `190–283`) | 103 tr (`PDF 342–444` / Sách `335–437`) | 199 tr (`PDF 416–647` / Sách `418–649`) | **396 trang** |
| **4. Cái Hoàng Bảo Kin** (`kin`) | 92 tr (`PDF 290–381` / Sách `284–375`) | 103 tr (`PDF 445–547` / Sách `438–540`) | 198 tr (`PDF 648–861` / Sách `650–863`) | **393 trang** |

---

## Lệnh Trích Xuất Ảnh 300 DPI Dành Riêng Cho Phần Của Khánh (`396 trang`)

Khánh chỉ cần chạy 3 lệnh dưới đây trên máy Windows của mình để xuất toàn bộ 396 trang PNG 300 DPI thuộc phạm vi của Khánh:

```powershell
# 1. Cuốn VPO_01 (Hán Văn Tinh Túy): PDF trang 196 đến 289 (94 trang, gồm cả trang chẵn và trang lẻ Dịch thơ)
python main.py extract --book VPO_01 --pages 196-289 --dpi 300

# 2. Cuốn VPO_02 (Thể loại từ VN thời trung đại): PDF trang 342 đến 444 (103 trang)
python main.py extract --book VPO_02 --pages 342-444 --dpi 300

# 3. Cuốn VPO_03 (Thơ văn Lý - Trần 2): PDF trang 416 đến 492 và 526 đến 647 (199 trang, đã trừ 2 bài chữ Nôm 493-525)
python main.py extract --book VPO_03 --pages 416-492,526-647 --dpi 300
```

---

## Quy Chuẩn Bắt Buộc Theo Nhận Xét Mới Nhất Của Chị Lưu Như (22/11)

1. **Dòng tiêu đề từng bài (`Title Row`)**:
   - Trước nội dung chính của mỗi bài thơ/văn trong tuyển tập, bắt buộc có **1 dòng tiêu đề riêng**.
   - Các thành phần của tiêu đề (Chữ Hán gốc, Dịch âm, Dịch nghĩa, Dịch thơ nếu có) đặt đúng vào 4 cột tương ứng.
2. **Định dạng 4 cột đồng nhất cho cả 3 cuốn (`Hán` – `Dịch âm` – `Dịch nghĩa` – `Dịch thơ`)**:
   - **`CV04_VPO_01` (*Hán Văn Tinh Túy*)**: Lấy cả phần **Dịch thơ** ở các trang lẻ đối diện (`PDF 9, 11, 13...`) ghép vào cột 4; riêng bài cuối (*Thu dạ hoài ngâm*, `PDF 367–381`) để trống cột `Dịch nghĩa`.
   - **`CV04_VPO_02` (*Thể loại từ VN*)**: Đưa phần *Phiên âm* vào cột `Dịch âm`, *Dịch nghĩa* vào cột `Dịch nghĩa`, và *Dịch theo nguyên điệu* vào cột `Dịch thơ`.
   - **`CV04_VPO_03` (*Thơ văn Lý – Trần 2*)**: Các bài thơ/kệ điền đủ 4 cột; các bài văn xuôi không có dịch thơ thì để trống cột `Dịch thơ` (`""`); văn biền ngẫu có thể dóng vào cột `Dịch thơ`.
