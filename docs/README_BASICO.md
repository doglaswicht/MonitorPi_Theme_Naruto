# 🥷 Menu Básico - Painel Ninja

Sistema simplificado de menu para Raspberry Pi com 3 funcionalidades principais.

## 📋 Funcionalidades

### 🌐 Painel IP
- **Descrição**: Monitor de dispositivos na rede com animação GIF ninja
- **Arquivo**: `painelip/painel_ips.py`
- **Recursos**: Descoberta de rede, GIF Kakashi, tempo real

### 📊 Painel V3  
- **Descrição**: Painel principal de monitoramento do sistema
- **Arquivo**: `painelv3.py`
- **Recursos**: Monitoramento completo do Raspberry Pi

### 🎬 Painel GIF
- **Descrição**: Visualizador de GIFs animados
- **Arquivo**: `painel_gif.py`
- **Recursos**: Reprodução de GIFs no framebuffer

## 🚀 Como Usar

### Menu por Linha de Comando
```bash
# Menu simples no terminal
python3 menu_basico.py
```

### Menu Touchscreen
```bash
# Menu com interface gráfica touchscreen (requer root)
sudo python3 menu_touch_basico.py
```

## 🎮 Navegação

### Menu Terminal
- **1**: Executa Painel IP
- **2**: Executa Painel V3  
- **3**: Executa Painel GIF
- **0**: Sair

### Menu Touchscreen
- **Toque nos botões**: Executa aplicação
- **Ctrl+C**: Sair do menu

## ⚙️ Configuração

### Arquivos Principais
- **`menu_basico.py`**: Menu por linha de comando
- **`menu_touch_basico.py`**: Menu touchscreen
- **`menu_apps.py`**: Definições das 3 aplicações
- **`menu_config.py`**: Configurações de display e touch

### Personalização
Edite `menu_apps.py` para alterar comandos ou descrições:

```python
MenuApp(
    id="painel_ip",
    name="🌐 Painel IP",
    description="Monitor de dispositivos na rede",
    command=["python3", "painelip/painel_ips.py"],
    requires_sudo=True
)
```

## 🔧 Instalação

### Dependências
```bash
sudo apt install python3-pip python3-pil
pip3 install pillow numpy
```

### Permissões
```bash
# Para usar touchscreen
chmod +x menu_touch_basico.py
chmod +x menu_basico.py

# Para framebuffer (necessário para interface gráfica)
sudo usermod -a -G video $USER
```

## 📱 Interface Touchscreen

### Layout
- **Header**: Título e subtítulo
- **Botões**: 3 botões lado a lado com ícones
- **Footer**: Instruções e hora atual

### Calibração Touch
Edite `menu_config.py` se necessário:
```python
TOUCH_CONFIG = {
    "device": "/dev/input/event0",  # Ajuste seu dispositivo
    "screen_width": 480,
    "screen_height": 320,
    "calibration": {
        "x_min": 0, "x_max": 4095,
        "y_min": 0, "y_max": 4095
    }
}
```

## 🎯 Diferenças dos Menus

### Menu Básico (`menu_basico.py`)
- ✅ Funciona sem root
- ✅ Interface simples por texto
- ✅ Navegação por teclado
- ✅ Baixo uso de recursos

### Menu Touchscreen (`menu_touch_basico.py`)
- ⚠️ Requer root para framebuffer
- ✅ Interface gráfica bonita
- ✅ Navegação por toque
- ✅ Ícones e cores

## 🐛 Solução de Problemas

### "Permission denied" no framebuffer
```bash
# Execute como root
sudo python3 menu_touch_basico.py

# Ou adicione usuário ao grupo video
sudo usermod -a -G video $USER
```

### Touch não funciona
```bash
# Verifique dispositivos disponíveis
ls /dev/input/event*

# Teste eventos touch
sudo cat /dev/input/event0
```

### Aplicação não executa
```bash
# Teste manualmente
cd /home/dw/painel
sudo python3 painelv3.py

# Verifique permissões
ls -la painelv3.py
```

## 📊 Recursos do Sistema

### Performance
- **Menu Básico**: ~1MB RAM, CPU baixo
- **Menu Touch**: ~10MB RAM, 5 FPS

### Compatibilidade
- ✅ Raspberry Pi 3/4
- ✅ Display TFT 3.5" (480x320)
- ✅ Touchscreen resistivo/capacitivo
- ✅ Raspbian/Raspberry Pi OS

## 🎨 Personalização Visual

### Cores (edite `menu_config.py`)
```python
"colors": {
    "background": "#000000",      # Fundo preto
    "primary": "#1e3a8a",        # Azul escuro
    "button": "#1f2937",         # Botões cinza
    "accent": "#fbbf24",         # Destaque dourado
    "text": "#ffffff"            # Texto branco
}
```

### Layout
- **Botões**: 200x80 pixels
- **Margem**: 20 pixels
- **Header**: 80 pixels
- **Footer**: 40 pixels

---

**🥷 Sistema básico e eficiente para controle via touchscreen**
