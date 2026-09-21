# 🚀 HƯỚNG DẪN SỬ DỤNG TOOL PUSH NOTIFICATION BACKEND (FCM)
> **Vị trí file tool**: `coloring-data/tools/push_notification_tool.py`  
> **Chức năng**: Bắn thông báo tự động từ Backend qua Firebase Cloud Messaging (FCM), tự động dịch đúng ngôn ngữ (`vi`, `en`, `ja`, `ko`, `zh`, `es`, `pt`, `fr`) của từng người dùng.

---

## 🔑 1. Chuẩn Bị File Chứng Thực Firebase (Service Account)

1. Mở [Firebase Console](https://console.firebase.google.com/) $\rightarrow$ Chọn dự án của bạn.
2. Bấm vào icon bánh răng **Project Settings (Cài đặt dự án)** $\rightarrow$ Tab **Service accounts (Tài khoản dịch vụ)**.
3. Bấm nút **Generate new private key (Tạo khóa riêng tư mới)**.
4. Bạn sẽ tải về 1 file `.json`. Đổi tên file đó thành:
   `serviceAccountKey.json`
5. Đặt file này vào thư mục `coloring-data/tools/` (hoặc thư mục gốc dự án).

---

## 📦 2. Cài Đặt Thư Viện Python (Chỉ chạy 1 lần)

```bash
pip3 install firebase-admin
```

---

## 🎯 3. Các Lệnh Bắn Thông Báo Thông Dụng

### Trường hợp 1: Bắn đích danh 1 User bằng Token và Ngôn ngữ của họ
*(Khi Backend nhận được request từ FE gửi lên gồm `fcm_token` và `lang`)*:

```bash
# Bắn thông báo tiếng Việt:
python3 coloring-data/tools/push_notification_tool.py \
  --token "fK9xL2pQ_8z:APA91bH7e..." \
  --lang vi \
  --template new_artworks

# Bắn thông báo tiếng Anh:
python3 coloring-data/tools/push_notification_tool.py \
  --token "fK9xL2pQ_8z:APA91bH7e..." \
  --lang en \
  --template unfinished_reminder

# Bắn thông báo tiếng Nhật:
python3 coloring-data/tools/push_notification_tool.py \
  --token "fK9xL2pQ_8z:APA91bH7e..." \
  --lang ja \
  --template daily_streak
```

---

### Trường hợp 2: Bắn theo User ID (Tự động đọc Firestore)
*(Tool sẽ tự tìm `userId` trong Firestore để lấy `fcmToken` và `language`, rồi bắn đúng ngôn ngữ của họ)*:

```bash
python3 coloring-data/tools/push_notification_tool.py \
  --user-id "USER_UID_12345" \
  --template unfinished_reminder
```

---

### Trường hợp 3: Bắn Hàng Loạt Toàn Bộ Người Dùng Trong Firestore
*(Tool sẽ duyệt qua toàn bộ database, người Việt nhận tiếng Việt, người Mỹ nhận tiếng Anh, người Nhật nhận tiếng Nhật)*:

```bash
python3 coloring-data/tools/push_notification_tool.py \
  --from-firestore \
  --template new_artworks
```

---

### Trường hợp 4: Bắn Qua Topic Ngôn Ngữ (Siêu Nhanh, Không Cần Quét Database)
*(Dành cho thông báo sự kiện, tranh mới tới hàng triệu user)*:

```bash
python3 coloring-data/tools/push_notification_tool.py \
  --topic-lang \
  --template weekend_special
```

---

### Trường hợp 5: Bắn Tiêu Đề & Nội Dung Tùy Chỉnh (Custom)
```bash
python3 coloring-data/tools/push_notification_tool.py \
  --token "fK9xL2pQ_8z..." \
  --title "Chào bạn!" \
  --body "Hôm nay bạn đã tô màu chưa?" \
  --data '{"artworkId":"CBN_Dragon_30x30px"}'
```

---

## 🎨 4. Danh Sách Mẫu Thông Báo Có Sẵn (`--template`)

Tool đã tích hợp sẵn các mẫu thông báo đa ngôn ngữ được tối ưu hóa copywriting cho game tô màu:

| Template Name | Nội dung thông báo |
| :--- | :--- |
| `new_artworks` | Thông báo có tranh mới hôm nay (Daily New Art) |
| `unfinished_reminder` | Nhắc nhở người dùng quay lại hoàn thành tranh dở dang |
| `daily_streak` | Nhắc nhở duy trì chuỗi ngày tô màu liên tục để nhận sao |
| `weekend_special` | Sự kiện thư giãn cuối tuần mở khóa bộ sưu tập miễn phí |

---

## 🧪 5. Chế Độ Test Thử Nghiệm Không Bắn Thật (`--dry-run`)
Bạn có thể thêm cờ `--dry-run` vào bất kỳ lệnh nào để kiểm tra nội dung hiển thị trên terminal mà không cần token thật:
```bash
python3 coloring-data/tools/push_notification_tool.py --topic-lang --template daily_streak --dry-run
```
