#!/usr/bin/env python3
"""
Módulo de detecção de toque para sair de scripts
Detecta toque na tela e permite retornar ao menu principal
"""

import struct
import time
import threading
import glob

def find_touch_device():
    """Encontra automaticamente o dispositivo de touchscreen"""
    for event_path in glob.glob('/dev/input/event*'):
        try:
            event_name = event_path.split('/')[-1]  # ex: event2
            name_path = f'/sys/class/input/{event_name}/device/name'
            with open(name_path, 'r') as f:
                device_name = f.read().strip()
            
            # Procura por dispositivos de touchscreen conhecidos
            if any(touch_name in device_name.lower() for touch_name in 
                   ['ads7846', 'touchscreen', 'touch', 'ft6236', 'goodix']):
                print(f"✅ Touchscreen encontrado: {event_path} ({device_name})")
                return event_path
        except:
            continue
    
    # Fallback para event0 se não encontrar
    print("⚠️  Usando fallback: /dev/input/event0")
    return '/dev/input/event0'

TOUCH_DEVICE = find_touch_device()

class TouchExit:
    def __init__(self):
        self.exit_requested = False
        self.monitor_thread = None
        self.running = True
        
    def start_monitoring(self):
        """Inicia monitoramento de toque em thread separada"""
        print("👆 Toque na tela para voltar ao menu principal...")
        
        def monitor_touch():
            # Período de carência - ignora toques nos primeiros 3 segundos
            start_time = time.time()
            grace_period = 3.0
            
            try:
                with open(TOUCH_DEVICE, 'rb') as f:
                    while self.running and not self.exit_requested:
                        data = f.read(24)
                        if len(data) < 24:
                            time.sleep(0.01)
                            continue
                            
                        sec, usec, type_, code, value = struct.unpack('llHHi', data)
                        
                        # Detecta toque (mais específico)
                        if type_ == 3 and code == 24 and value > 100:  # Valor mais alto
                            current_time = time.time()
                            
                            # Ignora toques durante período de carência
                            if current_time - start_time < grace_period:
                                print(f"⏰ Toque ignorado durante carência ({grace_period:.1f}s)")
                                continue
                            
                            print("🔴 TOQUE DETECTADO - VOLTANDO AO MENU!")
                            self.exit_requested = True
                            break  # Apenas para o loop, sem enviar sinal
                            
            except Exception as e:
                print(f"❌ Erro monitorando toque: {e}")
        
        self.monitor_thread = threading.Thread(target=monitor_touch)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def should_exit(self):
        """Verifica se deve sair"""
        return self.exit_requested
        
    def stop(self):
        """Para o monitoramento"""
        self.running = False
        print("🛑 Touch monitor parado")

# Instância global
touch_exit = TouchExit()

def setup_touch_exit():
    """Configura detecção de toque para sair"""
    # Removido signal handlers que podem causar conflito
    touch_exit.start_monitoring()
    return touch_exit
