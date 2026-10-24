# Atualização do acervo

## Objetivo e destinos

Manter o Arquivo Bolsonaro atualizado com checagens publicadas, declarações, entrevistas, vídeos, áudios, documentos e desdobramentos envolvendo Jair Bolsonaro e Flávio Bolsonaro. A cobertura é ampliada progressivamente e não representa um inventário completo de tudo o que ambos disseram.

O repositório autorizado é `QGBALTIGO/Internacional`, branch `main`. O site publicado lê os arquivos públicos desta branch. Uma atualização de dados não exige republicar o desenho do site.

As instruções editoriais estão em `documentacao/CRITERIOS-EDITORIAIS.md`. A execução deve respeitar as permissões efetivamente disponíveis no conector. Se houver pedido de reconexão, aprovação ou acesso insuficiente, preservar os dados existentes e informar o impedimento. Nunca buscar tokens em arquivos ou contornar controles de acesso.

## Duas rotinas

O workflow `.github/workflows/atualizar-fontes.yml` consulta RSS e Atom a cada hora. O script usa somente a biblioteca padrão do Python. Publica títulos, datas, veículos, links e a situação de cada consulta em `dist/data/news.json` e `dist/data/news.js`. Não atribui vereditos. O GitHub pode atrasar ou interromper execuções; o painel exibe o horário efetivo da coleta.

A tarefa de pesquisa complementar procura novos materiais e confere a documentação antes de ampliar as fichas. Ela pode usar busca pública e o conector GitHub. Essa pesquisa não deve alterar a configuração de permissões, enviar mensagens aos veículos ou republicar artigos integrais.

## Procedimento de pesquisa

1. Ler a versão atual de `content/acervo.editorial.json`, `content/editorial-updates.json`, `dist/data/news.json` e os critérios editoriais. Conferir as datas para evitar refazer ou duplicar registros.
2. Consultar publicações recentes de Aos Fatos, Lupa, AFP Checamos, Estadão Verifica e veículos que apresentem documentos ou gravações. Verificar também TSE, STF, TCU, Câmara, Senado, PF, Anvisa, IBGE e demais fontes primárias pertinentes ao episódio. `content/sources.json` informa os feeds já conferidos. Os feeds não cobrem toda a produção de cada veículo.
3. Procurar entrevistas e declarações em canais originais, por exemplo Flow, TV Cultura, TV Senado, TV Câmara, CNN Brasil, Poder360 e os próprios emissores. Identificar vídeo, canal, data e eventual trecho relevante. Não inventar IDs, marcações de tempo ou transcrições. Um título do YouTube não basta para classificar uma alegação.
4. Quando não houver novidade recente suficiente, ampliar um episódio histórico ainda pouco documentado. Preferir novos registros distintos a várias fichas da mesma afirmação repetida. Não há quantidade mínima por execução.
5. Abrir as fontes usadas. Separar data da fala, data de publicação e data da revisão. Uma ficha exige declaração atribuída com segurança e evidência diretamente relacionada. Usar ao menos uma checagem identificada ou um confronto documental explícito; acrescentar fonte primária quando disponível. Registrar respostas, recuos, ressalvas e correções posteriores.
6. Comparações de falas precisam de ambos os registros. Distinguir contradição documentada, correção posterior e mudança de posição. Alteração de posição política, isoladamente, não comprova falsidade.
7. No caso Vorcaro, separar contatos, pedidos, valores negociados, transferências documentadas e alegações investigativas. Não confundir autorização para investigar com condenação. Só usar materiais já publicados legitimamente, com procedência, contexto e respostas. Não publicar dados pessoais desnecessários.
8. Se a evidência for insuficiente, não acrescentar uma ficha com veredito. Um link relevante pode integrar a seção de publicações ou um dossiê com atribuição e limites claros.

## Formato do complemento editorial

Preservar `schemaVersion: 1`, `updatedAt` em ISO 8601 e os arrays `records`, `media`, `documents`, `comparisons` e `investigations`. Um item novo é acrescentado por `id`; um item com ID existente substitui o objeto inteiro. Por isso, uma correção deve carregar todos os campos necessários e incluir a nota de correção. Não publicar objetos parciais.

Cada ficha usa, no mínimo:

```json
{
  "id": "pessoa-assunto-ano",
  "person": "jair",
  "title": "Título factual e conciso",
  "claim": "Síntese atribuída da declaração",
  "summary": "O que a documentação permite concluir",
  "context": "Ocasião, alcance e ressalvas",
  "topic": "Política",
  "verdict": "Sem comprovação",
  "year": 2026,
  "statementDate": "AAAA-MM-DD",
  "dateLabel": "Data conferida da declaração",
  "datePrecision": "day",
  "sortDate": "AAAA-MM-DD",
  "reviewedAt": "AAAA-MM-DD",
  "sources": [
    {
      "title": "Título da fonte consultada",
      "publisher": "Publicador identificado",
      "url": "https://endereco-real-conferido",
      "date": "AAAA-MM-DD",
      "type": "primary"
    }
  ],
  "relatedMedia": []
}
```

O exemplo é apenas um esquema, não um registro publicável. Datas e URLs ilustrativas nunca devem entrar no acervo. `person` aceita `jair` ou `flavio`; os vereditos são `Falso`, `Enganoso` e `Sem comprovação`. Ver critérios antes de escolher. Para os outros tipos, seguir objetos completos já existentes no conteúdo canônico.

Mídias precisam de título, tipo, publicador, data, crédito, fonte e URL válida. Para YouTube, registrar somente o ID realmente encontrado. Áudios devem ter origem e direitos identificados; nunca gerar ou imitar vozes. Transcrição integral só quando autorizada ou disponibilizada pelo publicador. Resumos devem ser breves e em redação própria.

## Gravação sem sessão de navegador

O conector GitHub permite ler os arquivos e criar uma revisão no repositório público autorizado. Não é necessário ter o site aberto.

1. Ler novamente o head de `main` e a revisão atual dos arquivos antes de gravar.
2. Integrar os itens conferidos ao complemento atual por ID. Preservar todos os demais itens. Atualizar `updatedAt` somente quando o conteúdo editorial mudar.
3. Gravar, na mesma revisão, `content/editorial-updates.json`, `dist/data/editorial-updates.json` e `dist/data/editorial-updates.js`. O JS contém apenas `window.ARQUIVO_UPDATES = ` seguido do JSON serializado e `;`. Escapar `</` como `<\/` na serialização do JS. Não inserir código de terceiros.
4. Usar commit com mensagem objetiva. Nas APIs Git Data, criar a árvore a partir da árvore atual, o commit com o head atual como pai e mover `main` sem force, com a verificação `expected_sha`. Se houver conflito, reler e integrar a mudança concorrente; não sobrescrevê-la.
5. Ler o JSON publicado no commit retornado e conferir IDs, contagens, fontes e `updatedAt`. Somente depois da leitura considerar a publicação concluída. Guardar o SHA no relato da execução, sem credenciais.
6. O cliente verifica esses dados ao abrir e a cada 20 minutos enquanto visível. Se o GitHub estiver indisponível, mantém o conteúdo já carregado e a edição incluída no site.

O workflow de notícias mantém seus próprios arquivos. A pesquisa editorial não deve sobrescrever uma coleta mais recente. A rotina pode registrar falha de fontes, mas nunca fabricar horário de consulta bem-sucedida. Não marcar `scheduleVerified` manualmente para sugerir que uma coleta ocorreu.

## Revisões completas e PDF

O PDF é uma edição fechada. Novos itens do complemento aparecem primeiro no site e nas exportações da página. Para consolidar uma edição: integrar o complemento ao JSON canônico, conferir as fichas, executar `python scripts/sync_content.py`, instalar `requirements.txt`, restaurar anexos com `python scripts/fetch_assets.py` e executar `python scripts/build_pdf.py`. Conferir visualmente a paginação antes de publicar o PDF. Não anunciar PDF atualizado sem regerá-lo.

## Relato e falhas

Comunicar ao proprietário apenas acréscimos relevantes, correções ou impedimentos que exijam ação. Informar o que mudou e as fontes correspondentes. Se nada verificável mudar, não inventar atualização nem enviar um relatório repetitivo. Não prometer monitoramento segundo a segundo, acesso integral a todos os arquivos ou disponibilidade contínua dos publicadores.

Se a busca, o conector ou uma origem estiver indisponível, preservar o acervo e informar a limitação concreta. Repetir somente quando houver fundamento para uma nova tentativa; não contornar autenticação, paywall ou bloqueio de segurança.
