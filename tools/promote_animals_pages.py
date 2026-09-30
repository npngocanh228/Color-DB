#!/usr/bin/env python3
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT_DIR = os.path.join(BASE_DIR, "public", "api", "categories", "animals")
CDN_BASE = "https://npngocanh228.github.io/Color-DB/public/"

TOTAL_PAGES = 80
PAGE_SIZE = 30


def run():
    print("[*] Đang đọc toàn bộ 80 trang của categories animals...")
    pages_data = {}
    for p in range(1, TOTAL_PAGES + 1):
        file_path = os.path.join(CAT_DIR, f"page_{p}.json")
        with open(file_path, "r", encoding="utf-8") as f:
            pages_data[p] = json.load(f)

    # Đẩy page 2 lên vị trí 1, page 50 lên vị trí 2
    # Các trang còn lại nối tiếp: page 1 -> trang 3, page 3 -> trang 4, ..., page 49 -> trang 50, page 51 -> trang 51...
    new_page_order = [2, 50, 1] + [p for p in range(3, TOTAL_PAGES + 1) if p != 50]

    assert len(new_page_order) == TOTAL_PAGES
    assert set(new_page_order) == set(range(1, TOTAL_PAGES + 1))

    # Re-assemble items
    new_pages_items = {}
    for new_idx, old_p in enumerate(new_page_order, start=1):
        new_pages_items[new_idx] = pages_data[old_p]["items"]

    total_items = sum(len(items) for items in new_pages_items.values())

    print("[*] Đang ghi lại các file page_1.json đến page_80.json...")
    for p in range(1, TOTAL_PAGES + 1):
        p_items = new_pages_items[p]
        has_more = p < TOTAL_PAGES
        next_url = f"{CDN_BASE}api/categories/animals/page_{p+1}.json" if has_more else None

        page_data = {
            "category": "animals",
            "category_name": "Động Vật",
            "category_name_en": "Animals",
            "page": p,
            "limit": PAGE_SIZE,
            "total_items": total_items,
            "total_pages": TOTAL_PAGES,
            "has_more": has_more,
            "next_page": p + 1 if has_more else None,
            "next_page_url": next_url,
            "items": p_items,
            "images": p_items
        }

        file_path = os.path.join(CAT_DIR, f"page_{p}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(page_data, f, indent=2, ensure_ascii=False)

    # Cập nhật icon_url trong categories.json
    new_first_icon = new_pages_items[1][0]["url"]
    for cat_file in [
        os.path.join(BASE_DIR, "public", "api", "categories.json"),
        os.path.join(BASE_DIR, "public", "artworks", "categories.json")
    ]:
        if os.path.exists(cat_file):
            with open(cat_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for cat in data.get("categories", []):
                if cat.get("id") == "animals":
                    cat["icon_url"] = new_first_icon
            with open(cat_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[+] Thành công! Đã đẩy page 2 lên vị trí 1 và page 50 lên vị trí 2!")
    print(f"[+] Tổng số tranh: {total_items}, Tổng số trang: {TOTAL_PAGES}")
    print(f"[+] Trang 1 hiện bắt đầu bằng: {new_pages_items[1][0]['id']} ({new_pages_items[1][0]['title']})")
    print(f"[+] Trang 2 hiện bắt đầu bằng: {new_pages_items[2][0]['id']} ({new_pages_items[2][0]['title']})")
    print(f"[+] Trang 3 hiện bắt đầu bằng: {new_pages_items[3][0]['id']} ({new_pages_items[3][0]['title']})")


if __name__ == "__main__":
    run()
