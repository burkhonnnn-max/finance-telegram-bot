# 💰 Shaxsiy Moliya va Kirim-Chiqim Telegram Boti

Ushbu bot shaxsiy harajat va daromadlarni hisoblab borish, statistika yuritish va oylik/haftalik moliyaviy hisobotlarni ko'rish uchun mo'ljallangan.

---

## 🚀 Ishga tushirish bo'yicha ko'rsatma

### 1. Telegram'dan Bot Token olish:
1. Telegram qidiruvidan [@BotFather](https://t.me/BotFather) ni toping va `/start` bosing.
2. `/newbot` buyrug'ini yuboring.
3. Botingizga nom (masalan: `Mening Hisobchim`) va username (masalan: `mening_hisobchim_bot`) bering.
4. BotFather sizga **API Token** beradi (masalan: `7123456789:AAH...`).

### 2. Tokenni kiritish:
Loyihaning ildiz papkasidagi `.env` faylini oching va tokenni yozing:
```env
BOT_TOKEN=bu_yerga_botfatherdan_olingan_tokenni_yozing
```

### 3. Botni ishga tushirish:
- **Usul 1:** `start_bot.bat` fayliga sichqoncha bilan 2 marta bosing.
- **Usul 2:** Terminalda quyidagi buyruqni bering:
```bash
.\.venv\Scripts\python.exe main.py
```

---

## ✨ Imkoniyatlar va Funksiyalar

1. **➕ Kirim qo'shish va ➖ Chiqim qo'shish:**
   - Tugmalar orqali bosqichma-bosqich: Summa -> Toifa tanlash -> Izoh kiritish.
2. **⚡️ Tezkor yozuvlar (Eng qulayi!):**
   Hech qanday menyuga kirmasdan, botga to'g'ridan-to'g'ri xabar yuborish:
   - `-15000 tushlik` *(15 000 so'm ovqat chiqimi)*
   - `-25k taxi` *(25 000 so'm transport chiqimi)*
   - `+500000 oylik` *(500 000 so'm daromad)*
   - `+100k frilans` *(100 000 so'm biznes daromadi)*
3. **💰 Mening balansim:**
   - Jami kirim, jami chiqim va hamyondagi sof foyda/jamg'armani ko'rsatadi.
4. **📊 Statistika & Hisobot:**
   - Bugun, kecha, oxirgi 7 kun, shu oy yoki o'tgan oy bo'yicha hisobot.
   - Har bir toifa bo'yicha foizlar va vizual chiziqlar (diagramma).
5. **🕒 Oxirgi amallar:**
   - Oxirgi 8 ta tranzaksiyani ko'rish va xato kiritilgan bo'lsa darhol bitta tugma orqali o'chirib tashlash.
