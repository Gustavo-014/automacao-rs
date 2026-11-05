"""Testes automatizados das regras de negócio do núcleo da aplicação."""

import io
import openpyxl
import pandas as pd
from unittest.mock import patch

from core.processador import ler_planilha_entrada, processar_lote_veiculos
from core.exportacao import gerar_planilha_modelo, gerar_planilha_resultado


def test_modelo_e_leitura():
    modelo_bytes = gerar_planilha_modelo()
    wb = openpyxl.load_workbook(io.BytesIO(modelo_bytes))
    assert "Modelo" in wb.sheetnames
    assert "Instruções" in wb.sheetnames

    # Simular planilha preenchida
    df_exemplo = pd.DataFrame([
        {"Placa": "ABC1D23", "Renavam": "00123456789"},
        {"Placa": "XYZ9876", "Renavam": "09876543210"},
    ])
    buffer = io.BytesIO()
    df_exemplo.to_excel(buffer, index=False)

    valido, df_lido, erro = ler_planilha_entrada(buffer.getvalue())
    assert valido is True
    assert erro is None
    assert len(df_lido) == 2
    assert df_lido.loc[0, "Renavam"] == "00123456789"


def test_reprocessamento_e_ordem_estrita():
    df_teste = pd.DataFrame([
        {"Placa": "AAA1111", "Renavam": "11111111111"},
        {"Placa": "BBB2222", "Renavam": "22222222222"},
        {"Placa": "CCC3333", "Renavam": "33333333333"},
        {"Placa": "DDD4444", "Renavam": "44444444444"},
    ])

    chamadas = {"CCC3333": 0}

    def mock_consultar(placa, renavam, **kwargs):
        if placa == "AAA1111":
            return True, {"Placa": "AAA1111", "RENAVAM": "11111111111", "UF": "RS", "Chassi": "CHASSI_A"}, None
        elif placa == "BBB2222":
            return True, {"Placa": "BBB2222", "RENAVAM": "22222222222", "UF": "RS", "Chassi": "CHASSI_B"}, None
        elif placa == "CCC3333":
            chamadas["CCC3333"] += 1
            if chamadas["CCC3333"] == 1:
                return False, None, "Falha de rede temporaria"
            else:
                return True, {"Placa": "CCC3333", "RENAVAM": "33333333333", "UF": "RS", "Chassi": "CHASSI_C"}, None
        elif placa == "DDD4444":
            return False, None, "Veiculo inexistente"
        return False, None, "Erro generico"

    with patch("core.processador.consultar_veiculo", side_effect=mock_consultar):
        df_res, df_err = processar_lote_veiculos(df_teste, delay_entre_requisicoes=0)

    # 1. Deve conter 4 linhas rigorosamente na mesma ordem
    assert len(df_res) == 4
    assert list(df_res["Placa"]) == ["AAA1111", "BBB2222", "CCC3333", "DDD4444"]

    # 2. CCC3333 deve ter sido recuperado com sucesso no reprocessamento
    assert df_res.loc[2, "Situação"] == "Sucesso"
    assert df_res.loc[2, "Chassi"] == "CHASSI_C"

    # 3. DDD4444 permaneceu com erro
    assert "Veiculo inexistente" in df_res.loc[3, "Situação"]

    # 4. Planilha Excel final em aba única
    excel_bytes = gerar_planilha_resultado(df_res, df_err)
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    assert wb.sheetnames == ["Resultados"]

    ws = wb["Resultados"]
    assert [cell.value for cell in ws[1]] == ["Placa", "RENAVAM", "UF", "Chassi", "Situação"]


if __name__ == "__main__":
    test_modelo_e_leitura()
    test_reprocessamento_e_ordem_estrita()
    print("Todos os testes unitários passaram com sucesso!")
