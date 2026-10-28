# Banco de anotações — prioridade e observação editáveis

O painel continua sendo uma página estática. As duas colunas novas
(**Prioridade equipe** e **Observação**) ficam num banco Postgres hospedado no
**Supabase**, no plano gratuito. Quem estiver logado edita direto na tabela do painel;
quem não estiver apenas visualiza.

---

## 1. Criar o projeto

1. Acesse `supabase.com` → **Start your project** → entre com GitHub ou e-mail
2. **New project**
   - Name: `suporte-cabotagem`
   - Database password: gere uma forte e **guarde no seu gerenciador de senhas**
   - Region: **South America (São Paulo)**
3. Espere uns 2 minutos até o projeto subir

## 2. Criar a tabela

**SQL Editor** → **New query** → cole o conteúdo de `01-criar-tabela.sql` → **Run**.

Se quiser guardar o histórico de cada alteração, rode também o `02-historico-opcional.sql`.

## 3. Pegar as duas chaves

**Project Settings** → **API**:

- **Project URL** — algo como `https://abcdefgh.supabase.co`
- **anon public** — a chave pública (começa com `eyJ...`)

> A chave `anon` é feita para ficar visível no navegador, não é segredo.
> Quem protege a escrita são as políticas de segurança criadas no passo 2.
> **Nunca** use a chave `service_role` no painel.

## 4. Colar no painel

Abra o `index.html` num editor de texto, procure por `const SUP=` e preencha:

```js
const SUP={url:'https://abcdefgh.supabase.co',anon:'eyJhbGciOi...'};
```

Salve e suba o arquivo para o GitHub.

## 5. Criar os usuários do time

**Authentication** → **Users** → **Add user** → e-mail e senha para cada pessoa.
Marque "Auto Confirm User" para não precisar de confirmação por e-mail.

Sugestão: crie um usuário por pessoa, não um compartilhado — assim a coluna
`atualizado_por` registra quem alterou.

Em **Authentication → Providers → Email**, desligue **Enable signup** para que
ninguém de fora consiga se cadastrar sozinho.

---

## Como usar no dia a dia

1. Abra o painel publicado
2. Clique em **Entrar para editar**, informe e-mail e senha
3. As colunas Prioridade equipe e Observação viram campos editáveis nas abas
   **Fila em aberto** e **Todos os chamados**
4. A gravação é automática ao sair do campo — a borda fica verde quando salvou

As anotações ficam ligadas ao número do chamado, então **sobrevivem a qualquer
atualização do CSV do GLPI**. Importar dados novos não apaga nada.

---

## Limites e cuidados

- **No artefato do Cowork a edição não funciona**: aquele ambiente bloqueia chamadas
  de rede externas. Use o painel publicado no GitHub Pages.
- **Leitura é pública**: qualquer pessoa com o link vê as anotações. Se precisar
  esconder, troque a política `leitura publica` para exigir login também.
- **Plano gratuito** do Supabase pausa projetos sem acesso por uma semana. Basta
  reativar pelo console. Para uso diário, não é problema.
- Se alguém sair da equipe, remova o usuário em Authentication → Users.
