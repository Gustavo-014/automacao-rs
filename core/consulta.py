"""Comunicação com a API de consulta simplificada de veículos do DetranRS."""

import json
import logging
import time
from typing import Any, Dict, Optional, Tuple
import requests

logger = logging.getLogger(__name__)

DETRAN_API_URL = "https://pcsdetran.procergs.com.br/pcsdetran/rest/veiculos/simplificada"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Origin": "https://pcsdetran.rs.gov.br",
    "Referer": "https://pcsdetran.rs.gov.br/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def criar_sessao_detran() -> requests.Session:
    """Cria e configura uma sessão HTTP com os cabeçalhos necessários."""
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def _decodificar_resposta(response: requests.Response) -> str:
    """Decodifica o texto da resposta HTTP tratando encodings da PROCERGS (ISO-8859-1)."""
    raw_bytes = response.content
    # A API da PROCERGS comumente emite respostas em ISO-8859-1 / Latin-1
    try:
        # Testa se decodifica perfeitamente como UTF-8 estrito
        return raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return raw_bytes.decode("iso-8859-1", errors="replace")


def _extrair_mensagem_erro_json(texto_resposta: str) -> Optional[str]:
    """Tenta extrair uma mensagem amigável de erro de uma resposta JSON."""
    try:
        dados = json.loads(texto_resposta)
        if isinstance(dados, list) and len(dados) > 0 and isinstance(dados[0], dict):
            msg = dados[0].get("message") or dados[0].get("erro") or dados[0].get("detail")
            if msg:
                return str(msg).strip()
        elif isinstance(dados, dict):
            msg = dados.get("message") or dados.get("erro") or dados.get("detail")
            if msg:
                return str(msg).strip()
    except Exception:
        pass
    return None


def consultar_veiculo(
    placa: str,
    renavam: str,
    session: Optional[requests.Session] = None,
    timeout: int = 15,
    max_retries: int = 2,
    delay_between_retries: float = 1.0,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Consulta um veículo na API do DetranRS.

    Parâmetros:
        placa: Placa original informada na planilha.
        renavam: RENAVAM original informado na planilha.
        session: Sessão HTTP reutilizável (opcional).
        timeout: Tempo limite em segundos para cada requisição.
        max_retries: Quantidade máxima de tentativas para falhas transitórias.
        delay_between_retries: Intervalo em segundos entre tentativas.

    Retorna:
        (sucesso, dados_veiculo, motivo_erro)
        Se sucesso for True:
            dados_veiculo: dict com chaves {'Placa', 'RENAVAM', 'UF', 'Chassi'}
            motivo_erro: None
        Se sucesso for False:
            dados_veiculo: None
            motivo_erro: string descrevendo a causa da falha.
    """
    placa_limpa = str(placa or "").strip()
    renavam_limpo = str(renavam or "").strip()

    if not placa_limpa:
        return False, None, "Placa não informada ou vazia."
    if not renavam_limpo:
        return False, None, "RENAVAM não informado ou vazio."

    sessao = session or criar_sessao_detran()
    params = {
        "placa": placa_limpa,
        "renavam": renavam_limpo,
        "somenteRS": "false",
    }

    tentativa = 0
    ultimo_erro = "Falha desconhecida na requisição."

    while tentativa < max_retries:
        tentativa += 1
        try:
            response = sessao.get(
                DETRAN_API_URL,
                params=params,
                timeout=timeout,
            )

            texto_resposta = _decodificar_resposta(response)

            # Caso 1: Sucesso HTTP 200
            if response.status_code == 200:
                try:
                    dados_json = json.loads(texto_resposta)
                except Exception:
                    return False, None, "Resposta do servidor não é um JSON válido."

                # Verifica indicadores de erro de negócio no corpo do JSON
                if dados_json.get("temErro") is True or dados_json.get("erro"):
                    msg = dados_json.get("erro") or "Veículo com restrição ou erro retornado pela API."
                    return False, None, str(msg).strip()

                # Valida dados essenciais retornados pela API
                placa_api = dados_json.get("placa")
                renavam_api = dados_json.get("renavam")

                if not placa_api and not renavam_api:
                    return False, None, "Dados do veículo não retornados pela API."

                # Mapeamento estrito conforme os requisitos:
                # 1. Placa <- placa
                # 2. RENAVAM <- renavam (preservando formato texto)
                # 3. UF <- ufPlaca
                # 4. Chassi <- chassi
                resultado = {
                    "Placa": str(placa_api).strip() if placa_api is not None else "",
                    "RENAVAM": str(renavam_api).strip() if renavam_api is not None else "",
                    "UF": str(dados_json.get("ufPlaca") or "").strip(),
                    "Chassi": str(dados_json.get("chassi") or "").strip(),
                }

                return True, resultado, None

            # Caso 2: HTTP 400 (Bad Request - comumente placa inválida, renavam incorreto, etc.)
            elif response.status_code == 400:
                msg_amigavel = _extrair_mensagem_erro_json(texto_resposta)
                if msg_amigavel:
                    return False, None, msg_amigavel
                return False, None, f"Requisição inválida (HTTP 400): {texto_resposta[:100]}"

            # Caso 3: HTTP 429 (Rate limiting / Muitas requisições)
            elif response.status_code == 429:
                return False, None, "Limite de requisições excedido (HTTP 429 - Bloqueio temporário por excesso de consultas). Aumente o intervalo e aguarde alguns instantes."

            # Caso 4: HTTP 401 ou 403 (Autenticação/Bloqueio)
            elif response.status_code in (401, 403):
                return False, None, f"Acesso não autorizado ou bloqueado pelo serviço DetranRS (HTTP {response.status_code})."

            # Caso 5: HTTP 404 (Não encontrado)
            elif response.status_code == 404:
                return False, None, "Veículo ou serviço não encontrado (HTTP 404)."

            # Caso 6: HTTP 5xx (Erro interno do servidor)
            elif 500 <= response.status_code < 600:
                ultimo_erro = f"Serviço do DetranRS instável ou indisponível (HTTP {response.status_code})."
                # Erro 5xx é temporário, pode tentar novamente
                if tentativa < max_retries:
                    time.sleep(delay_between_retries)
                    continue
                return False, None, ultimo_erro

            # Outros códigos HTTP
            else:
                return False, None, f"Erro inesperado do servidor DetranRS (HTTP {response.status_code})."

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            ultimo_erro = "Falha de conexão ou tempo limite excedido ao contatar o DetranRS."
            logger.warning("Falha temporária ao consultar veículo %s (%s): %s", placa_limpa, renavam_limpo, e)
            if tentativa < max_retries:
                time.sleep(delay_between_retries)
                continue
            return False, None, ultimo_erro

        except requests.exceptions.RequestException as e:
            return False, None, f"Erro na requisição HTTP: {str(e)}"

        except Exception as e:
            return False, None, f"Erro inesperado durante a consulta: {str(e)}"

    return False, None, ultimo_erro
