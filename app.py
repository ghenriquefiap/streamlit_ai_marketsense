import streamlit as st
import requests
import uuid
import os
import json
import pandas as pd

# ==========================================
# CONSTANTES E CONFIGURAÇÕES GERAIS
# ==========================================
LANGFLOW_API_URL = "https://gushenrique-ai-marketsense-playground.hf.space/api/v1/run/ce489da1-4b85-4278-86a0-3f4730233685"
API_KEY = os.environ.get("LANGFLOW_API_KEY")

# Usar um Set {} em vez de Lista [] deixa a busca O(1) - instantânea
SAUDACOES = {"olá", "ola", "oi", "bom dia", "boa tarde", "boa noite", "opa", "eae", "hello"}

st.set_page_config(page_title="AI MarketSense | Branding Contabilidade", page_icon="📊", layout="centered")

# ==========================================
# UI: BANNER DE CABEÇALHO
# ==========================================
try:
    st.image("fundo.png", use_container_width=True)
    # Reintroduzindo o texto técnico como uma legenda centralizada e elegante
    st.markdown("<p style='text-align: center; color: #a0aab2; font-size: 0.9em; margin-top: -10px;'>Assistente de Inteligência de Mercado para Branding com Dados Públicos da Receita Federal de SC até Fevereiro/26</p>", unsafe_allow_html=True)
except FileNotFoundError:
    st.title("📊 AI MarketSense")
    st.markdown("Assistente de Inteligência de Mercado para Branding com Dados Públicos da Receita Federal de Santa Catarina até Fevereiro/26")

st.markdown("---")

# ==========================================
# FUNÇÕES DE LÓGICA E RENDERIZAÇÃO
# ==========================================
def renderizar_mensagem(conteudo):
    """Renderiza a resposta da IA e adiciona botões de ação na base."""
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
            prompt_pr = f"""
Aja como um Assessor de Imprensa Sênior. Transforme os dados da análise abaixo em um press release profissional de 3 parágrafos para portais de negócios. Destaque a autoridade da nossa inteligência de mercado.

DADOS DA ANÁLISE:
{conteudo}
            """
            st.success("Copiado! Envie o comando abaixo no chat para gerar:")
            st.code(prompt_pr, language="markdown")

def consultar_langflow(prompt_usuario, session_id):
    """Encapsula a chamada de rede para manter o loop principal limpo."""
    payload = {
        "output_type": "chat",
        "input_type": "chat",
        "input_value": prompt_usuario,
        "session_id": session_id
    }
    headers = {"x-api-key": API_KEY}
    
    response = requests.post(LANGFLOW_API_URL, json=payload, headers=headers, timeout=90)
    response.raise_for_status()
    
    dados = response.json()
    return dados['outputs'][0]['outputs'][0]['results']['message']['text']

# ==========================================
# GERENCIAMENTO DE SESSÃO E HISTÓRICO
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            renderizar_mensagem(message["content"])
        else:
            st.markdown(message["content"])

# ==========================================
# MOTOR DO CHAT
# ==========================================
if prompt := st.chat_input("Ex: Quantas empresas ativas temos em Joinville?"):
    if not API_KEY:
        st.error("⚠️ Chave de API não encontrada! Verifique as variáveis de ambiente.")
        st.stop()
        
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        if prompt.lower().strip() in SAUDACOES:
            resposta_ia = "Olá! Sou o AI MarketSense, seu Especialista em Inteligência de Mercado. Estou conectado aos dados estruturados da Receita Federal com foco em Santa Catarina. Como posso ajudar você a analisar nossos cenários hoje?"
            st.markdown(resposta_ia)
            st.session_state.messages.append({"role": "assistant", "content": resposta_ia})
            
        else:
            with st.spinner('🤖 Analisando milhões de dados da Receita Federal... Isso pode levar alguns segundos.'):
                try:
                    resposta_ia = consultar_langflow(prompt, st.session_state.session_id)
                    
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
