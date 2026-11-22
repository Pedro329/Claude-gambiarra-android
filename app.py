import flet as ft
import sys
import threading
import runpy
import os
import shutil

class TelaConsole:
    def __init__(self, controle, page):
        self.controle = controle
        self.page = page
    def write(self, texto):
        self.controle.value += str(texto)
        self.page.update()
    def flush(self):
        pass

def main(page: ft.Page):
    page.title = "Claude infinite"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 15

    console = ft.Text(value="Pronto...\n", font_family="monospace", size=12, selectable=True)
    coluna = ft.Column([console], scroll=ft.ScrollMode.ALWAYS, expand=True)

    def executar(e):
        e.control.disabled = True
        page.update()

        def rodar():
            sys.stdout = TelaConsole(console, page)
            sys.stderr = sys.stdout
            try:
                # 1. Pega o diretório de arquivos que o Android libera para escrita
                # No Flet, a variável de ambiente 'FLET_APP_STORAGE' ou 'ANDROID_DATA' costuma liberar o caminho.
                app_dir = os.path.dirname(os.path.abspath(__file__))
                user_data = os.environ.get("FLET_APP_STORAGE") or os.path.expanduser("~")
                
                alvo_original = os.path.join(app_dir, "core", "main.py")
                alvo_trabalho = os.path.join(user_data, "core", "main.py")
                
                # 2. Copia a pasta 'core' do pacote read-only para a pasta liberada do usuario
                if not os.path.exists(os.path.join(user_data, "core")) and os.path.exists(os.path.join(app_dir, "core")):
                    shutil.copytree(os.path.join(app_dir, "core"), os.path.join(user_data, "core"))
                    print(f"Copiando arquivos internos para: {user_data}\n")

                if os.path.exists(alvo_trabalho):
                    print("--- Iniciando ---\n")
                    # Muda o foco total para a pasta do usuario, que tem permissão de criar a pasta "dados"
                    os.chdir(user_data)
                    if user_data not in sys.path:
                        sys.path.insert(0, user_data)
                    runpy.run_path(alvo_trabalho, run_name="__main__")
                elif os.path.exists(alvo_original):
                    print("--- Rodando em modo Somente Leitura ---\n")
                    os.chdir(app_dir)
                    if app_dir not in sys.path:
                        sys.path.insert(0, app_dir)
                    runpy.run_path(alvo_original, run_name="__main__")
                else:
                    print(f"Erro: O diretorio 'core' nao foi empacotado corretamente!")
            except Exception as ex:
                print(f"\nErro fatal: {ex}")
            finally:
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
                e.control.disabled = False
                page.update()

        threading.Thread(target=rodar, daemon=True).start()

    page.add(
        ft.Text("Claude infinite", size=22, weight=ft.FontWeight.BOLD),
        ft.ElevatedButton("Iniciar", on_click=executar),
        ft.Container(content=coluna, bgcolor="#111111", border_radius=8, padding=10, expand=True)
    )

ft.app(target=main)
