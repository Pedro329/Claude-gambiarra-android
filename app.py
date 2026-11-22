import flet as ft
import sys
import threading
import runpy
import os

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
            # Redireciona os "prints" do seu código original para a tela do app
            sys.stdout = TelaConsole(console, page)
            sys.stderr = sys.stdout
            try:
                if os.path.exists("core/main.py"):
                    print("--- Iniciando ---\n")
                    runpy.run_path("core/main.py", run_name="__main__")
                else:
                    print("Erro: core/main.py não encontrado na pasta!")
            except Exception as ex:
                print(f"\nErro fatal: {ex}")
            finally:
                # Devolve o print para o sistema normal ao terminar
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
