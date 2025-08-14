#!/usr/bin/env python3
"""Interface gráfica para o painel de dispositivos."""

import time
import math
from datetime import datetime
from typing import List, Tuple, Union
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from models import DeviceInfo
from config import *


class PanelUI:
    """Gerenciador da interface do painel."""
    
    def __init__(self, width: int, height: int):
        """
        Inicializa a UI do painel.
        
        Args:
            width: Largura da tela
            height: Altura da tela
        """
        self.width = width
        self.height = height
        self._load_fonts()
        self.loading_gif_frames: List[Image.Image] = []
        self.loading_gif_durations: List[int] = []
    
    def _load_fonts(self) -> None:
        """Carrega as fontes necessárias."""
        try:
            self.font_title = ImageFont.truetype(FONT_TITLE_PATH, FONT_TITLE_SIZE)
            self.font_text = ImageFont.truetype(FONT_TEXT_PATH, FONT_TEXT_SIZE)
            self.font_small = ImageFont.truetype(FONT_TEXT_PATH, FONT_SMALL_SIZE)
        except Exception:
            # Fallback para fonte padrão
            self.font_title = ImageFont.load_default()
            self.font_text = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
    
    def create_loading_screen(self, step: int, title: str, info: str) -> Image.Image:
        """
        Cria uma tela de carregamento com animação de pontos.
        
        Args:
            step: Passo da animação
            title: Título principal
            info: Informação adicional
            
        Returns:
            Imagem PIL da tela de carregamento
        """
        img = Image.new("RGB", (self.width, self.height), COLOR_BACKGROUND)
        draw = ImageDraw.Draw(img)
        
        # Título
        #draw.text((10, 8), title, fill=COLOR_TITLE, font=self.font_title)
        
        # Informação
        draw.text((10, 40), info, fill=COLOR_INFO, font=self.font_text)
        
        # Animação de 3 pontos
        self._draw_loading_dots(draw, step)
        
        # Desenha a hora atual
        self._draw_current_time(draw)
        
        return img

    def _load_loading_gif(self) -> None:
        if self.loading_gif_frames:
            return
        try:
            with Image.open(LOADING_GIF_PATH) as im:
                for frame in ImageSequence.Iterator(im):
                    self.loading_gif_frames.append(frame.convert("RGB"))
                    self.loading_gif_durations.append(frame.info.get("duration", 100))
        except Exception:
            self.loading_gif_frames = []
            self.loading_gif_durations = []

    def create_gif_loading_screen(self, elapsed: float, title: str, info: str) -> Image.Image:
        """Cria uma tela de carregamento usando um GIF animado."""
        self._load_loading_gif()

        if not self.loading_gif_frames:
            return self.create_loading_screen(0, title, info)

        durations = self.loading_gif_durations or [100] * len(self.loading_gif_frames)
        total = sum(durations)
        elapsed_ms = int((elapsed * 1000) % total)
        cumulative = 0
        frame_index = 0
        for i, d in enumerate(durations):
            cumulative += d
            if elapsed_ms < cumulative:
                frame_index = i
                break
        frame = self.loading_gif_frames[frame_index].copy()
        frame.thumbnail((self.width, self.height))
        x = (self.width - frame.width) // 2
        y = (self.height - frame.height) // 2

        img = Image.new("RGB", (self.width, self.height), COLOR_BACKGROUND)
        img.paste(frame, (x, y))
        draw = ImageDraw.Draw(img)
        draw.text((10, 8), title, fill=COLOR_TITLE, font=self.font_title)
        draw.text((10, 40), info, fill=COLOR_INFO, font=self.font_text)
        self._draw_current_time(draw)
        
        return img
    
    def _draw_loading_dots(self, draw: ImageDraw.Draw, step: int) -> None:
        """Desenha pontos animados de carregamento."""
        x_start = 10
        y_pos = 70
        dot_size = 8
        dot_spacing = 20
        
        for i in range(3):
            x = x_start + (i * dot_spacing)
            # Animação cíclica dos pontos
            alpha = (step + i * 10) % 30
            if alpha < 15:
                color = COLOR_LOADING_DOTS
            else:
                color = "darkred"
            
            draw.ellipse(
                [x, y_pos, x + dot_size, y_pos + dot_size], 
                fill=color
            )
    
    def create_device_list_screen(
        self, 
        title: str, 
        interface: str, 
        ip_display: str, 
        devices: List[DeviceInfo], 
        page: int, 
        page_time: float, 
        page_started: float
    ) -> Tuple[Image.Image, Union[int, Tuple[int, float]]]:
        """
        Cria uma tela com lista paginada de dispositivos.
        
        Args:
            title: Título da tela
            interface: Interface de rede
            ip_display: IP para exibição
            devices: Lista de dispositivos
            page: Página atual
            page_time: Tempo por página
            page_started: Timestamp do início da página
            
        Returns:
            Nova página ou tupla (página, timestamp)
        """
        img = Image.new("RGB", (self.width, self.height), COLOR_BACKGROUND)
        draw = ImageDraw.Draw(img)
        
        # Cabeçalho
        self._draw_header(draw, title, interface, ip_display, len(devices))
        
        # Lista de dispositivos
        if devices:
            devices_per_page = self._calculate_devices_per_page()
            total_pages = math.ceil(len(devices) / devices_per_page)
            
            # Controle de paginação
            current_time = time.time()
            if current_time - page_started >= page_time:
                page = (page + 1) % total_pages
                page_started = current_time
            
            # Desenha dispositivos da página atual
            start_idx = page * devices_per_page
            end_idx = min(start_idx + devices_per_page, len(devices))
            page_devices = devices[start_idx:end_idx]
            
            self._draw_device_list(draw, page_devices, start_idx)
            
            # Indicador de página
            if total_pages > 1:
                self._draw_page_indicator(draw, page + 1, total_pages)
            
            # Desenha a hora atual
            self._draw_current_time(draw)
            
            return img, (page, page_started)
        else:
            # Nenhum dispositivo encontrado
            self._draw_no_devices_message(draw)
            
            # Desenha a hora atual mesmo quando não há dispositivos
            self._draw_current_time(draw)
            
            return img, page
    
    def _draw_header(
        self, 
        draw: ImageDraw.Draw, 
        title: str, 
        interface: str, 
        ip_display: str, 
        device_count: int
    ) -> None:
        """Desenha o cabeçalho da tela."""
        # Título principal
        draw.text((10, 8), title, fill=COLOR_TITLE, font=self.font_title)
        
        # Informações da rede
        info_text = f"{interface}: {ip_display} ({device_count} dispositivos)"
        draw.text((10, 40), info_text, fill=COLOR_INFO, font=self.font_text)
    
    def _calculate_devices_per_page(self) -> int:
        """Calcula quantos dispositivos cabem por página."""
        if not DEVICES_PER_PAGE_AUTO:
            return DEVICES_PER_PAGE_MANUAL
        
        # Reserva espaço para cabeçalho e indicador de página
        header_height = 70
        footer_height = 20
        available_height = self.height - header_height - footer_height
        
        # Usa altura configurável por dispositivo
        return max(1, available_height // DEVICE_LINE_HEIGHT)
    
    def _draw_device_list(
        self, 
        draw: ImageDraw.Draw, 
        devices: List[DeviceInfo], 
        start_idx: int
    ) -> None:
        """Desenha a lista de dispositivos."""
        y_start = 70
        
        for i, device in enumerate(devices):
            y_pos = y_start + (i * DEVICE_LINE_HEIGHT)
            device_text = self._format_device_info(device, start_idx + i + 1)
            draw.text((DEVICE_TEXT_INDENT, y_pos), device_text, fill=COLOR_TEXT, font=self.font_small)
    
    def _format_device_info(self, device: DeviceInfo, index: int) -> str:
        """Formata as informações do dispositivo para exibição."""
        parts = []
        
        # Número do dispositivo
        if SHOW_DEVICE_INDEX:
            parts.append(f"{index:2d}.")
        
        # Nome do dispositivo (hostname)
        if SHOW_HOSTNAME and device.hostname:
            hostname = device.hostname[:MAX_HOSTNAME_LENGTH]
            parts.append(hostname)
        
        # Endereço IP
        if SHOW_IP and device.ip:
            parts.append(device.ip)
        
        # MAC Address (últimos caracteres)
        if SHOW_MAC and device.mac:
            parts.append(device.mac[-8:])
        
        # Vendor/Fabricante
        if SHOW_VENDOR and device.vendor:
            vendor = device.vendor[:MAX_VENDOR_LENGTH]
            parts.append(f"({vendor})")
        
        # Sistema Operacional
        if SHOW_OS and device.os:
            os_info = device.os[:MAX_OS_LENGTH]
            parts.append(f"OS:{os_info}")
        
        return " ".join(parts)
    
    def _draw_page_indicator(self, draw: ImageDraw.Draw, current_page: int, total_pages: int) -> None:
        """Desenha o indicador de página."""
        indicator_text = f"Página {current_page}/{total_pages}"
        text_width = draw.textlength(indicator_text, font=self.font_small)
        x_pos = self.width - text_width - 10
        y_pos = self.height - 20
        
        draw.text((x_pos, y_pos), indicator_text, fill=COLOR_INFO, font=self.font_small)
    
    def _draw_current_time(self, draw: ImageDraw.Draw) -> None:
        """Desenha a hora atual no canto inferior direito."""
        if not SHOW_TIME:
            return
            
        # Formata a hora atual usando a configuração
        current_time = datetime.now().strftime(TIME_FORMAT)
        
        # Calcula posição no canto inferior direito
        text_width = draw.textlength(current_time, font=self.font_small)
        x_pos = self.width - text_width - 10
        y_pos = self.height - 40  # Um pouco acima do indicador de página
        
        # Desenha a hora
        draw.text((x_pos, y_pos), current_time, fill=TIME_COLOR, font=self.font_small)
    
    def _draw_no_devices_message(self, draw: ImageDraw.Draw) -> None:
        """Desenha mensagem quando não há dispositivos."""
        message = "Nenhum dispositivo encontrado"
        text_width = draw.textlength(message, font=self.font_text)
        x_pos = (self.width - text_width) // 2
        y_pos = self.height // 2
        
        draw.text((x_pos, y_pos), message, fill=COLOR_TEXT, font=self.font_text)
