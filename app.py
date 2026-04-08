import streamlit as st
import requests
import uuid
import os
import json
import pandas as pd
import base64

# ==========================================
# CONSTANTES E CONFIGURAÇÕES GERAIS
# ==========================================
LANGFLOW_API_URL = "https://gushenrique-ai-marketsense-playground.hf.space/api/v1/run/ce489da1-4b85-4278-86a0-3f4730233685"
API_KEY = os.environ.get("LANGFLOW_API_KEY")

# Usar um Set {} em vez de Lista [] deixa a busca O(1) - instantânea
SAUDACOES = {"olá", "ola", "oi", "bom dia", "boa tarde", "boa noite", "opa", "eae", "hello"}

st.set_page_config(page_title="AI MarketSense | Branding Contabilidade", page_icon="📊", layout="centered")

# ==========================================
# FUNÇÃO: INJEÇÃO DE BACKGROUND (UI/UX)
# ==========================================
def adicionar_fundo_tela(arquivo_imagem):
    """Injeta CSS para colocar a imagem de fundo e ajusta a transparência dos containers."""
    try:
        with open(arquivo_imagem, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
            
        css = f"""
        <style>
        /* Aplica a imagem no fundo geral da aplicação */
        .stApp {{
            background-image: url(data:image/png;base64,{encoded_string});
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        
        /* Deixa o cabeçalho superior invisível */
        .stApp > header {{
            background-color: transparent;
        }}
        
        /* Cria um 'vidro fumê' atrás do conteúdo principal para garantir a leitura do texto */
        .block-container {{
            background-color: rgba(14, 17, 23, 0.85);
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
            margin-top: 2rem;
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"⚠️ Imagem '{arquivo_imagem}' não encontrada na pasta. Fundo padrão ativado.")

# Chama a função passando o nome do arquivo da imagem
adicionar_fundo_tela("fundo.png")

st.title("📊 AI MarketSense")
st.markdown("Assistente de Inteligência de Mercado para Branding com Dados Públicos da Receita Federal de Santa Catarina até Fevereiro/26")

# ==========================================
# FUNÇÕES DE LÓGICA E RENDERIZAÇÃO
# ==========================================
def renderizar_mensagem(conteudo):
    """Renderiza a resposta da IA e adiciona botões de ação na base."""
    # 1. Renderiza a análise textual/gráfica da IA
    st.markdown(conteudo)
    
    # 2. Área de Ações Ágeis (Botões)
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        # Botão 1: Baixar Relatório Completo
        st.download_button(
            label="📥 Baixar Relatório (.txt)",
            data=conteudo.encode('utf-8'),
            file_name="relatorio_marketsense.txt",
            mime="text/plain",
            use_container_width=True,
            key=f"btn_dw_{hash(conteudo)}" # Chave única para não bugar no histórico
        )
        
    with col2:
        # Botão 2: Gerar Press Release
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

# Renderiza o histórico salvando o estado dos gráficos e botões
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
        
        # Interceptador de Small Talk
        if prompt.lower().strip() in SAUDACOES:
            resposta_ia = "Olá! Sou o AI MarketSense, seu Especialista em Inteligência de Mercado. Estou conectado aos dados estruturados da Receita Federal com foco em Santa Catarina. Como posso ajudar você a analisar nossos cenários hoje?"
            st.markdown(resposta_ia)
            st.session_state.messages.append({"role": "assistant", "content": resposta_ia})
            
        else:
            # === O SPINNER MÁGICO ENTRA AQUI ===
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
