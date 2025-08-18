#!/usr/bin/env python3
import os, re, time, glob, subprocess
import numpy as np
from PIL import Image, ImageSequence

# Importa módulo de detecção de toque
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.touch_exit import setup_touch_exit

ROTATE_DEG = 0
GIF_DIR = "/home/dw/painel/assets/gifs2"
SWITCH_DELAY = float(os.getenv("SWITCH_DELAY", 5))

def find_fb_by_name(target="fb_ili9486"):
    for p in glob.glob("/sys/class/graphics/fb*/name"):
        try:
            if open(p).read().strip() == target:
                fb = os.path.basename(os.path.dirname(p))  # ex: fb2 ou fb0
                return f"/dev/{fb}", int(fb[2:])
        except Exception:
            pass
    raise RuntimeError(f"Framebuffer '{target}' não encontrado. Verifique se o overlay SPI está ativo (dtoverlay=tft35a) e reinicie.")

def read(path, as_int=False, default=None):
    try:
        s = open(path).read().strip()
        return int(s) if as_int else s
    except Exception:
        return default

def fb_geometry(fbdev):
    idx = int(os.path.basename(fbdev)[2:])
    # width/height via fbset
    w = h = None
    try:
        out = subprocess.check_output(["fbset", "-s", "-fb", fbdev], text=True)
        m = re.search(r"geometry\s+(\d+)\s+(\d+)", out)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    if not (w and h):
        # fallback padrão da MPI3501
        w, h = 320, 480
    bpp = read(f"/sys/class/graphics/fb{idx}/bits_per_pixel", as_int=True, default=16)
    stride = (read(f"/sys/class/graphics/fb{idx}/stride", as_int=True) or
              read(f"/sys/class/graphics/fb{idx}/fb_fix/line_length", as_int=True) or
              w * (bpp // 8))
    return w, h, bpp, stride

def rgb_to_rgb565_le(pil_img):
    arr = np.asarray(pil_img, dtype=np.uint8)    # [H,W,3]
    r = (arr[...,0] >> 3).astype(np.uint16)
    g = (arr[...,1] >> 2).astype(np.uint16)
    b = (arr[...,2] >> 3).astype(np.uint16)
    rgb565 = (r << 11) | (g << 5) | b
    lo = (rgb565 & 0xFF).astype(np.uint8)
    hi = (rgb565 >> 8).astype(np.uint8)
    out = np.stack([lo, hi], axis=-1)           # [H,W,2]
    return out

def load_gif(path, width, height):
    gif = Image.open(path)
    frames, durations = [], []
    for f in ImageSequence.Iterator(gif):
        fr = f.convert("RGB")
        # Ajuste de tamanho: caber na tela mantendo proporção
        fr.thumbnail((width, height))
        frames.append(fr.copy())
        durations.append(f.info.get("duration", 100) / 1000.0)
    return frames, durations

def main():
    # Configura detecção de toque para sair
    touch_monitor = setup_touch_exit()
    
    FB, fb_idx = find_fb_by_name("fb_ili9486")
    width, height, bpp, stride = fb_geometry(FB)
    bytespp = bpp // 8
    print(f"[fb] {FB}: {width}x{height} @{bpp}bpp stride={stride}")

    gif_paths = glob.glob(os.path.join(GIF_DIR, "*.gif"))
    if not gif_paths:
        raise FileNotFoundError(f"Nenhum GIF encontrado em {GIF_DIR}")

    while True:
        # Verifica se deve sair
        if touch_monitor.should_exit():
            print("🔴 TOQUE DETECTADO - VOLTANDO AO MENU!")
            print("🚀 Executando menu principal...")
            
            # Para este script e executa o menu
            touch_monitor.stop()
            
            # Executa o menu principal
            import subprocess
            subprocess.run(["sudo", "python3", "/home/dw/painel/src/core/touch_menu_visual.py"])
            break
            
        for path in gif_paths:
            if touch_monitor.should_exit():
                print("🔴 TOQUE DETECTADO - VOLTANDO AO MENU!")
                print("🚀 Executando menu principal...")
                
                # Executa o menu principal
                import subprocess
                subprocess.run(["sudo", "python3", "/home/dw/painel/src/core/touch_menu_visual.py"])
                break
                
            frames, durations = load_gif(path, width, height)
            for fr, dt in zip(frames, durations):
                # Verifica toque antes de cada frame
                if touch_monitor.should_exit():
                    print("🔴 TOQUE DETECTADO - VOLTANDO AO MENU!")
                    print("🚀 Executando menu principal...")
                    
                    # Executa o menu principal
                    import subprocess
                    subprocess.run(["sudo", "python3", "/home/dw/painel/src/core/touch_menu_visual.py"])
                    break
                # Canvas do tamanho exato do fb
                canvas = Image.new("RGB", (width, height), "black")
                # centralizado; mude pos se quiser
                x = (width  - fr.width)  // 2
                y = (height - fr.height) // 2
                canvas.paste(fr, (x, y))

                if ROTATE_DEG:
                    canvas = canvas.rotate(ROTATE_DEG, expand=False)

                if bpp == 16:
                    rgb565 = rgb_to_rgb565_le(canvas)          # [H,W,2]
                    row_bytes = width * 2
                    flat = rgb565.reshape(height, row_bytes)
                    buf = bytearray()
                    for y_line in range(height):
                        line = flat[y_line].tobytes()
                        buf += line
                        if stride > row_bytes:
                            buf += b"\x00" * (stride - row_bytes)
                    payload = bytes(buf)
                else:
                    raw = canvas.tobytes()
                    row_bytes = width * bytespp
                    buf = bytearray()
                    for y_line in range(height):
                        start = y_line * row_bytes
                        buf += raw[start:start+row_bytes]
                        if stride > row_bytes:
                            buf += b"\x00" * (stride - row_bytes)
                    payload = bytes(buf)

                with open(FB, "wb") as f:
                    f.write(payload)

                time.sleep(dt)
                
                # Verifica toque após cada frame
                if touch_monitor.should_exit():
                    print("🔴 TOQUE DETECTADO - VOLTANDO AO MENU!")
                    print("🚀 Executando menu principal...")
                    
                    # Executa o menu principal
                    import subprocess
                    subprocess.run(["sudo", "python3", "/home/dw/painel/src/core/touch_menu_visual.py"])
                    break

            # Verifica toque após cada GIF
            if touch_monitor.should_exit():
                print("🔴 TOQUE DETECTADO - VOLTANDO AO MENU!")
                print("🚀 Executando menu principal...")
                
                # Executa o menu principal
                import subprocess
                subprocess.run(["sudo", "python3", "/home/dw/painel/src/core/touch_menu_visual.py"])
                break
                
            time.sleep(SWITCH_DELAY)

if __name__ == "__main__":
    main()