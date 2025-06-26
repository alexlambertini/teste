import win32print

# Nome da impressora (obtenha o nome correto no Painel de Controle)
printer_name = win32print.GetDefaultPrinter()

try:
    # Abre a impressora
    hprinter = win32print.OpenPrinter(printer_name)

    # Inicia um trabalho de impressão
    job = win32print.StartDocPrinter(hprinter, 1, ("Teste de impressão", None, "RAW"))
    win32print.StartPagePrinter(hprinter)

    # Texto com acentuação
    texto = (
        "Teste de impressão com acentuação:\n"
        "Olá, mundo!\n"
        "Acentuação: áéíóúâêîôûãõç\n"
        "Texto em tamanho maior.\n"
    )

    # Comandos ESC/POS para aumentar o tamanho do texto
    comando_tamanho_duplo = b"\x1D\x21\x10"  # Tamanho duplo de altura e largura
    comando_tamanho_normal = b"\x1D\x21\x00"  # Volta ao tamanho normal

    # Envia o texto para a impressora
    win32print.WritePrinter(hprinter, comando_tamanho_duplo)  # Aumenta o tamanho do texto
    win32print.WritePrinter(hprinter, texto.encode("cp860", errors="replace"))
    win32print.WritePrinter(hprinter, comando_tamanho_normal)  # Volta ao tamanho normal

    # Finaliza o trabalho de impressão
    win32print.EndPagePrinter(hprinter)
    win32print.EndDocPrinter(hprinter)
    win32print.ClosePrinter(hprinter)
    print("Impressão realizada com sucesso!")
except Exception as e:
    print(f"Erro ao imprimir: {e}")