#!/usr/bin/env bash
# ============================================================
#  Gambiarra-Infinite  -  launcher macOS
#  Identico ao Linux; so acerta o PATH do Homebrew e o Python
#  que vem com o Xcode (que e 3.9 em versoes novas do macOS).
#  Tambem pode ser aberto com duplo clique (extensao .command).
# ============================================================
set -u

cd "$(dirname "$0")" || exit 1

# Homebrew em Apple Silicon fica em /opt/homebrew, em Intel em /usr/local
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-$LANG}"
export PYTHONIOENCODING="utf-8"
export PYTHONUTF8="1"
export TERM="${TERM:-xterm-256color}"
printf '\033]0;%s\007' "Gambiarra-Infinite"

PY=""
for c in python3 python3.13 python3.12 python3.11 python3.10 python3.9 \
         /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then
        if "$c" -c 'import sys; raise SystemExit(0 if sys.version_info>=(3,9) else 1)' 2>/dev/null; then
            PY="$c"
            break
        fi
    fi
done

if [ -z "$PY" ]; then
    echo
    echo "   Python 3.9 ou superior nao encontrado."
    echo
    echo "   Instale com:  brew install python@3"
    echo "   ou baixe em:  https://python.org/downloads"
    echo
    echo "   Pressione enter para fechar."
    read -r _
    exit 1
fi

exec "$PY" -u -X utf8 iniciar.py "$@"
