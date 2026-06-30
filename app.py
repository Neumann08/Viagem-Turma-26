import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(page_title="Organizador de Viagens", layout="wide", page_icon="✈️")

# Nome do arquivo que guardará os votos permanentemente no servidor (Solução Estável)
ARQUIVO_VOTOS = "banco_de_votos.csv"

# Função para carregar os votos salvos no servidor
def carregar_votos():
    if os.path.exists(ARQUIVO_VOTOS):
        try:
            return pd.read_csv(ARQUIVO_VOTOS)
        except:
            return pd.DataFrame(columns=["Nome", "Votos"])
    return pd.DataFrame(columns=["Nome", "Votos"])

# 1. Gerar todos os finais de semana de Agosto a Dezembro de 2026
@st.cache_data
def gerar_finais_de_semana():
    finais_de_semana = []
    data_inicio = datetime(2026, 8, 1)
    data_fim = datetime(2026, 12, 31)
    
    # 🚫 SUAS DATAS EXCLUÍDAS SOLICITADAS
    datas_para_excluir = [
        "01/08", "08/08", "15/10", "22/08", "05/09", "12/09", 
        "19/09", "26/09", "10/10", "17/10", "31/10", "14/11", 
        "05/12", "26/12"
    ]
    
    data_atual = data_inicio
    while data_atual <= data_fim:
        if data_atual.weekday() == 5:  # Sábado
            sabado = data_atual
            domingo = data_atual + timedelta(days=1)
            
            nome_fds = f"{sabado.strftime('%d/%m')} e {domingo.strftime('%d/%m')} de {sabado.strftime('%B/%Y')}"
            meses_en_pt = {"August": "Agosto", "September": "Setembro", "October": "Outubro", "November": "Novembro", "December": "Dezembro"}
            for en, pt in meses_en_pt.items():
                nome_fds = nome_fds.replace(en, pt)
                
            # 🔍 Só adiciona se não estiver na sua lista de exclusão
            if sabado.strftime('%d/%m') not in datas_para_excluir:
                finais_de_semana.append(nome_fds)
        data_atual += timedelta(days=1)
    return finais_de_semana

FDS_LISTA = gerar_finais_de_semana()

# --- INTERFACE GRÁFICA ---
st.title("✈️ Escolha do Final de Semana para a Viagem da turma 26!")

# 🖼️ SUA IMAGEM CENTRALIZADA E AJUSTADA
col_esquerda, col_centro, col_direita = st.columns([2, 1, 2])
with col_centro:
    st.image(
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRE5_dUh7nVSUSHGxWGcJDU5vNBwvTVyb9vDtEogdBw50zA_5s9e-1HAhik&s=10", 
        caption="Rumo à Viagem da Turma 26! 🚀"
    )

aba_votar, aba_painel = st.tabs(["✍️ Indicar Disponibilidade", "📊 Painel de Resultados"])

# --- ABA 1: VOTAÇÃO ---
with aba_votar:
    st.markdown("### Informe o nome e sobrenome do (a) aluno (a) abaixo:")
    nome = st.text_input("Nome do (a) aluno (a):", placeholder="Ex: João Silva").strip()
    
    st.markdown("**Selecione os finais de semana que você TEM DISPONIBILIDADE:**")
    votos_usuario = []
    for fds in FDS_LISTA:
        if st.checkbox(fds, key=f"check_{fds}"):
            votos_usuario.append(fds)
            
    if st.button("Enviar Disponibilidade", type="primary"):
        if not nome:
            st.error("Por favor, insira o seu nome antes de enviar.")
        else:
            votos_texto = "; ".join(votos_usuario) if votos_usuario else "Nenhum"
            
            # --- SALVAMENTO LOCAL SEGURO ---
            df_atual = carregar_votos()
            if not df_atual.empty:
                df_atual = df_atual[df_atual['Nome'].str.lower() != nome.lower()] # Evita duplicações
            
            novo_voto = pd.DataFrame([{"Nome": nome, "Votos": votos_texto}])
            df_final = pd.concat([df_atual, novo_voto], ignore_index=True)
            df_final.to_csv(ARQUIVO_VOTOS, index=False)
            
            # --- ENVIO PARALELO PARA O SEU GOOGLE FORMS ---
            import requests
            url_form = "https://docs.google.com/forms/d/e/1FAIpQLSdOwb2mMIDCOdkxGcLBkmiIPh4UEBOOFGSqyobx7Cxip_6Whw/formResponse"
            dados_voto = {
                "entry.611490973": nome,
                "entry.692886392": votos_texto
            }
            try:
                requests.post(url_form, data=dados_voto, timeout=5)
            except:
                pass # Se o Google falhar, o sistema local garante o voto no painel
                
            st.success(f"Disponibilidade de {nome} registrada com sucesso!")
            st.balloons()

# --- ABA 2: PAINEL ---
with aba_painel:
    st.markdown("### 🔐 Área Restrita ao Organizador")
    senha = st.text_input("Digite a senha para visualizar os resultados:", type="password")
    
    if senha == "26":
        st.success("Acesso liberado!")
        
        df_painel = carregar_votos()
        
        if df_painel.empty:
            st.info("Nenhum voto registrado até o momento.")
        else:
            total_participantes = len(df_painel)
            st.metric(label="Total de Participantes que Votaram", value=total_participantes)
            
            dados_votos_mapeados = {}
            for _, row in df_painel.iterrows():
                votos_lista = str(row['Votos']).split("; ") if row['Votos'] != "Nenhum" else []
                dados_votos_mapeados[row['Nome']] = votos_lista
                
            linhas_resultado = []
            for fds in FDS_LISTA:
                quem_pode = [p for p, v in dados_votos_mapeados.items() if fds in v]
                votos_sim = len(quem_pode)
                percentual = (votos_sim / total_participantes) * 100
                
                linhas_resultado.append({
                    "Final de Semana": fds,
                    "Votos Favoráveis": votos_sim,
                    "Aderência (%)": round(percentual, 1),
                    "Quem pode ir": ", ".join(quem_pode) if quem_pode else "Ninguém"
                })
                
            df_resultados = pd.DataFrame(linhas_resultado).sort_values(by=["Aderência (%)", "Votos Favoráveis"], ascending=False)
            
            st.dataframe(
                df_resultados,
                column_config={"Aderência (%)": st.column_config.ProgressColumn("Aderência (%)", format="%.1f%%", min_value=0, max_value=100)},
                hide_index=True, use_container_width=True
            )
            
            # Botão para baixar relatório se quiser consolidar no Excel
            st.markdown("---")
            csv_data = df_painel.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Dados Consolidados (CSV)",
                data=csv_data,
                file_name="votacao_viagem_turma26.csv",
                mime="text/csv"
            )
    elif senha != "":
        st.error("Senha incorreta.")
