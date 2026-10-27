# Automação de Consulta de Veículos — DetranRS

Aplicação em Python com interface interativa Streamlit para automatizar consultas em lote de dados de veículos na API pública do DetranRS (desenvolvida pela PROCERGS).

## 🚀 Funcionalidades

- **Download de Planilha Modelo:** Gera um arquivo Excel (.xlsx) pré-formatado com as colunas `Placa` e `Renavam`, formatadas como texto para preservar zeros à esquerda, acompanhado de uma aba de instruções.
- **Upload Flexível:** Suporte a arquivos `.xlsx` e `.xls`.
- **Validação de Cabeçalhos:** Valida de forma resiliente as colunas necessárias, tolerando espaços adicionais e variações de maiúsculas/minúsculas.
- **Consulta Confiável na API:**
  - Envia exatamente os valores informados na planilha (sem conversões prévias).
  - Trata o cabeçalho `Origin` exigido pelo gateway da PROCERGS.
  - Decodifica caracteres acentuados corretamente (charset Latin-1/ISO-8859-1 utilizado pelo órgão estadual).
  - Controle de retentativas para falhas temporárias de rede.
  - Intervalo controlado entre requisições configurável na tela (padrão de 2,0s para proteção contra bloqueios/rate-limit).
- **Acompanhamento em Tempo Real:** Barra de progresso com porcentagem, contagem de registros processados e painel de métricas (Total, Concluídas e Erros).
- **Tratamento Individual de Erros:** Qualquer falha isolada (veículo inexistente, RENAVAM incorreto, placa inválida) é registrada com seu motivo amigável sem interromper os demais veículos.
- **Exportação do Resultado Final:** Gera planilha Excel com duas abas:
  - **`Resultados`:** Apenas registros bem-sucedidos com as informações retornadas diretamente pela API (`Placa`, `RENAVAM`, `UF`, `Chassi`).
  - **`Erros`:** Registros que apresentaram divergência ou erro com `Placa`, `RENAVAM` e `Motivo do erro`.

---

## 📁 Estrutura do Projeto

```text
├── app.py                  # Interface gráfica Streamlit
├── core/
│   ├── __init__.py
│   ├── consulta.py         # Comunicação HTTP com a API do DetranRS
│   ├── processador.py      # Leitura, validação e orquestração do lote
│   └── exportacao.py       # Geração dos arquivos Excel (modelo e resultado)
├── requirements.txt        # Dependências do projeto
├── README.md               # Instruções de instalação e execução
└── test_core.py            # Testes automatizados das regras de negócio
```

---

## 🛠️ Pré-requisitos

- **Python 3.9+** instalado no computador.
- Gerenciador de pacotes **pip**.

---

## 📦 Instalação

1. Abra o terminal (PowerShell ou Prompt de Comando) na pasta do projeto:
   ```powershell
   cd "c:\Gustavo\Automação Detran RS"
   ```

2. (Opcional, porém recomendado) Crie e ative um ambiente virtual:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Instale as dependências:
   ```powershell
   pip install -r requirements.txt
   ```

---

## ▶️ Como Executar a Aplicação

### Opção 1: Pelo arquivo executável (Recomendado)
Basta dar um **duplo clique** no arquivo:
- `Iniciar_Aplicacao.bat`

A aplicação iniciará automaticamente e abrirá o navegador no endereço `http://localhost:8503`.

### Opção 2: Pelo Terminal
No terminal (PowerShell ou Prompt de Comando), execute:

```powershell
streamlit run app.py
```

O navegador abrirá automaticamente no endereço:
`http://localhost:8503`

---

## 🧪 Como Executar os Testes Automatizados

Para verificar a integridade da leitura, validação e geração de arquivos Excel:

```powershell
python test_core.py
```
