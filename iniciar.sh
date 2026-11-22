#!/usr/bin/env bash
# ============================================================
#  Gambiarra-Infinite  -  launcher Linux
#  Mesma logica do iniciar.bat: tudo mora em iniciar.py.
# ============================================================
set -u

cd "$(dirname "$0")" || exit 1

# ---- terminal: UTF-8 e cores ----
export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-$LANG}"
export PYTHONIOENCODING="utf-8"
export PYTHONUTF8="1"
export TERM="${TERM:-xterm-256color}"
# titulo da janela (funciona em quase todo terminal)
printf '\033]0;%s\007' "Gambiarra-Infinite"

# ---- acha o python 3.9+ ----
PY=""
for c in python3 python python3.13 python3.12 python3.11 python3.10; do
    if command -v "$c" >/dev/null 2>&1; then
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
    echo "   Debian/Ubuntu :  sudo apt install python3 python3-pip"
    echo "   Fedora        :  sudo dnf install python3 python3-pip"
    echo "   Arch          :  sudo pacman -S python python-pip"
    echo
    exit 1
fi

exec "$PY" -u -X utf8 iniciar.py "$@"
