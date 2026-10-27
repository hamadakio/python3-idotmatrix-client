<p align="center">
  <img src="images/logo.png" alt="iDotMatrix Studio Pro Logo" width="220" height="220">
</p>

<h1 align="center">iDotMatrix Studio Pro & Client</h1>

<p align="center">
  <strong>A suíte definitiva e moderna para controle de telas pixel art Bluetooth (16x16 e 32x32).</strong><br/>
  Totalmente reconstruída com arquitetura assíncrona, monitoramento de PC em tempo real, estúdio DIY de animação, cliente nativo Windows e muito mais.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/.NET-8.0%20WPF-512BD4?style=flat&logo=dotnet&logoColor=white" alt=".NET 8"/>
  <img src="https://img.shields.io/badge/Interface-PyQt5%20Modern%20Dark-21262d?style=flat" alt="Modern UI"/>
  <img src="https://img.shields.io/badge/Bluetooth-BLE%20Persistent-0078D7?style=flat&logo=bluetooth&logoColor=white" alt="Bluetooth LE"/>
  <img src="https://img.shields.io/badge/License-GPL--3.0-green.svg" alt="License GPLv3"/>
</p>

---

## 🚀 Sobre a Nova Versão

A aplicação foi **completamente reconstruída e modernizada**! O que antes era um conjunto de scripts com chamadas de console avulsas e lentas agora se tornou um **estúdio completo, ágil e visualmente deslumbrante** para gerenciar matrizes de LED iDotMatrix (16x16 e 32x32).

### ✨ O que foi feito e melhorado?

1. **Conexão BLE Persistente e Instantânea (`core/ble_controller.py`)**:
   - **Antes:** Cada ação abria um novo subprocesso de linha de comando (`QProcess`), iniciava uma conexão Bluetooth do zero, transmitia o comando e desconectava. Isso demorava vários segundos e causava lentidão ou travamentos.
   - **Agora:** Uma arquitetura assíncrona desacoplada em `QThread` com loop `asyncio` exclusivo mantém a conexão GATT aberta continuamente. As respostas agora são **instantâneas**, permitindo fluxos contínuos de streaming com baixa latência.

2. **Monitor de Hardware do PC em Tempo Real (`core/hardware_monitor.py`)**:
   - Transmissão ao vivo de métricas do computador direto para o painel LED 32x32:
     - **CPU**: porcentagem de uso e temperatura (°C).
     - **GPU**: suporte a placas NVIDIA via `nvidia-smi` em processo oculto (utilização e temperatura).
     - **RAM**: porcentagem e quantidade utilizada/total.
   - **Fonte Bitmap 3x5 Pixel-Perfect:** Desenvolvida especificamente para a matriz de 32x32, garantindo máxima legibilidade sem borrões de interpolação.
   - Barras de nível com código de cores inteligente (Ciano, Verde Esmeralda, Roxo Neon e alerta Vermelho).

3. **Previsão do Tempo Integrada (`core/weather_service.py`)**:
   - Consulta meteorológica automática (por geolocalização IP) ou personalizada por nome de cidade.
   - Geração de cards temáticos em pixel art 32x32 (Sol, Nuvens, Chuva, Tempestade com raios, Neve).
   - Alertas e mensagens de bem-estar/saúde com base na temperatura atual.

4. **Estúdio DIY de Pixel Art & Animações (`gui.py`)**:
   - Grade interativa de desenho em tempo real com zoom ajustável e suporte a tamanhos 16x16 e 32x32.
   - Ferramentas completas: Lápis, Borracha, Balde de Tinta (*Flood Fill*), Conta-gotas (*Color Picker*), Espelhar Horizontal e Vertical.
   - **Animações Frame a Frame:** Criação de múltiplos quadros, gerenciamento da linha do tempo (adicionar, clonar, remover, navegar), pré-visualização animada e envio direto para o display.

5. **Galeria de Presets & Modo Carrossel / Playlist (`core/presets.py`)**:
   - Presets embutidos em pixel art prontos para uso (Coração Neon, Super Cogumelo, Space Invader, Neon Skull, Café & Foco).
   - Conversor inteligente de imagens e GIFs com redimensionamento, ajuste de contraste e centralização automática.
   - Modo **Carrossel** para alternar imagens e artes automaticamente na tela com temporizador configurável.

6. **Áudio, Equalizador e Ambientes de Relaxamento**:
   - Simulação de visualizador de espectro sonoro com barras de equalização em degradê neon.
   - Padrões visuais dinâmicos para momentos de foco e descanso (Fogueira aconchegante animada e Ondas do oceano sob a luz do luar).

7. **Games Retrô & Utilitários Interativos**:
   - **Jogo da Cobrinha (Snake):** Motor completo do clássico Snake renderizado diretamente no display de LED, controlável em tempo real.
   - **Placar de Jogos:** Placar para competições e partidas com botões de incremento/decremento rápidos.
   - **Cronômetro e Contagem Regressiva.**
   - **Simulador de Notificações:** Emissão de ícones de alerta fiéis para WhatsApp, Instagram, Discord, Email e Chamada Telefônica.

8. **Novo Aplicativo Nativo Windows em C# / .NET 8 WPF (`iDotMatrixPro`)**:
   - Foi desenvolvido um cliente nativo completo em **C# WPF com Material Design**.
   - Conexão BLE direta através das APIs nativas do Windows (`Windows.Devices.Bluetooth`), sem necessidade de instalar dependências Python.
   - Suporte à bandeja do sistema (*System Tray*), inicialização com o Windows e streaming contínuo de status.

9. **Launcher Automático no Windows (`start_gui.bat`)**:
   - Detecta e cria automaticamente o ambiente virtual isolado (`venv_windows`).
   - Instala e atualiza as dependências do `requirements.txt` sem necessidade de configurações manuais.

---

## 🖥️ As Telas do Novo iDotMatrix Studio Pro (`gui.py`)

A interface foi desenhada com tema escuro moderno (*Dark Theme / Glassmorphic*) e dividida em abas focadas em produtividade e entretenimento:

| Aba | Descrição |
| :--- | :--- |
| **⚡ Início & Hardware** | Dashboard com status da conexão BLE, controle rápido de liga/desliga, controle deslizante de brilho e transmissão do monitor de hardware do PC (CPU, GPU, RAM, temps). |
| **🕒 Relógio & Clima** | Seletor com 8 estilos de mostradores (Digital, Natal Festivo, Velocímetro Racing, Alto Contraste, Ampulheta, Neon, Sci-Fi e Arcade), formato 12/24h e card de previsão do tempo ao vivo. |
| **🎨 Estúdio DIY & Animação** | Editor de desenho pixel por pixel, gerenciador de paletas de cores, clonagem de frames e gravação de animações multi-quadros. |
| **🖼️ Galeria & Playlists** | Biblioteca de pixel art pré-montada, importação de PNG/JPEG/GIF do computador e modo carrossel contínuo. |
| **✍️ Letreiro de Texto** | Envio de mensagens personalizadas com rolagem (*marquee*), ajuste de velocidade, paleta de cores para texto e plano de fundo. |
| **🎵 Áudio & Relaxamento** | Equalizador animado em tempo real e cenas de ambiência para foco ou descanso (Fogueira e Mar Noturno). |
| **🎮 Games & Utilitários** | Jogo Snake jogável na matriz, placar de pontuação, cronômetro e envio de badges de notificações de apps. |

---

## 📦 Estrutura do Projeto

```plaintext
python3-idotmatrix-client/
├── core/                        # Núcleo modular da aplicação
│   ├── ble_controller.py        # Controlador Bluetooth BLE persistente (QThread + Asyncio)
│   ├── hardware_monitor.py      # Monitor de CPU/GPU/RAM e renderizador de matriz 32x32
│   ├── weather_service.py       # Serviço meteorológico e gerador de cards pixel art
│   ├── presets.py               # Estilos de relógio, pixel arts, motor do Snake e animações
│   └── cmd.py                   # Interface e comandos via linha de comando
│
├── iDotMatrixPro/               # Cliente nativo Windows WPF (.NET 8)
│   ├── MainWindow.xaml          # Interface rica em Material Design
│   ├── Services/                # Serviços de Bluetooth nativo WinRT, Tray e Hardware
│   └── publish/                 # Executável compilado pronto para uso
│
├── gui.py                       # Nova interface gráfica principal (PyQt5 Studio Pro)
├── gui_legacy.py                # Interface gráfica legada preservada para referência
├── app.py                       # Ponto de entrada para automação e CLI
├── start_gui.bat                # Inicializador automatizado com auto-instalação para Windows
├── requirements.txt             # Dependências Python atualizadas
└── fonts/                       # Fontes bitmap e tipografias compatíveis
```

---

## 🔧 Como Executar

### Opção 1: Executar a Nova Interface Python (Recomendado)

#### No Windows:
Basta dar um duplo clique no arquivo **`start_gui.bat`**.  
O script irá:
1. Criar o ambiente virtual `venv_windows` se ainda não existir.
2. Instalar as dependências necessárias automaticamente.
3. Iniciar o **iDotMatrix Studio Pro**.

#### Manualmente via Terminal (Linux, macOS ou Windows):
```bash
# 1. Clone o repositório ou acesse a pasta do projeto
cd python3-idotmatrix-client

# 2. Crie e ative o ambiente virtual
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/macOS:
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Inicie o estúdio
python gui.py
```

---

### Opção 2: Cliente Nativo Windows .NET 8 (`iDotMatrixPro`)

Se preferir utilizar o cliente nativo compilado em C# para Windows:
1. Acesse o diretório `iDotMatrixPro/publish/`.
2. Execute **`iDotMatrixPro.exe`**.
3. O aplicativo integra-se com a área de notificação do Windows (*System Tray*) e usa a pilha Bluetooth nativa do sistema.

---

### Opção 3: Modo Linha de Comando (CLI / Automações)

A interface por linha de comando continua totalmente suportada para automações, integrações com Home Assistant, scripts ou lives de streaming:

```bash
# Escanear displays próximos:
python app.py --scan

# Ligar/Desligar a tela:
python app.py --address "SEU_MAC_ADDRESS" --screen on
python app.py --address "SEU_MAC_ADDRESS" --screen off

# Ajustar brilho (1 a 100):
python app.py --address "SEU_MAC_ADDRESS" --brightness 75

# Definir modo relógio:
python app.py --address "SEU_MAC_ADDRESS" --clock

# Exibir imagem ou animação:
python app.py --address "SEU_MAC_ADDRESS" --image "caminho/para/imagem.png"
python app.py --address "SEU_MAC_ADDRESS" --gif "caminho/para/animacao.gif"

# Exibir texto em rolagem:
python app.py --address "SEU_MAC_ADDRESS" --text "Ola Mundo" --color "00FFCC"
```

---

## 🛠️ Tecnologias e Bibliotecas

- **[Python 3.10+](https://www.python.org/)**
- **[Bleak](https://github.com/hbldh/bleak):** Comunicação Bluetooth Low Energy assíncrona multiplataforma.
- **[PyQt5](https://riverbankcomputing.com/software/pyqt/):** Interface rica com suporte a temas modernos e renderização personalizada de widgets.
- **[Pillow (PIL)](https://python-pillow.org/):** Processamento gráfico, manipulação de pixels e renderização de frames.
- **[psutil](https://github.com/giampaolo/psutil):** Leitura de métricas e sensores do sistema em tempo real.
- **[requests](https://requests.readthedocs.io/):** Integrações HTTP com serviços meteorológicos.
- **[.NET 8 WPF](https://dotnet.microsoft.com/):** Cliente alternativo nativo de alta performance para Windows.

---

## 📄 Licença

Este projeto é distribuído sob a licença **GNU General Public License v3.0**. Consulte o arquivo [LICENSE](LICENSE) para obter mais detalhes.

---

## 🏛️ Projeto Original & Créditos

Este software é uma evolução direta construída a partir do projeto pioneiro de engenharia reversa [python3-idotmatrix-client](https://github.com/derkalle4/python3-idotmatrix-client) e da biblioteca [python3-idotmatrix-library](https://github.com/derkalle4/python3-idotmatrix-library). Expressamos nosso enorme respeito e gratidão a todos que iniciaram e contribuíram para tornar possível o controle dessas matrizes de LED fora do aplicativo móvel proprietário.

### 👥 Fundadores & Autores Originais

* **[Kalle Minkner](https://github.com/derkalle4)** (*derkalle4*) – Idealizador e Criador do Projeto Original.
* **[Jon-Mailes Graeffe](https://github.com/jmgraeffe)** (*jmgraeffe*) – Co-Fundador e Desenvolvedor.

### 🤝 Contribuintes & Engenharia Reversa

Um agradecimento especial a todos os incríveis desenvolvedores da comunidade open-source cujas pesquisas e contribuições viabilizaram a compreensão dos protocolos BLE do iDotMatrix:

* **[LordRippon](https://github.com/LordRippon)** – Engenharia reversa dos protocolos dos displays.
* **[8none1](https://github.com/8none1)** – Engenharia reversa dos protocolos e payloads Bluetooth.
* **[inselberg](https://github.com/inselberg)** – Engenharia reversa dos displays e rotinas gráficas.
* **[tekka007](https://github.com/tekka007)** – Refatoração do código e aprofundamento na engenharia reversa.
* **[TheBigWazz](https://github.com/thebigwazz)** – Primeira versão da GUI e ferramenta de busca de dispositivos.
* **[schorsch3000](https://github.com/schorsch3000)** – Correções pontuais e melhorias de compatibilidade.
* **[Othneil Drew](https://github.com/othneildrew/Best-README-Template)** – Estrutura base de template de documentação.

