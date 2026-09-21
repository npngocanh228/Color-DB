# 🎨 HƯỚNG DẪN KHỞI ĐỘNG VÀ SỬ DỤNG GIAO DIỆN BẮN THÔNG BÁO (PUSH NOTIFICATION ADMIN APP)

---

## ⚡ 1. Lệnh Khởi Động Nhanh (1 Giây)

Mở Terminal và gõ đúng 1 lệnh duy nhất:

```bash
python3 coloring-data/tools/noti_admin_server.py
```

* 🚀 Trình duyệt web của bạn sẽ **tự động bật lên** và mở trang quản trị tại:
👉 **`http://localhost:8080`**

*(Để tắt ứng dụng: Bạn chỉ cần quay lại cửa sổ Terminal và bấm tổ hợp phím **`Ctrl + C`**)*.

---

## 🔑 2. Chuẩn Bị File Chứng Thực Firebase (Chỉ Làm 1 Lần Khi Bắn Thật)

Nếu bạn muốn bắn thông báo thật tới máy người dùng qua Firebase:

1. Mở [Firebase Console](https://console.firebase.google.com/) $\rightarrow$ Chọn dự án của bạn.
2. Bấm vào icon bánh răng **Project Settings (Cài đặt dự án)** $\rightarrow$ Chọn tab **Service accounts (Tài khoản dịch vụ)**.
3. Bấm nút **Generate new private key (Tạo khóa riêng tư mới)** để tải về 1 file `.json`.
4. Đổi tên file đó thành:
   ```
   serviceAccountKey.json
   ```
5. Thả file này vào thư mục:
   ```
   coloring-data/tools/serviceAccountKey.json
   ```
6. Cài thư viện Firebase bằng lệnh:
   ```bash
   pip3 install firebase-admin
   ```

> 💡 **Mẹo**: Nếu bạn chưa kịp tải file chứng thực Firebase, bạn vẫn có thể mở app và sử dụng tính năng **"🧪 Thử Nghiệm (Dry Run)"** để xem trước nội dung và mô phỏng gửi 100% mượt mà!

---

## 🖥️ 3. Hướng Dẫn Sử Dụng Giao Diện Từng Bước

Giao diện được thiết kế gồm 2 phần: **Bảng Điều Khiển bên trái** và **Màn Hình Điện Thoại Mô Phỏng bên phải**.

### Bước 1: Chọn Đối Tượng Nhận Thông Báo
* **🎯 1 FCM Token**: Dành cho trường hợp bạn có mã `fcmToken` của 1 máy cụ thể (do FE gửi lên).
* **👤 1 User ID**: Nhập UID của người dùng $\rightarrow$ hệ thống tự tìm token và ngôn ngữ của user trong Firestore.
* **📢 Topic Ngôn Ngữ**: Bắn hàng loạt cho toàn bộ người dùng theo kênh ngôn ngữ (`lang_vi`, `lang_en`, `lang_ja`...).
* **👥 Tất Cả Users**: Quét toàn bộ database Firestore, người Việt nhận tiếng Việt, người Mỹ nhận tiếng Anh...

### Bước 2: Chọn Ngôn Ngữ (Language)
Chọn 1 trong 8 ngôn ngữ hỗ trợ:
* 🇻🇳 Tiếng Việt (`vi`)
* 🇺🇸 English (`en`)
* 🇯🇵 日本語 (`ja`)
* 🇰🇷 한국어 (`ko`)
* 🇨🇳 中文 (`zh`)
* 🇪🇸 Español (`es`)
* 🇧🇷 Português (`pt`)
* 🇫🇷 Français (`fr`)

### Bước 3: Chọn Mẫu Thông Báo Có Sẵn (Template Preset)
Khi bạn chọn mẫu, Tiêu đề và Nội dung sẽ **tự động dịch chuẩn sang ngôn ngữ bạn vừa chọn**:
* 🎨 **Có 10+ tranh mới hôm nay**: Thông báo tranh mới hàng ngày.
* ⏳ **Nhắc hoàn thành tranh dở dang**: Nhắc user quay lại tô nốt tranh.
* 🔥 **Giữ chuỗi ngày tô màu**: Nhắc duy trì streak nhận quà.
* ✨ **Sự kiện cuối tuần**: Mở khóa tranh đặc biệt.
* ✍️ **Tự nhập nội dung**: Tự do soạn thảo theo ý muốn.

### Bước 4: Xem Trước Trên Màn Hình Điện Thoại
* Khi bạn gõ phím hoặc đổi ngôn ngữ, **màn hình khóa của chiếc điện thoại bên phải sẽ thay đổi theo thời gian thực** giúp bạn thấy chính xác thông báo trông như thế nào trước khi bấm gửi.

### Bước 5: Bấm Gửi
* Bấm **"🚀 Bắn Thông Báo Ngay"** để gửi thật tới thiết bị.
* Hoặc bấm **"🧪 Thử Nghiệm (Dry Run)"** để kiểm tra kịch bản gửi.
* Khung **Nhật Ký (Output Log)** phía dưới sẽ báo kết quả gửi thành công hay thất bại ngay lập tức.
