#!/usr/bin/env python3
"""Modelos de dados para o painel de dispositivos."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DeviceInfo:
    """Informações básicas sobre um dispositivo descoberto na rede."""
    ip: str = ""
    mac: str = ""
    vendor: str = ""
    hostname: str = ""
    os: str = ""
    open_ports: dict[int, str] = field(default_factory=dict)
    is_camera: bool = False

    def __str__(self) -> str:
        """Representação em string do dispositivo."""
        parts = []
        if self.hostname:
            parts.append(f"Host: {self.hostname}")
        if self.ip:
            parts.append(f"IP: {self.ip}")
        if self.mac:
            parts.append(f"MAC: {self.mac}")
        if self.vendor:
            parts.append(f"Vendor: {self.vendor}")
        if self.os:
            parts.append(f"OS: {self.os}")
        return " | ".join(parts) if parts else "Dispositivo vazio"

    @property
    def display_name(self) -> str:
        """Nome para exibição (hostname ou IP)."""
        return self.hostname or self.ip or "Desconhecido"


@dataclass
class NetworkScanResult:
    """Resultado de uma varredura de rede."""
    devices: List[DeviceInfo]
    scan_time: float
    interface: str
    network: str
    success: bool = True
    error_message: str = ""
