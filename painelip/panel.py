#!/usr/bin/env python3
"""Módulo principal do painel de dispositivos de rede."""

import time
import subprocess
from typing import List, Optional
from config import *
from models import DeviceInfo
from framebuffer import (
    find_framebuffer_by_name, 
    get_framebuffer_geometry, 
    write_image_to_framebuffer
)
from network import NetworkDiscovery
from ui import PanelUI


class NetworkPanel:
    """Controlador principal do painel de dispositivos de rede."""
    
    def __init__(self):
        """Inicializa o painel."""
        self.discovery = NetworkDiscovery(PREF_IFACES)
        self.devices: List[DeviceInfo] = []
        self.scan_process: Optional[subprocess.Popen] = None
        
        # Estado da UI
        self.page = 0
        self.page_started = time.time()
        self.last_scan_end = 0.0
        self.loading_start = time.time()
        
        # Configuração do framebuffer
        self._setup_framebuffer()
        self.ui = PanelUI(self.width, self.height)
    
    def _setup_framebuffer(self) -> None:
        """Configura o framebuffer."""
        try:
            self.fb_device, self.fb_index = find_framebuffer_by_name(FB_TARGET)
            self.width, self.height, self.bpp, self.stride = get_framebuffer_geometry(self.fb_device)
            
            print(f"[fb] {self.fb_device}: {self.width}x{self.height} @{self.bpp}bpp stride={self.stride}")
        except Exception as e:
            raise RuntimeError(f"Erro ao configurar framebuffer: {e}")
    
    def _should_start_new_scan(self) -> bool:
        """Verifica se deve iniciar uma nova varredura."""
        return (self.scan_process is None and 
                time.time() - self.last_scan_end >= SCAN_INTERVAL)
    
    def _start_network_scan(self) -> None:
        """Inicia uma nova varredura de rede."""
        interface, cidr = self.discovery.get_best_interface()
        if not interface or not cidr:
            return
        
        network = self.discovery.cidr_to_network(cidr)
        if not network:
            return
        
        self.scan_process = self.discovery.start_nmap_scan(network)
        if self.scan_process:
            print(f"Iniciando varredura da rede {network} via {interface}")
            self.loading_start = time.time()
    
    def _update_scan_progress(self) -> None:
        """Atualiza o progresso da varredura em andamento."""
        if self.scan_process and self.scan_process.poll() is None:
            # Varredura ainda em andamento - NÃO tenta ler stdout durante execução
            # Isso permite que a UI continue responsiva
            pass
        elif self.scan_process:
            # Varredura terminou, mas verifica tempo mínimo de exibição
            elapsed_time = time.time() - self.loading_start
            if elapsed_time < MIN_LOADING_TIME:
                # Ainda não passou o tempo mínimo, continua mostrando GIF
                return
            
            # Tempo mínimo passou, processa resultados
            try:
                # Lê toda a saída do processo
                stdout, stderr = self.scan_process.communicate()
                if stdout:
                    text = stdout
                else:
                    text = ""
            except Exception:
                text = ""
            
            # Processa resultados
            self.devices = self.discovery.parse_nmap_output(text)
            
            # Reset estado
            self.last_scan_end = time.time()
            self.scan_process = None
            self.page = 0
            self.page_started = time.time()
            
            print(f"Varredura concluída: {len(self.devices)} dispositivos encontrados")
    
    def _render_current_screen(self) -> None:
        """Renderiza a tela atual."""
        interface, cidr = self.discovery.get_best_interface()
        ip_display = cidr.split('/')[0] if cidr else "N/A"
        
        # Verifica se deve mostrar tela de carregamento
        show_loading = False
        
        if self.scan_process and self.scan_process.poll() is None:
            # Processo ainda rodando
            show_loading = True
        elif self.scan_process:
            # Processo terminou, mas verifica tempo mínimo
            elapsed_time = time.time() - self.loading_start
            if elapsed_time < MIN_LOADING_TIME:
                show_loading = True
        
        if show_loading:
            # Tela de carregamento durante varredura com GIF
            subtitle = f"{interface}: {ip_display}" if interface else "Configurando rede..."
            elapsed = time.time() - self.loading_start
            img = self.ui.create_gif_loading_screen(
                elapsed,
                LOADING_TITLE,
                subtitle + "  (escaneando...)"
            )
        else:
            # Tela de lista de dispositivos
            img, result = self.ui.create_device_list_screen(
                TITLE,
                interface or "N/A",
                ip_display,
                self.devices,
                self.page,
                PAGE_TIME,
                self.page_started
            )
            
            if isinstance(result, tuple):
                self.page, self.page_started = result
            else:
                self.page = result
        
        # Aplica rotação se necessário
        if ROTATE_DEG:
            img = img.rotate(ROTATE_DEG, expand=False)
        
        # Escreve no framebuffer
        write_image_to_framebuffer(self.fb_device, img, self.bpp, self.stride)
    
    def run(self) -> None:
        """Loop principal do painel."""
        print(f"Iniciando painel de dispositivos de rede...")
        print(f"Display: {self.width}x{self.height}, Intervalo: {SCAN_INTERVAL}s")
        
        try:
            while True:
                # Verifica se deve iniciar nova varredura
                if self._should_start_new_scan():
                    self._start_network_scan()
                
                # Atualiza progresso da varredura
                self._update_scan_progress()
                
                # Renderiza tela
                self._render_current_screen()
                
                # Pausa para animação suave e economia de CPU
                time.sleep(0.2)
                
        except KeyboardInterrupt:
            print("\\nEncerrando painel...")
        except Exception as e:
            print(f"Erro no painel: {e}")
            raise
