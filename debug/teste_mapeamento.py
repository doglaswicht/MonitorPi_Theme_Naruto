#!/usr/bin/env python3
"""
TESTE DE MAPEAMENTO DOS 3 BOTÕES
- Só registra os toques, não executa scripts
- Para mapeamento preciso das posições
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

# Layout
LEFT_PANEL_WIDTH = 240
RIGHT_PANEL_WIDTH = 240
BUTTON_HEIGHT = 100
BUTTON_MARGIN = 6

class TouchMappingTest:
    """Teste para mapear posições dos botões."""
    
    def __init__(self):
        self.running = False
        self.buttons = []
        self.touch_count = 0
        self._create_buttons()
        
    def _create_buttons(self):
        """Cria os 3 botões."""
        button_configs = [
            {"name": "SISTEMA", "icon": "📊", "color": (50, 150, 255)},
            {"name": "ANIMAÇÃO", "icon": "🎬", "color": (255, 100, 50)},
            {"name": "REDE", "icon": "🌐", "color": (50, 255, 150)}
        ]
        
        start_y = (SCREEN_HEIGHT - (3 * BUTTON_HEIGHT + 2 * BUTTON_MARGIN)) // 2
        
        for i, config in enumerate(button_configs):
            button = {
                "x": LEFT_PANEL_WIDTH + 10,
                "y": start_y + i * (BUTTON_HEIGHT + BUTTON_MARGIN),
                "width": RIGHT_PANEL_WIDTH - 20,
                "height": BUTTON_HEIGHT,
                "name": config["name"],
                "icon": config["icon"],
                "color": config["color"],
                "number": i + 1
            }
            self.buttons.append(button)
    
    def _coordinate_mapper(self, raw_x, raw_y):
        """Mapeia coordenadas."""
        x_min, x_max = 600, 3600
        y_min, y_max = 400, 3800
        
        screen_x = int((raw_x - x_min) * SCREEN_WIDTH / (x_max - x_min))
        screen_y = int((raw_y - y_min) * SCREEN_HEIGHT / (y_max - y_min))
        
        screen_x = max(0, min(screen_x, SCREEN_WIDTH - 1))
        screen_y = max(0, min(screen_y, SCREEN_HEIGHT - 1))
        
        return screen_x, screen_y
    
    def _draw_menu(self):
        """Desenha menu de teste."""
        img = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), (20, 20, 30))
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        
        # Linha divisória
        draw.line([(LEFT_PANEL_WIDTH, 0), (LEFT_PANEL_WIDTH, SCREEN_HEIGHT)], 
                 fill=(100, 100, 100), width=3)
        
        # Lado esquerdo
        draw.text((LEFT_PANEL_WIDTH//2, 50), "TESTE DE", font=font_large, 
                 fill=(255, 255, 255), anchor="mm")
        draw.text((LEFT_PANEL_WIDTH//2, 80), "MAPEAMENTO", font=font_large, 
                 fill=(255, 255, 255), anchor="mm")
        
        draw.text((LEFT_PANEL_WIDTH//2, 130), f"Toques: {self.touch_count}/3", font=font_medium, 
                 fill=(255, 255, 0), anchor="mm")
        
        instructions = [
            "1º: SISTEMA (📊)",
            "2º: ANIMAÇÃO (🎬)", 
            "3º: REDE (🌐)"
        ]
        
        for i, inst in enumerate(instructions):
            color = (0, 255, 0) if i < self.touch_count else (200, 200, 200)
            draw.text((LEFT_PANEL_WIDTH//2, 160 + i*25), inst, font=font_medium, 
                     fill=color, anchor="mm")
        
        # Botões do lado direito
        for button in self.buttons:
            x1, y1 = button["x"], button["y"]
            x2, y2 = x1 + button["width"], y1 + button["height"]
            
            # Retângulo do botão
            draw.rectangle([x1, y1, x2, y2], 
                          fill=button["color"], outline=(255, 255, 255), width=3)
            
            # Ícone e texto
            center_x = x1 + button["width"] // 2
            center_y = y1 + button["height"] // 2
            
            draw.text((center_x, center_y - 15), button["icon"], 
                     font=font_large, fill=(255, 255, 255), anchor="mm")
            draw.text((center_x, center_y + 15), button["name"], 
                     font=font_medium, fill=(255, 255, 255), anchor="mm")
            
            # Número
            draw.text((x1 + 10, y1 + 10), f"{button['number']}", 
                     font=font_medium, fill=(255, 255, 255))
        
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
                                self._handle_touch(current_x, current_y, screen_x, screen_y)
                                
        except Exception as e:
            print(f"❌ Erro lendo toque: {e}")
    
    def _handle_touch(self, raw_x, raw_y, screen_x, screen_y):
        """Processa toques APENAS para mapeamento."""
        self.touch_count += 1
        
        print(f"🎯 TOQUE {self.touch_count}: RAW({raw_x},{raw_y}) -> TELA({screen_x},{screen_y})")
        
        # Verifica qual botão foi tocado
        for button in self.buttons:
            x1, y1 = button["x"], button["y"]
            x2, y2 = x1 + button["width"], y1 + button["height"]
            
            if x1 <= screen_x <= x2 and y1 <= screen_y <= y2:
                print(f"   ✅ BOTÃO {button['number']} ({button['name']}) DETECTADO!")
                return
        
        print(f"   ❌ Toque fora dos botões")
        print(f"   📍 Posições dos botões:")
        for button in self.buttons:
            x1, y1 = button["x"], button["y"]
            x2, y2 = x1 + button["width"], y1 + button["height"]
            print(f"      {button['number']}. {button['name']}: ({x1},{y1}) até ({x2},{y2})")
    
    def start(self):
        """Inicia teste."""
        print("🎯 TESTE DE MAPEAMENTO DOS 3 BOTÕES")
        print("=" * 40)
        print("👆 Dê 3 toques na ordem:")
        print("   1º: Centro do botão SISTEMA (📊)")
        print("   2º: Centro do botão ANIMAÇÃO (🎬)")
        print("   3º: Centro do botão REDE (🌐)")
        print()
        
        self.running = True
        
        # Thread para toques
        touch_thread = threading.Thread(target=self._read_touch)
        touch_thread.daemon = True
        touch_thread.start()
        
        # Loop de renderização
        try:
            while self.running and self.touch_count < 10:  # Para após 10 toques
                menu_image = self._draw_menu()
                self._write_to_framebuffer(menu_image)
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n🛑 Teste interrompido")
        
        self.stop()
    
    def stop(self):
        """Para teste."""
        self.running = False
        with open(FRAMEBUFFER, 'wb') as fb:
            fb.write(b'\x00\x00' * (SCREEN_WIDTH * SCREEN_HEIGHT))

def main():
    """Função principal."""
    if os.geteuid() != 0:
        print("⚠️  Execute como root: sudo python3 teste_mapeamento.py")
        return
    
    test = TouchMappingTest()
    test.start()

if __name__ == "__main__":
    main()
