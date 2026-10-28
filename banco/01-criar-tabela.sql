-- Execute no Supabase: SQL Editor → New query → cole tudo → Run

create table if not exists public.anotacoes (
  chamado_id      text primary key,
  prioridade      text,
  observacao      text,
  atualizado_por  text,
  atualizado_em   timestamptz not null default now()
);

-- carimba a data a cada alteração
create or replace function public.toca_anotacao()
returns trigger language plpgsql as $$
begin
  new.atualizado_em = now();
  return new;
end $$;

drop trigger if exists trg_anotacoes on public.anotacoes;
create trigger trg_anotacoes before insert or update on public.anotacoes
for each row execute function public.toca_anotacao();

-- segurança: leitura liberada, escrita só para quem estiver autenticado
alter table public.anotacoes enable row level security;

drop policy if exists "leitura publica"   on public.anotacoes;
drop policy if exists "escrita logada"    on public.anotacoes;
drop policy if exists "alteracao logada"  on public.anotacoes;

create policy "leitura publica"  on public.anotacoes for select using (true);
create policy "escrita logada"   on public.anotacoes for insert to authenticated with check (true);
create policy "alteracao logada" on public.anotacoes for update to authenticated using (true) with check (true);
