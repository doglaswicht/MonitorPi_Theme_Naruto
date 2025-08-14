#!/usr/bin/env python3
"""Script de teste para verificar se o GIF de carregamento funciona."""

import time
import subprocess
import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, '/home/dw/painel/painelip')

from ui import PanelUI
from config import *

def test_gif_loading():
    """Testa o carregamento do GIF."""
    print("🎬 Testando GIF de carregamento...")
    
    # Cria UI
    ui = PanelUI(480, 320)
    print("✅ UI criada!")
    
    # Testa carregamento do GIF várias vezes
    for i in range(10):
        elapsed = i * 0.5  # Simula tempo passando
        print(f"⏱️  Frame {i+1}: elapsed = {elapsed:.1f}s")
        
        try:
            img = ui.create_gif_loading_screen(
                elapsed,
                "Teste GIF",
                f"Frame {i+1} - Teste de animação..."
            )
            print(f"✅ Frame {i+1} criado: {img.size}")
            
            # Salva uma amostra para verificar
            if i == 0:
                img.save(f"/tmp/test_gif_frame_{i}.png")
                print(f"💾 Frame salvo em /tmp/test_gif_frame_{i}.png")
                
        except Exception as e:
            print(f"❌ Erro no frame {i+1}: {e}")
            import traceback
            traceback.print_exc()
            break
        
        time.sleep(0.2)  # Simula refresh da tela
    
    print("🎉 Teste do GIF concluído!")

def test_nmap_simulation():
    """Simula o nmap para testar a integração."""
    print("🔍 Testando simulação do nmap...")
    
    # Comando nmap real mas com timeout curto
    cmd = ["nmap", "-T4", "--max-rtt-timeout", "100ms", "192.168.8.1"]
    print(f"📡 Comando: {' '.join(cmd)}")
    
    # Inicia processo
    start_time = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    ui = PanelUI(480, 320)
    frame_count = 0
    
    # Loop enquanto processo roda
    while proc.poll() is None:
        elapsed = time.time() - start_time
        print(f"⏱️  Frame {frame_count}: {elapsed:.1f}s - processo rodando")
        
        try:
            img = ui.create_gif_loading_screen(
                elapsed,
                "Teste Real", 
                f"Nmap rodando... {elapsed:.1f}s"
            )
            print(f"✅ Frame renderizado: {img.size}")
        except Exception as e:
            print(f"❌ Erro: {e}")
            break
            
        frame_count += 1
        time.sleep(0.2)
        
        # Proteção contra loop infinito
        if elapsed > 10:
            print("⏰ Timeout - terminando teste")
            proc.terminate()
            break
    
    # Processo terminou
    stdout, stderr = proc.communicate()
    elapsed = time.time() - start_time
    print(f"✅ Processo terminou após {elapsed:.1f}s")
    print(f"📊 Frames renderizados: {frame_count}")
    
    if frame_count > 0:
        print("🎉 GIF funcionou durante processo real!")
    else:
        print("❌ GIF não foi renderizado")

if __name__ == "__main__":
    print("🚀 Iniciando testes de GIF...")
    
    # Teste 1: GIF básico
    test_gif_loading()
    print("")
    
    # Teste 2: Integração com nmap
    test_nmap_simulation()
    
    print("\n🏁 Testes concluídos!")
