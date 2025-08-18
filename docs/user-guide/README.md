# Guia do Usuário

## 🎮 Como Usar o Painel

### Navegação Principal

O painel possui uma interface simples e intuitiva:

```
┌─────────────────────────────────────────────┐
│  [GIF Animado]     │  📊 SISTEMA            │
│                    │  🎬 ANIMAÇÃO           │
│                    │  🌐 REDE               │
└─────────────────────────────────────────────┘
```

### 📊 Monitor do Sistema

**Como Acessar**: Toque no botão "SISTEMA"

**Funcionalidades**:
- Exibição em tempo real da data e hora
- Informações do usuário atual
- Endereço IP da interface de rede ativa
- Logo/imagem personalizada

**Como Voltar**: Toque em qualquer lugar da tela

### 🎬 Visualizador de GIFs

**Como Acessar**: Toque no botão "ANIMAÇÃO"

**Funcionalidades**:
- Reprodução automática de GIFs
- Rotação entre múltiplos arquivos
- Transições suaves entre animações
- Ajuste automático de tamanho

**Configuração de GIFs**:
- Adicione arquivos `.gif` em `/home/pi/painel/assets/gifs2/`
- O sistema detecta automaticamente novos arquivos
- Formatos suportados: GIF animado

**Como Voltar**: Toque em qualquer lugar da tela

### 🌐 Scanner de Rede

**Como Acessar**: Toque no botão "REDE"

**Funcionalidades**:
- Detecção automática da rede local
- Varredura periódica (a cada 15 segundos)
- Exibição de dispositivos conectados
- Informações de IP e interface de rede

**Informações Exibidas**:
- Total de dispositivos encontrados
- Interface de rede ativa
- Progresso da varredura
- Lista de IPs detectados

**Como Voltar**: Toque em qualquer lugar da tela

## ⚙️ Configurações Avançadas

### Personalizando GIFs

1. **Adicionar novos GIFs**:
```bash
cp meu_gif.gif /home/pi/painel/assets/gifs2/
```

2. **Alterar velocidade** (editar `painel_gif.py`):
```python
SWITCH_DELAY = 5.0  # Segundos entre GIFs
```

### Personalizando Interface do Sistema

1. **Alterar imagem de logo** (editar `painelv3.py`):
```python
IMG_PATH = "/home/pi/painel/assets/minha_imagem.png"
```

2. **Personalizar textos e cores**:
```python
draw.text((10, 10), "MEU NOME", fill="yellow", font=FONT_BIG)
```

### Configurações de Rede

1. **Alterar intervalo de varredura** (editar `config.py`):
```python
SCAN_INTERVAL = 30  # Segundos entre varreduras
```

2. **Personalizar range de IPs**:
```python
NETWORK_RANGE = "192.168.1.0/24"  # Sua rede
```

## 🔧 Solução de Problemas

### Touch não responde
1. Verificar dispositivo: `ls /dev/input/event*`
2. Testar touch: `evtest /dev/input/event2`
3. Ajustar permissões: `sudo chmod 666 /dev/input/event*`

### Display com cores erradas
1. Verificar configuração em `/boot/config.txt`
2. Ajustar rotação: `dtparam=rotate=270`
3. Reiniciar: `sudo reboot`

### Aplicação trava
1. Parar processos: `sudo pkill -f python3.*painel`
2. Reiniciar: `sudo ./scripts/start_menu.sh`

### Performance lenta
1. Verificar temperatura: `vcgencmd measure_temp`
2. Reduzir FPS dos GIFs
3. Diminuir resolução das imagens

## 🎨 Personalização

### Themes e Cores
Edite os arquivos em `src/` para personalizar:
- Cores dos botões
- Fontes e tamanhos
- Layout e posicionamento
- Animações e transições

### Adicionando Novos Módulos
1. Crie novo arquivo em `src/modules/`
2. Implemente detecção de touch
3. Adicione botão no menu principal
4. Registre no `touch_menu_visual.py`

## 📱 Dicas de Uso

### Melhor Performance
- Use GIFs otimizados (< 5MB)
- Mantenha poucos GIFs na pasta
- Reinicie periodicamente o sistema

### Cuidados com o Hardware
- Evite toques muito fortes na tela
- Mantenha o Pi bem ventilado
- Use fonte de alimentação adequada

### Backup e Manutenção
```bash
# Backup das configurações
cp -r /home/pi/painel /home/pi/painel_backup

# Atualizar o sistema
cd /home/pi/painel
git pull origin main
```

## ❓ FAQ

**P: Como adicionar mais botões?**
R: Edite `touch_menu_visual.py` e adicione novos botões no array `self.buttons`.

**P: Posso usar outros formatos de imagem?**
R: Sim, PNG, JPG são suportados. Modifique o código para carregar outros formatos.

**P: Como alterar o tamanho dos botões?**
R: Ajuste as coordenadas em `BUTTON_HEIGHT` e `RIGHT_PANEL_WIDTH`.

**P: É possível usar sem touch?**
R: Sim, mas será necessário usar teclado/mouse ou implementar controle por GPIO.
