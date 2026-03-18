from flask import Flask
from flask_jwt_extended import JWTManager
from config import Config
from app.routes.auth import auth_bp
from app.routes.users import customers_bp
from app.routes.hotels import hotels_bp
from app.routes.invoices import invoices_bp
from app.routes.payment import payment_bp
from app.routes.admin import admin_bp
from app.routes.help import help_bp
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

# Cấu hình JWT
app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
jwt = JWTManager(app)

# Đăng ký route
app.register_blueprint(auth_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(hotels_bp)
app.register_blueprint(invoices_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(help_bp)

if __name__ == "__main__":
    app.run(host="172.168.66.82", port=5000, debug=True)
