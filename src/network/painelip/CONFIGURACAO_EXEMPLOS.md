# 📋 Exemplos de Configuração - Painel de Dispositivos

## 🎛️ Como Personalizar a Tela Detalhada

Edite o arquivo `config.py` para personalizar o que aparece na tela:

### 📱 Configuração Atual (Padrão)
```python
# Mostra: "1. Router 192.168.1.1 AA:BB:CC (Vendor) OS:Linux"
SHOW_DEVICE_INDEX = True     # ✅ Mostra número (1., 2., etc.)
SHOW_HOSTNAME = True         # ✅ Mostra nome do dispositivo  
SHOW_IP = True              # ✅ Mostra endereço IP
SHOW_MAC = True             # ✅ Mostra MAC (últimos 8 chars)
SHOW_VENDOR = True          # ✅ Mostra fabricante
SHOW_OS = True              # ✅ Mostra sistema operacional
```

### 🎯 Configurações de Exemplo

#### Tela Simples (só IP e Nome)
```python
SHOW_DEVICE_INDEX = True
SHOW_HOSTNAME = True  
SHOW_IP = True
SHOW_MAC = False           # ❌ Oculta MAC
SHOW_VENDOR = False        # ❌ Oculta fabricante
SHOW_OS = False            # ❌ Oculta OS
```
**Resultado**: `1. Router 192.168.1.1`

#### Tela Técnica (foco em hardware)
```python
SHOW_DEVICE_INDEX = True
SHOW_HOSTNAME = True
SHOW_IP = True  
SHOW_MAC = True
SHOW_VENDOR = True
SHOW_OS = False            # ❌ Oculta OS para economizar espaço
```
**Resultado**: `1. Router 192.168.1.1 AA:BB:CC (Vendor)`

#### Tela Completa (máximo detalhe)
```python
SHOW_DEVICE_INDEX = True
SHOW_HOSTNAME = True
SHOW_IP = True
SHOW_MAC = True  
SHOW_VENDOR = True
SHOW_OS = True
MAX_HOSTNAME_LENGTH = 25   # ⬆️ Mais espaço para nomes
MAX_VENDOR_LENGTH = 20     # ⬆️ Mais espaço para fabricante
MAX_OS_LENGTH = 30         # ⬆️ Mais espaço para OS
```

#### Tela Minimalista (só essencial)
```python
SHOW_DEVICE_INDEX = False  # ❌ Remove numeração
SHOW_HOSTNAME = True
SHOW_IP = True
SHOW_MAC = False
SHOW_VENDOR = False  
SHOW_OS = False
```
**Resultado**: `Router 192.168.1.1`

### ⚙️ Ajuste de Layout

#### Mais Dispositivos por Tela
```python
DEVICE_LINE_HEIGHT = 20        # ⬇️ Linhas mais baixas
DEVICES_PER_PAGE_AUTO = False  # Manual
DEVICES_PER_PAGE_MANUAL = 12   # ⬆️ Mais dispositivos
```

#### Menos Dispositivos (mais espaço)
```python
DEVICE_LINE_HEIGHT = 35        # ⬆️ Linhas mais altas
DEVICES_PER_PAGE_AUTO = False
DEVICES_PER_PAGE_MANUAL = 6    # ⬇️ Menos dispositivos
```

### 🎨 Personalização Visual

#### Cores Personalizadas
```python
COLOR_BACKGROUND = "navy"      # Fundo azul escuro
COLOR_TITLE = "orange"         # Título laranja
COLOR_INFO = "lightgreen"      # Info verde claro
COLOR_TEXT = "white"           # Texto branco
```

#### Fontes Maiores
```python
FONT_TITLE_SIZE = 30          # ⬆️ Título maior
FONT_TEXT_SIZE = 18           # ⬆️ Texto maior  
FONT_SMALL_SIZE = 14          # ⬆️ Lista maior
```

### ⏰ Controle de Tempo

#### Páginas Mais Lentas
```python
PAGE_TIME = 5                 # ⬆️ 5 segundos por página
```

#### Varreduras Mais Frequentes  
```python
SCAN_INTERVAL = 30            # ⬇️ Escaneia a cada 30 segundos
```

## 🚀 Como Aplicar

1. **Edite** `config.py` com suas preferências
2. **Salve** o arquivo
3. **Execute** novamente: `sudo python3 painel_ips.py`
4. **Veja** as mudanças em tempo real!

## 💡 Dicas

- 📏 **Teste diferentes tamanhos**: Ajuste `MAX_*_LENGTH` até ficar bom
- ⚡ **Performance**: Menos informações = mais dispositivos por tela
- 🎨 **Visual**: Combine cores que contrastem bem com o fundo
- 📱 **Espaço**: Em telas pequenas, prefira informações essenciais

---

**Sua tela detalhada está no `_format_device_info()` em `ui.py` - agora totalmente configurável! 🎛️**
