# Guia de Instalação

## Requisitos

| | |
|---|---|
| **QGIS** | 3.16 ou superior (`qgisMinimumVersion=3.16`, `qgisMaximumVersion=4.99`) |
| **Qt** | Qt5 (QGIS 3.x) e Qt6 (QGIS 4.x) — o plugin declara `supportsQt6=True` |
| **Python** | o interpretador embarcado no QGIS; apenas a biblioteca padrão é usada |
| **Dependências externas** | nenhuma obrigatória |

O logis roda somente com **PyQGIS + stdlib**. `pyarrow` e `OR-Tools` são opcionais: o
import é *lazy* e há fallback automático para as heurísticas em Python puro, de modo que
a ausência (ou a falha de instalação) dessas bibliotecas nunca impede o uso do plugin.

## Instalação pelo pacote ZIP

O pacote distribuível é gerado em `dist/logis-<versão>.zip` (por exemplo,
`dist/logis-0.1.5.zip`) — para gerá-lo a partir do código-fonte, use `make package`.

1. No QGIS, abra **Complementos → Gerenciar e Instalar Complementos…**
2. Vá até a aba **Instalar a partir do ZIP**.
3. Em *Arquivo ZIP*, aponte para `dist/logis-<versão>.zip`.
4. Clique em **Instalar Complemento**. Confirme o aviso de instalação a partir de fonte
   não oficial, caso apareça.
5. Na aba **Instalados**, verifique que **Logis** está marcado.

## Habilitando o complemento `experimental`

O logis declara `experimental=True` no seu `metadata.txt`. O Gerenciador de Complementos **oculta
plugins experimentais por padrão**, então, para encontrá-lo na aba *Todos* (instalação
pelo repositório oficial) ou para que ele apareça após a instalação, é preciso liberar a
exibição:

1. **Complementos → Gerenciar e Instalar Complementos… → Configurações**.
2. Marque **Mostrar também complementos experimentais**.
3. Volte à aba **Todos** e pesquise por `logis`.

> A instalação a partir do ZIP funciona mesmo com a opção desmarcada, mas o complemento
> pode não ser listado depois — mantenha a opção marcada enquanto o logis estiver
> em estado experimental.

## Onde as funções aparecem

Depois de instalado e habilitado, o logis se expõe em três lugares:

- **Caixa de Ferramentas de Processamento** — provedor **logis**, com todos os
  algoritmos (`logis:*`) agrupados por módulo. É a via scriptável, também acessível pelo
  Console Python via `processing.run("logis:...", {...})`.
- **Menu Complementos → logis** — as entradas *Indicadores Urbanos*, *Indicadores
  Regionais*, *Coleta de Lixo* e *Dependências…*.
- **Painéis (docks)**, ancorados à **direita** da janela principal e abertos pelas
  entradas do menu acima:
  - *logis — Indicadores Urbanos*
  - *logis — Indicadores Regionais*
  - *logis — Coleta de Lixo*

  Se um painel for fechado, reabra-o pela entrada correspondente no menu **Complementos
  → logis** (ou por **Ver → Painéis**).

O diálogo **logis — Gerenciador de Dependências** (menu **Complementos → logis →
Dependências…**) mostra o estado de `OR-Tools` e `pyarrow` e oferece a instalação
assistida do backend opcional de otimização.

## Ambientes validados

- **QGIS 4.2 “Belém do Pará” sobre Ubuntu** — validado pelo autor. A instalação do
  OR-Tools pelo diálogo *Dependências* fixa as versões já presentes no ambiente do QGIS
  (`numpy`, `pandas`, `typing_extensions`), evitando que o pip substitua pacotes em uso
  pelo QGIS.
- **QGIS 4.2 Flatpak / Python 3.13** — o plugin funciona normalmente, mas a **instalação
  do OR-Tools pode falhar** por ausência de pacote binário (wheel) para esse
  interpretador em ambiente isolado. Nesse caso, todos os algoritmos continuam
  disponíveis com as heurísticas em Python puro; nada precisa ser feito.

## Instalação por symlink (desenvolvimento)

Para trabalhar no código sem reempacotar a cada mudança, o `Makefile` cria um link
simbólico do diretório `logis/` dentro do perfil `default` do QGIS:

```bash
cd ~/projects/logis

make deploy         # perfil QGIS3 (Qt5): ~/.local/share/QGIS/QGIS3/...
make deploy-flatpak # perfil QGIS3 do QGIS instalado via Flatpak
```

Depois do symlink, recarregue o complemento no QGIS (com o *Plugin Reloader*) ou
reinicie o programa. Para desfazer, use `make undeploy` (ou `make undeploy-flatpak`).

> O alvo aborta com erro se já existir um diretório real — e não um symlink — no destino;
> nesse caso, remova a instalação anterior pelo Gerenciador de Complementos antes de
> rodar o `make deploy`.

Verificações rápidas durante o desenvolvimento:

```bash
make test                            # checagem de sintaxe de todos os .py (sem QGIS)
python3 tools/qgis4_compat_check.py  # símbolos legados/escopados de Qt6 / QGIS 4
```
