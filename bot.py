import telebot

# Замени 'ТВОЙ_ТОКЕН' на токен от @BotFather
API_TOKEN = 8107805210:AAEXO1hsM6juHVrFoIYpicenlFy_mGrrIl4

bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Твоя игра скоро будет готова. Бот работает!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ты написал: {message.text}")

bot.infinity_polling()
  
