#!/usr/bin/env python3
import os, re, time, glob, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import subprocess
# ===== CONFIGS =====
ROTATE_DEG = 0  # 0, 90, 180, 270
IMG_PATH   = "/home/dw/painel/assets/kakashicute.png"
# ========RETURN IP=========
def list_ipv4():
    """Retorna dict iface->IP v4 (sem 127.0.0.1)."""
    ips = {}
    try:
        out = subprocess.check_output(["ip", "-4", "-o", "addr", "show"], text=True)
        # linhas tipo: "2: wlan0    inet 192.168.1.23/24 brd ..."
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[2] == "inet":
                ip_cidr = parts[3]
                ip = ip_cidr.split("/")[0]
                iface = parts[1]
                if ip != "127.0.0.1":
                    ips[iface] = ip
    except Exception:
        pass
    return ips

def pick_ip():
    """Escolhe um IP “preferido”: wlan0 > eth0 > primeiro disponível."""
    ips = list_ipv4()
    if "wlan0" in ips: return "wlan0", ips["wlan0"]
    if "eth0"  in ips: return "eth0",  ips["eth0"]
    if ips: return next(iter(ips.items()))
    return None, "sem IP"

# -- util: ler arquivo simples
def read(path, as_int=False, default=None):
    try:
        s = open(path).read().strip()
        return int(s) if as_int else s
    except Exception:
        return default

# -- achar /dev/fbN pelo nome do driver (não importa se vira fb0, fb2...)
def find_fb_by_name(target="fb_ili9486"):
    for p in glob.glob("/sys/class/graphics/fb*/name"):
        try:
            if open(p).read().strip() == target:
                fb = os.path.basename(os.path.dirname(p))  # "fb2"
                return f"/dev/{fb}", int(fb[2:])
        except Exception:
            pass
    raise RuntimeError(f"{target} não encontrado (confira dtoverlay=tft35a e SPI).")

# -- obter largura/altura/bpp/stride de forma robusta
def fb_geometry(fbdev):
    idx = int(os.path.basename(fbdev)[2:])
    # 1) tentar via fbset
    w = h = None
    try:
        out = subprocess.check_output(["fbset", "-s", "-fb", fbdev], text=True)
        m = re.search(r"geometry\s+(\d+)\s+(\d+)", out)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    # 2) fallback: alguns kernels têm virtual_size
    if not (w and h):
        vs = read(f"/sys/class/graphics/fb{idx}/virtual_size")
        if vs and "," in vs:
            a, b = vs.replace(" ", "").split(",")
            w, h = int(a), int(b)
    # 3) último recurso: padrão da MPI3501
    if not (w and h):
        w, h = 320, 480

    bpp = read(f"/sys/class/graphics/fb{idx}/bits_per_pixel", as_int=True, default=16)
    stride = (read(f"/sys/class/graphics/fb{idx}/stride", as_int=True) or
              read(f"/sys/class/graphics/fb{idx}/fb_fix/line_length", as_int=True) or
              w * (bpp // 8))
    return w, h, bpp, stride

# -- conversão RGB888 -> RGB565 (LE)
def rgb_to_rgb565_le(pil_img):
    arr = np.asarray(pil_img, dtype=np.uint8)  # [H,W,3]
    r = (arr[..., 0] >> 3).astype(np.uint16)
    g = (arr[..., 1] >> 2).astype(np.uint16)
    b = (arr[..., 2] >> 3).astype(np.uint16)
    rgb565 = (r << 11) | (g << 5) | b
    lo = (rgb565 & 0xFF).astype(np.uint8)
    hi = (rgb565 >> 8).astype(np.uint8)
    out = np.stack([lo, hi], axis=-1)         # [H,W,2]
    return out

# ===== INICIALIZAÇÃO =====
FB, fb_index = find_fb_by_name("fb_ili9486")
width, height, bpp, stride = fb_geometry(FB)
bytespp = bpp // 8

# fontes
FONT_BIG   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      18)

print(f"[fb] {FB}: {width}x{height} @{bpp}bpp stride={stride}")

# ===== LOOP =====
while True:
    # canvas do tamanho exato do fb
    img = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(img)
    iface, ip = pick_ip()
    # textos
    draw.text((10, 10),  "DOGLAS WICHT",                  fill="yellow", font=FONT_BIG)
    draw.text((10, 50),  time.strftime("Hora: %H:%M:%S"), fill="yellow", font=FONT_BIG)
    draw.text((10, 90),  time.strftime("Data: %d/%m/%Y"), fill="cyan",   font=FONT_SMALL)
    draw.text((10, 270), f"IP ({iface or '-'}) : {ip}", fill="lime", font=FONT_SMALL)
    # imagem (com transparência preservada)
    if os.path.exists(IMG_PATH):
        logo = Image.open(IMG_PATH).convert("RGBA")

        # thumbnail precisa de tupla de INTEIROS. Ex.: metade da largura e 1/2 da altura:
        max_w = int(width * 0.1)   # ajuste conforme preferir (0.6, 0.7…)
        max_h = int(height * 0.5)
        #logo.thumbnail((max_w, max_h))  # mantém proporção

        # ===== POSICIONAMENTO =====
        # 1) centralizado embaixo:
        # pos_x = (width - logo.width) // 2
        # pos_y = height - logo.height - 10

        # 2) canto inferior direito (ativo):
        pos_x = width - logo.width - 10
        pos_y = height - logo.height - 10

        # 3) canto inferior esquerdo:
        # pos_x = 10
        # pos_y = height - logo.height - 10

        # 4) logo abaixo da data (~130 px do topo):
        # pos_x = (width - logo.width) // 2
        # pos_y = 130
        # ===========================

        img.paste(logo, (pos_x, pos_y), logo)

    # rotação (90/270 usa expand=False pra manter o buffer)
    if ROTATE_DEG:
        img = img.rotate(ROTATE_DEG, expand=False)

    # enviar ao framebuffer respeitando stride por linha
    if bpp == 16:
        rgb565 = rgb_to_rgb565_le(img)              # [H,W,2]
        row_bytes = width * 2
        flat = rgb565.reshape(height, row_bytes)
        buf = bytearray()
        for y in range(height):
            line = flat[y].tobytes()
            buf += line
            if stride > row_bytes:
                buf += b"\x00" * (stride - row_bytes)
        payload = bytes(buf)
    else:
        raw = img.tobytes()
        row_bytes = width * bytespp
        buf = bytearray()
        for y in range(height):
            start = y * row_bytes
            buf += raw[start:start+row_bytes]
            if stride > row_bytes:
                buf += b"\x00" * (stride - row_bytes)
        payload = bytes(buf)

    with open(FB, "wb") as f:
        f.write(payload)

    time.sleep(1)

