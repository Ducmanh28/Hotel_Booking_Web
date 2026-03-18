# HOTEL BOOKING APP
# Mô tả ứng dụng
Là một ứng dụng đặt phòng khách sạn. Sử dụng ngôn ngữ lập trình Python và cơ sở dữ liệu MySql làm database để thiết kế hệ thống phần back end.

Ứng dụng có các chức năng cơ bản so với một ứng dụng hoàn chỉnh. Các chức năng đó bao gồm:
- Xác thực: 
  - Đăng ký: Cần có mã OTP để xác nhận email!
  - Đăng nhập: Tạo ra khóa JWT để xác thực khi đăng nhập thành công. Khóa này sẽ có khi người dùng đăng nhập và phải có nó để sử dụng các dịch vụ của trang web.
  - Quên mật khẩu: Người dùng nhập vào email để lấy mã OTP để lấy lại mật khẩu.
  - Lấy lại mật khẩu: Sử dụng mã OTP để lấy lại mật khẩu.
- Xem:
  - Xem khách sạn: Hiển thị danh sách tất cả khách sạn đang có.
  - Tìm kiếm khách sạn: Nhập vào khu vực, ngày nhận phòng và trả phòng để tìm kiếm khách sạn.
  - Xem thông tin chi tiết của 1 khách sạn: Hiển thị toàn bộ thông tin của 1 khách sạn kèm danh sách các loại phòng trong khách sạn đó.
  - Xem thông tin loại phòng: Hiển thị thông tin chi tiết của 1 loại phòng.
  - Xem bảng thông tin các dịch vụ thêm như: đưa đón, ăn sáng, ăn tối, tour du lịch,...
  - Xem hóa đơn trước khi thanh toán. 
  - Xem thông tin cá nhân của mình, lịch sử mua hàng của bản thân.
  - Xem các câu hỏi trong list câu hỏi có sẵn
  - Xem các trang BLOG thông tin giới thiệu về du lịch, về công ty
- CRUD:
  - Người dùng có thể tạo 1 Hóa đơn: Hóa đơn được tạo bằng các thông tin về khách sạn, loại phòng, dịch vụ kèm theo, ngày nhận và trả phòng mà người dùng đã chọn trước đó
  - Người dùng có thể chỉnh sửa các thông tin hóa đơn của mình
  - Người dùng có thể hủy hóa đơn đó(khi chưa thanh toán)
  - Có thể thêm, thông tin cá nhân, sửa thông tin và xóa thông tin của mình
  - Người dùng có thể hủy đơn mua hàng kể cả khi thanh toán xong nếu như đáp ứng điều kiện(Hủy trước 1 ngày so với ngày nhận phòng)
- Thao tác:
  - Người dùng có thể chat với Bot
  - Người dùng có thể thực hiện giao tiếp với Admin thông qua Email
- Quản lý (ADMIN), các chức năng quản lý cơ bản như xem, thêm, sửa, xóa:
  - Xem báo cáo thống kê của trang web
  - Quản lý thông tin người dùng
  - Quản lý thông tin khách sạn
  - Quản lý thông tin về các loại phòng, phòng
  - Quản lý thông tin của các dịch vụ tiện ích khách sạn
  - Quản lý thông tin của các hóa đơn
  - Quản lý thông tin liên quan tới lịch
  - Xem và kiểm tra Log của trang web
  - Xem và trả lời các câu hỏi của người dùng
# Database
Mô hình database của ứng dụng


# Sơ đồ hoạt động
![](/Anh/Screenshot_1033.png)

Ban đầu người dùng sẽ cần đăng ký, sau đó đăng nhập vào hệ thống. Với token đã được cấp, người dùng thực hiện quy trình như trong ảnh:
- Tìm kiếm khách sạn: Nhập vào khu vực, check_in, check_out
- Chọn khách sạn mà mình muốn
- Chọn loại phòng
- Chọn các dịch vụ thêm
- Xem lại hóa đơn
- Thanh toán hóa đơn
- Thanh toán thành công! Xác nhận đặt phòng!

