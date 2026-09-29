# Operação do piloto LAN

## Âmbito

O piloto corre num único servidor Docker Compose, numa rede privada, apenas em HTTP/80. PostgreSQL e Redis não são publicados pela configuração `infra/docker-compose.yml`; o browser usa o mesmo host para a SPA e `/api/v1`.

## Instalação limpa

No servidor Linux, a partir da raiz do repositório:

```sh
cp infra/.env.example infra/.env
python -c "import secrets; print(secrets.token_urlsafe(64))"
docker compose -f infra/docker-compose.yml --env-file infra/.env config --quiet
docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build
curl --fail http://127.0.0.1/health
```

Antes de iniciar, substitua em `infra/.env` `POSTGRES_PASSWORD`, `SECRET_KEY` e `ENCRYPTION_KEY`. Restrinja a porta 80 à LAN no firewall do servidor. O serviço `migrate` executa `alembic upgrade head`; o backend só arranca quando a migração termina com sucesso.

Aceda por `http://<ip-do-servidor>/`. O primeiro registo cria uma clínica e o administrador inicial. Contas adicionais são criadas pelo administrador com palavra-passe temporária e ficam limitadas à alteração obrigatória dessa palavra-passe.

## Atualização

1. Anuncie uma janela de manutenção e confirme que não há consultas em edição.
2. Crie e valide um backup.
3. Atualize o código/imagens.
4. Execute `docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build`.
5. Confirme `docker compose ... ps`, os logs de `migrate` e `curl --fail http://127.0.0.1/health`.
6. Faça login e valide agenda, sala de espera, histórico e faturação mock.

Se `migrate` falhar, o backend não arranca. Preserve a base, recolha `docker compose -f infra/docker-compose.yml --env-file infra/.env logs migrate` e corrija a causa antes de repetir; não contorne a migração.

## Backup

Crie um dump PostgreSQL em formato customizado:

```sh
sh infra/scripts/backup-db.sh
```

O caminho do ficheiro é devolvido no fim. Pode indicar um diretório externo como primeiro argumento. Guarde cópias fora do servidor, cifradas e com acesso restrito. Um backup só é aceite para dados reais depois de se confirmar que o ficheiro é não vazio e de concluir um ensaio de restauro.

## Restauro e ensaio obrigatório

O restauro substitui os dados atuais. Faça-o numa janela de manutenção e, para o ensaio, prefira uma instalação descartável com uma cópia do `.env` própria:

```sh
CONFIRM_RESTORE=YES sh infra/scripts/restore-db.sh /caminho/patas-AAAAMMDDTHHMMSSZ.dump
curl --fail http://127.0.0.1/health
```

Depois do restauro, confirme que um administrador inicia sessão, que donos/animais arquivados permanecem no histórico, que uma fatura e uma consulta histórica abrem e que uma nova marcação pode ser criada. Registe data, operador, ficheiro, resultado e duração do ensaio fora do repositório.

## Verificações operacionais

- `/health` deve devolver `200` e `database=ok`, `redis=ok`; `503` significa que o nó não está saudável.
- O relógio funcional é `Africa/Luanda`; a persistência usa UTC.
- Donos e animais são arquivados, não apagados. Tratamentos não têm eliminação física. Faturas terminam em `paid` ou `cancelled`; cancelamento exige motivo.
- O piloto não inclui HTTPS público, pagamentos reais, email de convite/recuperação, alta disponibilidade ou monitorização avançada.
