#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply-custom.py — embute a configuracao de servidor do `custom.env` no codigo
antes da compilacao.

Uso:
    python3 apply-custom.py            # le custom.env e aplica os patches
    python3 apply-custom.py --check    # so mostra o que seria feito

O que ele altera (apenas se o valor correspondente estiver preenchido):
  1. libs/hbb_common/src/config.rs -> RENDEZVOUS_SERVERS  (RENDEZVOUS_SERVER)
  2. libs/hbb_common/src/config.rs -> RS_PUB_KEY          (RS_PUB_KEY)
  3. src/common.rs                 -> fallback da API      (API_SERVER)

Variaveis de ambiente com os mesmos nomes tem prioridade sobre o custom.env
(util para configurar via GitHub Secrets sem commitar valores).

O script e idempotente: pode rodar varias vezes sem efeito colateral.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(ROOT, "custom.env")
CONFIG_RS = os.path.join(ROOT, "libs", "hbb_common", "src", "config.rs")
COMMON_RS = os.path.join(ROOT, "src", "common.rs")


def load_env():
    values = {"RENDEZVOUS_SERVER": "", "RS_PUB_KEY": "", "API_SERVER": ""}
    if os.path.isfile(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip().strip('"').strip("'")
                if key in values:
                    values[key] = val
    # Variaveis de ambiente (ex.: GitHub Secrets) tem prioridade
    for key in values:
        env_val = os.environ.get(key, "").strip()
        if env_val:
            values[key] = env_val
    return values


def patch_file(path, pattern, replacement, label, check_only):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if replacement in content:
        print(f"OK  : {label} ja estava aplicado.")
        return
    new_content, count = re.subn(pattern, replacement, content, count=1)
    if count == 0:
        print(f"ERRO: padrao de '{label}' nao encontrado em {path}.")
        print("      O codigo upstream pode ter mudado; ajuste apply-custom.py.")
        sys.exit(1)
    if check_only:
        print(f"FARIA: {label} em {os.path.relpath(path, ROOT)}")
        return
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(new_content)
    print(f"OK  : {label} aplicado em {os.path.relpath(path, ROOT)}")


def main():
    check_only = "--check" in sys.argv
    values = load_env()

    if not any(values.values()):
        print("custom.env sem valores preenchidos — nada a fazer (build padrao).")
        return

    if not os.path.isfile(CONFIG_RS):
        print(f"ERRO: {CONFIG_RS} nao existe.")
        print("      Baixe os submodulos: git submodule update --init --recursive")
        sys.exit(1)

    if values["RENDEZVOUS_SERVER"]:
        patch_file(
            CONFIG_RS,
            r'pub const RENDEZVOUS_SERVERS: &\[&str\] = &\[[^\]]*\];',
            'pub const RENDEZVOUS_SERVERS: &[&str] = &["%s"];'
            % values["RENDEZVOUS_SERVER"],
            "RENDEZVOUS_SERVER = %s" % values["RENDEZVOUS_SERVER"],
            check_only,
        )

    if values["RS_PUB_KEY"]:
        patch_file(
            CONFIG_RS,
            r'pub const RS_PUB_KEY: &str = "[^"]*";',
            'pub const RS_PUB_KEY: &str = "%s";' % values["RS_PUB_KEY"],
            "RS_PUB_KEY = %s..." % values["RS_PUB_KEY"][:12],
            check_only,
        )

    if values["API_SERVER"]:
        patch_file(
            COMMON_RS,
            r'"https://admin\.rustdesk\.com"\.to_owned\(\)',
            '"%s".to_owned()' % values["API_SERVER"],
            "API_SERVER = %s" % values["API_SERVER"],
            check_only,
        )

    print("Pronto. Agora compile normalmente (build.py / cargo / flutter).")


if __name__ == "__main__":
    main()
