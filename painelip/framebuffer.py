#!/usr/bin/env python3
"""Utilidades para manipulação do framebuffer."""

import os
import re
import glob
import subprocess
from typing import Tuple, Optional
import numpy as np
from PIL import Image


def read_sys_file(path: str, as_int: bool = False, default=None):
    """Lê um arquivo do sistema de forma segura."""
    try:
        with open(path, 'r') as f:
            content = f.read().strip()
        return int(content) if as_int else content
    except Exception:
        return default


def find_framebuffer_by_name(target: str = "fb_ili9486") -> Tuple[str, int]:
    """
    Encontra o dispositivo framebuffer pelo nome.
    
    Args:
        target: Nome do framebuffer alvo
        
    Returns:
        Tupla com (caminho_device, índice)
        
    Raises:
        RuntimeError: Se o framebuffer não for encontrado
    """
    for path in glob.glob("/sys/class/graphics/fb*/name"):
        try:
            with open(path, 'r') as f:
                name = f.read().strip()
            if name == target:
                fb = os.path.basename(os.path.dirname(path))  # "fb2", "fb0", etc.
                return f"/dev/{fb}", int(fb[2:])
        except Exception:
            continue
    
    raise RuntimeError(f"{target} não encontrado (confira dtoverlay=tft35a e SPI).")


def get_framebuffer_geometry(fbdev: str) -> Tuple[int, int, int, int]:
    """
    Obtém a geometria do framebuffer.
    
    Args:
        fbdev: Caminho para o dispositivo framebuffer
        
    Returns:
        Tupla com (largura, altura, bits_por_pixel, stride)
    """
    idx = int(os.path.basename(fbdev)[2:])
    width = height = None
    
    # Tenta obter geometria via fbset
    try:
        output = subprocess.check_output(["fbset", "-s", "-fb", fbdev], text=True)
        match = re.search(r"geometry\s+(\d+)\s+(\d+)", output)
        if match:
            width, height = int(match.group(1)), int(match.group(2))
    except Exception:
        pass
    
    # Fallback para virtual_size
    if not (width and height):
        vs = read_sys_file(f"/sys/class/graphics/fb{idx}/virtual_size")
        if vs and "," in vs:
            a, b = vs.replace(" ", "").split(",")
            width, height = int(a), int(b)
    
    # Fallback padrão
    if not (width and height):
        width, height = 320, 480  # Típico do ILI9486
    
    # Obtém bits por pixel
    bpp = read_sys_file(f"/sys/class/graphics/fb{idx}/bits_per_pixel", as_int=True, default=16)
    
    # Obtém stride
    stride = (read_sys_file(f"/sys/class/graphics/fb{idx}/stride", as_int=True) or
              read_sys_file(f"/sys/class/graphics/fb{idx}/fb_fix/line_length", as_int=True) or
              width * (bpp // 8))
    
    return width, height, bpp, stride


def convert_rgb_to_rgb565_le(pil_img: Image.Image) -> np.ndarray:
    """
    Converte uma imagem PIL RGB para formato RGB565 little-endian.
    
    Args:
        pil_img: Imagem PIL no formato RGB
        
    Returns:
        Array numpy com dados RGB565 em formato [H,W,2]
    """
    arr = np.asarray(pil_img, dtype=np.uint8)  # [H,W,3]
    r = (arr[..., 0] >> 3).astype(np.uint16)
    g = (arr[..., 1] >> 2).astype(np.uint16)
    b = (arr[..., 2] >> 3).astype(np.uint16)
    
    rgb565 = (r << 11) | (g << 5) | b
    lo = (rgb565 & 0xFF).astype(np.uint8)
    hi = (rgb565 >> 8).astype(np.uint8)
    
    return np.stack([lo, hi], axis=-1)  # [H,W,2]


def write_image_to_framebuffer(fbdev: str, img: Image.Image, bpp: int, stride: int) -> None:
    """
    Escreve uma imagem PIL no framebuffer.
    
    Args:
        fbdev: Caminho para o dispositivo framebuffer
        img: Imagem PIL a ser escrita
        bpp: Bits por pixel
        stride: Stride (bytes por linha)
    """
    width, height = img.size
    bytespp = bpp // 8
    
    if bpp == 16:
        # Conversão para RGB565
        rgb565 = convert_rgb_to_rgb565_le(img)  # [H,W,2]
        row_bytes = width * 2
        flat = rgb565.reshape(height, row_bytes)
        
        buf = bytearray()
        for y in range(height):
            line = flat[y].tobytes()
            buf += line
            if stride > row_bytes:
                buf += b"\x00" * (stride - row_bytes)
        payload = bytes(buf)
    else:
        # Outros formatos de pixel
        raw = img.tobytes()
        row_bytes = width * bytespp
        
        buf = bytearray()
        for y in range(height):
            start = y * row_bytes
            buf += raw[start:start + row_bytes]
            if stride > row_bytes:
                buf += b"\x00" * (stride - row_bytes)
        payload = bytes(buf)
    
    with open(fbdev, "wb") as f:
        f.write(payload)
