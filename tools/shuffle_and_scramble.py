#!/usr/bin/env python3
import os
import json
import random
import math
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
ARTWORKS_DIR = os.path.join(PUBLIC_DIR, "artworks")
IMAGES_DIR = os.path.join(PUBLIC_DIR, "images")
API_DIR = os.path.join(PUBLIC_DIR, "api")
CAT_API_DIR = os.path.join(API_DIR, "categories")
ALL_API_DIR = os.path.join(API_DIR, "all")
CATALOG_PATH = os.path.join(PUBLIC_DIR, "imagesupdates_android_compressed.json")
CATALOG_GZ = os.path.join(PUBLIC_DIR, "imagesupdates_android_compressed.json.gz")

CDN_BASE = "https://npngocanh228.github.io/Color-DB/public/"
PAGE_SIZE = 30

# Dùng seed cố định để thứ tự xáo trộn luôn ổn định sau mỗi lần chạy (không bị nhảy loạn giữa các lần push)
SEED = 20260916
rng = random.Random(SEED)

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


def scramble_title(img_id, category_name):
    """Tạo title ngẫu nhiên nghệ thuật, tránh lộ thứ tự 01, 02..."""
    h = hashlib.md5(img_id.encode('utf-8')).hexdigest()[:4].upper()
    return f"{category_name} #{h}"


def run():
    print("[*] 1. Đang đọc catalog tổng...")
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    raw_images = catalog.get("images", [])
    print(f"[+] Tổng số tranh hiện có: {len(raw_images)}")

    # Xáo trộn hoàn toàn mảng tranh trong catalog tổng
    print("[*] Đang trộn ngẫu nhiên toàn bộ 21.000+ tranh trong catalog...")
    rng.shuffle(raw_images)

    catalog["images"] = raw_images
    catalog["json_id"] = f"v_scrambled_{SEED}"

    # Lưu lại catalog đã trộn
    import gzip
    json_bytes = json.dumps(catalog, indent=2, ensure_ascii=False).encode("utf-8")
    with open(CATALOG_PATH, "wb") as f:
        f.write(json_bytes)
    with open(CATALOG_GZ, "wb") as f:
        f.write(gzip.compress(json_bytes))
    print("[+] Đã cập nhật và nén lại catalog.json.gz!")

    # Index các ảnh trong catalog lớn theo tag
    tag_to_big_images = {}
    for img in raw_images:
        for t in img.get("tags", []):
            t_clean = t.strip().lower()
            if not t_clean:
                continue
            if t_clean not in tag_to_big_images:
                tag_to_big_images[t_clean] = []
            tag_to_big_images[t_clean].append(img)

    # 2. Xáo trộn và phân trang cho Category-based API
    print("[*] 2. Đang xáo trộn và tái phân trang theo Categories...")
    os.makedirs(CAT_API_DIR, exist_ok=True)
    categories_list = []
    seen_urls_global = set()

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

        # A. Ảnh từ artworks/{folder}/ (772 tranh của PixelArtPaint)
        files = sorted(os.listdir(cat_dir))
        for fname in files:
            if fname.lower().endswith((".png", ".gif")):
                img_id = f"{folder}_{fname.split('.')[0]}"
                url = f"{CDN_BASE}artworks/{folder}/{fname}"
                category_items.append({
                    "id": img_id,
                    "title": scramble_title(img_id, meta["name"]),
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

        # B. Ảnh từ kho tranh lớn (ghép chung vào)
        tag_keys = [folder, folder.rstrip("s"), folder + "s"]
        seen_in_cat = {item["url"] for item in category_items}
        for tk in tag_keys:
            if tk in tag_to_big_images:
                for b_img in tag_to_big_images[tk]:
                    b_id = b_img.get("id")
                    is_gif = b_img.get("gif", False) or b_img.get("contentType") == "gif"
                    ext = ".gif" if is_gif else ".png"
                    b_url = f"{CDN_BASE}images/{b_id}{ext}"
                    if b_url not in seen_in_cat:
                        seen_in_cat.add(b_url)
                        category_items.append({
                            "id": b_id,
                            "title": scramble_title(b_id, meta["name"]),
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

        if not category_items:
            continue

        # 🔥 XÁO TRỘN NGẪU NHIÊN TOÀN BỘ TRANH TRONG CATEGORY NÀY 🔥
        # (772 tranh gốc bị phân tán ngẫu nhiên vào hàng nghìn tranh khác, không còn thứ tự 01, 02...)
        rng.shuffle(category_items)

        total_items = len(category_items)
        total_pages = math.ceil(total_items / PAGE_SIZE)
        icon_url = category_items[0]["url"]

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

        # Ghi các file trang
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
                "items": p_items,
                "images": p_items
            }

            with open(os.path.join(cat_folder_out, f"page_{p}.json"), "w", encoding="utf-8") as f:
                json.dump(page_data, f, indent=2, ensure_ascii=False)

    # Đảo cả thứ tự hiển thị các danh mục nếu muốn (hoặc giữ theo độ phổ biến)
    categories_catalog = {
        "version": 2,
        "total_categories": len(categories_list),
        "categories": categories_list
    }
    with open(os.path.join(API_DIR, "categories.json"), "w", encoding="utf-8") as f:
        json.dump(categories_catalog, f, indent=2, ensure_ascii=False)
    with open(os.path.join(PUBLIC_DIR, "artworks", "categories.json"), "w", encoding="utf-8") as f:
        json.dump(categories_catalog, f, indent=2, ensure_ascii=False)

    # 3. Phân trang ngẫu nhiên cho ALL API
    print("[*] 3. Đang xáo trộn API all/page_N.json...")
    all_items = []
    existing_files = set(os.listdir(IMAGES_DIR))
    for img in raw_images:
        img_id = img.get("id")
        is_gif = img.get("gif", False) or img.get("contentType") == "gif"
        ext = ".gif" if is_gif else ".png"
        fname = f"{img_id}{ext}"
        if fname in existing_files:
            all_items.append({
                "id": img_id,
                "title": f"Artwork #{hashlib.md5(img_id.encode('utf-8')).hexdigest()[:4].upper()}",
                "url": f"{CDN_BASE}images/{fname}",
                "thumbnail_url": f"{CDN_BASE}images/{fname}",
                "free": img.get("free", True),
                "gif": is_gif,
                "pixelCount": img.get("pixelCount", 1000),
                "tags": img.get("tags", [])
            })

    # Shuffle all
    rng.shuffle(all_items)
    os.makedirs(ALL_API_DIR, exist_ok=True)
    total_all_pages = math.ceil(len(all_items) / PAGE_SIZE)
    for p in range(1, total_all_pages + 1):
        start = (p - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        p_items = all_items[start:end]
        has_more = p < total_all_pages
        next_url = f"{CDN_BASE}api/all/page_{p+1}.json" if has_more else None
        page_data = {
            "category": "all",
            "page": p,
            "limit": PAGE_SIZE,
            "total_items": len(all_items),
            "total_pages": total_all_pages,
            "has_more": has_more,
            "next_page": p + 1 if has_more else None,
            "next_page_url": next_url,
            "items": p_items,
            "images": p_items
        }
        with open(os.path.join(ALL_API_DIR, f"page_{p}.json"), "w", encoding="utf-8") as f:
            json.dump(page_data, f, indent=2, ensure_ascii=False)

    print("[=== HOÀN TẤT XÁO TRỘN & LÀM RỐI DATA 100% ===]")


if __name__ == "__main__":
    run()
