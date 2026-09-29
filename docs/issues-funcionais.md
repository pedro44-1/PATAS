# Gestão de defeitos funcionais do MVP

As antigas propostas de implementação RF01–RF11 foram incorporadas no código e deixaram de representar trabalho pendente. A cobertura e a evidência atual estão em `matriz-rastreabilidade.md`.

Antes de uma release piloto:

- qualquer defeito P0/P1 no percurso principal bloqueia a release;
- cada defeito deve indicar o RF e o critério vertical afetado;
- a correção deve acrescentar ou ajustar um teste automatizado que reproduza a regressão;
- limitações assumidas — HTTPS público, pagamentos reais, email, WhatsApp operacional, alta disponibilidade e monitorização avançada — são exclusões, não defeitos deste MVP.
