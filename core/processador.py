"""Leitura, validação e orquestração do processamento da planilha."""

import io
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import pandas as pd
import requests

from core.consulta import consultar_veiculo, criar_sessao_detran


def ler_planilha_entrada(
    arquivo_ou_buffer: Union[str, bytes, io.BytesIO, Any],
    nome_arquivo: str = "",
) -> Tuple[bool, Optional[pd.DataFrame], Optional[str]]:
    """Lê e valida a planilha de entrada enviada pelo usuário.

    Regras:
    - Suporta arquivos .xlsx e .xls.
    - Lê todos os dados como texto (dtype=str) para preservar zeros à esquerda.
    - Validação de cabeçalhos ignorando diferenças de maiúsculas/minúsculas e espaços extras.
    - Exige a presença das colunas 'Placa' e 'Renavam'.

    Retorna:
        (sucesso, df_validado, mensagem_erro)
    """
    try:
        # Se for bytes, envelopar em BytesIO
        if isinstance(arquivo_ou_buffer, bytes):
            buffer = io.BytesIO(arquivo_ou_buffer)
        else:
            buffer = arquivo_ou_buffer

        # Determina o engine adequado
        nome_lower = str(nome_arquivo or getattr(arquivo_ou_buffer, "name", "")).lower()
        engine = "xlrd" if nome_lower.endswith(".xls") else "openpyxl"

        # Leitura da primeira aba preservando tudo como string
        df_raw = pd.read_excel(buffer, dtype=str, engine=engine)

    except Exception as e:
        return False, None, f"Erro ao ler o arquivo Excel: {str(e)}"

    if df_raw.empty:
        return False, None, "A planilha enviada está vazia."

    # Normalização de cabeçalhos para busca
    mapa_colunas: Dict[str, str] = {}
    col_placa: Optional[str] = None
    col_renavam: Optional[str] = None

    for col in df_raw.columns:
        col_norm = str(col).strip().lower()
        if col_norm == "placa" and col_placa is None:
            col_placa = col
        elif col_norm == "renavam" and col_renavam is None:
            col_renavam = col

    faltantes = []
    if not col_placa:
        faltantes.append("'Placa'")
    if not col_renavam:
        faltantes.append("'Renavam'")

    if faltantes:
        colunas_encontradas = [str(c).strip() for c in df_raw.columns]
        return (
            False,
            None,
            f"Coluna(s) obrigatória(s) não encontrada(s): {', '.join(faltantes)}. "
            f"Colunas presentes no arquivo: {colunas_encontradas}.",
        )

    # Cria dataframe padronizado apenas com as colunas relevantes
    df_processado = pd.DataFrame()
    df_processado["Placa"] = df_raw[col_placa].fillna("").astype(str).str.strip()
    df_processado["Renavam"] = df_raw[col_renavam].fillna("").astype(str).str.strip()

    # Remove linhas completamente vazias
    linhas_validas = (df_processado["Placa"] != "") | (df_processado["Renavam"] != "")
    df_processado = df_processado[linhas_validas].reset_index(drop=True)

    if df_processado.empty:
        return False, None, "A planilha não contém nenhuma linha preenchida com Placa ou Renavam."

    return True, df_processado, None


def processar_lote_veiculos(
    df_entrada: pd.DataFrame,
    progresso_callback: Optional[Callable[[int, int, Dict[str, Any]], None]] = None,
    delay_entre_requisicoes: float = 2.0,
    session: Optional[requests.Session] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Processa a lista de veículos consultando a API do DetranRS.

    Fluxo de execução:
    1. Primeira passada: consulta cada veículo na ordem original de entrada.
    2. Identificação de erros: os veículos que falharam na primeira tentativa são marcados.
    3. Reprocessamento de erros: após concluir a consulta do último veículo do lote,
       o sistema realiza uma nova tentativa para cada item que havia falhado.
    4. Unificação e integridade de ordem: os resultados finais são mantidos rigorosamente
       na mesma ordem da planilha de entrada, com uma coluna 'Situação' indicando o status
       (ex.: 'Sucesso' ou o motivo do erro).

    Parâmetros:
        df_entrada: DataFrame contendo colunas 'Placa' e 'Renavam'.
        progresso_callback: Função chamada a cada item processado (atual, total, status_dict).
        delay_entre_requisicoes: Pausa em segundos entre requisições para evitar rate-limiting.
        session: Sessão requests opcional.

    Retorna:
        (df_resultados_unificado, df_erros)
    """
    total = len(df_entrada)
    registros: List[Dict[str, Any]] = [{} for _ in range(total)]
    indices_erros: List[int] = []

    sessao = session or criar_sessao_detran()

    # ── 1ª Passada: Consulta sequencial de todos os itens ──────────────────────
    for idx, row in enumerate(df_entrada.itertuples(index=False)):
        placa_orig = str(getattr(row, "Placa", "") or "").strip()
        renavam_orig = str(getattr(row, "Renavam", "") or "").strip()

        sucesso, dados_veiculo, motivo_erro = consultar_veiculo(
            placa=placa_orig,
            renavam=renavam_orig,
            session=sessao,
        )

        if sucesso and dados_veiculo:
            registros[idx] = {
                "Placa": dados_veiculo.get("Placa", placa_orig),
                "RENAVAM": dados_veiculo.get("RENAVAM", renavam_orig),
                "UF": dados_veiculo.get("UF", ""),
                "Chassi": dados_veiculo.get("Chassi", ""),
                "Situação": "Sucesso",
                "sucesso": True,
            }
            status_item = {
                "fase": "principal",
                "sucesso": True,
                "placa": registros[idx]["Placa"],
                "renavam": registros[idx]["RENAVAM"],
                "indice": idx,
            }
        else:
            erro_desc = motivo_erro or "Erro na consulta do veículo."
            registros[idx] = {
                "Placa": placa_orig,
                "RENAVAM": renavam_orig,
                "UF": "",
                "Chassi": "",
                "Situação": erro_desc,
                "sucesso": False,
            }
            indices_erros.append(idx)
            status_item = {
                "fase": "principal",
                "sucesso": False,
                "placa": placa_orig,
                "renavam": renavam_orig,
                "indice": idx,
                "erro": erro_desc,
            }

        if progresso_callback:
            progresso_callback(idx + 1, total, status_item)

        # Intervalo entre requisições da 1ª passada
        if (idx + 1) < total and delay_entre_requisicoes > 0:
            time.sleep(delay_entre_requisicoes)

    # ── 2ª Passada: Reprocessamento dos itens que apresentaram erro ────────────
    if indices_erros:
        total_erros_inicial = len(indices_erros)
        if delay_entre_requisicoes > 0:
            time.sleep(delay_entre_requisicoes)

        if progresso_callback:
            progresso_callback(
                0,
                total_erros_inicial,
                {
                    "fase": "reprocessamento_inicio",
                    "qtd_reprocessar": total_erros_inicial,
                },
            )

        for rep_num, idx_erro in enumerate(indices_erros, start=1):
            placa_rep = registros[idx_erro]["Placa"]
            renavam_rep = registros[idx_erro]["RENAVAM"]

            sucesso_rep, dados_veiculo_rep, motivo_erro_rep = consultar_veiculo(
                placa=placa_rep,
                renavam=renavam_rep,
                session=sessao,
            )

            if sucesso_rep and dados_veiculo_rep:
                registros[idx_erro] = {
                    "Placa": dados_veiculo_rep.get("Placa", placa_rep),
                    "RENAVAM": dados_veiculo_rep.get("RENAVAM", renavam_rep),
                    "UF": dados_veiculo_rep.get("UF", ""),
                    "Chassi": dados_veiculo_rep.get("Chassi", ""),
                    "Situação": "Sucesso",
                    "sucesso": True,
                }
                status_rep = {
                    "fase": "reprocessamento_item",
                    "sucesso": True,
                    "placa": placa_rep,
                    "renavam": renavam_rep,
                    "indice": idx_erro,
                }
            else:
                erro_atualizado = motivo_erro_rep or registros[idx_erro]["Situação"]
                registros[idx_erro]["Situação"] = erro_atualizado
                registros[idx_erro]["sucesso"] = False
                status_rep = {
                    "fase": "reprocessamento_item",
                    "sucesso": False,
                    "placa": placa_rep,
                    "renavam": renavam_rep,
                    "indice": idx_erro,
                    "erro": erro_atualizado,
                }

            if progresso_callback:
                progresso_callback(rep_num, total_erros_inicial, status_rep)

            if rep_num < total_erros_inicial and delay_entre_requisicoes > 0:
                time.sleep(delay_entre_requisicoes)

    # ── Construção do DataFrame mantendo a ordem estrita da entrada ────────────
    colunas_finais = ["Placa", "RENAVAM", "UF", "Chassi", "Situação"]
    df_resultados_unificado = pd.DataFrame(registros)[colunas_finais]

    # Dataframe auxiliar contendo apenas os registros que permaneceram com erro
    df_erros = df_resultados_unificado[df_resultados_unificado["Situação"] != "Sucesso"].copy()

    return df_resultados_unificado, df_erros
