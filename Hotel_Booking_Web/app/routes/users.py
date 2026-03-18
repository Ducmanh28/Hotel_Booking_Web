from db import get_db_connection
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.utils import get_userid_from_token,format_rfc1123_to_date
customers_bp = Blueprint("customers", __name__)


@customers_bp.route("/customers/<int:user_id>",methods=["GET"])
@jwt_required()
def get_users(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers WHERE id = %s",(user_id, ))
    users = cursor.fetchone()
    if users.get('birth_date'):
        users['birth_date'] = format_rfc1123_to_date(users['birth_date'])
    cursor.close()
    conn.close()
    return jsonify(users)
@customers_bp.route("/customers/<int:user_id>",methods=["PUT"])
@jwt_required()
def updated_users(user_id):
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
        fields.append("password = %s")
        values.append(data["password"])
    if "full_name" in data:
        fields.append("full_name = %s")
        values.append(data["full_name"])
    if "birth_date" in data:
        fields.append("birth_date = %s")
        values.append(data["birth_date"])
    if "current_address" in data:
        fields.append("current_address = %s")
        values.append(data["current_address"])

    if not fields:
        return jsonify({"error": "Không có thông tin nào để cập nhật"}), 400

    query = f"UPDATE customers SET {', '.join(fields)} WHERE id = %s"
    values.append(user_id)
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
@customers_bp.route("/customers/<int:user_id>",methods=["DELETE"])
@jwt_required()
def deleted_users(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = %s", (user_id, ))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"message": "User deleted successfully"}), 201
@customers_bp.route('/get_customer_info', methods=['GET'])
@jwt_required()  
def get_customer_info():
    customer_id = get_userid_from_token()
    if customer_id:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = cursor.fetchone()
        cursor.close()
        conn.close()
        if not customer:
            return jsonify({"error": "Khách hàng không tồn tại"}), 404
    else: 
        return jsonify({"error": "Không tìm thấy tên khách hàng"}), 404
    return jsonify(customer)
@customers_bp.route("/customer/<int:user_id>/invoices", methods=["GET"])
@jwt_required()
def get_invoices_of_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM invoices WHERE customer_id = %s", (user_id,))
    invoices = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(invoices)
@customers_bp.route("/customer/discounts/<int:customer_type_id>",methods=["GET"])
@jwt_required()
def get_customer_discount(customer_type_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT customer_type,discount FROM discounts WHERE id = %s",(customer_type_id, ))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(data)
    