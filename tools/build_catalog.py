#!/usr/bin/env python3
import os
import sys
import json
import gzip
import struct
from datetime import datetime

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
IMAGES_DIR = os.path.join(PUBLIC_DIR, "images")
CATALOG_JSON = os.path.join(PUBLIC_DIR, "imagesupdates_android_compressed.json")
CATALOG_GZ = os.path.join(PUBLIC_DIR, "imagesupdates_android_compressed.json.gz")


def get_image_dimensions(file_path):
    """Lấy kích thước ảnh (width, height) thuần Python không cần cài PIL/Pillow"""
    with open(file_path, "rb") as f:
        head = f.read(32)

    # PNG format
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        width, height = struct.unpack(">II", head[16:24])
        return width, height

    # GIF format
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        width, height = struct.unpack("<HH", head[6:10])
        return width, height

    return 30, 30  # Mặc định nếu không đọc được


def build_catalog():
    if not os.path.exists(IMAGES_DIR):
        print(f"[!] Thư mục không tồn tại: {IMAGES_DIR}")
        return

    # Nếu đã có file json cũ, giữ lại metadata tùy chỉnh (như tags, free/vip)
    existing_meta = {}
    if os.path.exists(CATALOG_JSON):
        try:
            with open(CATALOG_JSON, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for item in old_data.get("images", []):
                    existing_meta[item["id"]] = item
        except Exception as e:
            print(f"[!] Không đọc được file cũ: {e}")

    images_list = []
    files = sorted(os.listdir(IMAGES_DIR))

    for fname in files:
        if fname.startswith("."):
            continue

        name, ext = os.path.splitext(fname)
        ext_lower = ext.lower()

        if ext_lower not in [".png", ".gif"]:
            continue

        full_path = os.path.join(IMAGES_DIR, fname)
        is_gif = ext_lower == ".gif"

        # Nếu đã có cấu hình cũ thì giữ lại
        if name in existing_meta:
            item = existing_meta[name]
        else:
            w, h = get_image_dimensions(full_path)
            pixel_count = w * h
            now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            # Gán tag mẫu dựa theo tên
            tags = ["Basic"]
            if is_gif:
                tags.append("Animated")
            if "animal" in name.lower() or any(a in name.lower() for a in ["frog", "pig", "duck", "boxer", "hamster"]):
                tags.append("Animals")
            if any(f in name.lower() for f in ["cake", "strawberry", "truffles", "mug"]):
                tags.append("Food")

            item = {
                "id": name,
                "free": True,
                "gif": is_gif,
                "pixelCount": pixel_count,
                "release_date": now_str,
                "tags": tags
            }

        images_list.append(item)

    catalog_data = {
        "json_id": datetime.utcnow().strftime("v_%Y%m%d_%H%M%S"),
        "images": images_list
    }

    # 1. Ghi file JSON thường
    json_bytes = json.dumps(catalog_data, indent=2, ensure_ascii=False).encode("utf-8")
    with open(CATALOG_JSON, "wb") as f:
        f.write(json_bytes)
    print(f"[+] Đã tạo file: {CATALOG_JSON} ({len(images_list)} ảnh)")

    # 2. Ghi file JSON nén gzip (File mà Android app gọi tải về)
    gz_bytes = gzip.compress(json_bytes)
    with open(CATALOG_GZ, "wb") as f:
        f.write(gz_bytes)
    print(f"[+] Đã tạo file nén Gzip: {CATALOG_GZ} ({len(gz_bytes)} bytes)")


if __name__ == "__main__":
    build_catalog()
