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
FONTE_ERRO_TEXTO = Font(name="Calibri", size=11, bold=True, color="C00000")
FILL_ERRO_SUAVE = PatternFill(start_color="FDE8E8", end_color="FDE8E8", fill_type="solid")


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
    """Gera a planilha Excel final contendo uma única aba com todos os registros na ordem original.

    Aba 'Resultados':
    - Colunas: Placa, RENAVAM, UF, Chassi, Situação.
    - Mantém rigorosamente a ordem original da planilha enviada.
    - Os veículos com sucesso exibem 'Sucesso' na coluna 'Situação' e seus dados cadastrais.
    - Os veículos que falharam mantêm a Placa e o RENAVAM originais, com a coluna 'Situação'
      descrevendo o erro encontrado e formatação em destaque.
    """
    wb = openpyxl.Workbook()

    # --- Aba única: Resultados ---
    ws_resultados = wb.active
    ws_resultados.title = "Resultados"

    cols_saida = ["Placa", "RENAVAM", "UF", "Chassi", "Situação"]
    for col_idx, col_name in enumerate(cols_saida, start=1):
        cell = ws_resultados.cell(row=1, column=col_idx, value=col_name)
        cell.font = FONTE_CABECALHO
        cell.fill = FILL_CABECALHO_AZUL
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER_FINA
    ws_resultados.row_dimensions[1].height = 24

    if df_resultados is not None and not df_resultados.empty:
        for row_idx, row_dict in enumerate(df_resultados.to_dict(orient="records"), start=2):
            situacao_val = str(row_dict.get("Situação", "") or "").strip()
            eh_sucesso = situacao_val.upper() == "SUCESSO"

            for col_idx, col_name in enumerate(cols_saida, start=1):
                val = row_dict.get(col_name)
                # Fallback caso colunas venham com outros nomes
                if (val is None or (isinstance(val, float) and pd.isna(val)) or val == "") and col_name == "UF":
                    val = row_dict.get("UF da placa", "")

                cell = ws_resultados.cell(row=row_idx, column=col_idx)
                val_str = str(val).strip() if (val is not None and pd.notna(val)) else ""
                cell.value = val_str
                cell.number_format = "@"
                cell.border = BORDER_FINA

                if eh_sucesso:
                    cell.font = FONTE_CORPO
                    if col_name in ("Placa", "UF"):
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                    elif col_name == "Situação":
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                    else:
                        cell.alignment = Alignment(horizontal="left", vertical="center")
                else:
                    # Linha com erro: destaque na coluna Situação para identificação rápida
                    if col_name == "Situação":
                        cell.font = FONTE_ERRO_TEXTO
                        cell.fill = FILL_ERRO_SUAVE
                        cell.alignment = Alignment(horizontal="left", vertical="center")
                    elif col_name in ("Placa", "RENAVAM"):
                        cell.font = FONTE_CORPO
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                    else:
                        cell.font = FONTE_CORPO
                        cell.alignment = Alignment(horizontal="center", vertical="center")

    _ajustar_largura_colunas(ws_resultados)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
