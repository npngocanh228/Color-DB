#!/usr/bin/env python3
import os
import json
import math

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
IMAGES_DIR = os.path.join(PUBLIC_DIR, "images")
API_DIR = os.path.join(PUBLIC_DIR, "api")
CATALOG_PATH = os.path.join(PUBLIC_DIR, "imagesupdates_android_compressed.json")

CDN_IMAGE_BASE = "https://npngocanh228.github.io/Color-DB/public/images/"
API_BASE = "https://npngocanh228.github.io/Color-DB/public/api/"
PAGE_SIZE = 30  # Số lượng ảnh mỗi trang (chuẩn cho mobile app load more)


def generate():
    print("[*] Đang đọc catalog...")
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Lấy danh sách các file ảnh thực tế có trong thư mục
    existing_files = set(os.listdir(IMAGES_DIR))
    print(f"[+] Số file ảnh thực tế trong thư mục: {len(existing_files)}")

    raw_images = catalog.get("images", [])
    valid_images = []

    for img in raw_images:
        img_id = img.get("id")
        if not img_id:
            continue
        is_gif = img.get("gif", False) or img.get("contentType") == "gif"
        ext = ".gif" if is_gif else ".png"
        filename = f"{img_id}{ext}"

        if filename in existing_files:
            valid_images.append({
                "id": img_id,
                "url": f"{CDN_IMAGE_BASE}{filename}",
                "free": img.get("free", True),
                "gif": is_gif,
                "pixelCount": img.get("pixelCount", 0),
                "release_date": img.get("release_date", ""),
                "tags": [t for t in img.get("tags", []) if t]
            })

    print(f"[+] Số ảnh hợp lệ để phân trang: {len(valid_images)}")

    # 1. Phân trang cho toàn bộ ảnh (ALL)
    paginate_list(valid_images, "all", "all")

    # 2. Phân loại và phân trang theo từng Tag/Category
    tag_map = {}
    for img in valid_images:
        for t in img["tags"]:
            # chuẩn hóa tên tag
            t_clean = t.strip().lower()
            if not t_clean:
                continue
            if t_clean not in tag_map:
                tag_map[t_clean] = []
            tag_map[t_clean].append(img)

    categories_index = []
    for tag_name, img_list in sorted(tag_map.items(), key=lambda x: len(x[1]), reverse=True):
        categories_index.append({
            "tag": tag_name,
            "count": len(img_list),
            "first_page_url": f"{API_BASE}tag/{tag_name}/page_1.json"
        })
        # Chỉ tạo tag nếu có từ 5 ảnh trở lên
        if len(img_list) >= 5:
            paginate_list(img_list, f"tag/{tag_name}", tag_name)

    # Lưu danh sách categories
    os.makedirs(API_DIR, exist_ok=True)
    with open(os.path.join(API_DIR, "categories.json"), "w", encoding="utf-8") as f:
        json.dump(categories_index, f, indent=2, ensure_ascii=False)

    print(f"[+] Đã tạo danh sách {len(categories_index)} categories tại: public/api/categories.json")
    print("[=== HOÀN TẤT PHÂN TRANG ===]")


def paginate_list(items, folder_subpath, title):
    folder_path = os.path.join(API_DIR, folder_subpath)
    os.makedirs(folder_path, exist_ok=True)

    total_items = len(items)
    total_pages = math.ceil(total_items / PAGE_SIZE)

    for p in range(1, total_pages + 1):
        start_idx = (p - 1) * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        page_items = items[start_idx:end_idx]

        has_more = p < total_pages
        next_page = p + 1 if has_more else None
        next_page_url = f"{API_BASE}{folder_subpath}/page_{p+1}.json" if has_more else None

        page_data = {
            "category": title,
            "page": p,
            "limit": PAGE_SIZE,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_more": has_more,
            "next_page": next_page,
            "next_page_url": next_page_url,
            "images": page_items
        }

        page_file = os.path.join(folder_path, f"page_{p}.json")
        with open(page_file, "w", encoding="utf-8") as f:
            json.dump(page_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    generate()
