#!/usr/bin/env python3
"""Arquivo __init__.py para o pacote painelip."""

from models import DeviceInfo, NetworkScanResult
from network import NetworkDiscovery
from ui import PanelUI
from panel import NetworkPanel
from framebuffer import (
    find_framebuffer_by_name,
    get_framebuffer_geometry,
    write_image_to_framebuffer
)

__version__ = "2.0.0"
__author__ = "Painel IP Team"

__all__ = [
    "DeviceInfo",
    "NetworkScanResult", 
    "NetworkDiscovery",
    "PanelUI",
    "NetworkPanel",
    "find_framebuffer_by_name",
    "get_framebuffer_geometry", 
    "write_image_to_framebuffer"
]
