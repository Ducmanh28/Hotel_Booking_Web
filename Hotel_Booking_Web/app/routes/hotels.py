from flask import Blueprint, request, jsonify
from db import get_db_connection
from app.utils import get_hotel_id_from_room_id

hotels_bp = Blueprint("hotels", __name__)
@hotels_bp.route("/hotels/<int:hotel_id>", methods=["GET"])
def get_hotel(hotel_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM hotels WHERE id = %s",(hotel_id, ))
    hotels = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(hotels)
@hotels_bp.route("/hotels", methods=["GET"])
def get_all_hotels():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM hotels")
    hotels = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(hotels)
@hotels_bp.route("/hotels/5_stars",methods=["GET"])
def get_5_stars_hotels():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM hotels WHERE rate = 5")
    hotels = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(hotels)
@hotels_bp.route("/hotels/find", methods=["POST"])
def find_hotel():
    data = request.json
    if not data:
        return jsonify({"error": "Thiếu dữ liệu!"}), 400
    area = data.get("area")
    check_in = data.get("check_in")
    check_out = data.get("check_out")
    status = "Available"  
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM hotels WHERE area = %s AND status = %s", (area, status))
    hotels = cursor.fetchall()

    available_hotels = []

    for hotel in hotels:
        hotel_id = hotel["id"]
        
        # Kiểm tra xem tất cả các phòng của khách sạn có bận trong khoảng thời gian check_in, check_out
        cursor.execute("""
            SELECT COUNT(room_number) as busy_room_count
            FROM busy_room 
            WHERE hotel_id = %s AND state = 'Busy' AND (
                (busy_from <= %s AND busy_to > %s) OR
                (busy_from < %s AND busy_to >= %s) OR
                (busy_from >= %s AND busy_to <= %s)
            )
        """, (hotel_id, check_in, check_in, check_out, check_out, check_in, check_out))

        busy_room_count = cursor.fetchone()["busy_room_count"] or 0

        # Lấy tổng số phòng của khách sạn
        cursor.execute("SELECT COUNT(room_number) as total_rooms FROM busy_room WHERE hotel_id = %s", (hotel_id,))
        total_rooms = cursor.fetchone()["total_rooms"]
        # Nếu tất cả các phòng đều bận trong khoảng thời gian check_in -> check_out, không thêm khách sạn vào danh sách
        if busy_room_count < total_rooms:
            available_hotels.append(hotel)

    cursor.close()
    conn.close()

    return jsonify(available_hotels)
@hotels_bp.route("/hotels/<int:hotel_id>/roomtypes",methods=["GET"])
def get_roomtypes_of_hotels(hotel_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * from roomtypes WHERE hotel_id = %s",(hotel_id, ))
    hotels = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(hotels)
@hotels_bp.route("/roomtypes/<int:roomtypes_id>",methods=["GET"])
def get_room_info(roomtypes_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM roomtypes WHERE id = %s",(roomtypes_id, ))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(data)
@hotels_bp.route("/additionalservices",methods=["GET"])
def get_addtional_services():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM additionalservices")
    data = cursor.fetchall()
    return jsonify(data)
@hotels_bp.route("/name_of_hotel/<int:room_type_id>",methods=["GET"])
def get_name_of_hotel(room_type_id):
    hotel_id = get_hotel_id_from_room_id(room_type_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM hotels WHERE id = %s",(hotel_id, ))
    name = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(name)
@hotels_bp.route("/name_of_roomtype/<int:room_type_id>",methods=["GET"])
def get_name_of_roomtype(room_type_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM roomtypes WHERE id = %s",(room_type_id, ))
    name = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(name)
@hotels_bp.route("/hotels/areas",methods=["GET"])
def get_areas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT area FROM hotels")
    areas = cursor.fetchall()
    cursor.close()
    conn.close()
    area_list = [area[0] for area in areas]
    return jsonify(area_list)
@hotels_bp.route("/hotels/prices", methods=["POST"])
def get_hotels_by_price():
    data = request.json
    hotel_price = data.get("hotel_price")
    area = data.get("area")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM hotels WHERE hotel_price = %s and area = %s",(hotel_price,area, ))
    hotels = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(hotels)
@hotels_bp.route("/hotels/prices", methods=["GET"])
def get_all_prices():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT hotel_price FROM hotels")
    prices = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(prices)
