#!/usr/bin/env python3
"""
DEBUG VISUAL - MAPA DE COORDENADAS
- Mostra onde cada toque é mapeado
- Desenha grid de coordenadas na tela
"""

import os
import sys
import time
import signal
import struct
import threading
from PIL import Image, ImageDraw, ImageFont

# Configurações
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
FRAMEBUFFER = "/dev/fb0"
TOUCH_DEVICE = "/dev/input/event0"

class TouchDebugMap:
    """Mapa visual de debug para coordenadas."""
    
    def __init__(self):
        self.running = False
        self.last_touch = None
        
    def _coordinate_mapper(self, raw_x, raw_y):
        """Mapeia coordenadas (mesma função do menu)."""
        x_min, x_max = 600, 3600
        y_min, y_max = 400, 3800
        
        # Mapeia coordenadas normalizadas (0-1)
        norm_x = (raw_x - x_min) / (x_max - x_min)
        norm_y = (raw_y - y_min) / (y_max - y_min)
        
        # MESMA CORREÇÃO DO MENU: Rotação corrigida
        screen_x = int((1.0 - norm_y) * SCREEN_WIDTH)     # Y raw invertido → X tela
        screen_y = int(norm_x * SCREEN_HEIGHT)            # X raw direto → Y tela
        
        screen_x = max(0, min(screen_x, SCREEN_WIDTH - 1))
        screen_y = max(0, min(screen_y, SCREEN_HEIGHT - 1))
        
        return screen_x, screen_y
    
    def _draw_debug_map(self):
        """Desenha mapa de debug com grid."""
        img = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), (20, 20, 30))
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Título
        draw.text((SCREEN_WIDTH//2, 15), "🔍 MAPA DE DEBUG - COORDENADAS", 
                 font=font_large, fill=(255, 255, 255), anchor="mm")
        
        # Grid de coordenadas
        # Linhas verticais a cada 60px
        for x in range(0, SCREEN_WIDTH, 60):
            color = (100, 100, 100) if x % 120 == 0 else (60, 60, 60)
            draw.line([(x, 30), (x, SCREEN_HEIGHT)], fill=color, width=1)
            if x % 120 == 0:
                draw.text((x, 35), str(x), font=font_small, fill=(200, 200, 200), anchor="mm")
        
        # Linhas horizontais a cada 40px
        for y in range(40, SCREEN_HEIGHT, 40):
            color = (100, 100, 100) if y % 80 == 0 else (60, 60, 60)
            draw.line([(0, y), (SCREEN_WIDTH, y)], fill=color, width=1)
            if y % 80 == 0:
                draw.text((10, y), str(y), font=font_small, fill=(200, 200, 200))
        
        # Áreas dos botões (do menu original)
        button_areas = [
            {"name": "BOTÃO 1", "x": 180, "y": 4, "w": 280, "h": 100, "color": (50, 150, 255)},
            {"name": "BOTÃO 2", "x": 180, "y": 110, "w": 280, "h": 100, "color": (255, 100, 50)},
            {"name": "BOTÃO 3", "x": 180, "y": 216, "w": 280, "h": 100, "color": (50, 255, 150)}
        ]
        
        for i, btn in enumerate(button_areas):
            # Retângulo semi-transparente
            overlay = Image.new('RGBA', (btn["w"], btn["h"]), (*btn["color"], 80))
            img.paste(overlay, (btn["x"], btn["y"]), overlay)
            
            # Borda
            draw.rectangle([btn["x"], btn["y"], btn["x"]+btn["w"], btn["y"]+btn["h"]], 
                          outline=btn["color"], width=2)
            
            # Texto
            center_x = btn["x"] + btn["w"]//2
            center_y = btn["y"] + btn["h"]//2
            draw.text((center_x, center_y), btn["name"], 
                     font=font_large, fill=(255, 255, 255), anchor="mm")
            
            # Coordenadas nos cantos
            draw.text((btn["x"]+5, btn["y"]+5), f"({btn['x']},{btn['y']})", 
                     font=font_small, fill=(255, 255, 255))
            draw.text((btn["x"]+btn["w"]-5, btn["y"]+btn["h"]-5), 
                     f"({btn['x']+btn['w']},{btn['y']+btn['h']})", 
                     font=font_small, fill=(255, 255, 255), anchor="rb")
        
        # Último toque
        if self.last_touch:
            raw_x, raw_y, screen_x, screen_y = self.last_touch
            
            # Marca o ponto do toque
            draw.ellipse([screen_x-10, screen_y-10, screen_x+10, screen_y+10], 
                        fill=(255, 255, 0), outline=(255, 0, 0), width=3)
            
            # Informações do toque
            info_y = SCREEN_HEIGHT - 40
            draw.text((SCREEN_WIDTH//2, info_y), 
                     f"ÚLTIMO TOQUE: RAW({raw_x},{raw_y}) → TELA({screen_x},{screen_y})", 
                     font=font_small, fill=(255, 255, 0), anchor="mm")
            
            # Seta apontando para o toque
            draw.polygon([(screen_x, screen_y-15), (screen_x-5, screen_y-25), (screen_x+5, screen_y-25)], 
                        fill=(255, 0, 0))
        
        return img
    
    def _write_to_framebuffer(self, image):
        """Escreve no framebuffer."""
        try:
            rgb565_data = bytearray()
            pixels = image.load()
            
            for y in range(SCREEN_HEIGHT):
                for x in range(SCREEN_WIDTH):
                    r, g, b = pixels[x, y]
                    r565 = (r >> 3) & 0x1F
                    g565 = (g >> 2) & 0x3F
                    b565 = (b >> 3) & 0x1F
                    rgb565 = (r565 << 11) | (g565 << 5) | b565
                    rgb565_data.append(rgb565 & 0xFF)
                    rgb565_data.append((rgb565 >> 8) & 0xFF)
            
            with open(FRAMEBUFFER, 'wb') as fb:
                fb.write(rgb565_data)
                fb.flush()
                
        except Exception as e:
            print(f"❌ Erro no framebuffer: {e}")
    
    def _read_touch(self):
        """Monitora toques."""
        try:
            with open(TOUCH_DEVICE, 'rb') as f:
                current_x = 0
                current_y = 0
                
                while self.running:
                    data = f.read(24)
                    if len(data) < 24:
                        continue
                        
                    sec, usec, type_, code, value = struct.unpack('llHHi', data)
                    
                    if type_ == 3:  # EV_ABS
                        if code == 0:  # ABS_X
                            current_x = value
                        elif code == 1:  # ABS_Y
                            current_y = value
                        elif code == 24 and value > 100:  # Pressão
                            if current_x > 0:
                                screen_x, screen_y = self._coordinate_mapper(current_x, current_y)
                                self.last_touch = (current_x, current_y, screen_x, screen_y)
                                print(f"🎯 TOQUE: RAW({current_x},{current_y}) -> TELA({screen_x},{screen_y})")
                                
                                # Verifica qual botão seria
                                if 180 <= screen_x <= 460:
                                    if 4 <= screen_y <= 104:
                                        print(f"   → Seria BOTÃO 1 (SISTEMA)")
                                    elif 110 <= screen_y <= 210:
                                        print(f"   → Seria BOTÃO 2 (ANIMAÇÃO)")
                                    elif 216 <= screen_y <= 316:
                                        print(f"   → Seria BOTÃO 3 (REDE)")
                                    else:
                                        print(f"   → Fora das áreas dos botões")
                                else:
                                    print(f"   → X fora da área dos botões")
                                
        except Exception as e:
            print(f"❌ Erro lendo toque: {e}")
    
    def start(self):
        """Inicia debug."""
        print("🔍 MAPA DE DEBUG - COORDENADAS")
        print("=" * 40)
        print("👆 Toque na tela para ver onde cada coordenada é mapeada")
        print("📍 As áreas coloridas mostram onde deveriam estar os botões")
        print()
        
        self.running = True
        
        # Thread para toques
        touch_thread = threading.Thread(target=self._read_touch)
        touch_thread.daemon = True
        touch_thread.start()
        
        # Loop de renderização
        try:
            while self.running:
                debug_image = self._draw_debug_map()
                self._write_to_framebuffer(debug_image)
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n🛑 Debug interrompido")
        
        self.stop()
    
    def stop(self):
        """Para debug."""
        self.running = False
        with open(FRAMEBUFFER, 'wb') as fb:
            fb.write(b'\x00\x00' * (SCREEN_WIDTH * SCREEN_HEIGHT))

def main():
    """Função principal."""
    if os.geteuid() != 0:
        print("⚠️  Execute como root: sudo python3 debug_coordenadas.py")
        return
    
    debug = TouchDebugMap()
    debug.start()

if __name__ == "__main__":
    main()
