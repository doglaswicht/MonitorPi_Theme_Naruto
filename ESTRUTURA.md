# 📁 ESTRUTURA DO PROJETO PAINEL TOUCHSCREEN

## 🎯 ARQUIVOS PRINCIPAIS (Raiz)

### 🚀 Scripts Funcionais
- **`touch_menu_visual.py`** - ⭐ **MENU PRINCIPAL** - Menu touchscreen com GIF e 3 botões
- **`painelv3.py`** - 📊 Monitor do sistema (CPU, Memória, Temperatura)
- **`painel_gif.py`** - 🎬 Exibidor de GIFs animados
- **`README.md`** - 📖 Documentação principal do projeto

### 📂 Subprojetos
- **`painelip/`** - 🌐 Monitor de rede (IPs, dispositivos conectados)
- **`painel_c/`** - 🔧 Implementações em linguagem C

## 📚 DIRETÓRIOS ORGANIZADOS

### 📖 `/docs/` - Documentação
- `README_BASICO.md` - Guia básico de uso
- `README_MENU.md` - Documentação do sistema de menu
- `README_STATUS.md` - Status do desenvolvimento
- `README_TOUCH_FIX.md` - Correções de calibração touch

### 🎨 `/assets/` - Recursos Visuais
- `kakashicute.gif` - GIF principal do menu (58 frames)
- `kakashicute.png` - Imagem estática
- `gifs2/` - Outros GIFs (obito.gif, sasuke.gif, etc.)

### 🔧 `/debug/` - Ferramentas de Debug
- `debug_coordenadas.py` - 🎯 Mapa visual de coordenadas touchscreen
- `teste_mapeamento.py` - 📍 Teste de mapeamento de botões
- `limpar_sistema.sh` - 🧹 Script de limpeza do sistema

### 📦 `/archive/` - Arquivos Arquivados
- Diretório para versões antigas ou testes (vazio atualmente)

## 🎮 COMO USAR

### ▶️ Executar Menu Principal
```bash
cd /home/dw/painel
sudo python3 touch_menu_visual.py
```

### 🔧 Debug de Coordenadas
```bash
cd /home/dw/painel/debug
sudo python3 debug_coordenadas.py
```

### 🧹 Limpeza do Sistema
```bash
cd /home/dw/painel/debug
chmod +x limpar_sistema.sh
sudo ./limpar_sistema.sh
```

## ⚙️ ESPECIFICAÇÕES TÉCNICAS

### 🖥️ Hardware
- **Display**: 3.5" TFT 480x320 pixels
- **Touchscreen**: ADS7846 (/dev/input/event0)
- **Formato**: RGB565, 16bpp, stride=960

### 🎯 Coordenadas Touchscreen
- **Raw Range**: X(600-3600), Y(400-3800)
- **Mapeamento**: Rotação 270° + ajustes de calibração
- **Botões**: 3 áreas verticais (180x100 pixels cada)

### 🎬 Animação
- **GIF**: 58 frames, 10 FPS
- **Lado Esquerdo**: 240px largura para GIF
- **Lado Direito**: 240px largura para botões

## 📊 STATUS DO PROJETO

✅ **COMPLETO** - Menu touchscreen funcional  
✅ **COMPLETO** - Calibração de coordenadas  
✅ **COMPLETO** - Integração de 3 scripts  
✅ **COMPLETO** - Sistema de debug  
✅ **COMPLETO** - Organização de arquivos  

---
**🎊 PROJETO FINALIZADO - AGOSTO 2025**
