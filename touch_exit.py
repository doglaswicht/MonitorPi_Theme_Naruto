#!/usr/bin/env python3
"""
Módulo de detecção de toque para sair de scripts
Detecta toque na tela e permite retornar ao menu principal
"""

import struct
import time
import threading
import signal
import sys

TOUCH_DEVICE = '/dev/input/event0'

class TouchExit:
    def __init__(self):
        self.exit_requested = False
        self.monitor_thread = None
        self.running = True
        
    def start_monitoring(self):
        """Inicia monitoramento de toque em thread separada"""
        print("👆 Toque na tela para voltar ao menu principal...")
        
        def monitor_touch():
            try:
                with open(TOUCH_DEVICE, 'rb') as f:
                    while self.running and not self.exit_requested:
                        data = f.read(24)
                        if len(data) < 24:
                            time.sleep(0.01)
                            continue
                            
                        sec, usec, type_, code, value = struct.unpack('llHHi', data)
                        
                        # Detecta toque
                        if type_ == 3 and code == 24 and value > 50:
                            print("🔴 TOQUE DETECTADO - VOLTANDO AO MENU!")
                            self.exit_requested = True
                            # Envia sinal para o processo principal
                            import os
                            os.kill(os.getpid(), signal.SIGTERM)
                            break
                            
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

# Instância global
touch_exit = TouchExit()

def setup_touch_exit():
    """Configura detecção de toque para sair"""
    
    def signal_handler(signum, frame):
        print("\n🔴 SAINDO...")
        touch_exit.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    touch_exit.start_monitoring()
    
    return touch_exit
