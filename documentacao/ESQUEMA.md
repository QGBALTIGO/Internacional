# Modelo do catálogo de pesquisa

O catálogo em `content/research.json` é separado de `content/acervo.editorial.json`. O primeiro conserva caminhos de pesquisa, metadados e leituras com limitações. O segundo preserva as checagens da edição anterior. Catalogar um material não conclui sua verificação.

`python3 scripts/build_research.py` normaliza checkpoints de `content/research-input/` e escreve JSON para edição, JSON para exportação e `window.ARQUIVO_RESEARCH` para carregamento estático. `--import-dir` copia checkpoints de uma rodada para a pasta de origem. Os dados brutos são preservados; resumos e URLs não são executados como código.

## Entidades

| Entidade | Identidade e função |
| --- | --- |
| `sources` | Instituição ou publicador. Tem ID, URL, responsável declarado, natureza, método, acesso e periodicidade quando existe feed efetivamente coletado. Consulta de pesquisa e coleta recorrente têm horários separados. |
| `items` | Material pelo URL canônico, sem parâmetros de rastreamento. Uma página pode abrigar várias afirmações. A quantidade de materiais não é quantidade de falsidades nem de confirmações independentes. |
| `events` | Contexto e data do evento, quando fornecida. A data da publicação permanece no material; uma data desconhecida é `null`. |
| `statements` | Afirmações da edição anterior, com origem e estado de revisão herdados explicitamente. Não são apresentadas como reexaminadas pelo novo lote. |
| `propositions` | Perguntas factuais candidatas, ainda sem formulação normalizada de afirmação, classificação ou vínculo principal. Não contam como novas declarações confirmadas. |
| `occurrences` | Ocasiões de uma proposição principal. A lista permanece vazia até confirmar autoria, formulação e vínculo; não se inventa ocorrência a partir de uma notícia sobre o mesmo tema. |
| `evidence` | Referência ao material e seu localizador. `supports` e `weakens` permanecem vazios enquanto não há julgamento sobre uma proposição delimitada. |
| `reviews` | Revisões editoriais identificadas. Nenhuma nova revisão humana é inferida da leitura automatizada. |
| `history` | Alterações editoriais materiais. Nenhum caso de correção é inventado para preencher a coleção. |
| `repetitionGroups` | Candidatos a repetição ou núcleos de pesquisa. Um grupo sobre financiamento ou empresas não equivale automaticamente a uma proposição única. |
| `queries` | Consulta executada, frente, referência temporal e resultado/limitação. Não é um índice exaustivo da internet. |
| `coverage` | Matriz anual 2003 a 2026 com temas, formatos, fontes e níveis reais de trabalho. Lacuna não demonstra inexistência. |

## Contrato de cada material

`id`, `title`, `url`, `publisher`, `date`, `eventDate`, `year`, `datePrecision`, `format`, `topic`, `topics`, `stage`, `summary`, `limitations`, `locator`, `sourceId`, `review`, `statementId`, `statementCandidateId`, `transcript`, `durationSeconds`, `collectedAt`, `lastModifiedAt`, `editorialClassification`, `sourceConclusion`, `factualQuestion`, `publicResponse`, `actor`, `literalQuote`, `documentNumber`, `legacyRecordIds`, `researchOrigins`, `accessMethod`, `newToArchive`.

Formatos permitidos: `documento`, `video`, `audio`, `checagem`, `reportagem`, `registro`. Os níveis `encontrado`, `acessado` e `analisado` são estados do trabalho de pesquisa, não vereditos. `analisado` significa texto efetivamente lido e resumido. Metadados audiovisuais ficam em `acessado`; não provam reprodução.

`revisado` e `publicado` são reservados a etapas futuras com revisão identificada. Este gerador nunca promove materiais a esses níveis, não cria revisor, não publica nova acusação nem atribui classificação própria. A propriedade `publicationState` deixa explícito que a página publica apenas o catálogo do material.

Campos desconhecidos ficam `null`. Datas parciais preservam apenas o ano ou mês disponível. Horários de sistema são UTC, com apresentação em `America/Campo_Grande`. Hora e fuso originais só entram quando informados pela fonte. `generatedAt` é a data do checkpoint do conjunto de inputs e não funciona como selo de revisão. Rodar novamente sem mudar inputs preserva esse checkpoint.

## Mídia e direitos

`media` é uma projeção para os players, com IDs conferidos na origem e o aviso de que o áudio ainda não foi ouvido. URLs de publicadores e IDs de plataforma são campos diferentes. Um ID localizado não certifica reprodução, duração ou autenticidade. `mediaCataloguedSeconds` soma somente durações conhecidas, algumas arredondadas pelos distribuidores; `reviewedAudioSeconds` permanece zero neste lote.

Transcrições oficiais consultadas são identificadas em `transcript.method`; `transcript.text` continua nulo quando a íntegra não foi autorizada para reprodução. Citações oficiais curtas podem aparecer em `literalQuote` ou `transcript.excerpt`, com localizador. Não se anuncia transcrição própria ou áudio conferido.

## Deduplicação e retomada

A URL canônica é a identidade de material. Reaberturas e achados de frentes diferentes são fundidos com todas as `researchOrigins`. Referências já presentes na edição anterior recebem `legacyRecordIds` e não entram no contador de materiais novos. Isso não substitui deduplicação semântica de afirmações nem autenticação de uma gravação.

O hash de inputs permite detectar alteração de checkpoint. Ele comprova correspondência de dados e não veracidade. Testes técnicos usam domínios e títulos sintéticos, em memória, sem serem importados na produção.

O gerador preserva `history` da saída anterior. Quando existir `content/research-history.json`, lê essa fonte explícita como array ou objeto contendo `history`. Acrescentar histórico real exige texto e motivo próprios; a simples execução do gerador não inventa uma correção.
