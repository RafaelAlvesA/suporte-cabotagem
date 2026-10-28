-- Dados do painel (chamados, board, plantão, análises) fora do HTML público
-- Execute no Supabase: SQL Editor → New query → cole tudo → Run

create table if not exists public.painel_dados (
  chave           text primary key,          -- RAW, SNAP, PLANTAO, DEPLOYS, RELEASES, ATIV, ANALISES
  dados           jsonb not null,
  atualizado_por  text,
  atualizado_em   timestamptz not null default now()
);

alter table public.painel_dados enable row level security;

drop policy if exists "dados leitura logada" on public.painel_dados;
drop policy if exists "dados insert nstech"  on public.painel_dados;
drop policy if exists "dados update nstech"  on public.painel_dados;

-- ler: qualquer usuário logado (nstech e Maersk)
create policy "dados leitura logada" on public.painel_dados
  for select to authenticated using (true);

-- gravar: só login @nstech.com.br
create policy "dados insert nstech" on public.painel_dados
  for insert to authenticated
  with check ((auth.jwt() ->> 'email') ilike '%@nstech.com.br');

create policy "dados update nstech" on public.painel_dados
  for update to authenticated
  using ((auth.jwt() ->> 'email') ilike '%@nstech.com.br')
  with check ((auth.jwt() ->> 'email') ilike '%@nstech.com.br');

-- Anotações: hoje a leitura é pública; com o login obrigatório, passa a ser só para logados
drop policy if exists "leitura publica" on public.anotacoes;
drop policy if exists "leitura logada"  on public.anotacoes;
create policy "leitura logada" on public.anotacoes for select to authenticated using (true);
