# API Reference

## 📚 Documentação das Classes e Módulos

### Core Modules

#### `TouchMenu` (touch_menu_visual.py)

Classe principal responsável pelo menu touchscreen.

```python
class TouchMenu:
    def __init__(self)
    def run(self)
    def _load_gif_frames(self, gif_path)
    def _render_frame(self)
    def _handle_touch_events(self)
    def _detect_button_press(self, x, y)
    def _execute_script(self, button_index)
```

**Métodos Principais**:

##### `__init__(self)`
Inicializa o menu touchscreen.
- Configura tela e framebuffer
- Carrega assets (GIFs, fontes)
- Define layout dos botões

##### `run(self)`
Loop principal do menu.
- Renderiza frames do GIF
- Processa eventos de touch
- Gerencia navegação

##### `_detect_button_press(self, x, y)`
Detecta qual botão foi pressionado.

**Parâmetros**:
- `x` (int): Coordenada X do toque
- `y` (int): Coordenada Y do toque

**Retorna**: Índice do botão ou -1 se fora dos botões

#### `TouchExit` (touch_exit.py)

Classe para detecção de toque e saída dos módulos.

```python
class TouchExit:
    def __init__(self)
    def start_monitoring(self)
    def should_exit(self)
    def stop(self)
```

**Métodos**:

##### `start_monitoring(self)`
Inicia thread de monitoramento de toque.
- Período de carência de 3 segundos
- Detecção contínua em background

##### `should_exit(self)`
Verifica se foi detectado toque para sair.

**Retorna**: `bool` - True se deve sair

### Application Modules

#### Sistema Monitor (`painelv3.py`)

Módulo de monitoramento do sistema.

**Funções Principais**:

```python
def find_fb_by_name(target="fb_ili9486")
def fb_geometry(fbdev)
def list_ipv4()
def pick_ip()
def rgb_to_rgb565_le(img)
```

##### `list_ipv4()`
Lista interfaces IPv4 ativas.

**Retorna**: `dict` - {interface: IP}

##### `pick_ip()`
Seleciona melhor interface de rede.

**Retorna**: `tuple` - (interface, ip)

##### `rgb_to_rgb565_le(img)`
Converte imagem RGB para RGB565 Little Endian.

**Parâmetros**:
- `img` (PIL.Image): Imagem RGB

**Retorna**: `numpy.array` - Dados RGB565

#### GIF Viewer (`painel_gif.py`)

Módulo de visualização de GIFs.

**Funções**:

```python
def load_gif(path, target_width, target_height)
def main()
```

##### `load_gif(path, target_width, target_height)`
Carrega e processa arquivo GIF.

**Parâmetros**:
- `path` (str): Caminho do arquivo GIF
- `target_width` (int): Largura alvo
- `target_height` (int): Altura alvo

**Retorna**: `tuple` - (frames, durations)

### Network Module

#### `NetworkPanel` (network/panel.py)

Painel de monitoramento de rede.

```python
class NetworkPanel:
    def __init__(self)
    def run(self)
    def _should_start_new_scan(self)
    def _start_network_scan(self)
    def _update_scan_progress(self)
    def _render_current_screen(self)
```

**Métodos**:

##### `_start_network_scan(self)`
Inicia nova varredura da rede.
- Detecção automática da rede local
- Execução em background

##### `_render_current_screen(self)`
Renderiza tela atual com informações.
- Progresso da varredura
- Dispositivos encontrados
- Estatísticas de rede

## 🔧 Configurações

### Constantes Globais

```python
# Dimensões da tela
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320

# Layout
LEFT_PANEL_WIDTH = 240
RIGHT_PANEL_WIDTH = 240
BUTTON_HEIGHT = 100

# Dispositivos
FRAMEBUFFER = "/dev/fb0"
TOUCH_DEVICE = "/dev/input/event2"  # Auto-detectado

# Timing
FRAME_RATE = 10  # FPS
SCAN_INTERVAL = 15  # Segundos
```

### Estrutura de Botões

```python
buttons = [
    {
        "name": "SISTEMA",
        "icon": "📊",
        "script": "src/modules/painelv3.py",
        "rect": (180, 4, 460, 104)
    },
    {
        "name": "ANIMAÇÃO", 
        "icon": "🎬",
        "script": "src/modules/painel_gif.py",
        "rect": (180, 110, 460, 210)
    },
    {
        "name": "REDE",
        "icon": "🌐", 
        "script": "src/network/painelip/painel_ips.py",
        "rect": (180, 216, 460, 316)
    }
]
```

## 🎨 Customização

### Adicionando Novo Módulo

1. **Criar módulo** em `src/modules/`:

```python
#!/usr/bin/env python3
from src.core.touch_exit import setup_touch_exit

def main():
    touch_monitor = setup_touch_exit()
    
    while True:
        if touch_monitor.should_exit():
            print("🔴 TOQUE DETECTADO - VOLTANDO AO MENU!")
            import subprocess
            subprocess.run(["sudo", "python3", "src/core/touch_menu_visual.py"])
            break
            
        # Seu código aqui
        time.sleep(0.1)

if __name__ == "__main__":
    main()
```

2. **Adicionar botão** em `touch_menu_visual.py`:

```python
self.buttons.append({
    "name": "MEU MÓDULO",
    "icon": "🔧",
    "script": "src/modules/meu_modulo.py",
    "rect": (180, 322, 460, 422)  # Nova posição
})
```

### Personalizando Visual

```python
# Cores
BACKGROUND_COLOR = (0, 0, 0)      # Preto
BUTTON_COLOR = (64, 64, 64)       # Cinza escuro
TEXT_COLOR = (255, 255, 255)      # Branco
ACCENT_COLOR = (0, 255, 0)        # Verde

# Fontes
FONT_PATH = "/usr/share/fonts/truetype/dejavu/"
FONT_BIG = ImageFont.truetype(f"{FONT_PATH}DejaVuSans-Bold.ttf", 28)
FONT_SMALL = ImageFont.truetype(f"{FONT_PATH}DejaVuSans.ttf", 18)
```

## 🔍 Debugging

### Logs e Debug

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

### Testando Componentes

```python
# Testar detecção de touch
python3 -c "from src.core.touch_exit import TouchExit; t=TouchExit(); t.start_monitoring()"

# Testar framebuffer
python3 -c "with open('/dev/fb0', 'wb') as f: f.write(b'\\xFF\\x00' * 153600)"

# Testar módulos individualmente
python3 src/modules/painelv3.py
```

## 🛡️ Error Handling

Todos os módulos implementam tratamento robusto de erros:

```python
try:
    # Operação crítica
    with open(FRAMEBUFFER, 'wb') as f:
        f.write(payload)
except PermissionError:
    logger.error("Sem permissão para acessar framebuffer")
except FileNotFoundError:
    logger.error("Framebuffer não encontrado")
except Exception as e:
    logger.error(f"Erro inesperado: {e}")
    # Recuperação ou fallback
```
