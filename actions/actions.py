import json
import re
import os
from typing import Any, Text, Dict, List, Tuple
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from fuzzywuzzy import process, fuzz

# Biến toàn cục lưu đường dẫn đến file nganh.json
NGANH_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "nganh.json")

def load_nganh_data():
    """
    Hàm đọc dữ liệu từ file nganh.json
    
    Returns:
        list: Danh sách các ngành học
    """
    try:
        with open(NGANH_JSON_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Lỗi khi đọc file JSON: {e}")
        return []

def find_similar_nganh(nganh_name, nganh_list, threshold=70):
    
    """
    Tìm kiếm ngành gần đúng sử dụng fuzzywuzzy
    
    
    Args:
        nganh_name (str): Tên ngành cần tìm
        nganh_list (list): Danh sách các ngành
        threshold (int): Ngưỡng điểm tương đồng (mặc định: 70)
        
    Returns:
        dict: Ngành học tương đồng nhất nếu điểm cao hơn ngưỡng, None nếu không tìm thấy
    """
    
    if not nganh_name or not nganh_list:
        return None
        
    # Trích xuất tên ngành từ danh sách
    nganh_names = [nganh["ten_nganh"] for nganh in nganh_list]
    
    # Tìm tên ngành tương đồng nhất
    best_match, score = process.extractOne(nganh_name, nganh_names, scorer=fuzz.token_sort_ratio)
    
    if score >= threshold:
        # Trả về đối tượng ngành đầy đủ
        for nganh in nganh_list:
            if nganh["ten_nganh"] == best_match:
                return nganh
                
    return None

class ActionXuLyTen(Action):
    """
    Hành động xử lý tên người dùng
    """
    def name(self) -> Text:
        return "action_xu_ly_ten"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Lấy tên người dùng từ slot
        ten_nguoi_dung = tracker.get_slot("ten_nguoi_dung")
        
        if not ten_nguoi_dung:
            dispatcher.utter_message(text="Tôi chưa biết tên bạn. Bạn có thể cho tôi biết tên được không?")
            return []
            
        # Xử lý tên người dùng bằng regex
        processed_name = self.process_name(ten_nguoi_dung)
        
        # Gửi lời chào với tên đã xử lý
        dispatcher.utter_message(response="utter_chao_sau_khi_biet_ten", ten_nguoi_dung=processed_name)
        
        return [SlotSet("ten_nguoi_dung", processed_name)]
    
    def process_name(self, name: Text) -> Text:
        """
        Xử lý tên người dùng:
        - Loại bỏ khoảng trắng thừa
        - Chuẩn hóa các chữ cái đầu thành chữ hoa
        - Loại bỏ các ký tự đặc biệt
        
        Args:
            name (str): Tên người dùng cần xử lý
            
        Returns:
            str: Tên đã được xử lý
        """
        if not name:
            return ""
            
        # Loại bỏ ký tự đặc biệt và số
        name = re.sub(r'[^a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂưăạảấầẩẫậắằẳẵặẹẻẽềềểỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪễếệỉịọỏốồổỗộớờởỡợụủứừỬỮỰỲỴÝỶỸửữựỳỵỷỹ\s]', '', name)
        
        # Loại bỏ khoảng trắng thừa
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Chuẩn hóa chữ cái đầu thành chữ hoa
        name = name.title()
        
        return name

class ActionTraLoiNganhTuyenSinh(Action):
    """
    Hành động trả lời về các ngành tuyển sinh
    """
    def name(self) -> Text:
        return "action_tra_loi_nganh_tuyen_sinh"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Đọc danh sách ngành từ JSON
        nganh_list = load_nganh_data()
        
        if not nganh_list:
            dispatcher.utter_message(text="Hiện tại tôi không thể cung cấp thông tin về các ngành tuyển sinh. Xin vui lòng thử lại sau.")
            return []
            
        # Tạo thông báo về các ngành
        message = "Trường Đại học Giao thông Vận tải TP.HCM đào tạo các ngành sau:\n"
        for i, nganh in enumerate(nganh_list, 1):
            message += f"\n{i}. {nganh['ten_nganh']}\n\n"
            
        dispatcher.utter_message(text=message)
        return []

class ActionTraLoiThongTinNganh(Action):
    """
    Hành động trả lời thông tin giới thiệu về ngành
    """
    def name(self) -> Text:
        return "action_tra_loi_thong_tin_nganh"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        ten_nganh = tracker.get_slot("ten_nganh")
        if not ten_nganh:
            dispatcher.utter_message(text="Bạn muốn tìm hiểu về ngành nào?")
            return []
            
        nganh_list = load_nganh_data()
        nganh = find_similar_nganh(ten_nganh, nganh_list)
        
        if nganh:
            message = f"Dưới đây là thông tin về ngành {nganh['ten_nganh']}, mã ngành {nganh['ma_nganh']}:\n\n"
            message += nganh["gioi_thieu_chung"]
            dispatcher.utter_message(text=message)
            return [SlotSet("ten_nganh", nganh["ten_nganh"])]
        else:
            dispatcher.utter_message(text=f"Tôi không tìm thấy thông tin về ngành '{ten_nganh}'. Bạn có thể kiểm tra lại tên ngành hoặc tìm hiểu về ngành khác.")
            return []

class ActionTraLoiCoHoiViecLam(Action):
    """
    Hành động trả lời về cơ hội việc làm của ngành
    """
    def name(self) -> Text:
        return "action_tra_loi_co_hoi_viec_lam"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        ten_nganh = tracker.get_slot("ten_nganh")
        if not ten_nganh:
            dispatcher.utter_message(text="Bạn muốn tìm hiểu cơ hội việc làm của ngành nào?")
            return []
            
        nganh_list = load_nganh_data()
        nganh = find_similar_nganh(ten_nganh, nganh_list)
        
        if nganh:
            message = f"Cơ hội việc làm của ngành {nganh['ten_nganh']}:\n\n"
            for i, co_hoi in enumerate(nganh["co_hoi_viec_lam"], 1):
                message += f"{i}. {co_hoi}\n"
                
            dispatcher.utter_message(text=message)
            return [SlotSet("ten_nganh", nganh["ten_nganh"])]
        else:
            dispatcher.utter_message(text=f"Tôi không tìm thấy thông tin về cơ hội việc làm của ngành '{ten_nganh}'. Bạn có thể kiểm tra lại tên ngành hoặc tìm hiểu về ngành khác.")
            return []

class ActionTraLoiDiemChuanNganh(Action):
    """
    Hành động trả lời về điểm chuẩn của ngành
    """
    def name(self) -> Text:
        return "action_tra_loi_diem_chuan_nganh"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        ten_nganh = tracker.get_slot("ten_nganh")
        nam = tracker.get_slot("nam")
        
        if not ten_nganh:
            dispatcher.utter_message(text="Bạn muốn tìm hiểu điểm chuẩn của ngành nào?")
            return []
            
        nganh_list = load_nganh_data()
        nganh = find_similar_nganh(ten_nganh, nganh_list)
        
        if not nganh:
            dispatcher.utter_message(text=f"Tôi không tìm thấy thông tin về ngành '{ten_nganh}'. Bạn có thể kiểm tra lại tên ngành hoặc tìm hiểu về ngành khác.")
            return []
            
        # Xử lý năm cụ thể nếu có
        if nam:
            # Trích xuất năm từ chuỗi (ví dụ: "năm 2024" -> "2024")
            nam_match = re.search(r'\d{4}', nam)
            if nam_match:
                nam_value = nam_match.group(0)
                if nam_value in nganh["diem_chuan"]:
                    diem = nganh["diem_chuan"][nam_value]
                    if diem is not None:
                        dispatcher.utter_message(text=f"Điểm chuẩn ngành {nganh['ten_nganh']} năm {nam_value} là: {diem} điểm.")
                    else:
                        dispatcher.utter_message(text=f"Chưa có thông tin điểm chuẩn ngành {nganh['ten_nganh']} năm {nam_value}.")
                else:
                    dispatcher.utter_message(text=f"Tôi không có thông tin về điểm chuẩn ngành {nganh['ten_nganh']} năm {nam_value}.")
            else:
                # Trường hợp người dùng nhập "năm ngoái", "năm trước", v.v.
                self.tra_loi_diem_chuan_khong_co_nam(dispatcher, nganh)
        else:
            # Trường hợp không có năm cụ thể
            self.tra_loi_diem_chuan_khong_co_nam(dispatcher, nganh)
            
        return [SlotSet("ten_nganh", nganh["ten_nganh"])]
        
    def tra_loi_diem_chuan_khong_co_nam(self, dispatcher, nganh):
        """
        Trả lời điểm chuẩn khi không có năm cụ thể
        """
        message = f"Điểm chuẩn ngành {nganh['ten_nganh']} các năm gần đây:\n\n"
        for nam, diem in nganh["diem_chuan"].items():
            if diem is not None:
                message += f"Năm {nam}: {diem} điểm\n"
                
        dispatcher.utter_message(text=message)

class ActionTraLoiKhoiXetTuyen(Action):
    """
    Hành động trả lời về khối xét tuyển của ngành
    """
    def name(self) -> Text:
        return "action_tra_loi_khoi_xet_tuyen"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        ten_nganh = tracker.get_slot("ten_nganh")
        if not ten_nganh:
            dispatcher.utter_message(text="Bạn muốn tìm hiểu khối xét tuyển của ngành nào?")
            return []
            
        nganh_list = load_nganh_data()
        nganh = find_similar_nganh(ten_nganh, nganh_list)
        
        if nganh:
            message = f"Khối xét tuyển của ngành {nganh['ten_nganh']} là: "
            message += ", ".join(nganh["khoi_xet_tuyen"])
            
            dispatcher.utter_message(text=message)
            return [SlotSet("ten_nganh", nganh["ten_nganh"])]
        else:
            dispatcher.utter_message(text=f"Tôi không tìm thấy thông tin về khối xét tuyển của ngành '{ten_nganh}'. Bạn có thể kiểm tra lại tên ngành hoặc tìm hiểu về ngành khác.")
            return []
        
# Thêm các hàm tư vấn ngành theo điểm và sở thích
class ActionTuVanNganhTheoDiem(Action):
    """
    Hành động tư vấn ngành học dựa trên điểm thi của thí sinh
    """
    def name(self) -> Text:
        return "action_tu_van_nganh_theo_diem"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Trích xuất thông tin điểm từ tin nhắn của người dùng
        message = tracker.latest_message.get('text', '')
        diem_pattern = r'(\d{1,2}(\.\d+)?)\s*(?:điểm|diem)'
        diem_matches = re.findall(diem_pattern, message)
        
        diem = None
        if diem_matches:
            try:
                diem = float(diem_matches[0][0])
            except (ValueError, IndexError):
                pass
        
        if not diem:
            # Tìm số điểm từ các cụm từ thông thường
            diem_pattern = r'(\d{1,2}(\.\d+)?)'
            diem_matches = re.findall(diem_pattern, message)
            
            if diem_matches:
                try:
                    # Lấy số điểm đầu tiên tìm thấy
                    diem = float(diem_matches[0][0])
                except (ValueError, IndexError):
                    pass
        
        if not diem:
            dispatcher.utter_message(text="Xin lỗi, tôi không xác định được điểm của bạn. Vui lòng cho biết tổng điểm 3 môn là bao nhiêu?")
            return []
        
        # Đọc danh sách ngành từ JSON
        nganh_list = load_nganh_data()
        
        if not nganh_list:
            dispatcher.utter_message(text="Hiện tại tôi không thể cung cấp thông tin về các ngành tuyển sinh. Xin vui lòng thử lại sau.")
            return []
        
        # Tư vấn dựa theo mức điểm
        suitable_nganh = []
        
        # Lấy điểm chuẩn các ngành năm gần nhất
        latest_year = "2024"  # Năm mới nhất trong dữ liệu
        
        for nganh in nganh_list:
            if latest_year in nganh["diem_chuan"] and nganh["diem_chuan"][latest_year] is not None:
                diem_chuan = nganh["diem_chuan"][latest_year]
                
                # Phân loại theo mức độ phù hợp
                if diem >= diem_chuan + 2:  # Dư điểm nhiều
                    suitable_nganh.append((nganh["ten_nganh"], diem_chuan, "rất phù hợp"))
                elif diem >= diem_chuan:  # Đủ điểm
                    suitable_nganh.append((nganh["ten_nganh"], diem_chuan, "phù hợp"))
                elif diem >= diem_chuan - 2:  # Thiếu điểm không nhiều
                    suitable_nganh.append((nganh["ten_nganh"], diem_chuan, "có thể cân nhắc"))
        
        # Sắp xếp theo mức độ phù hợp
        suitable_nganh.sort(key=lambda x: (
            0 if x[2] == "rất phù hợp" else 1 if x[2] == "phù hợp" else 2,
            x[1]  # Sau đó sắp xếp theo điểm chuẩn để ưu tiên ngành có điểm cao hơn
        ))
        
        if suitable_nganh:
            message = f"Với {diem} điểm, bạn có thể tham khảo các ngành sau:\n\n"
            
            for i, (ten_nganh, diem_chuan, muc_do) in enumerate(suitable_nganh[:5], 1):
                message += f"{i}. {ten_nganh} (điểm chuẩn: {diem_chuan}) - {muc_do}\n"
                
            message += "\nBạn có muốn biết thêm thông tin về ngành nào trong số này không?"
        else:
            message = f"Với mức điểm {diem}, bạn có thể cân nhắc các ngành có điểm chuẩn thấp hơn hoặc cân nhắc các phương thức xét tuyển khác như xét học bạ hoặc đánh giá năng lực."
        
        dispatcher.utter_message(text=message)
        return []

class ActionTuVanNganhTheoSoThich(Action):
    """
    Hành động tư vấn ngành học dựa trên sở thích của thí sinh
    """
    def name(self) -> Text:
        return "action_tu_van_nganh_theo_so_thich"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Lấy tin nhắn chứa sở thích của người dùng
        message = tracker.latest_message.get('text', '').lower()
        
        # Từ khóa ánh xạ sở thích với ngành học
        so_thich_nganh_mapping = {
            "máy tính": ["Công nghệ thông tin", "Kỹ thuật phần mềm", "Hệ thống thông tin", "An toàn thông tin"],
            "lập trình": ["Công nghệ thông tin", "Kỹ thuật phần mềm", "Khoa học máy tính"],
            "thiết kế": ["Kiến trúc", "Kỹ thuật công trình", "Thiết kế công nghiệp"],
            "ô tô": ["Công nghệ kỹ thuật ô tô", "Kỹ thuật cơ khí động lực"],
            "xe máy": ["Công nghệ kỹ thuật ô tô", "Kỹ thuật cơ khí động lực"],
            "động cơ": ["Công nghệ kỹ thuật ô tô", "Kỹ thuật cơ khí động lực"],
            "điện": ["Công nghệ kỹ thuật điện, điện tử", "Công nghệ kỹ thuật điều khiển và tự động hóa"],
            "điện tử": ["Công nghệ kỹ thuật điện, điện tử", "Công nghệ kỹ thuật điều khiển và tự động hóa"],
            "tự động hóa": ["Công nghệ kỹ thuật điều khiển và tự động hóa"],
            "robot": ["Công nghệ kỹ thuật điều khiển và tự động hóa", "Công nghệ kỹ thuật cơ điện tử"],
            "cơ khí": ["Công nghệ kỹ thuật cơ khí", "Công nghệ chế tạo máy"],
            "máy móc": ["Công nghệ kỹ thuật cơ khí", "Công nghệ chế tạo máy"],
            "công trình": ["Kỹ thuật xây dựng", "Kỹ thuật xây dựng công trình giao thông"],
            "xây dựng": ["Kỹ thuật xây dựng", "Kỹ thuật xây dựng công trình giao thông"],
            "cầu đường": ["Kỹ thuật xây dựng công trình giao thông"],
            "giao thông": ["Kỹ thuật xây dựng công trình giao thông", "Quy hoạch và quản lý giao thông"],
            "vận tải": ["Logistics và hạ tầng giao thông", "Quy hoạch và quản lý giao thông"],
            "logistics": ["Logistics và hạ tầng giao thông"],
            "kinh doanh": ["Quản trị kinh doanh", "Marketing", "Thương mại điện tử"],
            "quản lý": ["Quản trị kinh doanh", "Quản trị nhân lực"],
            "marketing": ["Marketing", "Thương mại điện tử"],
            "tiếng anh": ["Ngôn ngữ Anh"],
            "ngoại ngữ": ["Ngôn ngữ Anh"]
        }
        
        # Tìm các từ khóa liên quan đến sở thích trong tin nhắn
        matched_interests = []
        for keyword, nganh_list in so_thich_nganh_mapping.items():
            if keyword in message:
                matched_interests.extend(nganh_list)
        
        # Loại bỏ các ngành trùng lặp và lấy tối đa 5 ngành
        recommended_nganh = list(dict.fromkeys(matched_interests))[:5]
        
        if recommended_nganh:
            message = "Dựa trên sở thích của bạn, tôi gợi ý các ngành sau:\n\n"
            for i, nganh in enumerate(recommended_nganh, 1):
                message += f"{i}. {nganh}\n"
                
            message += "\nBạn có muốn biết thêm thông tin về ngành nào trong số này không?"
        else:
            message = "Tôi chưa xác định được sở thích rõ ràng của bạn. Bạn có thể cho tôi biết bạn thích gì hoặc quan tâm đến lĩnh vực nào không?"
        
        dispatcher.utter_message(text=message)
        return []
    
class ActionTinhKhoiVaGoiYNganh(Action):
    def name(self) -> Text:
        return "action_tinh_khoi_va_goi_y_nganh"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = tracker.latest_message.get('text', '').lower()
        
        # 1) Lấy điểm từ regex (ví dụ "8 điểm toán")
        matches: List[Tuple[str, str]] = re.findall(
            r'(\d+(?:\.\d+)?)\s*điểm\s*([^\d,]+)', text
        )
        
        # 2) Chuẩn bị danh sách ngành
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "nganh.json"), "r", encoding="utf-8") as f:
                ds_nganh = json.load(f)
        except Exception as e:
            dispatcher.utter_message(text=f"❗ Lỗi đọc dữ liệu ngành: {e}")
            return []

        # 3) Nếu có >=3 môn điểm, tính khối và lọc theo điểm chuẩn 2024
        phu_hop, can_nhac = [], []
        if len(matches) >= 3:
            m = {mat.strip(): float(s) for s, mat in matches[:3]}
            khoi_def = {
                "A00": ["toán", "lý", "hóa"],
                "A01": ["toán", "lý", "anh"],
                "B00": ["toán", "hóa", "sinh"],
                "C00": ["văn", "sử", "địa"],
                "D01": ["toán", "văn", "anh"],
                "D07": ["toán", "hóa", "anh"],
            }
            diem_khoi = {k: sum(m.get(subj, 0) for subj in subjs)
                         for k, subjs in khoi_def.items()}
            best_khoi = max(diem_khoi, key=diem_khoi.get)
            best_score = diem_khoi[best_khoi]
            dispatcher.utter_message(
                text=f"📊 Khối phù hợp nhất: *{best_khoi}* với tổng {best_score} điểm."
            )

            for ng in ds_nganh:
                if best_khoi in ng.get("khoi_xet_tuyen", []):
                    dc = ng.get("diem_chuan", {}).get("2024")
                    if dc is None:
                        continue
                    if best_score >= dc:
                        phu_hop.append(ng["ten_nganh"])
                    elif best_score + 2 >= dc:
                        can_nhac.append(ng["ten_nganh"])

            if phu_hop:
                dispatcher.utter_message("🎉 Bạn đủ điểm cho các ngành sau:")
                for ng in phu_hop:
                    dispatcher.utter_message(f"- {ng}")
            if can_nhac:
                dispatcher.utter_message("💡 Có thể cân nhắc (cách điểm chuẩn ≤2 điểm):")
                for ng in can_nhac:
                    dispatcher.utter_message(f"- {ng}")
            if not phu_hop and not can_nhac:
                dispatcher.utter_message("❗ Rất tiếc, chưa tìm được ngành nào phù hợp với điểm hiện tại.")

        else:
            dispatcher.utter_message(
                "🔍 Bạn vui lòng cung cấp ít nhất 3 môn và điểm tương ứng (ví dụ: 8 điểm Toán, 7 điểm Văn, 9 điểm Anh)."
            )

        return []