# Referências visuais e arquitetura editorial

Revisão de direção visual: 24 de outubro de 2026. Escopo restrito à apresentação do Arquivo Bolsonaro. Não altera conteúdo editorial, classificações, revisores ou coleta.

## Resultado da análise

O projeto não deve reproduzir uma interface de SaaS, um painel de monitoramento operacional ou uma peça de campanha. A referência é um **arquivo de jornalismo documental**, pesquisável, sóbrio, com procedência visível. Uma fonte não se torna prova conclusiva apenas por constar do índice.

| Referência | URL consultável | Elemento aproveitado | O que não foi copiado |
| --- | --- | --- | --- |
| ProPublica | https://www.propublica.org/ | Hierarquia editorial, tipografia legível, concentração da atenção nos títulos e assuntos | Marca, imagens, textos e identidade gráfica |
| ICIJ, Panama Papers | https://www.icij.org/investigations/panama-papers/ | Organização de investigações em coleções, material de apoio e contextualização | Sensacionalismo visual, chamadas acusatórias e logos |
| National Security Archive, Briefing Books | https://nsarchive.gwu.edu/postings/briefing-books | Fichas documentais com data, descrição, documentos relacionados e contexto | Linguagem e classificações de documentos específicos |
| DocumentCloud (referência visual) | https://www.documentcloud.org/ | Busca clara e separação entre índice e leitura de documento | Recursos de upload, anotação ou processamento não implementados |
| MuckRock, busca de projetos públicos | https://www.muckrock.com/news/archives/2024/aug/06/documentcloud-project-search/ | Campos de busca objetivos e resultados escaneáveis | Marca e qualquer alegação de indexação de documentos externos |
| Aos Fatos, metodologia | https://www.aosfatos.org/webstories/como-o-aos-fatos-faz-uma-checagem/ | Transparência sobre a origem e o processo editorial antes da classificação | Selos e vereditos atribuídos a terceiros |
| Chequeado | https://chequeado.com/ | Distinção entre publicações factuais, checagens e conteúdos explicativos | Taxonomia própria de checagem |
| Agência Pública | https://apublica.org/ | Tom editorial brasileiro, identificação de materiais e assuntos | Projeto gráfico, fotografias e textos |
| OCCRP Aleph Pro | https://aleph.occrp.org/ | Importância de busca, organização e origem dos registros | Integração com bases restritas e recursos pagos |
| Full Fact | https://fullfact.org/ | Distinguir alegação e avaliação acompanhada de contexto | Modelos de revisão, fluxos e selos não aplicáveis ao projeto |

O DocumentCloud bloqueou uma leitura direta via ferramenta pública consultada (HTTP 403). A avaliação foi limitada aos exemplos públicos e documentação do MuckRock. Não se afirma acesso ao seu ambiente privado.

## Decisão de organização

1. Cabeçalho compacto com nome do arquivo, busca, tema e menu no celular.
2. Navegação horizontal por tipo de material, não uma barra lateral de administração.
3. Abertura breve sobre Flávio Bolsonaro com fotografia institucional já creditada.
4. Campo de pesquisa bem visível, seguido dos números reais carregados do catálogo.
5. Coleções organizadas por finalidade, depois materiais recentes, mídia e arquivo anterior.
6. Áreas detalhadas separadas: catálogo em pesquisa, fichas da edição anterior, dossiês, comparações, documentos, notícias, fontes, cobertura, correções e metodologia.
7. Todas as fichas mantêm indicação de origem, limitações e estado editorial; não se criam classificações automáticas.

## Sistema visual

- Base: papel claro, superfície branca, texto carvão e acento vinho discreto, sem cores de campanhas partidárias.
- Tipografia: Manrope local em navegação e corpo; Georgia do sistema em títulos editoriais. Não são adicionadas fontes de terceiros.
- Grade: largura máxima 1.200px, margens consistentes e respiro vertical controlado.
- Na capa, fotografia institucional ao lado do texto no desktop e abaixo do texto no celular, nunca como fundo que prejudique a leitura.
- Cartões sem sombras exageradas e com títulos de tamanho coerente; status de revisão discreto.
- Temas claro e escuro preservados; contornos de foco visíveis; sem animações essenciais.
- Acessibilidade: navegação por teclado, labels, controles clicáveis, regiões e fontes explícitas.

## QA exigido

- Abrir e navegar por todas as seções em 320, 390, 768, 1024 e 1440px.
- Conferir busca, filtros, abertura/fechamento de ficha, rota por hash, player, links externos e tema.
- Confirmar ausência de sobreposição, overflow horizontal, clique inerte, corte de título e botões escondidos.
- Verificar JSON persistido, ausência de alteração no acervo e dados do coletor, e status de publicação.
- Testes por DOM simulado não substituem inspeção visual em navegadores e iPhone/Safari real.

## Escopo preservado

Sem novas acusações, comparações sensíveis, vereditos ou revisores. Nenhum arquivo de conteúdo canônico, estado do coletor, checkpoint de pesquisa ou serviço pago faz parte desta alteração.
