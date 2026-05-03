<!--
SYNC IMPACT REPORT
==================
Version change: (sem versão anterior) → 1.0.0
Esta é a instanciação inicial da constituição — todos os tokens de placeholder foram substituídos.

Princípios modificados: N/A (primeira versão)

Seções adicionadas:
- Core Principles: 5 princípios definidos
- Diretrizes de IA: estrutura de agentes, condutas obrigatórias e proibições
- Gestão de Dados e Integrações: armazenamento, integrações, restrições operacionais
- Governance: procedimento de emenda, política de versionamento, conformidade

Seções removidas: N/A

Templates validados:
- ✅ .specify/templates/plan-template.md — seção "Constitution Check" é genérica; sem alterações necessárias
- ✅ .specify/templates/spec-template.md — sem referências específicas à constituição; sem alterações necessárias
- ✅ .specify/templates/tasks-template.md — sem referências específicas à constituição; sem alterações necessárias
- ✅ .specify/templates/checklist-template.md — sem referências específicas à constituição; sem alterações necessárias

TODOs adiados: Nenhum
-->

# CRM Inteligente para Loja Infantil — Constitution

## Core Principles

### I. Foco no Cliente

Todo recurso do sistema DEVE priorizar a experiência e o contexto do cliente.
Interações DEVEM ser personalizadas com base no histórico de conversas e comportamento do cliente.
Respostas genéricas sem uso de contexto disponível são PROIBIDAS.
O sistema DEVE manter histórico de conversas, interesses e análise de sentimento por cliente.

### II. Simplicidade Operacional

A interface DEVE ser utilizável por operadores sem conhecimento técnico.
Fluxos operacionais DEVEM ter no máximo 3 etapas para ações críticas (ex.: envio de campanha, cadastro de cliente).
Abstrações técnicas NÃO DEVEM ser expostas na interface de usuário.
O sistema DEVE fornecer mensagens de erro claras e acionáveis em linguagem leiga.

### III. Human-in-the-Loop (NÃO NEGOCIÁVEL)

Nenhuma campanha de marketing PODE ser enviada sem aprovação humana explícita.
Nenhuma ação que afete múltiplos clientes simultaneamente PODE ser executada de forma totalmente automatizada.
O sistema DEVE exibir prévia e solicitar confirmação antes de qualquer ação de comunicação em massa.
Agentes de IA DEVEM apresentar sugestões; a execução final DEVE ser autorizada pelo operador.

### IV. Privacidade e Segurança

O sistema DEVE estar em conformidade com a LGPD (Lei Geral de Proteção de Dados — Lei nº 13.709/2018).
Dados sensíveis de clientes (nome, telefone, histórico de compras) DEVEM ser armazenados com criptografia em repouso.
O opt-in do cliente DEVE ser registrado antes de qualquer comunicação via WhatsApp.
Dados de clientes NÃO DEVEM ser compartilhados com terceiros sem consentimento explícito e documentado.

### V. Comunicação Adequada ao Público

Toda comunicação gerada pelo sistema DEVE usar linguagem amigável, leve e acessível.
O tom das mensagens DEVE ser adequado ao público-alvo: mães, responsáveis e famílias com crianças.
Mensagens DEVEM evitar jargões técnicos, termos formais excessivos ou linguagem corporativa impessoal.
O sistema DEVE respeitar as regras da WhatsApp Business API, incluindo a janela de 24h para mensagens livres
e o uso obrigatório de templates aprovados para mensagens fora dessa janela.

## Diretrizes de IA

### Estrutura de Agentes

O sistema DEVE operar com três agentes especializados:
- **Chat Agent**: responsável pelo atendimento ao cliente via WhatsApp.
- **Growth Agent**: responsável por ações de conversão e retenção de clientes.
- **Ads Agent**: responsável pelo gerenciamento e análise de campanhas de marketing (Meta Ads).

### Condutas Obrigatórias dos Agentes

Cada agente DEVE:
- Utilizar o contexto completo do cliente (histórico, interesses, sentimento) antes de gerar respostas.
- Ser claro, objetivo e educado em todas as interações.
- Indicar ao operador quando não dispõe de informação suficiente para responder com precisão.

### Proibições dos Agentes

Nenhum agente PODE:
- Inventar ou inferir informações não registradas no sistema.
- Executar ou intermediar transações financeiras de qualquer natureza.
- Enviar mensagens em massa sem consentimento registrado e aprovação humana.
- Tomar decisões autônomas que impactem a reputação ou os dados da loja ou dos clientes.

## Gestão de Dados e Integrações

### Dados a Armazenar

O sistema DEVE armazenar e manter atualizados os seguintes dados:
- **Clientes**: dados de identificação, contato e segmentação.
- **Mensagens**: histórico completo de conversas por canal.
- **Interações**: ações realizadas, campanhas recebidas, cliques e respostas.
- **Campanhas**: configuração, audiência, resultados e status de aprovação.
- **Análise de sentimento**: classificação derivada das mensagens trocadas.
- **Interesses do cliente**: preferências inferidas a partir do comportamento registrado.

### Integrações Suportadas

- **WhatsApp Business API**: canal principal de comunicação com clientes.
- **Meta Ads API**: gerenciamento e análise de campanhas de anúncios pagos.
- **Bases de dados**: Integração com as bases de dados do ecommerce da loja e o sistema de agentes que realizam o atendimento humanizado, o Nino. 
- O sistema DEVE expor pontos de integração documentados para adição de novos canais no futuro.

### Restrições Operacionais

- Mensagens fora da janela de 24h do WhatsApp DEVEM utilizar templates previamente aprovados pela Meta.
- O sistema DEVE bloquear envios que violem as políticas da WhatsApp Business API.
- O opt-in do cliente DEVE ser verificado automaticamente antes de qualquer envio de mensagem.

## Governance

Esta constituição é o documento de referência supremo para decisões de design, escopo e comportamento do sistema.
Toda nova funcionalidade DEVE ser avaliada contra estes princípios antes de ser implementada.
Conflitos entre requisitos de produto e princípios constitucionais DEVEM ser escalados para revisão humana
antes de prosseguir com a implementação.

**Procedimento de emenda**: Alterações DEVEM ser propostas com justificativa explícita, revisadas e aprovadas
pelo responsável do projeto antes de serem aplicadas a este arquivo.

**Política de versionamento**:
- MAJOR: remoção ou redefinição incompatível de princípios existentes.
- MINOR: adição de novo princípio, seção ou expansão material de orientações.
- PATCH: clarificações, correções de redação ou refinamentos não semânticos.

**Revisão de conformidade**: Recomenda-se revisão desta constituição a cada trimestre ou sempre que uma nova
integração, agente ou funcionalidade significativa for adicionada ao sistema.

**Version**: 1.0.0 | **Ratified**: 2026-05-03 | **Last Amended**: 2026-05-03
