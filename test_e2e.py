"""Teste de ponta a ponta (E2E) simulando a execução completa."""

import io
import pandas as pd
from core.exportacao import gerar_planilha_resultado
from core.processador import ler_planilha_entrada, processar_lote_veiculos

def test_fluxo_completo():
    print("1. Criando planilha de entrada com dados mistos...")
    dados_entrada = pd.DataFrame([
        {"Placa": "TUP9B47", "Renavam": "01506247196"}, # Sucesso esperado
        {"Placa": "TUP9B47", "Renavam": "00000000000"}, # Erro: renavam não confere
        {"Placa": "AAA0000", "Renavam": "00000000000"}, # Erro: placa inválida
    ])
    buffer_in = io.BytesIO()
    dados_entrada.to_excel(buffer_in, index=False)
    buffer_in.seek(0)

    print("2. Lendo e validando a planilha de entrada...")
    sucesso_leitura, df_validado, erro_msg = ler_planilha_entrada(buffer_in.getvalue(), "entrada.xlsx")
    assert sucesso_leitura is True, f"Falha na leitura: {erro_msg}"
    assert len(df_validado) == 3

    print("3. Processando lote de consultas contra a API do DetranRS...")
    eventos_progresso = []
    def callback(atual, total, item):
        eventos_progresso.append((atual, total, item))
        print(f"   Progresso: {atual}/{total} - Placa: {item.get('placa')} - Sucesso: {item.get('sucesso')}")

    df_res, df_err = processar_lote_veiculos(df_validado, progresso_callback=callback, delay_entre_requisicoes=0.5)

    print(f"4. Verificando resultados: {len(df_res)} sucessos, {len(df_err)} erros.")
    assert len(eventos_progresso) == 3
    assert len(df_res) == 1, f"Esperava 1 sucesso, obteve {len(df_res)}"
    assert len(df_err) == 2, f"Esperava 2 erros, obteve {len(df_err)}"

    # Verifica os campos retornados da API
    res_linha = df_res.iloc[0]
    print("   Dados retornados da API:", res_linha.to_dict())
    assert res_linha["Placa"] == "TUP9B47"
    assert res_linha["RENAVAM"] == "1506247196"
    assert res_linha["UF"] == "RJ"
    assert res_linha["Chassi"] == "9536B8TD6VR020673"

    print("   Erros registrados:")
    for _, err_linha in df_err.iterrows():
        print(f"   - {err_linha['Placa']} ({err_linha['RENAVAM']}): {err_linha['Motivo do erro']}")

    print("5. Gerando planilha Excel final com duas abas...")
    excel_bytes = gerar_planilha_resultado(df_res, df_err)
    assert len(excel_bytes) > 0

    xl = pd.ExcelFile(io.BytesIO(excel_bytes))
    assert "Resultados" in xl.sheet_names
    assert "Erros" in xl.sheet_names

    df_res_lido = pd.read_excel(xl, sheet_name="Resultados", dtype=str)
    df_err_lido = pd.read_excel(xl, sheet_name="Erros", dtype=str)

    assert len(df_res_lido) == 1
    assert len(df_err_lido) == 2
    assert list(df_res_lido.columns) == ["Placa", "RENAVAM", "UF", "Chassi"]
    assert df_res_lido.iloc[0]["UF"] == "RJ"
    assert list(df_err_lido.columns) == ["Placa", "RENAVAM", "Motivo do erro"]
    assert pd.notna(df_err_lido.iloc[0]["Motivo do erro"]) and len(str(df_err_lido.iloc[0]["Motivo do erro"])) > 0

    print("\n>>> TESTE DE PONTA A PONTA CONCLUÍDO COM 100% DE SUCESSO! <<<")

if __name__ == "__main__":
    test_fluxo_completo()
