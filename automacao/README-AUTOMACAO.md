# Automação do painel de chamados

Três peças nesta pasta:

| Arquivo | Para que serve |
|---|---|
| `atualizar_painel.py` | Faz todo o trabalho: busca os chamados, regenera o painel e (opcional) publica no GitHub |
| `config.ini` | Onde você diz de onde vêm os dados e para onde vai o resultado |
| `atualizar.bat` | Atalho para rodar com dois cliques no Windows |

Pré-requisito: Python 3.9 ou mais novo. Para o modo API, instale a biblioteca de rede:

```
pip install requests
```

---

## Modo CSV (funciona hoje, sem depender de ninguém)

Você exporta o CSV do GLPI como já faz. O script pega **o mais recente** da pasta e
regenera o painel.

No `config.ini`:

```ini
[geral]
modo = csv
arquivo_painel = C:\Users\Rafael Alves\Downloads\suporte-cabotagem\index.html

[csv]
pasta = C:\Users\Rafael Alves\Downloads
padrao = glpi*.csv
```

Rode com duplo clique no `atualizar.bat`. Deve aparecer algo como:

```
lendo glpi (48).csv
painel atualizado: 193 chamados, 31 em aberto, referência 2026-08-21 12:05
```

---

## Modo API (elimina o export manual)

### 1. Descobrir se a API está ligada

No GLPI, com perfil de administrador: **Configurar → Geral → API**.
Procure por "Habilitar API REST" e pela URL da API (normalmente
`https://hubtech.nstech.com.br/apirest.php`).

Se você não tiver acesso a essa tela, peça ao administrador do GLPI:

> "Preciso da API REST habilitada e de um App-Token (client) para uso interno.
> Vou consumir só leitura de chamados do grupo Suporte Cabotagem."

### 2. Gerar os dois tokens

- **App-Token**: em Configurar → Geral → API → "Adicionar cliente de API". O administrador gera.
- **User-Token**: seu, em **Preferências** (menu do seu usuário) → aba **Chaves de acesso remoto**
  → "Token de API" → Gerar.

### 3. Preencher o config.ini

```ini
[geral]
modo = api

[glpi]
url = https://hubtech.nstech.com.br/apirest.php
app_token = SEU_APP_TOKEN
user_token = SEU_USER_TOKEN
grupo_tecnico = Suporte Cabotagem
```

> O arquivo fica só na sua máquina. Não suba o `config.ini` para o GitHub —
> se for versionar a pasta, adicione `config.ini` ao `.gitignore`.

### 4. Testar

```
python atualizar_painel.py --testar
```

Resposta esperada: `conexão OK` e a contagem de campos reconhecidos.
Se der erro 401, o token está errado ou a API não está liberada para o seu usuário.

---

## Publicar no GitHub automaticamente

Só funciona se você tiver um clone local do repositório e o `git` autenticado
(via GitHub Desktop, credential manager ou chave SSH).

```ini
[github]
publicar = sim
pasta_repo = C:\Users\Rafael Alves\repos\suporte-cabotagem
```

Nesse caso aponte também o `arquivo_painel` para o `index.html` dentro do clone.
O script faz `git add`, `commit` e `push` sozinho.

---

## Rodar sozinho todo dia

Windows: **Agendador de Tarefas** → Criar Tarefa Básica

1. Nome: `Atualiza painel de chamados`
2. Disparador: Diariamente, no horário que quiser (ex.: 08:00)
3. Ação: Iniciar um programa
   - Programa: `C:\Windows\System32\cmd.exe`
   - Argumentos: `/c "C:\Users\Rafael Alves\Downloads\suporte-cabotagem\automacao\atualizar.bat"`
4. Marque "Executar estando o usuário conectado ou não" se for modo API com acesso direto

No modo CSV o agendamento só faz sentido se o export do GLPI também for automático —
senão o script vai reprocessar o mesmo arquivo.

---

## Limites conhecidos

- O script reescreve **apenas o bloco de dados** do `index.html`. Layout, marca e
  funcionalidades ficam intactos, e novas versões do painel continuam compatíveis.
- Se a busca não retornar nada, ele aborta sem gravar — evita apagar o painel por engano.
- O histórico diário continua acumulando dentro do próprio HTML, como já funciona hoje.
