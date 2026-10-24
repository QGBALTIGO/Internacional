# Arquivo Bolsonaro | Flávio, declarações e documentos

Site com acesso restrito ao proprietário: https://arquivo-bolsonaro-fatos.copperkoala32.chatgpt.site

Repositório: https://github.com/QGBALTIGO/Internacional

Edição 03 de pesquisa. Datas de sistema em UTC; apresentação em America/Campo_Grande. O foco atual é Flávio Bolsonaro. O acervo anterior de Jair permanece disponível na seção identificada e não integra as contagens de novas checagens de Flávio.

## Catálogo e apresentação

Na consolidação inicial desta apresentação, o catálogo passou a **153 materiais únicos**: 138 ainda não vinculados à edição anterior e 15 relacionados a ela. O lote inclui 70 documentos, 13 vídeos e 5 áudios. Há 150 materiais acessados, 124 textos examinados, 27 fontes mapeadas, 77 consultas e 14 falhas de acesso registradas. As durações são nominais: nenhum segundo foi ouvido nesta consolidação.

Foram integrados os 56 materiais que estavam somente em checkpoints. Lotes posteriores são preservados pelo gerador; consulte a contagem atual em content/research.json e documentacao/COBERTURA.md. As 71 fichas anteriores, 26 de Flávio e 45 de Jair, permanecem intactas. A midiateca combina registros históricos e de pesquisa e elimina reproduções da mesma URL/ID na apresentação, sem apagar seus metadados.

A interface agora tem navegação lateral, atalhos no celular, busca geral e telas próprias para catálogo, fichas, mídias e fontes. A busca não converte uma notícia em veredito. Os novos materiais continuam aguardando revisão editorial identificada.

O endereço chatgpt.site depende de republicação do layout; alterações no GitHub atualizam seus dados, não o HTML/CSS hospedado. A rotina existente do GitHub Pages publica o diretório do repositório. Nenhuma permissão ou audiência foi alterada.

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
python3 scripts/sync_content.py --allow-remote-assets
python3 scripts/check_site.py
python3 -m unittest discover -s tests -v
node --check dist/assets/app.js
node --check dist/assets/research.js
node --check dist/assets/portal.js
node tests/frontend.mjs
```

`python3 scripts/benchmark_static.py` usa loopback com 100 tarefas HTTP simultâneas e uma fixture separada de 1.000 metadados. A fixture nunca integra o catálogo de produção. O teste não homologa CDN, reprodução audiovisual ou Safari.

Para coleta manual: `python3 scripts/update_news.py --force`. O script mantém sucessos e itens anteriores diante de falhas, não contorna bloqueios e não atribui falsidade a notícias.

## Operação, limites e continuidade

Leia `documentacao/RELATORIO-EDICAO-03.md`, `MONITORAMENTO.md`, `COBERTURA.md`, `ESQUEMA.md` e `ATUALIZACAO.md`. O balanço final de implantação identifica a execução real do runner. Configurar uma agenda não prova que ela executou.

A nova automação de pesquisa deve acrescentar materiais e pendências. Novas conclusões sensíveis exigem um revisor autorizado registrado em `metadata.approvedReviewerIds` e um objeto `review` aprovado. A lista começa vazia; nenhuma concordância entre modelos autoriza sua inclusão. O conteúdo catalogado permanece pesquisável enquanto aguarda revisão.

A homologação visual da edição 03 ficou limitada pelo bloqueio de acesso da prévia no navegador do ambiente. Os testes de lógica usam DOM simulado e os testes de transporte usam HTTP local. Não há declaração de homologação em Safari físico.

## Consolidação automática e anexos

O workflow `catalogo.yml` reconstrói `research.json` quando os checkpoints mudam, executa testes e publica apenas os derivados. A validação impede apagar materiais, criar revisores ou aprovar novos vereditos. Os arquivos do coletor não são incluídos no commit.

Sem `--allow-remote-assets`, o sincronizador continua exigindo todos os bytes locais. Com a opção explícita, ele aceita apenas anexos ausentes cujo caminho, URL HTTPS e SHA-256 constam no manifesto, e os relata como referências remotas não conferidas. Isso não comprova disponibilidade, integridade dos bytes remotos nem reprodução audiovisual.

O PDF histórico não é recriado automaticamente nem apresentado como download local disponível. O botão de contexto aponta para a documentação da edição. Os links originais dos documentos continuam nas fichas.

A verificação local da interface está em `documentacao/interface-qa.json`: Chromium com arquivos do checkout, cinco larguras e rede externa desativada. Não é uma certificação de Safari físico, disponibilidade das fontes ou do site publicado.
