#!/usr/bin/env python3
import os
import sys
import zlib
import struct
import colorsys
import argparse
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
IMAGES_DIR = os.path.join(PUBLIC_DIR, "images")
ARTWORKS_DIR = os.path.join(PUBLIC_DIR, "artworks")


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    elif pb <= pc:
        return b
    else:
        return c


def transform_single_pixel(r, g, b, mode="hue", hue_shift=0.33, sat_mult=1.0, val_mult=1.0):
    """Xử lý màu của 1 pixel theo mode mong muốn"""
    # Không can thiệp màu đen tuyền / trắng tuyền của viền nét
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    h, l, s = colorsys.rgb_to_hls(rf, gf, bf)

    if l <= 0.05 or l >= 0.95 or s <= 0.05:
        return r, g, b

    if mode == "invert":
        return 255 - r, 255 - g, 255 - b
    elif mode == "pastel":
        s = min(1.0, s * 0.55)
        l = min(0.92, max(0.2, l * 1.3))
    elif mode == "neon":
        s = min(1.0, s * 1.6 + 0.15)
        l = min(0.85, max(0.15, l * 1.15))
    elif mode == "warm":
        h = (h * 0.4 + 0.03) % 1.0  # Tông đỏ, cam, vàng ấm
    elif mode == "cool":
        h = (h * 0.4 + 0.52) % 1.0  # Tông xanh biển, xanh lá mát
    elif mode == "cyberpunk":
        h = (h * 0.3 + 0.8) % 1.0   # Tông tím, hồng neon Cyberpunk
        s = min(1.0, s * 1.4)
    elif mode == "sunset":
        h = (h * 0.35 + 0.08) % 1.0 # Tông hoàng hôn cam tím
        l = min(0.9, l * 1.1)
    elif mode == "forest":
        h = (h * 0.3 + 0.3) % 1.0   # Tông xanh rêu, xanh lá rừng
    elif mode == "ocean":
        h = (h * 0.3 + 0.55) % 1.0  # Tông xanh ngọc bích, đại dương
    elif mode == "vintage":
        s = min(1.0, s * 0.65)
        l = min(0.9, l * 0.95 + 0.05)
    else:
        # Mặc định xoay góc màu (Hue shift)
        h = (h + hue_shift) % 1.0
        s = min(1.0, max(0.0, s * sat_mult))
        l = min(1.0, max(0.0, l * val_mult))

    nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
    return int(nr * 255), int(ng * 255), int(nb * 255)


def process_png(filepath, outpath, mode="hue", hue_shift=0.33, flip_h=False):
    """Xử lý ảnh PNG: hỗ trợ cả Palette-based (PLTE) và Truecolor RGBA"""
    try:
        with open(filepath, "rb") as f:
            data = f.read()

        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            return False

        pos = 8
        chunks = []
        has_plte = False
        width = height = bit_depth = color_type = None
        idat_parts = []

        while pos < len(data):
            length = struct.unpack(">I", data[pos:pos+4])[0]
            ctype = data[pos+4:pos+8]
            cdata = data[pos+8:pos+8+length]
            crc = data[pos+8+length:pos+12+length]
            pos += 12 + length

            if ctype == b"IHDR":
                width, height, bit_depth, color_type = struct.unpack(">IIBB", cdata[:10])
                chunks.append((ctype, cdata, crc))
            elif ctype == b"PLTE":
                has_plte = True
                # Đổi màu trực tiếp trên Palette PLTE (cực nhanh và bảo toàn 100% độ nét pixel)
                new_cdata = bytearray()
                for i in range(0, len(cdata), 3):
                    nr, ng, nb = transform_single_pixel(cdata[i], cdata[i+1], cdata[i+2], mode, hue_shift)
                    new_cdata.extend([nr, ng, nb])
                cdata = bytes(new_cdata)
                crc = struct.pack(">I", zlib.crc32(ctype + cdata) & 0xffffffff)
                chunks.append((ctype, cdata, crc))
            elif ctype == b"IDAT":
                idat_parts.append(cdata)
            elif ctype != b"IEND":
                chunks.append((ctype, cdata, crc))

        # Nếu là ảnh Indexed PLTE và không lật đối xứng, chỉ cần ghi lại PLTE mới
        if has_plte and not flip_h:
            out = bytearray(b"\x89PNG\r\n\x1a\n")
            for ct, cd, cr in chunks:
                out.extend(struct.pack(">I", len(cd)) + ct + cd + cr)
            for idat in idat_parts:
                out.extend(struct.pack(">I", len(idat)) + b"IDAT" + idat + struct.pack(">I", zlib.crc32(b"IDAT" + idat) & 0xffffffff))
            out.extend(struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xffffffff))
            with open(outpath, "wb") as f:
                f.write(out)
            return True

        # Nếu là Truecolor hoặc cần lật gương (Flip Horizontal):
        if color_type in (2, 6) and bit_depth == 8:
            bpp = 4 if color_type == 6 else 3
            stride = width * bpp
            raw = zlib.decompress(b"".join(idat_parts))
            unfiltered = bytearray()
            prior = bytearray(stride)
            raw_pos = 0

            for _ in range(height):
                ftype = raw[raw_pos]
                raw_pos += 1
                line = raw[raw_pos:raw_pos+stride]
                raw_pos += stride
                curr = bytearray(stride)
                for i in range(stride):
                    x = line[i]
                    a = curr[i-bpp] if i >= bpp else 0
                    b = prior[i]
                    c = prior[i-bpp] if i >= bpp else 0
                    if ftype == 0: v = x
                    elif ftype == 1: v = (x + a) & 0xff
                    elif ftype == 2: v = (x + b) & 0xff
                    elif ftype == 3: v = (x + ((a + b) >> 1)) & 0xff
                    elif ftype == 4: v = (x + paeth(a, b, c)) & 0xff
                    else: v = x
                    curr[i] = v
                prior = curr
                unfiltered.extend(curr)

            new_raw = bytearray()
            for y in range(height):
                row_pixels = []
                for x in range(width):
                    off = (y * width + x) * bpp
                    r, g, b = unfiltered[off], unfiltered[off+1], unfiltered[off+2]
                    a = unfiltered[off+3] if bpp == 4 else None

                    if a is None or a > 10:
                        nr, ng, nb = transform_single_pixel(r, g, b, mode, hue_shift)
                    else:
                        nr, ng, nb = r, g, b

                    if bpp == 4:
                        row_pixels.append([nr, ng, nb, a])
                    else:
                        row_pixels.append([nr, ng, nb])

                if flip_h:
                    row_pixels.reverse()

                new_raw.append(0)
                for px in row_pixels:
                    new_raw.extend(px)

            comp = zlib.compress(bytes(new_raw), 6)
            out = bytearray(b"\x89PNG\r\n\x1a\n")
            for ct, cd, cr in chunks:
                out.extend(struct.pack(">I", len(cd)) + ct + cd + cr)
            out.extend(struct.pack(">I", len(comp)) + b"IDAT" + comp + struct.pack(">I", zlib.crc32(b"IDAT" + comp) & 0xffffffff))
            out.extend(struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xffffffff))
            with open(outpath, "wb") as f:
                f.write(out)
            return True

        return False
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Tool đổi màu sắc, chống bản quyền cho kho tranh Pixel Art")
    parser.add_argument("--mode", choices=["hue", "pastel", "neon", "warm", "cool", "invert", "random"], default="random",
                        help="Phong cách đổi màu (mặc định: 'random' để mỗi tranh có một màu sắc ngẫu nhiên độc nhất)")
    parser.add_argument("--hue", type=float, default=0.33, help="Góc lệch màu (từ 0.0 đến 1.0, mặc định 0.33 ~ 120 độ)")
    parser.add_argument("--flip", action="store_true", help="Lật đối xứng gương (Horizontal Flip) toàn bộ ảnh")
    parser.add_argument("--flip-random", action="store_true", help="Ngẫu nhiên lật gương 50/50 cho từng ảnh")
    parser.add_argument("--preview", type=str, help="Chạy thử nghiệm trên 1 ảnh để xem trước kết quả")
    parser.add_argument("--target", choices=["all", "artworks", "images"], default="all", help="Thư mục muốn áp dụng")
    parser.add_argument("--dir", type=str, help="Đường dẫn thư mục tùy chọn muốn xử lý (vd: --dir /duong/dan/folder)")
    parser.add_argument("--workers", type=int, default=16, help="Số luồng xử lý song song")

    args = parser.parse_args()

    # Chế độ Preview 1 ảnh
    if args.preview:
        if not os.path.exists(args.preview):
            print(f"[!] Không tìm thấy file: {args.preview}")
            sys.exit(1)
        out_preview = "preview_transformed.png"
        h = random.random() if args.mode == "random" else args.hue
        m = random.choice(["pastel", "neon", "warm", "cool", "hue"]) if args.mode == "random" else args.mode
        ok = process_png(args.preview, out_preview, mode=m, hue_shift=h, flip_h=args.flip)
        if ok:
            print(f"[+] Đã tạo ảnh xem thử thành công: {os.path.abspath(out_preview)}")
            print("[*] Đang mở ảnh preview...")
            os.system(f"open {out_preview}")
        else:
            print("[!] Không xử lý được file xem thử.")
        return

    # Chế độ áp dụng hàng loạt
    targets = []
    if args.dir:
        if not os.path.exists(args.dir):
            print(f"[!] Thư mục không tồn tại: {args.dir}")
            sys.exit(1)
        for root, _, files in os.walk(args.dir):
            for f in files:
                if f.lower().endswith(".png"):
                    targets.append(os.path.join(root, f))
    else:
        if args.target in ("all", "images"):
            for f in os.listdir(IMAGES_DIR):
                if f.lower().endswith(".png"):
                    targets.append(os.path.join(IMAGES_DIR, f))

        if args.target in ("all", "artworks"):
            for root, _, files in os.walk(ARTWORKS_DIR):
                for f in files:
                    if f.lower().endswith(".png"):
                        targets.append(os.path.join(root, f))

    total = len(targets)
    print(f"[*] Bắt đầu xử lý {total} ảnh...")
    print(f"[*] Chế độ: mode={args.mode}, flip_horizontal={args.flip}, workers={args.workers}")

    success = 0
    failed = 0

    ALL_MODES = ["pastel", "neon", "warm", "cool", "cyberpunk", "sunset", "forest", "ocean", "vintage", "hue"]

    def worker(path):
        h = random.uniform(0.05, 0.95) if args.mode == "random" else args.hue
        m = random.choice(ALL_MODES) if args.mode == "random" else args.mode
        flip_this = random.choice([True, False]) if args.flip_random else args.flip
        return process_png(path, path, mode=m, hue_shift=h, flip_h=flip_this)

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(worker, p): p for p in targets}
        done = 0
        for f in as_completed(futures):
            done += 1
            if f.result():
                success += 1
            else:
                failed += 1
            if done % 500 == 0 or done == total:
                percent = (done / total) * 100
                print(f"\rTiến độ: {done}/{total} ({percent:.1f}%) | Thành công: {success} | Bỏ qua: {failed}", end="", flush=True)

    print("\n\n[=== HOÀN TẤT ĐỔI MÀU ===]")
    print(f"- Thành công: {success}")
    print(f"- Bỏ qua: {failed}")

    # Tự động cập nhật lại API và nén lại catalog
    print("\n[*] Đang tái tạo lại toàn bộ API và nén lại Catalog...")
    os.system(f"python3 {os.path.join(BASE_DIR, 'tools', 'shuffle_and_scramble.py')}")


if __name__ == "__main__":
    main()
