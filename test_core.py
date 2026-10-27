"""Testes para os módulos core."""

import io
import pandas as pd
from core.exportacao import gerar_planilha_modelo, gerar_planilha_resultado
from core.processador import ler_planilha_entrada, processar_lote_veiculos
from core.consulta import consultar_veiculo

def test_modelo():
    modelo_bytes = gerar_planilha_modelo()
    assert len(modelo_bytes) > 0
    # Verifica se pode ser lido
    xl = pd.ExcelFile(io.BytesIO(modelo_bytes))
    assert "Modelo" in xl.sheet_names
    assert "Instruções" in xl.sheet_names
    df = pd.read_excel(xl, sheet_name="Modelo")
    assert "Placa" in df.columns
    assert "Renavam" in df.columns
    print("[PASS] test_modelo")

def test_validacao_planilha():
    # Planilha válida com espaços e case diferente
    buf = io.BytesIO()
    df_raw = pd.DataFrame({
        "  pLaCa  ": ["TUP9B47", "ABC1234"],
        "RENAVAM ": ["01506247196", "00123456789"]
    })
    df_raw.to_excel(buf, index=False)
    buf.seek(0)

    sucesso, df_validado, erro = ler_planilha_entrada(buf.getvalue(), "teste.xlsx")
    assert sucesso is True
    assert erro is None
    assert list(df_validado.columns) == ["Placa", "Renavam"]
    assert df_validado.iloc[0]["Renavam"] == "01506247196" # Preserva zeros à esquerda!
    print("[PASS] test_validacao_planilha")

def test_planilha_invalida():
    buf = io.BytesIO()
    df_bad = pd.DataFrame({"Veiculo": ["123"], "Ano": ["2020"]})
    df_bad.to_excel(buf, index=False)
    buf.seek(0)
    sucesso, df_val, erro = ler_planilha_entrada(buf.getvalue(), "teste.xlsx")
    assert sucesso is False
    assert df_val is None
    assert "Coluna(s) obrigatória(s)" in erro
    print("[PASS] test_planilha_invalida")

def test_geracao_resultado_excel():
    df_res = pd.DataFrame([
        {
            "Placa": "TUP9B47",
            "RENAVAM": "01506247196",
            "UF": "RJ",
            "Chassi": "9536B8TD6VR020673",
        }
    ])
    df_err = pd.DataFrame([
        {
            "Placa": "AAA0000",
            "RENAVAM": "00000000000",
            "Motivo do erro": "Placa inválida",
        }
    ])
    res_bytes = gerar_planilha_resultado(df_res, df_err)
    assert len(res_bytes) > 0
    xl = pd.ExcelFile(io.BytesIO(res_bytes))
    assert "Resultados" in xl.sheet_names
    assert "Erros" in xl.sheet_names

    df_res_read = pd.read_excel(xl, sheet_name="Resultados", dtype=str)
    assert df_res_read.iloc[0]["Placa"] == "TUP9B47"
    assert df_res_read.iloc[0]["RENAVAM"] == "01506247196"
    assert df_res_read.iloc[0]["UF"] == "RJ"
    assert df_res_read.iloc[0]["Chassi"] == "9536B8TD6VR020673"
    assert list(df_res_read.columns) == ["Placa", "RENAVAM", "UF", "Chassi"]

    df_err_read = pd.read_excel(xl, sheet_name="Erros", dtype=str)
    assert df_err_read.iloc[0]["Placa"] == "AAA0000"
    assert df_err_read.iloc[0]["RENAVAM"] == "00000000000"
    assert df_err_read.iloc[0]["Motivo do erro"] == "Placa inválida"
    assert list(df_err_read.columns) == ["Placa", "RENAVAM", "Motivo do erro"]
    print("[PASS] test_geracao_resultado_excel")

if __name__ == "__main__":
    test_modelo()
    test_validacao_planilha()
    test_planilha_invalida()
    test_geracao_resultado_excel()
    print("ALL CORE UNIT TESTS PASSED!")
