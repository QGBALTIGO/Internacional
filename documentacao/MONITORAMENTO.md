# Coleta recorrente e fila persistente

O coletor descobre metadados de RSS e Atom. Um item descoberto não é um artigo examinado, uma declaração transcrita, uma checagem revisada ou uma acusação validada. O código não escreve vereditos e não altera fichas editoriais.

## Situação verificável

A execução anterior à ampliação foi confirmada pelo proprietário da integração em 23/10/2026, no fuso America/Campo_Grande: [GitHub Actions 40058865498](https://github.com/QGBALTIGO/Internacional/actions/runs/40058865498), evento `push`, iniciada às 03:34:33 UTC de 24/10/2026 e concluída com sucesso. Os dados dessa execução informam seis fontes acessíveis de oito consultadas, às 03:34:39 UTC. Isso comprova uma execução acionada por alteração de código. Não comprova, isoladamente, a execução do agendamento horário anterior.

A versão atual precisa de uma nova execução no GitHub para comprovar operação da fila modificada. A configuração de cron não é apresentada como comprovação de coleta. O metadado legado `scheduleVerified` permanece falso; as execuções novas incluem identificador, evento e URL do provedor quando esses dados estão disponíveis. O início registrado pelo worker deve ser confrontado com a conclusão mostrada pelo GitHub.

## Agendamento e persistência

O workflow `atualizar-fontes.yml` verifica a fila quatro vezes por hora, nos minutos 7, 22, 37 e 52 UTC. Cada fonte conserva seu próprio `nextAttemptAt`. O intervalo de sucesso vem de `intervalMinutes` da fonte ou do arquivo de configuração, atualmente 60 minutos por padrão. Execuções do GitHub podem atrasar ou ser suspensas pelo provedor. Esses intervalos são configuração, sem garantia de horário.

O estado durável é `.monitor/state.json`, versionado pelo próprio workflow junto aos resultados. Não contém segredos, arquivos de áudio, textos integrais de reportagens ou dados de visitantes. É público porque pertence a um repositório público. As gravações são atômicas e a concorrência do workflow mantém um único escritor da fila. Operadores locais devem também executar uma instância por vez.

Antes de iniciar a rede, os jobs devidos recebem estado `running` e são gravados. Após cada resposta, o ledger de URLs e a conclusão do job são gravados juntos. Um reinício retoma jobs que ficaram `running`; URLs já conhecidas mantêm o ID e a primeira data de coleta. O estado conserva URLs e metadados históricos sem a janela móvel do painel. A persistência é limitada pelo armazenamento do repositório: acompanhar seu crescimento antes de migrar para um banco; não há descarte silencioso do ledger histórico.

O painel público tem somente os últimos 180 dias e, no máximo, 500 notícias. A saída JS e JSON conserva `schemaVersion: 1`. Uma notícia repetida em fontes diferentes tem uma URL canônica, `sourceIds` no ledger e uma entrada na lista. Textos iguais com URLs diferentes continuam candidatos distintos à triagem. Similaridade de títulos não comprova identidade de alegações ou independência editorial; essa deduplicação exige análise.

## Falhas, quotas e limites

Há até quatro consultas concorrentes e apenas uma requisição por host de cada vez. A leitura de cada feed limita-se a 3 MB, 300 entradas e 18 segundos por requisição. XML com entidades ou DTD é rejeitado. O parser aceita RSS, Atom, RDF com namespaces, datas em `dc:date` e links em `guid` permanente.

Cada fonte mantém tentativa, sucesso, erro, estado e próxima tentativa separados. Uma falha conserva a última coleta bem-sucedida e os materiais conhecidos. As novas tentativas usam espera agendada de 15, 30, 60, 120, 240 e até 480 minutos, sem manter um processo dormindo. `Retry-After` numérico ou em data é respeitado, limitado a 24 horas. Uma falha inesperada de um worker não cancela os demais. Falha de todas as fontes consultadas produz saída de erro após salvar o diagnóstico. Uma execução sem jobs devidos termina normalmente.

O worker consulta apenas os hosts públicos auditados e declarados em `ALLOWED_FETCH_HOSTS`. A validação é repetida em redirecionamentos. HTTPS, porta padrão, ausência de credenciais na URL e endereços de DNS públicos são obrigatórios. URLs de notícias não são abertas automaticamente pelo coletor. Não há endpoint público para visitantes enviarem URLs. Uma mudança de domínio legítima exige revisão do mapa e do código; não se contornam autenticação, paywalls ou CAPTCHA.

O foco padrão de novas coletas é a referência explícita a Flávio Bolsonaro nos metadados. Referências a Jair somente entram nessa descoberta quando o contexto também contém Flávio, salvo uma configuração explícita de foco mais amplo. O título ou a descrição de um feed não prova autoria pessoal de uma declaração.

## Estados e balanços

- `waiting`: fonte coletada; aguardando seu próximo intervalo.
- `running`: tentativa iniciada e checkpoint persistido.
- `retry`: falha registrada; nova tentativa programada.
- `editorialState: coletado`: metadados aguardam análise; não contam como checagem concluída.

O balanço diário usa datas UTC e conta materiais novos por URL, consultas bem-sucedidas e falhas. Os campos de revisão e correção editorial não são incrementados pelo coletor. A fila não transcreve vídeos, não mede horas de mídia revisada, não envia alertas a terceiros e não publica acusações.

## Operação e recuperação

```bash
python3 -m unittest discover -s tests -v
python3 scripts/update_news.py
python3 scripts/update_news.py --force
```

`--force` consulta as fontes agora sem apagar o ledger, útil para diagnóstico. Para testes técnicos ou ensaios, use `--state` e `--output` apontando para um diretório temporário separado da produção. Nunca coloque fixtures sintéticas em `content/` ou `dist/`.

Se o checkpoint estiver corrompido, o worker falha sem sobrescrevê-lo. Recupere uma revisão conhecida de `.monitor/state.json`, confira sua integridade e retome a coleta. O histórico Git permite recuperar dados e a edição pública anterior. O estado e os metadados de fonte são independentes da revisão editorial de fichas.

Nenhuma API paga foi habilitada e o coletor não usa modelos ou serviços de transcrição. A operação depende dos limites e da disponibilidade existentes do GitHub e das fontes. Não há orçamento de custo zero garantido nem preço inventado de infraestrutura.

## Validação técnica desta alteração

Passaram 15 testes com fixtures sintéticas fora da produção: metadados sem vereditos, atribuição de pessoas, rejeição de entidades XML, RSS/Atom/RDF, `guid`, canonicalização, preservação de resultados após falha, retomada de job interrompido, deduplicação entre fontes, execução repetida sem nova URL, janela pública separada do ledger, backoff e quota, falha isolada e destinos internos/redirecionamentos rejeitados. Esses testes demonstram comportamento do código. O êxito da implantação e a consulta real das fontes precisam de comprovação própria no provedor.
