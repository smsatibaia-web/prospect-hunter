# 🎯 Prospect Hunter 2.0 (Web Edition)

Ferramenta de automação para geração de leads (prospecção) baseada em localização. O sistema varre o Google Maps em busca de empresas de nichos específicos, extrai contatos e gera planilhas enriquecidas com links diretos para WhatsApp e Geolocalização.

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
