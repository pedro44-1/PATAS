# Plano de faturação operacional

## Objetivo

Completar o fluxo de faturação do piloto LAN como preparação e envio de dados para um software terceiro responsável pela emissão fiscal. O PATAS recolhe, valida e preserva os dados da operação; o provedor devolve a referência, o número, o estado e, quando suportado, a ligação do documento emitido.

O PATAS não cria numeração fiscal nem declara certificação pela Administração Geral Tributária. A validade fiscal, a série, o número e o PDF pertencem ao software terceiro contratado.

## Âmbito

- Associar uma fatura a um dono e, opcionalmente, a uma consulta do mesmo dono e clínica.
- Registar linhas com descrição, quantidade e preço unitário líquido.
- Calcular apenas o subtotal comercial provisório; IVA, retenções e total fiscal pertencem ao Vendas.
- Manter compatibilidade com o contrato legado de `amount` e `description`.
- Receber do provedor a série, o número e a ligação do documento, quando disponíveis.
- Guardar instantâneos dos dados da clínica e do cliente para que documentos históricos não mudem.
- Guardar NIF opcional no cadastro da clínica e do dono; ambos são exigidos antes da emissão.
- Preservar campos de pagamento para futura reconciliação, sem permitir confirmação manual no PATAS.
- Permitir abrir ou descarregar o documento devolvido pelo provedor sem expor dados entre clínicas.
- Manter `draft -> sent | paid | cancelled`; uma FT emitida passa a `sent` e uma FR passa a `paid` só após confirmação da emissão pelo Vendas, sem marcação manual.
- Manter um adaptador substituível para emissão externa, usando o mock local por omissão e o Vendas quando configurado.

## Estado

Os quatro marcos abaixo estão implementados para o modo `TRAINING` e foram exercitados entre PATAS e Vendas em 2026-09-29, incluindo FT, FR, prévia, retry idempotente e referência à consulta. Não representam emissão fiscal AGT.

## Contrato Vendas confirmado

- Emissão: `POST /api/integrations/v1/invoices`; reconciliação por ID ou `externalId`.
- Autenticação server-to-server com Bearer key guardada apenas no backend.
- Escopos mínimos: `invoice.issue`, `invoice.read`, `customer.upsert` e `product.upsert`.
- Idempotência: UUID persistido no PATAS e enviado em `Idempotency-Key`; retries mantêm chave e corpo.
- Identidade: `externalId` estável da cobrança, `storeExternalId` configurado por clínica e referência opcional à consulta.
- Cliente: nome, NIF em `customer.taxId`, contactos, endereço e país `AO`.
- Linhas: identificador, código obrigatório de até 64 caracteres (com fallback determinístico por clínica, tipo e descrição para legados), descrição, `SERVICE`/`PRODUCT`, unidade, operação, quantidade, preço e desconto.
- O `externalId` da linha identifica o produto/serviço, deriva de clínica, tipo e código estável e é reutilizado entre faturas; o `externalId` da cobrança permanece separado.
- No JSON Vendas, código de linha é obrigatório, decimais são strings exatas e campos opcionais não configurados são omitidos em vez de enviados como `null`.
- Cada linha envia `vatProfileCode` de até 80 caracteres, escolhido por override da linha ou pelo perfil predefinido configurado na instalação; o perfil seleciona a regra, mas o cálculo continua no Vendas.
- Prévia: `POST /api/integrations/v1/invoices/preview`, com `externalId`, `storeExternalId`, data e as mesmas linhas líquidas da emissão. A chave UUID da prévia torna-se `quote.id` e a cotação expira em dez minutos.
- O PATAS preserva `quote.id`, expiração, versão fiscal, digest, `totals.payable` e o snapshot devolvido. A ausência de perfil fiscal resulta em `VAT_PROFILE_REQUIRED` e deve ser corrigida no Vendas.
- Emissão: `POST /api/integrations/v1/invoices` usa `quoteId`, o mesmo payload comercial e uma nova chave idempotente, diferente da prévia.
- FT não envia pagamento. FR envia `tenders` cuja soma é exatamente o `payable` cotado; numerário exige `cash.operate` e uma sessão de caixa Vendas aberta.
- Métodos FR suportados são numerário, cartão/TPA e transferência; o método genérico `other` fica bloqueado por não existir tender equivalente no Vendas.
- O Vendas resolve o perfil fiscal, calcula IVA, retenções e `payable`, e devolve estado, modo, série, número e referência do documento.
- A integração atual aponta ao modo `TRAINING`, sem validade fiscal nem comunicação AGT.

## Fora do âmbito imediato

- Certificação fiscal, comunicação direta do PATAS à AGT, assinatura digital fiscal ou séries próprias.
- Cobrança real sem provedor, contrato comercial, credenciais e regras de conciliação definidos.
- Reembolsos, notas de crédito, pagamentos parciais e múltiplas moedas.

## Marco 1 - Dados e migração

- Adicionar `nif` opcional a clínicas e donos.
- Criar linhas de fatura com `clinic_id`, descrição, quantidade, preço unitário e campos legados de total.
- Acrescentar à fatura subtotal provisório, campos legados, método de pagamento, cotação, datas, instantâneos de emitente/cliente e campos de resposta do provedor.
- Converter faturas anteriores numa linha única usando descrição e valor existentes.
- Preservar `amount` como total compatível para clientes antigos.

## Marco 2 - API e regras

- Aceitar linhas no pedido de criação e usar o formato legado quando não forem enviadas.
- Validar quantidades positivas, valores não negativos e rejeitar cálculo fiscal local.
- Rejeitar consultas de outro dono, outra clínica ou entidades arquivadas.
- Impedir alterações financeiras depois de sair de `draft`.
- Rejeitar a marcação manual como paga.
- Expor o documento completo, incluindo linhas e instantâneos.
- Construir o payload estrito da prévia sem dados do cliente e o payload de emissão com `quoteId`, NIF e nome do cliente, serviços/produtos, quantidades e preços líquidos; a credencial identifica a entidade emitente no Vendas.
- Validar os dados obrigatórios antes do envio e devolver erros acionáveis.
- Guardar a referência, número, série, estado e URL devolvidos pelo provedor.
- Invalidar a cotação e pedir nova prévia em `QUOTE_NOT_FOUND`, `QUOTE_EXPIRED`, `QUOTE_MISMATCH` ou `QUOTE_STALE`; timeout de emissão repete o mesmo corpo e a mesma chave.

## Marco 3 - Experiência de emissão

- Mostrar dono, consulta opcional e linhas repetíveis no formulário.
- Filtrar as consultas pelo dono selecionado.
- Mostrar o subtotal comercial provisório, obter a prévia e apresentar o `payable` calculado pelo Vendas antes da emissão.
- Mostrar o número devolvido pelo provedor e permitir abrir o documento quando existir URL.
- Manter estados de carregamento, erro, vazio e ações terminais já existentes.
- Adicionar todos os textos a `pt.json` e manter `en.json` alinhado.

## Marco 4 - Pagamentos externos

- Formalizar o contrato do adaptador: emissão, consulta de estado, referência idempotente e documento devolvido.
- Manter `mock` como provedor seguro por omissão no piloto.
- Bloquear configuração de um provedor desconhecido com erro explícito.
- Ativar FT e FR no adaptador Vendas apenas com URL, chave, tipo de operação e `storeExternalId` válidos; numerário exige ainda sessão de caixa.
- Nunca marcar a emissão ou o pagamento como concluídos antes da resposta de sucesso do Vendas.
- Guardar tentativas, último erro seguro e instante de reconciliação para permitir retry sem duplicação.

## Testes e gate de entrega

- Backend: cálculo e arredondamento, formato legado, payload externo, instantâneos, consulta/dono, tenant, estados terminais e adaptador mock.
- Migração: base vazia e atualização de uma base com faturas anteriores.
- Frontend: linhas, subtotal provisório, consulta filtrada, payable da cotação, FT/FR e abertura do documento devolvido.
- Build: shared types, frontend e lint backend.
- Verificação visual: formulário em desktop e largura reduzida; ligação do documento e erros do provedor apresentados sem cortes.

## Definição de concluído

- Uma rececionista consegue preparar e enviar uma FT ou FR discriminada sem calcular IVA ou digitar o total fiscal manualmente.
- A consulta escolhida pertence ao dono e à clínica autenticada.
- O pedido preserva dados históricos e recebe a referência e os dados documentais devolvidos pelo provedor.
- Faturas antigas continuam legíveis e ganham uma linha de compatibilidade.
- Documentos emitidos não podem ser anulados apenas no PATAS; `paid` e `cancelled` são terminais.
- O adaptador local continua funcional e a ativação de pagamentos reais permanece bloqueada até existir uma decisão explícita de provedor.
