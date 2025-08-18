# Painel de Dispositivos de Rede v2.0

## Arquitetura Modular

O projeto foi reestruturado seguindo princípios de arquitetura limpa, dividido em módulos especializados:

### 📁 Estrutura de Arquivos

```
painelip/
├── __init__.py          # Inicialização do pacote
├── main.py             # Ponto de entrada principal
├── config.py           # Configurações centralizadas
├── models.py           # Modelos de dados (DeviceInfo, etc.)
├── framebuffer.py      # Manipulação do framebuffer
├── network.py          # Descoberta de dispositivos na rede
├── ui.py              # Interface gráfica
├── panel.py           # Controlador principal
└── painel_ips.py      # Arquivo original (legacy)
```

### 🏗️ Arquitetura dos Módulos

#### 1. **config.py** - Configurações
- Centraliza todas as configurações do sistema
- Cores, fontes, intervalos, interfaces preferidas
- Fácil manutenção e customização

#### 2. **models.py** - Modelos de Dados
- `DeviceInfo`: Estrutura para informações de dispositivos
- `NetworkScanResult`: Resultado de varreduras de rede
- Tipo-seguro com dataclasses

#### 3. **framebuffer.py** - Interface de Hardware
- Abstração completa do framebuffer
- Detecção automática de dispositivos
- Conversão de formatos de pixel
- Isolamento da complexidade de hardware

#### 4. **network.py** - Descoberta de Rede
- `NetworkDiscovery`: Classe principal para varreduras
- Descoberta automática de interfaces
- Parse inteligente da saída do nmap
- Deduplicação e ordenação de dispositivos

#### 5. **ui.py** - Interface Gráfica
- `PanelUI`: Gerenciador de telas
- Telas de carregamento com animações
- Listas paginadas de dispositivos
- Renderização responsiva

#### 6. **panel.py** - Controlador Principal
- `NetworkPanel`: Orquestra todo o sistema
- Gerencia ciclo de varreduras
- Controla estado da aplicação
- Loop principal com tratamento de erros

#### 7. **main.py** - Ponto de Entrada
- Interface simples para inicialização
- Importação limpa do controlador

### 🚀 Como Usar

#### Executar o Painel
```bash
sudo python3 main.py
```

#### Personalizar Configurações
Edite `config.py` para ajustar:
- Interfaces de rede preferidas
- Intervalos de varredura
- Cores e fontes
- Rotação da tela

#### Usar Módulos Individualmente
```python
from painelip import NetworkDiscovery, PanelUI, DeviceInfo

# Descoberta de rede
discovery = NetworkDiscovery()
devices = discovery.parse_nmap_output(nmap_output)

# Interface gráfica
ui = PanelUI(480, 320)
screen = ui.create_loading_screen(0, "Título", "Info")
```

### 🎯 Vantagens da Nova Arquitetura

#### **Separação de Responsabilidades**
- Cada módulo tem uma função específica e bem definida
- Facilita manutenção e debugging
- Código mais legível e organizacional

#### **Reutilização**
- Módulos podem ser usados independentemente
- Fácil criação de diferentes interfaces
- Testabilidade melhorada

#### **Extensibilidade**
- Novos tipos de tela facilmente adicionáveis em `ui.py`
- Suporte a novos protocolos de descoberta em `network.py`
- Configurações centralizadas em `config.py`

#### **Manutenibilidade**
- Bugs isolados em módulos específicos
- Atualizações incrementais possíveis
- Documentação modular

#### **Testabilidade**
- Cada módulo pode ser testado isoladamente
- Mocks e stubs mais simples
- Cobertura de testes granular

### 🔧 Dependências

```bash
pip install pillow numpy
```

### 📝 Compatibilidade

- A nova arquitetura mantém compatibilidade funcional
- O arquivo original `painel_ips.py` permanece como referência
- Migração gradual possível

### 🚦 Status do Projeto

- ✅ Arquitetura modular implementada
- ✅ Separação de responsabilidades
- ✅ Configurações centralizadas
- ✅ Interface limpa e documentada
- 🔄 Testes unitários (próxima fase)
- 🔄 CI/CD pipeline (próxima fase)
