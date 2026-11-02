import os
import cv2
import numpy as np
import telebot

# Ambil token dari tetapan pelayan Render (Environment Variables)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

memory_zon = {}


@bot.message_handler(content_types=["photo"])
def handle_screenshot(message):
  try:
    chat_id = message.chat.id
    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)

    image_path = "screenshot_carta.jpg"
    with open(image_path, "wb") as new_file:
      new_file.write(downloaded_file)

    img = cv2.imread(image_path)
    if img is None:
      bot.reply_to(message, "❌ Ralat: Gagal membaca imej.")
      return

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 100, 100])
    upper_green = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    row_sums = np.sum(mask > 0, axis=1)
    garisan_y = np.where(row_sums > 50)[0]

    if len(garisan_y) > 0:
      groups = np.split(garisan_y, np.where(np.diff(garisan_y) > 5)[0] + 1)
      peak_groups = [int(np.mean(g)) for g in groups if len(g) > 5]

      if len(peak_groups) >= 2:
        y_atas = min(peak_groups)
        y_bawah = max(peak_groups)

        harga_atas = 3883.91
        harga_bawah = 3875.09
        beza_piksel = abs(y_bawah - y_atas)
        beza_harga = abs(harga_atas - harga_bawah)

        if beza_piksel > 0:
          nilai_per_piksel = beza_harga / beza_piksel
          pips = beza_piksel * nilai_per_piksel * 10

          memory_zon[chat_id] = {
              "peak": harga_atas,
              "trough": harga_bawah,
              "pips": pips,
          }

          respon = (
              f"🎯 **Analisis Swap Zone (Render)**\n\n"
              f"🔴 **Garisan Atas** : `{harga_atas}`\n"
              f"🟢 **Garisan Bawah** : `{harga_bawah}`\n"
              f"📏 **Jarak Keseluruhan** : `{pips:.1f} Pips`\n\n"
              f"💾 *Zon tersimpan dalam memori bot!*"
          )
          bot.reply_to(message, respon, parse_mode="Markdown")
        else:
          bot.reply_to(message, "⚠️ Jarak garisan hijau terlalu rapat.")
      else:
        bot.reply_to(
            message,
            "⚠️ Sila pastikan anda melukis dua garisan hijau yang jelas.",
        )
    else:
      bot.reply_to(message, "⚠️ Tiada garisan hijau dikesan pada carta.")

  except Exception as e:
    bot.reply_to(message, f"❌ Ralat Sistem: {str(e)}")


@bot.message_handler(commands=["semak", "zone"])
def semak_memori(message):
  chat_id = message.chat.id
  if chat_id in memory_zon:
    zone = memory_zon[chat_id]
    bot.reply_to(
        message,
        f"📋 **Swap Zone Tersimpan**:\n\n"
        f"🔴 Rujukan Atas  : {zone['peak']}\n"
        f"🟢 Rujukan Bawah : {zone['trough']}\n"
        f"📏 Jarak Pips    : {zone['pips']:.1f} Pips",
        parse_mode="Markdown",
    )
  else:
    bot.reply_to(
        message,
        "⚠️ Tiada memori zon tersimpan. Sila hantar screenshot carta dahulu.",
    )


print("🤖 Bot Render sedang beroperasi...")
bot.infinity_polling()

