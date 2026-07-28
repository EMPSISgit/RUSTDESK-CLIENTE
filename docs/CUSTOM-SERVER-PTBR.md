# Cliente customizado — apontando para o SEU servidor

Este fork do [RustDesk](https://github.com/rustdesk/rustdesk) é o **cliente** da
stack de suporte remoto do painel
[**rustdesk-config**](https://github.com/comunitariogpt-blip/rustdesk-config)
(servidor `hbbs`/`hbbr` em Docker + painel PHP de gestão de operadores,
dispositivos e sessões).

Quem instala essa stack tem um **IP/domínio próprio** — e o cliente precisa
sair da compilação já apontando para ele. Toda essa configuração fica em **um
único arquivo**: [`custom.env`](../custom.env), na raiz deste repositório.

```text
┌─────────────────────┐  21115-21119   ┌───────────────────────────┐
│  ESTE CLIENTE       │◄──────────────►│  SEU servidor RustDesk    │
│  (fork compilado)   │  (P2P/relay)   │  hbbs + hbbr (Docker)     │
└─────────┬───────────┘                └───────────────────────────┘
          │ HTTPS (login/política)
          ▼
┌───────────────────────────┐
│  SEU painel (rustdesk-config)  │
└───────────────────────────┘
```

---

## 1. O que você precisa antes de compilar

Suba primeiro o backend seguindo o
[README do rustdesk-config](https://github.com/comunitariogpt-blip/rustdesk-config#readme).
Dele você tira os três valores:

| Valor               | De onde vem                                                        |
|---------------------|--------------------------------------------------------------------|
| `RENDEZVOUS_SERVER` | IP público ou domínio onde o `hbbs`/`hbbr` roda (ex.: `rd.exemplo.com`) |
| `RS_PUB_KEY`        | Conteúdo do arquivo `data/id_ed25519.pub` (chave **pública**, gerada no 1º start) |
| `API_SERVER`        | URL do painel (ex.: `https://rd.exemplo.com`) — opcional, mas necessário para login de operadores |

> A chave **privada** (`data/id_ed25519`) nunca sai do servidor. A pública pode
> (e deve) ser distribuída nos clientes.

## 2. Configurar o `custom.env`

Edite o [`custom.env`](../custom.env) na raiz do projeto:

```ini
RENDEZVOUS_SERVER=rd.exemplo.com
RS_PUB_KEY=OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=
API_SERVER=https://rd.exemplo.com
```

É só isso. O script [`apply-custom.py`](../apply-custom.py) injeta esses
valores no código antes da compilação (nos workflows do GitHub Actions isso é
automático):

- `RENDEZVOUS_SERVERS` e `RS_PUB_KEY` em `libs/hbb_common/src/config.rs`
- fallback da API em `src/common.rs`

Valores vazios mantêm o comportamento padrão do RustDesk. Quem preferir não
commitar os valores pode defini-los como **GitHub Secrets/Variables de
ambiente** com os mesmos nomes — variáveis de ambiente têm prioridade sobre o
arquivo.

## 3. Compilar pelo GitHub Actions (recomendado)

Não precisa de máquina de build: o próprio GitHub compila para Windows, Linux,
macOS, Android e iOS.

1. **Fork/clone** deste repositório na sua conta do GitHub.
2. Edite o `custom.env` (seção 2), commit e push.
3. Dispare o build de release por **um** destes caminhos:
   - **Tag:** crie e envie uma tag no formato `X.Y.Z` ou `vX.Y.Z`
     (ex.: `git tag v1.4.7-1 && git push origin v1.4.7-1`); ou
   - **Manual:** aba **Actions → Flutter Tag Build → Run workflow**, informando
     o nome da tag no campo que aparece.
4. Aguarde o workflow terminar (leva bastante tempo — compila todas as
   plataformas) e baixe os instaladores na aba **Releases** do seu fork.
5. Publique os instaladores no seu painel, em `panel/public/dist/` do
   [rustdesk-config](https://github.com/comunitariogpt-blip/rustdesk-config)
   (diretório ignorado pelo Git, de onde o painel serve os downloads).

> **Secrets de assinatura são opcionais.** Sem `ANDROID_SIGNING_KEY`,
> `MACOS_P12_BASE64` etc., os binários saem sem assinatura digital — funcionam,
> mas o sistema operacional pode exibir avisos na instalação.

## 4. Compilar localmente

Siga a [documentação oficial de build](https://rustdesk.com/docs/en/dev/build/)
para preparar o ambiente (Rust, vcpkg, Flutter). A única diferença é rodar o
script **antes** de compilar:

```bash
python3 apply-custom.py      # (Windows: python apply-custom.py)
python3 build.py --flutter   # ou o comando de build da sua plataforma
```

O script é idempotente — pode rodar quantas vezes quiser.

## 5. Alternativa sem recompilar (Windows)

O RustDesk lê configuração embutida **no nome do arquivo** do executável. Para
um teste rápido, renomeie o instalador para:

```text
rustdesk-host=rd.exemplo.com,key=SUACHAVEPUBLICA.exe
```

Também aceita `api=` e `relay=`, separados por vírgula. **Limitação:** se a sua
chave pública contiver `/` (caractere inválido em nomes de arquivo no Windows),
esse truque não funciona — use o build customizado.

## 6. Login obrigatório de operadores

Cada build conversa **apenas com o painel embutido nele** (o `API_SERVER` do
`custom.env`): é dali que vêm os usuários/senhas (tabela `operators` do
rustdesk-config), o registro de dispositivos e o histórico de conexões. Deploys
diferentes ficam naturalmente isolados — o build de um servidor nunca consulta
o painel de outro.

Para **exigir login antes de conectar**, ative no painel:
**Configurações → Exigir login** (a opção nasce **desligada**). A política
chega aos clientes pelo heartbeat em ~15 segundos, sem recompilar; ao ligar,
todo clique em "Conectar" passa a abrir a tela de login se o operador ainda não
estiver autenticado.

Requisitos: `API_SERVER` preenchido no `custom.env` e cliente compilado a
partir deste repositório (o RustDesk original não tem essa política).

## 7. Logo e marca própria

Os ícones do aplicativo ficam em `res/` (e `flutter/android/.../mipmap-*` no
Android). Substitua-os pelos seus **mantendo os mesmos nomes e tamanhos** antes
de disparar o build. O diretório
[`brand_suporte/` do rustdesk-config](https://github.com/comunitariogpt-blip/rustdesk-config/tree/master/brand_suporte)
serve de gabarito com todos os formatos necessários (ICO, PNGs
multi-resolução, ICNS, tray, Android). Detalhes no
[README do painel, seção 4](https://github.com/comunitariogpt-blip/rustdesk-config#4-sua-pr%C3%B3pria-logo--personaliza%C3%A7%C3%A3o).

---

## 8. Problemas comuns no build

**Todos os passos `Publish ...` falham com `Resource not accessible by
integration`, mas a compilação passou**
→ O `GITHUB_TOKEN` está sem permissão para criar o Release. Os workflows deste
fork já declaram `permissions: contents: write`, então **atualize o seu fork**
(botão **Sync fork** na página do repositório) e rode o build de novo. Se ainda
assim falhar, a conta/organização está forçando token somente leitura: vá em
**Settings → Actions → General → Workflow permissions**, marque **"Read and
write permissions"** e salve.

**O workflow falha imediatamente, em segundos, num arquivo `main.yml`**
→ Um workflow vazio criado por engano pelo botão verde **"New workflow"**.
Apague `.github/workflows/main.yml` — os workflows de build já vêm prontos no
fork, não é preciso criar nenhum.

**O release saiu com o nome "master"**
→ Execução manual sem informar a tag em versões antigas deste fork. Atualize o
fork (Sync fork) e informe a tag no campo do **Run workflow**, ou publique via
`git tag`.

**O cliente conecta sem pedir login de operador**
→ Ative **Configurações → Exigir login** no painel (seção 6) e aguarde ~15 s
com o cliente aberto. Se continuar, o build é anterior à chegada dessa política
no branch `master` — sincronize o fork e recompile.

**O cliente compila mas não conecta no servidor**
→ Confira no log do job o passo *Apply custom server settings*: ele imprime os
valores aplicados. Se disser "custom.env sem valores preenchidos", o arquivo
não foi commitado com os dados do seu servidor.

---

## Resumo (TL;DR)

```bash
# 1. suba o servidor (repo rustdesk-config) e anote IP + chave pública
# 2. neste repo:
vim custom.env               # RENDEZVOUS_SERVER / RS_PUB_KEY / API_SERVER
git commit -am "meu servidor" && git push
git tag v1.4.7-1 && git push origin v1.4.7-1
# 3. baixe os instaladores em Releases e publique em panel/public/dist/
```
