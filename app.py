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
    """Separa o texto da IA do payload do gráfico e renderiza com botões de ação."""
    if "[GRAFICO]" not in conteudo:
        st.markdown(conteudo)
        return

    # Quebra a resposta em duas partes: Texto e JSON
    partes = conteudo.split("[GRAFICO]")
    texto_analise = partes[0].strip()
    st.markdown(texto_analise)
    
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
            
            # ==========================================
            # ÁREA DE AÇÕES ÁGEIS (BOTÕES)
            # ==========================================
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Botão 1: Baixar CSV
                csv = df.to_csv().encode('utf-8')
                st.download_button(
                    label="📥 Baixar Dados (CSV)",
                    data=csv,
                    file_name="analise_marketsense.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
            with col2:
                # Botão 2: Dica do PPT
                st.info("💡 Dica: Clique nos '...' no canto superior do gráfico para salvá-arlo como imagem para o PPT.")
                
            with col3:
                # Botão 3: Press Release (Gera um prompt pronto)
                if st.button("📝 Gerar Press Release", use_container_width=True):
                    prompt_pr = f"""
                    Aja como um Assessor de Imprensa Sênior. Transforme os dados abaixo em um press release profissional de 3 parágrafos para portais de negócios.
                    Destaque a autoridade da nossa inteligência de mercado.
                    
                    DADOS DA ANÁLISE:
                    {texto_analise}
                    
                    NÚMEROS EXATOS:
                    {df.to_string()}
                    """
                    st.success("Copiado! Envie o texto abaixo no chat para gerar:")
                    st.code(prompt_pr, language="markdown")
                    
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
