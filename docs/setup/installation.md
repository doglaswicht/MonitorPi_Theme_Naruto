# Guia de Instalação

## 📋 Pré-requisitos de Hardware

### Hardware Necessário
- **Raspberry Pi 3B+ ou 4** (recomendado)
- **Display TFT 3.5"** com driver ili9486
- **Touchscreen ADS7846** ou compatível
- **Cartão MicroSD** (16GB ou maior)
- **Fonte de alimentação** adequada para o Pi

### Configuração do Display

1. **Habilitar SPI** no Raspberry Pi:
```bash
sudo raspi-config
# Interfacing Options > SPI > Yes
```

2. **Adicionar overlay do display** em `/boot/config.txt`:
```bash
sudo nano /boot/config.txt
```

Adicione as linhas:
```
# Display TFT 3.5"
dtoverlay=tft35a
dtparam=rotate=270
```

3. **Reiniciar** o Raspberry Pi:
```bash
sudo reboot
```

## 📦 Instalação de Dependências

### Atualizar Sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### Instalar Python e Bibliotecas
```bash
sudo apt install python3-pip python3-numpy python3-pil -y
pip3 install pillow numpy
```

### Verificar Framebuffer
```bash
ls /dev/fb*
# Deve mostrar /dev/fb0 (e possivelmente /dev/fb1)
```

### Verificar Dispositivo de Touch
```bash
ls /dev/input/event*
cat /proc/bus/input/devices | grep -A 5 "ADS7846"
```

## 🚀 Instalação do Painel

### 1. Clonar Repositório
```bash
cd /home/pi
git clone https://github.com/doglaswicht/miniecran35.git painel
cd painel
```

### 2. Configurar Permissões
```bash
chmod +x scripts/start_menu.sh
sudo chown -R pi:pi /home/pi/painel
```

### 3. Testar Instalação
```bash
sudo ./scripts/start_menu.sh
```

## 🔧 Configuração Automática

### Inicialização Automática
Para iniciar o painel automaticamente no boot:

1. **Criar serviço systemd**:
```bash
sudo nano /etc/systemd/system/painel.service
```

2. **Adicionar conteúdo**:
```ini
[Unit]
Description=Painel Touchscreen
After=graphical.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/painel
ExecStart=/home/pi/painel/scripts/start_menu.sh
Restart=always

[Install]
WantedBy=graphical.target
```

3. **Habilitar serviço**:
```bash
sudo systemctl enable painel.service
sudo systemctl start painel.service
```

## 🔍 Verificação da Instalação

### Verificar Funcionamento
1. **Menu principal** deve aparecer na tela
2. **Touch deve responder** aos toques
3. **Botões devem estar visíveis** e funcionais

### Solução de Problemas Comuns

#### Display não aparece
- Verificar conexões físicas
- Confirmar overlay no config.txt
- Verificar se /dev/fb0 existe

#### Touch não responde
- Verificar /dev/input/event* disponíveis
- Executar: `evtest /dev/input/eventX` para testar
- Ajustar permissões: `sudo chmod 666 /dev/input/event*`

#### Erro de permissão
```bash
sudo chmod +x /home/pi/painel/scripts/start_menu.sh
sudo usermod -a -G input pi
```

## 📁 Estrutura Pós-Instalação

```
/home/pi/painel/
├── src/core/touch_menu_visual.py    # Menu principal
├── src/modules/painelv3.py          # Monitor sistema
├── src/modules/painel_gif.py        # Visualizador GIF
├── src/network/painelip/            # Scanner rede
├── assets/gifs2/                    # Arquivos GIF
├── scripts/start_menu.sh            # Script inicialização
└── docs/                            # Documentação
```

## ✅ Teste Final

Execute o comando de teste:
```bash
cd /home/pi/painel
sudo python3 src/core/touch_menu_visual.py
```

Se tudo estiver funcionando, você verá o menu principal com GIF animado e três botões funcionais.

## 🆘 Suporte

Em caso de problemas, consulte:
- [Troubleshooting](troubleshooting.md)
- [FAQ](../user-guide/faq.md)
- Issues no GitHub
