"""Interface Streamlit para Automação de Consulta de Veículos — DetranRS."""

import streamlit as st
import pandas as pd
from datetime import datetime

from core.consulta import criar_sessao_detran, consultar_veiculo
from core.exportacao import gerar_planilha_modelo, gerar_planilha_resultado
from core.processador import ler_planilha_entrada, processar_lote_veiculos


def aplicar_estilos_visuais():
    """Aplica folha de estilos moderna, eliminando o aspecto de 'tela preta vazia'."""
    st.markdown(
        """
        <style>
        /* Tipografia e espaçamento geral */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Banner Hero Superior */
        .hero-banner {
            background: linear-gradient(135deg, #111c35 0%, #0d1527 60%, #152238 100%);
            border: 1px solid rgba(59, 130, 246, 0.25);
            border-radius: 16px;
            padding: 1.8rem 2.2rem;
            margin-bottom: 1.8rem;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
            position: relative;
            overflow: hidden;
        }

        .hero-banner::after {
            content: '';
            position: absolute;
            top: -60px;
            right: -60px;
            width: 240px;
            height: 240px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.18) 0%, rgba(59, 130, 246, 0) 70%);
            pointer-events: none;
        }

        .hero-badges {
            display: flex;
            gap: 0.5rem;
            align-items: center;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
        }

        .badge-pill {
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.35);
            color: #93c5fd;
            padding: 0.2rem 0.65rem;
            border-radius: 9999px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }

        .badge-pill-gov {
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #6ee7b7;
        }

        .hero-title {
            color: #ffffff;
            font-size: 1.85rem;
            font-weight: 800;
            margin: 0;
            line-height: 1.25;
            letter-spacing: -0.02em;
        }

        .hero-subtitle {
            color: #94a3b8;
            font-size: 0.92rem;
            margin-top: 0.5rem;
            margin-bottom: 0;
            line-height: 1.5;
            max-width: 820px;
        }

        /* Estilização dos Containers com borda */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 14px !important;
            background: #111a2e !important;
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.3) !important;
            transition: all 0.2s ease;
        }

        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: rgba(59, 130, 246, 0.35) !important;
            box-shadow: 0 8px 24px -4px rgba(59, 130, 246, 0.15) !important;
        }

        /* Títulos dentro dos cards */
        .card-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1.05rem;
            font-weight: 700;
            color: #f1f5f9;
            margin-bottom: 0.35rem;
        }

        .card-desc {
            font-size: 0.86rem;
            color: #94a3b8;
            margin-bottom: 1rem;
            line-height: 1.45;
        }

        /* Métricas com visual moderno */
        [data-testid="stMetric"] {
            background: #142038 !important;
            border: 1px solid rgba(59, 130, 246, 0.2) !important;
            border-radius: 10px !important;
            padding: 0.8rem 1rem !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.78rem !important;
            font-weight: 700 !important;
            color: #94a3b8 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            font-weight: 800 !important;
            color: #60a5fa !important;
        }

        /* Botão Primário Refinado */
        button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            border: 1px solid rgba(147, 197, 253, 0.3) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 14px -2px rgba(37, 99, 235, 0.4) !important;
            transition: all 0.2s ease !important;
        }

        button[kind="primary"]:hover {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            box-shadow: 0 6px 20px -2px rgba(37, 99, 235, 0.6) !important;
            transform: translateY(-1px);
        }

        /* Botão Secundário */
        button[kind="secondary"] {
            background: #1e293b !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            color: #f1f5f9 !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }

        button[kind="secondary"]:hover {
            background: #334155 !important;
            border-color: rgba(59, 130, 246, 0.4) !important;
        }

        /* Rodapé elegante */
        .footer-note {
            text-align: center;
            color: #64748b;
            font-size: 0.8rem;
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(
        page_title="Consulta de Veículos — DetranRS",
        page_icon=":material/directions_car:",
        layout="wide",
    )

    aplicar_estilos_visuais()

    # Banner Superior Elegante (sem emojis, com badges e visual limpo)
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-badges">
                <span class="badge-pill">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
                    Processamento em Lote
                </span>
                <span class="badge-pill badge-pill-gov">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                    API Pública DetranRS
                </span>
            </div>
            <h1 class="hero-title">Consulta de Veículos — DetranRS</h1>
            <p class="hero-subtitle">
                Sistema automatizado para consulta cadastral de veículos. Consulte um veículo individualmente digitando
                <strong>Placa</strong> e <strong>RENAVAM</strong>, ou envie uma planilha Excel para processamento em lote
                diretamente da base oficial do DetranRS.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Inicialização de estado da sessão
    if "processamento_concluido" not in st.session_state:
        st.session_state.processamento_concluido = False
    if "df_resultados" not in st.session_state:
        st.session_state.df_resultados = None
    if "df_erros" not in st.session_state:
        st.session_state.df_erros = None
    if "ultimo_arquivo_id" not in st.session_state:
        st.session_state.ultimo_arquivo_id = None
    if "resultado_individual" not in st.session_state:
        st.session_state.resultado_individual = None  # dict com dados ou None
    if "erro_individual" not in st.session_state:
        st.session_state.erro_individual = None  # str de erro ou None

    # ─────────────────────────────────────────────────────────────────────────
    # SEÇÃO: Consulta Individual
    # ─────────────────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown(
            """
            <div class="card-header">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <span>Consulta Individual de Veículo</span>
            </div>
            <div class="card-desc">
                Informe a <strong>Placa</strong> e o <strong>RENAVAM</strong> para consultar um único veículo diretamente, sem precisar enviar arquivo.
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_placa, col_renavam, col_btn_ind = st.columns([1, 1, 0.6], gap="medium")
        with col_placa:
            placa_individual = st.text_input(
                "Placa:",
                placeholder="Ex.: ABC1234",
                key="input_placa_individual",
                help="Digite a placa do veículo (com ou sem hífen).",
            )
        with col_renavam:
            renavam_individual = st.text_input(
                "RENAVAM:",
                placeholder="Ex.: 01234567890",
                key="input_renavam_individual",
                help="Digite o RENAVAM do veículo (preservando zeros à esquerda).",
            )
        with col_btn_ind:
            st.write("")
            st.write("")
            consultar_individual = st.button(
                label="Consultar",
                type="primary",
                icon=":material/search:",
                use_container_width=True,
                key="btn_consulta_individual",
            )

        if consultar_individual:
            placa_ind_limpa = placa_individual.strip()
            renavam_ind_limpo = renavam_individual.strip()
            if not placa_ind_limpa or not renavam_ind_limpo:
                st.session_state.resultado_individual = None
                st.session_state.erro_individual = "Preencha os campos Placa e RENAVAM antes de consultar."
            else:
                with st.spinner("Consultando dados na API do DetranRS..."):
                    sessao_ind = criar_sessao_detran()
                    sucesso, dados_ind, erro_ind = consultar_veiculo(
                        placa=placa_ind_limpa,
                        renavam=renavam_ind_limpo,
                        session=sessao_ind,
                    )
                if sucesso:
                    st.session_state.resultado_individual = dados_ind
                    st.session_state.erro_individual = None
                else:
                    st.session_state.resultado_individual = None
                    st.session_state.erro_individual = erro_ind

        # Exibição do resultado / erro individual
        if st.session_state.erro_individual:
            st.error(st.session_state.erro_individual, icon=":material/error:")

        if st.session_state.resultado_individual:
            dados = st.session_state.resultado_individual
            st.write("")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Placa", dados.get("Placa", "—"), border=True)
            r2.metric("RENAVAM", dados.get("RENAVAM", "—"), border=True)
            r3.metric("UF", dados.get("UF", "—"), border=True)
            r4.metric("Chassi", dados.get("Chassi", "—"), border=True)

    st.write("")

    # ─────────────────────────────────────────────────────────────────────────
    # SEÇÃO: Consulta em Lote (planilha)
    # ─────────────────────────────────────────────────────────────────────────

    # Seção 1 e 2 em Cards Paralelos com Bordas e Sombras
    col_topo1, col_topo2 = st.columns([1, 1], gap="medium")

    with col_topo1:
        with st.container(border=True):
            st.markdown(
                """
                <div class="card-header">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    <span>1. Baixar Planilha Modelo</span>
                </div>
                <div class="card-desc">
                    Utilize o modelo padronizado com as colunas pré-formatadas como texto para garantir que zeros à esquerda de códigos RENAVAM sejam preservados.
                </div>
                """,
                unsafe_allow_html=True,
            )
            modelo_bytes = gerar_planilha_modelo()
            st.download_button(
                label="Baixar Planilha Modelo (.xlsx)",
                data=modelo_bytes,
                file_name="modelo_consulta_detranrs.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                icon=":material/download:",
                help="Clique para baixar a planilha modelo em formato Excel (.xlsx).",
                use_container_width=True,
            )

    with col_topo2:
        with st.container(border=True):
            st.markdown(
                """
                <div class="card-header">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                    <span>2. Enviar Planilha de Entrada</span>
                </div>
                <div class="card-desc">
                    Selecione o arquivo Excel contendo as colunas obrigatórias <strong>Placa</strong> e <strong>Renavam</strong>.
                </div>
                """,
                unsafe_allow_html=True,
            )
            arquivo_enviado = st.file_uploader(
                label="Selecione o arquivo Excel (.xlsx ou .xls):",
                type=["xlsx", "xls"],
                label_visibility="collapsed",
                help="O arquivo deve conter obrigatoriamente as colunas 'Placa' e 'Renavam'.",
            )

    # Se o arquivo mudar ou for removido, resetamos os resultados anteriores
    arquivo_id_atual = f"{arquivo_enviado.name}_{arquivo_enviado.size}" if arquivo_enviado else None
    if arquivo_id_atual != st.session_state.ultimo_arquivo_id:
        st.session_state.ultimo_arquivo_id = arquivo_id_atual
        st.session_state.processamento_concluido = False
        st.session_state.df_resultados = None
        st.session_state.df_erros = None

    df_validado = None

    # Validação do arquivo enviado
    if arquivo_enviado is not None:
        valido, df_validado, msg_validacao = ler_planilha_entrada(
            arquivo_ou_buffer=arquivo_enviado.getvalue(),
            nome_arquivo=arquivo_enviado.name,
        )

        if not valido:
            st.error(f"Erro na validação do arquivo: {msg_validacao}", icon=":material/error:")
            return
        else:
            qtd_registros = len(df_validado)
            st.success(
                f"Planilha validada com sucesso! Foram identificados **{qtd_registros}** registro(s) prontos para consulta.",
                icon=":material/check_circle:",
            )

            # Card de Prévia e Configurações
            with st.container(border=True):
                with st.expander("Visualizar dados importados da planilha", icon=":material/table_view:", expanded=False):
                    st.dataframe(df_validado, use_container_width=True)

                col_cfg, col_btn = st.columns([1, 1], gap="large")
                with col_cfg:
                    delay_segundos = st.number_input(
                        "Intervalo entre consultas (segundos):",
                        min_value=1.0,
                        max_value=10.0,
                        value=2.0,
                        step=0.5,
                        help="Tempo de espera entre cada consulta para evitar bloqueios ou sobrecarga na API do DetranRS. Recomendado: 2 segundos ou mais.",
                    )
                with col_btn:
                    st.write("")
                    st.write("")
                    iniciar = st.button(
                        label="Iniciar Consulta em Lote",
                        type="primary",
                        icon=":material/play_arrow:",
                        disabled=st.session_state.processamento_concluido,
                        use_container_width=True,
                    )

            if iniciar:
                # Indicador de progresso com Card Dedicado
                st.write("")
                with st.container(border=True):
                    st.markdown(
                        """
                        <div class="card-header">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                            <span>Processando Consultas</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    status_placeholder = st.empty()
                    progress_bar = st.progress(0)
                    metric_placeholder = st.empty()

                    total_regs = len(df_validado)
                    contador_sucessos = 0
                    contador_erros = 0

                    def atualizar_progresso(atual: int, total: int, status_item: dict):
                        nonlocal contador_sucessos, contador_erros
                        if status_item.get("sucesso"):
                            contador_sucessos += 1
                        else:
                            contador_erros += 1

                        pct = atual / total
                        progress_bar.progress(pct)
                        status_placeholder.info(
                            f"Consultando veículo {atual} de {total} ({int(pct * 100)}%) — "
                            f"Última placa: `{status_item.get('placa', '')}` "
                            f"(intervalo de {delay_segundos:.1f}s)",
                            icon=":material/sync:",
                        )

                        with metric_placeholder.container():
                            m1, m2, m3 = st.columns(3)
                            m1.metric("Total no Lote", total, border=True)
                            m2.metric("Consultas Concluídas", contador_sucessos, border=True)
                            m3.metric("Erros Registrados", contador_erros, border=True)

                    # Processa o lote
                    with st.spinner("Consultando dados na API do DetranRS..."):
                        sessao = criar_sessao_detran()
                        df_res, df_err = processar_lote_veiculos(
                            df_entrada=df_validado,
                            progresso_callback=atualizar_progresso,
                            delay_entre_requisicoes=delay_segundos,
                            session=sessao,
                        )

                    st.session_state.df_resultados = df_res
                    st.session_state.df_erros = df_err
                    st.session_state.processamento_concluido = True

                    progress_bar.progress(1.0)
                    status_placeholder.success("Processamento do lote finalizado com sucesso!", icon=":material/task_alt:")
                    st.rerun()

    # Exibição dos resultados após o processamento
    if st.session_state.processamento_concluido:
        st.write("")
        with st.container(border=True):
            st.markdown(
                """
                <div class="card-header">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                    <span>Relatório de Resultados</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            df_resultados = st.session_state.df_resultados
            df_erros = st.session_state.df_erros

            total_concluido = len(df_resultados) if df_resultados is not None else 0
            total_erros = len(df_erros) if df_erros is not None else 0
            total_geral = total_concluido + total_erros

            # Resumo em métricas
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Total de Veículos", total_geral, border=True)
            col_m2.metric("Consultas Concluídas", total_concluido, border=True)
            col_m3.metric("Erros / Inconsistências", total_erros, border=True)

            st.write("")

            # Botão para baixar a planilha final
            resultado_excel_bytes = gerar_planilha_resultado(df_resultados, df_erros)
            nome_arquivo_resultado = f"resultado_detranrs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            st.download_button(
                label="Baixar Relatório Completo (.xlsx)",
                data=resultado_excel_bytes,
                file_name=nome_arquivo_resultado,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                icon=":material/file_download:",
                help="Baixar o arquivo Excel contendo as abas 'Resultados' e 'Erros'.",
                use_container_width=True,
            )

            st.write("")

            # Abas sem emojis, com ícones Material
            tab_resultados, tab_erros = st.tabs([
                f":material/check_circle: Veículos Localizados ({total_concluido})",
                f":material/warning: Erros e Inconsistências ({total_erros})",
            ])

            with tab_resultados:
                if df_resultados is not None and not df_resultados.empty:
                    st.dataframe(df_resultados, use_container_width=True)
                else:
                    st.info("Nenhum veículo retornou dados com sucesso.", icon=":material/info:")

            with tab_erros:
                if df_erros is not None and not df_erros.empty:
                    st.warning("Os seguintes registros apresentaram inconsistências ou erros de consulta:", icon=":material/warning:")
                    st.dataframe(df_erros, use_container_width=True)
                else:
                    st.success("Nenhum erro registrado durante as consultas!", icon=":material/check_circle:")

    # Rodapé Discreto
    st.markdown(
        """
        <div class="footer-note">
            Automação DetranRS &bull; Consulta Oficial em Lote &bull; Formato Excel (.xlsx)
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
