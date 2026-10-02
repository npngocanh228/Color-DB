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

    # Đẩy page 2, 5, 10 lên đầu (vị trí 1, 2, 3)
    # Page 3 chuyển hẳn xuống trang cuối cùng (trang 80)
    # Các trang còn lại nối tiếp: [1, 4, 6, 7, 8, 9, 11, ...]
    middle_pages = [p for p in range(1, TOTAL_PAGES + 1) if p not in (2, 5, 10, 3)]
    new_page_order = [2, 5, 10] + middle_pages + [3]

    assert len(new_page_order) == TOTAL_PAGES, f"Tổng số trang {len(new_page_order)} != {TOTAL_PAGES}"
    assert set(new_page_order) == set(range(1, TOTAL_PAGES + 1)), "Thiếu hoặc thừa trang trong danh sách sắp xếp!"

    print(f"[*] Thứ tự trang mới: 5 trang đầu = {new_page_order[:5]} ... Trang cuối = {new_page_order[-1]}")

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

    print("[+] Thành công! Đã đẩy Page 2, 5, 10 lên đầu và chuyển Page 3 xuống cuối cùng!")
    print(f"[+] Tổng số tranh: {total_items}, Tổng số trang: {TOTAL_PAGES}")
    first_p1 = new_pages_items[1][0]
    first_p2 = new_pages_items[2][0]
    first_p3 = new_pages_items[3][0]
    first_p80 = new_pages_items[80][0]
    print(f"[+] Trang 1 mới (cũ: Page 2): {first_p1['id']} ({first_p1['title']})")
    print(f"[+] Trang 2 mới (cũ: Page 5): {first_p2['id']} ({first_p2['title']})")
    print(f"[+] Trang 3 mới (cũ: Page 10): {first_p3['id']} ({first_p3['title']})")
    print(f"[+] Trang 80 mới (cũ: Page 3): {first_p80['id']} ({first_p80['title']})")


if __name__ == "__main__":
    run()
