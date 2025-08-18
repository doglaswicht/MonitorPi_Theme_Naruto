# 📁 Estrutura do Projeto

## 📋 Organização Atual

```
painel/
├── 📂 src/                     # Código fonte principal
│   ├── 📂 core/               # Módulos centrais
│   │   └── touch_menu_visual.py    # Menu principal touchscreen
│   ├── 📂 modules/            # Módulos funcionais
│   │   ├── painelv3.py       # Monitor do sistema
│   │   └── painel_gif.py     # Visualizador de GIFs
│   └── 📂 network/            # Módulos de rede
│       └── 📂 painelip/       # Scanner de IPs da rede
│           ├── panel.py       # Interface principal
│           └── painel_ips.py  # Lógica de scanning
│
├── 📂 scripts/                # Scripts de automação
│   └── start_menu.sh         # Script de inicialização
│
├── 📂 docs/                   # Documentação
│   ├── 📂 api/               # Documentação da API
│   ├── 📂 setup/             # Guias de instalação
│   ├── 📂 user-guide/        # Manual do usuário
│   └── project-structure.md  # Este arquivo
│
├── 📂 assets/                 # Recursos multimídia
│   └── 📂 gifs/              # Arquivos GIF para exibição
│
├── 📂 painel_c/              # Implementação em C (legacy)
│
└── 📂 archive/               # Arquivos antigos/backup
```

## 🔄 Fluxo de Execução

1. **Inicialização**: `scripts/start_menu.sh` → `src/core/touch_menu_visual.py`
2. **Menu Principal**: Interface touchscreen com 3 opções
3. **Módulos**: Cada botão executa um módulo específico
4. **Retorno**: Touch em qualquer lugar retorna ao menu

## 📦 Módulos Principais

### 🎯 Core (`src/core/`)
- **touch_menu_visual.py**: Menu principal com interface touchscreen

### 🔧 Módulos (`src/modules/`)
- **painelv3.py**: Monitor de sistema (CPU, RAM, temperatura)
- **painel_gif.py**: Visualizador de GIFs com controles

### 🌐 Network (`src/network/`)
- **painelip/**: Scanner de dispositivos na rede local

## 🚀 Como Usar

### Inicialização Rápida
```bash
# Executar diretamente
sudo python3 src/core/touch_menu_visual.py

# Ou usar o script
chmod +x scripts/start_menu.sh
./scripts/start_menu.sh
```

### Estrutura de Navegação
- **Botão 1**: Monitor do Sistema
- **Botão 2**: Visualizador GIF
- **Botão 3**: Scanner de Rede
- **Touch**: Retornar ao menu (de qualquer módulo)

## 🔧 Configuração

### Hardware Requerido
- Raspberry Pi com display TFT 3.5" (480x320)
- Touchscreen ADS7846 (auto-detectado)
- Python 3.7+ com pygame, psutil, PIL

### Dependências
```bash
sudo apt update
sudo apt install python3-pygame python3-psutil python3-pil
pip3 install python-nmap
```

## 📝 Status do Projeto

- ✅ **Estrutura Organizada**: Código fonte bem estruturado
- ✅ **Documentação Completa**: Guias e referências criados
- ✅ **Sistema Funcional**: Menu e módulos operacionais
- ✅ **Hardware Configurado**: Touchscreen calibrado e funcionando
- ✅ **Navegação Intuitiva**: Fluxo de telas implementado

## 🔄 Próximos Passos

1. **Testes Completos**: Verificar todos os módulos após reorganização
2. **Otimizações**: Melhorar performance e responsividade
3. **Novos Módulos**: Adicionar funcionalidades conforme necessário
4. **Backup**: Manter versões estáveis em `archive/`

---
*Projeto organizado e documentado em: $(date)*
