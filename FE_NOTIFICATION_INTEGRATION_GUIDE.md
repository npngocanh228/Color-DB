# 📱 TÀI LIỆU FRONTEND (FE): THU THẬP & ĐỒNG BỘ THÔNG TIN ĐỂ NHẬN PUSH NOTIFICATION
> **Dành cho**: Đội ngũ Frontend Mobile (Android Kotlin / Flutter / React Native / iOS Swift)  
> **Mục tiêu**: Hướng dẫn FE lấy và gửi đầy đủ các thông số thiết bị (FCM Token, Ngôn ngữ, Múi giờ, Platform, Quyền thông báo) lên Backend/Firestore để Backend có thể bắn thông báo **đúng ngôn ngữ, đúng người, đúng múi giờ địa phương (không bắn lúc nửa đêm)** và **mở thẳng vào tranh khi click thông báo**.

---

## 📋 1. Danh Sách Các Trường Dữ Liệu FE Cần Gửi (Data Contract)

Dưới đây là các thông tin chuẩn mà Backend yêu cầu FE thu thập và gửi lên:

| Trường (Field) | Kiểu dữ liệu | Bắt buộc | Ví dụ mẫu | Mục đích sử dụng của Backend |
| :--- | :--- | :---: | :--- | :--- |
| `userId` | `String` | **Có** | `"u_89123849"` | Định danh người dùng (từ Firebase Auth / Guest ID) |
| `fcmToken` | `String` | **Có** | `"fK9xL2pQ_8z:APA91..."` | Mã token duy nhất của thiết bị để Firebase gửi tin nhắn tới |
| `language` | `String` | **Có** | `"vi"`, `"en"`, `"ja"` | Mã ngôn ngữ app đang dùng (ISO 639-1) để gửi đúng bản dịch |
| `timezone` | `String` | **Có** | `"Asia/Ho_Chi_Minh"` | Múi giờ IANA để Backend tính giờ gửi (vd: gửi lúc 20h tối của user) |
| `timezoneOffsetMinutes` | `Int` | Khuyên dùng | `420` (cho UTC+7) | Độ lệch phút so với UTC để Backend tính giờ dễ dàng |
| `platform` | `String` | **Có** | `"android"` hoặc `"ios"` | Phân loại nền tảng hệ điều hành |
| `appVersion` | `String` | Khuyên dùng | `"1.0.2"` | Hỗ trợ lọc gửi thông báo cập nhật cho version cũ |
| `notificationsEnabled` | `Boolean` | Khuyên dùng | `true` | Trạng thái người dùng đã cấp quyền thông báo trong OS |
| `lastActive` | `Long` | **Có** | `1726915600000` | Timestamp mở app gần nhất (để lọc user bỏ app lâu ngày) |

---

## 🌐 2. Phương Thức Gửi Dữ Liệu Lên Hệ Thống

FE có thể lựa chọn 1 trong 2 cách sau tùy theo kiến trúc của dự án:

### CÁCH A: Ghi trực tiếp vào Firebase Firestore (Khuyên dùng nếu dùng Firebase)
FE ghi đè/hợp nhất vào Document: **`users/{userId}`**:
```json
{
  "userId": "u_89123849",
  "fcmToken": "fK9xL2pQ_8z:APA91bH7e...",
  "language": "vi",
  "timezone": "Asia/Ho_Chi_Minh",
  "timezoneOffsetMinutes": 420,
  "platform": "android",
  "appVersion": "1.0.0",
  "notificationsEnabled": true,
  "lastActive": 1726915600000
}
```

### CÁCH B: Gửi qua REST API Backend (Nếu dự án có Server API riêng)
* **Endpoint**: `POST /api/user/device-info`
* **Headers**: `Content-Type: application/json`, `Authorization: Bearer <token_neu_co>`
* **Body (JSON)**:
```json
{
  "user_id": "u_89123849",
  "fcm_token": "fK9xL2pQ_8z:APA91bH7e...",
  "language": "vi",
  "timezone": "Asia/Ho_Chi_Minh",
  "timezone_offset_minutes": 420,
  "platform": "android",
  "app_version": "1.0.0",
  "notifications_enabled": true
}
```

---

## ⏰ 3. Bốn (4) Thời Điểm Bắt Buộc FE Phải Gửi Thông Tin

FE không cần gửi liên tục mỗi màn hình, chỉ gửi vào **4 thời điểm sau**:
1. **Khi mở App lần đầu hoặc sau mỗi lần khởi động (App Launch)**: Thu thập thông tin và gửi lên server.
2. **Khi FCM Token được làm mới (`onNewToken`)**: Firebase sẽ tự đổi token định kỳ, FE phải bắt sự kiện này để cập nhật token mới.
3. **Khi Người dùng ĐỔI NGÔN NGỮ trong Settings của App**: Ví dụ người dùng từ tiếng Anh chuyển sang tiếng Việt $\rightarrow$ Gửi cập nhật `language = "vi"` ngay để lần sau nhận thông báo tiếng Việt.
4. **Khi Người dùng Bật / Tắt quyền nhận thông báo trong Cài đặt**.

---

## 💻 4. Code Mẫu Triển Khai Hoàn Chỉnh Cho Android (Kotlin)

### 4.1. Lớp Helper thu thập dữ liệu thiết bị (`DeviceSyncHelper.kt`)
```kotlin
package com.coloring.app.notifications

import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationManagerCompat
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.SetOptions
import com.google.firebase.messaging.FirebaseMessaging
import java.util.Locale
import java.util.TimeZone

object DeviceSyncHelper {

    fun syncDeviceInfo(context: Context, customLanguage: String? = null) {
        val uid = FirebaseAuth.getInstance().currentUser?.uid ?: return

        // 1. Lấy FCM Token mới nhất
        FirebaseMessaging.getInstance().token.addOnSuccessListener { token ->
            // 2. Lấy ngôn ngữ: ưu tiên ngôn ngữ user chọn trong app, nếu không lấy của máy
            val lang = customLanguage ?: Locale.getDefault().language.lowercase()

            // 3. Lấy múi giờ IANA và offset
            val tz = TimeZone.getDefault()
            val timezoneName = tz.id // vd: "Asia/Ho_Chi_Minh"
            val offsetMinutes = tz.getOffset(System.currentTimeMillis()) / (1000 * 60)

            // 4. Lấy version app
            val appVersion = try {
                val pInfo = context.packageManager.getPackageInfo(context.packageName, 0)
                pInfo.versionName ?: "1.0.0"
            } catch (e: Exception) {
                "1.0.0"
            }

            // 5. Kiểm tra quyền thông báo
            val isNotiEnabled = NotificationManagerCompat.from(context).areNotificationsEnabled()

            val deviceData = mapOf(
                "userId" to uid,
                "fcmToken" to token,
                "language" to lang,
                "timezone" to timezoneName,
                "timezoneOffsetMinutes" to offsetMinutes,
                "platform" to "android",
                "deviceModel" to "${Build.MANUFACTURER} ${Build.MODEL}",
                "appVersion" to appVersion,
                "notificationsEnabled" to isNotiEnabled,
                "lastActive" to System.currentTimeMillis()
            )

            // Lưu trực tiếp vào Firestore
            FirebaseFirestore.getInstance()
                .collection("users")
                .document(uid)
                .set(deviceData, SetOptions.merge())

            // Đăng ký topic ngôn ngữ tương ứng
            FirebaseMessaging.getInstance().subscribeToTopic("lang_$lang")
        }
    }
}
```

### 4.2. Xử lý Token Refresh trong `MyFirebaseMessagingService.kt`
```kotlin
package com.coloring.app.notifications

import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

class MyFirebaseMessagingService : FirebaseMessagingService() {

    // Khi Firebase tự động cấp token mới cho thiết bị
    override fun onNewToken(token: String) {
        super.onNewToken(token)
        // Đồng bộ lại token mới lên Firestore / Backend
        DeviceSyncHelper.syncDeviceInfo(applicationContext)
    }

    // Khi nhận được thông báo lúc đang mở app (Foreground)
    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        super.onMessageReceived(remoteMessage)
        
        // Đọc dữ liệu kèm theo (nếu Backend có gửi artworkId)
        val artworkId = remoteMessage.data["artworkId"]
        
        // Hiển thị Custom Notification trong status bar (nếu cần)
    }
}
```

---

## 💙 5. Code Mẫu Triển Khai Hoàn Chỉnh Cho Flutter (Dart)

```dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:package_info_plus/package_info_plus.dart';

class DeviceNotificationService {
  static final _fcm = FirebaseMessaging.instance;
  static final _db = FirebaseFirestore.instance;
  static final _auth = FirebaseAuth.instance;

  static Future<void> initAndSyncDevice({String? customLanguage}) async {
    // 1. Xin quyền thông báo (bắt buộc với iOS và Android 13+)
    NotificationSettings settings = await _fcm.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    bool isEnabled = settings.authorizationStatus == AuthorizationStatus.authorized;

    // 2. Lấy UID của User
    String? uid = _auth.currentUser?.uid;
    if (uid == null) {
      UserCredential cred = await _auth.signInAnonymously();
      uid = cred.user!.uid;
    }

    // 3. Lấy FCM Token
    String? token = await _fcm.getToken();
    if (token == null) return;

    // 4. Lấy ngôn ngữ
    String lang = customLanguage ?? Platform.localeName.split('_')[0].toLowerCase();

    // 5. Lấy múi giờ
    DateTime now = DateTime.now();
    Duration offset = now.timeZoneOffset;
    String timezoneName = now.timeZoneName;
    int offsetMinutes = offset.inMinutes;

    // 6. Lấy phiên bản App
    String appVersion = "1.0.0";
    try {
      PackageInfo packageInfo = await PackageInfo.fromPlatform();
      appVersion = packageInfo.version;
    } catch (_) {}

    // 7. Đồng bộ lên Firestore
    await _db.collection('users').doc(uid).set({
      'userId': uid,
      'fcmToken': token,
      'language': lang,
      'timezone': timezoneName,
      'timezoneOffsetMinutes': offsetMinutes,
      'platform': Platform.isAndroid ? 'android' : 'ios',
      'appVersion': appVersion,
      'notificationsEnabled': isEnabled,
      'lastActive': DateTime.now().millisecondsSinceEpoch,
    }, SetOptions(merge: true));

    // 8. Đăng ký nhận thông báo theo Topic ngôn ngữ
    await _fcm.subscribeToTopic('lang_$lang');

    // 9. Lắng nghe khi token bị refresh
    _fcm.onTokenRefresh.listen((newToken) {
      _db.collection('users').doc(uid).update({
        'fcmToken': newToken,
      });
    });
  }

  // Gọi hàm này khi user đổi ngôn ngữ trong cài đặt của App
  static Future<void> onUserChangeLanguage(String oldLang, String newLang) async {
    await _fcm.unsubscribeFromTopic('lang_$oldLang');
    await _fcm.subscribeToTopic('lang_$newLang');

    String? uid = _auth.currentUser?.uid;
    if (uid != null) {
      await _db.collection('users').doc(uid).update({
        'language': newLang.toLowerCase(),
      });
    }
  }
}
```

---

## 🎯 6. Xử Lý Khi Người Dùng Bấm Vào Thông Báo (Click Action & Deep Link)

Khi Backend gửi thông báo có kèm dữ liệu bức tranh:
`data: {"artworkId": "CBN_Dragon_30x30px", "category": "animals"}`

### Yêu cầu xử lý phía FE:
Khi người dùng chạm vào thông báo trên thanh trạng thái:
1. App tự động khởi động.
2. Đọc payload `artworkId` trong intent/remote message.
3. Điều hướng người dùng **vào thẳng màn hình tô của bức tranh đó**, không bắt người dùng phải tự tìm trong danh sách!

#### Code Flutter bắt sự kiện click thông báo:
```dart
// Khi app đang mở hoặc đang chạy ngầm bấm vào thông báo:
FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
  if (message.data.containsKey('artworkId')) {
    String artworkId = message.data['artworkId'];
    // Điều hướng vào màn hình tô màu với artworkId này:
    Navigator.pushNamed(context, '/coloring_canvas', arguments: artworkId);
  }
});

// Khi app bị đóng hoàn toàn (Terminated) được mở lên từ thông báo:
RemoteMessage? initialMessage = await FirebaseMessaging.instance.getInitialMessage();
if (initialMessage != null && initialMessage.data.containsKey('artworkId')) {
  String artworkId = initialMessage.data['artworkId'];
  Navigator.pushNamed(context, '/coloring_canvas', arguments: artworkId);
}
```

---

## ✅ Checklist Kiểm Tra Cho Đội FE

- [ ] Khi cài app và mở lần đầu, Firestore Document `users/{userId}` đã có đủ 8 trường dữ liệu ở bảng mục 1.
- [ ] Múi giờ `timezone` và `timezoneOffsetMinutes` hiển thị đúng với múi giờ thực tế của thiết bị thử nghiệm.
- [ ] Đổi ngôn ngữ trong Cài đặt App $\rightarrow$ Trường `language` trên Firestore tự động cập nhật ngay.
- [ ] Chạm vào thông báo mẫu Backend bắn thử $\rightarrow$ Mở app thành công và nhảy đúng vào tranh tương ứng.
