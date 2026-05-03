# Feature Specification: CRM Inteligente com Agentes de IA — Loja Infantil

**Feature Branch**: `001-crm-ia-loja-infantil`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: CRM Inteligente com Agentes de IA para uma loja infantil, com atendimento via WhatsApp, gestão de clientes, segmentação, agentes de crescimento e campanhas.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Atendimento Contextualizado via WhatsApp (Priority: P1)

Uma cliente entra em contato pelo WhatsApp perguntando sobre um produto. O sistema (Agent Nino) identifica a cliente pelo número de telefone, recupera o histórico de conversas anteriores e responde de forma personalizada, levando em conta o contexto das interações passadas. Ao final, a mensagem é classificada por sentimento e tema.

**Why this priority**: É o ponto de entrada principal do sistema e o canal de relacionamento mais crítico. Sem atendimento funcional, nenhuma outra funcionalidade tem valor para o negócio.

**Independent Test**: Pode ser testado independentemente enviando uma mensagem de WhatsApp para o sistema e verificando que a resposta é contextualizada com o histórico do cliente, e que a classificação de sentimento e tema é salva corretamente.

**Acceptance Scenarios**:

1. **Given** uma cliente já cadastrada envia uma mensagem via WhatsApp, **When** o Agent Nino processa a mensagem, **Then** o sistema recupera o histórico e gera uma resposta personalizada em menos de 30 segundos.
2. **Given** uma nova cliente entra em contato pelo WhatsApp, **When** a mensagem é recebida, **Then** o sistema cria um novo registro de cliente automaticamente e registra a primeira interação.
3. **Given** um operador deseja assumir uma conversa em andamento, **When** aciona o handoff no painel, **Then** o Agent Nino para de responder automaticamente e o operador assume o controle em tempo real.
4. **Given** uma mensagem é classificada como sentimento negativo, **When** a classificação é concluída, **Then** o resultado é persistido no histórico do cliente e um evento `cliente_insatisfeito` é gerado.

---

### User Story 2 — Gestão Centralizada de Clientes (Priority: P2)

A operadora acessa o CRM e consulta o perfil completo de uma cliente: data da primeira interação, última compra, histórico de conversas, sentimentos registrados e classificação atual. Todos os dados foram preenchidos automaticamente pelo sistema ao longo das interações.

**Why this priority**: É a espinha dorsal do CRM. Todos os outros agentes e funcionalidades dependem de dados de cliente bem estruturados e atualizados.

**Independent Test**: Pode ser testado verificando que, após uma interação via WhatsApp, o perfil do cliente é atualizado automaticamente com os dados corretos sem qualquer input manual.

**Acceptance Scenarios**:

1. **Given** uma interação via WhatsApp é concluída, **When** o sistema processa a conversa, **Then** os campos data de última interação, sentimento e tema são atualizados no perfil do cliente automaticamente.
2. **Given** um cliente realiza uma compra registrada no sistema, **When** a compra é confirmada, **Then** o campo data da última compra é atualizado e a classificação do cliente é recalculada.
3. **Given** um operador acessa o perfil de um cliente, **When** visualiza a timeline, **Then** vê todas as mensagens, sentimentos e compras em ordem cronológica.
4. **Given** um cliente não tem interação há mais de 30 dias, **When** o sistema avalia o perfil, **Then** a classificação muda para "inativo" automaticamente.

---

### User Story 3 — Segmentação Automática de Clientes (Priority: P3)

O sistema classifica automaticamente cada cliente em segmentos com base no comportamento registrado. A operadora filtra clientes inativos no painel para iniciar uma ação de reativação.

**Why this priority**: Segmentação é o que transforma dados brutos em inteligência de negócio acionável. Habilita Growth Agent e Ads Agent a atuarem com contexto correto.

**Independent Test**: Pode ser testado verificando que clientes com diferentes comportamentos (ex: sem compra há 35 dias) são automaticamente atribuídos ao segmento correto ("inativos") sem ação manual.

**Acceptance Scenarios**:

1. **Given** um cliente não realiza compra ou interação há mais de 30 dias, **When** o sistema recalcula segmentos, **Then** o cliente aparece no segmento "Clientes Inativos".
2. **Given** um cliente demonstra interesse recorrente sem realizar compra, **When** o sistema avalia o comportamento, **Then** o cliente é classificado como "Lead Quente".
3. **Given** uma operadora acessa o CRM e aplica filtro por segmento "Inativos", **When** a lista é carregada, **Then** apenas clientes classificados como inativos são exibidos.
4. **Given** um cliente realiza uma nova compra após estar inativo, **When** a compra é registrada, **Then** o cliente é automaticamente movido para o segmento "Clientes Ativos".

---

### User Story 4 — Ativação e Conversão via Growth Agent (Priority: P4)

O sistema detecta que uma cliente demonstrou alto interesse mas não finalizou uma compra. O Growth Agent recebe o evento `cliente_pronto_compra`, identifica a oportunidade e sugere um convite para o grupo VIP ou envio de uma oferta personalizada. A operadora revisa e aprova a ação antes do envio.

**Why this priority**: Converte comportamento passivo em ação comercial. Depende de Segmentação (P3) e CRM (P2) funcionais para operar com contexto.

**Independent Test**: Pode ser testado simulando o evento `cliente_pronto_compra` e verificando que o Growth Agent gera uma sugestão de ação que pode ser revisada e aprovada pela operadora antes de qualquer envio.

**Acceptance Scenarios**:

1. **Given** o evento `cliente_interessado` é gerado, **When** o Growth Agent processa o evento, **Then** uma sugestão de ação é criada e apresentada à operadora para aprovação.
2. **Given** a operadora aprova uma ação sugerida pelo Growth Agent, **When** a ação é executada, **Then** a mensagem é enviada ao cliente respeitando as regras da WhatsApp Business API.
3. **Given** um cliente está dentro da janela de 24h de conversa ativa, **When** o Growth Agent sugere envio de oferta, **Then** a mensagem é processada sem necessidade de template aprovado.
4. **Given** um cliente está fora da janela de 24h, **When** o Growth Agent sugere contato, **Then** o sistema utiliza apenas templates aprovados para o envio.

---

### User Story 5 — Criação e Aprovação de Campanhas via Ads Agent (Priority: P5)

A operadora solicita uma campanha para clientes inativos. O Ads Agent analisa o segmento, gera uma sugestão de copy, público-alvo e orçamento. A operadora revisa, edita o texto e aprova. Somente então a campanha é publicada.

**Why this priority**: Amplia o alcance de marketing de forma inteligente. Depende de Segmentação (P3) para definir audiências e de aprovação humana obrigatória por princípio constitucional.

**Independent Test**: Pode ser testado verificando que nenhuma campanha pode ser publicada sem o passo de aprovação humana, mesmo que o Ads Agent gere todos os campos corretamente.

**Acceptance Scenarios**:

1. **Given** a operadora solicita uma campanha para o segmento "Clientes Inativos", **When** o Ads Agent processa a solicitação, **Then** uma sugestão de copy, público e orçamento é apresentada para revisão.
2. **Given** a operadora edita o copy sugerido pelo Ads Agent, **When** confirma as alterações, **Then** as edições são salvas e o status da campanha permanece "aguardando aprovação".
3. **Given** uma campanha está aguardando aprovação, **When** a operadora aprova, **Then** a campanha é marcada como aprovada e encaminhada para publicação.
4. **Given** uma campanha foi gerada pelo Ads Agent, **When** nenhuma operadora aprova, **Then** a campanha permanece em rascunho e nenhum anúncio é publicado.

---

### User Story 6 — Painel Administrativo (CRM UI) (Priority: P6)

A operadora acessa o painel web, visualiza métricas gerais (clientes novos, ativos, inativos), filtra por segmento, abre o perfil de um cliente, vê a timeline completa e decide assumir a conversa manualmente.

**Why this priority**: Consolida a visibilidade operacional do sistema. Depende de dados de CRM (P2) e segmentação (P3) para ser útil.

**Independent Test**: Pode ser testado verificando que a interface carrega corretamente com dados reais de clientes e que as ações críticas (assumir conversa, aprovar campanha) requerem confirmação antes de executar.

**Acceptance Scenarios**:

1. **Given** a operadora acessa o painel principal, **When** a página carrega, **Then** métricas de clientes novos, ativos e inativos são exibidas com valores corretos.
2. **Given** a operadora aplica um filtro por segmento na lista de clientes, **When** o filtro é aplicado, **Then** apenas clientes daquele segmento são listados.
3. **Given** a operadora clica em "Assumir conversa", **When** o sistema solicita confirmação, **Then** após confirmar, o Agent Nino para de responder e o operador recebe o controle da conversa.
4. **Given** a operadora acessa o painel de campanhas, **When** visualiza uma campanha pendente, **Then** pode aprovar, editar ou rejeitar com no máximo 3 interações na interface.

---

### Edge Cases

- O que acontece se o cliente enviar mensagem enquanto o operador está no controle manual da conversa?
- Como o sistema lida com mensagens fora da janela de 24h do WhatsApp sem template disponível?
- Quando dois operadores tentam assumir a mesma conversa simultaneamente, o sistema bloqueia a conversa para o primeiro; os demais veem "em atendimento por [nome do operador ativo]" e não podem assumir enquanto o handoff estiver ativo.
- Como o sistema classifica mensagens com sentimento misto (ex: elogio ao produto mas reclamação do preço)?
- O que acontece se o Ads Agent sugerir uma campanha para um segmento sem clientes com opt-in?

## Requirements *(mandatory)*

### Functional Requirements

**Atendimento Inteligente**

- **FR-001**: O sistema DEVE receber e processar mensagens recebidas via WhatsApp Business API.
- **FR-002**: O sistema DEVE identificar o cliente pelo número de telefone a cada nova mensagem.
- **FR-003**: O sistema DEVE recuperar o histórico completo de conversas do cliente antes de gerar uma resposta.
- **FR-004**: O Agent Nino DEVE gerar respostas contextualizadas com base no histórico e no conteúdo da mensagem atual.
- **FR-005**: O sistema DEVE armazenar a classificação de sentimento (positivo, neutro, negativo) e tema (preço, produto, atendimento, qualidade) de cada mensagem. A classificação é gerada de forma assíncrona pelo sistema multi-agêntico Nino (já existente) e entregue ao CRM após o envio da resposta; o CRM não reimplementa essa lógica.
- **FR-006**: Operadores DEVEM poder assumir qualquer conversa ativa a qualquer momento, desativando respostas automáticas do Agent Nino.

**Gestão de Clientes**

- **FR-007**: O sistema DEVE criar automaticamente um registro de cliente ao receber a primeira mensagem de um número não cadastrado.
- **FR-008**: O sistema DEVE registrar e manter atualizados: data da primeira interação, data da última interação e data da última compra, lendo os dados de compra diretamente do banco de dados interno do e-commerce Playbekids (acesso compartilhado ao banco).
- **FR-009**: O sistema DEVE classificar cada cliente como: lead, cliente, cliente recorrente ou inativo, com base em regras de comportamento automáticas.
- **FR-010**: O sistema DEVE armazenar histórico completo de mensagens, sentimentos e temas por cliente.
- **FR-011**: O sistema DEVE atualizar o perfil do cliente automaticamente após cada interação, sem necessidade de input manual.

**Segmentação**

- **FR-012**: O sistema DEVE manter ao menos os seguintes segmentos automáticos: Clientes Novos, Clientes Ativos, Clientes Inativos (>30 dias sem compra ou interação), Engajados sem Compra, Sentimento Negativo Recorrente, Lead Quente.
- **FR-013**: A segmentação DEVE ser recalculada automaticamente quando o comportamento do cliente mudar.
- **FR-014**: Cada cliente DEVE pertencer a pelo menos um segmento a qualquer momento.

**Sistema de Eventos**

- **FR-015**: O sistema DEVE gerar os seguintes eventos internos com base no comportamento classificado: `cliente_interessado`, `cliente_inativo`, `cliente_insatisfeito`, `cliente_pronto_compra`.
- **FR-016**: Eventos DEVEM acionar o agente correspondente (Growth Agent ou Ads Agent) automaticamente.

**Growth Agent**

- **FR-017**: O Growth Agent DEVE receber eventos internos e gerar sugestões de ação de conversão com base no contexto do cliente.
- **FR-018**: O Growth Agent NÃO DEVE executar nenhuma ação de envio de mensagem sem aprovação humana.
- **FR-019**: O Growth Agent DEVE respeitar a janela de 24h do WhatsApp Business API, utilizando templates aprovados quando necessário.

**Ads Agent**

- **FR-020**: O Ads Agent DEVE gerar sugestões de campanha incluindo: copy, público-alvo (baseado em segmento) e orçamento estimado.
- **FR-021**: O sistema DEVE permitir edição manual de todos os campos da campanha antes da publicação.
- **FR-022**: Nenhuma campanha PODE ser publicada sem aprovação explícita de um operador humano.

**Interface Administrativa**

- **FR-023**: O acesso ao painel administrativo DEVE ser protegido por autenticação via e-mail e senha, gerenciada internamente pelo CRM, com convite enviado por e-mail para novos operadores.
- **FR-024**: Operadores DEVEM poder visualizar lista de clientes com filtro por segmento.
- **FR-025**: Operadores DEVEM poder acessar timeline individual de cada cliente com mensagens, sentimentos e compras em ordem cronológica.
- **FR-026**: Operadores DEVEM poder visualizar métricas gerais: clientes novos, ativos e inativos.
- **FR-027**: Operadores DEVEM poder aprovar ou rejeitar campanhas geradas pelo Ads Agent.
- **FR-028**: Ações críticas (assumir conversa, aprovar campanha) DEVEM exigir confirmação explícita do operador.
- **FR-029**: Quando um operador assumir uma conversa, o sistema DEVE bloquear o handoff para outros operadores e exibir o nome do operador ativo. Um segundo operador NÃO PODE assumir a mesma conversa enquanto o handoff estiver em curso.

### Key Entities

- **Cliente**: número de telefone, nome, data de primeira interação, data de última interação, data de última compra, classificação (lead/cliente/recorrente/inativo), status de opt-in, segmentos associados.
- **Mensagem**: conteúdo, direção (entrada/saída), timestamp, sentimento, tema, referência à conversa.
- **Conversa**: cliente associado, canal (WhatsApp), status (ativa/em_handoff/encerrada), data de início, agente responsável.
- **Segmento**: nome, descrição, critérios de inclusão automática, lista de clientes associados.
- **Evento**: tipo (cliente_interessado/inativo/insatisfeito/pronto_compra), cliente associado, timestamp, dados contextuais.
- **Campanha**: copy, público-alvo (segmento), orçamento sugerido, status (rascunho/aguardando_aprovação/aprovada/publicada), histórico de edições.
- **Ação de Agente**: tipo (convite_vip/oferta/follow_up), agente origem, cliente alvo, status (sugerida/aprovada/executada/rejeitada).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das mensagens recebidas são classificadas automaticamente por sentimento e tema sem intervenção manual.
- **SC-002**: O perfil do cliente é atualizado automaticamente após cada interação em menos de 5 segundos.
- **SC-003**: Nenhuma mensagem em massa ou campanha é enviada sem passar pelo fluxo de aprovação humana (0 exceções toleradas).
- **SC-004**: Operadores conseguem visualizar o histórico completo de um cliente em menos de 30 segundos a partir do acesso ao painel.
- **SC-005**: 95% dos clientes com mais de 2 interações estão corretamente segmentados em pelo menos um segmento.
- **SC-006**: Operadores conseguem assumir uma conversa ativa com no máximo 2 interações na interface.
- **SC-007**: O tempo de resposta do Agent Nino para mensagens padrão é inferior a 30 segundos após o recebimento.
- **SC-008**: Campanhas geradas pelo Ads Agent incluem copy, público e orçamento em 100% dos casos — reduzindo o tempo de criação manual em pelo menos 60%.

## Clarifications

### Session 2026-05-03

- Q: Como operadores autenticam no painel CRM? → A: Email + senha gerenciado internamente pelo CRM, com convite por e-mail.
- Q: Como o CRM recebe dados de compra do e-commerce Playbekids? → A: Leitura direta do banco de dados interno do Playbekids (banco compartilhado), pois ambos os sistemas são mantidos pelo mesmo time.
- Q: O que acontece quando dois operadores tentam assumir a mesma conversa simultaneamente? → A: A conversa fica bloqueada para o primeiro operador; os demais veem "em atendimento por [nome]" e não podem assumir enquanto o handoff estiver ativo.
- Q: Qual o volume esperado de clientes e atendimentos? → A: Base atual de ~50 clientes; expectativa de ~50 atendimentos/dia com campanhas de captação ativas.
- Q: Quando ocorre a classificação de sentimento e tema — antes ou após o envio da resposta? → A: Assíncrona (após o envio), pois a classificação já está implementada dentro do sistema multi-agêntico Nino. O CRM recebe e armazena os resultados; não precisa reimplementar a lógica de classificação.

## Assumptions

- O Agent Nino (atendimento via WhatsApp) já existe e está funcional como sistema multi-agêntico; este projeto integra e amplia suas capacidades, não o reconstrói do zero.
- A classificação de sentimento e tema já está implementada dentro do Nino. O CRM apenas recebe e persiste os resultados de forma assíncrona, sem latência adicional no caminho de resposta ao cliente.
- WhatsApp é o único canal de comunicação com clientes no escopo desta versão.
- O sistema será operado por uma equipe pequena de 1 a 5 operadores.
- Volume atual: ~50 clientes na base. Volume alvo: ~50 atendimentos/dia com campanhas de captação ativas. Infraestrutura deve ser dimensionada para suportar crescimento até ~500 clientes sem redesign.
- O CRM acessa dados de compra do e-commerce Playbekids via leitura direta no banco de dados compartilhado. Ambos os sistemas são mantidos pelo mesmo time, o que torna o acoplamento gerenciável. O mapeamento de tabelas/colunas relevantes será definido na fase de planejamento.
- Um cliente com 2+ compras confirmadas é classificado como "cliente recorrente"; com 1 compra como "cliente"; sem compras como "lead".
- "Inativo" = sem interação ou compra registrada há mais de 30 dias.
- "Lead Quente" = cliente com múltiplas interações de interesse (sentimento positivo) mas sem compra registrada.
- Banco vetorial está explicitamente fora do escopo desta versão.
- Integração com múltiplos canais além do WhatsApp está fora do escopo desta versão.
- Automação completa sem supervisão humana está fora do escopo desta versão.
- O opt-in do cliente via WhatsApp é considerado registrado automaticamente ao iniciar conversa; o sistema deve manter registro formal desse consentimento.
