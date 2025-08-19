#!/usr/bin/env python3
"""Módulo para descoberta e análise de dispositivos de rede."""

import re
import subprocess
import ipaddress
from typing import Dict, List, Optional, Tuple
from models import DeviceInfo, NetworkScanResult

# Principais fabricantes de câmeras IP para identificação pelo vendor
CAMERA_VENDORS = [
    "hikvision",
    "dahua",
    "axis",
    "hanwha",
    "vivotek",
    "foscam",
    "bosch",
    "arlo",
    "grandstream",
    "mobotix",
    "avigilon",
]

class NetworkDiscovery:
    """Gerenciador de descoberta de dispositivos na rede."""
    
    def __init__(self, preferred_interfaces: List[str] = None):
        """
        Inicializa o descobridor de rede.
        
        Args:
            preferred_interfaces: Lista de interfaces preferidas
        """
        self.preferred_interfaces = preferred_interfaces or ["wlan0", "eth0"]
    
    def list_ipv4_interfaces(self) -> Dict[str, str]:
        """
        Lista todas as interfaces IPv4 ativas e seus CIDRs.
        
        Returns:
            Dicionário {interface: cidr}
        """
        result = {}
        try:
            output = subprocess.check_output(["ip", "-4", "-o", "addr", "show"], text=True)
            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 4 and parts[2] == "inet":
                    interface = parts[1]
                    cidr = parts[3]  # "192.168.1.15/24"
                    result[interface] = cidr
        except Exception:
            pass
        return result
    
    def get_best_interface(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Seleciona a melhor interface disponível.
        
        Returns:
            Tupla (interface, cidr) ou (None, None) se não encontrar
        """
        interfaces = self.list_ipv4_interfaces()
        
        # Tenta interfaces preferidas primeiro
        for iface in self.preferred_interfaces:
            if iface in interfaces:
                return iface, interfaces[iface]
        
        # Se não encontrou preferida, pega a primeira disponível
        if interfaces:
            first_iface = next(iter(interfaces.keys()))
            return first_iface, interfaces[first_iface]
        
        return None, None
    
    def cidr_to_network(self, cidr: str) -> Optional[str]:
        """
        Converte CIDR para rede (ex: 192.168.1.15/24 -> 192.168.1.0/24).
        
        Args:
            cidr: String CIDR
            
        Returns:
            String da rede ou None em caso de erro
        """
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            return str(network.with_prefixlen)
        except Exception:
            return None
    
    def start_nmap_scan(self, network: str) -> Optional[subprocess.Popen]:
        """
        Inicia uma varredura nmap assíncrona.
        
        Args:
            network: Rede CIDR para escanear
            
        Returns:
            Processo subprocess ou None em caso de erro
        """
        if not network:
            return None
        
        cmd = ["nmap", "-sS", "-O", "-sV", "--version-intensity", "1", "-T4", "-p", "80,443,554,8080,8888,81,8554,9000,5000", network]
        try:
            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True
            )
            return proc
        except Exception:
            return None
    
    def parse_nmap_output(self, text: str) -> List[DeviceInfo]:
        """
        Converte a saída do nmap em lista de DeviceInfo.
        
        Args:
            text: Saída do comando nmap
            
        Returns:
            Lista de dispositivos encontrados
        """
        devices: List[DeviceInfo] = []
        current_device: Optional[DeviceInfo] = None
        parsing_ports = False

        def mark_camera(device: DeviceInfo) -> None:
            """Define a flag is_camera se portas ou vendor indicarem câmera."""
            if 80 in device.open_ports or 554 in device.open_ports:
                device.is_camera = True
                return
            vendor_lower = device.vendor.lower()
            if any(v in vendor_lower for v in CAMERA_VENDORS):
                device.is_camera = True

        for line in text.splitlines():
            line = line.strip()
            
            # Início de novo dispositivo
            scan_match = re.search(r"Nmap scan report for (.*)", line)
            if scan_match:
                if current_device:
                    mark_camera(current_device)
                    devices.append(current_device)
                
                token = scan_match.group(1).strip()
                current_device = DeviceInfo()
                parsing_ports = False
                
                # Verifica se tem hostname e IP no formato: hostname (ip)
                ip_match = re.search(r"\(([0-9.]+)\)$", token)
                if ip_match:
                    current_device.ip = ip_match.group(1)
                    host = token[:ip_match.start()].strip()
                    if host and not re.match(r"^[0-9.]+$", host):
                        current_device.hostname = host
                else:
                    # Token é apenas IP ou apenas hostname
                    if re.match(r"^[0-9.]+$", token):
                        current_device.ip = token
                    else:
                        current_device.hostname = token
                continue
            
            if not current_device:
                continue
            
            if line.startswith("PORT"):
                parsing_ports = True
                continue

            if parsing_ports:
                # Tenta capturar informações de porta e serviço (incluindo versões)
                port_match = re.match(r"(\d+)/\w+\s+(\w+)\s+(.+)", line)
                if port_match:
                    port = int(port_match.group(1))
                    state = port_match.group(2)
                    service_info = port_match.group(3).strip()
                    if state == "open":
                        # Pega apenas o nome do serviço (antes do espaço, se houver)
                        service = service_info.split()[0] if service_info else "unknown"
                        current_device.open_ports[port] = service
                    continue
                else:
                    parsing_ports = False
            # Informações MAC
            if line.startswith("MAC Address:"):
                parts = line.split()
                if len(parts) >= 3:
                    current_device.mac = parts[2]
                if len(parts) > 3:
                    current_device.vendor = " ".join(parts[3:]).strip("()")
            
            # Informações do sistema operacional
            elif line.startswith("OS details:"):
                current_device.os = line.split("OS details:", 1)[1].strip()
            elif line.startswith("Running:") and not current_device.os:
                current_device.os = line.split("Running:", 1)[1].strip()
        
        # Adiciona o último dispositivo
        if current_device:
            mark_camera(current_device)
            devices.append(current_device)
        
        return self._deduplicate_devices(devices)
    
    def _deduplicate_devices(self, devices: List[DeviceInfo]) -> List[DeviceInfo]:
        """
        Remove dispositivos duplicados baseado no IP.
        
        Args:
            devices: Lista de dispositivos
            
        Returns:
            Lista de dispositivos únicos ordenada por IP
        """
        unique_devices: Dict[str, DeviceInfo] = {}
        
        for device in devices:
            if device.ip:
                unique_devices[device.ip] = device
        
        # Ordena por IP
        sorted_devices = sorted(
            unique_devices.values(), 
            key=lambda d: tuple(int(x) for x in d.ip.split("."))
        )
        
        return sorted_devices
