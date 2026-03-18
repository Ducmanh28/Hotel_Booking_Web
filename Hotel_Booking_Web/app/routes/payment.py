from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from db import get_db_connection
from decimal import Decimal

payment_bp = Blueprint("payment",__name__)

@payment_bp.route("/payment/vnpay",methods=["POST"])
@jwt_required()
def payment_vnpay():
    data = request.json
    invoices_id = data.get("invoices_id")
    number = data.get("card_number")
    card_type = "VNPAY account"
    state = "DA THANH TOAN"
    type_of_payment = "VNPAY"
    pay_money = Decimal(data.get("total_money"))
    pay_description = data.get("description")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT total_price FROM invoices WHERE id = %s",(invoices_id, ))
    total = cursor.fetchone()
    if total:
        total_price = Decimal(total.get("total_price"))
    else:
        return jsonify({"message": "Lỗi lấy dữ liệu giá"})
    if abs(total_price - pay_money) < Decimal(0.01):
        cursor.execute("INSERT INTO payment (invoices_id,total_money,pay_description,type_of_payment,card_number,card_type) VALUES  (%s,%s,%s,%s,%s,%s)",(invoices_id,pay_money,pay_description,type_of_payment,number,card_type))
        conn.commit()
        cursor.execute("UPDATE invoices SET state =%s WHERE id = %s",(state,invoices_id))
        conn.commit()
        return jsonify({"message": f"Thanh Toán thành công đơn hàng {invoices_id} bằng VNPAY!"}),201
    else:
        return jsonify({"message": "Vui lòng thanh toán đúng số tiền!"})
@payment_bp.route("/payment/card", methods=["POST"])
@jwt_required()
def payment_card():
    data = request.json
    invoices_id = data.get("invoices_id")
    state = "DA THANH TOAN"
    type_of_payment = "card"
    card_number = data.get("card_number")
    card_type = data.get("card_type")
    pay_money = Decimal(data.get("total_money"))  
    pay_description = data.get("description")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT total_price FROM invoices WHERE id = %s", (invoices_id,))
    total = cursor.fetchone()
    
    if total:
        total_price = Decimal(total.get("total_price"))  
    else:
        return jsonify({"message": "Lỗi lấy dữ liệu giá"})
    if abs(total_price - pay_money) < Decimal(0.01):
        cursor.execute("INSERT INTO payment (invoices_id, total_money, pay_description, type_of_payment, card_number, card_type) VALUES  (%s, %s, %s, %s, %s, %s)", 
                       (invoices_id, pay_money, pay_description, type_of_payment, card_number, card_type))
        conn.commit()
        
        cursor.execute("UPDATE invoices SET state = %s WHERE id = %s", (state, invoices_id))
        conn.commit()
        
        return jsonify({"message": f"Thanh Toán thành công đơn hàng {invoices_id} bằng {card_type}!"}), 201
    else:
        return jsonify({"message": "Vui lòng thanh toán đúng số tiền!"})
@payment_bp.route("/payment/banking",methods=["POST"])
def payment_banking():
    data = request.json
    invoices_id = data.get("invoices_id")
    state = "DA THANH TOAN"
    type_of_payment = "banking"
    card_number = data.get("card_number")
    card_type = data.get("card_type")
    pay_money = Decimal(data.get("total_money"))  
    pay_description = data.get("description")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT total_price FROM invoices WHERE id = %s", (invoices_id,))
    total = cursor.fetchone()
    
    if total:
        total_price = Decimal(total.get("total_price"))  
    else:
        return jsonify({"message": "Lỗi lấy dữ liệu giá"})
    
    if abs(total_price - pay_money) < Decimal(0.01): 
        cursor.execute("INSERT INTO payment (invoices_id, total_money, pay_description, type_of_payment, card_number, card_type) VALUES  (%s, %s, %s, %s, %s, %s)", 
                       (invoices_id, pay_money, pay_description, type_of_payment, card_number, card_type))
        conn.commit()
        
        cursor.execute("UPDATE invoices SET state = %s WHERE id = %s", (state, invoices_id))
        conn.commit()
        
        return jsonify({"message": f"Thanh Toán thành công đơn hàng {invoices_id} bằng {card_type}!"}), 201
    else:
        return jsonify({"message": "Vui lòng thanh toán đúng số tiền!"})
@payment_bp.route("/payment/<int:invoice_id>",methods=["GET"])
@jwt_required()
def get_payment_info(invoice_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM payment WHERE invoices_id = %s",(invoice_id, ))
    data = cursor.fetchone()
    return jsonify(data)
