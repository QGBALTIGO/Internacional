# Arquivo Bolsonaro | Flávio, declarações e documentos

Site com acesso restrito ao proprietário: https://arquivo-bolsonaro-fatos.copperkoala32.chatgpt.site

Repositório: https://github.com/QGBALTIGO/Internacional

Edição 03 de pesquisa. Datas de sistema em UTC; apresentação em America/Campo_Grande. O foco atual é Flávio Bolsonaro. O acervo anterior de Jair permanece disponível na seção identificada e não integra as contagens de novas checagens de Flávio.

## O que foi acrescentado

O catálogo contém 82 materiais únicos, sendo 69 novos e 13 relacionados à base anterior. Foram acessados 79 materiais e examinados 53 textos. Há 18 mídias no lote, 18 documentos, 26 fontes/canais cadastrados, 22 consultados, 45 consultas de pesquisa e 9 falhas registradas. As durações nominais conhecidas somam 4h41min55s; nenhum segundo de áudio foi ouvido nesta execução.

Os materiais novos aguardam revisão editorial identificada. Não foram acrescentados vereditos, acusações ou comparações conclusivas. As 71 fichas anteriores, 26 de Flávio e 45 de Jair, foram preservadas com IDs e fontes. As contagens de links não são contagens de afirmações falsas.

## Consultar

A página oferece busca de falas, catálogo com período/tema/formato/fonte/etapa/classificação, linha do tempo, biblioteca audiovisual, comparações anteriores, frente Vorcaro, notícias coletadas, documentos, matriz de cobertura, mapa de fontes, metodologia e histórico. Players externos são carregados sob demanda, com link ao publicador. O PDF está rotulado como edição histórica 01 e não representa o catálogo atual.

Novos materiais de `dist/data/research.json`, notícias e complementos são consultados no GitHub ao abrir a página e a cada 20 minutos enquanto visível. Dados incluídos na versão hospedada continuam disponíveis quando a consulta remota falha. O desenho do site só muda após nova publicação.

## Dados e rotinas

| Arquivo | Função |
| --- | --- |
| `content/acervo.editorial.json` | Fichas e documentos da base anterior, com metadados da edição atual |
| `content/research-input/` | Checkpoints de pesquisa, consultas, acessos e limitações |
| `content/research.json` | Entidades normalizadas, materiais, fontes, cobertura e candidatos |
| `content/research-history.json` | Alterações reais de apresentação e estado editorial |
| `content/sources.json` | Feeds autorizados e intervalos |
| `.monitor/state.json` | Checkpoint persistente de coletas, fila e ledger histórico criado pelo runner |
| `scripts/build_research.py` | Normalização e deduplicação, sem publicar conclusões sensíveis |
| `scripts/update_news.py` | Coleta permitida, retentativas e diagnóstico por fonte |
| `.github/workflows/atualizar-fontes.yml` | Acorda a fila a cada 15 minutos, respeitando o intervalo de cada fonte |

O site é estático. Busca e filtros ocorrem no navegador. Uma visita não executa coleta, transcrição ou modelos. A edição depende das permissões de escrita do GitHub; não há formulário público de ingestão ou painel editorial com credenciais no cliente.

## Verificar e reconstruir

```bash
python3 scripts/build_research.py
python3 scripts/sync_content.py
python3 scripts/check_site.py
python3 -m unittest discover -s tests -v
node --check dist/assets/app.js
node --check dist/assets/research.js
node tests/frontend.mjs
```

`python3 scripts/benchmark_static.py` usa loopback com 100 tarefas HTTP simultâneas e uma fixture separada de 1.000 metadados. A fixture nunca integra o catálogo de produção. O teste não homologa CDN, reprodução audiovisual ou Safari.

Para coleta manual: `python3 scripts/update_news.py --force`. O script mantém sucessos e itens anteriores diante de falhas, não contorna bloqueios e não atribui falsidade a notícias.

## Operação, limites e continuidade

Leia `documentacao/RELATORIO-EDICAO-03.md`, `MONITORAMENTO.md`, `COBERTURA.md`, `ESQUEMA.md` e `ATUALIZACAO.md`. O balanço final de implantação identifica a execução real do runner. Configurar uma agenda não prova que ela executou.

A nova automação de pesquisa deve acrescentar materiais e pendências. Novas conclusões sensíveis exigem um revisor autorizado registrado em `metadata.approvedReviewerIds` e um objeto `review` aprovado. A lista começa vazia; nenhuma concordância entre modelos autoriza sua inclusão. O conteúdo catalogado permanece pesquisável enquanto aguarda revisão.

A homologação visual da edição 03 ficou limitada pelo bloqueio de acesso da prévia no navegador do ambiente. Os testes de lógica usam DOM simulado e os testes de transporte usam HTTP local. Não há declaração de homologação em Safari físico.
