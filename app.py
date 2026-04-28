import streamlit as st
import requests
import uuid
import os
import json
import pandas as pd

# ==========================================
# CONSTANTES E CONFIGURAÇÕES GERAIS
# ==========================================
LANGFLOW_API_URL = "https://gushenrique-ai-marketsense-playground.hf.space/api/v1/run/54c543c5-663a-49eb-8107-cce96dcc964c"
API_KEY = os.environ.get("LANGFLOW_API_KEY")

SAUDACOES = {"olá", "ola", "oi", "bom dia", "boa tarde", "boa noite", "opa", "eae", "hello"}

st.set_page_config(page_title="AI MarketSense | Inteligência de Mercado", page_icon="📊", layout="wide") # Mudança para 'wide' para aproveitar a barra lateral

# ==========================================
# GERENCIAMENTO DE SESSÃO E ESTADO
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Gatilho para perguntas sugeridas
prompt_sugerido = None

# ==========================================
# UI: BARRA LATERAL (CONTROLES E EXEMPLOS)
# ==========================================
with st.sidebar:
    st.image("fundo.png", use_container_width=True) # Movemos a imagem para a sidebar para ficar mais com cara de dashboard
    st.markdown("---")
    
    st.markdown("### ⚙️ Controles da Sessão")
    if st.button("🗑️ Limpar Histórico de Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
        
    st.markdown("---")
    st.markdown("### 💡 Exemplos de Perguntas")
    st.caption("Clique em um botão abaixo para pesquisar rapidamente:")
    
    # Botões que preenchem o prompt automaticamente
    if st.button("📈 Setores em alta em Blumenau", use_container_width=True):
        prompt_sugerido = "Quais são os 5 setores (CNAE) com mais empresas abertas no último trimestre em Blumenau?"
    
    if st.button("⚖️ LTDA vs S.A. em Joinville", use_container_width=True):
        prompt_sugerido = "Faça um comparativo entre empresas Sociedade Limitada e Sociedade Anônima ativas em Joinville."
        
    if st.button("💼 Empresas com Administradores", use_container_width=True):
        prompt_sugerido = "Quantos grupos empresariais ativos em SC possuem sócio com qualificação de Administrador?"

# ==========================================
# UI: ÁREA PRINCIPAL E TELA DE BOAS VINDAS
# ==========================================
st.title("📊 AI MarketSense")
st.markdown("<p style='color: #a0aab2; font-size: 1em;'>Central de Inteligência de Mercado (Dados da Receita Federal - SC)</p>", unsafe_allow_html=True)
st.markdown("---")

# Se não houver mensagens, mostra o painel de introdução (Empty State) igual ao print
if len(st.session_state.messages) == 0:
    st.markdown("### Faça suas perguntas sobre:")
    st.markdown("""
    * 🎯 **Mapeamento de Nichos** (CNAEs dominantes, setores em expansão)
    * 📍 **Geolocalização Estratégica** (Densidade de empresas em Joinville, Blumenau, etc.)
    * 🏢 **Maturidade e Porte** (Idade das empresas, capital social declarado)
    * 💼 **Estrutura Societária** (Presença de administradores formais, tipos jurídicos)
    """)
    st.info("👈 Use os botões no menu lateral para começar com exemplos rápidos ou digite sua pergunta abaixo.")

# ==========================================
# FUNÇÕES DE LÓGICA E RENDERIZAÇÃO
# ==========================================
def renderizar_mensagem(conteudo):
    st.markdown(conteudo)
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📥 Baixar Relatório (.txt)",
            data=conteudo.encode('utf-8'),
            file_name="relatorio_marketsense.txt",
            mime="text/plain",
            use_container_width=True,
            key=f"btn_dw_{hash(conteudo)}"
        )
        
    with col2:
        if st.button("📝 Criar Press Release", key=f"btn_pr_{hash(conteudo)}", use_container_width=True):
            prompt_pr = f"Aja como um Assessor de Imprensa Sênior. Transforme os dados da análise abaixo em um press release profissional de 3 parágrafos para portais de negócios. Destaque a autoridade da nossa inteligência de mercado.\n\nDADOS DA ANÁLISE:\n{conteudo}"
            st.success("Copiado! Envie o comando abaixo no chat para gerar:")
            st.code(prompt_pr, language="markdown")

def consultar_langflow(prompt_usuario, session_id):
    payload = {
        "output_type": "chat",
        "input_type": "chat",
        "input_value": prompt_usuario,
        "session_id": session_id
    }
    headers = {"x-api-key": API_KEY}
    response = requests.post(LANGFLOW_API_URL, json=payload, headers=headers, timeout=90)
    response.raise_for_status()
    return response.json()['outputs'][0]['outputs'][0]['results']['message']['text']

# ==========================================
# RENDERIZAÇÃO DO HISTÓRICO
# ==========================================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            renderizar_mensagem(message["content"])
        else:
            st.markdown(message["content"])

# ==========================================
# MOTOR DO CHAT
# ==========================================
# Intercepta se o usuário clicou em uma sugestão na barra lateral
prompt_input = st.chat_input("Digite sua pergunta aqui... (ex: Quantas empresas ativas temos em Joinville?)")
prompt_final = prompt_sugerido if prompt_sugerido else prompt_input

if prompt_final:
    if not API_KEY:
        st.error("⚠️ Chave de API não encontrada! Verifique as variáveis de ambiente.")
        st.stop()
        
    st.session_state.messages.append({"role": "user", "content": prompt_final})
    
    with st.chat_message("user"):
        st.markdown(prompt_final)
        
    with st.chat_message("assistant"):
        if prompt_final.lower().strip() in SAUDACOES:
            resposta_ia = "Olá! Sou o AI MarketSense, seu Especialista em Inteligência de Mercado. Estou conectado aos dados estruturados da Receita Federal com foco em Santa Catarina. Como posso ajudar você a analisar nossos cenários hoje?"
            st.markdown(resposta_ia)
            st.session_state.messages.append({"role": "assistant", "content": resposta_ia})
            
        else:
            with st.spinner('🤖 Analisando dados da Receita Federal...'):
                try:
                    resposta_ia = consultar_langflow(prompt_final, st.session_state.session_id)
                    
                    if not resposta_ia or resposta_ia.strip() == "":
                        st.error("⚠️ O Langflow processou a requisição, mas retornou um texto vazio via API.")
                    else:
                        renderizar_mensagem(resposta_ia)
                        st.session_state.messages.append({"role": "assistant", "content": resposta_ia})
                        
                except requests.exceptions.Timeout:
                    st.error("⏳ Tempo limite excedido. O banco de dados demorou mais de 90 segundos.")
                except requests.exceptions.RequestException as e:
                    st.error(f"⚠️ Erro ao conectar com a API: {e}")
                except (ValueError, KeyError) as e:
                    st.error(f"⚠️ A estrutura da resposta da API mudou. Erro: {e}")
