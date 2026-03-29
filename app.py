import streamlit as st
import requests
import uuid
import os
import json
import pandas as pd

# ==========================================
# CONSTANTES E CONFIGURAÇÕES GERAIS
# ==========================================
LANGFLOW_API_URL = "https://gushenrique-ai-marketsense-playground.hf.space/api/v1/run/093a1edb-73c5-46a0-8c2d-d0f6f5a643dd"
API_KEY = os.environ.get("LANGFLOW_API_KEY")

# Usar um Set {} em vez de Lista [] deixa a busca O(1) - instantânea
SAUDACOES = {"olá", "ola", "oi", "bom dia", "boa tarde", "boa noite", "opa", "eae", "hello"}

st.set_page_config(page_title="AI MarketSense | Branding Contabilidade", page_icon="📊", layout="centered")
st.title("📊 AI MarketSense")
st.markdown("Assistente de Inteligência de Mercado para Branding com Dados Públicos da Receita Federal até Fevereiro/26")

# ==========================================
# FUNÇÕES DE LÓGICA E RENDERIZAÇÃO
# ==========================================
def renderizar_mensagem(conteudo):
    """Separa o texto da IA do payload do gráfico e renderiza ambos na tela."""
    if "[GRAFICO]" not in conteudo:
        st.markdown(conteudo)
        return

    # Quebra a resposta em duas partes: Texto e JSON
    partes = conteudo.split("[GRAFICO]")
    st.markdown(partes[0].strip())
    
    try:
        # Limpa possíveis blocos de formatação markdown
        json_str = partes[1].strip().replace("```json", "").replace("```", "").strip()
        dados_grafico = json.loads(json_str)
        
        st.subheader(dados_grafico.get("titulo", "Análise Visual"))
        
        # Converte para DataFrame de forma segura
        df = pd.DataFrame(list(dados_grafico.get("dados", {}).items()), columns=['Categoria', 'Quantidade'])
        if not df.empty:
            df.set_index('Categoria', inplace=True)
            st.bar_chart(df)
        else:
            st.warning("⚠️ O gráfico não contém dados suficientes para exibição.")
            
    except json.JSONDecodeError:
        st.caption("⚠️ A IA tentou gerar um gráfico, mas o formato estrutural falhou.")

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

# Renderiza o histórico salvando o estado dos gráficos
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
        message_placeholder = st.empty()
        
        # Interceptador de Small Talk
        if prompt.lower().strip() in SAUDACOES:
            resposta_ia = "Olá! Sou o AI MarketSense, seu Especialista em Inteligência de Mercado. Estou conectado aos dados estruturados da Receita Federal com foco em Santa Catarina. Como posso ajudar você a analisar nossos cenários hoje?"
            message_placeholder.markdown(resposta_ia)
            st.session_state.messages.append({"role": "assistant", "content": resposta_ia})
            
        else:
            message_placeholder.markdown("⏳ Processando dados estruturados...")
            
            try:
                resposta_ia = consultar_langflow(prompt, st.session_state.session_id)
                message_placeholder.empty()
                
                if not resposta_ia or resposta_ia.strip() == "":
                    st.error("⚠️ O Langflow processou a requisição, mas retornou um texto vazio via API.")
                else:
                    renderizar_mensagem(resposta_ia)
                    st.session_state.messages.append({"role": "assistant", "content": resposta_ia})
                    
            except requests.exceptions.Timeout:
                message_placeholder.error("⏳ Tempo limite excedido. O banco de dados demorou mais de 90 segundos.")
            except requests.exceptions.RequestException as e:
                message_placeholder.error(f"⚠️ Erro ao conectar com a API: {e}")
            except (ValueError, KeyError) as e:
                message_placeholder.error(f"⚠️ A estrutura da resposta da API mudou. Erro: {e}")
