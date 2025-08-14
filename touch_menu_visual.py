#!/usr/bin/env python3
"""
TOUCHSCREEN MENU COM GIF E BOTÕES VISUAIS
- Lado esquerdo: GIF animado (toda a altura)
- Lado direito: 3 botões verticais com imagens e texto
- Touch interativo para executar scripts
"""

import os
import sys
import time
import signal
import struct
import subprocess
import threading
from threading import Lock
from PIL import Image, ImageDraw, ImageFont

# Configurações
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
FRAMEBUFFER = "/dev/fb0"
TOUCH_DEVICE = "/dev/input/event0"

# Layout
LEFT_PANEL_WIDTH = 240   # Lado esquerdo para GIF
RIGHT_PANEL_WIDTH = 240  # Lado direito para botões
BUTTON_HEIGHT = 100      # Altura de cada botão
BUTTON_MARGIN = 6        # Margem entre botões

# Processo atual
current_process = None
process_lock = threading.Lock()

class TouchMenu:
    """Menu touchscreen com GIF e botões visuais."""
    
    def __init__(self):
        self.running = False
        self.gif_frames = []
        self.gif_frame_index = 0
        self.gif_last_update = 0
        self.buttons = []
        self._load_gif()
        self._create_buttons()
        
    def _load_gif(self):
        """Carrega frames do GIF."""
        try:
            gif_path = "/home/dw/painel/assets/kakashicute.gif"
            if os.path.exists(gif_path):
                gif = Image.open(gif_path)
                self.gif_frames = []
                
                try:
                    while True:
                        # Redimensiona frame para caber no lado esquerdo
                        frame = gif.copy()
                        frame = frame.resize((LEFT_PANEL_WIDTH - 20, 280), Image.Resampling.LANCZOS)
                        
                        # Converte para RGB se necessário
                        if frame.mode != 'RGB':
                            frame = frame.convert('RGB')
                            
                        self.gif_frames.append(frame)
                        gif.seek(gif.tell() + 1)
                        
                except EOFError:
                    pass
                    
                print(f"📽️  GIF carregado: {len(self.gif_frames)} frames")
            else:
                print(f"⚠️  GIF não encontrado: {gif_path}")
                
        except Exception as e:
            print(f"❌ Erro carregando GIF: {e}")
    
    def _create_buttons(self):
        """Cria os 3 botões do lado direito."""
        # Configuração dos botões
        button_configs = [
            {
                "name": "SISTEMA",
                "script": "painelv3.py",
                "icon": "📊",
                "color": (50, 150, 255),
                "description": "Monitor do Sistema"
            },
            {
                "name": "ANIMAÇÃO", 
                "script": "painel_gif.py",
                "icon": "🎬",
                "color": (255, 100, 50),
                "description": "GIFs & Animações"
            },
            {
                "name": "REDE",
                "script": "painelip/main.py", 
                "icon": "🌐",
                "color": (50, 255, 150),
                "description": "Monitor de Rede"
            }
        ]
        
        # Calcula posições dos botões (ajustado para área de toque natural)
        start_y = (SCREEN_HEIGHT - (3 * BUTTON_HEIGHT + 2 * BUTTON_MARGIN)) // 2
        
        for i, config in enumerate(button_configs):
            button = {
                "x": 180,  # Movido mais para esquerda (era 250)
                "y": start_y + i * (BUTTON_HEIGHT + BUTTON_MARGIN), 
                "width": 280,  # Largura maior para cobrir mais área (era 220)
                "height": BUTTON_HEIGHT,
                "name": config["name"],
                "script": config["script"],
                "icon": config["icon"],
                "color": config["color"],
                "description": config["description"],
                "number": i + 1
            }
            self.buttons.append(button)
    
    def _coordinate_mapper(self, raw_x, raw_y):
        """Mapeia coordenadas raw do touch para tela."""
        # Range baseado nos testes anteriores
        x_min, x_max = 600, 3600
        y_min, y_max = 400, 3800
        
        # Mapeia coordenadas normalizadas (0-1)
        norm_x = (raw_x - x_min) / (x_max - x_min)
        norm_y = (raw_y - y_min) / (y_max - y_min)
        
        # CORREÇÃO: Baseado no debug RAW(974,3598) -> TELA(59,300)
        # RAW Y=3598 (alto) está virando TELA Y=300 (baixo) - Y ainda invertido!
        # Precisa inverter o norm_y também
        screen_x = int((1.0 - norm_y) * SCREEN_WIDTH)     # Y raw invertido → X tela
        screen_y = int(norm_x * SCREEN_HEIGHT)            # X raw direto → Y tela (sem inversão)
        
        # Limita aos bounds da tela
        screen_x = max(0, min(screen_x, SCREEN_WIDTH - 1))
        screen_y = max(0, min(screen_y, SCREEN_HEIGHT - 1))
        
        return screen_x, screen_y
    
    def _create_button_image(self, button):
        """Cria imagem de um botão."""
        img = Image.new('RGB', (button["width"], button["height"]), button["color"])
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Borda do botão
        draw.rectangle([0, 0, button["width"]-1, button["height"]-1], 
                      outline=(255, 255, 255), width=3)
        
        # Ícone grande no centro
        icon_y = 25
        draw.text((button["width"]//2, icon_y), button["icon"], 
                 font=font_large, fill=(255, 255, 255), anchor="mm")
        
        # Nome do botão
        name_y = icon_y + 35
        draw.text((button["width"]//2, name_y), button["name"], 
                 font=font_medium, fill=(255, 255, 255), anchor="mm")
        
        # Descrição
        desc_y = name_y + 25
        draw.text((button["width"]//2, desc_y), button["description"], 
                 font=font_small, fill=(230, 230, 230), anchor="mm")
        
        # Número do botão no canto
        draw.text((10, 10), f"{button['number']}", 
                 font=font_small, fill=(255, 255, 255))
        
        return img
    
    def _draw_menu(self):
        """Desenha o menu completo."""
        # Cria imagem base
        img = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), (20, 20, 30))
        draw = ImageDraw.Draw(img)
        
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            font_title = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # === LADO ESQUERDO - GIF ===
        if self.gif_frames:
            # Atualiza frame do GIF a cada 100ms
            current_time = time.time() * 1000
            if current_time - self.gif_last_update > 100:
                self.gif_frame_index = (self.gif_frame_index + 1) % len(self.gif_frames)
                self.gif_last_update = current_time
            
            # Cola frame atual do GIF
            gif_frame = self.gif_frames[self.gif_frame_index]
            gif_x = 10
            gif_y = (SCREEN_HEIGHT - gif_frame.height) // 2
            img.paste(gif_frame, (gif_x, gif_y))
            
        else:
            # Placeholder se GIF não carregou
            draw.rectangle([10, 20, LEFT_PANEL_WIDTH-10, SCREEN_HEIGHT-20], 
                          fill=(40, 40, 60), outline=(100, 100, 100), width=2)
            draw.text((LEFT_PANEL_WIDTH//2, SCREEN_HEIGHT//2), "GIF\nKAKASHI", 
                     font=font_title, fill=(150, 150, 150), anchor="mm")
        
        # Título no topo do lado esquerdo
        draw.text((LEFT_PANEL_WIDTH//2, 15), "🎯 PAINEL KAKASHI", 
                 font=font_title, fill=(255, 255, 255), anchor="mm")
        
        # === LINHA DIVISÓRIA ===
        draw.line([(LEFT_PANEL_WIDTH, 0), (LEFT_PANEL_WIDTH, SCREEN_HEIGHT)], 
                 fill=(100, 100, 100), width=3)
        
        # === LADO DIREITO - BOTÕES ===
        for button in self.buttons:
            button_img = self._create_button_image(button)
            img.paste(button_img, (button["x"], button["y"]))
        
        # Título do lado direito
        draw.text((LEFT_PANEL_WIDTH + RIGHT_PANEL_WIDTH//2, 15), "MENU PRINCIPAL", 
                 font=font_title, fill=(255, 255, 255), anchor="mm")
        
        # Status na parte inferior
        status_y = SCREEN_HEIGHT - 15
        draw.text((SCREEN_WIDTH//2, status_y), f"⏰ {time.strftime('%H:%M:%S')} | 👆 Toque nos botões", 
                 font=font_small, fill=(200, 200, 200), anchor="mm")
        
        return img
    
    def _write_to_framebuffer(self, image):
        """Escreve imagem no framebuffer."""
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
        """Monitora eventos de toque."""
        try:
            last_touch_time = 0
            
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
                            current_time = time.time()
                            
                            # Debounce: ignora toques muito rápidos
                            if current_time - last_touch_time < 0.8:
                                continue
                                
                            last_touch_time = current_time
                            
                            if current_x > 0:
                                screen_x, screen_y = self._coordinate_mapper(current_x, current_y)
                                self._handle_touch(current_x, current_y, screen_x, screen_y)
                                
        except Exception as e:
            print(f"❌ Erro lendo toque: {e}")
    
    def _handle_touch(self, raw_x, raw_y, screen_x, screen_y):
        """Processa eventos de toque."""
        global current_process
        
        print(f"📍 TOQUE: RAW({raw_x},{raw_y}) -> TELA({screen_x},{screen_y})")
        
        # Se há processo rodando, para ele
        with process_lock:
            if current_process and current_process.poll() is None:
                print("🛑 Parando processo atual...")
                current_process.terminate()
                current_process = None
                print("🔄 Voltando ao menu...")
                return
        
        # Verifica qual botão foi tocado
        for button in self.buttons:
            x1, y1 = button["x"], button["y"]
            x2, y2 = x1 + button["width"], y1 + button["height"]
            
            if x1 <= screen_x <= x2 and y1 <= screen_y <= y2:
                print(f"✅ BOTÃO {button['number']} TOCADO: {button['name']}")
                self._execute_script(button["script"], button["name"])
                return
        
        print(f"❌ Toque fora dos botões")
    
    def _execute_script(self, script, name):
        """Executa script selecionado."""
        print(f"🚀 EXECUTANDO: {name}")
        
        # Para o menu
        self.running = False
        
        # Executa script em processo separado e aguarda retorno
        try:
            # Define timeout de 30 segundos para voltar automaticamente
            threading.Timer(30.0, self._force_return_to_menu).start()
            
            # Executa script
            self._run_script_and_wait(script, name)
            
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        # Sempre volta ao menu
        self._force_return_to_menu()

    def _run_script_and_wait(self, script, name):
        """Executa script e aguarda toque para sair."""
        # Limpa tela
        with open(FRAMEBUFFER, 'wb') as fb:
            fb.write(b'\x00\x00' * (SCREEN_WIDTH * SCREEN_HEIGHT))
        
        # Ajusta diretório
        if "painelip" in script:
            os.chdir("/home/dw/painel/painelip")
            cmd = ["python3", "painel_ips.py"]
        else:
            os.chdir("/home/dw/painel")
            cmd = ["python3", script]
        
        print(f"⚡ Executando: {' '.join(cmd)}")
        
        # Executa script
        process = subprocess.Popen(cmd, preexec_fn=os.setsid)
        print(f"✅ PID: {process.pid}")
        
        # Aguarda 3 segundos
        time.sleep(3.0)
        print("👆 Toque na tela para voltar ao menu...")
        
        # Monitora toque com detecção melhorada
        touch_detected = False
        last_touch_time = 0
        
        try:
            with open(TOUCH_DEVICE, 'rb') as f:
                while process.poll() is None and not touch_detected:
                    data = f.read(24)
                    if len(data) < 24:
                        time.sleep(0.01)  # Pequena pausa
                        continue
                        
                    sec, usec, type_, code, value = struct.unpack('llHHi', data)
                    
                    # Detecta qualquer evento de toque (mais sensível)
                    if type_ == 3 and code == 24 and value > 50:  # Reduzido de 200 para 50
                        current_time = time.time()
                        
                        # Debounce mais curto
                        if current_time - last_touch_time < 0.5:
                            continue
                            
                        last_touch_time = current_time
                        print("🔴 Toque detectado - saindo!")
                        touch_detected = True
                        break
                        
                    # Detecta também evento de release (quando solta o dedo)
                    elif type_ == 1 and code == 330:  # BTN_TOUCH release
                        current_time = time.time()
                        if current_time - last_touch_time > 0.5:
                            print("🔴 Release detectado - saindo!")
                            touch_detected = True
                            break
                            
        except Exception as e:
            print(f"❌ Erro monitorando toque: {e}")
        
        # Para o processo
        try:
            if process.poll() is None:
                print("🛑 Parando processo...")
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                time.sleep(1)
                if process.poll() is None:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                print("✅ Processo parado")
        except Exception as e:
            print(f"⚠️  Erro parando processo: {e}")

    def _force_return_to_menu(self):
        """Força retorno ao menu."""
        print("🔄 VOLTANDO AO MENU...")
        
        # Mata qualquer processo restante
        try:
            subprocess.run(["sudo", "pkill", "-f", "python3.*painel"], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
        
        # Limpa tela
        try:
            with open(FRAMEBUFFER, 'wb') as fb:
                fb.write(b'\x00\x00' * (SCREEN_WIDTH * SCREEN_HEIGHT))
        except:
            pass
        
        time.sleep(1)
        
        # Volta ao menu
        self.running = True
        print("✅ MENU RESTAURADO!")
    
    def start(self):
        """Inicia o menu touchscreen."""
        print("🎯 TOUCHSCREEN MENU COM GIF")
        print("=" * 40)
        print("📽️  Lado esquerdo: GIF animado")
        print("🔘 Lado direito: 3 botões interativos")
        print("👆 Toque nos botões para executar")
        print()
        
        self.running = True
        
        # Thread para monitorar toques
        touch_thread = threading.Thread(target=self._read_touch)
        touch_thread.daemon = True
        touch_thread.start()
        
        print("📱 Menu iniciado!")
        for button in self.buttons:
            x1, y1 = button["x"], button["y"]
            x2, y2 = x1 + button["width"], y1 + button["height"]
            print(f"   {button['icon']} {button['name']}: {button['description']}")
            print(f"      Posição: ({x1},{y1}) até ({x2},{y2})")
        print()
        
        # Loop principal - renderiza menu
        try:
            while self.running:
                menu_image = self._draw_menu()
                self._write_to_framebuffer(menu_image)
                time.sleep(0.1)  # 10 FPS
                
        except KeyboardInterrupt:
            print("\n🛑 Menu interrompido")
        
        self.stop()
    
    def stop(self):
        """Para o menu."""
        self.running = False
        
        # Limpa tela
        with open(FRAMEBUFFER, 'wb') as fb:
            fb.write(b'\x00\x00' * (SCREEN_WIDTH * SCREEN_HEIGHT))

def main():
    """Função principal."""
    if os.geteuid() != 0:
        print("⚠️  Execute como root: sudo python3 touch_menu_visual.py")
        return
    
    if not os.path.exists(TOUCH_DEVICE):
        print(f"❌ Touch não encontrado: {TOUCH_DEVICE}")
        return
    
    # Signal handler para saída limpa
    def signal_handler(signum, frame):
        print("\n🛑 Saindo...")
        with open(FRAMEBUFFER, 'wb') as fb:
            fb.write(b'\x00\x00' * (SCREEN_WIDTH * SCREEN_HEIGHT))
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Inicia menu
    menu = TouchMenu()
    menu.start()

if __name__ == "__main__":
    main()
