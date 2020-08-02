import config
import pyowm
import logging
import telebot as t
from telebot import types
import re
from datetime import datetime
import requests

# Лог событий
# t.logger.setLevel(logging.DEBUG)

# Определяем в библиотеке OpenWeatherApi параметры
owm = pyowm.OWM(config.OWM_API_KEY, config.owm_config)
# Определяем в библиотеке pyTelegramBotAPI параметры
bot = t.TeleBot(config.TELEGRAM_BOT_KEY)
manager = owm.weather_manager()


# Родительский класс обработки текстовых сообщений
class Message(object):
	def __init__(self, text, **options):
		self.text = text
		self.options = options


# Форматируем текстовые сообщения посредством тегов HTML
class HTML(Message):
	def __init__(self, text, **options):
		super(HTML, self).__init__(text, parse_mode="HTML", **options)


# Форматируем текстовые сообщения посредством посредством **, __, ``
class Markdown(Message):
	def __init__(self, text, **options):
		super(Markdown, self).__init__(text, parse_mode='Markdown', **options)


@bot.message_handler(commands=['start'])
def send_message(command):
	# Если пользователь находится в разрешенном списке, то бот приветсвует его.
	if command.from_user.id in config.USERS:
		
		# Добавляем кнопку запроса местоположения
		keyboard = types.ReplyKeyboardMarkup(True, True)
		keyboard.add(types.KeyboardButton('Погода у меня', request_location=True))
		
		# Отправляем приветственное сообщение
		bot.send_message(command.chat.id,
		                 f"""Приветствую Вас, <b>{command.from_user.first_name}</b> !
Я могу рассказать о погоде.
Для этого, нажмите на кнопку "Погода у меня" или просто напишите мне название своего города.

<i>Если пошло что-то не так, пожалуйста напишите моему конструктору</i> => <b>@KOT_B_TPYCAX</b>""",
		                 parse_mode="HTML", reply_markup=keyboard)
	
	# Если пользователь не находится в расзрешенном списке, то бот направлет ему сообщение
	# и направляет сообщение владельцу/администратору бота или тому, кого укажут
	else:
		bot.send_message(command.from_user.id,
		                 f"""Привет, <b>{command.from_user.first_name}</b>!
Я закрыт для публичного использования.
Если Вы хотите мной пользоваться, то напишите моему конструктору => <b>@KOT_B_TPYCAX</b>""",
		                 parse_mode="HTML")
		bot.send_message(config.ADMIN,
		                 f"""Пользователь *{command.from_user.first_name}*,
с ID _{command.from_user.id}_ не входит в список разрешенных""",
		                 parse_mode="Markdown")


# Отдаем погоду по названию города или указанным координатам
@bot.message_handler(content_types=['text', 'location'])
def send_weather(city):
	if city.from_user.id in config.USERS:
		inline_keyboard = types.InlineKeyboardMarkup()
		now_in_city = manager
		data = None
		
		# Обрабатываем ошибки ввода (несуществующие города, опечатки и прочее)
		try:
			
			# Если пользователь ввел название местоположения
			if city.text:
				now_in_city = now_in_city.weather_at_place(city.text)
				data = city.text
			
			# Если пользовователь передал координаты
			elif city.location:
				if city.location is not None:
					now_in_city = now_in_city.weather_at_coords(city.location.latitude, city.location.longitude)
					data = str([city.location.latitude, city.location.longitude])
			inline_keyboard.add(types.InlineKeyboardButton('Прогноз на 3 дня', callback_data=data))
			now_information = [
				{'weather': {'current_weather': now_in_city.weather.detailed_status,
				             'humidity': now_in_city.weather.humidity,
				             'wind': now_in_city.weather.wind('meters_sec')['speed']}},
				{'temp': {'now_temp': int(now_in_city.weather.temperature('celsius')['temp']),
				          'feeling': int(now_in_city.weather.temperature('celsius')['feels_like'])}},
				{'sun': {'sunrise': datetime.fromtimestamp(now_in_city.weather.sunrise_time(
					timeformat='unix')).strftime('%H:%M:%S'),
				         'sunset': datetime.fromtimestamp(now_in_city.weather.sunset_time(
					         timeformat='unix')).strftime('%H:%M:%S')}}
			]
			# Локализуем статусы погоды
			if now_information[0]['weather']['current_weather'] == 'Clouds':
				now_information[0]['weather']['current_weather'] = 'Облачно ☁'
			elif now_information[0]['weather']['current_weather'] == 'Clear':
				now_information[0]['weather']['current_weather'] = 'Ясно ☀'
			elif now_information[0]['weather']['current_weather'] == 'Rain':
				now_information[0]['weather']['current_weather'] = 'Капает дождь ☔'
			elif now_information[0]['weather']['current_weather'] == 'Snow':
				now_information[0]['weather']['current_weather'] = 'Падает снег ❄'
			elif now_information[0]['weather']['current_weather'] == 'Wind':
				now_information[0]['weather']['current_weather'] = 'Ветренно 💨'
			elif now_information[0]['weather']['current_weather'] == 'Fog':
				now_information[0]['weather']['current_weather'] = 'Туман 🌫'
			elif now_information[0]['weather']['current_weather'] == 'Haze':
				now_information[0]['weather']['current_weather'] = 'Мгла 🌚'
			
			# Добавляем мнение о погоде на основе температуры
			opinion = ''
			if now_information[1]['temp']['now_temp'] <= -21:
				opinion = 'очень холодно 🥶'
			elif -20 <= now_information[1]['temp']['now_temp'] <= -16:
				opinion = 'холодно 🧣'
			elif -15 <= now_information[1]['temp']['now_temp'] <= -1:
				opinion = 'зимовато ❄'
			elif 0 <= now_information[1]['temp']['now_temp'] <= 8:
				opinion = 'холодновато'
			elif 9 <= now_information[1]['temp']['now_temp'] <= 12:
				opinion = 'прохладно 😕'
			elif 13 <= now_information[1]['temp']['now_temp'] <= 20:
				opinion = 'хорошо 👍'
			elif 21 <= now_information[1]['temp']['now_temp'] <= 24:
				opinion = 'тепло 🏖'
			elif now_information[1]['temp']['now_temp'] >= 25:
				opinion = 'жара 🔥'
			
			# Отправляем текущую погоду
			bot.send_message(city.chat.id, f"""Здесь {opinion}

ПОГОДНЫЕ УСЛОВИЯ:

На улице: {now_information[0]['weather']['current_weather']}
Влажность: {now_information[0]['weather']['humidity']} % 💦
Скорость ветра: {now_information[0]['weather']['wind']} м/с 🌬

ТЕМПЕРАТУРА:

Сейчас: *{now_information[1]['temp']['now_temp']} ℃*
Чувствуется как: {now_information[1]['temp']['feeling']} ℃

СОЛНЦЕ:

Восход: {now_information[2]['sun']['sunrise']} ↗
Закат: {now_information[2]['sun']['sunset']} ↘""",
			                 parse_mode="Markdown",
			                 reply_to_message_id=city.message_id,
			                 reply_markup=inline_keyboard)
		except Exception as e:
			e = city.text
			bot.send_message(city.chat.id, f"""*{city.from_user.first_name}* , к сожалению, Вы ввели _{e}_ - это
несуществующий город или я его просто не знаю.
Пожалуйста, введите другое или корректное название города.""",
			                 parse_mode="Markdown")
	else:
		bot.send_message(city.from_user.id,
		                 f"""Привет, <b>{city.from_user.first_name}</b>!
Я закрыт для публичного использования.
Если Вы хотите мной пользоваться, то напишите моему конструктору => <b>@KOT_B_TPYCAX</b>""",
		                 parse_mode="HTML")
		bot.send_message(config.ADMIN,
		                 f"""Пользователь *{city.from_user.first_name}*, с ID _{city.from_user.id}_
не входит в список разрешенных""",
		                 parse_mode="Markdown")


# Принимаем, обрабатываем и отдаем прогноз погоды на 3 дня
@bot.callback_query_handler(func=lambda call: True)
def forecast(call):
	forecast_information = []
	
	# Обрабатываем запрос запрос из inline кнопки
	# Если был запрос по координатам, то преобразуем координаты в список вещественных чисел
	if [x for x in call.data if re.findall(r"(\d)|(\.)", x)]:
		data = []
		for coord in re.sub(r"(\[)|(\')|(\])|(,)", "", call.data).split():
			data.append(float(coord))
		
		# Запрашиваем данные по API стандартно через requests без использования библиотеки, т.к. в библиотеке pyowm
		# отсутствует адекватное представление данных
		forecast_url = f'http://api.openweathermap.org/data/2.5/forecast?' \
		               f'lat={data[0]}&lon={data[1]}'
	
	# Иначе, обрабатываем как название местоположения
	else:
		forecast_url = f'http://api.openweathermap.org/data/2.5/forecast?' \
		               f'q={call.data}'
	req = requests.get(forecast_url, params=config.params)
	resp = req.json()['list']
	for item in resp:
		forecast_information.append({'date': datetime.fromtimestamp(item['dt']).strftime('%d.%m.%Y'),
		                             'time': datetime.strptime(item['dt_txt'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M'),
		                             'current_temp': int(item['main']['temp']),
		                             'feeling': int(item['main']['feels_like']),
		                             'humidity': item['main']['humidity'],
		                             'pressure': item['main']['pressure'],
		                             'detailed_status': str(item['weather'][0]['description']).capitalize(),
		                             'speed': item['wind']['speed']})
	
	# Сортируем данные по дате и времени
	sorted_data = sorted(forecast_information,
	                     key=lambda d: (datetime.strptime(d['date'], '%d.%m.%Y'), d['time']))
	
	# Проходимся по отсортированному списку с уловием, что все данные о погоде
	# группируются по дате
	finish_data = set()
	result = ''
	for i in sorted_data:
		if i['date'] not in finish_data:
			result += f"\n\n*{i['date']}* 👈\n"
			finish_data.add(i['date'])
		
		# Добавляем к статусам о погоде иконки
		if i['detailed_status'] == 'Облачно с прояснениями':
			i['detailed_status'] += ' ⛅'
		elif i['detailed_status'] == 'Переменная облачность':
			i['detailed_status'] += ' ☁'
		elif i['detailed_status'] == 'Небольшой дождь':
			i['detailed_status'] += ' 🌧'
		elif i['detailed_status'] == 'Небольшая облачность':
			i['detailed_status'] += ' ☁'
		elif i['detailed_status'] == 'Ясно':
			i['detailed_status'] += ' ☀'
		elif i['detailed_status'] == 'Ясно':
			i['detailed_status'] += ' ☀'
		elif i['detailed_status'] == 'Пасмурно':
			i['detailed_status'] += ' 🌥'
		
		result += f"""\nВремя: {i['time']}
Статус: {i['detailed_status']}
Температура: {str(i['current_temp'])} ℃
Влажность: {i['humidity']} %
Давление: {i['pressure']} мм
Скорость ветра: {i['speed']} м/с
"""
	# Отправляем сообщение с прогнозом погоды на 3 дня, каждые 3 часа
	bot.edit_message_text(chat_id=call.message.chat.id,
	                      text=result,
	                      message_id=call.message.message_id,
	                      parse_mode="Markdown")


# Запуск
if __name__ == '__main__':
	bot.polling(none_stop=True)
