#!/usr/bin/env python3
import os, re, time, glob, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import subprocess

# Importa módulo de detecção de toque
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.touch_exit import setup_touch_exit
    print("✅ Módulo touch_exit importado com sucesso")
except Exception as e:
    print(f"❌ Erro importando touch_exit: {e}")
    import sys
    sys.exit(1)

# ===== CONFIGS =====
ROTATE_DEG = 0  # 0, 90, 180, 270
IMG_PATH   = "/home/dw/painel/assets/kakashicute.png"
LOCATION_CACHE_FILE = "/home/dw/.painel_location_cache"  # Arquivo oculto seguro
LOCATION_CACHE_DURATION = 3600  # 1 hora em segundos
ENABLE_GEOLOCATION = False  # DESABILITADO por padrão por segurança
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

def get_wifi_network_name():
    """Obtém o nome da rede WiFi conectada (SSID)."""
    try:
        # Tenta iwgetid primeiro (mais comum)
        out = subprocess.check_output(["iwgetid", "-r"], text=True, stderr=subprocess.DEVNULL)
        return out.strip() or "Cabo/Desconhecida"
    except Exception:
        pass
    
    try:
        # Fallback: nmcli
        out = subprocess.check_output(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"], 
                                    text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if line.startswith("yes:"):
                ssid = line.split(":", 1)[1].strip()
                return ssid or "Cabo/Desconhecida"
    except Exception:
        pass
    
    return "Cabo/Desconhecida"

def get_temperature():
    """Obtém a temperatura do sistema (CPU)."""
    try:
        # Raspberry Pi - temperatura da CPU
        temp = read("/sys/class/thermal/thermal_zone0/temp", as_int=True, default=None)
        if temp:
            return f"{temp / 1000:.1f}°C"
    except Exception:
        pass
    
    return "N/A"

def get_location():
    """Obtém localização com proteções de privacidade."""
    
    # PROTEÇÃO: Verifica se geolocalização está habilitada
    if not ENABLE_GEOLOCATION:
        return get_location_fallback()
    
    # Verifica cache primeiro
    cached_location = get_cached_location()
    if cached_location:
        return cached_location
    
    # PROTEÇÃO: Apenas APIs HTTPS confiáveis
    apis = [
        {
            "url": "https://ipapi.co/json/",
            "timeout": 3,  # Timeout reduzido
            "parser": lambda data: parse_ipapi_response_safe(data)
        }
    ]
    
    for api in apis:
        try:
            import urllib.request
            import json
            
            # PROTEÇÃO: Headers genéricos para evitar fingerprinting
            request = urllib.request.Request(api["url"])
            request.add_header('User-Agent', 'Mozilla/5.0')
            
            with urllib.request.urlopen(request, timeout=api["timeout"]) as response:
                data = json.loads(response.read().decode())
                result = api["parser"](data)
                if result:
                    # Salva no cache protegido
                    save_location_cache_safe(result)
                    return result
                    
        except Exception as e:
            print(f"⚠️ Erro de geolocalização (privacidade protegida)")
            continue
    
    # Fallback: timezone do sistema (sempre disponível)
    fallback = get_location_fallback()
    save_location_cache_safe(fallback)
    return fallback

def parse_ipapi_response_safe(data):
    """Parser seguro - sem coordenadas precisas."""
    city = data.get("city")
    region = data.get("region")
    country = data.get("country_name")
    
    # PROTEÇÃO: Não exibe coordenadas GPS precisas
    if city and region:
        return f"{city}, {region[:2]}"[:15]
    elif city:
        return city[:12]
    elif country:
        return country[:10]
    return None

def save_location_cache_safe(location):
    """Salva localização no cache com proteções."""
    try:
        # PROTEÇÃO: Arquivo com permissões restritas
        import stat
        with open(LOCATION_CACHE_FILE, 'w') as f:
            f.write(location)
        # Define permissões apenas para o usuário (600)
        os.chmod(LOCATION_CACHE_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass

def get_cached_location():
    """Verifica se há localização válida no cache."""
    try:
        if os.path.exists(LOCATION_CACHE_FILE):
            stat = os.stat(LOCATION_CACHE_FILE)
            age = time.time() - stat.st_mtime
            
            if age < LOCATION_CACHE_DURATION:
                with open(LOCATION_CACHE_FILE, 'r') as f:
                    cached = f.read().strip()
                    if cached and not cached.endswith("(TZ)"):
                        return cached + " (cache)"
    except Exception:
        pass
    return None

def save_location_cache(location):
    """Salva localização no cache."""
    try:
        with open(LOCATION_CACHE_FILE, 'w') as f:
            f.write(location)
    except Exception:
        pass

def get_cached_location():
    """Verifica se há localização válida no cache."""
    try:
        if os.path.exists(LOCATION_CACHE_FILE):
            stat = os.stat(LOCATION_CACHE_FILE)
            age = time.time() - stat.st_mtime
            
            if age < LOCATION_CACHE_DURATION:
                with open(LOCATION_CACHE_FILE, 'r') as f:
                    cached = f.read().strip()
                    if cached and not cached.endswith("(TZ)"):
                        return cached + " (cache)"
    except Exception:
        pass
    return None

def parse_ipapi_response(data):
    """Parser para ipapi.co"""
    city = data.get("city")
    region = data.get("region")
    country = data.get("country_name")
    lat = data.get("latitude")
    lon = data.get("longitude")
    
    if city and region:
        location = f"{city}, {region[:2]}"
        if lat and lon:
            location += f" ({lat:.1f},{lon:.1f})"
        return location[:20]
    elif city:
        return city[:15]
    elif country:
        return country[:10]
    return None

def parse_ipinfo_response(data):
    """Parser para ipinfo.io"""
    city = data.get("city")
    region = data.get("region")
    country = data.get("country")
    loc = data.get("loc")  # "lat,lon"
    
    if city and region:
        location = f"{city}, {region[:2]}"
        if loc and "," in loc:
            lat, lon = loc.split(",")
            location += f" ({float(lat):.1f},{float(lon):.1f})"
        return location[:20]
    elif city:
        return city[:15]
    elif country:
        return country[:10]
    return None

def get_location_fallback():
    """Fallback: localização baseada no timezone do sistema."""
    try:
        timezone = subprocess.check_output(["timedatectl", "show", "-p", "Timezone", "--value"], 
                                         text=True, stderr=subprocess.DEVNULL).strip()
        if "/" in timezone:
            location = timezone.split("/")[-1].replace("_", " ")
            return f"{location[:12]} (TZ)"
        return f"{timezone[:10]} (TZ)"
    except Exception:
        pass
    
    return "Local"

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

# Configura detecção de toque para sair
try:
    print("🔧 Configurando detecção de toque...")
    touch_monitor = setup_touch_exit()
    print("✅ Touch monitor configurado com sucesso")
    print("⏰ Script rodará indefinidamente até toque")
except Exception as e:
    print(f"❌ Erro configurando touch monitor: {e}")
    import sys
    sys.exit(1)

# ===== LOOP =====
print("🔄 Iniciando loop principal...")
frame_count = 0
while True:
    frame_count += 1
    
    # Verifica toque a cada frame para resposta rápida
    if touch_monitor.should_exit():
        print("🔴 TOQUE DETECTADO - VOLTANDO AO MENU!")
        print("🚀 Executando menu principal...")
        
        # Para este script e executa o menu
        touch_monitor.stop()
        
        # Executa o menu principal
        import subprocess
        subprocess.run(["sudo", "python3", "/home/dw/painel/src/core/touch_menu_visual.py"])
        break
            
        print(f"📊 Frame {frame_count} - Sistema rodando...")
    
    try:
        # canvas do tamanho exato do fb
        img = Image.new("RGB", (width, height), "black")
        draw = ImageDraw.Draw(img)
        iface, ip = pick_ip()
        
        # Obtém as novas informações
        wifi_name = get_wifi_network_name()
        temperature = get_temperature()
        location = get_location()
        
        # textos
        draw.text((10, 10),  "Dw",                            fill="yellow", font=FONT_BIG)
        draw.text((10, 40), f"IP ({iface or '-'}) : {ip}", fill="lime", font=FONT_SMALL)
        draw.text((10, 60), f"WiFi: {wifi_name}", fill="orange", font=FONT_SMALL)
        draw.text((10, 80), f"Temp: {temperature}", fill="red", font=FONT_SMALL)
        draw.text((10, 100), f"Local: {location}", fill="magenta", font=FONT_SMALL)
        draw.text((10, 260),  time.strftime("Hora: %H:%M:%S"), fill="cyan", font=FONT_SMALL)
        draw.text((10, 280),  time.strftime("Data: %d/%m/%Y"), fill="cyan",   font=FONT_SMALL)

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

        time.sleep(0.1)  # Reduzido de 1s para 0.1s para melhor responsividade
        
    except Exception as e:
        print(f"❌ Erro no frame {frame_count}: {e}")
        time.sleep(0.1)  # Reduzido de 1s para 0.1s

