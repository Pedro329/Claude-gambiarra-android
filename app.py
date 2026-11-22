import flet as ft
import subprocess
import threading

def main(page: ft.Page):
    page.title = "Gambiarra-Infinite"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 15

    console = ft.Text(value="Pronto para iniciar...\n", font_family="monospace", size=12, selectable=True)
    coluna_log = ft.Column([console], scroll=ft.ScrollMode.ALWAYS, expand=True)

    def executar_core(e):
        btn_iniciar.disabled = True
        console.value += "\n--- Iniciando ---\n"
        page.update()

        def rodar():
            processo = subprocess.Popen(["python", "-u", "core/main.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for linha in processo.stdout:
                console.value += linha
                page.update()
            btn_iniciar.disabled = False
            console.value += "\n--- Finalizado ---\n"
            page.update()

        threading.Thread(target=rodar, daemon=True).start()

    btn_iniciar = ft.ElevatedButton("Iniciar", on_click=executar_core)
    page.add(ft.Text("Gambiarra-Infinite", size=22, weight=ft.FontWeight.BOLD), btn_iniciar, ft.Container(content=coluna_log, bgcolor="#111111", border_radius=8, padding=10, expand=True))

ft.app(target=main)
