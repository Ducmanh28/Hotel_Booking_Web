from flask import Blueprint, request, jsonify
import mysql.connector as connect
from flask_jwt_extended import jwt_required
from app.utils import get_db_connection, get_userid_from_token
from config import Config 
import google.generativeai as genai


genai.configure(api_key=Config.API_KEY) 
model = genai.GenerativeModel('gemini-flash-lite-latest')


help_bp = Blueprint("help", __name__)
@help_bp.route("/help", methods=["GET"])
def get_all_helps():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM help")
    helps = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(helps)
@help_bp.route("/help/contact_admin", methods=["POST"])
def contact_admin():
    data = request.json
    subject = data.get("subject")
    message = data.get("message")
    email = data.get("email")
    customer_id = get_userid_from_token()
    if not customer_id and not email:
        return jsonify({"message": "Vui lòng đăng nhập hoặc nhập email để được hỗ trợ"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO support_tickets (customer_id, email, subject, message) 
            VALUES (%s, %s, %s, %s)
        """, (customer_id, email, subject, message))
        conn.commit()
        return jsonify({"message": "Gửi yêu cầu thành công!"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"message": "Lỗi hệ thống"}), 500
    finally:
        cursor.close()
        conn.close() 
@help_bp.route("/help/chat", methods=["POST"])
def chat_with_ai():
    try:
        data = request.json
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"reply": "Vui lòng nhập câu hỏi."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT question, answer FROM help")
        db_knowledge = cursor.fetchall()
        cursor.close()
        conn.close()

        knowledge_text = "\n".join([f"- Hỏi: {item['question']} | Đáp: {item['answer']}" for item in db_knowledge])
        prompt = f"""
        Bạn là trợ lý ảo chăm sóc khách hàng của hệ thống đặt phòng 'HotelBooking'.
        Dưới đây là cơ sở dữ liệu các câu hỏi thường gặp (FAQ) của hệ thống:
        
        {knowledge_text}

        Yêu cầu:
        1. Dựa vào thông tin trên để trả lời câu hỏi của khách hàng: "{user_message}"
        2. Trả lời ngắn gọn, thân thiện, xưng hô là "mình" hoặc "chúng tôi".
        3. Nếu câu hỏi KHÔNG có trong dữ liệu trên, hãy trả lời dựa trên kiến thức du lịch chung hoặc khéo léo đề nghị khách dùng chức năng 'Gửi yêu cầu admin'.
        4. Tuyệt đối không bịa đặt các chính sách hoàn tiền/giá cả nếu không có trong dữ liệu.
        5. Nếu khách hỏi về thông tin cá nhân hoặc bảo mật, hãy nhắc họ liên hệ admin.
        6. Luôn giữ thái độ lịch sự và chuyên nghiệp.
        7. Nếu khách hỏi về các câu hỏi ngoài phạm vi hệ thống, tuy nhiên vẫn liên quan tới du lịch, hãy cố gắng trả lời dựa trên kiến thức chung của bạn.
        8. Nếu có thể, hãy trò chuyện với khách hàng, tạo cảm giác thân thiện và gần gũi.
        """

        response = model.generate_content(prompt)
        
        return jsonify({"reply": response.text})

    except Exception as e:
        print(f"Lỗi AI: {e}")
        return jsonify({"reply": "Xin lỗi, hệ thống đang bận. Bạn vui lòng thử lại sau."}), 500
 