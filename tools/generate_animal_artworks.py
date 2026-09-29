#!/usr/bin/env python3
import os
import zlib
import struct
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTWORKS_ANIMALS_DIR = os.path.join(BASE_DIR, "public", "artworks", "animals")

def write_rgba_png(width, height, pixels_rgba, out_path):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            r, g, b, a = pixels_rgba[y * width + x]
            raw.extend([r, g, b, a])
    
    comp = zlib.compress(bytes(raw), 6)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    out = bytearray(b"\x89PNG\r\n\x1a\n")
    out.extend(struct.pack(">I", 13) + b"IHDR" + ihdr + struct.pack(">I", zlib.crc32(b"IHDR" + ihdr) & 0xffffffff))
    out.extend(struct.pack(">I", len(comp)) + b"IDAT" + comp + struct.pack(">I", zlib.crc32(b"IDAT" + comp) & 0xffffffff))
    out.extend(struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xffffffff))
    with open(out_path, "wb") as f:
        f.write(out)

def create_grid(w=36, h=36):
    return [[(0,0,0,0) for _ in range(w)] for _ in range(h)]

def draw_rect(g, x1, y1, x2, y2, c):
    h, w = len(g), len(g[0])
    for y in range(max(0, y1), min(h, y2+1)):
        for x in range(max(0, x1), min(w, x2+1)):
            g[y][x] = c

def draw_circle(g, cx, cy, r, c):
    h, w = len(g), len(g[0])
    for y in range(h):
        for x in range(w):
            if (x - cx)**2 + (y - cy)**2 <= r**2:
                g[y][x] = c

def add_outline(g, outline_color=(25, 25, 30, 255)):
    h, w = len(g), len(g[0])
    new_g = [row[:] for row in g]
    for y in range(h):
        for x in range(w):
            if g[y][x][3] > 0:
                for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w:
                        if g[ny][nx][3] == 0:
                            new_g[ny][nx] = outline_color
    return new_g

def flatten(g):
    return [p for row in g for p in row]

def main():
    artworks = {}

    C_DARK = (30, 25, 25, 255)
    C_WHITE = (255, 255, 255, 255)
    C_PINK = (255, 160, 180, 255)
    C_RED = (220, 45, 45, 255)
    C_YELLOW = (255, 205, 40, 255)

    # 1. Shiba Inu
    g = create_grid()
    C_SHIBA = (235, 150, 60, 255)
    C_CREAM = (255, 240, 215, 255)
    draw_rect(g, 7, 5, 12, 12, C_SHIBA)
    draw_rect(g, 23, 5, 28, 12, C_SHIBA)
    draw_rect(g, 9, 8, 11, 11, C_PINK)
    draw_rect(g, 24, 8, 26, 11, C_PINK)
    draw_circle(g, 18, 17, 10, C_SHIBA)
    draw_circle(g, 18, 19, 8, C_CREAM)
    g[16][14] = C_DARK; g[16][22] = C_DARK
    g[19][18] = C_DARK
    g[18][12] = C_PINK; g[18][24] = C_PINK
    draw_rect(g, 12, 25, 24, 27, C_RED)
    draw_circle(g, 18, 30, 6, C_SHIBA)
    g = add_outline(g)
    artworks["art_shiba_inu.png"] = flatten(g)

    # 2. Red Panda
    g = create_grid()
    C_RED_PANDA = (205, 75, 45, 255)
    C_DARK_BROWN = (55, 35, 30, 255)
    draw_circle(g, 8, 8, 4, C_WHITE)
    draw_circle(g, 27, 8, 4, C_WHITE)
    draw_circle(g, 8, 8, 2, C_DARK_BROWN)
    draw_circle(g, 27, 8, 2, C_DARK_BROWN)
    draw_circle(g, 18, 16, 9, C_RED_PANDA)
    draw_rect(g, 13, 17, 23, 23, C_WHITE)
    g[15][14] = C_DARK_BROWN; g[15][21] = C_DARK_BROWN
    g[18][17] = C_DARK_BROWN
    for i in range(5):
        col = C_RED_PANDA if i % 2 == 0 else C_DARK_BROWN
        draw_rect(g, 23 + i, 22 + i, 27 + i, 24 + i, col)
    draw_circle(g, 18, 28, 6, C_DARK_BROWN)
    g = add_outline(g)
    artworks["art_red_panda.png"] = flatten(g)

    # 3. Cute Axolotl
    g = create_grid()
    C_AXO_PINK = (255, 175, 195, 255)
    C_AXO_GILL = (240, 75, 120, 255)
    C_LIGHT_PINK = (255, 220, 235, 255)
    for dy in [-4, 0, 4]:
        draw_rect(g, 4, 15 + dy, 8, 17 + dy, C_AXO_GILL)
        draw_rect(g, 27, 15 + dy, 31, 17 + dy, C_AXO_GILL)
    draw_circle(g, 18, 16, 9, C_AXO_PINK)
    draw_circle(g, 18, 18, 6, C_LIGHT_PINK)
    g[15][13] = C_DARK; g[15][22] = C_DARK
    g[17][12] = C_AXO_GILL; g[17][23] = C_AXO_GILL
    draw_circle(g, 18, 27, 6, C_AXO_PINK)
    g = add_outline(g)
    artworks["art_axolotl_cute.png"] = flatten(g)

    # 4. Corgi Loaf
    g = create_grid()
    C_CORGI_ORANGE = (240, 165, 65, 255)
    draw_rect(g, 8, 4, 13, 12, C_CORGI_ORANGE)
    draw_rect(g, 22, 4, 27, 12, C_CORGI_ORANGE)
    draw_circle(g, 18, 17, 9, C_CORGI_ORANGE)
    draw_rect(g, 14, 15, 21, 23, C_WHITE)
    g[15][13] = C_DARK; g[15][22] = C_DARK
    g[18][17] = C_DARK
    draw_circle(g, 18, 28, 8, C_CORGI_ORANGE)
    draw_rect(g, 15, 27, 20, 34, C_WHITE)
    g = add_outline(g)
    artworks["art_corgi_loaf.png"] = flatten(g)

    # 5. Bunny with Carrot
    g = create_grid()
    C_CARROT_ORANGE = (250, 120, 30, 255)
    C_LEAF_GREEN = (60, 180, 75, 255)
    draw_rect(g, 12, 3, 15, 14, C_WHITE)
    draw_rect(g, 20, 3, 23, 14, C_WHITE)
    draw_rect(g, 13, 6, 14, 12, C_PINK)
    draw_rect(g, 21, 6, 22, 12, C_PINK)
    draw_circle(g, 18, 18, 8, C_WHITE)
    g[17][14] = C_DARK; g[17][21] = C_DARK
    g[19][17] = C_PINK
    draw_circle(g, 18, 28, 7, C_WHITE)
    draw_rect(g, 15, 24, 23, 30, C_CARROT_ORANGE)
    draw_rect(g, 22, 22, 25, 24, C_LEAF_GREEN)
    g = add_outline(g)
    artworks["art_bunny_carrot.png"] = flatten(g)

    # 6. Baby Penguin
    g = create_grid()
    C_BLUE_SCARF = (45, 140, 240, 255)
    draw_circle(g, 18, 15, 9, C_DARK)
    draw_circle(g, 18, 16, 6, C_WHITE)
    g[14][14] = C_DARK; g[14][21] = C_DARK
    draw_rect(g, 16, 16, 19, 18, C_YELLOW)
    draw_rect(g, 11, 22, 24, 25, C_BLUE_SCARF)
    draw_rect(g, 19, 25, 22, 30, C_BLUE_SCARF)
    draw_circle(g, 18, 29, 6, C_WHITE)
    draw_rect(g, 11, 26, 14, 31, C_DARK)
    draw_rect(g, 21, 26, 24, 31, C_DARK)
    draw_rect(g, 14, 33, 16, 35, C_YELLOW)
    draw_rect(g, 19, 33, 21, 35, C_YELLOW)
    g = add_outline(g)
    artworks["art_baby_penguin.png"] = flatten(g)

    # 7. Sea Turtle
    g = create_grid()
    C_SHELL_GREEN = (40, 135, 80, 255)
    C_SHELL_LIGHT = (90, 190, 125, 255)
    C_SKIN_GREEN = (140, 215, 140, 255)
    draw_circle(g, 18, 18, 9, C_SHELL_GREEN)
    draw_circle(g, 18, 18, 6, C_SHELL_LIGHT)
    draw_circle(g, 18, 7, 4, C_SKIN_GREEN)
    g[6][16] = C_DARK; g[6][19] = C_DARK
    draw_rect(g, 6, 10, 11, 16, C_SKIN_GREEN)
    draw_rect(g, 24, 10, 29, 16, C_SKIN_GREEN)
    draw_rect(g, 8, 23, 12, 27, C_SKIN_GREEN)
    draw_rect(g, 23, 23, 27, 27, C_SKIN_GREEN)
    g = add_outline(g)
    artworks["art_sea_turtle.png"] = flatten(g)

    # 8. Sweet Koala
    g = create_grid()
    C_KOALA_GRAY = (145, 155, 165, 255)
    C_TREE_BROWN = (125, 75, 45, 255)
    draw_rect(g, 6, 2, 10, 34, C_TREE_BROWN)
    draw_circle(g, 13, 10, 4, C_WHITE)
    draw_circle(g, 26, 10, 4, C_WHITE)
    draw_circle(g, 19, 16, 8, C_KOALA_GRAY)
    g[14][16] = C_DARK; g[14][23] = C_DARK
    draw_circle(g, 19, 18, 3, C_DARK)
    draw_circle(g, 17, 26, 7, C_KOALA_GRAY)
    g = add_outline(g)
    artworks["art_sweet_koala.png"] = flatten(g)

    # 9. Blue Whale
    g = create_grid()
    C_WHALE_BLUE = (50, 115, 215, 255)
    C_WHALE_BELLY = (185, 220, 255, 255)
    C_WATER_SPRAY = (110, 200, 255, 255)
    draw_rect(g, 12, 4, 14, 9, C_WATER_SPRAY)
    draw_rect(g, 15, 3, 17, 7, C_WATER_SPRAY)
    draw_circle(g, 17, 20, 10, C_WHALE_BLUE)
    draw_rect(g, 10, 22, 24, 28, C_WHALE_BELLY)
    g[17][11] = C_DARK
    draw_rect(g, 24, 17, 30, 21, C_WHALE_BLUE)
    draw_rect(g, 29, 13, 33, 25, C_WHALE_BLUE)
    g = add_outline(g)
    artworks["art_blue_whale.png"] = flatten(g)

    # 10. Baby Tiger
    g = create_grid()
    C_TIGER_ORANGE = (245, 135, 35, 255)
    draw_circle(g, 9, 8, 3, C_TIGER_ORANGE)
    draw_circle(g, 26, 8, 3, C_TIGER_ORANGE)
    draw_circle(g, 18, 17, 9, C_TIGER_ORANGE)
    g[10][17] = C_DARK; g[11][18] = C_DARK; g[12][17] = C_DARK
    g[16][10] = C_DARK; g[17][10] = C_DARK
    g[16][25] = C_DARK; g[17][25] = C_DARK
    g[16][14] = C_DARK; g[16][21] = C_DARK
    draw_circle(g, 18, 20, 4, C_WHITE)
    g[19][18] = C_DARK
    draw_circle(g, 18, 28, 7, C_TIGER_ORANGE)
    g = add_outline(g)
    artworks["art_baby_tiger.png"] = flatten(g)

    # 11. Little Owl
    g = create_grid()
    C_OWL_BROWN = (155, 95, 55, 255)
    C_OWL_CREAM = (245, 230, 195, 255)
    draw_circle(g, 18, 15, 9, C_OWL_BROWN)
    draw_circle(g, 13, 14, 4, C_WHITE)
    draw_circle(g, 22, 14, 4, C_WHITE)
    draw_circle(g, 13, 14, 2, C_DARK)
    draw_circle(g, 22, 14, 2, C_DARK)
    draw_rect(g, 17, 17, 18, 19, C_YELLOW)
    draw_circle(g, 18, 26, 7, C_OWL_CREAM)
    draw_rect(g, 8, 31, 27, 33, C_TREE_BROWN)
    draw_rect(g, 14, 30, 16, 32, C_YELLOW)
    draw_rect(g, 19, 30, 21, 32, C_YELLOW)
    g = add_outline(g)
    artworks["art_little_owl.png"] = flatten(g)

    # 12. Fluffy Hamster
    g = create_grid()
    C_HAM_GOLD = (235, 175, 115, 255)
    draw_circle(g, 10, 8, 3, C_PINK)
    draw_circle(g, 25, 8, 3, C_PINK)
    draw_circle(g, 18, 18, 10, C_HAM_GOLD)
    draw_circle(g, 18, 21, 7, C_WHITE)
    g[15][13] = C_DARK; g[15][22] = C_DARK
    g[18][12] = C_PINK; g[18][23] = C_PINK
    g[18][17] = C_DARK
    draw_rect(g, 16, 23, 19, 27, C_DARK_BROWN)
    g = add_outline(g)
    artworks["art_fluffy_hamster.png"] = flatten(g)

    # 13. Baby Dragon
    g = create_grid()
    C_DRAGON_PURPLE = (175, 95, 230, 255)
    C_DRAGON_WING = (255, 160, 210, 255)
    C_HORNS = (255, 215, 75, 255)
    draw_rect(g, 11, 4, 13, 8, C_HORNS)
    draw_rect(g, 22, 4, 24, 8, C_HORNS)
    draw_circle(g, 18, 15, 8, C_DRAGON_PURPLE)
    g[14][14] = C_DARK; g[14][21] = C_DARK
    draw_rect(g, 5, 18, 10, 24, C_DRAGON_WING)
    draw_rect(g, 25, 18, 30, 24, C_DRAGON_WING)
    draw_circle(g, 18, 26, 7, C_DRAGON_PURPLE)
    draw_rect(g, 15, 24, 20, 31, C_HORNS)
    g = add_outline(g)
    artworks["art_baby_dragon.png"] = flatten(g)

    # 14. Chameleon Rainbow
    g = create_grid()
    C_CHAM_CYAN = (45, 205, 195, 255)
    C_CHAM_LIME = (135, 230, 60, 255)
    draw_circle(g, 14, 15, 8, C_CHAM_CYAN)
    draw_circle(g, 13, 13, 3, C_WHITE)
    draw_circle(g, 13, 13, 1, C_DARK)
    draw_circle(g, 21, 21, 8, C_CHAM_LIME)
    draw_rect(g, 26, 21, 31, 27, C_CHAM_LIME)
    draw_rect(g, 28, 25, 32, 29, C_YELLOW)
    g = add_outline(g)
    artworks["art_chameleon_rainbow.png"] = flatten(g)

    # 15. Hedgehog with Flower
    g = create_grid()
    C_HEDGE_QUILLS = (95, 65, 50, 255)
    C_HEDGE_BODY = (225, 190, 160, 255)
    draw_circle(g, 21, 18, 10, C_HEDGE_QUILLS)
    draw_circle(g, 13, 22, 6, C_HEDGE_BODY)
    g[20][10] = C_DARK
    g[22][8] = C_DARK
    draw_circle(g, 22, 10, 3, C_PINK)
    g[10][22] = C_YELLOW
    g = add_outline(g)
    artworks["art_hedgehog_flower.png"] = flatten(g)

    # 16. Cat with Boba
    g = create_grid()
    C_CAT_ORANGE = (245, 150, 65, 255)
    draw_rect(g, 9, 5, 13, 11, C_CAT_ORANGE)
    draw_rect(g, 22, 5, 26, 11, C_CAT_ORANGE)
    draw_circle(g, 18, 14, 7, C_CAT_ORANGE)
    g[13][14] = C_DARK; g[13][21] = C_DARK
    g[15][17] = C_PINK
    draw_rect(g, 14, 21, 22, 31, C_WHITE)
    draw_rect(g, 15, 23, 21, 29, (215, 170, 130, 255))
    g[27][17] = C_DARK; g[27][19] = C_DARK; g[28][18] = C_DARK
    draw_rect(g, 17, 16, 18, 23, C_RED)
    g = add_outline(g)
    artworks["art_cat_boba.png"] = flatten(g)

    saved = 0
    for filename, pixels in artworks.items():
        filepath = os.path.join(ARTWORKS_ANIMALS_DIR, filename)
        write_rgba_png(36, 36, pixels, filepath)
        saved += 1

    print(f"[+] Saved {saved} new pixel art animal files in {ARTWORKS_ANIMALS_DIR}")

    # Update manifest.json
    manifest_path = os.path.join(ARTWORKS_ANIMALS_DIR, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    current_items = set(manifest.get("items", []))
    for fn in artworks.keys():
        current_items.add(fn)

    manifest["items"] = sorted(list(current_items))
    total_manifest = len(manifest["items"])
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[+] Updated {manifest_path} with {total_manifest} items!")

if __name__ == "__main__":
    main()
