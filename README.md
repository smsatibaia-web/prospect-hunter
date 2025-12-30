# 🎯 Prospect Hunter 2.0 (Web Edition)

Ferramenta de automação para geração de leads (prospecção) baseada em localização. O sistema varre o Google Maps em busca de empresas de nichos específicos, extrai contatos e gera planilhas enriquecidas com links diretos para WhatsApp e Geolocalização.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://prospect-hunter-l7juemqf5jwzubevkoeh99.streamlit.app/)

> **🔗 Acesse o sistema online:** [Prospect Hunter 2.0 · Streamlit](COLE_O_LINK_DO_SEU_APP_AQUI)

![Status](https://img.shields.io/badge/Status-Functional-brightgreen)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31%2B-red)

## 🚀 Funcionalidades

- **Busca por Geolocalização:** Define um ponto (ex: "Centro, Atibaia - SP") e varre arredores.
- **Multinicho:** Busca simultânea por múltiplos tipos de comércio (Advocacia, Padarias, Oficinas, etc.).
- **Enriquecimento de Dados:**
  - 📞 **Telefone:** Extração do contato público.
  - 💬 **WhatsApp API:** Gera link direto (`wa.me`) limpando o número e adicionando DDI.
  - 🗺️ **Google Maps:** Captura o link exato e coordenadas (Lat/Lon) para visualização.
  - 🌐 **Website:** Identifica site oficial se disponível.
- **Visualização em Mapa:** Plota os resultados encontrados em um mapa interativo.
- **Exportação:** Gera planilha Excel (`.xlsx`) formatada e pronta para uso.

## 🛠️ Instalação e Uso Local

Para rodar na sua máquina:

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/SEU-USUARIO/prospect-hunter.git](https://github.com/SEU-USUARIO/prospect-hunter.git)
   cd prospect-hunter
Instale as dependências:

Bash

pip install -r requirements.txt
Execute a aplicação:

Bash

streamlit run app.py
Nota: O sistema detectará automaticamente que você está em ambiente local e usará o webdriver-manager para baixar o driver do Chrome.

☁️ Deploy no Streamlit Cloud
Este projeto está configurado para rodar gratuitamente no Streamlit Community Cloud.

Arquivos Críticos para Cloud:
packages.txt: Instala o Chromium e o Driver no servidor Linux (Essencial).

app.py: Contém lógica de detecção de ambiente para usar os binários do sistema (/usr/bin/chromium).

Como subir:
Faça um Fork deste repositório.

Acesse share.streamlit.io.

Conecte seu GitHub e selecione este projeto.

O deploy será automático.

📦 Estrutura do Projeto
Plaintext

prospect-hunter/
├── app.py              # Aplicação principal (Lógica + Interface)
├── requirements.txt    # Bibliotecas Python (Selenium, Pandas, etc.)
├── packages.txt        # Dependências do Sistema (Chromium para Cloud)
└── README.md           # Esta documentação
⚠️ Aviso Legal
Esta ferramenta utiliza automação de navegador (Web Scraping). O uso excessivo ou rápido demais pode gerar bloqueios temporários por parte do provedor dos dados. Use com moderação e responsabilidade.

Desenvolvido com Python e Streamlit.
