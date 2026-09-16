# Coloring App Data Server (CDN & Category-based Load More API)

Kho lưu trữ dữ liệu tranh, CDN và API phân trang (Load More) tổ chức chuẩn theo **Categories / Chủ đề** cho ứng dụng Tô màu theo số (Color by Number / Pixel Art Paint). Host hoàn toàn miễn phí trên GitHub Pages.

---

## 📡 Tài liệu API Phân trang theo Categories

### 1. Lấy danh sách toàn bộ Categories (Menu / Danh mục chính)
* **URL:**  
  `https://npngocanh228.github.io/Color-DB/public/api/categories.json`
* **JSON trả về:**
  ```json
  {
    "version": 2,
    "total_categories": 31,
    "categories": [
      {
        "id": "animals",
        "folder": "animals",
        "name": "Động Vật",
        "name_en": "Animals",
        "icon_url": "https://npngocanh228.github.io/Color-DB/public/artworks/animals/01.png",
        "total_items": 1625,
        "total_pages": 55,
        "first_page_url": "https://npngocanh228.github.io/Color-DB/public/api/categories/animals/page_1.json"
      },
      ...
    ]
  }
  ```

---

### 2. Lấy tranh có phân trang (Load More) theo từng Category
Mỗi Category đều có API phân trang riêng với 30 ảnh/trang:

* **Ví dụ danh mục Động vật (`animals`):**
  * **Trang 1:** `https://npngocanh228.github.io/Color-DB/public/api/categories/animals/page_1.json`
  * **Trang 2:** `https://npngocanh228.github.io/Color-DB/public/api/categories/animals/page_2.json`
  * **Trang N:** `https://npngocanh228.github.io/Color-DB/public/api/categories/animals/page_{N}.json`

* **Cấu trúc JSON trả về:**
  ```json
  {
    "category": "animals",
    "category_name": "Động Vật",
    "category_name_en": "Animals",
    "page": 1,
    "limit": 30,
    "total_items": 1625,
    "total_pages": 55,
    "has_more": true,
    "next_page": 2,
    "next_page_url": "https://npngocanh228.github.io/Color-DB/public/api/categories/animals/page_2.json",
    "items": [
      {
        "id": "animals_01",
        "title": "Động Vật 01",
        "file_name": "01.png",
        "url": "https://npngocanh228.github.io/Color-DB/public/artworks/animals/01.png",
        "thumbnail_url": "https://npngocanh228.github.io/Color-DB/public/artworks/animals/01.png",
        "category": "animals",
        "category_name": "Động Vật",
        "free": true,
        "gif": false,
        "pixelCount": 1000
      },
      ... (30 ảnh)
    ]
  }
  ```

---

### 3. Tương thích với cấu trúc Artworks gốc của PixelArtPaint:
* `categories.json`: `https://npngocanh228.github.io/Color-DB/public/artworks/categories.json`
* Ảnh trực tiếp: `https://npngocanh228.github.io/Color-DB/public/artworks/{folder}/{filename}.png`
* Town: `https://npngocanh228.github.io/Color-DB/public/town/`

---

## 🚀 Lệnh cập nhật lên GitHub Pages

```bash
cd /Users/quan/Downloads/coloring_decompiled/coloring-data

git add .
git commit -m "Update category-based architecture and pagination API"
git push
```
