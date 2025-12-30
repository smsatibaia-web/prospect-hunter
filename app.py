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
    page_title="Prospect Hunter 3.0",
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
# FUNÇÕES ÚTEIS
# =============================================================================
def limpar_telefone_gerar_link(telefone):
    """Gera link do WhatsApp limpo."""
    if not telefone or telefone == "Não encontrado":
        return None, None
    nums = re.sub(r'\D', '', telefone)
    if not nums: return None, None
    if 10 <= len(nums) <= 11: nums = "55" + nums
    link = f"https://web.whatsapp.com/send?phone={nums}"
    return nums, link

def get_driver():
    """Configura o driver Chrome (Cloud ou Local)."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Configuração para Streamlit Cloud
    if os.path.exists("/usr/bin/chromium") and os.path.exists("/usr/bin/chromedriver"):
        options.binary_location = "/usr/bin/chromium"
        service = Service("/usr/bin/chromedriver")
    else:
        # Configuração Local
        try:
            service = Service(ChromeDriverManager().install())
        except:
            return None
        
    return webdriver.Chrome(service=service, options=options)

# =============================================================================
# MOTOR DE BUSCA (SCRAPER ATUALIZADO)
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
            status_text.markdown(f"🔍 Buscando: **{nicho}** em {localizacao}...")
            termo = f"{nicho} near {localizacao}"
            
            try:
                driver.get("https://www.google.com/maps?hl=pt-BR")
                input_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
                input_box.clear(); input_box.send_keys(termo); input_box.send_keys(Keys.ENTER)
                time.sleep(3) 
            except: continue

            # Scroll para carregar
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
                    # Re-captura elementos para evitar erro
                    itens = driver.find_elements(By.CLASS_NAME, "hfpxzc")
                    if i >= len(itens): break
                    item = itens[i]
                    
                    nome = item.get_attribute("aria-label")
                    if not nome: continue

                    # Clica no item para abrir detalhes
                    driver.execute_script("arguments[0].click();", item)
                    time.sleep(2)
                    
                    # === EXTRAÇÃO DE DETALHES ===
                    url_maps = driver.current_url
                    telefone = "Não encontrado"
                    endereco = "Não informado"
                    nota = "Sem avaliações"
                    categoria = nicho
                    horario = "Não informado"

                    # 1. Telefone e Endereço (via botões laterais)
                    btns = driver.find_elements(By.TAG_NAME, "button")
                    for btn in btns:
                        aria = btn.get_attribute("aria-label")
                        if not aria: continue
                        
                        if "Telefone" in aria or "Phone" in aria:
                            telefone = aria.replace("Telefone: ", "").replace("Phone: ", "").strip()
                        
                        if "Endereço" in aria or "Address" in aria:
                            endereco = aria.replace("Endereço: ", "").replace("Address: ", "").strip()

                    # 2. Nota e Categoria (via texto no painel)
                    try:
                        # Tenta pegar a div que contém as estrelas (geralmente tem role="img")
                        estrelas = driver.find_element(By.CSS_SELECTOR, "span[role='img']")
                        lbl = estrelas.get_attribute("aria-label")
                        if lbl and ("estrelas" in lbl or "stars" in lbl):
                            nota = lbl # Ex: "4,8 estrelas 150 avaliações"
                    except: pass
                    
                    try:
                        # Tenta pegar a categoria específica (geralmente texto cinza abaixo do nome)
                        # No maps, a categoria costuma ser um botão com classe específica, mas varia.
                        # Vamos tentar uma abordagem genérica por hierarquia se necessário.
                        pass 
                    except: pass

                    # 3. Horário (Status simples)
                    try:
                        # Procura aria-labels que indiquem status
                        labels_status = ["Aberto", "Fechado", "Open", "Closed"]
                        divs = driver.find_elements(By.TAG_NAME, "div")
                        for div in divs:
                            aria_div = div.get_attribute("aria-label")
                            if aria_div and any(s in aria_div for s in labels_status):
                                # Geralmente é algo como "Aberto ⋅ Fecha às 18:00"
                                horario = aria_div
                                break
                    except: pass

                    # Processamento final
                    tel_limpo, link_wpp = limpar_telefone_gerar_link(telefone)
                    
                    dados = {
                        "Empresa": nome,
                        "Nicho": nicho,
                        "Telefone": telefone,
                        "Endereço": endereco,
                        "Avaliação": nota,
                        "Status/Horário": horario,
                        "WhatsApp Link": link_wpp if link_wpp else "",
                        "Maps Link": url_maps
                    }
                    resultados.append(dados)
                    
                except Exception: continue
            
            progress_bar.progress((idx + 1) / total_steps)
            
    except Exception as e:
        st.error(f"Erro: {e}")
    finally:
        if driver: driver.quit()
        status_text.empty()
        progress_bar.empty()
        
    return pd.DataFrame(resultados)

# =============================================================================
# INTERFACE (FRONTEND)
# =============================================================================

st.title("🎯 Prospect Hunter 3.0")
st.markdown("### Ficha Técnica e Contato Rápido")

# Sidebar
with st.sidebar:
    st.header("Configuração")
    local_input = st.text_input("📍 Localização", placeholder="Ex: Centro, Atibaia - SP")
    
    todos = st.checkbox("Selecionar Todos")
    if todos:
        nichos_selecionados = st.multiselect("Nichos", PADRAO_NICHOS, default=PADRAO_NICHOS)
    else:
        nichos_selecionados = st.multiselect("Nichos", PADRAO_NICHOS, default=["Advocacia"])
        
    novo = st.text_input("Novo Nicho")
    if st.button("Add") and novo:
        PADRAO_NICHOS.append(novo); st.rerun()

    max_res = st.slider("Resultados por Nicho", 5, 50, 10)
    st.divider()
    btn_buscar = st.button("🚀 Iniciar Varredura", type="primary")

# Estado
if "df_resultados" not in st.session_state:
    st.session_state.df_resultados = pd.DataFrame()

# Execução
if btn_buscar:
    if not local_input or not nichos_selecionados:
        st.warning("Preencha local e nichos.")
    else:
        with st.spinner("Extraindo fichas técnicas..."):
            st.session_state.df_resultados = pd.DataFrame()
            novo_df = run_scraper(local_input, nichos_selecionados, max_res)
            
            if not novo_df.empty:
                st.session_state.df_resultados = novo_df
                st.success(f"{len(novo_df)} leads encontrados!")
            else:
                st.warning("Nenhum resultado.")

# Visualização
if not st.session_state.df_resultados.empty:
    df = st.session_state.df_resultados
    
    st.divider()
    
    # Tabela Principal
    st.subheader("📋 Lista de Leads")
    st.data_editor(
        df,
        column_config={
            "WhatsApp Link": st.column_config.LinkColumn("WhatsApp", display_text="💬 Conversar"),
            "Maps Link": st.column_config.LinkColumn("Google Maps", display_text="🗺️ Ver"),
            "Avaliação": st.column_config.TextColumn("Feedback", help="Nota e Qtd Avaliações"),
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Download
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')
    
    col_dl, col_cl = st.columns([4, 1])
    with col_dl:
        st.download_button("📥 Baixar Planilha Excel", output.getvalue(), f"leads_{int(time.time())}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with col_cl:
        if st.button("Limpar"): st.session_state.df_resultados = pd.DataFrame(); st.rerun()

    # --- FICHA TÉCNICA DETALHADA ---
    st.divider()
    st.subheader("📝 Ficha Técnica da Empresa")
    
    empresas = df["Empresa"].tolist()
    selecao = st.selectbox("Selecione para ver detalhes:", empresas)
    
    if selecao:
        dados = df[df["Empresa"] == selecao].iloc[0]
        
        # Container Visual estilo "Card"
        with st.container():
            # Cabeçalho com Nome e Avaliação
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"## {dados['Empresa']}")
                st.markdown(f"**Nicho:** {dados['Nicho']}")
            with c2:
                st.metric(label="Avaliação", value=dados['Avaliação'].split(" ")[0] if dados['Avaliação'][0].isdigit() else "-", delta=dados['Avaliação'])

            st.markdown("---")
            
            # Informações Técnicas
            col_info, col_actions = st.columns([2, 1])
            
            with col_info:
                st.markdown(f"📍 **Endereço:** \n{dados['Endereço']}")
                st.markdown(f"🕒 **Horário/Status:** \n{dados['Status/Horário']}")
                st.markdown(f"📞 **Telefone:** {dados['Telefone']}")
            
            with col_actions:
                st.markdown("### Ações Rápidas")
                if dados["WhatsApp Link"]:
                    st.link_button("💬 Chamar no WhatsApp", dados["WhatsApp Link"], type="primary", use_container_width=True)
                else:
                    st.button("🚫 Sem WhatsApp", disabled=True, use_container_width=True)
                
                if dados["Maps Link"]:
                    st.link_button("🗺️ Ver no Google Maps", dados["Maps Link"], use_container_width=True)

else:
    if not btn_buscar:
        st.info("👈 Use a barra lateral para configurar sua busca.")
