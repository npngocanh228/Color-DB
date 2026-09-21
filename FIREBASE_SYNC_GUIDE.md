# 📱 HƯỚNG DẪN TRIỂN KHAI FIREBASE CLOUD SYNC CHO FRONTEND (FE)
> **Dành cho**: Android (Kotlin) / Flutter / React Native  
> **Mục tiêu**: Lưu tiến trình tô màu (Coloring Progress), khôi phục data khi xóa app cài lại hoặc đổi máy, **100% Offline-First** và **hoàn toàn miễn phí (0đ trong Firebase Free Tier)**.

---

## 🏗️ 1. Kiến Trúc Tổng Quan (Offline-First Architecture)

```
[Người dùng chạm tô màu]
          │
          ▼ (Cực mượt 60/120fps, không phụ thuộc mạng)
┌──────────────────────────────────────────────┐
│       1. LOCAL STORAGE (Máy người dùng)      │
│  - Android: Room Database / SQLite           │
│  - Flutter: Hive / Isar / SQLite             │
│  👉 Lưu chi tiết từng pixel đã tô            │
└──────────────────────────────────────────────┘
          │
          │ (Chỉ đồng bộ khi: Xong tranh 100% HOẶC Thoát Canvas)
          ▼
┌──────────────────────────────────────────────┐
│       2. CLOUD FIRESTORE (Đồng bộ đám mây)   │
│  👉 Chỉ lưu: %, trạng thái, thời gian        │
│  👉 1 bức tranh chỉ tốn đúng 1 - 2 lượt Ghi  │
│  👉 Gói Free gánh được 5.000 - 10.000 DAU    │
└──────────────────────────────────────────────┘
```

---

## 📐 2. Cấu Trúc Dữ Liệu (Firestore Schema)

Cơ sở dữ liệu Firestore được tổ chức theo cấu trúc sau:

### Collection: `users`
Mỗi người dùng có một Document mang tên `userId` (UID từ Firebase Auth).

#### Document: `users/{userId}`
Lưu thông tin tổng quan của người chơi:
```json
{
  "displayName": "Pixel Painter #8492",
  "avatar": "avatar_01",
  "totalCompleted": 12,
  "level": 3,
  "stars": 45,
  "createdAt": 1726912345000,
  "lastActive": 1726915600000
}
```

#### Sub-collection: `users/{userId}/artworks/{artworkId}`
Mỗi bức tranh là 1 Document con, tên Document chính là `artworkId` (vd: `CBN_Dragon_30x30px`):
```json
{
  "artworkId": "CBN_Dragon_30x30px",
  "percent": 100,
  "status": "completed",
  "completedAt": 1726915600000,
  "timeSpentSeconds": 145,
  "updatedAt": 1726915600000,
  "paintedPixelsCompressed": "" 
}
```

> **Ghi chú về `paintedPixelsCompressed`**:
> - Nếu tranh **đã hoàn thành 100%**: Đặt chuỗi rỗng `""` (vì khi mở lại app chỉ cần render tranh hoàn chỉnh).
> - Nếu tranh **đang tô dở dang**: Nén mảng các pixel đã tô thành chuỗi Base64 hoặc Bitmask ngắn để lưu, không lưu mảng thô hàng nghìn phần tử.

---

## 🔐 3. Firebase Authentication: Đăng Nhập Ẩn Danh (Anonymous)

### Nguyên tắc UX:
1. Khi user mới cài app: Tự động đăng nhập ẩn danh (`signInAnonymously()`). User không cần đăng ký hay gõ mật khẩu gì cả, có UID ngay lập tức.
2. Trong màn hình Settings / Profile: Cung cấp nút **"Liên kết tài khoản Google / Apple"** (`linkWithCredential`) để nếu đổi sang máy mới thì đăng nhập là data tự kéo về.

### Firebase Security Rules (Bảo mật chỉ cho chủ tài khoản đọc/ghi data của mình):
Paste đoạn rule này vào **Firebase Console -> Firestore Database -> Rules**:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      
      match /artworks/{artworkId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
    }
  }
}
```

---

## 💻 4. Hướng Dẫn Code Mẫu: Kotlin (Android)

### 4.1. Khởi tạo Auth ẩn danh khi mở App
```kotlin
import com.google.firebase.auth.FirebaseAuth

class AppAuthManager {
    private val auth = FirebaseAuth.getInstance()

    fun initAuth(onSuccess: (String) -> Unit) {
        val currentUser = auth.currentUser
        if (currentUser != null) {
            onSuccess(currentUser.uid)
        } else {
            auth.signInAnonymously().addOnSuccessListener { result ->
                result.user?.uid?.let { onSuccess(it) }
            }
        }
    }
}
```

### 4.2. Repository đồng bộ tiến trình lên Firestore
```kotlin
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.SetOptions

class ColoringSyncRepository {
    private val db = FirebaseFirestore.getInstance()
    private val auth = FirebaseAuth.getInstance()

    // 1. Đồng bộ khi hoàn thành bức tranh 100%
    fun syncCompletedArtwork(artworkId: String, timeSpentSeconds: Long) {
        val uid = auth.currentUser?.uid ?: return
        val docRef = db.collection("users").document(uid)
            .collection("artworks").document(artworkId)

        val data = mapOf(
            "artworkId" to artworkId,
            "percent" to 100,
            "status" to "completed",
            "completedAt" to System.currentTimeMillis(),
            "timeSpentSeconds" to timeSpentSeconds,
            "updatedAt" to System.currentTimeMillis()
        )

        docRef.set(data, SetOptions.merge())

        // Tăng tổng số tranh hoàn thành trong profile
        db.collection("users").document(uid).update(
            "totalCompleted", com.google.firebase.firestore.FieldValue.increment(1)
        )
    }

    // 2. Đồng bộ khi người dùng bấm Back thoát khỏi màn hình tô (tranh dở dang)
    fun syncInProgressArtwork(artworkId: String, percent: Int, compressedPixels: String) {
        val uid = auth.currentUser?.uid ?: return
        val docRef = db.collection("users").document(uid)
            .collection("artworks").document(artworkId)

        val data = mapOf(
            "artworkId" to artworkId,
            "percent" to percent,
            "status" to "in_progress",
            "paintedPixelsCompressed" to compressedPixels,
            "updatedAt" to System.currentTimeMillis()
        )

        docRef.set(data, SetOptions.merge())
    }

    // 3. Khôi phục toàn bộ tiến trình khi cài lại App
    fun restoreAllProgress(onSuccess: (Map<String, Int>) -> Unit) {
        val uid = auth.currentUser?.uid ?: return
        db.collection("users").document(uid).collection("artworks")
            .get()
            .addOnSuccessListener { snapshot ->
                val progressMap = mutableMapOf<String, Int>()
                for (doc in snapshot.documents) {
                    val id = doc.getString("artworkId") ?: continue
                    val percent = doc.getLong("percent")?.toInt() ?: 0
                    progressMap[id] = percent
                }
                onSuccess(progressMap)
            }
    }
}
```

---

## 💙 5. Hướng Dẫn Code Mẫu: Flutter (Dart)

### 5.1. Khởi tạo Auth
```dart
import 'package:firebase_auth/firebase_auth.dart';

class AuthService {
  static final _auth = FirebaseAuth.instance;

  static Future<String> getOrInitUserId() async {
    User? user = _auth.currentUser;
    if (user == null) {
      UserCredential cred = await _auth.signInAnonymously();
      user = cred.user;
    }
    return user!.uid;
  }
}
```

### 5.2. Service lưu và khôi phục tiến trình
```dart
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

class ColoringProgressService {
  static final _db = FirebaseFirestore.instance;
  static final _auth = FirebaseAuth.instance;

  static String? get _uid => _auth.currentUser?.uid;

  // 1. Khi tô xong 100%
  static Future<void> syncCompleted(String artworkId, int timeSpent) async {
    if (_uid == null) return;

    final doc = _db.collection('users').doc(_uid).collection('artworks').doc(artworkId);

    await doc.set({
      'artworkId': artworkId,
      'percent': 100,
      'status': 'completed',
      'completedAt': DateTime.now().millisecondsSinceEpoch,
      'timeSpentSeconds': timeSpent,
      'updatedAt': DateTime.now().millisecondsSinceEpoch,
    }, SetOptions(merge: true));

    // Tăng count profile
    await _db.collection('users').doc(_uid).set({
      'totalCompleted': FieldValue.increment(1),
      'lastActive': DateTime.now().millisecondsSinceEpoch,
    }, SetOptions(merge: true));
  }

  // 2. Khi thoát màn hình Canvas (Tranh đang dở dang)
  static Future<void> syncInProgress(String artworkId, int percent, String compressedPixels) async {
    if (_uid == null) return;

    final doc = _db.collection('users').doc(_uid).collection('artworks').doc(artworkId);

    await doc.set({
      'artworkId': artworkId,
      'percent': percent,
      'status': 'in_progress',
      'paintedPixelsCompressed': compressedPixels,
      'updatedAt': DateTime.now().millisecondsSinceEpoch,
    }, SetOptions(merge: true));
  }

  // 3. Khôi phục toàn bộ tiến trình khi mở App lần đầu (Restore data)
  static Future<Map<String, int>> fetchUserProgress() async {
    if (_uid == null) return {};

    final query = await _db.collection('users').doc(_uid).collection('artworks').get();
    Map<String, int> resultMap = {};

    for (var doc in query.docs) {
      final data = doc.data();
      final id = data['artworkId'] as String?;
      final percent = data['percent'] as int? ?? 0;
      if (id != null) {
        resultMap[id] = percent;
      }
    }
    return resultMap;
  }
}
```

---

## ⚡ 6. Best Practices Cho FE Khi Hiển Thị Danh Sách Tranh

Khi FE fetch danh sách tranh từ API phân trang của server:
`https://npngocanh228.github.io/Color-DB/public/api/categories/animals/page_1.json`

```
┌───────────────────────────────────┐
│     API Server (Color-DB)         │ ───▶ Trả về danh sách 30 tranh mẫu
└───────────────────────────────────┘
                  │
                  ▼ Kết hợp (Join)
┌───────────────────────────────────┐
│   Local Cache / Firestore Map     │ ───▶ { "CBN_Dragon_30x30px": 100, "plncute_11": 45 }
└───────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────┐
│ UI ITEM HIỂN THỊ:                                      │
│ - Nếu percent == 100: Hiện huy hiệu "Đã Hoàn Thành" ✅ │
│ - Nếu 0 < percent < 100: Hiện thanh tiến độ (vd: 45%)   │
│ - Nếu chưa có: Hiện nút "Tô Màu"                       │
└────────────────────────────────────────────────────────┘
```

---

## 🎯 7. Checklist Kiểm Thử (Testing Checklist)

1. [ ] Mở app lần đầu không có mạng: Chơi và lưu được bình thường (Local DB).
2. [ ] Bật mạng lên và hoàn thành tranh: Firestore có Document mới tại `users/{uid}/artworks/{id}`.
3. [ ] Xóa app cài lại trên cùng máy: Mở app lên toàn bộ các tranh đã tô trước đó vẫn giữ nguyên trạng thái hoàn thành.
4. [ ] Kiểm tra số lượt Write trên Firebase Console: Tô 1 bức tranh 5.000 pixel chỉ tăng **1 lượt Write** (không tăng 5.000 lượt).
