# Verificação da edição 02

Revisão em 24/10/2026. A conferência cobre o conteúdo e a implementação entregues nesta edição.

## Acervo e fontes

- 71 fichas: 45 de Jair e 26 de Flávio. Classificações: 44 Falso, 24 Enganoso e 3 Sem comprovação.
- 5 comparações, 1 apuração documental, 43 registros de mídia e 12 documentos de referência.
- 120 URLs únicas nas fontes das fichas, comparações e apuração. Isso não equivale a 120 checagens independentes.
- Os lotes novos de Jair e Flávio foram revisados de forma cruzada. Ajustados o estudo sobre quarta dose, o contexto de autorizações emergenciais, a admissão parcial dos insultos ao STF e a resposta sobre a cota da aeronave.
- A comparação da Petrobras permanece como mudança de posição. O dossiê Vorcaro distingue reportagens, reconhecimento de contatos, autorização judicial, respostas e limites.
- Validação de IDs, campos essenciais, fontes, classificações e referências de arquivos pelo sincronizador.

## Interface

- HTML, CSS e JavaScript sem framework. Sintaxe JavaScript conferida com Node.
- Inspeção em desktop e em contêineres de 390 e 768 pixels no Chrome. A largura útil de celular foi de 375 pixels e a página não apresentou transbordamento horizontal.
- Testados filtro Flávio com 26 resultados, busca, resultado vazio, limpeza dos filtros, linha do tempo, menu móvel, tema escuro e abertura de fichas.
- Modal do YouTube carregou com título, canal, player e links de origem. A reprodução integral dos vídeos externos não foi comprovada neste ambiente.
- Os players são carregados sob demanda. Áudios da grade usam preload none. A interface mantém dados incluídos e cache anterior quando o acesso remoto falha.
- A inspeção responsiva não substitui uma homologação em aparelhos físicos ou Safari.

## Coletor e integridade

- Seis testes do coletor aprovados: RSS, Atom, atribuição explícita, HTTPS sem credenciais, remoção de rastreadores, rejeição de entidades XML e preservação de itens em falhas.
- A consulta de preparação obteve resposta legível das oito fontes habilitadas e reuniu 30 links relacionados.
- O coletor publica apenas metadados. Não transforma automaticamente notícias em vereditos.
- O manifesto de sete anexos grandes contém SHA-256 e URLs de origem. A conferência local de integridade passou.
- A validação de uma coleta de preparação não comprova a execução futura de um agendamento. O histórico do GitHub e o painel indicam as execuções reais.

## Mídias

- Foram acrescentados 26 vídeos e dez áudios. IDs, títulos e canais dos vídeos foram conferidos por oEmbed e páginas dos publicadores.
- Os dez MP3 novos responderam HTTP 200 e tiveram formato e duração conferidos com ffprobe. Cinco publicações oferecem transcrição integral na fonte.
- A base contém 31 vídeos e 12 áudios. Gravações originais, entrevistas, reportagens e materiais de contexto têm funções distintas e são identificados no cadastro.
- Reprodução e disponibilidade de conteúdos externos dependem dos respectivos publicadores. O site fornece links alternativos para as páginas de origem.

## PDF

- 113 páginas, 2.905.697 bytes na versão revisada.
- 353 links externos, 222 destinos externos únicos e 502 links totais, incluindo navegação interna.
- As 113 páginas foram renderizadas e inspecionadas em contato; 12 páginas representativas foram ampliadas.
- Nenhum texto fora da página. Corrigido o espaçamento de materiais associados.
- A extração confirma os campos das 71 fichas e as 120 referências únicas das fichas, comparações e apuração.
- O PDF é uma edição fechada. Atualizações posteriores do site não alteram automaticamente suas páginas.

## Alcance e limites

O acervo é selecionado e cresce com as atualizações. Não há garantia de totalidade, reprodução integral de todos os vídeos ou disponibilidade contínua das fontes. A classificação de uma afirmação não demonstra intenção de enganar. O código estático evita processamento por visitante no servidor de aplicação, mas não foi realizado ensaio de carga para certificar um número de acessos simultâneos.
