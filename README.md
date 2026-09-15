# Coloring App Data Server (GitHub Pages CDN & Load More API)

Kho lưu trữ dữ liệu tranh, CDN và API phân trang (Load More) cho ứng dụng Coloring by Number / Paint by Number. Host hoàn toàn miễn phí trên GitHub Pages.

---

## 📡 Tài liệu API Phân trang (Load More API)

Hệ thống cung cấp sẵn các endpoint JSON phân trang tĩnh để app gọi trực tiếp khi cuộn màn hình:

### 1. Lấy danh sách toàn bộ ảnh (Có phân trang / Load more)
* **Trang 1 (Khởi động):**
  `https://npngocanh228.github.io/Color-DB/public/api/all/page_1.json`
* **Trang 2 (Load more lần 1):**
  `https://npngocanh228.github.io/Color-DB/public/api/all/page_2.json`
* **Trang `N`:**
  `https://npngocanh228.github.io/Color-DB/public/api/all/page_{N}.json`

#### Cấu trúc JSON trả về cho mỗi trang:
```json
{
  "category": "all",
  "page": 1,
  "limit": 30,
  "total_items": 19603,
  "total_pages": 654,
  "has_more": true,
  "next_page": 2,
  "next_page_url": "https://npngocanh228.github.io/Color-DB/public/api/all/page_2.json",
  "images": [
    {
      "id": "CBN_Dragon_30x30px",
      "url": "https://npngocanh228.github.io/Color-DB/public/images/CBN_Dragon_30x30px.png",
      "free": true,
      "gif": false,
      "pixelCount": 1296,
      "release_date": "2026-09-15 00:00:00",
      "tags": ["animal", "fantasy"]
    },
    ... (30 ảnh)
  ]
}
```

* **Cơ chế gọi ở App:**
  1. Khi vào màn hình: Gọi `page_1.json`.
  2. Khi cuộn tới cuối danh sách: Nếu `has_more == true`, gọi tiếp `next_page_url` (hoặc tăng `page++`) rồi nối mảng `images` vào RecyclerView / ListView.
  3. Khi `has_more == false`: Dừng không gọi thêm nữa.

---

### 2. Lấy danh sách Categories / Danh mục
* **URL:** `https://npngocanh228.github.io/Color-DB/public/api/categories.json`
* **Trả về:** Danh sách các chủ đề (tag) kèm số lượng tranh và link trang 1 của chủ đề đó:
  ```json
  [
    {
      "tag": "animal",
      "count": 1494,
      "first_page_url": "https://npngocanh228.github.io/Color-DB/public/api/tag/animal/page_1.json"
    },
    {
      "tag": "cute",
      "count": 1955,
      "first_page_url": "https://npngocanh228.github.io/Color-DB/public/api/tag/cute/page_1.json"
    }
  ]
  ```

### 3. Lấy ảnh phân trang theo từng Chủ đề (Category)
* Ví dụ xem tranh chủ đề Động vật (`animal`):
  * Trang 1: `https://npngocanh228.github.io/Color-DB/public/api/tag/animal/page_1.json`
  * Trang 2: `https://npngocanh228.github.io/Color-DB/public/api/tag/animal/page_2.json`
* Tương tự với các tag khác: `cute`, `food`, `holiday`, `fantasy`, `people`...

---

## 📁 Cấu trúc thư mục

```text
coloring-data/
├── public/
│   ├── imagesupdates_android_compressed.json.gz   <-- Catalog nén (cho app gốc)
│   ├── images/                                    <-- 19.600+ file ảnh .png / .gif
│   └── api/                                       <-- API Phân trang Load more
│       ├── all/
│       │   ├── page_1.json
│       │   ├── page_2.json
│       │   └── ...
│       ├── tag/
│       │   ├── animal/page_1.json...
│       │   └── cute/page_1.json...
│       └── categories.json
├── tools/
│   ├── generate_paginated_api.py  <-- Tự động sinh lại toàn bộ API phân trang
│   ├── build_catalog.py           <-- Build lại catalog nén gzip
│   └── add_image.py               <-- Script thêm nhanh ảnh mới
├── api/images.js                  <-- Serverless API (Dành cho Vercel nếu cần)
├── vercel.json
└── README.md
```

---

## 🚀 Đẩy cập nhật lên GitHub Pages

Mở Terminal chạy lệnh:

```bash
cd /Users/quan/Downloads/coloring_decompiled/coloring-data

git add .
git commit -m "Add Paginated Load More API and full image collection"
git push
```
*(Chờ 1-2 phút GitHub Pages build xong là bạn có thể test ngay các link API trên)*.
