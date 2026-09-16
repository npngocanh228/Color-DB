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

THEMES = {
    "fire": [(30, 8, 8), (175, 20, 20), (230, 70, 15), (255, 145, 20), (255, 220, 80), (255, 250, 210)],
    "ice": [(8, 18, 42), (30, 70, 135), (65, 135, 215), (130, 198, 245), (210, 238, 255), (255, 255, 255)],
    "cyberpunk": [(25, 12, 45), (120, 18, 150), (230, 15, 115), (45, 185, 245), (255, 225, 35), (255, 255, 255)],
    "golden": [(35, 25, 8), (115, 75, 20), (190, 130, 35), (245, 185, 55), (255, 225, 120), (255, 250, 215)],
    "toxic": [(12, 28, 12), (35, 95, 30), (85, 180, 45), (160, 235, 65), (225, 255, 150), (255, 255, 255)],
    "synthwave": [(35, 12, 55), (95, 20, 100), (180, 40, 125), (245, 95, 85), (255, 190, 100), (255, 245, 210)],
    "gameboy": [(15, 56, 15), (48, 98, 48), (139, 172, 15), (155, 188, 15)],
    "pastel_sweet": [(50, 40, 60), (140, 100, 160), (190, 140, 200), (160, 200, 230), (240, 190, 220), (255, 245, 250)],
    "gothic": [(15, 15, 20), (50, 45, 60), (90, 80, 105), (140, 125, 160), (200, 190, 215), (245, 240, 255)],
}

THEME_NAMES = list(THEMES.keys())
LEGACY_MODES = ["drastic", "shuffle", "pastel", "neon", "warm", "cool", "cyberpunk_hue", "sunset", "forest", "ocean", "vintage", "invert", "hue"]
ALL_CHOICES = THEME_NAMES + LEGACY_MODES + ["random"]


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    elif pb <= pc:
        return b
    else:
        return c


def remap_palette_colors(cols, theme_colors, tint_outline=False):
    cols = list(cols)
    indexed = []
    for i, (r, g, b) in enumerate(cols):
        if r < 18 and g < 18 and b < 18:
            if tint_outline:
                cols[i] = theme_colors[0]
            continue
        if r > 240 and g > 240 and b > 240:
            continue
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        indexed.append((lum, i))

    if indexed:
        indexed.sort(key=lambda x: x[0])
        N = len(indexed)
        M = len(theme_colors)
        start_c = 1 if len(theme_colors) > 3 else 0
        end_c = M - 1
        for rank, (lum, orig_idx) in enumerate(indexed):
            ratio = rank / max(1, N - 1)
            t_idx = int(start_c + ratio * (end_c - start_c))
            cols[orig_idx] = theme_colors[t_idx]
    return cols


def shuffle_palette_colors(cols):
    cols = list(cols)
    indices = [i for i, (r, g, b) in enumerate(cols) if not ((r < 18 and g < 18 and b < 18) or (r > 240 and g > 240 and b > 240))]
    if len(indices) >= 2:
        shift = random.randint(1, len(indices) - 1)
        shifted_indices = indices[shift:] + indices[:shift]
        temp = [cols[i] for i in shifted_indices]
        for idx, col in zip(indices, temp):
            cols[idx] = col
    return cols


def transform_single_pixel(r, g, b, mode="hue", hue_shift=0.33, sat_mult=1.0, val_mult=1.0):
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    h, l, s = colorsys.rgb_to_hls(rf, gf, bf)

    if l <= 0.05 or l >= 0.95 or s <= 0.05:
        return r, g, b

    if mode == "invert":
        return 255 - r, 255 - g, 255 - b
    elif mode == "drastic":
        h = (h + 0.5) % 1.0
        s = min(1.0, s * 1.35 + 0.1)
    elif mode == "pastel":
        s = min(1.0, s * 0.55)
        l = min(0.92, max(0.2, l * 1.3))
    elif mode == "neon":
        s = min(1.0, s * 1.6 + 0.15)
        l = min(0.85, max(0.15, l * 1.15))
    elif mode == "warm":
        h = (h * 0.4 + 0.03) % 1.0
    elif mode == "cool":
        h = (h * 0.4 + 0.52) % 1.0
    elif mode == "cyberpunk_hue":
        h = (h * 0.3 + 0.8) % 1.0
        s = min(1.0, s * 1.4)
    elif mode == "sunset":
        h = (h * 0.35 + 0.08) % 1.0
        l = min(0.9, l * 1.1)
    elif mode == "forest":
        h = (h * 0.3 + 0.3) % 1.0
    elif mode == "ocean":
        h = (h * 0.3 + 0.55) % 1.0
    elif mode == "vintage":
        s = min(1.0, s * 0.65)
        l = min(0.9, l * 0.95 + 0.05)
    else:
        h = (h + hue_shift) % 1.0
        s = min(1.0, max(0.0, s * sat_mult))
        l = min(1.0, max(0.0, l * val_mult))

    nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
    return int(nr * 255), int(ng * 255), int(nb * 255)


def process_png(filepath, outpath, mode="random", hue_shift=0.33, flip_h=False, tint_outline=False):
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
                orig_cols = [(cdata[i*3], cdata[i*3+1], cdata[i*3+2]) for i in range(len(cdata)//3)]
                
                if mode in THEMES:
                    new_cols = remap_palette_colors(orig_cols, THEMES[mode], tint_outline)
                elif mode == "shuffle":
                    new_cols = shuffle_palette_colors(orig_cols)
                else:
                    new_cols = []
                    for r, g, b in orig_cols:
                        nr, ng, nb = transform_single_pixel(r, g, b, mode, hue_shift)
                        new_cols.append((nr, ng, nb))

                new_cdata = bytearray()
                for r, g, b in new_cols:
                    new_cdata.extend([r, g, b])
                cdata = bytes(new_cdata)
                crc = struct.pack(">I", zlib.crc32(ctype + cdata) & 0xffffffff)
                chunks.append((ctype, cdata, crc))
            elif ctype == b"IDAT":
                idat_parts.append(cdata)
            elif ctype != b"IEND":
                chunks.append((ctype, cdata, crc))

        # 1. Trường hợp ảnh Indexed PLTE (color_type == 3):
        if has_plte:
            if not flip_h:
                out = bytearray(b"\x89PNG\r\n\x1a\n")
                for ct, cd, cr in chunks:
                    out.extend(struct.pack(">I", len(cd)) + ct + cd + cr)
                for idat in idat_parts:
                    out.extend(struct.pack(">I", len(idat)) + b"IDAT" + idat + struct.pack(">I", zlib.crc32(b"IDAT" + idat) & 0xffffffff))
                out.extend(struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xffffffff))
                with open(outpath, "wb") as f:
                    f.write(out)
                return True
            else:
                raw = zlib.decompress(b"".join(idat_parts))
                new_raw = bytearray()
                raw_pos = 0

                if bit_depth == 8:
                    stride = width
                    prior = bytearray(stride)
                    for _ in range(height):
                        ftype = raw[raw_pos]
                        raw_pos += 1
                        line = raw[raw_pos:raw_pos+stride]
                        raw_pos += stride
                        curr = bytearray(stride)
                        for i in range(stride):
                            x = line[i]
                            a = curr[i-1] if i >= 1 else 0
                            b = prior[i]
                            c = prior[i-1] if i >= 1 else 0
                            if ftype == 0: v = x
                            elif ftype == 1: v = (x + a) & 0xff
                            elif ftype == 2: v = (x + b) & 0xff
                            elif ftype == 3: v = (x + ((a + b) >> 1)) & 0xff
                            elif ftype == 4: v = (x + paeth(a, b, c)) & 0xff
                            else: v = x
                            curr[i] = v
                        prior = curr
                        curr.reverse()
                        new_raw.append(0)
                        new_raw.extend(curr)
                elif bit_depth == 4:
                    stride = (width + 1) // 2
                    prior = bytearray(stride)
                    for _ in range(height):
                        ftype = raw[raw_pos]
                        raw_pos += 1
                        line = raw[raw_pos:raw_pos+stride]
                        raw_pos += stride
                        curr = bytearray(stride)
                        for i in range(stride):
                            x = line[i]
                            a = curr[i-1] if i >= 1 else 0
                            b = prior[i]
                            c = prior[i-1] if i >= 1 else 0
                            if ftype == 0: v = x
                            elif ftype == 1: v = (x + a) & 0xff
                            elif ftype == 2: v = (x + b) & 0xff
                            elif ftype == 3: v = (x + ((a + b) >> 1)) & 0xff
                            elif ftype == 4: v = (x + paeth(a, b, c)) & 0xff
                            else: v = x
                            curr[i] = v
                        prior = curr
                        pix = []
                        for b in curr:
                            pix.append((b >> 4) & 0x0f)
                            pix.append(b & 0x0f)
                        pix = pix[:width]
                        pix.reverse()
                        packed = bytearray()
                        for i in range(0, len(pix), 2):
                            p1 = pix[i]
                            p2 = pix[i+1] if i+1 < len(pix) else 0
                            packed.append((p1 << 4) | (p2 & 0x0f))
                        new_raw.append(0)
                        new_raw.extend(packed)
                else:
                    return False

                comp = zlib.compress(bytes(new_raw), 6)
                out = bytearray(b"\x89PNG\r\n\x1a\n")
                for ct, cd, cr in chunks:
                    out.extend(struct.pack(">I", len(cd)) + ct + cd + cr)
                out.extend(struct.pack(">I", len(comp)) + b"IDAT" + comp + struct.pack(">I", zlib.crc32(b"IDAT" + comp) & 0xffffffff))
                out.extend(struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xffffffff))
                with open(outpath, "wb") as f:
                    f.write(out)
                return True

        # 2. Trường hợp ảnh Truecolor RGBA/RGB (color_type == 2 hoặc 6):
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

            color_map = {}
            if mode in THEMES:
                unique_cols = set()
                for y in range(height):
                    for x in range(width):
                        off = (y * width + x) * bpp
                        a = unfiltered[off+3] if bpp == 4 else 255
                        if a > 15:
                            unique_cols.add((unfiltered[off], unfiltered[off+1], unfiltered[off+2]))
                
                orig_list = list(unique_cols)
                remapped_list = remap_palette_colors(orig_list, THEMES[mode], tint_outline)
                for o, r_col in zip(orig_list, remapped_list):
                    color_map[o] = r_col

            elif mode == "shuffle":
                unique_cols = set()
                for y in range(height):
                    for x in range(width):
                        off = (y * width + x) * bpp
                        a = unfiltered[off+3] if bpp == 4 else 255
                        if a > 15:
                            unique_cols.add((unfiltered[off], unfiltered[off+1], unfiltered[off+2]))
                
                orig_list = list(unique_cols)
                shuffled_list = shuffle_palette_colors(orig_list)
                for o, s_col in zip(orig_list, shuffled_list):
                    color_map[o] = s_col

            new_raw = bytearray()
            for y in range(height):
                row_pixels = []
                for x in range(width):
                    off = (y * width + x) * bpp
                    r, g, b = unfiltered[off], unfiltered[off+1], unfiltered[off+2]
                    a = unfiltered[off+3] if bpp == 4 else None

                    if color_map:
                        nr, ng, nb = color_map.get((r, g, b), (r, g, b))
                    else:
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
    except Exception as ex:
        # print(f"Error processing {filepath}: {ex}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Tool đổi màu sắc, chống bản quyền triệt để cho kho tranh Pixel Art")
    parser.add_argument("--mode", choices=ALL_CHOICES, default="random",
                        help="Phong cách đổi màu (Themes: fire, ice, cyberpunk, golden, toxic, synthwave, gameboy, pastel_sweet, gothic; Shuffle: hoán vị mảng màu; hoặc drastic, neon...)")
    parser.add_argument("--hue", type=float, default=0.33, help="Góc lệch màu cho legacy hue mode")
    parser.add_argument("--flip", action="store_true", help="Lật đối xứng gương (Horizontal Flip) toàn bộ ảnh")
    parser.add_argument("--flip-random", action="store_true", help="Ngẫu nhiên lật gương 50/50 cho từng ảnh")
    parser.add_argument("--tint-outline", action="store_true", help="Nhuộm màu nét viền theo theme thay vì giữ viền đen nguyên bản")
    parser.add_argument("--preview", type=str, help="Chạy thử nghiệm trên 1 ảnh để xem trước kết quả")
    parser.add_argument("--target", choices=["all", "artworks", "images"], default="all", help="Thư mục muốn áp dụng")
    parser.add_argument("--dir", type=str, help="Đường dẫn thư mục tùy chọn muốn xử lý")
    parser.add_argument("--workers", type=int, default=16, help="Số luồng xử lý song song")

    args = parser.parse_args()

    # Chế độ Preview 1 ảnh
    if args.preview:
        if not os.path.exists(args.preview):
            print(f"[!] Không tìm thấy file: {args.preview}")
            sys.exit(1)
        out_preview = "preview_transformed.png"
        h = random.uniform(0.05, 0.95) if args.mode == "random" else args.hue
        m = random.choice(THEME_NAMES + ["drastic", "shuffle", "pastel_sweet", "cyberpunk"]) if args.mode == "random" else args.mode
        ok = process_png(args.preview, out_preview, mode=m, hue_shift=h, flip_h=args.flip, tint_outline=args.tint_outline)
        if ok:
            print(f"[+] Đã tạo ảnh xem thử thành công với mode='{m}': {os.path.abspath(out_preview)}")
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
    print(f"[*] Chế độ: mode={args.mode}, flip_horizontal={args.flip}, flip_random={args.flip_random}, tint_outline={args.tint_outline}, workers={args.workers}")

    success = 0
    failed = 0

    RANDOM_MODES = THEME_NAMES + ["drastic", "shuffle", "pastel_sweet", "neon", "sunset", "forest", "ocean", "cyberpunk"]

    def worker(path):
        h = random.uniform(0.05, 0.95) if args.mode == "random" else args.hue
        m = random.choice(RANDOM_MODES) if args.mode == "random" else args.mode
        flip_this = random.choice([True, False]) if args.flip_random else args.flip
        tint_this = args.tint_outline or (args.mode == "random" and random.choice([True, False]))
        return process_png(path, path, mode=m, hue_shift=h, flip_h=flip_this, tint_outline=tint_this)

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

    print("\n\n[=== HOÀN TẤT ĐỔI MÀU & CHỐNG BẢN QUYỀN ===]")
    print(f"- Thành công: {success}")
    print(f"- Bỏ qua: {failed}")

    print("\n[*] Đang tái tạo lại toàn bộ API và nén lại Catalog...")
    os.system(f"python3 {os.path.join(BASE_DIR, 'tools', 'shuffle_and_scramble.py')}")


if __name__ == "__main__":
    main()
