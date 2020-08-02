from pyowm.utils.config import get_default_config

# Ключ телеграм бота
TELEGRAM_BOT_KEY = 'API key'

# Ключ OpenWeatherMap
OWM_API_KEY = 'API key'

# Параметры при get запросе к API OpenWeatherMap
params = {
	'units': 'metric',
	'lang': 'ru',
	'cnt': '24',
	'appid': OWM_API_KEY
}

# ID пользователей, которые могут пользоваться ботом. Опционально.
USERS = [931471202, 454443373, 345336993, 730035455]

# ID администратора бота, для получения уведомлений
ADMIN = 454443373

# Изменение дефолтной конфигурации в библиотеке pyowm
owm_config = get_default_config()
owm_config['language'] = 'ru'
