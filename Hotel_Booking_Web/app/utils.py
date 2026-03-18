import smtplib
import ssl
from email.message import EmailMessage
from config import Config
import re
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from db import get_db_connection
from datetime import datetime, date

def send_email(receiver_email, otp_code):
    try:
        subject = "Mã OTP của bạn"
        body = f"Mã OTP của bạn là: {otp_code} \n"
        body += "Mã sẽ có hiệu lực trong vòng 5 phút!"
        
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = Config.SENDER_EMAIL
        msg["To"] = receiver_email

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT, context=context) as server:
            server.login(Config.SENDER_EMAIL, Config.APP_PASSWORD)
            server.send_message(msg)
        return True  
    except Exception as e:
        print("Lỗi gửi email:", e)
        return False 
def send_booking_confirmation_email(receiver_email, booking_data):
    try:
        subject = f"[Xác nhận] Đặt phòng thành công #{booking_data['invoice_id']} - {booking_data['hotel_name']}"
        body = f"""
        Thân gửi {booking_data['customer_name']},

        Chúng tôi vui mừng xác nhận đơn đặt phòng của quý khách tại {booking_data['hotel_name']} đã thành công!
        
        MÃ ĐẶT PHÒNG: {booking_data['invoice_id']}
        --------------------------------------------------
        1. THÔNG TIN KHÁCH HÀNG
        - Người đặt: {booking_data['customer_name']}
        - Khách nhận phòng: {booking_data['guest_name']} (Vui lòng mang theo CCID khi nhận phòng)
        
        2. THÔNG TIN LƯU TRÚ
        - Khách sạn: {booking_data['hotel_name']}
        - Địa chỉ: {booking_data['hotel_address']}
        - SĐT Lễ tân: {booking_data['hotel_phone']}
        - Loại phòng: {booking_data['room_type_name']}
        
        - Ngày nhận phòng: 14:00 - {booking_data['check_in']}
        - Ngày trả phòng: 12:00 - {booking_data['check_out']}
        - Thời gian ở: {booking_data['duration']} đêm
        
        3. CHI TIẾT THANH TOÁN
        - Giảm giá: -{booking_data['discount']} VNĐ
        - TỔNG THANH TOÁN: {booking_data['total_price']} VNĐ
        
        4. CHÍNH SÁCH HỦY
        - Hủy miễn phí trước: 14:00 ngày {booking_data['free_cancel_date']}
        - Sau thời gian này hoặc không đến: Không hoàn tiền.
        --------------------------------------------------
        
        Nếu cần hỗ trợ, vui lòng liên hệ hotline: 0925940864.
        Cảm ơn quý khách đã lựa chọn HotelBooking!
        """
        
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = Config.SENDER_EMAIL
        msg["To"] = receiver_email

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT, context=context) as server:
            server.login(Config.SENDER_EMAIL, Config.APP_PASSWORD)
            server.send_message(msg)

        print(f"Email đã được gửi tới {receiver_email}")
        return True
    except Exception as e:
        print("Lỗi gửi email:", e)
        return False
def get_old_passwords(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password, old_password_1, old_password_2 FROM customers WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user  
def is_new_password_valid(new_password, old_passwords):
    return new_password not in old_passwords
def is_valid_password(password):
    """Kiểm tra mật khẩu phải trên 8 ký tự và chứa ít nhất 1 ký tự đặc biệt"""
    return len(password) > 8 and re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
def get_userid_from_token():
    try:
        verify_jwt_in_request(optional=True)
        user_name = get_jwt_identity()
        if not user_name:
            return None
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM customers WHERE username = %s", (user_name, ))
            user_id = cursor.fetchone()
            if user_id:
                return user_id[0] 
            return None
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Lỗi check token: {e}")
        return None
def get_hotel_id_from_room_id(room_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT hotel_id FROM roomtypes WHERE id = %s", (room_id, ))
    hotel_id_tuple = cursor.fetchone()
    cursor.close()
    conn.close()
    if hotel_id_tuple:
        return hotel_id_tuple[0]
    return None
def format_rfc1123_to_date(date_input):
    if isinstance(date_input, str):
        date_obj = datetime.strptime(date_input, '%a, %d %b %Y %H:%M:%S GMT')
        return date_obj.date().isoformat()
    elif isinstance(date_input, (datetime, date)):
        return date_input.isoformat()
    else:
        return None  
def get_service_id(service_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM additionalservices WHERE service_name = %s",(service_name, ))
    id = cursor.fetchone()
    cursor.close()
    conn.close()
    if id:
        return id["id"]
    return None
def get_sql_aggregation(report_type):
    if report_type == 'revenue':
        return "SUM(total_price)"
    elif report_type == 'orders':
        return "COUNT(id)"
    elif report_type == 'customers':
        return "COUNT(DISTINCT customer_id)"
    else:
        return "COUNT(id)"
def get_roomtypes_id_from_invoice(invoice_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT room_type_id FROM invoices WHERE id = %s", (invoice_id, ))
    room_type_id_tuple = cursor.fetchone()
    cursor.close()
    conn.close()
    return room_type_id_tuple["room_type_id"] if room_type_id_tuple else None
def send_answer_email(receiver_email, data):
    try:
        if not data:
            return False
        print(data)
        subject = f"Chủ đề: Phản hồi yêu cầu hỗ trợ #{data.get('id')}"
        
        body = f"""Thân gửi {data.get('customer_name', 'Quý khách')},

Cảm ơn bạn đã liên hệ với bộ phận hỗ trợ của HotelBooking!

Về câu hỏi của bạn liên quan đến: "{data.get('subject')}", chúng tôi xin phản hồi như sau:

{data.get('response')}

Hy vọng thông tin trên giải quyết được vấn đề của bạn. Nếu cần hỗ trợ thêm, vui lòng trả lời email này hoặc liên hệ hotline 0925940864.

Trân trọng,
Đội ngũ Hỗ trợ Khách hàng - HotelBooking!
"""

        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = Config.SENDER_EMAIL
        msg["To"] = receiver_email

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT, context=context) as server:
            server.login(Config.SENDER_EMAIL, Config.APP_PASSWORD)
            server.send_message(msg)
        
        print(f"Email đã được gửi tới {receiver_email}")
        return True

    except Exception as e:
        print("Lỗi gửi email:", e)
        return False