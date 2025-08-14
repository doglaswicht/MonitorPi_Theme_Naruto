#!/usr/bin/env python3
"""Gerenciador simplificado para execução de scripts do menu."""

import os
import sys
import time
import struct
import signal
import subprocess
import threading
from threading import Lock

# Configurações
TOUCH_DEVICE = "/dev/input/event0"
FRAMEBUFFER = "/dev/fb0"
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320

# Variáveis globais
current_process = None
process_lock = Lock()
should_return = False

def clear_screen():
    """Limpa a tela."""
    try:
        with open(FRAMEBUFFER, 'wb') as fb:
            fb.write(b'\x00\x00' * (SCREEN_WIDTH * SCREEN_HEIGHT))
    except:
        pass

def kill_process_group(pid):
    """Mata um grupo de processos."""
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        time.sleep(0.5)
        os.killpg(os.getpgid(pid), signal.SIGKILL)
    except:
        pass

def monitor_touch():
    """Monitora toque para voltar ao menu."""
    global should_return
    
    try:
        # Aguarda 3 segundos antes de aceitar toque
        time.sleep(3.0)
        print("👆 Toque na tela para voltar ao menu...")
        
        last_touch_time = 0
        
        with open(TOUCH_DEVICE, 'rb') as f:
            while not should_return:
                data = f.read(24)
                if len(data) < 24:
                    continue
                    
                sec, usec, type_, code, value = struct.unpack('llHHi', data)
                
                if type_ == 3 and code == 24 and value > 200:
                    current_time = time.time()
                    
                    # Debounce: ignora toques muito rápidos (< 1 segundo)
                    if current_time - last_touch_time < 1.0:
                        print("⚡ Toque muito rápido - ignorado")
                        continue
                        
                    last_touch_time = current_time
                    print("🔴 Toque detectado - saindo...")
                    should_return = True
                    break
                    
    except Exception as e:
        print(f"❌ Erro monitorando toque: {e}")
        should_return = True

def run_script(script_path, script_name):
    """Executa um script e aguarda toque para sair."""
    global current_process, should_return
    
    print(f"🚀 EXECUTANDO: {script_name}")
    clear_screen()
    
    try:
        # Muda para diretório do script
        script_dir = os.path.dirname(script_path) if os.path.dirname(script_path) else "/home/dw/painel"
        script_file = os.path.basename(script_path)
        
        os.chdir(script_dir)
        print(f"📁 Diretório: {script_dir}")
        print(f"📄 Script: {script_file}")
        
        # Executa script
        cmd = ["python3", script_file]
        print(f"⚡ Comando: {' '.join(cmd)}")
        
        current_process = subprocess.Popen(cmd, preexec_fn=os.setsid)
        print(f"✅ Processo iniciado (PID: {current_process.pid})")
        
        # Inicia monitor de toque
        should_return = False
        touch_thread = threading.Thread(target=monitor_touch)
        touch_thread.daemon = True
        touch_thread.start()
        
        # Aguarda até toque ou processo terminar
        while current_process.poll() is None and not should_return:
            time.sleep(0.1)
        
        # Para processo se ainda estiver rodando
        if current_process and current_process.poll() is None:
            print("🛑 Parando processo...")
            kill_process_group(current_process.pid)
        
        current_process = None
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    finally:
        # Limpa tela e força retorno ao menu
        print("🧹 Limpando tela...")
        clear_screen()
        time.sleep(1)
        
        # Mata qualquer processo restante
        if current_process:
            try:
                kill_process_group(current_process.pid)
            except:
                pass
        
        print("🔄 Voltando ao menu principal...")
        
        # Força limpeza adicional do framebuffer
        try:
            subprocess.run(["sudo", "dd", "if=/dev/zero", "of=/dev/fb0", "bs=307200", "count=1"], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

def main():
    """Função principal."""
    if len(sys.argv) != 3:
        print("Uso: python3 menu_manager.py <script_path> <script_name>")
        sys.exit(1)
    
    script_path = sys.argv[1]
    script_name = sys.argv[2]
    
    run_script(script_path, script_name)

if __name__ == "__main__":
    main()
