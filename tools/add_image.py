#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
from build_catalog import build_catalog, get_image_dimensions

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
IMAGES_DIR = os.path.join(PUBLIC_DIR, "images")


def main():
    parser = argparse.ArgumentParser(description="Thêm ảnh/gif mới vào thư mục và tự động cập nhật catalog JSON")
    parser.add_argument("file_path", help="Đường dẫn tới file ảnh PNG hoặc GIF muốn thêm")
    parser.add_argument("--id", help="ID của tranh (mặc định lấy tên file không đuôi)")
    parser.add_argument("--tags", default="Popular", help="Danh sách tag, phân tách bằng dấu phẩy (vd: 'Animals,Cute')")
    parser.add_argument("--vip", action="store_true", help="Nếu đặt cờ này, ảnh sẽ yêu cầu tài khoản VIP (free = False)")

    args = parser.parse_args()

    src_file = os.path.abspath(args.file_path)
    if not os.path.exists(src_file):
        print(f"[!] File không tồn tại: {src_file}")
        sys.exit(1)

    _, ext = os.path.splitext(src_file)
    ext_lower = ext.lower()
    if ext_lower not in [".png", ".gif"]:
        print("[!] Chỉ hỗ trợ định dạng .png hoặc .gif")
        sys.exit(1)

    img_id = args.id if args.id else os.path.splitext(os.path.basename(src_file))[0]
    dest_filename = f"{img_id}{ext_lower}"
    dest_path = os.path.join(IMAGES_DIR, dest_filename)

    # Copy file vào public/images/
    shutil.copy2(src_file, dest_path)
    print(f"[+] Đã thêm file vào: {dest_path}")

    # Chạy lại build_catalog để cập nhật file json & json.gz
    build_catalog()
    print(f"[+] Hoàn tất thêm tranh: {img_id} (Tags: {args.tags}, Free: {not args.vip})")


if __name__ == "__main__":
    main()
