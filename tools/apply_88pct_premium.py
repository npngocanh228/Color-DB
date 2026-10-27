#!/usr/bin/env python3
"""
apply_88pct_premium.py
Cập nhật toàn bộ hệ thống tranh sang tỉ lệ 88% Premium (VIP) và 12% Free.
Áp dụng:
1. Category APIs (public/api/categories/*/*.json)
2. All Feed APIs (public/api/all/*.json)
3. Tag Feed APIs (public/api/tag/*/*.json)
4. Catalog CDN (public/imagesupdates_android_compressed.json & .gz)
5. Root Catalog (catalog.json)
"""

import os
import glob
import json
import gzip
import random
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)

TARGET_PREMIUM_RATIO = 0.88  # 88%
SEED = 20261027
rng = random.Random(SEED)


def run():
    print("=" * 65)
    print("🚀 BẮT ĐẦU CẬP NHẬT TỈ LỆ 88% TRANH PREMIUM (VIP) & 12% FREE")
    print("=" * 65)

    # Dictionary lưu trữ trạng thái cố định của từng image_id để đảm bảo đồng bộ
    image_is_free = {}

    # -------------------------------------------------------------
    # 1. XỬ LÝ CATEGORY APIS
    # -------------------------------------------------------------
    cat_dirs = sorted(glob.glob(os.path.join(BASE_DIR, "public", "api", "categories", "*")))
    total_cat_items = 0
    cat_paid_count = 0
    cat_free_count = 0

    print("\n[*] 1. Đang cập nhật Categories APIs (31 danh mục)...")
    for cdir in cat_dirs:
        if not os.path.isdir(cdir):
            continue
        cname = os.path.basename(cdir)
        page_files = sorted(
            glob.glob(os.path.join(cdir, "page_*.json")),
            key=lambda x: int(re.search(r"page_(\d+)\.json", x).group(1))
        )

        for p_idx, pfile in enumerate(page_files, start=1):
            with open(pfile, "r", encoding="utf-8") as f:
                data = json.load(f)

            items = data.get("items", [])
            n_items = len(items)
            if n_items == 0:
                continue

            if cname == "vip":
                # Danh mục VIP: 100% là Premium
                free_indices = set()
            else:
                # Tỉ lệ 88% Premium -> 12% Free (~3 đến 4 tranh Free mỗi trang 30 tranh)
                num_free = max(1, round(n_items * (1.0 - TARGET_PREMIUM_RATIO)))
                step = n_items / num_free
                free_indices = {int(i * step) for i in range(num_free)}
                # Luôn đảm bảo vị trí 0 là Free trên Page 1 cho trải nghiệm mở app tốt
                if p_idx == 1:
                    free_indices.add(0)
                    while len(free_indices) > num_free and len(free_indices) > 1:
                        free_indices.remove(max(free_indices))

            for idx, item in enumerate(items):
                img_id = item.get("id")
                is_free = (idx in free_indices)

                # Ghi nhận trạng thái đồng bộ
                if img_id:
                    image_is_free[img_id] = is_free

                item["free"] = is_free
                total_cat_items += 1
                if is_free:
                    cat_free_count += 1
                else:
                    cat_paid_count += 1

            if "images" in data:
                data["images"] = items

            with open(pfile, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    pct_cat_paid = (cat_paid_count / total_cat_items * 100) if total_cat_items else 0
    print(f"[+] Categories API hoàn tất: {total_cat_items} items | Free: {cat_free_count} | Paid: {cat_paid_count} ({pct_cat_paid:.2f}% Premium)")

    # -------------------------------------------------------------
    # 2. XỬ LÝ ALL FEED APIS (public/api/all/*.json)
    # -------------------------------------------------------------
    all_files = sorted(
        glob.glob(os.path.join(BASE_DIR, "public", "api", "all", "page_*.json")),
        key=lambda x: int(re.search(r"page_(\d+)\.json", x).group(1))
    )
    print(f"\n[*] 2. Đang cập nhật All Feed APIs ({len(all_files)} trang)...")
    all_total = 0
    all_paid = 0

    for p_idx, pfile in enumerate(all_files, start=1):
        with open(pfile, "r", encoding="utf-8") as f:
            data = json.load(f)

        items = data.get("items", [])
        n_items = len(items)
        if n_items == 0:
            continue

        num_free = max(1, round(n_items * (1.0 - TARGET_PREMIUM_RATIO)))
        step = n_items / num_free
        default_free_indices = {int(i * step) for i in range(num_free)}
        if p_idx == 1:
            default_free_indices.add(0)
            while len(default_free_indices) > num_free and len(default_free_indices) > 1:
                default_free_indices.remove(max(default_free_indices))

        for idx, item in enumerate(items):
            img_id = item.get("id")
            if img_id in image_is_free:
                is_free = image_is_free[img_id]
            else:
                is_free = (idx in default_free_indices)
                if img_id:
                    image_is_free[img_id] = is_free

            item["free"] = is_free
            all_total += 1
            if not is_free:
                all_paid += 1

        if "images" in data:
            data["images"] = items

        with open(pfile, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    pct_all_paid = (all_paid / all_total * 100) if all_total else 0
    print(f"[+] All Feed hoàn tất: {all_total} items | Paid: {all_paid} ({pct_all_paid:.2f}% Premium)")

    # -------------------------------------------------------------
    # 3. XỬ LÝ TAG APIS (public/api/tag/*/*.json)
    # -------------------------------------------------------------
    tag_files = glob.glob(os.path.join(BASE_DIR, "public", "api", "tag", "*", "page_*.json"))
    print(f"\n[*] 3. Đang cập nhật Tag APIs ({len(tag_files)} file)...")
    tag_total = 0
    tag_paid = 0

    for pfile in tag_files:
        with open(pfile, "r", encoding="utf-8") as f:
            data = json.load(f)

        is_images_key = "images" in data
        items = data.get("images") if is_images_key else data.get("items", [])
        n_items = len(items)
        if n_items == 0:
            continue

        num_free = max(1, round(n_items * (1.0 - TARGET_PREMIUM_RATIO)))
        step = n_items / num_free
        default_free_indices = {int(i * step) for i in range(num_free)}

        for idx, item in enumerate(items):
            img_id = item.get("id")
            if img_id in image_is_free:
                is_free = image_is_free[img_id]
            else:
                is_free = (idx in default_free_indices)
                if img_id:
                    image_is_free[img_id] = is_free

            item["free"] = is_free
            tag_total += 1
            if not is_free:
                tag_paid += 1

        if is_images_key:
            data["images"] = items
        if "items" in data:
            data["items"] = items

        with open(pfile, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    pct_tag_paid = (tag_paid / tag_total * 100) if tag_total else 0
    print(f"[+] Tag APIs hoàn tất: {tag_total} items | Paid: {tag_paid} ({pct_tag_paid:.2f}% Premium)")

    # -------------------------------------------------------------
    # 4. XỬ LÝ CATALOG CDN (imagesupdates_android_compressed.json & .gz)
    # -------------------------------------------------------------
    catalog_path = os.path.join(BASE_DIR, "public", "imagesupdates_android_compressed.json")
    catalog_gz = os.path.join(BASE_DIR, "public", "imagesupdates_android_compressed.json.gz")
    print("\n[*] 4. Đang cập nhật Catalog CDN nén...")
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    images = catalog.get("images", [])
    total_imgs = len(images)

    # Tính toán chính xác số lượng Free cần có: 12% của tổng
    target_total_free = round(total_imgs * (1.0 - TARGET_PREMIUM_RATIO))

    fixed_free = []
    unassigned = []
    for img in images:
        img_id = img.get("id")
        if img_id in image_is_free:
            if image_is_free[img_id]:
                fixed_free.append(img)
        else:
            unassigned.append(img)

    remaining_free_needed = max(0, target_total_free - len(fixed_free))
    rng.shuffle(unassigned)
    new_free_set = set(img.get("id") for img in unassigned[:remaining_free_needed])

    catlg_paid = 0
    catlg_free = 0
    for img in images:
        img_id = img.get("id")
        if img_id in image_is_free:
            is_free = image_is_free[img_id]
        elif img_id in new_free_set:
            is_free = True
            image_is_free[img_id] = True
        else:
            is_free = False
            image_is_free[img_id] = False

        img["free"] = "true" if is_free else "false"
        if is_free:
            catlg_free += 1
        else:
            catlg_paid += 1

    catalog["images"] = images
    json_bytes = json.dumps(catalog, indent=2, ensure_ascii=False).encode("utf-8")
    with open(catalog_path, "wb") as f:
        f.write(json_bytes)
    with open(catalog_gz, "wb") as f:
        f.write(gzip.compress(json_bytes))

    pct_catlg_paid = (catlg_paid / total_imgs * 100) if total_imgs else 0
    print(f"[+] Catalog CDN hoàn tất: {total_imgs} images | Free: {catlg_free} | Paid: {catlg_paid} ({pct_catlg_paid:.2f}% Premium)")

    # -------------------------------------------------------------
    # 5. XỬ LÝ ROOT CATALOG (catalog.json)
    # -------------------------------------------------------------
    root_catalog_path = os.path.join(ROOT_DIR, "catalog.json")
    if os.path.exists(root_catalog_path):
        print("\n[*] 5. Đang cập nhật Root Catalog (catalog.json)...")
        with open(root_catalog_path, "r", encoding="utf-8") as f:
            root_catalog = json.load(f)

        root_images = root_catalog.get("images", [])
        total_root = len(root_images)
        target_root_free = round(total_root * (1.0 - TARGET_PREMIUM_RATIO))

        root_fixed_free = []
        root_unassigned = []
        for img in root_images:
            img_id = img.get("id")
            if img_id in image_is_free and image_is_free[img_id]:
                root_fixed_free.append(img)
            elif img_id not in image_is_free:
                root_unassigned.append(img)

        needed = max(0, target_root_free - len(root_fixed_free))
        rng.shuffle(root_unassigned)
        extra_free_set = set(img.get("id") for img in root_unassigned[:needed])

        root_paid = 0
        root_free = 0
        for img in root_images:
            img_id = img.get("id")
            if img_id in image_is_free:
                is_free = image_is_free[img_id]
            elif img_id in extra_free_set:
                is_free = True
                image_is_free[img_id] = True
            else:
                is_free = False
                image_is_free[img_id] = False

            img["free"] = "true" if is_free else "false"
            if is_free:
                root_free += 1
            else:
                root_paid += 1

        root_catalog["images"] = root_images
        with open(root_catalog_path, "w", encoding="utf-8") as f:
            json.dump(root_catalog, f, indent=2, ensure_ascii=False)

        pct_root_paid = (root_paid / total_root * 100) if total_root else 0
        print(f"[+] Root Catalog hoàn tất: {total_root} images | Free: {root_free} | Paid: {root_paid} ({pct_root_paid:.2f}% Premium)")

    print("\n" + "=" * 65)
    print("🎉 TẤT CẢ DỮ LIỆU ĐÃ ĐƯỢC CẬP NHẬT CHUẨN XÁC TỈ LỆ 88% PREMIUM!")
    print("=" * 65)


if __name__ == "__main__":
    run()
