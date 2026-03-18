from flask import Blueprint, request, jsonify
import mysql.connector as connect
from decimal import Decimal
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils import get_db_connection, get_sql_aggregation, get_userid_from_token, send_answer_email
from datetime import datetime
import os
import bcrypt
import re

admin_bp = Blueprint("admin",__name__)

@admin_bp.route("/admin/logs", methods=["GET"])
@jwt_required()
def get_logs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  
    
    # Truy vấn lấy dữ liệu từ bảng log
    cursor.execute("SELECT * FROM log")
    datas = cursor.fetchall()
    
    logs = []
    for data in datas:
        log_entry = {
            "id": data["id"],
            "created_at": data["created_at"],
            "customer_id": data["customer_id"],
            "action": data["action"]
        }

        # Truy vấn lấy tên người dùng từ bảng users
        cursor.execute("SELECT username FROM customers WHERE id = %s", (data["customer_id"],))
        user_data = cursor.fetchone()
        if user_data:
            log_entry["username"] = user_data["username"]
        else:
            log_entry["username"] = "Unknown"
        
        logs.append(log_entry)

    return jsonify(logs)
@admin_bp.route("/admin/logs",methods=["POST"])
@jwt_required()
def create_log():
    data = request.json
    customer_id = get_userid_from_token()
    action = data.get("action")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO log(customer_id, action) VALUES(%s,%s)",(customer_id,action))
    conn.commit()
    message = f"{action} complete!"
    return jsonify({"message":message})
@admin_bp.route("/admin/customers",methods=["GET"])
@jwt_required()
def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)
@admin_bp.route("/admin/customers/total",methods=["GET"])
@jwt_required()
def get_total_customers():
    count = 0
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id from customers where role = 'customers' ")
    customers = cursor.fetchall()
    cursor.close()
    conn.close()
    for customer in customers:
        count += 1
    return jsonify({"count":count})
@admin_bp.route("/admin/customers/<int:customer_id>",methods=["GET"])
@jwt_required()
def get_all_customers(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers WHERE id != %s",(customer_id,))
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)
@admin_bp.route("/admin/customers/<int:customer_id>",methods=["DELETE"])
@jwt_required()
def remove_customers(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("DELETE FROM log WHERE customer_id = %s",(customer_id,))
    conn.commit()
    cursor.execute("DELETE FROM support_tickets WHERE customer_id = %s",(customer_id, ))
    conn.commit()
    cursor.execute("DELETE FROM invoices WHERE customer_id = %s",(customer_id, ))
    conn.commit()
    cursor.execute("DELETE FROM customers WHERE id = %s",(customer_id, ))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Xóa user thành công!"})
@admin_bp.route("/admin/customers/<int:customer_id>", methods=["PUT"])
@jwt_required()
def updated_customers(customer_id):
    data = request.json
    if not data:
        return jsonify({"error": "Dữ liệu cập nhật không hợp lệ"}), 400
    fields = []
    values = []
    if "username" in data:
        fields.append("username = %s")
        values.append(data["username"])
    if "phone" in data:
        fields.append("phone_number = %s")
        values.append(data["phone"])
    if "email" in data:
        fields.append("email = %s")
        values.append(data["email"])
    if "password" in data:
        raw_password = data["password"]
        if raw_password:
            fields.append("password = %s")
            password_bytes = raw_password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
            values.append(hashed_password)

    if "full_name" in data:
        fields.append("full_name = %s")
        values.append(data["full_name"])
    
    if "birth_date" in data:
        fields.append("birth_date = %s")
        values.append(data["birth_date"])
    
    if "current_address" in data:
        fields.append("current_address = %s")
        values.append(data["current_address"])
    
    if "citizen_id" in data:
        fields.append("citizen_id = %s")
        values.append(data["citizen_id"])

    # Nếu không có trường nào để cập nhật, trả về lỗi
    if not fields:
        return jsonify({"error": "Không có thông tin nào để cập nhật"}), 400

    # Ghép câu lệnh SQL
    query = f"UPDATE customers SET {', '.join(fields)} WHERE id = %s"
    values.append(customer_id)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "User updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@admin_bp.route("/admin/customers/create_user", methods=["POST"])
@jwt_required()
def create_customers():
    try:
        data = request.json
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        phone = data.get("phone_number")
        full_name = data.get("full_name") 
        citizen_id = data.get("citizen_id")
        role = data.get("role")
        if not all([username, email, password, full_name, role]):
            return jsonify({"error": "Vui lòng điền đầy đủ thông tin bắt buộc"}), 400
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')  
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO customers (username, email, password, phone_number, full_name, citizen_id, role) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        val = (username, email, hashed_password, phone, full_name, citizen_id, role)
        cursor.execute(sql, val)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Tạo thành công!"}), 201
    except mysql.connector.Error as err:
        if err.errno == 1062:
            return jsonify({"error": "Username hoặc Email này đã tồn tại!"}), 409
        print(f"Lỗi DB: {err}")
        return jsonify({"error": "Lỗi cơ sở dữ liệu"}), 500
    except Exception as e:
        print(f"Lỗi hệ thống: {e}")
        return jsonify({"error": "Có lỗi xảy ra, vui lòng thử lại"}), 500
@admin_bp.route("/admin/customers/find", methods=["POST"])
@jwt_required()
def find_customer():
    data = request.json
    search_type = data.get("type")          
    type_data = data.get("type_data")       
    allowed_fields = ["id", "username", "email", "full_name"]
    if search_type not in allowed_fields:
        return jsonify({"error": "Trường tìm kiếm không hợp lệ!"}), 400
    if isinstance(type_data, str):
        type_data = type_data.strip()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM customers WHERE {search_type} = %s"
    cursor.execute(query, (type_data,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(result if result else {"message": "Không tìm thấy!"})
@admin_bp.route("/admin/hotels/total",methods=["GET"])
@jwt_required()
def get_total_hotels():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    count = 0
    cursor.execute("SELECT id FROM hotels")
    hotels = cursor.fetchall()
    cursor.close()
    conn.close()
    for hotel in hotels:
        count +=1
    return jsonify({"count":count})    
@admin_bp.route("/admin/hotels/create",methods=["POST"])
@jwt_required()
def create_hotels():
    data = request.json
    print(data)
    name = data.get("name")
    address = data.get("address")
    area = data.get("area")
    hotline = data.get("hotline")
    rate = data.get("rate")
    image_url = data.get("image_url")
    description = data.get("description")
    status = data.get("status")
    review_score = data.get("review_score")
    price = data.get("hotel_price")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO hotels(name,address,area,hotline,rate,image_url,description,status,review_score,hotel_price) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                   ,(name,address,area,hotline,rate,image_url,description,status,review_score,price))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Đã tạo thành công!"})
@admin_bp.route("/admin/hotels/find", methods=["POST"])
@jwt_required()
def find_hotel():
    data = request.json
    search_type = data.get("type")          
    type_data = data.get("type_data")       
    allowed_fields = ["id", "name", "area", "hotline"]
    if search_type not in allowed_fields:
        return jsonify({"error": "Trường tìm kiếm không hợp lệ!"}), 400
    if isinstance(type_data, str):
        type_data = type_data.strip()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM hotels WHERE {search_type} = %s"
    cursor.execute(query, (type_data,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result if result else {"message": "Không tìm thấy!"})
@admin_bp.route("/admin/hotels/<int:hotel_id>",methods=["PUT"])
@jwt_required()
def update_hotel(hotel_id):
    data = request.json
    if not data:
        return jsonify({"error": "Dữ liệu cập nhật không hợp lệ"}), 400

    fields = []
    values = []
    if "name" in data:
        fields.append("name = %s")
        values.append(data["name"])
    if "hotline" in data:
        fields.append("hotline = %s")
        values.append(data["hotline"])
    if "address" in data:
        fields.append("address = %s")
        values.append(data["address"])
    if "hotel_price" in data:
        fields.append("hotel_price = %s")
        values.append(data["hotel_price"])
    if "area" in data:
        fields.append("area = %s")
        values.append(data["area"])
    if "description" in data:
        fields.append("description = %s")
        values.append(data["description"])
    if "rate" in data:
        fields.append("rate = %s")
        values.append(data["rate"])
    if "review_score" in data:
        fields.append("review_score = %s")
        values.append(data["review_score"])
    if "image_url" in data:
        fields.append("image_url = %s")
        values.append(data["image_url"])
    if "status" in data:
        fields.append("status = %s")
        values.append(data["status"])
    if not fields:
        return jsonify({"error": "Không có thông tin nào để cập nhật"}), 400

    # Ghép câu lệnh SQL
    query = f"UPDATE hotels SET {', '.join(fields)} WHERE id = %s"
    print(query)
    values.append(hotel_id)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Cập nhật khách sạn thành công!"}), 200
    except connect.Exception as e:
        return jsonify({"error": str(e)}), 500
@admin_bp.route("/admin/hotels/<int:hotel_id>",methods=["DELETE"])
@jwt_required()
def delete_hotel(hotel_id):
    conn = get_db_connection()
    conn.cursor().execute("DELETE FROM roomtypes WHERE hotel_id = %s",(hotel_id, ))
    conn.commit()
    conn.cursor().execute("DELETE FROM hotels WHERE id = %s",(hotel_id, ))
    conn.commit()
    conn.cursor().close()
    conn.close()
    return jsonify({"message": f"Delete complete hotel {hotel_id}"})
@admin_bp.route("/admin/hotels/<int:hotel_id>/roomtypes",methods=["GET"])
@jwt_required()
def get_room_of_hotel(hotel_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM roomtypes WHERE hotel_id = %s",(hotel_id, ))
    rooms = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rooms)
@admin_bp.route("/admin/roomtypes/find", methods=["POST"])
@jwt_required()
def find_rooms():
    data = request.json
    search_type = data.get("type")
    type_data = data.get("type_data")
    allowed_fields = ["id", "hotel_id", "name", "availability"]
    if search_type not in allowed_fields:
        return jsonify({"error": "Trường tìm kiếm không hợp lệ!"}), 400
    if isinstance(type_data, str):
        type_data = type_data.strip()
    if search_type == "availability":
        try:
            type_data = float(type_data)
        except ValueError:
            return jsonify({"error": "Giá trị availability phải là số!"}), 400
        query = "SELECT * FROM roomtypes WHERE availability >= %s"
    else:
        query = f"SELECT * FROM roomtypes WHERE {search_type} = %s"
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (type_data,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    if not result:
        return jsonify({"message": "Không tìm thấy!"}), 404
    return jsonify(result)
@admin_bp.route("/admin/roomtypes/total",methods=["GET"])
@jwt_required()
def get_total_roomtypes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    count = 0
    cursor.execute("SELECT id FROM roomtypes")
    rooms = cursor.fetchall()
    cursor.close()
    conn.close()
    for room in rooms:
        count +=1
    return jsonify({"count":count})    
@admin_bp.route("/admin/roomtypes",methods=["GET"])
@jwt_required()
def get_all_roomtype():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM roomtypes")
    rooms = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rooms)
@admin_bp.route("/admin/roomtypes/<int:roomtype_id>",methods=["PUT"])
@jwt_required()
def update_room(roomtype_id):
    data = request.json
    if not data:
        return jsonify({"error": "Dữ liệu cập nhật không hợp lệ"}), 400

    fields = []
    values = []
    if "name" in data:
        fields.append("name = %s")
        values.append(data["name"])
    if " capacity" in data:
        fields.append("capacity = %s")
        values.append(data["capacity"])
    if "bed_type" in data:
        fields.append("bed_type = %s")
        values.append(data["bed_type"])
    if "price" in data:
        fields.append("price = %s")
        values.append(data["price"])
    if "rating" in data:
        fields.append("rating = %s")
        values.append(data["rating"])
    if "availability" in data:
        fields.append("availability = %s")
        values.append(data["availability"])
    if "services" in data:
        fields.append("services = %s")
        values.append(data["services"])
    if "area" in data:
        fields.append("area = %s")
        values.append(data["area"])
    if "img_url" in data:
        fields.append("img_url = %s")
        values.append(data["img_url"])
    if "hotel_id" in data:
        fields.append("hotel_id = %s")
        values.append(data["hotel_id"])
    if not fields:
        return jsonify({"error": "Không có thông tin nào để cập nhật"}), 400

    # Ghép câu lệnh SQL
    query = f"UPDATE roomtypes SET {', '.join(fields)} WHERE id = %s"
    values.append(roomtype_id)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Roomtype updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@admin_bp.route("/admin/roomtypes/create",methods=["POST"])
@jwt_required()
def create_rooms():
    data = request.json
    name = data.get("name")
    hotel_id = data.get("hotel_id")
    area = data.get("area")
    services = data.get("services")
    capacity = data.get("capacity")
    image_url = data.get("image_url")
    bed_type = data.get("bed_type")
    rating = data.get("rating")
    availability = data.get("availability")
    price = data.get("price")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO roomtypes(name,capacity,area,hotel_id,rating,img_url,bed_type,availability,price,services) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                   ,(name,capacity,area,hotel_id,rating,image_url,bed_type,availability,price,services))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Đã tạo thành công!"})
@admin_bp.route("/admin/roomtypes/<int:roomtype_id>",methods=["DELETE"])
@jwt_required()
def delete_room(roomtype_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM roomtypes WHERE id = %s",(roomtype_id, ))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Đã xóa thành công"})
@admin_bp.route("/admin/additionalservices/create",methods=["POST"])
@jwt_required()
def create_additionalservices():
    data = request.json
    name = data.get("service_name")
    price = data.get("price")
    description = data.get("description")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO additionalservices(service_name,price,description) VALUES(%s,%s,%s)",(name,price,description))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Thêm dịch vụ thành công"})
@admin_bp.route("/admin/additionalservices/<int:service_id>",methods=["GET"])
@jwt_required()
def get_additionalservices(service_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM additionalservices WHERE id = %s",(service_id, ))
    services = cursor.fetchone()
    print(services)
    cursor.close()
    conn.close()
    return jsonify(services)
@admin_bp.route("/admin/additionalservices/<int:service_id>",methods=["PUT"])
@jwt_required()
def update_additionalservices(service_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    data = request.json
    service_name = data.get("service_name")
    service_price = data.get("price")
    service_description = data.get("description")
    cursor.execute("UPDATE additionalservices SET service_name = %s,price = %s,description = %s WHERE id = %s",(service_name,service_price,service_description,service_id))
    conn.commit()
    cursor.close()
    conn.close()
    message = f"Cập nhật thành công dịch vụ {service_id}"
    return jsonify({"message": message})
@admin_bp.route("/admin/additionalservices/<int:service_id>",methods=["DELETE"])
@jwt_required()
def delete_additionalservices(service_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM additionalservices WHERE id = %s",(service_id,))
    conn.commit()
    cursor.close()
    conn.close()
    message = f"Xóa thành công dịch vụ {service_id}"
    return jsonify({"message": message})
@admin_bp.route("/admin/additionalservices/find",methods=["POST"])
@jwt_required()
def find_service():
    data = request.json
    search_type = data.get("type")          
    type_data = data.get("type_data")       
    allowed_fields = ["id", "service_name", "price"]
    if search_type not in allowed_fields:
        return jsonify({"error": "Trường tìm kiếm không hợp lệ!"}), 400
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if search_type == "price":
        service = float(type_data)
        query = f"SELECT * FROM additionalservices WHERE price <= %s"
    else:
        query = f"SELECT * FROM additionalservices WHERE {search_type} = %s"
    cursor.execute(query, (type_data,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result if result else {"message": "Không tìm thấy!"})
@admin_bp.route('/admin/report', methods=['POST'])
@jwt_required()
def report():
    data = request.json or {}

    report_type = data.get('type', 'revenue')
    time_range = data.get('range', 'month')
    year = int(data.get('year', datetime.now().year))

    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = []
    params = []
    labels = []
    expected_keys = []

    # ===== RANGE LOGIC =====
    if time_range == 'month':
        group_expr = "MONTH(create_at)"
        conditions.append("YEAR(create_at) = %s")
        params.append(year)

        expected_keys = list(range(1, 13))
        labels = [f"Tháng {i}" for i in expected_keys]

    elif time_range == 'quarter':
        group_expr = "QUARTER(create_at)"
        conditions.append("YEAR(create_at) = %s")
        params.append(year)

        expected_keys = list(range(1, 5))
        labels = [f"Quý {i}" for i in expected_keys]

    elif time_range == 'year':
        start_year = year - 2
        group_expr = "YEAR(create_at)"
        conditions.append("YEAR(create_at) BETWEEN %s AND %s")
        params.extend([start_year, year])

        expected_keys = list(range(start_year, year + 1))
        labels = [str(y) for y in expected_keys]

    else:
        return jsonify({"error": "Invalid range"}), 400

    # ===== REPORT TYPE =====
    if report_type == 'revenue':
        conditions.append("state = 'DA THANH TOAN'")
        select_expr = "SUM(total_price)"

    elif report_type == 'orders':
        select_expr = "COUNT(*)"

    elif report_type == 'customers':
        select_expr = "COUNT(DISTINCT customer_id)"

    else:
        return jsonify({"error": "Invalid type"}), 400

    where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT {group_expr} AS label, {select_expr}
        FROM invoices
        {where_clause}
        GROUP BY label
        ORDER BY label
    """

    cursor.execute(query, tuple(params))
    results = cursor.fetchall()

    value_map = {int(row[0]): float(row[1]) for row in results}
    values = [round(value_map.get(i, 0), 2) for i in expected_keys]

    cursor.close()
    conn.close()

    return jsonify({
        "labels": labels,
        "values": values
    })
@admin_bp.route("/admin/payment/total",methods=['GET'])
@jwt_required()
def get_total_money():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT total_money FROM payment")
    total = 0
    moneys = cursor.fetchall()
    cursor.close()
    conn.close()
    for money in moneys:
        total += money['total_money']
    return jsonify({"total": total})
@admin_bp.route("/admin/invoices/total",methods=["GET"])
@jwt_required()
def get_total_invoices():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM invoices")
    total = 0
    invoices = cursor.fetchall()
    cursor.close()
    conn.close()
    for invoice in invoices:
        total += 1
    return jsonify({"count": total}) 
@admin_bp.route("/admin/invoices/create", methods=["POST"])
@jwt_required()
def create_invoices():
    data = request.json
    customer_id = get_userid_from_token()

    room_type_id = data.get("room_type_id")
    check_in = data.get("check_in")
    check_out = data.get("check_out")
    additional_services = data.get("additional_services", [])
    forwho = data.get("forwho", False)
    anothercustomer = data.get("anothercustomer")
    anotherccid = data.get("anotherccid")
    hotel_id = data.get("hotel_id")

    if not all([customer_id, room_type_id, check_in, check_out, hotel_id]):
        return jsonify({"error": "Thiếu thông tin đặt phòng"}), 400

    if check_in >= check_out:
        return jsonify({"error": "Ngày check-in phải trước ngày check-out"}), 400

    if check_in < datetime.now().strftime("%Y-%m-%d"):
        return jsonify({"error": "Ngày check-in phải từ hôm nay trở đi"}), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT price, availability FROM roomtypes WHERE id = %s",
            (room_type_id,)
        )
        room_info = cursor.fetchone()

        if not room_info:
            return jsonify({"error": "Loại phòng không hợp lệ"}), 400

        room_price, availability = room_info

        if availability <= 0:
            return jsonify({"error": "Loại phòng đã hết chỗ"}), 400

        cursor.execute("""
            SELECT room_number
            FROM busy_room
            WHERE hotel_id = %s
              AND room_type_id = %s
              AND state = 'Free'
            LIMIT 1
        """, (hotel_id, room_type_id))

        room_row = cursor.fetchone()
        if not room_row:
            return jsonify({"error": "Không còn phòng trống phù hợp"}), 400

        room = room_row[0]

        cursor.execute("""
            SELECT d.discount
            FROM customers c
            JOIN discounts d ON c.customer_type = d.id
            WHERE c.id = %s
        """, (customer_id,))
        discount_row = cursor.fetchone()
        discount = float(discount_row[0]) if discount_row else 0

        total_service_price = 0
        if additional_services:
            additional_services = [int(s) for s in additional_services if s]

            placeholders = ",".join(["%s"] * len(additional_services))
            cursor.execute(
                f"SELECT price FROM additionalservices WHERE id IN ({placeholders})",
                tuple(additional_services)
            )
            total_service_price = sum(row[0] for row in cursor.fetchall())

        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
        num_nights = (check_out_date - check_in_date).days

        total_price = Decimal(room_price * num_nights + total_service_price)
        total_price -= (Decimal(discount) / 100) * total_price

        cursor.execute("""
            INSERT INTO invoices (
                customer_id, room_type_id, check_in, check_out,
                total_price, hotel_id,
                is_for_someone_else, other_person_name,
                other_person_ccid, room_number
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            customer_id,
            room_type_id,
            check_in,
            check_out,
            total_price,
            hotel_id,
            forwho,
            anothercustomer if forwho else None,
            anotherccid if forwho else None,
            room
        ))

        invoice_id = cursor.lastrowid

        cursor.execute("""
            UPDATE busy_room
            SET state = 'Busy',
                busy_from = %s,
                busy_to = %s,
                invoice_id = %s
            WHERE hotel_id = %s
              AND room_type_id = %s
              AND room_number = %s
        """, (
            check_in_date,
            check_out_date,
            invoice_id,
            hotel_id,
            room_type_id,
            room
        ))

        for service_id in additional_services:
            cursor.execute("""
                INSERT INTO invoice_additionalservices (invoice_id, service_id)
                VALUES (%s, %s)
            """, (invoice_id, service_id))

        cursor.execute("""
            UPDATE roomtypes
            SET availability = availability - 1
            WHERE id = %s
        """, (room_type_id,))

        conn.commit()

        return jsonify({
            "message": "Đặt phòng thành công",
            "invoice_id": invoice_id,
            "room_number": room,
            "total_price": float(total_price)
        }), 201

    except Exception as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@admin_bp.route("/admin/invoices",methods=["GET"])
@jwt_required()
def get_all_invoices():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM invoices")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)   
@admin_bp.route("/admin/invoices/get_name",methods=["POST"])
@jwt_required()
def get_name_from_id():
    data = request.json
    hotel_id = data.get("hotel_id")
    customer_id = data.get("customer_id")
    room_type_id = data.get("room_type_id")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Lấy tên người dùng
        cursor.execute("SELECT username FROM customers WHERE id = %s", (customer_id,))
        user = cursor.fetchone()
        username = user['username'] if user else "Không rõ"

        # Lấy tên khách sạn
        cursor.execute("SELECT name FROM hotels WHERE id = %s", (hotel_id,))
        hotel = cursor.fetchone()
        hotel_name = hotel['name'] if hotel else "Không rõ"

        # Lấy tên loại phòng
        cursor.execute("SELECT name FROM roomtypes WHERE id = %s", (room_type_id,))
        room = cursor.fetchone()
        room_name = room['name'] if room else "Không rõ"

        return jsonify({
            "username": username,
            "hotel_name": hotel_name,
            "room_type_name": room_name
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
@admin_bp.route("/admin/invoices/<int:invoice_id>",methods=["DELETE"])
@jwt_required()
def delete_invoices(invoice_id):
    customer_id = get_userid_from_token()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT hotel_id, room_type_id,room_number From invoices where id=%s",(invoice_id,))
    data = cursor.fetchone()
    hotel_id = data["hotel_id"]
    room_type_id = data["room_type_id"]
    room_number = data["room_number"]
    cursor.execute("DELETE FROM invoice_additionalservices WHERE invoice_id = %s",(invoice_id,))
    cursor.execute("UPDATE busy_room set state = 'Free',invoice_id=NULL,busy_from=NULL,busy_to=NULL where hotel_id = %s and room_type_id=%s and room_number=%s",(hotel_id,room_type_id,room_number,))
    cursor.execute("DELETE FROM invoices WHERE id = %s",(invoice_id,))
    cursor.execute("""
            UPDATE roomtypes SET availability = availability + 1 WHERE id = %s
        """, (room_type_id,))
    conn.commit()
    cursor.close()
    conn.close()
    message = f"Xóa thành công hóa đơn {invoice_id}"
    return jsonify({"message": message})
@admin_bp.route("/admin/invoices/find",methods=["POST"])
@jwt_required()
def find_invoices():
    data = request.json
    search_type = data.get("type")          
    type_data = data.get("type_data")

    allowed_fields = ["id", "hotels", "total_price", "customers", "roomtypes", "state"]
    if search_type not in allowed_fields:
        return jsonify({"error": "Trường tìm kiếm không hợp lệ!"}), 400
    if isinstance(type_data, str):
        type_data = type_data.strip()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True,buffered=True)

    try:
        if search_type in ["id", "state"]:
            query = f"SELECT * FROM invoices WHERE {search_type} = %s"
            cursor.execute(query, (type_data,))

        elif search_type == "total_price":
            query = "SELECT * FROM invoices WHERE total_price >= %s"
            cursor.execute(query, (type_data,))

        elif search_type == "customers":
            cursor.execute("SELECT id FROM customers WHERE username = %s", (type_data,))
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Không tìm thấy khách hàng"}), 404
            customer_id = row["id"]
            cursor.execute("SELECT * FROM invoices WHERE customer_id = %s", (customer_id,))

        elif search_type in ["hotels", "roomtypes"]:
            table_map = {
                "hotels": ("hotels", "hotel_id"),
                "roomtypes": ("roomtypes", "room_type_id")
            }
            table_name, column_name = table_map[search_type]
            cursor.execute(f"SELECT id FROM {table_name} WHERE name = %s", (type_data,))
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": f"Không tìm thấy {search_type[:-1]}"}), 404
            foreign_id = row["id"]
            cursor.execute(f"SELECT * FROM invoices WHERE {column_name} = %s", (foreign_id,))
            print(f"SELECT * FROM invoices WHERE {column_name} = {foreign_id}")
        result = cursor.fetchall()
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
@admin_bp.route("/admin/invoices/<int:invoices_id>",methods=["PUT"])
@jwt_required()
def updated_invoicess(invoices_id):
    customer_id = get_userid_from_token()
    data = request.json

    if not data:
        return jsonify({"message": "Không có data!"}), 400

    check_in = data.get("check_in")
    check_out = data.get("check_out")
    additional_services = data.get("additional_services", [])
    state = data.get("state")

    # Kiểm tra ngày tháng
    if check_in >= check_out:
        return jsonify({"message": "Ngày check-in phải trước ngày check-out"}), 400

    try:
        total = Decimal(str(data.get("total_price")))
    except:
        return jsonify({"message": "total_price không hợp lệ!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    try:
        # Lấy giảm giá từ loại khách hàng
        cursor.execute("SELECT customer_type FROM customers WHERE id = %s", (customer_id,))
        customer_type_row = cursor.fetchone()
        if not customer_type_row:
            return jsonify({"message": "Không tìm thấy loại khách hàng"}), 404

        customer_type = customer_type_row[0]
        cursor.execute("SELECT discount FROM discounts WHERE id = %s", (customer_type,))
        discount_row = cursor.fetchone()
        discount = Decimal(discount_row[0]) if discount_row else Decimal(0)

        # Áp dụng giảm giá
        total_after_discount = total - (discount * total / 100)
        new_total = total_after_discount
        new_state = state

        if state == "DA THANH TOAN":
            cursor.execute("SELECT total_money FROM payment WHERE invoices_id = %s", (invoices_id,))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "Không tìm thấy thanh toán trước đó"}), 404

            old_total = Decimal(result[0])
            if total_after_discount > old_total:
                new_total = total_after_discount - old_total
                new_state = "CHUA THANH TOAN"
                message = f"Cập nhật thành công hóa đơn, bạn còn thiếu: {new_total}!"
            elif total_after_discount < old_total:
                new_total = old_total - total_after_discount
                message = f"Cập nhật thành công hóa đơn, bạn còn thừa: {new_total}!"
            else:
                message = "Cập nhật thành công hóa đơn, không có thay đổi về số tiền."
        elif state == "CHUA THANH TOAN":
            message = f"Cập nhật thành công hóa đơn, vui lòng thanh toán: {new_total}!"
        else:
            message = "Cập nhật hóa đơn thành công!"

        # Cập nhật hóa đơn
        cursor.execute("""
            UPDATE invoices
            SET check_in = %s, check_out = %s, total_price = %s, state = %s
            WHERE id = %s
        """, (check_in, check_out, new_total, new_state, invoices_id))

        # Cập nhật dịch vụ bổ sung
        cursor.execute("DELETE FROM invoice_additionalservices WHERE invoice_id = %s", (invoices_id,))

        if additional_services:
            additional_services = [int(s) for s in additional_services if s]
            for service_id in additional_services:
                cursor.execute("""
                    INSERT INTO invoice_additionalservices (invoice_id, service_id)
                    VALUES (%s, %s)
                """, (invoices_id, service_id))

        conn.commit()
        return jsonify({"message": message}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
@admin_bp.route("/admin/schedules",methods=["GET"])
@jwt_required()
def get_schedules():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM busy_room WHERE busy_to IS NOT NULL;")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)
@admin_bp.route("/admin/schedules/<int:schedules_id>",methods=["GET"])
@jwt_required()
def get_schedules_byid(schedules_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM busy_room WHERE id=%s",(schedules_id,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    print(data)
    return jsonify(data)
@admin_bp.route("/admin/schedules/<int:schedules_id>",methods=["PUT"])
@jwt_required()
def update_schedules(schedules_id):
    data = request.json
    id = schedules_id
    busy_from = data.get("busy_from")
    busy_to = data.get("busy_to")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE busy_room SET busy_from=%s,busy_to=%s WHERE id=%s",(busy_from,busy_to,id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message":"Update success!"})
@admin_bp.route("/admin/schedules/<int:schedules_id>/get_name",methods=["POST"])
@jwt_required()
def get_schedules_name_byid(schedules_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM busy_room WHERE id=%s",(schedules_id,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(data)
@admin_bp.route("/admin/schedules/<int:schedules_id>",methods=["DELETE"])
@jwt_required()
def delete_schedules(schedules_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE busy_room SET busy_from=NULL,busy_to=NULL,state='Free',invoice_id=NULL WHERE id=%s",(schedules_id,))
    conn.commit()
    cursor.close()
    conn.close()
@admin_bp.route("/admin/schedules/create",methods=["POST"])
@jwt_required()
def create_schedules():
    data = request.json
    hotel_id = data.get("hotel_id")
    room_type_id = data.get("room_type_id")
    room_number = data.get("room_number")
    busy_from = data.get("busy_from")
    busy_to = data.get("busy_to")
    state = "Busy"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT busy_from FROM busy_room WHERE hotel_id = %s AND room_type_id = %s AND room_number = %s",(hotel_id,room_type_id,room_number))
    busy = cursor.fetchone()
    print(busy)
    if busy[0] is not None:
        cursor.close()
        conn.close()
        return jsonify({"message": "Không thể tạo lịch do đã có lịch cho phòng này!"})
    else:
        cursor.execute("UPDATE busy_room SET busy_from=%s,busy_to=%s,state=%s  WHERE hotel_id = %s AND room_type_id = %s AND room_number=%s",(busy_from,busy_to,state,hotel_id,room_type_id,room_number))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message":"Thêm lịch thành công"})
@admin_bp.route("/admin/schedules/<int:room_type_id>/roomnumber",methods=["GET"])
@jwt_required()
def get_room_free(room_type_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT room_number FROM busy_room WHERE room_type_id = %s AND state='Free'",(room_type_id,))
    data = cursor.fetchall()
    return jsonify(data)
@admin_bp.route("/admin/schedules/find",methods=["POST"])
@jwt_required()    
def find_schedules():
    data = request.json
    search_type = data.get("type")
    type_data = data.get("type_data")
    allowed_fields = ["room_number", "hotel_id", "room_type_id","state"]
    if search_type not in allowed_fields:
        return jsonify({"error": "Trường tìm kiếm không hợp lệ!"}), 400
    if isinstance(type_data, str):
        type_data = type_data.strip()
    query = f"SELECT * FROM busy_room WHERE {search_type} = %s"
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (type_data,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    if not result:
        return jsonify({"message": "Không tìm thấy!"}), 404
    return jsonify(result)
@admin_bp.route("/admin/supports", methods=["GET"])
@jwt_required()
def get_all_supports():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM support_tickets;")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data) 
@admin_bp.route("/admin/supports/<int:ticket_id>", methods=["PUT"])
@jwt_required()
def answer_support_ticket(ticket_id):
    try:
        data = request.json
        response_text = data.get("response") 
        receiver_email = data.get("receiver_email")
        subject = data.get("subject")
        cus_id = data.get("customer_id")

        if not response_text or not receiver_email:
            return jsonify({"error": "Nội dung phản hồi và Email người nhận không được để trống"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        customer_name = "Khách hàng"
        if cus_id:
            cursor.execute("SELECT full_name FROM customers WHERE id = %s", (cus_id,))
            customer = cursor.fetchone()
            if customer: 
                customer_name = customer["full_name"]
        email_data = {
            "id": ticket_id,
            "response": response_text,
            "customer_name": customer_name,
            "subject": subject
        }
        try:
            send_answer_email(receiver_email, email_data)
        except Exception as e:
            print(f"Lỗi gửi email: {e}")
        cursor.execute("""
            UPDATE support_tickets
            SET status = 'answered',
                answer = %s,
                answer_at = NOW()
            WHERE id = %s
        """, (response_text, ticket_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Đã gửi phản hồi và cập nhật trạng thái!"})

    except Exception as e:
        print(f"System Error: {e}")
        return jsonify({"error": "Lỗi hệ thống"}), 500
        