# Painel SuperAção SP — protótipo Streamlit

Identidade visual conforme **Manual de Identidade Visual do Governo do Estado de
São Paulo**, GESP v1.6, abr 2023.

## Estrutura

```
painel/
├── app.py                    aplicação
├── .streamlit/config.toml    tema com as cores oficiais
├── dados/                    saída da camada agregada (versão publicável)
│   ├── funil.csv
│   ├── tempos.csv
│   ├── recusas.csv
│   └── qualidade.csv
└── marcas/                   arquivos de logotipo
    ├── sp_governo_horizontal_negativo.png
    └── bid.png
```

## Como abrir o painel no Windows

### Forma mais simples e recomendada

Na pasta do projeto, execute:

`powershell
.\rodar_app.ps1
` 

Esse iniciador usa obrigatoriamente o Python do .venv e evita erros de dependências instaladas em outro ambiente.


Abra o **PowerShell** dentro da pasta do projeto. No Explorador de Arquivos,
entre na pasta `Dashboard`, clique na barra de endereços, digite `powershell` e
pressione **Enter**.

### Uso normal (o ambiente `.venv` já existe)

Ative o ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Quando aparecer `(.venv)` no início da linha, execute o app:

```powershell
streamlit run app.py
```

O navegador normalmente abre sozinho em <http://localhost:8501>. Para encerrar
o painel, volte ao PowerShell e pressione **Ctrl+C**. Para sair do ambiente
virtual, execute:

```powershell
deactivate
```

### Atalho sem ativar o ambiente virtual

Também é possível iniciar o painel diretamente com um único comando:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

### Se o PowerShell bloquear a ativação

Libere scripts apenas para essa janela e tente ativar novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Essa permissão termina quando a janela do PowerShell é fechada. Como
alternativa, use o comando de atalho acima, que não exige ativação.

### Recriar o `.venv` (somente se ele estiver ausente ou com problema)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

Execute sempre os comandos na pasta que contém `app.py`, `dados`, `assets` e
`requirements.txt`.

## Acrescentar um relatório

Duas alterações:

```python
def rel_novo(d: dict) -> None:
    secao("Título da seção")
    linha_cartoes([("Rótulo", "42%", "apoio")])

RELATORIOS = [
    ...,
    {"titulo": "Novo relatório", "fn": rel_novo, "status": "atual"},
]
```

A navegação, o marcador de situação e o título do cabeçalho se ajustam sozinhos.

## Decisões de identidade

| Elemento | Valor | Origem |
|---|---|---|
| Vermelho | `#FF161F` PANTONE 485 C | p. 10 |
| Preto | `#000000` PANTONE BLACK | p. 10 |
| Cinza 50% / 25% | `#808080` / `#BFBFBF` | p. 10 |
| Amarelo | `#FBB900` PANTONE 123 C | p. 10, paleta secundária |
| Azul | `#034EA2` PANTONE 2955 C | p. 10, paleta secundária |
| Verde | `#0B9247` PANTONE 347 C | p. 10, paleta secundária |
| Tipografia | Verdana | p. 24, 28, 29 |
| Grid | 12 colunas, 30px; 4 colunas <576px | p. 26 |
| Régua de logotipos | parceiros à esquerda, Governo à direita | p. 19, 21 |
| Tamanho mínimo digital | H = 5px | p. 12 |

**Papéis das cores no painel.** O vermelho fica reservado à identidade — faixa
superior, filete, marcador do item ativo, traço sob os títulos. Ele não é usado
como cor de alerta: num painel assinado pelo Governo do Estado, vermelho já
significa "Governo", e usá-lo também para desempenho ruim faz o cabeçalho inteiro
parecer alarme. Advertência usa o amarelo `#FBB900` da paleta secundária.

**Divergência no manual.** Na p. 10, o vermelho aparece como `#FF161F` mas com
RGB 237/28/36, que corresponde a `#ED1C24`. O código usa o hexadecimal impresso.
Vale confirmar com a Secretaria Especial de Comunicação qual prevalece.
