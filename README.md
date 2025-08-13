# miniecran35

 Pré-requisitos (instalação rápida)

sudo apt update
# Bibliotecas Python empacotadas (evita conflito com pip gerenciado)
sudo apt install -y python3-pillow python3-numpy fbset

# (opcional) fontes adicionais
sudo apt install -y fonts-dejavu fonts-liberation

Por que isso?
Pillow (PIL) → desenhar textos/imagens.


NumPy → converter RGB→RGB565 com desempenho.


fbset → inspecionar resolução/bpp do framebuffer.


Fontes → para usar TTF legível (tamanhos maiores).



2) Confirmar telas e escolher o framebuffer da mini tela
Liste os framebuffers e seus “nomes”:

for p in /sys/class/graphics/fb*/name; do echo -n "$p -> "; cat "$p"; done

Exemplo típico que você já viu:

/sys/class/graphics/fb0/name -> BCM2708 FB      (HDMI principal)
/sys/class/graphics/fb1/name -> simple
/sys/class/graphics/fb2/name -> fb_ili9486      (SUA MPI3501)

👉 Use o fb cujo name é fb_ili9486 (no exemplo, /dev/fb2).
Opcional: conferir resolução e bpp:

fbset -s -fb /dev/fb2
cat /sys/class/graphics/fb2/bits_per_pixel

Na MPI3501: normalmente geometry 320 480 e bpp=16 (RGB565).

3) O script (com posicionamento da imagem por modos)
Salve como painel.py (ajuste caminho da imagem e o FB se necessário):

#!/usr/bin/env python3
import time, os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# ===== CONFIGURAÇÕES =====
FB = "/dev/fb2"     # framebuffer da sua tela (ajuste se for outro)
ROTATE_DEG = 0      # rotação de software: 0, 90, 180, 270
IMG_PATH = "/home/dw/kakashicute.png"  # imagem PNG (com transparência, se quiser)
# =========================

def read_virtual_size(fb_index):
    # Em alguns kernels esse arquivo pode não existir; se for o caso,
    # troque por (width, height) = (320, 480) ou use fbset.
    w, h = open(f"/sys/class/graphics/fb{fb_index}/virtual_size").read().strip().split(",")
    return int(w), int(h)

def read_int(path, default=None):
    try:
        return int(open(path).read().strip())
    except:
        return default

fb_index = int(os.path.basename(FB).replace("fb", ""))
width, height = read_virtual_size(fb_index)
bpp = read_int(f"/sys/class/graphics/fb{fb_index}/bits_per_pixel", 16)
bytes_per_pixel = bpp // 8

# Fontes (ajuste tamanhos à vontade)
FONT_BIG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)

while True:
    # Fundo
    img = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(img)

    # Texto (nome, hora, data) — mude cores/tamanhos/textos como quiser
    draw.text((10, 10),  "DOGLAS WICHT",                  fill="yellow", font=FONT_BIG)
    draw.text((10, 50),  time.strftime("Hora: %H:%M:%S"), fill="yellow", font=FONT_BIG)
    draw.text((10, 90),  time.strftime("Data: %d/%m/%Y"), fill="cyan",   font=FONT_SMALL)

    # Imagem (opcional)
    if os.path.exists(IMG_PATH):
        img_logo = Image.open(IMG_PATH).convert("RGBA")
        # tamanho: limite a metade da largura e 1/3 da altura (mantém proporção)
        img_logo.thumbnail((width // 2, height // 3))

        # ===== ESCOLHA O MODO DE POSICIONAMENTO =====
        ## 1) Centralizado embaixo (padrão)
        pos_x = (width - img_logo.width) // 2
        pos_y = height - img_logo.height - 10

        ## 2) Canto inferior direito
        # pos_x = width - img_logo.width - 10
        # pos_y = height - img_logo.height - 10

        ## 3) Canto inferior esquerdo
        # pos_x = 10
        # pos_y = height - img_logo.height - 10

        ## 4) Logo abaixo da data (fixo ~130px do topo)
        # pos_x = (width - img_logo.width) // 2
        # pos_y = 130
        # ============================================

        img.paste(img_logo, (pos_x, pos_y), img_logo)  # mantém transparência

    # Rotação via software (se preferir, rode no kernel com dtoverlay=...:rotate=N)
    frame = img.rotate(ROTATE_DEG, expand=False) if ROTATE_DEG else img

    # Conversão para o formato do framebuffer
    if bpp == 16:
        # RGB888 -> RGB565 (little-endian)
        arr = np.asarray(frame, dtype=np.uint8)
        r = (arr[..., 0] >> 3).astype(np.uint16)
        g = (arr[..., 1] >> 2).astype(np.uint16)
        b = (arr[..., 2] >> 3).astype(np.uint16)
        rgb565 = (r << 11) | (g << 5) | b
        out = np.empty((height, width, 2), dtype=np.uint8)
        out[..., 0] = (rgb565 & 0xFF).astype(np.uint8)
        out[..., 1] = (rgb565 >> 8).astype(np.uint8)
        payload = out.tobytes()
    else:
        # para bpp=32, normalmente funciona direto
        payload = frame.tobytes()

    # Garante o tamanho exato (evita "No space left on device")
    expected = width * height * bytes_per_pixel
    with open(FB, "wb") as f:
        f.write(payload[:expected])

    time.sleep(1)

Executar:

sudo python3 ./painel.py


4) Entendendo o que cada parte faz
FB / ROTATE_DEG / IMG_PATH: configurações principais (qual framebuffer, rotação por software, imagem PNG opcional).


read_virtual_size / read_int: helpers para ler resolução e bits_per_pixel do /sys.


width/height/bpp: definem tamanho do canvas e formato de saída:


MPI3501 (ILI9486) costuma expor 320×480, bpp=16 (RGB565).


FONT_BIG / FONT_SMALL: fontes TTF legíveis; ajuste tamanhos como quiser.


Loop:


cria uma imagem preta,


desenha textos (nome, hora, data),


carrega e posiciona a imagem (com transparência, se for PNG),


rotaciona se necessário,


converte para RGB565 quando bpp == 16,


escreve os bytes direto no /dev/fbN,


repete a cada 1s.


Posicionamento (pos_x, pos_y):
pos_x maior → mais à direita; menor → mais à esquerda.


pos_y maior → mais embaixo; menor → mais em cima.


Você pode centralizar e depois ajustar “a partir do centro”:

 python

pos_x = (width - img_logo.width) // 2 + 20  # empurra 20px à direita



5) Rotação: kernel vs software
No kernel (boot): em /boot/config.txt:

 ini

dtoverlay=tft35a:rotate=90   # ou 270 p/ modo deitado
 Nesse caso, deixe ROTATE_DEG = 0 no script.


No software (script): mude ROTATE_DEG = 0|90|180|270.


Evite “somar rotações” (kernel + script). Prefira rotacionar em um lugar só.

6) Iniciar automaticamente no boot (sem travar)
Crie um service no systemd para rodar depois que o sistema subir (sem usar rc.local):
bash

sudo tee /etc/systemd/system/painel-fb.service >/dev/null <<'UNIT'
[Unit]
Description=Painel na tela SPI (fb_ili9486)
After=graphical.target
Wants=graphical.target
# Espera o fb_ili9486 aparecer até 30s (sem travar o boot)
ExecStartPre=/bin/sh -lc 'for i in $(seq 1 30); do for p in /sys/class/graphics/fb*/name; do [ "$(cat "$p" 2>/dev/null)" = "fb_ili9486" ] && exit 0; done; sleep 1; done; exit 1'

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /home/dw/painel.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable painel-fb.service
sudo systemctl start painel-fb.service

Ver status:
bash

sudo systemctl status painel-fb.service

Parar/desabilitar:
bash

sudo systemctl stop painel-fb.service
sudo systemctl disable painel-fb.service


7) Problemas comuns (e soluções)
“No space left on device” ao escrever no /dev/fbN
 → Payload maior que o esperado. Garanta bpp == 16 e corte os bytes:

 python

expected = width * height * (bpp//8)
f.write(payload[:expected])


ioctl VT_GETSTATE: not a linux console (usando fbi por SSH)
 → fbi precisa de TTY. Use openvt ou prefira o script direto no /dev/fbN.


virtual_size não existe
 → Use valores fixos (320×480) ou detecte com fbset -s -fb /dev/fbN.


Imagem “sumida” ou minúscula
 → thumbnail((1,2)) limita demais. Use thumbnail((width//2, height//3))
 ou resize((LARGURA, ALTURA), Image.LANCZOS).


PNG perde transparência
 → Não converta para RGB; use convert("RGBA") e img.paste(logo, pos, logo).


Cores trocadas (raro)
 → Alguns drivers usam BGR565; se acontecer, troque R↔B na montagem do rgb565.


Boot lento
 → Evite rc.local. Desative NetworkManager-wait-online.service.
 Plymouth travando? Máscare plymouth-quit-wait.service.


IndentationError depois de comentar/descomentar modos
 → Certifique-se de que as linhas pos_x/pos_y estão alinhadas no mesmo nível (sem tabs extras).
 → E cuidado com typos: é img_logo.width (com d).



8) Dicas úteis
Centralizar texto: use draw.textbbox() para medir e posicionar no centro.


“HUD” de sistema: dá pra mostrar CPU/RAM/temperatura/IP — se quiser, eu te mando um exemplo.


Tamanho da fonte: MPI3501 (320×480) fica legal com 24–36 para título e 18–24 para conteúdo.


