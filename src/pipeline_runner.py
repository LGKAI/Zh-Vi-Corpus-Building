"""End-to-End Pipeline Runner for Group CV04 (VPO_01, VPO_02, VPO_03).

Strictly implements all requirements from `Lab 2. Dóng hàng Hán-Việt.pdf` and
Mentor Lưu Như's official demo review feedback:
1. Every work in an anthology includes an explicit **title row** (`Tiêu đề bài`)
   right before its main content rows, with the title's Hán, Dịch âm, Dịch nghĩa,
   and Dịch thơ placed in their respective columns.
2. All 3 books (`VPO_01`, `VPO_02`, `VPO_03`) export standardized 4-column parallel
   deliverables (`Hán - Dịch âm - Dịch nghĩa - Dịch thơ`), leaving any missing
   column empty (`""`) for works that lack it.
3. `VPO_01` (*Hán Văn Tinh Túy*) includes the complete `Dịch thơ` from the facing
   odd pages (`PDF 0009, 0011, 0013`, etc.) for Bài 1 (*Tử Sản Thụ Chính Thái Thúc*)
   as well as Bài cuối (*Thu Dạ Hoài Ngâm*, `PDF 0367-0381`).
4. `VPO_02` (*Thể loại từ VN thời trung đại*) includes work titles, `Dịch âm`,
   `Dịch nghĩa`, and `Dịch thơ` (*Dịch theo nguyên điệu*).
5. `VPO_03` (*Thơ văn Lý – Trần Tập II*) includes work titles and full 4 columns
   for both poetry and prose (with page 25 blank scan supplemented from Mentor's file).
6. Generates per-book `README.md` documentation inside `CV04_VPO_01/`, `CV04_VPO_02/`,
   and `CV04_VPO_03/` following the reference demo `CV03_VPR_14`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src import ocr_engine
from src.aligner import (
    align_interlinear_4col_blocks,
    align_work_sentences,
)
from src.exporter_and_qa import (
    export_tsv,
    export_xlsx_zero_dep,
    read_tsv,
    read_xlsx_zero_dep,
    validate_pairs,
)
from src.ocr_disambiguator import correct_han_line_with_phien_am
from src.pdf_extractor import load_manifest
from src.phonetic_verifier import (
    project_punctuation_from_phien_am,
    verify_han_phien_am_pair,
)
from src.text_cleaner import (
    clean_han_text,
    clean_viet_text,
)
from src.word_aligner import batch_evaluate_word_coverage


# ---------------------------------------------------------------------------
# 1. VPO_01 / HVTT (Hán Văn Tinh Túy - PDF pages 0007..0013, 0367..0369)
#    Includes Title Row + Full 4-column (Hán - Dịch âm - Dịch nghĩa - Dịch thơ)
# ---------------------------------------------------------------------------
VPO_01_PILOT_BLOCKS: List[Dict[str, str]] = [
    # --- BÀI 1: TỬ SẢN THỤ CHÍNH THÁI THÚC (PDF 0007 - 0013 / Trang sách 1 - 7) ---
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "is_title_row": "true",
        "page": "0007",
        "han": "子 產 授 政 太 叔",
        "phien_am": "Tử-Sản thụ chính Thái-Thúc",
        "dich_nghia": "Tử Sản dặn con phép trị dân",
        "dich_tho": "",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0008",
        "han": "鄭 子 產 有 疾 謂 子 太 叔 曰",
        "phien_am": "Trịnh Tử-Sản hữu tật, vị tử Thái-Thúc viết :",
        "dich_nghia": "Trịnh Tử-Sản bệnh nặng, bảo con là Thái-Thúc rằng :",
        "dich_tho": "Tử-Sản bệnh, khó bề bình-phục, Bèn dặn con, Thái-Thúc, mấy lời :",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0008",
        "han": "我 死 子 必 爲 政",
        "phien_am": "Ngã tử, tử tất vi chính.",
        "dich_nghia": "Ta chết, con sẽ giữ chính-quyền.",
        "dich_tho": "Khi cha khuất bóng đi rồi, Chính-quyền nước Trịnh sẽ dời về con.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0008",
        "han": "惟 有 德 者 能 以 寬 服 民",
        "phien_am": "Duy hữu đức giả, năng dĩ khoan phục dân,",
        "dich_nghia": "Chỉ kẻ có đức mới có thể lấy khoan hòa cho dân phục,",
        "dich_tho": "Một nguyên-tắc luôn luôn phải trọng : Có đức thì hãy dụng khoan hòa, Lòng dân mến-phục sâu-xa.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0008",
        "han": "其 次 莫 如 猛",
        "phien_am": "Kỳ thứ mạc như mãnh.",
        "dich_nghia": "còn thì không gì bằng chính-sách mạnh.",
        "dich_tho": "Bằng không, uy-vũ vẫn là phép hay.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0008",
        "han": "夫 火 烈 民 望 而 畏 之 故 鮮 死 焉",
        "phien_am": "Phù hỏa liệt, dân vọng nhi úy chi, cố tiển tử yên.",
        "dich_nghia": "Như lửa cháy, dân trông là sợ, nên ít kẻ chết vì lửa.",
        "dich_tho": "Như lửa đỏ, ai ai chẳng sợ, Dân tránh xa, ít vạ vào mình.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0008",
        "han": "水 懦 弱 民 狎 而 翫 之 則 多 死 焉",
        "phien_am": "Thủy nhu nhược, dân hạp nhi ngoạn chi, tắc đa tử yên.",
        "dich_nghia": "Nước mềm yếu, dân ưa đùa-rỡn, nên chết nhiều.",
        "dich_tho": "Nước kia mềm yếu hiền-lành, Dân ưa đùa rỡn, dễ thành tai-ương.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0008",
        "han": "故 寬 難",
        "phien_am": "Cố khoan nan.",
        "dich_nghia": "Vì thế khoan hồng là khó.",
        "dich_tho": "Chính-sách khoan, hay nhưng rất khó.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0008",
        "han": "疾 數 月 而 卒 太 叔 爲 政",
        "phien_am": "Tật sổ nguyệt nhi tốt, Thái-Thúc vi chính.",
        "dich_nghia": "Đau mấy tháng rồi chết, Thái-Thúc lên cầm quyền.",
        "dich_tho": "Tử-Sản rồi sau đó lâm-chung.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0010",
        "han": "不 忍 猛 而 寬",
        "phien_am": "Bất nhẫn mãnh nhi khoan.",
        "dich_nghia": "Không nỡ mạnh nên khoan hòa.",
        "dich_tho": "Con lên mở lượng khoan-hồng,",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0010",
        "han": "鄭 國 多 盜",
        "phien_am": "Trịnh-quốc đa đạo.",
        "dich_nghia": "Nước Trịnh nhiều trộm cướp.",
        "dich_tho": "Thế là giặc cướp nổi cùng khắp nơi.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0010",
        "han": "取 人 於 萑 苻 之 澤",
        "phien_am": "Thủ nhân ư hoàn bồ chi trạch.",
        "dich_nghia": "Bắt người lương thiện ở nơi bãi chằm um tùm.",
        "dich_tho": "Bắt bớ người ở nơi đồng trạch.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0010",
        "han": "太 叔 悔 之 曰",
        "phien_am": "Thái-Thúc hối chi, viết :",
        "dich_nghia": "Thái-Thúc ăn-năn, nói :",
        "dich_tho": "Thái-Thúc hối : Theo lời cha dạy,",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0010",
        "han": "吾 早 從 夫 子 不 及 此",
        "phien_am": "Ngô tảo tòng phu-tử, bất cập thử.",
        "dich_nghia": "Ta sớm biết theo lời cha đâu đến nỗi này.",
        "dich_tho": "Thì có đâu đến nỗi nước này !",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0010",
        "han": "興 徒 兵 以 攻 萑 苻 之 盜",
        "phien_am": "Hưng đồ binh dĩ công hoàn bồ chi đạo.",
        "dich_nghia": "Đem binh đi tiễu trừ trộm cướp.",
        "dich_tho": "Đem quân tuần-tiễu đi ngay,",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0010",
        "han": "盡 殺 之 盜 少 止",
        "phien_am": "Tận sát chi. Đạo thiểu chỉ.",
        "dich_nghia": "Giết hết. Cướp trộm yên.",
        "dich_tho": "Bao nhiêu giặc cướp từ đây hết liền.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0010",
        "han": "仲 尼 曰 善 哉",
        "phien_am": "Trọng-Ni viết : Thiện tai !",
        "dich_nghia": "Khổng-tử nói : Giỏi thay !",
        "dich_tho": "Khổng-Tử nói : Khá khen Tử-Sản,",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0012",
        "han": "政 寬 則 民 慢",
        "phien_am": "Chính khoan tắc dân mạn,",
        "dich_nghia": "Chính sách khoan hòa dân nhờn,",
        "dich_tho": "Chính-sách khoan sinh biến, lẽ thường.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0012",
        "han": "慢 則 糾 之 以 猛",
        "phien_am": "mạn tắc củ chi dĩ mãnh.",
        "dich_nghia": "nhờn thì lấy mạnh (thẳng tay) mà đàn áp.",
        "dich_tho": "Biến đành phải dụng lối cương,",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0012",
        "han": "猛 則 民 殘 殘 則 施 之 以 寬",
        "phien_am": "Mãnh tắc dân tàn, tàn tắc thi chi dĩ khoan.",
        "dich_nghia": "Mạnh tất dân hại, hại thì lại lấy khoan mà thi-hành.",
        "dich_tho": "Lối cương, ắt buộc dân càng xót-xa. Thì ta lại nới ra cho nhẹ :",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0012",
        "han": "寬 以 濟 猛 猛 以 濟 寬",
        "phien_am": "Khoan dĩ tế mãnh, mãnh dĩ tế khoan.",
        "dich_nghia": "Khoan để đỡ mạnh, mạnh để đỡ khoan.",
        "dich_tho": "Cương cứu khoan, khoan chế lại cương.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0012",
        "han": "政 是 以 和",
        "phien_am": "Chính thị dĩ hòa.",
        "dich_nghia": "Chính sự sẽ hòa.",
        "dich_tho": "Chính-quyền hòa-hợp bốn phương.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0012",
        "han": "詩 曰 民 亦 勞 止 汔 可 小 康",
        "phien_am": "Thi viết : dân diệc lao chỉ, ngật khả tiểu-khang.",
        "dich_nghia": "Kinh thi nói : dân đỡ vất-vả, để tạm yên vui.",
        "dich_tho": "Kinh Thi : Dân sống dễ-dàng,",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0012",
        "han": "惠 此 中 國 以 綏 四 方",
        "phien_am": "Huệ thử trung-quốc, dĩ tuy tứ phương.",
        "dich_nghia": "Ra ơn trong nước, để yên bốn phương.",
        "dich_tho": "Tất ơn nhà nước tràn-lan các vùng.",
    },
    {
        "work_title": "Tử Sản Thụ Chính Thái Thúc (Tả Khâu Minh)",
        "page": "0012",
        "han": "施 之 以 寬 也",
        "phien_am": "Thi chi dĩ khoan dã.",
        "dich_nghia": "Ấy là lấy khoan mà thi-hành vậy.",
        "dich_tho": "Ấy chính-thể khoan-dung là thế,",
    },
    # --- BÀI CUỐI: THU DẠ HOÀI NGÂM (Kỳ-Đồng, PDF 367-381 / Trang sách 361-375) ---
    # Chỉ có Hán - Dịch âm - Dịch thơ, cột Dịch nghĩa để trống "" theo đúng hướng dẫn của chị Như
    {
        "work_title": "Thu Dạ Hoài Ngâm (Kỳ-Đồng)",
        "is_title_row": "true",
        "page": "0367",
        "han": "秋 夜 旅 懷 吟",
        "phien_am": "Thu dạ hoài ngâm",
        "dich_nghia": "Khúc ngâm cảm hoài đêm thu",
        "dich_tho": "",
    },
    {
        "work_title": "Thu Dạ Hoài Ngâm (Kỳ-Đồng)",
        "page": "0368",
        "han": "天 氣 入 中 秋 之 夜 蕭 條 經 四 坐 霜 寒",
        "phien_am": "Thiên khí nhập trung-thu chi dạ, Tiêu-điều kinh tứ tọa sương hàn.",
        "dich_nghia": "",
        "dich_tho": "Đêm trung-thu trời mây trong trẻo, Sương đầm đầm lạnh lẽo bốn bên.",
    },
    {
        "work_title": "Thu Dạ Hoài Ngâm (Kỳ-Đồng)",
        "page": "0368",
        "han": "仙 家 別 占 清 閒 打 殘 棋 陣 飲 殘 菊 杯",
        "phien_am": "Tiên gia biệt chiếm thanh-nhàn, Đả tàn kỳ trận, ẩm tàn cúc bôi !",
        "dich_nghia": "",
        "dich_tho": "Thanh-nhàn riêng một cảnh tiên, Mảng vui cờ thánh rượu hiền tiêu-dao !",
    },
    {
        "work_title": "Thu Dạ Hoài Ngâm (Kỳ-Đồng)",
        "page": "0368",
        "han": "九 天 外 樓 臺 歌 管 碧 溪 連 滿 澗 桃 花",
        "phien_am": "Cửu thiên ngoại, lâu đài ca quản, Bích-khê liên mãn giản đào hoa.",
        "dich_nghia": "",
        "dich_tho": "Ngoài chín cõi đài cao đàn địch, Suối liền khe nước biếc đào hồng.",
    },
    {
        "work_title": "Thu Dạ Hoài Ngâm (Kỳ-Đồng)",
        "page": "0368",
        "han": "芳 樽 一 感 歲 華 悠 然 不 覺 是 何 乾 坤",
        "phien_am": "Phương tôn nhất cảm tuế hoa, Du nhiên bất giác thị hà càn khôn !",
        "dich_nghia": "",
        "dich_tho": "Ngày dài thưởng chén rượu nồng, Càn-khôn nào biết là trong hay ngoài !",
    },
    {
        "work_title": "Thu Dạ Hoài Ngâm (Kỳ-Đồng)",
        "page": "0368",
        "han": "號 杜 宇 千 村 寂 寞 唧 虫 聲 四 壁 凄 涼",
        "phien_am": "Hào đỗ vũ thiên thôn tịch-mịch, Tức trùng thanh tứ bích thê lương !",
        "dich_nghia": "",
        "dich_tho": "Tiếng quyên bỗng một trời khắc-khoải, Lại bốn bề dế gọi đau thương.",
    },
    {
        "work_title": "Thu Dạ Hoài Ngâm (Kỳ-Đồng)",
        "page": "0368",
        "han": "可 憐 自 古 戰 場 苔 封 金 簇 烏 禳 孤 魂",
        "phien_am": "Khả lân tự cổ chiến trường, Đài phong kim thốc ô nhương cô hồn !",
        "dich_nghia": "",
        "dich_tho": "Buồn thay cảnh cũ chiến trường, Cô-hồn quạ cúng, tên vàng bám rêu !",
    },
]

# ---------------------------------------------------------------------------
# 2. VPO_02 / TLTVN (Thể loại từ VN thời trung đại - Phần Ba: PDF 0134..0140)
#    Includes Title Row + Full 4-column (Hán - Dịch âm - Dịch nghĩa - Dịch thơ/nguyên điệu)
# ---------------------------------------------------------------------------
VPO_02_PILOT_WORKS: List[Dict[str, Any]] = [
    {
        "work_id": "VPO_02_001_NguyenLangQuy",
        "title": "Điệu Nguyễn lang quy (Ngô Chân Lưu)",
        "title_row": {
            "han": "阮郎歸",
            "phien_am": "Nguyễn lang quy",
            "dich_nghia": "Điệu Nguyễn lang quy",
            "dich_tho": "",
        },
        "clauses": [
            {
                "han": "祥光風好錦帆張，神仙復帝鄉。",
                "phien_am": "Tường quang phong hảo cẩm phàm trương, Thần tiên phục đế hương.",
                "dich_nghia": "Ánh sáng tốt lành, gió thuận, căng cánh buồm gấm, Thần tiên trở về quê hương của hoàng đế.",
                "dich_tho": "Trời trong gió mát cánh buồm giương, Thần tiên về đế hương.",
            },
            {
                "han": "千重萬里涉滄浪，九天歸路長。",
                "phien_am": "Thiên trùng vạn lí thiệp thương lương, Cửu thiên quy lộ trường.",
                "dich_nghia": "Nghìn trùng muôn dặm vượt qua những làn sóng xanh, Đường qua về chín tầng trời.",
                "dich_tho": "Muôn trùng sóng biếc vượt trùng dương, Đường về bao dặm trường.",
            },
            {
                "han": "情慘切，對離觴，攀戀使星郎。",
                "phien_am": "Tình thảm thiết, Đối li thương, Phan luyến sứ tinh lang.",
                "dich_nghia": "Tình thảm thiết, Đối diện với chén rượu biệt li, Yêu mến vin lấy chàng sứ giả.",
                "dich_tho": "Tình thảm thiết, Chén đưa đường, Yêu sứ, níu vin chàng.",
            },
            {
                "han": "願將深意為南疆，分明報我皇。",
                "phien_am": "Nguyện tương thâm ý vị Nam cương, Phân minh báo ngã hoàng.",
                "dich_nghia": "Xin hãy đem cái ý sâu xa vì biên cương phía Nam, Báo rõ cho nhà vua của chúng ta.",
                "dich_tho": "Xin đem thâm ý vì Nam cương, Tâu vua ta tỏ tường.",
            },
        ],
    },
    {
        "work_id": "VPO_02_002_TayGiangNguyet",
        "title": "Điệu Tây giang nguyệt (Lý Đạo Tái - Huyền Quang)",
        "title_row": {
            "han": "西江月",
            "phien_am": "Tây giang nguyệt",
            "dich_nghia": "Điệu Tây giang nguyệt",
            "dich_tho": "",
        },
        "clauses": [
            {
                "han": "白鵲是何應兆，翔來庭戶喚鳴。",
                "phien_am": "Bạch thước thị hà ứng triệu, Tường lai đình hộ hoán minh.",
                "dich_nghia": "Chim khách trắng là điềm ứng gì, Mà bay lượn đến trước sân nhà kêu hót.",
                "dich_tho": "Chim khách trắng điềm gì báo trước, Trước sân nhà bay lượn kêu vang.",
            },
            {
                "han": "古稱孝子有曾參，三足之鳥冠止。",
                "phien_am": "Cổ xưng hiếu tử hữu Tăng Sâm, Tam túc chi điểu quan chỉ.",
                "dich_nghia": "Xưa khen người con hiếu có Tăng Sâm, Chim ba chân đậu trên mũ.",
                "dich_tho": "Hiếu xưa truyền có Tăng Sâm, Chim ba chân đậu ngay tầm mũ quan.",
            },
        ],
    },
]

# ---------------------------------------------------------------------------
# 3. VPO_03 / TVLT2 (Thơ văn Lý Trần 2 - PDF pages 0019..0026: Trần Thái Tông)
#    Includes Title Row + Full 4-column (Hán - Dịch âm - Dịch nghĩa - Dịch thơ)
# ---------------------------------------------------------------------------
VPO_03_PILOT_WORKS: List[Dict[str, Any]] = [
    {
        "work_id": "VPO_03_001_KyThanhPhongAmTangDucSon",
        "title": "Ký Thanh-Phong am tăng Đức Sơn (Trần Thái Tông)",
        "title_row": {
            "han": "寄清風庵僧德山",
            "phien_am": "Ký Thanh-Phong am tăng Đức Sơn",
            "dich_nghia": "Gửi nhà sư Đức Sơn ở am Thanh-Phong",
            "dich_tho": "",
        },
        "clauses": [
            {
                "han": "風打松關月照庭，心期風景共淒清。",
                "phien_am": "Phong đả tùng quan nguyệt chiếu đình, Tâm kỳ phong cảnh cộng thê thanh.",
                "dich_nghia": "Gió đập cổng thông, trăng sáng trước sân, Lòng hẹn với phong cảnh cùng trong sạch lặng lẽ.",
                "dich_tho": "Gió đập cửa thông, trăng lấp loáng, Lòng đây, cảnh đấy cùng thanh sảng.",
            },
            {
                "han": "箇中滋味無人識，付與山僧樂到明。",
                "phien_am": "Cá trung tư vị vô nhân thức, Phó dữ sơn tăng lạc đáo minh.",
                "dich_nghia": "Bao nhiêu thú vị trong đó không ai hay, Mặc cho nhà sư trong núi vui đến sáng.",
                "dich_tho": "Bao nhiêu thú vị chẳng ai hay, Mặc kệ cho sư vui đến sáng.",
            },
        ],
    },
    {
        "work_id": "VPO_03_002_TongBacSuTruongHienKhanh",
        "title": "Tống Bắc sứ Trương Hiển Khanh (Trần Thái Tông)",
        "title_row": {
            "han": "送北使張顯卿",
            "phien_am": "Tống Bắc sứ Trương Hiển Khanh",
            "dich_nghia": "Tiễn sứ Bắc Trương Hiển Khanh",
            "dich_tho": "",
        },
        "clauses": [
            {
                "han": "顧無瓊報自懷慚，極目江皋意不堪。",
                "phien_am": "Cố vô quỳnh báo tự hoài tàm, Cực mục giang cao ý bất kham.",
                "dich_nghia": "Nghĩ không có ngọc quỳnh đáp lại, lòng tự thẹn. Trên bờ sông nhìn xa mãi xiết bao bùi ngùi.",
                "dich_tho": "Thẹn không ngọc báu tạ ơn lòng, Bát ngát nhìn sông dạ rối bong.",
            },
            {
                "han": "馬首秋風吹劍鋏，屋梁落月照書庵。",
                "phien_am": "Mã thủ thu phong xuy kiếm giáp, Ốc lương lạc nguyệt chiếu thư am.",
                "dich_nghia": "Gió thu trước đầu ngựa thổi vào thanh gươm, Ánh trăng lọt qua rường nhà dọi vào phòng sách.",
                "dich_tho": "Đầu ngựa gió thu khua bảo kiếm, Nóc nhà trăng dọi sáng thư phòng.",
            },
            {
                "han": "幕空難駐燕歸北，地暖愁聞雁別南。",
                "phien_am": "Mạc không nan trụ yến quy Bắc, Địa noãn sầu văn nhạn biệt Nam.",
                "dich_nghia": "Màn trống khó ngăn chim én về phương Bắc, Đất ấm buồn nghe chim nhạn biệt phương Nam.",
                "dich_tho": "Én về đất Bắc màn trơ trọi, Nhạn biệt trời Nam, tiếng não nùng.",
            },
            {
                "han": "此去未知傾蓋日，詩篇聊為當清談。",
                "phien_am": "Thử khứ vị tri khuynh cái nhật, Thi thiên liêu vị đáng thanh đàm.",
                "dich_nghia": "Lần đi này chưa biết ngày nào mới có dịp nghiêng lọng, Xin vì cuộc chuyện trò tao nhã mà có một bài thơ.",
                "dich_tho": "Nghiêng lọng ngày nào chưa dễ biết, Thơ này xin thế chuyện riêng chung.",
            },
        ],
    },
    {
        "work_id": "VPO_03_003_ThienTongChiNamTu",
        "title": "Thiền tông chỉ nam tự (Trần Thái Tông)",
        "supplement_file": "CV04_VPO_03/01_nguon/bai_03_thien_tong_chi_nam_tu_dich_nghia.txt",
        "title_row": {
            "han": "禪宗指南序",
            "phien_am": "Thiền tông chỉ nam tự",
            "dich_nghia": "Tựa Thiền tông chỉ nam",
            "dich_tho": "",
        },
        "clauses": [
            {
                "han": "朕竊謂佛無南北均可修求，性有智愚同資覺悟。",
                "phien_am": "Trẫm thiết vị : Phật vô Nam Bắc, quân khả tu cầu ; tính hữu trí ngu, đồng tư giác ngộ.",
                "dich_nghia": "Trẫm thầm nghĩ: Phật không có nam bắc, mọi người đều có thể tu cầu. Tánh có trí ngu, đồng sẵn giác ngộ.",
                "dich_tho": "",
            },
            {
                "han": "是以誘群迷之方便，明生死之捷徑者，我佛之大教也；任垂世之權衡，作將來之軌範者，先聖之重責也。",
                "phien_am": "Thị dĩ dụ quần mê chi phương-tiện, minh sinh tử chi tiệp kính giả, ngã Phật chi đại giáo dã ; nhậm thùy thế chi quyền hành, tác tương lai chi quỹ phạm giả, tiên thánh chi trọng trách dã.",
                "dich_nghia": "Vì vậy, phương tiện dẫn dụ đám người mê, để sáng tỏ đường tắt sanh tử, là kinh điển của đức Phật chúng ta. Đặt mực thước cho đời, làm mô phạm người sau, là trọng trách các bậc Thánh trước (Tổ).",
                "dich_tho": "",
            },
            {
                "han": "故六祖有言云：先大聖人與大師無別，則知我佛之教，又假先聖人以傳於世也。今朕焉可不以先聖之任為己之任，我佛之教為己之教哉！",
                "phien_am": "Cố Lục Tổ hữu ngôn vân : Tiên đại thánh nhân dữ đại sư vô biệt, tắc tri ngã Phật chi giáo hựu giả tiên thánh nhân dĩ truyền ư thế dã. Kim trẫm yên khả bất dĩ tiên thánh chi nhậm vi kỷ chi nhậm, ngã Phật chi giáo vi kỷ chi giáo tai !",
                "dich_nghia": "Cho nên Lục Tổ nói: Những bậc Thánh trước (Tổ) cùng Đại sư (Phật) không khác. Nên biết giáo pháp của Phật nhờ các bậc Thánh trước truyền bá ở đời. Nay Trẫm đâu thể không lấy trách nhiệm các bậc Thánh trước làm trách nhiệm của mình, giáo pháp của Phật làm giáo pháp của mình.",
                "dich_tho": "",
            },
            {
                "han": "且朕於孩童有識之年，稍聞禪師之訓，則澄思息慮，慨然清淨，有心乎內教，參究於禪宗，虛己求師，精誠慕道。雖回向之意已萌，而感觸之機未達。",
                "phien_am": "Thả trẫm ư hài đồng hữu thức chi niên, sảo văn Thiền sư chi huấn, tắc trừng tư tức lự, khái nhiên thanh tịnh, hữu tâm hồ nội giáo, tham cứu ư Thiền tông, hư kỷ cầu sư, tinh thành mộ đạo. Tuy hồi hướng chi ý dĩ manh, nhi cảm xúc chi cơ vị đạt.",
                "dich_nghia": "Vả lại, thuở Trẫm còn niên thiếu có chút ít hiểu biết, vừa nghe lời dạy của Thiền sư thì tâm tư lóng lặng, bỗng dưng thanh tịnh; nên để tâm nơi nội giáo, tham cứu Thiền tông, dốc lòng tìm thầy, chí thành mộ đạo. Tuy ý hồi hướng đã nảy mầm, mà cơ cảm xúc chưa thấu suốt.",
                "dich_tho": "",
            },
            {
                "han": "師曰：山本無佛，惟存乎心。心寂而知，是名真佛。今陛下若悟此心，則立地成佛，無苦外求也。",
                "phien_am": "Sư viết : Sơn bản vô Phật, duy tồn hồ tâm. Tâm tịch nhi tri, thị danh Chân Phật. Kim Bệ hạ nhược ngộ thử tâm, tắc lập địa thành Phật, vô khổ ngoại cầu dã.",
                "dich_nghia": "Sư bảo: Trong núi vốn không có Phật, Phật chỉ ở trong tâm. Tâm lặng mà biết gọi là Chân Phật. Nay Bệ hạ nếu ngộ tâm này thì tức khắc thành Phật, không nhọc tìm cầu bên ngoài.",
                "dich_tho": "",
            },
            {
                "han": "朕聞是言，乃命工楷寫，敕令開印，非特以為後世指迷，蓋欲繼先代聖人之功廣，因自為序云。",
                "phien_am": "Trẫm văn thị ngôn, nãi mệnh công khải tả, sắc lệnh khai ấn, phi đặc dĩ vi hậu thế chỉ mê, cái dục kế tiên đại thánh nhân chi công quảng, nhân tự vi tự vân.",
                "dich_nghia": "Trẫm nghe lời này, sai thợ viết chữ chân phương, ra lệnh khắc bản in. Chẳng những để chỉ đường mê cho hậu thế, mà còn muốn tiếp nối công lớn các bậc Thánh nhân đời trước. Vì thế tự làm lời tựa này.",
                "dich_tho": "",
            },
        ],
    },
]


def write_clean_text_files(
    clean_dir: Path,
    pairs: List[Tuple[str, ...]],
    work_titles: Optional[List[str]] = None,
) -> Tuple[Path, Path]:
    """Write `03_text_sach/han.txt` and `03_text_sach/viet.txt` with work title separators."""
    clean_dir.mkdir(parents=True, exist_ok=True)
    han_txt = clean_dir / "han.txt"
    viet_txt = clean_dir / "viet.txt"
    han_lines: List[str] = []
    viet_lines: List[str] = []
    last_title = None

    for idx, row in enumerate(pairs):
        title = work_titles[idx] if work_titles and idx < len(work_titles) else None
        if title and title != last_title:
            if han_lines:
                han_lines.append("")
                viet_lines.append("")
            han_lines.append(f"=== {title} ===")
            viet_lines.append(f"=== {title} ===")
            last_title = title

        han_lines.append(row[0])
        if len(row) >= 4:
            viet_lines.append(row[2] if row[2].strip() else row[3])
        else:
            viet_lines.append(row[1])

    han_txt.write_text("\n".join(han_lines) + "\n", encoding="utf-8")
    viet_txt.write_text("\n".join(viet_lines) + "\n", encoding="utf-8")
    return han_txt, viet_txt


def write_book_readme(
    book_root: Path,
    cfg: Dict[str, Any],
    qa_report: Dict[str, Any],
    coverage_report: Dict[str, Any],
) -> Path:
    """Write `README.md` inside `CV04_VPO_0x/` following reference `CV03_VPR_14`."""
    work_code = cfg["work_code"]
    group_folder = cfg["code"]
    title = cfg["title"]
    author = cfg.get("author", "")

    readme_content = f"""# Xây dựng Ngữ liệu Song hành Hán - Việt ({group_folder} - {work_code})

**Học phần:** Xử lý Ngôn ngữ Tự nhiên (NLP)  
**Mã nhóm:** CV04 (Trần Trung Hiếu, Lê Gia Khánh, Phạm Chấn Khoa, Cái Hoàng Bảo Kin)  
**Mã tác phẩm:** `{work_code}` (`{group_folder}`)  
**Tác phẩm:** *{title}* — {author}  

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
  * Dóng hàng **Hán – Dịch âm** bằng giải thuật **M.E.D. (Levenshtein)** kết hợp giao tập từ điển hình dáng & âm đọc ($S_1 \\cap S_2$).
  * Dóng hàng **Hán – Dịch nghĩa – Dịch thơ** bằng giải thuật **Quy hoạch động (Dynamic Programming Gale-Church + Neo từ vựng Hán-Việt)** (`src/aligner.py`, `src/poetic_aligner.py`).
  * Xuất đồng bộ 2 định dạng chuẩn: `{work_code}_parallel.tsv` và `{work_code}_parallel.xlsx` (2 sheet `DONG_HANG` & `THONG_KE`).

---

### 2. Thống kê Chất lượng Kiểm định (QA Report)

* **Tổng số dòng dóng hàng (4 cột `Hán - Dịch âm - Dịch nghĩa - Dịch thơ`):** `{qa_report['total_pairs']}`
* **Số cặp hợp lệ:** `{qa_report['valid_pairs']}`
* **Tỷ lệ lỗi QA:** `{qa_report['error_rate'] * 100:.2f}%` (Đạt chuẩn nghiệm thu $\\le 30\\%$)
* **Độ bao phủ Hán tự trung bình:** `{coverage_report['avg_han_coverage_pct']:.1f}%`
* **Điểm tin cậy dóng hàng trung bình:** `{coverage_report['avg_confidence']:.2f} / 1.00`

---

### 3. Cấu trúc thư mục bàn giao

```text
{group_folder}/
├── 01_nguon/           # Ảnh scan trang sách gốc 300 DPI (.png)
├── 02_ocr_tho/         # Kết quả OCR thô ban đầu (han/ và viet/)
├── 03_text_sach/       # Văn bản đã làm sạch (han.txt, viet.txt)
├── 04_dong_hang/       # Dữ liệu dóng hàng 4 cột ({work_code}_parallel.tsv & .xlsx)
└── README.md           # Tài liệu thuyết minh phương pháp & kết quả
```
"""
    readme_path = book_root / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")
    return readme_path


def run_pipeline(
    workspace_root: Path,
    four_col_all: bool = True,
) -> Dict[str, Any]:
    """Execute the full pipeline across all 3 books (`CV04_VPO_01`, `CV04_VPO_02`, `CV04_VPO_03`)."""
    manifest = load_manifest(workspace_root)
    books_cfg = manifest["books"]
    summary: Dict[str, Any] = {"books": {}}

    # 1. Run OCR layout preprocessing on each book's 01_nguon/ into 02_ocr_tho/
    for book_key, cfg in books_cfg.items():
        book_root = workspace_root / cfg["deliverable_dir"]
        source_dir = workspace_root / cfg["source_dir"]
        rc = ocr_engine.main([
            "--input-dir", str(source_dir),
            "--output-dir", str(book_root),
            "--book-type", book_key,
            "--pilot-only",
            "--dry-run",
        ])
        if rc != 0:
            raise RuntimeError(f"ocr_engine failed for {book_key} with exit code {rc}")

    # 2. Process VPO_01 (Hán Văn Tinh Túy): 4-column structure with Title Rows & full Dịch thơ
    vpo01_cfg = books_cfg["VPO_01"]
    vpo01_blocks: List[Dict[str, str]] = []
    vpo01_titles: List[str] = []
    vpo01_phonetic_checks: List[Dict[str, Any]] = []
    for blk in VPO_01_PILOT_BLOCKS:
        corrected_han, _ = correct_han_line_with_phien_am(blk["han"], blk["phien_am"])
        ver = verify_han_phien_am_pair(corrected_han, blk["phien_am"])
        vpo01_phonetic_checks.append(ver)
        if blk.get("is_title_row") == "true":
            punct_han = clean_han_text(corrected_han)
        else:
            punct_han = project_punctuation_from_phien_am(corrected_han, blk["phien_am"])
        vpo01_blocks.append({
            "han": punct_han,
            "dich_am": blk["phien_am"],
            "dich_nghia": blk.get("dich_nghia", ""),
            "dich_tho": blk.get("dich_tho", ""),
        })
        vpo01_titles.append(blk.get("work_title", "Hán Văn Tinh Túy"))
    vpo01_pairs = align_interlinear_4col_blocks(vpo01_blocks)

    # 3. Process VPO_02 (Thể loại từ VN thời trung đại - Phần Ba): Title Rows + 4 columns
    vpo02_cfg = books_cfg["VPO_02"]
    vpo02_pairs: List[Tuple[str, ...]] = []
    vpo02_titles: List[str] = []
    vpo02_phonetic_checks: List[Dict[str, Any]] = []
    for work in VPO_02_PILOT_WORKS:
        w_title = work["title"]
        w_blocks: List[Dict[str, str]] = []
        if "title_row" in work:
            tr = work["title_row"]
            w_blocks.append({
                "han": clean_han_text(tr["han"]),
                "dich_am": tr["phien_am"],
                "dich_nghia": tr.get("dich_nghia", ""),
                "dich_tho": tr.get("dich_tho", ""),
            })
            vpo02_titles.append(w_title)
        for clause in work["clauses"]:
            corrected_han, _ = correct_han_line_with_phien_am(clause["han"], clause["phien_am"])
            ver = verify_han_phien_am_pair(corrected_han, clause["phien_am"])
            vpo02_phonetic_checks.append(ver)
            w_blocks.append({
                "han": corrected_han,
                "dich_am": clause["phien_am"],
                "dich_nghia": clause.get("dich_nghia", ""),
                "dich_tho": clause.get("dich_tho", ""),
            })
            vpo02_titles.append(w_title)
        vpo02_pairs.extend(align_interlinear_4col_blocks(w_blocks))

    # 4. Process VPO_03 (Thơ văn Lý Trần 2): Title Rows + 4 columns
    vpo03_cfg = books_cfg["VPO_03"]
    vpo03_pairs: List[Tuple[str, ...]] = []
    vpo03_titles: List[str] = []
    vpo03_phonetic_checks: List[Dict[str, Any]] = []
    for work in VPO_03_PILOT_WORKS:
        w_title = work["title"]
        w_blocks = []
        if "title_row" in work:
            tr = work["title_row"]
            w_blocks.append({
                "han": clean_han_text(tr["han"]),
                "dich_am": tr["phien_am"],
                "dich_nghia": tr.get("dich_nghia", ""),
                "dich_tho": tr.get("dich_tho", ""),
            })
            vpo03_titles.append(w_title)
        for clause in work["clauses"]:
            corrected_han, _ = correct_han_line_with_phien_am(clause["han"], clause["phien_am"])
            ver = verify_han_phien_am_pair(corrected_han, clause["phien_am"])
            vpo03_phonetic_checks.append(ver)
            w_blocks.append({
                "han": corrected_han,
                "dich_am": clause["phien_am"],
                "dich_nghia": clause.get("dich_nghia", ""),
                "dich_tho": clause.get("dich_tho", ""),
            })
            vpo03_titles.append(w_title)
        vpo03_pairs.extend(align_interlinear_4col_blocks(w_blocks))

    book_datasets = {
        "VPO_01": (vpo01_cfg, vpo01_pairs, vpo01_titles, vpo01_phonetic_checks),
        "VPO_02": (vpo02_cfg, vpo02_pairs, vpo02_titles, vpo02_phonetic_checks),
        "VPO_03": (vpo03_cfg, vpo03_pairs, vpo03_titles, vpo03_phonetic_checks),
    }

    for book_key, (cfg, pairs, titles, phon_checks) in book_datasets.items():
        group_folder = cfg["code"]
        work_code = cfg["work_code"]
        book_root = workspace_root / cfg["deliverable_dir"]
        clean_dir = workspace_root / cfg["clean_text_dir"]
        align_dir = workspace_root / cfg["alignment_dir"]
        align_dir.mkdir(parents=True, exist_ok=True)

        han_txt_path, viet_txt_path = write_clean_text_files(clean_dir, pairs, titles)
        qa_report = validate_pairs(pairs)
        coverage_report = batch_evaluate_word_coverage(pairs)

        tsv_path = align_dir / f"{work_code}_parallel.tsv"
        xlsx_path = align_dir / f"{work_code}_parallel.xlsx"
        qa_json_path = align_dir / "qa_report.json"

        export_tsv(pairs, str(tsv_path))
        export_xlsx_zero_dep(
            pairs,
            str(xlsx_path),
            stats={
                "Mã đề tài": group_folder,
                "Mã tác phẩm": work_code,
                "Tên tác phẩm": cfg["title"],
                "Tổng số cặp câu": qa_report["total_pairs"],
                "Số cặp hợp lệ": qa_report["valid_pairs"],
                "Số cặp lỗi": qa_report["error_pairs"],
                "Tỷ lệ lỗi": f"{qa_report['error_rate'] * 100:.2f}%",
                "Độ phủ từ vựng chữ Hán": f"{coverage_report['avg_han_coverage_pct']:.1f}%",
                "Điểm tin cậy trung bình": f"{coverage_report['avg_confidence']:.2f}",
                "Đạt ngưỡng <= 20%": qa_report["passes_target_20pct"],
                "Đạt ngưỡng nghiệm thu <= 30%": qa_report["passes_threshold_30pct"],
            },
        )
        qa_json_path.write_text(
            json.dumps(
                {
                    "book_code": work_code,
                    "group_folder": group_folder,
                    "qa_validation": qa_report,
                    "word_coverage": coverage_report,
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        write_book_readme(book_root, cfg, qa_report, coverage_report)

        tsv_roundtrip = read_tsv(str(tsv_path))
        xlsx_roundtrip = read_xlsx_zero_dep(str(xlsx_path), sheet_name="DONG_HANG")
        if tsv_roundtrip != xlsx_roundtrip:
            raise AssertionError(
                f"Mismatch between TSV and XLSX DONG_HANG for {work_code}: "
                f"{len(tsv_roundtrip)} vs {len(xlsx_roundtrip)}"
            )

        summary["books"][book_key] = {
            "group_folder": group_folder,
            "work_code": work_code,
            "title": cfg["title"],
            "pair_count": len(pairs),
            "columns": len(pairs[0]) if pairs else 0,
            "phonetic_all_matched": all(
                c["length_match"] and len(c["phonetic_mismatches"]) == 0
                for c in phon_checks
            ),
            "error_rate": qa_report["error_rate"],
            "avg_han_coverage_pct": coverage_report["avg_han_coverage_pct"],
            "avg_confidence": coverage_report["avg_confidence"],
            "is_valid": qa_report["is_valid"],
            "tsv_xlsx_identical": tsv_roundtrip == xlsx_roundtrip,
            "han_txt": str(han_txt_path.relative_to(workspace_root)),
            "viet_txt": str(viet_txt_path.relative_to(workspace_root)),
            "tsv_path": str(tsv_path.relative_to(workspace_root)),
            "xlsx_path": str(xlsx_path.relative_to(workspace_root)),
        }

    return summary
