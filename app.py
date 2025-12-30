import streamlit as st
import pandas as pd
import time
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Prospect Hunter Web",
    page_icon="🕵️",
    layout="wide"
)

# Nichos Padrão (incorporados no código para não depender de json externo)
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
# FUNÇÕES DE SCRAPING
# =============================================================================
def get_driver():
    """Configura o driver Chrome para rodar em ambiente Web (Headless)"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Essencial para rodar em servidores/streamlit
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extrair_email_do_site(driver, url):
    """Tenta extrair email visitando o site (simplificado)"""
    import re
    import requests
    if not url or "google" in url: return ""
    if not url.startswith("http"): url = "http://" + url
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
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
    wait = WebDriverWait(driver, 10)
    resultados = []
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    total_steps = len(nichos_selecionados)
    
    try:
        for idx, nicho in enumerate(nichos_selecionados):
            status_text.write(f"🔍 Buscando: **{nicho}** em {localizacao}...")
            termo = f"{nicho} near {localizacao}"
            
            driver.get("https://www.google.com/maps")
            
            try:
                input_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
                input_box.clear()
                input_box.send_keys(termo)
                input_box.send_keys(Keys.ENTER)
                time.sleep(3) # Aguarda carregamento inicial
            except Exception as e:
                st.error(f"Erro ao buscar {nicho}: {e}")
                continue

            # Scroll para carregar mais resultados
            try:
                painel = driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
                for _ in range(2): # Reduzi o scroll para ser mais rápido na web
                    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", painel)
                    time.sleep(1.5)
            except:
                pass

            links = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            limit = min(len(links), max_results) # Limita para não demorar eternamente
            
            for i in range(limit):
                try:
                    # Precisamos re-buscar os elementos para evitar StaleElementReferenceException
                    itens = driver.find_elements(By.CLASS_NAME, "hfpxzc")
                    if i >= len(itens): break
                    item = itens[i]
                    
                    nome = item.get_attribute("aria-label")
                    item.click()
                    time.sleep(1.5)
                    
                    telefone = "Não encontrado"
                    site = ""
                    
                    # Extração de dados do painel lateral
                    try:
                        btns = driver.find_elements(By.TAG_NAME, "button")
                        for btn in btns:
                            aria = btn.get_attribute("aria-label")
                            if aria:
                                if "Telefone" in aria or "Phone" in aria:
                                    telefone = aria.replace("Telefone: ", "").replace("Phone: ", "")
                                if "Website" in aria or "Site" in aria:
                                    site_candidato = btn.get_attribute("aria-label").replace("Website: ", "")
                                    if "." in site_candidato: site = site_candidato
                    except: pass
                    
                    if not site:
                        try:
                            web_btn = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority']")
                            site = web_btn.get_attribute("href")
                        except: pass
                    
                    email = ""
                    if site:
                        email = extrair_email_do_site(driver, site)

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
                    continue
            
            # Atualiza barra de progresso
            progress_bar.progress((idx + 1) / total_steps)
            
    except Exception as e:
        st.error(f"Erro fatal no scraper: {e}")
    finally:
        driver.quit()
        status_text.empty()
        progress_bar.empty()
        
    return pd.DataFrame(resultados)

# =============================================================================
# INTERFACE (FRONTEND)
# =============================================================================

st.title("🕵️ Prospect Hunter - Web Edition")
st.markdown("Busca de leads locais via Google Maps sem banco de dados fixo.")

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
    
    btn_buscar = st.button("🚀 Iniciar Varredura", type="primary")

# Área Principal
if "df_resultados" not in st.session_state:
    st.session_state.df_resultados = pd.DataFrame()

if btn_buscar:
    if not local_input:
        st.warning("Por favor, digite uma localização.")
    elif not nichos_selecionados:
        st.warning("Selecione pelo menos um nicho.")
    else:
        with st.spinner("Iniciando motor de busca... Isso pode levar alguns segundos."):
            novo_df = run_scraper(local_input, nichos_selecionados, max_res)
            
            if not novo_df.empty:
                # Concatena com resultados anteriores se houver (opcional, aqui substituímos para manter simples)
                st.session_state.df_resultados = novo_df
                st.success(f"Busca concluída! {len(novo_df)} empresas encontradas.")
            else:
                st.warning("Nenhum resultado encontrado. Tente outra localização.")

# Exibição dos Resultados
if not st.session_state.df_resultados.empty:
    st.divider()
    st.subheader("📋 Resultados Encontrados")
    
    # Editor de dados (permite corrigir manualmente antes de baixar)
    df_editavel = st.data_editor(
        st.session_state.df_resultados,
        num_rows="dynamic",
        use_container_width=True
    )
    
    # Área de Exportação
    col1, col2 = st.columns(2)
    
    # Gerar Excel em memória
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_editavel.to_excel(writer, index=False, sheet_name='Prospects')
    processed_data = output.getvalue()
    
    with col1:
        st.download_button(
            label="📥 Baixar Planilha Excel",
            data=processed_data,
            file_name=f"prospects_{local_input}_{int(time.time())}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    
    with col2:
        if st.button("🧹 Limpar Resultados"):
            st.session_state.df_resultados = pd.DataFrame()
            st.rerun()

else:
    st.info("Configure a busca na barra lateral e clique em Iniciar.")