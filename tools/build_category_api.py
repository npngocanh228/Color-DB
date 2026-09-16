#!/usr/bin/env python3
import os
import json
import math

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
ARTWORKS_DIR = os.path.join(PUBLIC_DIR, "artworks")
IMAGES_DIR = os.path.join(PUBLIC_DIR, "images")
API_DIR = os.path.join(PUBLIC_DIR, "api")
CAT_API_DIR = os.path.join(API_DIR, "categories")

CDN_BASE = "https://npngocanh228.github.io/Color-DB/public/"
PAGE_SIZE = 30  # Số ảnh mỗi trang (Load more)

# Danh sách danh mục chuẩn từ PixelArtPaint
CATEGORY_META = {
    "animals": {"name": "Động Vật", "name_en": "Animals"},
    "cute": {"name": "Đáng Yêu", "name_en": "Cute"},
    "cozy": {"name": "Cozy Lofi", "name_en": "Cozy Lofi"},
    "food": {"name": "Ẩm Thực", "name_en": "Food"},
    "flowers": {"name": "Hoa Cỏ", "name_en": "Flowers"},
    "scenery": {"name": "Phong Cảnh", "name_en": "Scenery"},
    "anime": {"name": "Anime", "name_en": "Anime"},
    "vip": {"name": "Bộ Sưu Tập VIP", "name_en": "VIP Collection"},
    "dailynew": {"name": "Mỗi Ngày", "name_en": "Daily Art"},
    "cartoon": {"name": "Hoạt Hình", "name_en": "Cartoon"},
    "love": {"name": "Tình Yêu", "name_en": "Love & Hearts"},
    "game": {"name": "Trò Chơi Retro", "name_en": "Retro Gaming"},
    "fashion": {"name": "Thời Trang", "name_en": "Fashion"},
    "dog": {"name": "Cún Cưng", "name_en": "Cute Dogs"},
    "birthday": {"name": "Sinh Nhật", "name_en": "Birthday Party"},
    "music": {"name": "Âm Nhạc", "name_en": "Music & Beats"},
    "sports": {"name": "Thể Thao", "name_en": "Sports & Energy"},
    "vehicle": {"name": "Phương Tiện", "name_en": "Vehicles & Cars"},
    "painting": {"name": "Hội Họa", "name_en": "Fine Art"},
    "portrait": {"name": "Chân Dung", "name_en": "Portraits"},
    "simple": {"name": "Đơn Giản", "name_en": "Simple & Easy"},
    "worldcup": {"name": "Bóng Đá", "name_en": "World Cup"},
    "halloween": {"name": "Halloween", "name_en": "Halloween"},
    "christmas": {"name": "Giáng Sinh", "name_en": "Christmas Holiday"},
    "holiday": {"name": "Lễ Hội", "name_en": "Holidays"},
    "people": {"name": "Con Người", "name_en": "People"},
    "fantasy": {"name": "Kỳ Ảo", "name_en": "Fantasy"},
    "jigsaw": {"name": "Ghép Hình", "name_en": "Jigsaw"},
    "pintu": {"name": "Tranh Ghép", "name_en": "Mosaic"},
    "town": {"name": "Thị Trấn", "name_en": "Pixel Town"},
    "bonus": {"name": "Phần Thưởng", "name_en": "Bonus Art"},
    "bonus_cn": {"name": "Phong Cách Cổ Trang", "name_en": "Ancient Style"},
    "challenge": {"name": "Thử Thách", "name_en": "Challenge"},
    "package": {"name": "Gói Chủ Đề", "name_en": "Art Packs"},
    "banner_v2": {"name": "Nổi Bật", "name_en": "Featured Banners"},
    "mystery": {"name": "Bí Ẩn", "name_en": "Mystery Art"},
    "task": {"name": "Nhiệm Vụ", "name_en": "Task Rewards"},
    "top": {"name": "Thịnh Hành", "name_en": "Top Trending"}
}


def build():
    os.makedirs(CAT_API_DIR, exist_ok=True)

    # 1. Đọc catalog lớn để lấy các ảnh phụ trợ ghép vào category
    catalog_path = os.path.join(PUBLIC_DIR, "imagesupdates_android_compressed.json")
    big_catalog_images = []
    if os.path.exists(catalog_path):
        with open(catalog_path, "r", encoding="utf-8") as f:
            big_catalog_images = json.load(f).get("images", [])

    # Index các ảnh trong catalog lớn theo tag
    tag_to_big_images = {}
    for img in big_catalog_images:
        for t in img.get("tags", []):
            t_clean = t.strip().lower()
            if not t_clean:
                continue
            if t_clean not in tag_to_big_images:
                tag_to_big_images[t_clean] = []
            tag_to_big_images[t_clean].append(img)

    categories_list = []
    seen_image_urls = set()

    # Quét tất cả các folder trong artworks/
    folders = sorted(os.listdir(ARTWORKS_DIR))
    for folder in folders:
        cat_dir = os.path.join(ARTWORKS_DIR, folder)
        if not os.path.isdir(cat_dir) or folder.startswith("."):
            continue

        meta = CATEGORY_META.get(folder, {
            "name": folder.replace("_", " ").title(),
            "name_en": folder.replace("_", " ").title()
        })

        category_items = []

        # A. Lấy tranh trực tiếp từ artworks/{folder}/
        files = sorted(os.listdir(cat_dir))
        for fname in files:
            if fname.lower().endswith((".png", ".gif")):
                img_id = f"{folder}_{fname.split('.')[0]}"
                url = f"{CDN_BASE}artworks/{folder}/{fname}"
                seen_image_urls.add(url)
                category_items.append({
                    "id": img_id,
                    "title": f"{meta['name']} {fname.split('.')[0]}",
                    "file_name": fname,
                    "url": url,
                    "thumbnail_url": url,
                    "category": folder,
                    "category_name": meta["name"],
                    "category_name_en": meta["name_en"],
                    "free": True if folder != "vip" else False,
                    "gif": fname.lower().endswith(".gif"),
                    "pixelCount": 1000
                })

        # B. Ghép thêm ảnh từ kho lớn có tag tương ứng (để có vô vàn ảnh load more)
        # Các tag tương đương
        tag_keys = [folder, folder.rstrip("s"), folder + "s"]
        added_from_big = 0
        for tk in tag_keys:
            if tk in tag_to_big_images:
                for b_img in tag_to_big_images[tk]:
                    b_id = b_img.get("id")
                    is_gif = b_img.get("gif", False) or b_img.get("contentType") == "gif"
                    ext = ".gif" if is_gif else ".png"
                    b_url = f"{CDN_BASE}images/{b_id}{ext}"
                    if b_url not in seen_image_urls:
                        seen_image_urls.add(b_url)
                        category_items.append({
                            "id": b_id,
                            "title": b_id.replace("_", " "),
                            "file_name": f"{b_id}{ext}",
                            "url": b_url,
                            "thumbnail_url": b_url,
                            "category": folder,
                            "category_name": meta["name"],
                            "category_name_en": meta["name_en"],
                            "free": b_img.get("free", True),
                            "gif": is_gif,
                            "pixelCount": b_img.get("pixelCount", 1000)
                        })
                        added_from_big += 1

        total_items = len(category_items)
        if total_items == 0:
            continue

        total_pages = math.ceil(total_items / PAGE_SIZE)
        icon_url = category_items[0]["url"]

        # Lưu thông tin Category vào danh sách tổng
        cat_info = {
            "id": folder,
            "folder": folder,
            "name": meta["name"],
            "name_en": meta["name_en"],
            "icon_url": icon_url,
            "total_items": total_items,
            "total_pages": total_pages,
            "first_page_url": f"{CDN_BASE}api/categories/{folder}/page_1.json"
        }
        categories_list.append(cat_info)

        # C. Sinh các file phân trang cho category này: page_1.json, page_2.json...
        cat_folder_out = os.path.join(CAT_API_DIR, folder)
        os.makedirs(cat_folder_out, exist_ok=True)

        for p in range(1, total_pages + 1):
            start = (p - 1) * PAGE_SIZE
            end = start + PAGE_SIZE
            p_items = category_items[start:end]

            has_more = p < total_pages
            next_url = f"{CDN_BASE}api/categories/{folder}/page_{p+1}.json" if has_more else None

            page_data = {
                "category": folder,
                "category_name": meta["name"],
                "category_name_en": meta["name_en"],
                "page": p,
                "limit": PAGE_SIZE,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_more": has_more,
                "next_page": p + 1 if has_more else None,
                "next_page_url": next_url,
                "items": p_items,       # chuẩn items
                "images": p_items      # hỗ trợ cả alias images cho tiện gọi
            }

            with open(os.path.join(cat_folder_out, f"page_{p}.json"), "w", encoding="utf-8") as f:
                json.dump(page_data, f, indent=2, ensure_ascii=False)

        print(f"[+] Category '{folder}' ({meta['name']}): {total_items} ảnh ({total_pages} trang)")

    # 2. Ghi file tổng categories.json
    categories_catalog = {
        "version": 2,
        "total_categories": len(categories_list),
        "categories": categories_list
    }

    # Ghi vào cả 2 nơi để app gọi đường dẫn nào cũng trúng
    with open(os.path.join(API_DIR, "categories.json"), "w", encoding="utf-8") as f:
        json.dump(categories_catalog, f, indent=2, ensure_ascii=False)

    with open(os.path.join(PUBLIC_DIR, "artworks", "categories.json"), "w", encoding="utf-8") as f:
        json.dump(categories_catalog, f, indent=2, ensure_ascii=False)

    print(f"\n[=== HOÀN TẤT ===] Đã tạo API cho {len(categories_list)} categories!")


if __name__ == "__main__":
    build()
