# OR-Tools (backend opcional)

O logis roda **somente com PyQGIS + a biblioteca padrão do Python**. O
[Google OR-Tools](https://developers.google.com/optimization) é um **backend opcional de
otimização**: quando está presente, os algoritmos de roteirização e de localização de
instalações podem delegar a solução a ele; quando não está — ou está quebrado —, o
plugin usa as **heurísticas em Python puro**, que são o padrão obrigatório. Nada no
logis deixa de funcionar por causa do OR-Tools.

## O comando de instalação é uma regra, não um comando fixo

O comando não pode ser copiado de um tutorial e colado em qualquer máquina: ele é
**montado a partir do ambiente Python do QGIS onde vai rodar**. A regra é:

1. instalar `ortools`;
2. acrescentar `nome==versão_instalada` para cada um de `numpy`, `pandas` e
   `typing_extensions` que **já esteja presente** no ambiente (módulo ausente fica de
   fora do comando, deixando o resolvedor do pip escolher);
3. passar `--only-binary=:all:`, para nunca tentar compilar o pacote.

Fixar `nome==versão_instalada` garante que o pip **não substitua nem altere** as versões
dos pacotes que o QGIS já carrega no seu `sys.path` — o requisito já está satisfeito e o
pip não toca no pacote instalado.

Num ambiente em que `numpy 2.1.3`, `pandas 2.2.3` e `typing_extensions 4.12.2` estejam
presentes, a regra produz:

```bash
python3 -m pip install --user --only-binary=:all: \
    ortools numpy==2.1.3 pandas==2.2.3 typing_extensions==4.12.2
```

Em outra máquina, com outras versões — ou sem o `pandas`, por exemplo —, o comando
correto é **outro**. É por isso que o plugin monta o comando na hora
(`core.ortools_installer.build_command()`, e `command_text()` para a linha pronta para
cópia) em vez de guardar uma linha literal.

### Por que a trava antiga quebra em Python 3.13

A forma antiga do comando fixava faixas em vez de versões instaladas:

```bash
# NÃO use — quebra em Python 3.13
pip install ortools "pandas<3" "numpy<2" "typing_extensions==4.10.0"
```

Ela funcionou no QGIS 3.34 (Python 3.10/3.11), mas falha no QGIS 4.2+ e no Flatpak, que
usam **Python 3.13**, por dois motivos que se somam:

- **não existe wheel de `numpy 1.x` para `cp313`** — a trava `numpy<2` não tem candidato
  binário nesse interpretador; e
- **`ortools>=9.15` exige `numpy>=2.0.2`** — ou seja, a trava contradiz diretamente o
  pacote que se está instalando, e o pip termina em `ResolutionImpossible`.

A regra `nome==versão_instalada` não tem esse problema: ela acompanha o ambiente em vez
de impor uma faixa histórica.

### Debian/Ubuntu — `--break-system-packages`

Quando o Python usado é o **do sistema** em distros com [PEP 668](https://peps.python.org/pep-0668/)
(Debian, Ubuntu), o pip recusa a instalação com `externally-managed-environment`. Nesse
caso, acrescente `--break-system-packages` ao comando:

```bash
python3 -m pip install --user --only-binary=:all: --break-system-packages \
    ortools numpy==2.1.3 ...
```

Quem roda o pip é você, então esse ajuste é seu: se a saída trouxer
`externally-managed-environment`, repita o comando com a opção acrescentada.

### Windows e macOS — use o Python do QGIS

O que importa é **qual interpretador recebe o pacote**: precisa ser o mesmo que o QGIS
usa, senão o `import ortools` dentro do QGIS continuará falhando.

No Windows há uma armadilha a mais, e ela já derrubou o comando antigo. Dentro do QGIS,
`sys.executable` **não** aponta para um Python: aponta para o `qgis-bin.exe`, porque o
QGIS embarca o interpretador no próprio executável. Um comando montado com esse valor
sai assim —

```bat
REM NÃO funciona — qgis-bin.exe não é um interpretador
"C:\Program Files\QGIS 3.34\bin\qgis-bin.exe" -m pip install ortools ...
```

— e não instala nada: o binário do QGIS não entende `-m pip`. Por isso o plugin **resolve
o `python.exe` do QGIS** (`core.ortools_installer.python_executable()`), que em geral fica
em `…\apps\Python3xx\python.exe`, e escreve esse caminho no comando que exibe:

```bat
"C:\Program Files\QGIS 3.34\apps\Python312\python.exe" -m pip install --user ^
    --only-binary=:all: --disable-pip-version-check ortools numpy==2.1.3 ...
```

Com o caminho completo na linha, o comando funciona tanto no **OSGeo4W Shell** (instalado
junto com o QGIS) quanto no **Prompt de Comando** comum — não é mais preciso que o console
já aponte para o Python certo. O que continua não servindo é trocar esse caminho pelo
`python` do PATH do Windows: é outro interpretador, e o QGIS não enxerga o que for
instalado nele.

No **macOS** vale a mesma ideia, sem a armadilha: o comando aponta para o Python embarcado
na instalação do QGIS (`/Applications/QGIS.app/Contents/MacOS/bin/python3`).

O interpretador que o plugin resolveu aparece na linha de *Ambiente detectado* do diálogo
**Dependências** — é ali que se confere, antes de instalar, se o pacote vai para o Python
certo.

## O diálogo “Dependências” do plugin

Em vez de montar o comando na mão, use **Complementos → logis → Dependências…**, que abre
o *logis — Gerenciador de Dependências*.

### O botão “Instalar OR-Tools agora”

O caminho curto é o botão **Instalar OR-Tools agora**, que aparece enquanto o OR-Tools não
estiver disponível (se não houver `pip` no ambiente, ele fica desabilitado e sobra o
comando manual). Ao clicar:

- o diálogo **pede confirmação**, avisando que o pip vai baixar algumas dezenas de MB e
  que a janela do QGIS pode ficar sem resposta durante o processo;
- a instalação roda **no Python do próprio QGIS** — o mesmo interpretador que depois vai
  importar a biblioteca —, aplicando a mesma regra de comando descrita acima;
- enquanto roda, o cursor vira relógio e **a janela pode ficar sem resposta** por alguns
  instantes: é esperado, não é travamento;
- o **log do pip aparece na tela**, na caixa escura abaixo do botão. É ali que se lê o
  motivo de uma falha — sem rede, sem permissão, sem wheel para este Python, conflito de
  `numpy`. Em ambientes PEP 668 (Debian/Ubuntu), a flag `--break-system-packages` já entra
  sozinha, decidida pela detecção de ambiente.

No fim há três desfechos, e o diálogo diz qual foi:

1. **instalado e já disponível** — o `import ortools` passa a funcionar na hora, sem
   reiniciar nada;
2. **instalado, mas é preciso reiniciar o QGIS** — o pip terminou bem e o interpretador
   ainda não enxerga a biblioteca; reinicie e ela entra;
3. **a instalação falhou** — o log fica visível, o **comando manual continua ali** para
   copiar e rodar no terminal, e o plugin segue funcionando com as heurísticas em Python
   puro.

### A linha de “Ambiente detectado”

Logo acima do botão, uma linha resume o que o plugin viu na máquina: **sistema
operacional**, **versão do Python**, **caminho do interpretador** que vai receber o
pacote, se o **`pip` está disponível**, se o ambiente é **gerenciado externamente**
(PEP 668) e se o QGIS roda em **Flatpak** ou **Snap**.

Ela existe para responder, antes de qualquer tentativa, as perguntas que explicam quase
toda falha de instalação: *é mesmo o Python do QGIS?*, *há pip aqui?*, *vai precisar de
`--break-system-packages`?*, *estou dentro de um sandbox?*. É também a linha a colar num
relato de problema.

### O comando manual continua disponível

Para quem prefere o terminal — ou quando o botão falha —, o mesmo bloco ainda:

- mostra o **status** — *Instalado (Disponível)* ou *Não instalado (Heurística pura
  ativada)*;
- **monta e exibe** o comando aplicando a regra acima com as versões detectadas na hora,
  já apontando para o interpretador do QGIS;
- copia essa linha para a área de transferência no botão **Copiar Comando**;
- lista os passos seguintes: abrir o terminal (ou o *OSGeo4W Shell*, no Windows), colar e
  executar o comando, e **reiniciar o QGIS** para que a biblioteca seja carregada.

O que o plugin **não** faz é executar processo externo: nenhum arquivo sob `logis/` chama
`subprocess`, para não acionar o achado **B603** do scanner do `plugins.qgis.org`. A
instalação pelo botão acontece **dentro do processo do QGIS**, chamando a **API do pip**
(`core.ortools_installer.install_ortools()`, com o ponto de entrada do pip resolvido em
`try/except` e fallback para o comando manual se ele não estiver acessível) — é por isso
que o log do pip sai na janela do diálogo, e não num terminal. Quando a instalação é feita
à mão, os erros do pip aparecem no seu terminal. Em qualquer um desses casos o plugin
segue funcionando com a heurística em Python puro.

O mesmo diálogo mostra o estado do **GisBR** (fonte de dados viários).

## Fallback automático para as heurísticas em Python puro

A detecção é sempre **lazy e protegida**: o `import ortools` só acontece na hora do uso e
qualquer exceção é capturada (`core.optim_backend.has_ortools()`). A escolha do backend
passa por `core.optim_backend.pick_backend()`:

- pedir `backend="ortools"` com a biblioteca disponível → resolve para `"ortools"`;
- pedir `backend="ortools"` sem a biblioteca (ausente, quebrada, ou instalada em outro
  interpretador) → **cai automaticamente** para `"python"` e registra um aviso no painel
  de *Log de Mensagens* do QGIS, aba `logis`;
- `backend="python"` (o padrão) → usa a heurística direto.

Ou seja: o resultado sai de qualquer jeito. Com o OR-Tools ele tende a ser melhor e mais
rápido; sem ele, sai pela heurística clássica (Clarke-Wright + 2-opt/Or-opt no CVRP,
Teitz-Bart na p-mediana, guloso nas coberturas) — **soluções boas, não necessariamente
ótimas**.

## Ambientes onde a instalação pode simplesmente não dar

Em instalações isoladas — **QGIS Flatpak ou Snap com Python 3.13** — pode não existir
pacote binário do OR-Tools para o interpretador do QGIS, e `--only-binary=:all:` impede a
compilação local. O pip termina em `No matching distribution found`.

Isso vale para os dois caminhos: o **botão do diálogo também falha ali**, pelo mesmo
motivo de sempre — não há wheel para o Python do QGIS —, e o log na tela mostra
exatamente essa mensagem. **Nada precisa ser feito**: todos os algoritmos continuam
disponíveis com as heurísticas em Python puro.
