# Arquivo Bolsonaro | Declarações e documentos

Acervo documental sobre declarações públicas de Jair Bolsonaro e Flávio Bolsonaro. Reúne fichas com fontes, entrevistas, vídeos, áudios, documentos, comparações entre falas e acompanhamento de publicações. A interface é estática, em português, com pesquisa e filtros executados no navegador.

Repositório público: [QGBALTIGO/Internacional](https://github.com/QGBALTIGO/Internacional).

## Abrangência desta edição

A edição 02 tem revisão editorial de **24 de outubro de 2026**. O conjunto incluído em `content/acervo.editorial.json` contém:

| Conteúdo | Quantidade |
| --- | ---: |
| Fichas de declarações | 71 |
| Fichas de Jair Bolsonaro | 45 |
| Fichas de Flávio Bolsonaro | 26 |
| Vídeos e áudios | 43 |
| Comparações entre falas | 5 |
| Documentos de referência | 12 |
| Episódio com apuração, cronologia e respostas | 1 |

Este é um acervo selecionado. A contagem não representa a totalidade das declarações, suas repetições ou a intenção dos autores. Os 43 itens multimídia incluem entrevistas completas e materiais de contexto; sua presença não significa que todas as falas contidas nesses registros tenham sido verificadas.

## Executar localmente

Use Python 3.12, versão configurada no workflow. O site não exige Node.js, framework, banco de dados ou serviço de aplicação. A geração do PDF utiliza ReportLab, Pillow e as fontes DejaVu.

Na raiz do repositório, restaure os anexos, instale as dependências do PDF e gere a edição para download:

```sh
python scripts/fetch_assets.py
python -m pip install -r requirements.txt
python scripts/build_pdf.py
python scripts/sync_content.py
python -m http.server 8080 --directory dist
```

Abra [http://localhost:8080](http://localhost:8080). Em ambientes que oferecem apenas o comando `python3`, use-o no lugar de `python`.

O gerador de PDF procura `DejaVuSans.ttf`, `DejaVuSans-Bold.ttf`, `DejaVuSerif.ttf` e `DejaVuSerif-Bold.ttf` em `/usr/share/fonts/truetype/dejavu`. Em Debian e Ubuntu, essas fontes são fornecidas pelo pacote `fonts-dejavu-core`. Em outros sistemas, ajuste a função `register_fonts()` de `scripts/build_pdf.py` para o diretório das fontes instaladas.

### Arquivos grandes e restauração

O clone conserva os dados, scripts, fontes tipográficas, miniaturas e imagens pequenas. Os anexos públicos maiores que 500 KB são relacionados em `content/assets.json`, com endereço de origem, destino, crédito, licença e SHA-256. O PDF compilado é gerado localmente.

`scripts/fetch_assets.py` baixa os anexos do manifesto, verifica o SHA-256 e grava o arquivo somente depois dessa conferência. Arquivos locais com o hash esperado são reaproveitados. Uma divergência exige revisar a fonte antes de atualizar o manifesto. Os novos áudios hospedados pelos publicadores continuam acessíveis pelas URLs originais.

A pasta preparada para publicação deve conter os anexos restaurados e o PDF gerado. Os scripts de coleta, sincronização e restauração usam apenas a biblioteca padrão do Python; `requirements.txt` reúne exclusivamente as dependências externas do PDF.

## Recursos da interface

- Busca sem distinção de acentos, com filtros de pessoa, assunto, classificação e ano.
- Visualização em cartões ou linha do tempo, ordenação e carregamento progressivo.
- Fichas com síntese da declaração, evidência, contexto, fontes, revisão e correções documentadas.
- Links diretos no formato `#ficha=identificador`, exportação da ficha em TXT e impressão.
- Exportações JSON e CSV do acervo carregado, incluindo atualizações editoriais aplicadas pelo navegador.
- Midiateca com pesquisa, filtros por pessoa e tipo de registro, créditos e acesso à publicação original.
- Comparações com duas datas, referências e explicação do contexto.
- Favoritos e preferência de tema mantidos no navegador, sem conta de usuário.
- Navegação por teclado, diálogos nativos, indicação de foco, tema claro ou escuro e respeito à preferência de movimento reduzido.

O atalho `/` leva à busca principal quando o foco não está em um campo de formulário ou diálogo. Os favoritos pertencem ao navegador e não são sincronizados entre dispositivos.

## Estrutura do projeto

| Caminho | Responsabilidade |
| --- | --- |
| `dist/index.html` | Estrutura e navegação do site |
| `dist/assets/app.js` | Pesquisa, filtros, diálogos, exportações e atualização remota |
| `dist/assets/styles.css` | Layout, temas, animações, responsividade e impressão |
| `dist/assets/` | Imagens, fonte local, miniaturas e anexos de mídia |
| `dist/data/` | Dados distribuídos em JSON, versões JavaScript e CSV |
| `dist/documentos/` | PDF da edição, documentos locais e eventual pacote portátil |
| `content/acervo.editorial.json` | Base editorial canônica |
| `content/editorial-updates.json` | Complemento editorial aplicado por identificador |
| `content/sources.json` | Catálogo de fontes RSS e Atom, com fontes ativas e desativadas |
| `content/assets.json` | Manifesto dos anexos públicos para restauração |
| `scripts/sync_content.py` | Validação e geração dos dados distribuídos |
| `scripts/update_news.py` | Coleta das publicações e situação de cada fonte |
| `scripts/build_pdf.py` | Geração do dossiê a partir da base canônica |
| `scripts/fetch_assets.py` | Restauração dos anexos com verificação de integridade |
| `scripts/package_portable.py` | Geração de uma cópia portátil |
| `.github/workflows/atualizar-fontes.yml` | Configuração da coleta periódica no GitHub Actions |
| `tests/test_news.py` | Testes de integridade da coleta |
| `documentacao/` | Histórico de alterações e registros de validação |

`scripts/integrate_edition.py` registra a integração editorial da edição 02. A manutenção cotidiana deve partir dos arquivos em `content/`; não depende de repetir a integração dos lotes de pesquisa originais.

## Critérios editoriais e dados

Cada ficha deve identificar a pessoa, a declaração, sua data ou precisão temporal, o contexto e as fontes que sustentam a conclusão. O texto da declaração é uma paráfrase quando identificado como síntese. A formulação original deve ser consultada no registro indicado.

| Classificação | Critério |
| --- | --- |
| Falso | A evidência contradiz a afirmação central |
| Enganoso | O recorte, a comparação ou a omissão distorce a compreensão |
| Sem comprovação | A sustentação disponível é insuficiente para confirmar a alegação |

As classificações descrevem o conteúdo e não presumem intenção de mentir. Uma mudança de posição pode ser legítima. Comparações, correções posteriores e apurações têm campos e contexto próprios. Investigação, acusação e condenação devem conservar suas distinções.

Na coleção `records`, mantenha `id` estável, `person`, `title`, `claim`, `summary`, `context`, `topic`, `verdict`, `dateLabel`, `year` e `sources`. Quando conhecida, registre a data exata em `statementDate`; quando parcial, preserve essa limitação em vez de inventar um dia. `reviewedAt` informa a revisão editorial da ficha. Relações com a midiateca usam os identificadores de `relatedMedia`.

Cada fonte contém título, publicador, URL e, quando disponível, data. `type` distingue documento ou registro primário de checagem publicada e apuração jornalística. As referências devem sustentar a autoria e a conclusão específica da ficha. Mudanças substanciais precisam preservar correções, respostas e ressalvas relevantes.

### Atualizar a base e sincronizar

Edite `content/acervo.editorial.json` após conferir as fontes. Atualize a data de revisão da ficha e, quando pertinente, `metadata.reviewedAt` e a edição. Execute:

```sh
python scripts/sync_content.py
```

O script verifica identificadores, campos obrigatórios, classificações, referências HTTPS, relações com mídias e existência dos anexos locais. Em seguida, gera `dist/data/acervo.json`, `dist/data/acervo.js` e `dist/data/acervo.csv`. A versão JavaScript permite iniciar a interface com os dados incluídos, sem depender de uma requisição ao JSON.

A validação estrutural não substitui a revisão das evidências. O CSV usa UTF-8 com BOM, separador `;` e proteção contra interpretação dos textos como fórmulas por planilhas.

### Publicar um complemento editorial

`content/editorial-updates.json` permite distribuir acréscimos e correções sem substituir os arquivos de interface. O formato inclui `schemaVersion: 1`, `updatedAt` e as listas `records`, `media`, `documents`, `comparisons` e `investigations`.

Insira o **objeto completo** de cada item alterado. O cliente substitui o item com o mesmo `id` ou acrescenta um identificador novo; não combina campos de objetos parciais. A ausência de um identificador no complemento não exclui o registro da base. A implementação atual não oferece remoção por esse arquivo.

Use `updatedAt` para a data e hora da revisão editorial, em ISO 8601, e mantenha `reviewedAt` nos registros revisados. Essa data pode atualizar a revisão geral exibida pelo site. Ela não deve ser alterada apenas porque houve uma coleta de notícias.

Depois de editar, execute `python scripts/sync_content.py`. O comando também sincroniza o complemento para `dist/data/editorial-updates.json` e `dist/data/editorial-updates.js`. Versione os arquivos de origem e os arquivos gerados juntos.

O complemento é aplicado pelo navegador. Para incorporá-lo à próxima edição do PDF, consolide as alterações em `content/acervo.editorial.json` e gere novamente o documento. O gerador de PDF não consulta automaticamente o complemento remoto.

## Acompanhamento de notícias

A coleta RSS e Atom publica **títulos, datas, publicadores, links e metadados de acompanhamento**. Ela não reproduz os artigos completos e não atribui vereditos. A indicação de que uma publicação vem de uma fonte de checagem descreve o tipo da publicação; sua inclusão entre as fichas depende de revisão editorial.

As fontes estão em `content/sources.json`. Para realizar uma coleta manual:

```sh
python scripts/update_news.py
```

O coletor filtra referências aos autores, normaliza endereços, remove parâmetros de rastreamento, deduplica URLs e mantém até 500 publicações dos últimos 180 dias. A cobertura depende do conteúdo disponibilizado por cada feed. Os resultados são gravados em `dist/data/news.json` e `dist/data/news.js`.

O painel apresenta a última tentativa, a última coleta com resultado e a situação de cada fonte. Falhas não apagam imediatamente os itens anteriores: eles permanecem enquanto estiverem dentro da janela de retenção e dos limites da coleção. Se nenhuma fonte responder, o script registra a tentativa e encerra com código de erro.

### Agendamento no GitHub Actions

O arquivo `.github/workflows/atualizar-fontes.yml` configura:

- Execução horária, no minuto 17 de cada hora em UTC, pelo cron `17 * * * *`.
- Execução manual por `workflow_dispatch`.
- Execução em alterações de `main` que atinjam o coletor, o catálogo de fontes ou o próprio workflow.
- Commit dos arquivos `dist/data/news.json` e `dist/data/news.js` quando houver mudanças, usando a permissão `contents: write` do token do workflow.

Não são necessárias chaves de API ou credenciais de leitores para consultar as fontes públicas. A configuração do cron expressa a periodicidade pretendida. Confirme execuções efetivas e eventuais falhas no [histórico do GitHub Actions](https://github.com/QGBALTIGO/Internacional/actions); este README não certifica que o agendamento já foi executado.

### Atualização no navegador e funcionamento sem conexão

Ao abrir a página por HTTP ou HTTPS, o cliente consulta `news.json` e `editorial-updates.json` em:

```text
https://raw.githubusercontent.com/QGBALTIGO/Internacional/main/dist/data/
```

A consulta se repete a cada 20 minutos enquanto a aba está visível. O botão de atualização também solicita a versão disponível. Esse intervalo é a frequência de leitura do navegador, independente da coleta horária dos feeds.

O site inicia com os dados incluídos em `dist/data/*.js`. Notícias e complementos recebidos podem ser guardados em `localStorage` e reutilizados nas visitas seguintes. Se o GitHub ou a conexão falhar, os dados já carregados continuam disponíveis. Restrições ao armazenamento local não impedem a navegação na sessão.

Uma cópia local com seus arquivos disponíveis permite consultar as fichas sem conexão. A abertura direta por `file:` usa os dados incluídos e desativa a consulta remota. Vídeos incorporados, áudios externos, notícias e documentos mantidos apenas na origem exigem acesso à internet. Não há Service Worker que faça o download integral do site para uso offline.

## Gerar o PDF e a cópia portátil

Com os anexos restaurados, as fontes DejaVu instaladas e as dependências de `requirements.txt` disponíveis:

```sh
python scripts/build_pdf.py
```

O comando lê `content/acervo.editorial.json`, gera `dist/documentos/dossie-documental.pdf` e registra o resumo da geração em `qa/pdf/manifest.json`. O documento inclui fichas, comparações, apurações, referências e créditos. A capa informa a edição e a revisão documental.

Para escolher outros arquivos de entrada e saída:

```sh
python scripts/build_pdf.py --data content/acervo.editorial.json --output dist/documentos/dossie-documental.pdf
```

O PDF é um retrato da edição na data indicada. Coletas RSS posteriores não o atualizam. Após alterações editoriais, sincronize os dados, gere o PDF e confira a composição das páginas antes de distribuir a nova edição.

Para gerar o pacote portátil depois dessa preparação:

```sh
python scripts/package_portable.py
```

O arquivo resultante fica em `dist/documentos/arquivo-bolsonaro.zip`. O pacote inclui um manifesto de integridade em `documentacao/ARQUIVOS-SHA256.json`. No pacote extraído, `index.html` fica na raiz; nesse formato, sirva a pasta extraída com `python -m http.server 8080`.

## Verificação e publicação

Os testes do coletor podem ser executados sem acessar fontes reais:

```sh
python -m unittest discover -s tests -p 'test_*.py'
```

Eles cobrem leitura de RSS e Atom, atribuição aos autores, metadados sem texto integral ou veredito, tratamento de URLs, retenção em falhas e duplicação de itens. Para conferir uma edição, execute também a sincronização estrutural e revise no navegador a busca, os filtros, as fichas, os links, a reprodução das mídias e os downloads.

A raiz a publicar em uma hospedagem estática é `dist/`, após restaurar anexos e gerar os documentos. Não é necessário processo de aplicação em produção. O endereço de uma implantação deve ser confirmado na plataforma escolhida antes de ser anunciado como ativo. A existência do repositório e dos arquivos de automação não comprova, por si só, uma hospedagem pública em funcionamento.

## Desempenho, privacidade e créditos

A interface usa HTML, CSS e JavaScript sem framework. A pesquisa opera sobre um índice local, e os cartões são exibidos progressivamente. Miniaturas usam carregamento tardio; os players do YouTube são criados somente quando solicitados e usam `youtube-nocookie.com`. Os cartões de áudio utilizam `preload="none"`. Ao abrir um player em diálogo, metadados podem ser carregados.

Fontes e retratos de apresentação estão no próprio site. Os efeitos respeitam `prefers-reduced-motion`. Busca, tema e favoritos são processados no navegador; a aplicação não exige login nem mantém um banco de dados de leitores. Consultas ao GitHub, miniaturas externas e reprodução de mídias estabelecem conexões com seus respectivos provedores.

Fotografias, vídeos, áudios, documentos e matérias conservam os direitos e as condições de uso dos respectivos autores e publicadores. Consulte `images`, `media` e `documents` na base editorial, o manifesto de anexos e a seção **Fontes e créditos** da interface. A fonte Manrope é distribuída sob Open Font License 1.1, incluída em `dist/assets/OFL-Manrope.txt`.

Este README não concede uma licença geral sobre materiais de terceiros. A disponibilidade de um link, de uma incorporação ou de uma cópia local não transfere os direitos do publicador. Preserve os créditos, a procedência e as condições próprias de cada material em qualquer redistribuição.

Para sugerir correções no repositório, informe o identificador da ficha, o trecho a corrigir, o motivo e a fonte que sustenta a alteração. O histórico de alterações deve permitir reconstruir a revisão e manter visíveis as correções relevantes.
