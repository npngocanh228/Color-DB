# Coloring App Data Server (GitHub Pages CDN)

Kho lưu trữ dữ liệu tranh và danh mục catalog cho ứng dụng Coloring by Number / Paint by Number. Host hoàn toàn miễn phí trên GitHub Pages.

---

## 📁 Cấu trúc thư mục

```text
coloring-data/
├── public/
│   ├── imagesupdates_android_compressed.json.gz   <-- File nén catalog app tải về
│   ├── imagesupdates_android_compressed.json      <-- File json catalog đọc được
│   └── images/                                    <-- Thư mục chứa các file .png / .gif
│       ├── CBN_BabyEgg_30x30px.png
│       ├── anim_cupcake.gif
│       └── ... (18 ảnh có sẵn)
├── tools/
│   ├── build_catalog.py   <-- Tự động quét thư mục images để build lại file JSON & JSON.GZ
│   └── add_image.py       <-- Script thêm nhanh ảnh mới vào thư mục và cập nhật catalog
└── README.md
```

---

## 🚀 Các bước đưa lên GitHub và kích hoạt GitHub Pages

### Bước 1: Tạo Repository trên GitHub
1. Đăng nhập vào [GitHub](https://github.com) và bấm **New repository**.
2. Đặt tên (ví dụ: `coloring-data`).
3. Chọn chế độ **Public** và bấm **Create repository**.

### Bước 2: Push code lên GitHub
Mở Terminal trên máy Mac của bạn và chạy:

```bash
cd /Users/quan/Downloads/coloring_decompiled/coloring-data

# Khởi tạo git repo
git init
git add .
git commit -m "Initial coloring data"
git branch -M main

# Trỏ tới repo vừa tạo trên GitHub (thay <username> và <repo-name> của bạn)
git remote add origin https://github.com/<username>/<repo-name>.git
git push -u origin main
```

### Bước 3: Bật GitHub Pages
1. Vào repository trên GitHub của bạn.
2. Vào **Settings** $\rightarrow$ chọn mục **Pages** (ở menu bên trái).
3. Tại phần **Build and deployment**:
   * **Source:** Chọn `Deploy from a branch`
   * **Branch:** Chọn `main`, thư mục chọn `/ (root)`
   * Bấm **Save**.
4. Chờ khoảng 1-2 phút, GitHub sẽ hiển thị đường link CDN của bạn dạng:
   ```text
   https://<username>.github.io/<repo-name>/
   ```

---

## 📱 Cấu hình vào App Android

Trong source code app decompile, bạn mở file [Addresses.java](file:///Users/quan/Downloads/coloring_decompiled/sources/com/fungamesforfree/colorbynumberandroid/Addresses/Addresses.java) và đổi URL sang link GitHub Pages của bạn:

```java
// Thay <username> và <repo-name> tương ứng:
public static final String CBN_PROD_REMOTE_CONTENT_URL = "https://<username>.github.io/<repo-name>/public/";
```

> **Lưu ý:** Đảm bảo cuối đường dẫn có dấu gạch chéo `/public/`. App sẽ tự động tải `https://<username>.github.io/<repo-name>/public/imagesupdates_android_compressed.json.gz` và ảnh tại `/public/images/{id}.png`.

---

## 🎨 Cách thêm tranh mới sau này

Khi bạn có ảnh `.png` hoặc `.gif` mới muốn thêm vào app:

1. Chạy lệnh:
   ```bash
   python3 tools/add_image.py /duong/dan/toi/anh_moi.png --tags "Animals,Cute"
   ```
   *(Nếu là tranh VIP yêu cầu tài khoản trả phí, thêm cờ `--vip`)*

2. Push cập nhật lên GitHub:
   ```bash
   git add .
   git commit -m "Add new image"
   git push
   ```
GitHub Pages sẽ tự cập nhật trong vòng vài giây, và tất cả người dùng mở app sẽ thấy tranh mới ngay lập tức!
