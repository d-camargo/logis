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
(`ORToolsInstallTask.build_command()`) em vez de guardar uma linha literal.

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

O diálogo *Dependências* faz isso sozinho: ao detectar `externally-managed-environment`
na saída do pip, ele repete a instalação **uma única vez** com a opção acrescentada.

### Windows e macOS — use o Python do QGIS

O que importa é **qual interpretador recebe o pacote**: precisa ser o mesmo que o QGIS
usa, senão o `import ortools` dentro do QGIS continuará falhando.

- **Windows:** abra o **OSGeo4W Shell** (instalado junto com o QGIS) e rode o comando
  ali — é o console que já aponta para o Python do QGIS. Não use o `python` do PATH do
  Windows.
- **macOS:** use o Python embarcado na instalação do QGIS
  (`/Applications/QGIS.app/Contents/MacOS/bin/python3`).

Dentro do QGIS, `sys.executable` no Console Python mostra qual interpretador está em uso
— e é exatamente ele que o instalador do plugin chama.

## O diálogo “Dependências” do plugin

Em vez de montar o comando na mão, use **Complementos → logis → Dependências…**, que
abre o *logis — Gerenciador de Dependências*. Para o OR-Tools ele:

- mostra o **status** — *Instalado (Disponível)* ou *Não instalado (Heurística pura
  ativada)*;
- instala com o botão **Instalar OR-Tools**, em segundo plano (`QgsTask`, cancelável),
  aplicando a regra acima com as versões detectadas na hora;
- exibe a **saída do pip** ao vivo em um painel de log;
- traduz as falhas mais comuns em mensagens claras (sem rede, sem permissão, sem `pip`,
  sem wheel para este Python, conflito de `numpy`), sempre lembrando que o plugin segue
  funcionando com a heurística;
- avisa que é preciso **reiniciar o QGIS** depois de uma instalação bem-sucedida, para
  que a biblioteca seja carregada.

O mesmo diálogo mostra o estado do **GisBR** (fonte de dados viários) e do **pyarrow**.

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
pacote binário do OR-Tools para o interpretador do QGIS, e `--only-binary=:all:` impede
a compilação local. O diálogo relata a falha e **nada precisa ser feito**: todos os
algoritmos continuam disponíveis com as heurísticas em Python puro.
