# 📱 HƯỚNG DẪN TRIỂN KHAI LƯU TRANH ĐÃ HOÀN THÀNH (DONE 100%) QUA FIREBASE
> **Dành cho**: Frontend (Android Kotlin / Flutter / React Native)  
> **Nguyên tắc cốt lõi**:
> - **Tranh chưa xong (0% - 99%)**: Lưu hoàn toàn ở **Local (máy người dùng)**. Không đẩy lên Cloud.
> - **Tranh ĐÃ XONG (100% DONE)**: Đẩy lên **Firebase Firestore** để bảo vệ data (xóa app cài lại vẫn còn).
> - **Chi phí Firebase**: **0 đồng (Hoàn toàn miễn phí)** vì 1 tranh chỉ ghi đúng 1 lần duy nhất trong đời tài khoản.

---

## 🏗️ 1. Mô Hình Hoạt Động (Workflow)

```
                       [Người dùng tô màu]
                                │
          ┌─────────────────────┴─────────────────────┐
          ▼                                           ▼
[Tranh Đang Tô (0% - 99%)]                  [Tranh ĐÃ XONG (100% DONE)]
          │                                           │
          ▼                                           ▼
┌───────────────────────────┐               ┌───────────────────────────┐
│     LƯU 100% TẠI LOCAL    │               │    ĐỒNG BỘ LÊN CLOUD      │
│  - SharedPreferences /    │               │  - Firebase Firestore     │
│    Room / SQLite / Hive   │               │  - Chỉ lưu ID tranh đã tô │
│  👉 Tự do lưu %, pixel    │               │  👉 Xóa app cài lại       │
│  👉 Mượt 60fps, ko mạng   │               │     KHÔNG BAO GIỜ MẤT     │
└───────────────────────────┘               └───────────────────────────┘
```

---

## 📐 2. Cấu Trúc Firestore (Siêu Tinh Gọn)

Mỗi người dùng có Document theo UID (Firebase Anonymous Auth hoặc Google Sign-in):

### Collection: `users/{userId}`
Lưu thông tin tóm tắt:
```json
{
  "totalCompleted": 15,
  "lastActive": 1726915600000
}
```

### Sub-collection: `users/{userId}/completed_artworks/{artworkId}`
Mỗi tranh hoàn thành lưu 1 document con với ID chính là mã bức tranh (vd: `CBN_Dragon_30x30px`):
```json
{
  "artworkId": "CBN_Dragon_30x30px",
  "completedAt": 1726915600000,
  "timeSpentSeconds": 135
}
```

---

## 🔒 3. Firebase Security Rules (Bảo mật cho Firestore)

Dán đoạn rule sau vào **Firebase Console -> Firestore Database -> Rules**:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      
      match /completed_artworks/{artworkId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
    }
  }
}
```

---

## 💻 4. Code Mẫu Android: Kotlin

### 4.1. Khởi tạo Auth ẩn danh (Tự động có UID khi mở App)
```kotlin
import com.google.firebase.auth.FirebaseAuth

object AuthManager {
    val uid: String?
        get() = FirebaseAuth.getInstance().currentUser?.uid

    fun init(onReady: (String) -> Unit) {
        val auth = FirebaseAuth.getInstance()
        val user = auth.currentUser
        if (user != null) {
            onReady(user.uid)
        } else {
            auth.signInAnonymously().addOnSuccessListener { res ->
                res.user?.uid?.let(onReady)
            }
        }
    }
}
```

### 4.2. Quản lý lưu tranh DONE (Firestore Repository)
```kotlin
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.FieldValue

class CompletedArtworksRepository {
    private val db = FirebaseFirestore.getInstance()

    // 1. GỌI KHI TRANH ĐẠT 100%: Lưu lên Firestore
    fun markAsDone(artworkId: String, timeSpentSeconds: Long = 0) {
        val uid = AuthManager.uid ?: return

        val docRef = db.collection("users").document(uid)
            .collection("completed_artworks").document(artworkId)

        val data = mapOf(
            "artworkId" to artworkId,
            "completedAt" to System.currentTimeMillis(),
            "timeSpentSeconds" to timeSpentSeconds
        )

        docRef.set(data).addOnSuccessListener {
            // Tăng tổng số tranh hoàn thành
            db.collection("users").document(uid).set(
                mapOf(
                    "totalCompleted" to FieldValue.increment(1),
                    "lastActive" to System.currentTimeMillis()
                ),
                com.google.firebase.firestore.SetOptions.merge()
            )
        }
    }

    // 2. GỌI KHI MỞ APP (Hoặc khi cài lại app): Tải danh sách các ID tranh đã tô xong
    fun getCompletedArtworkIds(onSuccess: (Set<String>) -> Unit) {
        val uid = AuthManager.uid ?: run {
            onSuccess(emptySet())
            return
        }

        db.collection("users").document(uid)
            .collection("completed_artworks")
            .get()
            .addOnSuccessListener { snapshot ->
                val completedIds = snapshot.documents.mapNotNull { it.getString("artworkId") }.toSet()
                onSuccess(completedIds)
            }
            .addOnFailureListener {
                onSuccess(emptySet())
            }
    }
}
```

---

## 💙 5. Code Mẫu Flutter (Dart)

### 5.1. Khởi tạo Auth
```dart
import 'package:firebase_auth/firebase_auth.dart';

class AuthService {
  static String? get currentUid => FirebaseAuth.instance.currentUser?.uid;

  static Future<String> initAuth() async {
    User? user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      final cred = await FirebaseAuth.instance.signInAnonymously();
      user = cred.user;
    }
    return user!.uid;
  }
}
```

### 5.2. Service lưu và lấy danh sách tranh DONE
```dart
import 'package:cloud_firestore/cloud_firestore.dart';

class CompletedArtworksService {
  static final _db = FirebaseFirestore.instance;

  // 1. GỌI KHI TRANH ĐẠT 100%
  static Future<void> markAsDone(String artworkId, {int timeSpent = 0}) async {
    final uid = AuthService.currentUid;
    if (uid == null) return;

    final docRef = _db
        .collection('users')
        .doc(uid)
        .collection('completed_artworks')
        .doc(artworkId);

    await docRef.set({
      'artworkId': artworkId,
      'completedAt': DateTime.now().millisecondsSinceEpoch,
      'timeSpentSeconds': timeSpent,
    });

    // Cập nhật tổng số tranh hoàn thành
    await _db.collection('users').doc(uid).set({
      'totalCompleted': FieldValue.increment(1),
      'lastActive': DateTime.now().millisecondsSinceEpoch,
    }, SetOptions(merge: true));
  }

  // 2. GỌI KHI KHỞI ĐỘNG APP: Lấy danh sách ID các tranh đã tô xong
  static Future<Set<String>> getCompletedArtworkIds() async {
    final uid = AuthService.currentUid;
    if (uid == null) return {};

    try {
      final snapshot = await _db
          .collection('users')
          .doc(uid)
          .collection('completed_artworks')
          .get();

      return snapshot.docs
          .map((doc) => doc.data()['artworkId'] as String?)
          .whereType<String>()
          .toSet();
    } catch (e) {
      return {};
    }
  }
}
```

---

## 🎨 6. Cách FE Ghép Vào Danh Sách Tranh (UI Integration)

Khi FE gọi API lấy danh mục tranh từ server:
`https://npngocanh228.github.io/Color-DB/public/api/categories/animals/page_1.json`

```
1. Khi mở App:
   👉 Tải Set các ID đã xong: Set<String> completedIds = ["KIO_fantasybagdad_3", "plncute_11", ...]

2. Khi render từng item trong ListView / GridView:
   👉 val isCompleted = completedIds.contains(item.id)

3. Hiển thị UI:
   - Nếu isCompleted == true:
       + Đè ảnh tranh đã hoàn thiện lên
       + Hiển thị icon huy hiệu "Đã Tô Xong" ✅ (hoặc nút "Xem lại")
   - Nếu isCompleted == false:
       + Kiểm tra Local xem có % đang tô dở không (ví dụ: SharedPreferences.getInt(item.id, 0))
       + Nếu có % dở: Hiện thanh tiến độ (vd: 60%) + nút "Tô tiếp"
       + Nếu 0%: Hiện nút "Bắt đầu tô"
```

---

## 💰 7. Tại Sao Cách Này Tối Ưu Chi Phí Tuyệt Đối?

1. **Ghi (Write)**: Mỗi bức tranh chỉ tốn đúng **1 lượt Write DUY NHẤT** khi người dùng hoàn thành 100%. Nếu người chơi tô 5 bức tranh mỗi ngày = **5 lượt Write/ngày** (Gói Free của Firebase cho phép 20.000 Write/ngày $\rightarrow$ gánh được 4.000 người chơi mỗi ngày hoàn toàn 0đ).
2. **Đọc (Read)**: Khi mở app chỉ đọc 1 lần toàn bộ danh sách `completed_artworks` (hoặc dùng Offline Persistence của Firebase SDK thì lần sau đọc từ cache máy không tốn lượt Read).
3. **Dữ liệu**: Tranh chưa xong người dùng đổi ý xóa app thì không cần khôi phục, chỉ khôi phục các tác phẩm nghệ thuật họ đã bỏ công sức hoàn thành 100%!
