-- Opcional: guarda o histórico de cada alteração (quem mudou o quê e quando)

create table if not exists public.anotacoes_log (
  id             bigserial primary key,
  chamado_id     text not null,
  prioridade     text,
  observacao     text,
  atualizado_por text,
  em             timestamptz not null default now()
);

create or replace function public.loga_anotacao()
returns trigger language plpgsql as $$
begin
  insert into public.anotacoes_log(chamado_id, prioridade, observacao, atualizado_por)
  values (new.chamado_id, new.prioridade, new.observacao, new.atualizado_por);
  return new;
end $$;

drop trigger if exists trg_anotacoes_log on public.anotacoes;
create trigger trg_anotacoes_log after insert or update on public.anotacoes
for each row execute function public.loga_anotacao();

alter table public.anotacoes_log enable row level security;
create policy "log leitura" on public.anotacoes_log for select using (true);
