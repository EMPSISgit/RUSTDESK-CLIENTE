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
REQUIRE_LOGIN=Y
```

É só isso. O script [`apply-custom.py`](../apply-custom.py) injeta esses
valores no código antes da compilação (nos workflows do GitHub Actions isso é
automático):

- `RENDEZVOUS_SERVERS` e `RS_PUB_KEY` em `libs/hbb_common/src/config.rs`
- fallback da API em `src/common.rs`
- `REQUIRE_LOGIN=Y` liga o padrão de login obrigatório em
  `flutter/lib/consts.dart` (veja a seção 7)

Valores vazios mantêm o comportamento padrão do RustDesk. Quem preferir não
commitar os valores pode defini-los como **GitHub Secrets/Variables de
ambiente** com os mesmos nomes — variáveis de ambiente têm prioridade sobre o
arquivo.

## 3. Dois executáveis: operador e cliente

O `custom.env` tem a variável **`BUILD_VARIANT`**, que define o que aparece na
interface do executável gerado:

| `BUILD_VARIANT` | O que mostra | Para quem |
|-----------------|--------------|-----------|
| `operador` | Campo de ID remoto + login. **Não** mostra o próprio ID/senha. | Quem presta o suporte |
| `cliente`  | **Apenas** o próprio ID e senha, para ditar ao operador. Sem login, sem campo de ID remoto, sem configurações. | Quem recebe o suporte |
| `completo` (ou vazio) | RustDesk normal: conecta e recebe. | Uso geral |

Nenhuma das variantes tem opção de instalação — as duas são **portable**
(rodam sem instalar).

**O build do GitHub Actions gera as duas de uma vez**, no mesmo release:

```text
rustdesk-1.4.7-x86_64-operador.exe
rustdesk-1.4.7-x86_64-cliente.exe
```

Ou seja, o `BUILD_VARIANT` do `custom.env` **não afeta o Windows no CI** (lá a
variante vem da matriz do workflow); ele vale para builds locais e para as
demais plataformas.

Por baixo, o `apply-custom.py` escreve as opções nativas do RustDesk
(`conn-type`, `disable-installation`, `disable-account`, `disable-settings`) em
`HARD_SETTINGS`/`BUILTIN_SETTINGS` — o mesmo mecanismo dos clientes
customizados oficiais.

## 4. Compilar pelo GitHub Actions (recomendado)

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

## 5. Compilar localmente

Siga a [documentação oficial de build](https://rustdesk.com/docs/en/dev/build/)
para preparar o ambiente (Rust, vcpkg, Flutter). A única diferença é rodar o
script **antes** de compilar:

```bash
python3 apply-custom.py --variant operador   # (Windows: python apply-custom.py ...)
python3 build.py --portable --flutter        # ou o comando da sua plataforma
```

Para gerar o segundo executável, rode de novo trocando a variante:

```bash
python3 apply-custom.py --variant cliente
python3 build.py --portable --flutter
```

Sem `--variant`, vale o `BUILD_VARIANT` do `custom.env`. O script é idempotente
e trocar de variante sobrescreve a anterior — mas **guarde o .exe da primeira
antes de compilar a segunda**, senão o build sobrescreve a saída.

## 6. Alternativa sem recompilar (Windows)

O RustDesk lê configuração embutida **no nome do arquivo** do executável. Para
um teste rápido, renomeie o instalador para:

```text
rustdesk-host=rd.exemplo.com,key=SUACHAVEPUBLICA.exe
```

Também aceita `api=` e `relay=`, separados por vírgula. **Limitação:** se a sua
chave pública contiver `/` (caractere inválido em nomes de arquivo no Windows),
esse truque não funciona — use o build customizado.

## 7. Login obrigatório de operadores

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

Com `REQUIRE_LOGIN=Y` no `custom.env`, o login já é obrigatório **desde o
primeiro uso**, antes mesmo do primeiro heartbeat — recomendado para builds de
operador. Depois que o painel responde, o valor de lá (Y/N) prevalece; ou seja,
o painel continua sendo o controle central.

Requisitos: `API_SERVER` preenchido no `custom.env` e cliente compilado a
partir deste repositório (o RustDesk original não tem essa política).

## 8. Logo e marca própria

Os ícones do aplicativo ficam em `res/` (e `flutter/android/.../mipmap-*` no
Android). Substitua-os pelos seus **mantendo os mesmos nomes e tamanhos** antes
de disparar o build. O diretório
[`brand_suporte/` do rustdesk-config](https://github.com/comunitariogpt-blip/rustdesk-config/tree/master/brand_suporte)
serve de gabarito com todos os formatos necessários (ICO, PNGs
multi-resolução, ICNS, tray, Android). Detalhes no
[README do painel, seção 4](https://github.com/comunitariogpt-blip/rustdesk-config#4-sua-pr%C3%B3pria-logo--personaliza%C3%A7%C3%A3o).

---

## 9. Problemas comuns no build

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
→ Ative **Configurações → Exigir login** no painel (seção 7) e aguarde ~15 s
com o cliente aberto. Se continuar, o build é anterior à chegada dessa política
no branch `master` — sincronize o fork e recompile.

**O cliente compila mas não conecta no servidor**
→ Confira no log do job o passo *Apply custom server settings*: ele imprime os
valores aplicados. Se disser "custom.env sem valores preenchidos", o arquivo
não foi commitado com os dados do seu servidor.

**Conectava antes, mas parou de conectar depois que o operador fez login**
→ Já corrigido no `master`. O `access_token` gravado no login fazia o cliente
exigir o handshake `secure_tcp` com o servidor de rendezvous — recurso que só o
RustDesk Pro tem, e que o hbbs OSS não implementa. Sincronize o fork e
recompile.

**O painel mostra os dispositivos online, mas conectar falha ("offline" /
"não está pronto" / timeout)**
→ O status "online" do painel usa HTTP; a conexão remota usa outras portas. A
causa mais comum é o firewall liberar só TCP: o registro de ID e o hole
punching usam **UDP 21116**, que precisa de regra própria (na AWS, TCP e UDP
são regras separadas no Security Group). Libere `21115–21119/tcp` **e**
`21116/udp`. Teste: a barra inferior do cliente deve dizer **"Pronto"**; se
disser "Não está pronto", o cliente não alcançou o hbbs.

**Erro "Key mismatch" / "Chave incompatível" ao conectar**
→ O `RS_PUB_KEY` do `custom.env` não é o mesmo do servidor. Ele deve ser o
conteúdo exato de `data/id_ed25519.pub` (uma linha, terminada em `=`). Se o
servidor foi recriado (nova pasta `data/`), a chave mudou — recompile com a
nova.

**Ambas as pontas precisam do cliente customizado**
→ Só dá para conectar em máquinas cujo cliente também aponte para o seu
servidor (este build). Um RustDesk oficial instalado na máquina remota registra
nos servidores públicos e nunca será encontrado pelo seu ID server. Na prática:
o operador usa o `-operador.exe` e a máquina atendida roda o `-cliente.exe`.

**O executável do operador não mostra o próprio ID (ou o do cliente não tem
onde digitar o ID remoto)**
→ Isso é o comportamento correto das variantes (seção 3). Se precisar dos dois
lados no mesmo executável, use `BUILD_VARIANT=completo`.

---

## Resumo (TL;DR)

```bash
# 1. suba o servidor (repo rustdesk-config) e anote IP + chave pública
# 2. neste repo:
vim custom.env               # RENDEZVOUS_SERVER / RS_PUB_KEY / API_SERVER
git commit -am "meu servidor" && git push
git tag v1.4.7-1 && git push origin v1.4.7-1
# 3. o release traz os dois portables: -operador.exe e -cliente.exe
# 3. baixe os instaladores em Releases e publique em panel/public/dist/
```
