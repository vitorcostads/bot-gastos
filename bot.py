# Importa bibliotecas essenciais
import os
import asyncio
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes
from telegram import Update
from telegram.ext import filters

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Carrega variáveis do .env
from dotenv import load_dotenv
load_dotenv(dotenv_path="tks.env")

# ----------------- CONFIGS DO GOOGLE SHEETS -------------------

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Gastos").worksheet("Conjunto")

# ----------------- CONFIGS DO TELEGRAM -------------------

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Variável TELEGRAM_TOKEN não encontrada. Verifique seu arquivo .env.")

# ----------------- FUNÇÃO PRINCIPAL -------------------

async def registrar_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = update.message.text.strip()
    partes = mensagem.split()

    if len(partes) < 3:
        await update.message.reply_text("Formato inválido. Use: <mês> <ID> <valor> [motivo]\nExemplo: Abril Uber 29,90 Transporte para o trabalho")
        return

    try:
        mes = partes[0].capitalize()
        id_categoria = partes[1]
        valor_str = partes[-1].replace(",", ".")
        valor = float(valor_str)
        motivo = " ".join(partes[2:-1]) if len(partes) > 3 else ""

        linha_header = sheet.row_values(1)
        try:
            col_inicio = linha_header.index(mes) + 1
        except ValueError:
            await update.message.reply_text(f"Mês '{mes}' não encontrado na primeira linha da planilha.")
            return

        col_id = col_inicio
        col_valor = col_inicio + 1
        col_motivo = col_inicio + 2

        col_id_values = sheet.col_values(col_id)
        proxima_linha = len(col_id_values) + 1

        sheet.update_cell(proxima_linha, col_id, id_categoria)
        sheet.update_cell(proxima_linha, col_valor, f"R$ {valor:.2f}")
        if motivo:
            sheet.update_cell(proxima_linha, col_motivo, motivo)

        resposta = f"Gasto registrado em {mes}:\n• ID: {id_categoria}\n• Valor: R$ {valor:.2f}"
        if motivo:
            resposta += f"\n• Motivo: {motivo}"

        await update.message.reply_text(resposta)

    except Exception as e:
        print(f"Erro: {e}")
        await update.message.reply_text("Erro ao registrar gasto. Verifique os dados e tente novamente.")

# ----------------- EXECUÇÃO DO BOT -------------------

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_gasto))

    print("Bot rodando... Ctrl + C para parar.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
