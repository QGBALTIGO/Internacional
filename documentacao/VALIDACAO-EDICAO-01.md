# Verificação da edição 01

Revisão em 23/10/2026 (America/Campo_Grande).

## Conteúdo

- 25 fichas com autoria atribuída pelas fontes, contexto e classificação delimitada.
- 49 URLs únicas nas referências das fichas. Nem todo link é uma verificação independente: há documentos da própria fala, dados institucionais e checagens jornalísticas.
- Revisão cruzada dos casos de gripezinha, máscaras, reunião com embaixadores, enchentes, falências, Smartmatic, Paraguai e debate de 2026.
- Datas desconhecidas no dia exato mantidas como mês/período. Retificações posteriores preservadas.
- Fontes acessadas na pesquisa. Alguns extratores não obtiveram texto de páginas antigas do TSE/TRE; as fichas mantêm fontes complementares acessíveis. Não se garante disponibilidade futura de páginas externas.

## Funcionamento da página

- Verificação sintática de `app.js` e `acervo.js` com Node.
- Validação dos IDs, referências de mídia, campos essenciais, datas e existência dos arquivos locais.
- Busca sem acentos testada com “mascaras”; filtragem combinada Flávio + 2026 retornou quatro fichas.
- Testados abertura/fechamento de ficha, favorito, filtro de salvos, resultado vazio e limpeza de filtros.
- Testada alternância para linha do tempo.
- Exportação CSV acionada pela interface e arquivo reaberto: 25 fichas e 11 colunas.
- Inspeção visual em desktop e em contêineres de celular/tablet. Larguras úteis de 375 e 753 pixels não apresentaram transbordamento horizontal do documento. O modal móvel também permaneceu dentro da largura disponível.
- A conferência responsiva foi feita no Chrome do ambiente de teste, por iframes de 390 e 768 pixels; não é uma execução em aparelhos físicos nem uma homologação do Safari.

## Mídias

- MP3 e MP4 locais tiveram formato e duração conferidos por `ffprobe`.
- Vídeo local NASA reproduzido: `readyState=4`, tempo avançando, duração de 27,77 segundos.
- Ambos os MP3 reproduzidos: 126,57 e 203,69 segundos. Ao iniciar o segundo, o primeiro foi pausado.
- IDs, autoria e incorporação dos quatro vídeos externos foram confirmados por oEmbed ou páginas dos publicadores. As interfaces de dois players YouTube carregaram no navegador.
- A reprodução integral dos vídeos externos não foi comprovada: o player do Poder360 iniciou a tentativa, mas permaneceu sem avanço no navegador remoto. O site oferece links alternativos ao publicador e ao YouTube. Disponibilidade e reprodução dependem do provedor externo.
- O trecho do Poder360 é uma gravação da declaração. Materiais da TV/Rádio Senado são identificados como reportagens, explicações ou depoimentos de contexto. A NASA é identificada como evidência científica.

## PDF

- 34 páginas, uma ficha por página, índices internos navegáveis e 100 links externos clicáveis.
- Texto extraído para conferir títulos, datas e notas de correção.
- Capa, metodologia e páginas representativas renderizadas e inspecionadas visualmente.
- Revisão específica das páginas 10 (gripezinha), 17 (militares), 27 (Smartmatic) e 28 (Paraguai), sem cortes ou sobreposições observados.
- Dois PDFs oficiais locais tiveram assinatura de formato e paginação conferidas: TCU (44 páginas) e voto do relator no TSE (457 páginas).

## Pacote portátil

- Contém o site, os dados, a documentação, arquivos de mídia locais e PDFs permitidos.
- Não contém credenciais, identidade do projeto hospedado, histórico Git ou capturas internas de QA.
- A opção de baixar o próprio pacote fica oculta na cópia portátil, evitando um link recursivo ausente.
- Inclui manifesto de tamanhos e SHA-256 dos arquivos para verificação de integridade.

## Limites

É uma edição estática e selecionada. Não há monitoramento automático, coleta de denúncias, verificação em tempo real ou garantia de exaustividade. Uma classificação documentada não prova intenção de enganar. O uso ou redistribuição de materiais de terceiros deve conservar os créditos e observar suas respectivas licenças.
