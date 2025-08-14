#!/bin/bash
# Script para limpeza completa do sistema de painel

echo "🧹 LIMPEZA COMPLETA DO SISTEMA"
echo "================================"

# Para todos os processos Python relacionados
echo "🛑 Parando todos os processos Python..."
sudo pkill -f python3 2>/dev/null
sudo pkill -f menu 2>/dev/null
sudo pkill -f painel 2>/dev/null

# Aguarda um momento
sleep 1

# Limpa completamente o framebuffer
echo "🖥️  Limpando tela (framebuffer)..."
sudo dd if=/dev/zero of=/dev/fb0 bs=1024 count=300 2>/dev/null

# Verifica se ainda há processos rodando
PROCESSES=$(ps aux | grep -E "python.*painel|python.*menu" | grep -v grep | wc -l)

if [ $PROCESSES -eq 0 ]; then
    echo "✅ Sistema limpo! Nenhum processo interferindo."
    echo "📺 Tela limpa (preta)."
    echo ""
    echo "🚀 Agora você pode executar qualquer script:"
    echo "   sudo python3 painelv3.py"
    echo "   sudo python3 painel_gif.py"  
    echo "   cd painelip && sudo python3 painel_ips.py"
else
    echo "⚠️  Ainda há $PROCESSES processo(s) rodando:"
    ps aux | grep -E "python.*painel|python.*menu" | grep -v grep
fi
