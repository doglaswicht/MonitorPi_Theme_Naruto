# 🎭 Títulos Personalizados para Tela de Carregamento

## 🎯 **Configuração Atual**

No arquivo `config.py`:
```python
LOADING_TITLE = "Iniciando Scan Ninja..."  # Título durante o GIF do Kakashi
TITLE = "Dispositivos na rede"             # Título na tela de resultados
```

## 🥷 **Sugestões Temáticas Ninja**

### **Clássicos Ninja:**
```python
LOADING_TITLE = "Jutsu de Reconhecimento..."
LOADING_TITLE = "Missão de Infiltração..."
LOADING_TITLE = "Técnica Secreta Ativada..."
LOADING_TITLE = "Iniciando Operação Ninja..."
LOADING_TITLE = "Invocação em Progresso..."
```

### **Específicos do Kakashi:**
```python
LOADING_TITLE = "Sharingan Analisando..."
LOADING_TITLE = "Kakashi Investigando..."
LOADING_TITLE = "Chidori Escaneando..."
LOADING_TITLE = "Sensei em Ação..."
LOADING_TITLE = "Copy Ninja Trabalhando..."
```

### **Frases Icônicas:**
```python
LOADING_TITLE = "Aqueles que quebram as regras..."
LOADING_TITLE = "Um ninja deve ver através..."
LOADING_TITLE = "Na vida ninja..."
LOADING_TITLE = "Trabalho em equipe..."
```

## 🌟 **Sugestões Criativas**

### **Tecnológicas:**
```python
LOADING_TITLE = "Radar Ninja Ativo..."
LOADING_TITLE = "Sensores Ligados..."
LOADING_TITLE = "Varredura Stealth..."
LOADING_TITLE = "Detectando Alvos..."
LOADING_TITLE = "Sistema de Espionagem..."
```

### **Divertidas:**
```python
LOADING_TITLE = "Procurando Inimigos..."
LOADING_TITLE = "Caçando Dispositivos..."
LOADING_TITLE = "Investigação Secreta..."
LOADING_TITLE = "Missão Impossível..."
LOADING_TITLE = "Operação Especial..."
```

### **Personalizadas:**
```python
LOADING_TITLE = "Painel do [SEU NOME]"
LOADING_TITLE = "Rede da Casa..."
LOADING_TITLE = "Central de Comando..."
LOADING_TITLE = "Sistema de Monitoramento..."
```

## 🎨 **Exemplos Visuais**

### **Antes:**
```
┌─────────────────────────────────────┐
│ Dispositivos na rede         14:30:15│  ← Sempre o mesmo
│ wlan0: 192.168.8.101 (escaneando...) │
│           🥷 KAKASHI GIF            │
└─────────────────────────────────────┘
```

### **Depois:**
```
┌─────────────────────────────────────┐
│ Jutsu de Reconhecimento...   14:30:15│  ← Personalizado!
│ wlan0: 192.168.8.101 (escaneando...) │
│           🥷 KAKASHI GIF            │
└─────────────────────────────────────┘
```

## 🔧 **Como Aplicar**

1. **Edite** `config.py`
2. **Altere** a linha:
   ```python
   LOADING_TITLE = "SEU TÍTULO AQUI"
   ```
3. **Salve** o arquivo
4. **Execute**: `sudo python3 painel_ips.py`

## 💡 **Dicas de Escolha**

### **Para Tela Pequena (480x320):**
- Prefira títulos curtos (até 25 caracteres)
- Evite palavras muito longas

### **Para Impacto Visual:**
- Use reticências "..." para indicar processo
- Combine com o tema ninja do GIF

### **Para Personalização:**
- Inclua seu nome ou local
- Use termos técnicos que você gosta

## 🎯 **Configurações Avançadas**

### **Títulos Dinâmicos** (baseados no horário):
```python
# Você pode adicionar lógica para mudar o título baseado na hora
# Manhã: "Missão Matinal..."
# Tarde: "Operação Vespertina..."
# Noite: "Vigilância Noturna..."
```

### **Títulos por Situação:**
```python
# Durante primeira varredura: "Primeira Missão..."
# Varreduras seguintes: "Patrulhamento..."
```

---

## 🎉 **Títulos Favoritos Recomendados:**

```python
# Top 5 para temas ninja:
LOADING_TITLE = "Jutsu de Reconhecimento..."    # 🥇
LOADING_TITLE = "Sharingan Analisando..."       # 🥈  
LOADING_TITLE = "Missão de Infiltração..."      # 🥉
LOADING_TITLE = "Técnica Secreta Ativada..."    # 🏆
LOADING_TITLE = "Copy Ninja Trabalhando..."     # ⭐
```

**Escolha o seu favorito e personalize seu painel ninja! 🥷✨**
