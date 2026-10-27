"""Geração e formatação de planilhas Excel (modelo e resultados)."""

import io
from typing import List, Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd


# Estilos padronizados para cabeçalhos e células
FONTE_CABECALHO = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
FILL_CABECALHO_AZUL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
FILL_CABECALHO_VERMELHO = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
FONTE_CORPO = Font(name="Calibri", size=11)
BORDER_FINA = Border(
    left=Side(style="thin", color="D9D9D9"),
    right=Side(style="thin", color="D9D9D9"),
    top=Side(style="thin", color="D9D9D9"),
    bottom=Side(style="thin", color="D9D9D9"),
)


def _ajustar_largura_colunas(ws):
    """Ajusta automaticamente a largura das colunas com base no conteúdo."""
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val = str(cell.value or "")
            if len(val) > max_len:
                max_len = len(val)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 14)


def gerar_planilha_modelo() -> bytes:
    """Gera a planilha modelo Excel (.xlsx) para preenchimento do usuário.

    Contém:
    - Aba 'Modelo': cabeçalhos 'Placa' e 'Renavam' configurados como texto.
    - Aba 'Instruções': orientações detalhadas de preenchimento.
    """
    wb = openpyxl.Workbook()

    # --- Aba 1: Modelo ---
    ws_modelo = wb.active
    ws_modelo.title = "Modelo"

    headers_modelo = ["Placa", "Renavam"]
    for col_idx, h in enumerate(headers_modelo, 1):
        cell = ws_modelo.cell(row=1, column=col_idx, value=h)
        cell.font = FONTE_CABECALHO
        cell.fill = FILL_CABECALHO_AZUL
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER_FINA

    # Linha em branco ou orientada com formato texto explícito
    ws_modelo.row_dimensions[1].height = 25
    _ajustar_largura_colunas(ws_modelo)

    # --- Aba 2: Instruções ---
    ws_instrucoes = wb.create_sheet(title="Instruções")
    ws_instrucoes.views.sheetView[0].showGridLines = True

    titulo_cell = ws_instrucoes.cell(row=1, column=1, value="Orientações para Preenchimento da Planilha")
    titulo_cell.font = Font(name="Calibri", size=13, bold=True, color="1F4E79")

    instrucoes = [
        "1. Na aba 'Modelo', preencha as placas e os RENAVAMs dos veículos que deseja consultar.",
        "2. Cabeçalhos obrigatórios na primeira linha: 'Placa' e 'Renavam'. Não altere os nomes.",
        "3. Insira a placa original (padrão antigo ou Mercosul). O sistema enviará o valor exato à API.",
        "4. Formate a coluna 'Renavam' como Texto para não perder eventuais zeros à esquerda.",
        "5. Deixe apenas os registros a serem consultados, sem linhas de comentário na aba 'Modelo'.",
    ]

    for row_idx, texto in enumerate(instrucoes, start=3):
        cell = ws_instrucoes.cell(row=row_idx, column=1, value=texto)
        cell.font = FONTE_CORPO

    ws_instrucoes.column_dimensions["A"].width = 85

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


def gerar_planilha_resultado(
    df_resultados: Optional[pd.DataFrame] = None,
    df_erros: Optional[pd.DataFrame] = None,
) -> bytes:
    """Gera a planilha Excel final contendo duas abas: 'Resultados' e 'Erros'.

    Aba 'Resultados':
    - Colunas: Placa, RENAVAM, UF, Chassi.
    - Valores estritamente retornados pela API.

    Aba 'Erros':
    - Colunas: Placa, RENAVAM, Motivo do erro.
    - Valores originais de entrada para identificação.
    """
    wb = openpyxl.Workbook()

    # --- Aba 1: Resultados ---
    ws_resultados = wb.active
    ws_resultados.title = "Resultados"

    cols_resultados = ["Placa", "RENAVAM", "UF", "Chassi"]
    for col_idx, col_name in enumerate(cols_resultados, start=1):
        cell = ws_resultados.cell(row=1, column=col_idx, value=col_name)
        cell.font = FONTE_CABECALHO
        cell.fill = FILL_CABECALHO_AZUL
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER_FINA
    ws_resultados.row_dimensions[1].height = 24

    if df_resultados is not None and not df_resultados.empty:
        for row_idx, row_dict in enumerate(df_resultados.to_dict(orient="records"), start=2):
            for col_idx, col_name in enumerate(cols_resultados, start=1):
                val = row_dict.get(col_name)
                # Fallback caso a fonte de dados ainda use "UF da placa"
                if (val is None or (isinstance(val, float) and pd.isna(val)) or val == "") and col_name == "UF":
                    val = row_dict.get("UF da placa", "")

                cell = ws_resultados.cell(row=row_idx, column=col_idx)
                # RENAVAM, Placa e Chassi sempre como texto explícito
                val_str = str(val).strip() if (val is not None and pd.notna(val)) else ""
                cell.value = val_str
                cell.number_format = "@"
                cell.font = FONTE_CORPO
                cell.border = BORDER_FINA
                if col_name in ("Placa", "UF"):
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

    _ajustar_largura_colunas(ws_resultados)

    # --- Aba 2: Erros ---
    ws_erros = wb.create_sheet(title="Erros")
    cols_erros = ["Placa", "RENAVAM", "Motivo do erro"]
    for col_idx, col_name in enumerate(cols_erros, start=1):
        cell = ws_erros.cell(row=1, column=col_idx, value=col_name)
        cell.font = FONTE_CABECALHO
        cell.fill = FILL_CABECALHO_VERMELHO
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER_FINA
    ws_erros.row_dimensions[1].height = 24

    if df_erros is not None and not df_erros.empty:
        for row_idx, row_dict in enumerate(df_erros.to_dict(orient="records"), start=2):
            for col_idx, col_name in enumerate(cols_erros, start=1):
                val = row_dict.get(col_name, "")
                cell = ws_erros.cell(row=row_idx, column=col_idx)
                val_str = str(val).strip() if (val is not None and pd.notna(val)) else ""
                cell.value = val_str
                cell.number_format = "@"
                cell.font = FONTE_CORPO
                cell.border = BORDER_FINA
                if col_name in ("Placa", "RENAVAM"):
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

    _ajustar_largura_colunas(ws_erros)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
