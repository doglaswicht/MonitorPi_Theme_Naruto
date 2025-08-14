#!/bin/bash
# 🚀 PAINEL TOUCHSCREEN - INICIALIZAÇÃO RÁPIDA
# 
# Script para iniciar o menu touchscreen com configuração automática

echo "🎯 PAINEL TOUCHSCREEN - MENU PRINCIPAL"
echo "======================================"

# Navega para o diretório correto
cd /home/dw/painel

# Verifica se os arquivos principais existem
if [ ! -f "touch_menu_visual.py" ]; then
    echo "❌ Arquivo principal não encontrado: touch_menu_visual.py"
    exit 1
fi

if [ ! -f "assets/kakashicute.gif" ]; then
    echo "❌ GIF não encontrado: assets/kakashicute.gif"
    exit 1
fi

# Mata processos anteriores se existirem
echo "🧹 Limpando processos anteriores..."
sudo pkill -f "python3.*painel" 2>/dev/null || true
sudo pkill -f "touch_menu_visual" 2>/dev/null || true

# Limpa framebuffer
echo "🖥️  Limpando tela..."
sudo dd if=/dev/zero of=/dev/fb0 bs=307200 count=1 2>/dev/null

# Pequena pausa para estabilizar
sleep 2

# Verifica se está rodando como root ou com sudo
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  Reiniciando com privilégios root..."
    sudo "$0" "$@"
    exit $?
fi

# Inicia o menu principal
echo "🚀 Iniciando menu touchscreen..."
echo ""
exec python3 touch_menu_visual.py
