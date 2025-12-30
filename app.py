import streamlit as st
import pandas as pd
import time
import os
import requests
import re
from io import BytesIO

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Prospect Hunter Web",
    page_icon="🕵️",
    layout="wide"
)

# Nichos Padrão
PADRAO_NICHOS = [
    "Advocacia", "Contabilidade", "Imobiliária", "Consultoria de TI", "Agência de Marketing",
    "Pizzaria", "Hamburgueria", "Restaurante Japonês", "Padaria", "Confeitaria",
    "Oficina Mecânica", "Lava Rápido", "Concessionária", "Auto Peças",
    "Dentista", "Clínica Médica", "Veterinário", "Pet Shop", "Academia",
    "Salão de Beleza", "Barbearia", "Estética", "Manicure",
    "Escola de Idiomas", "Escola Infantil", "Faculdade",
    "Loja de Roupas", "Loja de Calçados", "Loja de Móveis", "Material de Construção",
    "Hotel", "Pousada", "Agência de Viagens", "Transportadora",
    "Supermercado", "Farmácia", "Floricultura", "Gráfica"
]

# =============================================================================
# FUNÇÕES DE CONFIGURAÇÃO DO DRIVER (CORREÇÃO DO ERRO)
# =============================================================================
def get_driver():
    """
    Configura o driver do Chrome.
    Detecta automaticamente se está no Streamlit Cloud (Linux) ou Local (Windows/Mac).
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Roda sem interface gráfica (obrigatório na nuvem)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Caminhos padrão do Chromium no ambiente Linux do Streamlit Cloud
    chromium_path = "/usr/bin/chromium"
    chromedriver_path = "/usr/bin/chromedriver"
    
    # Verifica se estamos no ambiente Cloud (Linux com pacotes instalados)
    if os.path.exists(chromium_path) and os.path.exists(chromedriver_path):
        options.binary_location = chromium_path
        service = Service(chromedriver_path)
    else:
        # Ambiente Local: Usa o gerenciador para baixar a versão correta
        try:
            service = Service(ChromeDriverManager().install())
        except Exception as e:
            # Fallback genérico se o manager falhar
            st.error(f"Erro ao configurar driver local: {e}")
            return None
        
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# =============================================================================
# FUNÇÕES DE EXTRAÇÃO
# =============================================================================
def extrair_email_do_site(url):
    """Tenta extrair email visitando o site (simplificado)"""
    if not url or "google" in url: return ""
    if not url.startswith("http"): url = "http://" + url
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, timeout=5, headers=headers)
        if response.status_code == 200:
            emails = set(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", response.text, re.I))
            validos = [e for e in emails if not e.endswith(('.png', '.jpg', '.js', '.css', '.svg'))]
            if validos: return validos[0]
    except:
        pass
    return ""

def run_scraper(localizacao, nichos_selecionados, max_results=10):
    """Função principal de varredura"""
    driver = get_driver()
    if not driver:
        return pd.DataFrame()

    wait = WebDriverWait(driver, 10)
    resultados = []
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    total_steps = len(nichos_selecionados)
    
    try:
        for idx, nicho in enumerate(nichos_selecionados):
            status_text.write(f"🔍 Buscando: **{nicho}** em {localizacao}...")
            termo = f"{nicho} near {localizacao}"
            
            try:
                driver.get("https://www.google.com/maps?hl=pt-BR")
                
                # Aguarda e interage com a caixa de busca
                input_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
                input_box.clear()
                input_box.send_keys(termo)
                input_box.send_keys(Keys.ENTER)
                time.sleep(3) 
            except Exception as e:
                st.warning(f"Erro ao iniciar busca para {nicho}: {e}")
                continue

            # Tenta rolar a lista de resultados
            try:
                painel = driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
                for _ in range(2): 
                    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", painel)
                    time.sleep(1.5)
            except:
                pass # Às vezes o painel não carrega ou tem poucos resultados

            # Coleta os links dos locais
            links = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            limit = min(len(links), max_results)
            
            for i in range(limit):
                try:
                    # Re-busca elementos para evitar StaleElement
                    itens = driver.find_elements(By.CLASS_NAME, "hfpxzc")
                    if i >= len(itens): break
                    item = itens[i]
                    
                    nome = item.get_attribute("aria-label")
                    if not nome: continue

                    # Clica para ver detalhes
                    try:
                        item.click()
                        time.sleep(1.5)
                    except:
                        driver.execute_script("arguments[0].click();", item)
                        time.sleep(1.5)
                    
                    telefone = "Não encontrado"
                    site = ""
                    
                    # Extração Lateral
                    try:
                        # Procura botões com aria-labels específicos
                        btns = driver.find_elements(By.TAG_NAME, "button")
                        for btn in btns:
                            aria = btn.get_attribute("aria-label")
                            if aria:
                                if "Telefone" in aria or "Phone" in aria:
                                    telefone = aria.replace("Telefone: ", "").replace("Phone: ", "").strip()
                                if "Website" in aria or "Site" in aria:
                                    site_temp = btn.get_attribute("aria-label").replace("Website: ", "").strip()
                                    if "." in site_temp: site = site_temp
                        
                        # Fallback para site
                        if not site:
                            try:
                                web_elem = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority']")
                                site = web_elem.get_attribute("href")
                            except: pass
                            
                    except: pass
                    
                    email = ""
                    if site:
                        email = extrair_email_do_site(site)

                    dados = {
                        "Empresa": nome,
                        "Nicho": nicho,
                        "Local": localizacao,
                        "Telefone": telefone,
                        "Site": site,
                        "Email": email
                    }
                    resultados.append(dados)
                    
                except Exception as e:
                    # Erro em um item não deve parar o loop
                    continue
            
            progress_bar.progress((idx + 1) / total_steps)
            
    except Exception as e:
        st.error(f"Erro fatal durante a execução: {e}")
    finally:
        if driver:
            driver.quit()
        status_text.empty()
        progress_bar.empty()
        
    return pd.DataFrame(resultados)

# =============================================================================
# INTERFACE (FRONTEND)
# =============================================================================

st.title("🕵️ Prospect Hunter - Web Edition")
st.markdown("Busca de leads locais via Google Maps (Versão Cloud).")

# Sidebar de Controles
with st.sidebar:
    st.header("Configuração")
    local_input = st.text_input("📍 Localização", placeholder="Ex: Centro, Atibaia - SP")
    
    st.subheader("Nichos")
    todos = st.checkbox("Selecionar Todos")
    
    if todos:
        nichos_selecionados = st.multiselect("Selecione os Nichos", PADRAO_NICHOS, default=PADRAO_NICHOS)
    else:
        nichos_selecionados = st.multiselect("Selecione os Nichos", PADRAO_NICHOS, default=["Advocacia"])
        
    novo_nicho = st.text_input("Adicionar Nicho Customizado")
    if st.button("Adicionar"):
        if novo_nicho and novo_nicho not in PADRAO_NICHOS:
            PADRAO_NICHOS.append(novo_nicho)
            st.success(f"{novo_nicho} adicionado!")
            st.rerun()

    max_res = st.slider("Max resultados por nicho", 5, 50, 10)
    
    st.divider()
    btn_buscar = st.button("🚀 Iniciar Varredura", type="primary")

# Área Principal - Lógica de Estado
if "df_resultados" not in st.session_state:
    st.session_state.df_resultados = pd.DataFrame()

if btn_buscar:
    if not local_input:
        st.warning("Por favor, digite uma localização.")
    elif not nichos_selecionados:
        st.warning("Selecione pelo menos um nicho.")
    else:
        with st.spinner("Iniciando motor de busca... Isso pode levar alguns segundos."):
            # Limpa resultados anteriores
            st.session_state.df_resultados = pd.DataFrame()
            
            novo_df = run_scraper(local_input, nichos_selecionados, max_res)
            
            if not novo_df.empty:
                st.session_state.df_resultados = novo_df
                st.success(f"Busca concluída! {len(novo_df)} empresas encontradas.")
            else:
                st.warning("Nenhum resultado encontrado. Tente verificar a localização ou os nichos.")

# Exibição dos Resultados
if not st.session_state.df_resultados.empty:
    st.divider()
    st.subheader("📋 Resultados Encontrados")
    
    # Editor de dados interativo
    df_editavel = st.data_editor(
        st.session_state.df_resultados,
        num_rows="dynamic",
        use_container_width=True
    )
    
    st.divider()
    col1, col2 = st.columns(2)
    
    # Botão de Download Excel
    with col1:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_editavel.to_excel(writer, index=False, sheet_name='Prospects')
        processed_data = output.getvalue()
        
        st.download_button(
            label="📥 Baixar Planilha Excel",
            data=processed_data,
            file_name=f"prospects_{int(time.time())}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    
    # Botão de Limpar
    with col2:
        if st.button("🧹 Limpar Resultados"):
            st.session_state.df_resultados = pd.DataFrame()
            st.rerun()

else:
    if not btn_buscar:
        st.info("👈 Configure a busca na barra lateral e clique em Iniciar.")
