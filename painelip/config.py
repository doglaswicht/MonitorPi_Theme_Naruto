#!/usr/bin/env python3
"""Configurações do painel de dispositivos de rede."""

import os
# ===== CONFIGURAÇÕES DO DISPLAY =====
ROTATE_DEG = 0               # 0, 90, 180, 270
FB_TARGET = "fb_ili9486"     # Nome do framebuffer alvo

# ===== CONFIGURAÇÕES DE REDE =====
SCAN_INTERVAL = 45           # Segundos entre varreduras nmap
PREF_IFACES = ["wlan0", "eth0"]  # Interfaces preferidas

# ===== CONFIGURAÇÕES DE UI =====
PAGE_TIME = 3                # Segundos por página na lista
TITLE = "Dispositivos na rede"
LOADING_TITLE = "Scan Ninja..."  # Título durante carregamento/GIF
DOT_INTERVAL = 0.3           # Intervalo para animação dos pontos
LOADING_GIF_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "gifs2", "kakashicute.gif")
MIN_LOADING_TIME = 5         # Tempo mínimo (segundos) para mostrar o GIF de carregamento
# ===== CONFIGURAÇÕES DE EXIBIÇÃO DE DISPOSITIVOS =====
SHOW_DEVICE_INDEX = True     # Mostra número do dispositivo (1., 2., etc.)
SHOW_HOSTNAME = True         # Mostra nome do dispositivo
SHOW_IP = True              # Mostra endereço IP
SHOW_MAC = True             # Mostra endereço MAC (últimos 8 caracteres)
SHOW_VENDOR = True          # Mostra fabricante do dispositivo
SHOW_OS = True              # Mostra sistema operacional
MAX_HOSTNAME_LENGTH = 20    # Tamanho máximo do nome do dispositivo
MAX_VENDOR_LENGTH = 15      # Tamanho máximo do nome do fabricante
MAX_OS_LENGTH = 25          # Tamanho máximo da descrição do OS

# ===== LAYOUT DA LISTA =====
DEVICES_PER_PAGE_AUTO = True # Calcula automaticamente quantos dispositivos por página
DEVICES_PER_PAGE_MANUAL = 8  # Número fixo de dispositivos por página (se AUTO = False)
DEVICE_LINE_HEIGHT = 25      # Altura de cada linha de dispositivo
DEVICE_TEXT_INDENT = 10      # Indentação do texto dos dispositivos

# ===== CONFIGURAÇÕES DE TEMPO =====
SHOW_TIME = True             # Mostra hora no canto inferior direito
TIME_FORMAT = "%H:%M:%S"     # Formato da hora (24h com segundos)
# Outros formatos possíveis:
# "%H:%M" - 24h sem segundos (14:30)
# "%I:%M %p" - 12h com AM/PM (2:30 PM)
# "%d/%m %H:%M" - Data e hora (14/08 14:30)
TIME_COLOR = "cyan"          # Cor da hora (mesma cor das informações)

# ===== CONFIGURAÇÕES DE FONTS =====
FONT_TITLE_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_TEXT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_TITLE_SIZE = 26
FONT_TEXT_SIZE = 16
FONT_SMALL_SIZE = 12

# ===== CORES =====
COLOR_BACKGROUND = "black"
COLOR_TITLE = "yellow"
COLOR_INFO = "cyan"
COLOR_TEXT = "white"
COLOR_LOADING_DOTS = "red"
