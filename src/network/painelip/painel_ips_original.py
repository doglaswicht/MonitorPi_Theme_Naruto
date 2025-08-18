#!/usr/bin/env python3
"""Painel para exibição de dispositivos de rede a partir de varreduras nmap."""
import os, re, time, glob, subprocess, ipaddress
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ===== CONFIGS =====
ROTATE_DEG    = 0               # 0, 90, 180, 270
SCAN_INTERVAL = 45              # segundos entre varreduras nmap
PAGE_TIME     = 3               # segundos por página na lista
PREF_IFACES   = ["wlan0", "eth0"]
TITLE         = "Dispositivos na rede"
# ===================

@dataclass
class DeviceInfo:
    """Informações básicas sobre um dispositivo descoberto na rede."""

    ip: str = ""
    mac: str = ""
    vendor: str = ""
    hostname: str = ""
    os: str = ""
# ---------- util framebuffer ----------
def read(path, as_int=False, default=None):
    try:
        s = open(path).read().strip()
        return int(s) if as_int else s
    except Exception:
        return default

def find_fb_by_name(target="fb_ili9486"):
    for p in glob.glob("/sys/class/graphics/fb*/name"):
        try:
            if open(p).read().strip() == target:
                fb = os.path.basename(os.path.dirname(p))  # "fb2" | "fb0"...
                return f"/dev/{fb}", int(fb[2:])
        except Exception:
            pass
    raise RuntimeError(f"{target} não encontrado (confira dtoverlay=tft35a e SPI).")

def fb_geometry(fbdev):
    idx = int(os.path.basename(fbdev)[2:])
    w = h = None
    try:
        out = subprocess.check_output(["fbset", "-s", "-fb", fbdev], text=True)
        m = re.search(r"geometry\s+(\d+)\s+(\d+)", out)
        if m: w, h = int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    if not (w and h):
        vs = read(f"/sys/class/graphics/fb{idx}/virtual_size")
        if vs and "," in vs:
            a, b = vs.replace(" ", "").split(","); w, h = int(a), int(b)
    if not (w and h):
        w, h = 320, 480  # fallback típico do ILI9486
    bpp    = read(f"/sys/class/graphics/fb{idx}/bits_per_pixel", as_int=True, default=16)
    stride = (read(f"/sys/class/graphics/fb{idx}/stride", as_int=True) or
              read(f"/sys/class/graphics/fb{idx}/fb_fix/line_length", as_int=True) or
              w * (bpp // 8))
    return w, h, bpp, stride

def rgb_to_rgb565_le(pil_img):
    arr = np.asarray(pil_img, dtype=np.uint8)  # [H,W,3]
    r = (arr[...,0] >> 3).astype(np.uint16)
    g = (arr[...,1] >> 2).astype(np.uint16)
    b = (arr[...,2] >> 3).astype(np.uint16)
    rgb565 = (r << 11) | (g << 5) | b
    lo = (rgb565 & 0xFF).astype(np.uint8)
    hi = (rgb565 >> 8).astype(np.uint8)
    return np.stack([lo, hi], axis=-1)        # [H,W,2]

def fb_write(FB, img, bpp, stride):
    width, height = img.size
    bytespp = bpp // 8
    if bpp == 16:
        rgb565 = rgb_to_rgb565_le(img)           # [H,W,2]
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

# ---------- redes ----------
def list_ipv4_by_iface():
    res = {}
    try:
        out = subprocess.check_output(["ip", "-4", "-o", "addr", "show"], text=True)
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[2] == "inet":
                iface = parts[1]
                cidr  = parts[3]  # "192.168.1.15/24"
                res[iface] = cidr
    except Exception:
        pass
    return res

def pick_iface_and_cidr():
    ips = list_ipv4_by_iface()
    for i in PREF_IFACES:
        if i in ips:
            return i, ips[i]
    if ips:
        k = next(iter(ips.keys()))
        return k, ips[k]
    return None, None

def cidr_to_network(cidr):
    try:
        ipnet = ipaddress.ip_network(cidr, strict=False)
        return str(ipnet.with_prefixlen)  # "192.168.1.0/24"
    except Exception:
        return None

def run_nmap_scan(cidr_network):
    """
    Executa o nmap com detecção de sistema operacional e resolução de nomes
    na rede CIDR fornecida. Retorna o processo para leitura assíncrona da
    saída.
    """
    if not cidr_network:
        return None
    cmd = ["nmap", "-O", "-T4", cidr_network]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc

def parse_nmap_output(text: str) -> List[DeviceInfo]:
    """Converte a saída do nmap em lista de :class:`DeviceInfo`."""

    devices: List[DeviceInfo] = []
    cur: Optional[DeviceInfo] = None
    for line in text.splitlines():
        line = line.strip()
        # Inicia novo bloco para cada host encontrado
        m = re.search(r"Nmap scan report for (.*)", line)
        if m:
            if cur:
                devices.append(cur)
            token = m.group(1).strip()
            cur = DeviceInfo()
            
            # Verifica se o token contém IP e hostname (formato: hostname (ip))
            m2 = re.search(r"\(([\d.]+)\)$", token)
            if m2:
                cur.ip = m2.group(1)
                host = token[:m2.start()].strip()
                if host and not re.match(r"^\d+\.\d+\.\d+\.\d+$", host):
                    cur.hostname = host
            else:
                if re.match(r"^\d+\.\d+\.\d+\.\d+$", token):
                    cur.ip = token
                else:
                    cur.hostname = token
            continue

        if not cur:
            continue

        if line.startswith("MAC Address:"):
            parts = line.split()
            if len(parts) >= 3:
                cur.mac = parts[2]
            if len(parts) > 3:
                cur.vendor = " ".join(parts[3:]).strip("()")
        elif line.startswith("OS details:"):
            cur.os = line.split("OS details:", 1)[1].strip()
        elif line.startswith("Running:") and not cur.os:
            cur.os = line.split("Running:", 1)[1].strip()

    if cur:
        devices.append(cur)

    # únicos por IP
    uniq: Dict[str, DeviceInfo] = {}
    for d in devices:
        if d.ip:
            uniq[d.ip] = d
    # ordena por IP
    ordered = sorted(uniq.values(), key=lambda d: tuple(int(x) for x in d.ip.split(".")))
    return ordered

# ---------- UI ----------
def draw_loading(img, step, title, info):
    """Desenha título, info e 3 pontos vermelhos animados."""
    w, h = img.size
    draw = ImageDraw.Draw(img)
    FONT_TITLE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    FONT_TEXT  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      16)
    draw.text((10, 8), title, fill="yellow", font=FONT_TITLE)
    draw.text((10, 40), info,   fill="cyan",   font=FONT_TEXT)
    # 3 dots
    cx = w//2 - 30
    cy = h//2 + 10
    r  = 8
    # acende 1..3 conforme step
    active = (step % 3) + 1
    for i in range(3):
        x = cx + i*30
        fill = "red" if (i+1) <= active else (50,50,50)
        draw.ellipse((x-r, cy-r, x+r, cy+r), fill=fill, outline=None)

def draw_list(img, title, iface, ip_show, devices: List[DeviceInfo], page, page_time, started_at):
    w, h = img.size
    draw = ImageDraw.Draw(img)
    FONT_TITLE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    FONT_TEXT  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      16)

    draw.text((10, 8), title, fill="yellow", font=FONT_TITLE)
    draw.text((10, 40), f"IF: {iface or '-'}  IP: {ip_show or 'sem IP'}", fill="cyan", font=FONT_TEXT)
    draw.text((270, 270),  time.strftime("Hora: %H:%M:%S"), fill="yellow", font=FONT_TEXT)

    y0 = 70
    line_h = 22
    max_lines = (h - y0 - 10) // line_h
    total = len(devices)

    if total == 0:
        draw.text((10, y0), "Nenhum dispositivo encontrado.", fill="white", font=FONT_TEXT)
        return page  # sem paginação

    pages = max(1, (total + max_lines - 1) // max_lines)
    page = min(page, pages-1)
    start = page * max_lines
    end   = min(total, start + max_lines)

    for i, d in enumerate(devices[start:end], start=1):
        line = f"{start+i:02d}. {d.ip}"
        if d.mac:
            line += f"  {d.mac}"
        if d.vendor:
            line += f"  ({d.vendor})"
        draw.text((10, y0 + (i-1)*line_h), line, fill="white", font=FONT_TEXT)

    if pages > 1:
        draw.text((w-70, h-24), f"{page+1}/{pages}", fill="gray", font=FONT_TEXT)
        # troca página conforme PAGE_TIME
        if time.time() - started_at >= PAGE_TIME:
            page = (page + 1) % pages
            started_at = time.time()
    return page, started_at

# ---------- MAIN ----------

def main():
    
    FB, fb_idx = find_fb_by_name("fb_ili9486")
    width, height, bpp, stride = fb_geometry(FB)

    # fontes carregadas dentro dos draws para simplicidade de exemplo; ok assim
    print(f"[fb] {FB}: {width}x{height} @{bpp}bpp stride={stride}")

    # estado
    last_scan_end = 0
    scan_proc = None
    scan_buf  = []
    devices: List[DeviceInfo] = []
    page = 0
    page_started = time.time()
    loading_step = 0
    last_dot_change = time.time()
    DOT_INTERVAL = 5.0



    while True:
        # escolher iface e rede
        iface, cidr = pick_iface_and_cidr()
        ip_show = cidr.split("/")[0] if cidr else None
        network = cidr_to_network(cidr) if cidr else None
        subtitle = f"IF: {iface or '-'}  NET: {network or 'n/d'}"

        # decide iniciar novo scan
        if scan_proc is None and (time.time() - last_scan_end >= SCAN_INTERVAL) and network:
            scan_proc = run_nmap_scan(network)
            scan_buf  = []
            loading_step = 0
            page = 0
            page_started = time.time()

        # render
        img = Image.new("RGB", (width, height), "black")

        if scan_proc is not None and scan_proc.poll() is None:
            # ainda escaneando → anima 3 pontos
            draw_loading(img, loading_step, TITLE, subtitle + "  (escaneando...)")
            loading_step += 1
            if time.time() - last_dot_change >= DOT_INTERVAL:
                loading_step += 0.1
                last_dot_change = time.time()
            # drena saída parcial (se houver)
            try:
                chunk = scan_proc.stdout.read()
                if chunk:
                    scan_buf.append(chunk)
            except Exception:
                pass
        else:
            # se acabou de terminar, parseia
            if scan_proc is not None:
                try:
                    # pega o restante
                    rest = scan_proc.stdout.read() or ""
                    scan_buf.append(rest)
                except Exception:
                    pass
                text = "".join(scan_buf)
                devices = parse_nmap_output(text)
                last_scan_end = time.time()
                scan_proc = None
                page = 0
                page_started = time.time()

            # mostra lista paginada
            res = draw_list(img, TITLE, iface, ip_show, devices, page, PAGE_TIME, page_started)
            if isinstance(res, tuple):
                page, page_started = res
            else:
                page = res  # compat

        # rotação se necessário
        if ROTATE_DEG:
            img = img.rotate(ROTATE_DEG, expand=False)

        # escreve no framebuffer
        fb_write(FB, img, bpp, stride)

        time.sleep(0.2)  # animação suave + CPU amigável

if __name__ == "__main__":
    main()
