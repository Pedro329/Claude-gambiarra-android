#!/usr/bin/env python3
"""Gambiarra-Infinite - launcher multiplataforma.

Um unico ponto de entrada para Windows, Linux e macOS. Faz o que cada
launcher nativo (.bat / .sh / .command) faria, mas igual nos tres:

  * acha o Python 3.9+ disponivel
  * garante as dependencias (selenium para o farm com navegador)
  * valida a codificacao / terminal
  * entrega o controle ao core/main.py

Nao ha codigo especifico de sistema no core: so aqui, e sempre com o
mesmo comportamento.
"""

import os
import platform
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.join(AQUI, "core")
MINIMO = (3, 9)


# ---------------------------------------------------------------- terminal
def sistema():
    """Nome do sistema em minusculas: windows / linux / mac."""
    nome = platform.system().lower()
    if nome.startswith("win"):
        return "windows"
    if nome == "darwin":
        return "mac"
    return "linux"


def preparar_terminal():
    """UTF-8 e ANSI ligados, sem depender do .bat / .sh.

    O console do Windows precisa de duas coisas que ele nao faz sozinho:
    code page 65001 e o modo de terminal virtual para aceitar ANSI. No
    Linux/macOS o terminal ja nasce assim; so forca UTF-8.
    """
    so = sistema()
    if so == "windows":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleOutputCP(65001)
            k.SetConsoleCP(65001)
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING no stdout
            h = k.GetStdHandle(-11)
            modo = ctypes.c_uint32()
            if k.GetConsoleMode(h, ctypes.byref(modo)):
                k.SetConsoleMode(h, modo.value | 0x0004)
        except Exception:
            pass
    # em todos: garante que o Python fale UTF-8 com o terminal
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")


def titulo(nome):
    """Titulo da janela, do jeito de cada sistema."""
    so = sistema()
    try:
        if so == "windows":
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(nome)
            return
    except Exception:
        pass
    # ANSI OSC: funciona no Linux, macOS e Windows Terminal
    sys.stdout.write("\x1b]0;%s\x07" % nome)
    sys.stdout.flush()


# ----------------------------------------------------------------- python
def versao_ok():
    return sys.version_info >= MINIMO


def rodando_no_python_certo():
    """O launcher pode ter sido aberto pelo python do PATH errado."""
    return versao_ok()


def procurar_python():
    """Devolve o comando do primeiro Python 3.9+ encontrado."""
    candidatos = []
    so = sistema()
    if so == "windows":
        candidatos += ["py", "python", "python3"]
        # instalacoes por usuario, sem depender do PATH
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            base = os.path.join(local, "Programs", "Python")
            if os.path.isdir(base):
                for pasta in sorted(os.listdir(base), reverse=True):
                    exe = os.path.join(base, pasta, "python.exe")
                    if os.path.isfile(exe):
                        candidatos.append(exe)
    else:
        candidatos += ["python3", "python"]
        if so == "mac":
            candidatos += ["/opt/homebrew/bin/python3",
                           "/usr/local/bin/python3"]
    for c in candidatos:
        caminho = shutil.which(c) if os.sep not in c else c
        if not caminho or not os.path.isfile(caminho):
            continue
        if checa_versao(caminho):
            return caminho
    return None


def checa_versao(exe):
    try:
        r = subprocess.run([exe, "-c",
                            "import sys;print('%d.%d'%sys.version_info[:2])"],
                           capture_output=True, text=True, timeout=20)
        if r.returncode != 0:
            return False
        partes = r.stdout.strip().split(".")
        return (int(partes[0]), int(partes[1])) >= MINIMO
    except Exception:
        return False


def aviso_python():
    print()
    print("  Python 3.9 ou superior nao foi encontrado.")
    print()
    if sistema() == "windows":
        print("  Instale em https://python.org/downloads")
        print("  e marque 'Add python.exe to PATH' na primeira tela.")
    elif sistema() == "mac":
        print("  Instale com:  brew install python@3")
        print("  ou baixe em https://python.org/downloads")
    else:
        print("  Debian/Ubuntu :  sudo apt install python3 python3-pip")
        print("  Fedora        :  sudo dnf install python3 python3-pip")
        print("  Arch          :  sudo pacman -S python python-pip")
    print()
    return 1


# ------------------------------------------------------------ dependencias
def falta_selenium():
    try:
        import selenium  # noqa: F401
        return False
    except ImportError:
        return True


def instalar_selenium(python):
    print("  instalando selenium (necessario para o farm pelo navegador)...")
    comandos = [
        [python, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
         "selenium"],
        [python, "-m", "pip", "install", "--quiet", "--user",
         "--disable-pip-version-check", "selenium"],
        [python, "-m", "pip", "install", "--quiet", "--break-system-packages",
         "--disable-pip-version-check", "selenium"],
    ]
    for cmd in comandos:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and not falta_selenium():
                print("  selenium instalado.")
                return True
        except Exception:
            continue
    print("  nao consegui instalar o selenium automaticamente.")
    print("  o farm sem navegador continua funcionando.")
    return False


# ------------------------------------------------------------------ main
def main():
    preparar_terminal()
    titulo("Gambiarra-Infinite")

    if not rodando_no_python_certo():
        exe = procurar_python()
        if not exe:
            return aviso_python()
        os.execv(exe, [exe, os.path.abspath(__file__)] + sys.argv[1:])
        return 0

    if not os.path.isdir(CORE):
        print("  pasta 'core' nao encontrada ao lado do launcher.")
        return 1
    os.chdir(AQUI)

    if falta_selenium():
        instalar_selenium(sys.executable or "python3")

    sys.path.insert(0, CORE)
    alvo = os.path.join(CORE, "main.py")
    if not os.path.isfile(alvo):
        print("  core/main.py nao encontrado.")
        return 1

    # executa o main no mesmo processo para o terminal continuar igual
    import runpy
    runpy.run_path(alvo, run_name="__main__")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        sys.exit(0)
