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

    Parâmetros:
        df_entrada: DataFrame contendo colunas 'Placa' e 'Renavam'.
        progresso_callback: Função chamada a cada item processado (atual, total, status_dict).
        delay_entre_requisicoes: Pausa em segundos entre requisições para evitar rate-limiting (padrão 2.0s).
        session: Sessão requests opcional.

    Retorna:
        (df_resultados, df_erros)
    """
    total = len(df_entrada)
    lista_sucessos: List[Dict[str, Any]] = []
    lista_erros: List[Dict[str, Any]] = []

    sessao = session or criar_sessao_detran()

    for idx, row in enumerate(df_entrada.itertuples(index=False), start=1):
        placa_orig = str(getattr(row, "Placa", "") or "").strip()
        renavam_orig = str(getattr(row, "Renavam", "") or "").strip()

        sucesso, dados_veiculo, motivo_erro = consultar_veiculo(
            placa=placa_orig,
            renavam=renavam_orig,
            session=sessao,
        )

        if sucesso and dados_veiculo:
            lista_sucessos.append(dados_veiculo)
            status_item = {
                "sucesso": True,
                "placa": dados_veiculo.get("Placa", placa_orig),
                "renavam": dados_veiculo.get("RENAVAM", renavam_orig),
            }
        else:
            lista_erros.append({
                "Placa": placa_orig,
                "RENAVAM": renavam_orig,
                "Motivo do erro": motivo_erro or "Erro não especificado.",
            })
            status_item = {
                "sucesso": False,
                "placa": placa_orig,
                "renavam": renavam_orig,
                "erro": motivo_erro,
            }

        if progresso_callback:
            progresso_callback(idx, total, status_item)

        # Intervalo respeitoso entre requisições para proteção contra rate-limiting
        if idx < total and delay_entre_requisicoes > 0:
            time.sleep(delay_entre_requisicoes)

    # Constrói DataFrames finais estruturados
    cols_sucesso = ["Placa", "RENAVAM", "UF", "Chassi"]
    if lista_sucessos:
        df_sucessos_raw = pd.DataFrame(lista_sucessos)
        for c in cols_sucesso:
            if c not in df_sucessos_raw.columns:
                df_sucessos_raw[c] = ""
        df_resultados = df_sucessos_raw[cols_sucesso]
    else:
        df_resultados = pd.DataFrame(columns=cols_sucesso)

    cols_erro = ["Placa", "RENAVAM", "Motivo do erro"]
    if lista_erros:
        df_erros = pd.DataFrame(lista_erros)[cols_erro]
    else:
        df_erros = pd.DataFrame(columns=cols_erro)

    return df_resultados, df_erros
