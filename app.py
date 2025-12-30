import streamlit as st
import pandas as pd
import time
import os
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
    page_title="Prospect Hunter 2.0",
    page_icon="🎯",
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
# FUNÇÕES ÚTEIS (Limpeza e Links)
# =============================================================================
def limpar_telefone_gerar_link(telefone):
    """
    Remove caracteres não numéricos e formata para link do WhatsApp.
    Assume Brasil (55) se o número não tiver código de país.
    """
    if not telefone or telefone == "Não encontrado":
        return None, None
    
    # Remove tudo que não é dígito
    nums = re.sub(r'\D', '', telefone)
    
    if not nums:
        return None, None
        
    # Lógica simples para garantir o 55 (Brasil)
    # Se tiver 10 ou 11 dígitos, é DDD + Número (ex: 11999999999), adiciona 55
    if 10 <= len(nums) <= 11:
        nums = "55" + nums
    
    link = f"https://web.whatsapp.com/send?phone={nums}"
    return nums, link

def extrair_lat_long(url_maps):
    """
    Tenta extrair latitude e longitude da URL do Google Maps para plotar no mapa.
    Padrão comum: @-23.12345,-46.12345
    """
    if not url_maps: return None, None
    try:
        match = re.search(r'@([-.\d]+),([-.\d]+)', url_maps)
        if match:
            return float(match.group(1)), float(match.group(2))
    except:
        pass
    return None, None

# =============================================================================
# CONFIGURAÇÃO DO DRIVER
# =============================================================================
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    chromium_path = "/usr/bin/chromium"
    chromedriver_path = "/usr/bin/chromedriver"
    
    if os.path.exists(chromium_path) and os.path.exists(chromedriver_path):
        options.binary_location = chromium_path
        service = Service(chromedriver_path)
    else:
        try:
            service = Service(ChromeDriverManager().install())
        except Exception as e:
            st.error(f"Erro ao configurar driver local: {e}")
            return None
        
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# =============================================================================
# MOTOR DE BUSCA (SCRAPER)
# =============================================================================
def run_scraper(localizacao, nichos_selecionados, max_results=10):
    driver = get_driver()
    if not driver: return pd.DataFrame()

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
                input_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
                input_box.clear()
                input_box.send_keys(termo)
                input_box.send_keys(Keys.ENTER)
                time.sleep(3) 
            except Exception as e:
                continue

            try:
                painel = driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
                for _ in range(2): 
                    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", painel)
                    time.sleep(1.5)
            except: pass

            links = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            limit = min(len(links), max_results)
            
            for i in range(limit):
                try:
                    itens = driver.find_elements(By.CLASS_NAME, "hfpxzc")
                    if i >= len(itens): break
                    item = itens[i]
                    
                    nome = item.get_attribute("aria-label")
                    if not nome: continue

                    # Clica e aguarda atualização da URL
                    try:
                        item.click()
                        time.sleep(2) 
                    except:
                        driver.execute_script("arguments[0].click();", item)
                        time.sleep(2)
                    
                    # Captura URL atual (Link do Maps)
                    url_maps = driver.current_url
                    
                    telefone = "Não encontrado"
                    site = ""
                    
                    try:
                        btns = driver.find_elements(By.TAG_NAME, "button")
                        for btn in btns:
                            aria = btn.get_attribute("aria-label")
                            if aria:
                                if "Telefone" in aria or "Phone" in aria:
                                    telefone = aria.replace("Telefone: ", "").replace("Phone: ", "").strip()
                                if "Website" in aria or "Site" in aria:
                                    site_temp = btn.get_attribute("aria-label").replace("Website: ", "").strip()
                                    if "." in site_temp: site = site_temp
                        
                        if not site:
                            try:
                                web_elem = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority']")
                                site = web_elem.get_attribute("href")
                            except: pass
                    except: pass
                    
                    # Processa Telefone para WhatsApp
                    tel_limpo, link_wpp = limpar_telefone_gerar_link(telefone)
                    
                    # Extrai Lat/Long para o mapa visual
                    lat, lon = extrair_lat_long(url_maps)

                    dados = {
                        "Empresa": nome,
                        "Nicho": nicho,
                        "Telefone": telefone,
                        "WhatsApp Link": link_wpp if link_wpp else "",
                        "Maps Link": url_maps,
                        "Site": site,
                        "latitude": lat, # Usado internamente para o mapa
                        "longitude": lon # Usado internamente para o mapa
                    }
                    resultados.append(dados)
                    
                except Exception as e:
                    continue
            
            progress_bar.progress((idx + 1) / total_steps)
            
    except Exception as e:
        st.error(f"Erro fatal: {e}")
    finally:
        if driver: driver.quit()
        status_text.empty()
        progress_bar.empty()
        
    return pd.DataFrame(resultados)

# =============================================================================
# INTERFACE (FRONTEND)
# =============================================================================

st.title("🎯 Prospect Hunter 2.0")
st.markdown("Busca de Leads com Links Diretos para WhatsApp e Maps.")

# Sidebar
with st.sidebar:
    st.header("Configuração")
    local_input = st.text_input("📍 Localização", placeholder="Ex: Centro, Atibaia - SP")
    
    todos = st.checkbox("Selecionar Todos Nichos")
    if todos:
        nichos_selecionados = st.multiselect("Nichos", PADRAO_NICHOS, default=PADRAO_NICHOS)
    else:
        nichos_selecionados = st.multiselect("Nichos", PADRAO_NICHOS, default=["Advocacia"])
        
    novo_nicho = st.text_input("Novo Nicho")
    if st.button("Add Nicho"):
        if novo_nicho and novo_nicho not in PADRAO_NICHOS:
            PADRAO_NICHOS.append(novo_nicho)
            st.rerun()

    max_res = st.slider("Max resultados", 5, 50, 10)
    st.divider()
    btn_buscar = st.button("🚀 Iniciar Varredura", type="primary")

# Estado
if "df_resultados" not in st.session_state:
    st.session_state.df_resultados = pd.DataFrame()

# Lógica de Busca
if btn_buscar:
    if not local_input or not nichos_selecionados:
        st.warning("Preencha local e nichos.")
    else:
        with st.spinner("Varrendo o Google Maps..."):
            st.session_state.df_resultados = pd.DataFrame()
            novo_df = run_scraper(local_input, nichos_selecionados, max_res)
            
            if not novo_df.empty:
                st.session_state.df_resultados = novo_df
                st.success(f"Sucesso! {len(novo_df)} empresas encontradas.")
            else:
                st.warning("Nada encontrado.")

# Exibição
if not st.session_state.df_resultados.empty:
    df = st.session_state.df_resultados
    
    st.divider()
    st.subheader("📋 Lista de Leads")
    
    # Configuração das Colunas (Transforma texto em Link clicável e esconde lat/lon)
    st.data_editor(
        df,
        column_config={
            "WhatsApp Link": st.column_config.LinkColumn(
                "WhatsApp API", 
                display_text="Abrir Conversa",
                help="Clique para abrir o WhatsApp Web"
            ),
            "Maps Link": st.column_config.LinkColumn(
                "Google Maps", 
                display_text="Ver no Maps"
            ),
            "latitude": None, # Oculta na tabela
            "longitude": None # Oculta na tabela
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Botão de Download
    col_dl, col_trash = st.columns([3, 1])
    with col_dl:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Remove lat/lon do Excel para ficar limpo
            df_export = df.drop(columns=['latitude', 'longitude'], errors='ignore')
            df_export.to_excel(writer, index=False, sheet_name='Leads')
        
        st.download_button(
            label="📥 Baixar Planilha Excel (Com Links)",
            data=output.getvalue(),
            file_name=f"leads_{int(time.time())}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col_trash:
        if st.button("Limpar Tudo"):
            st.session_state.df_resultados = pd.DataFrame()
            st.rerun()

    # --- ÁREA DE DETALHES E MAPA ABAIXO DO DOWNLOAD ---
    st.divider()
    st.subheader("📍 Detalhes & Localização Visual")
    
    # Seletor de Empresa
    lista_empresas = df["Empresa"].tolist()
    empresa_selecionada = st.selectbox("Selecione uma empresa para ver no mapa e contatar:", lista_empresas)
    
    if empresa_selecionada:
        # Filtra os dados da empresa selecionada
        dados_emp = df[df["Empresa"] == empresa_selecionada].iloc[0]
        
        # Área de Botões de Ação Rápida
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info(f"📞 Tel: {dados_emp['Telefone']}")
        with c2:
            if dados_emp["WhatsApp Link"]:
                st.link_button("💬 Abrir WhatsApp Web", dados_emp["WhatsApp Link"], type="primary", use_container_width=True)
            else:
                st.button("Sem WhatsApp", disabled=True, use_container_width=True)
        with c3:
            if dados_emp["Maps Link"]:
                st.link_button("🗺️ Abrir no Google Maps", dados_emp["Maps Link"], use_container_width=True)
        
        # Mapa Visual
        st.markdown(f"**Localização Aproximada:** {dados_emp['Local'] if pd.isna(dados_emp['latitude']) else ''}")
        
        # Se tiver latitude e longitude extraídas, mostra o mapa
        if pd.notna(dados_emp['latitude']) and pd.notna(dados_emp['longitude']):
            map_data = pd.DataFrame({
                'lat': [dados_emp['latitude']],
                'lon': [dados_emp['longitude']]
            })
            st.map(map_data, zoom=15)
        else:
            st.warning("Coordenadas exatas não puderam ser extraídas para o mapa visual (use o botão 'Abrir no Google Maps').")

else:
    if not btn_buscar:
        st.info("👈 Configure a busca na esquerda.")
