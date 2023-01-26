from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

from config import Config, load_config


config: Config = load_config()
BOT_TOKEN: str = config.tg_bot.token

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
storage: MemoryStorage = MemoryStorage()

# Создаем объекты бота и диспетчера
bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher(bot, storage=storage)

# Создаем "базу данных" пользователей
user_dict: dict[int, dict[str, str | int]] = {}


# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMFillForm(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    fill_name = State()        # Состояние ожидания ввода имени
    fill_age = State()         # Состояние ожидания ввода возраста
    fill_gender = State()      # Состояние ожидания выбора пола
    upload_photo = State()     # Состояние ожидания загрузки фото
    fill_education = State()   # Состояние ожидания выбора образования
    fill_wish_news = State()   # Состояние ожидания выбора получать ли новости


# Этот хэндлер будет срабатывать на команду /start
# и предлагать перейти к заполнению анкеты,
# отправив команду /fillform
async def process_start_command(message: Message):
    await message.answer(text='Этот бот демонстрирует работу FSM\n\n'
                              'Чтобы перейти к заполнению анкеты - '
                              'отправьте команду /fillform')


# Этот хэндлер будет срабатывать на команду /fillform
# и переводить бота в состояние ожидания ввода имени
async def process_fillform_command(message: Message):
    await message.answer(text='Пожалуйста, введите ваше имя')
    # Устанавливаем состояние ожидания ввода имени
    await FSMFillForm.fill_name.set()


# Этот хэндлер будет срабатывать, если во время ввода имени
# будет введено что-то некорректное
async def warning_not_name(message: Message):
    await message.answer(text='То, что вы отправили не похоже на имя\n\n'
                              'Пожалуйста, введите ваше имя\n\n'
                              'Если вы хотите прервать заполнение анкеты - '
                              'отправьте команду /cancel')


# Этот хэндлер будет срабатывать, если введено корректное имя
# и переводить в состояние ожидания ввода возраста
async def process_name_sent(message: Message, state: FSMContext):
    # C помощью менеджера контекста сохраняем введенное имя
    # в хранилище по ключу "name"
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer(text='Спасибо!\n\nА теперь введите ваш возраст')
    # Устанавливаем состояние ожидания ввода возраста
    await FSMFillForm.fill_age.set()


# Этот хэндлер будет срабатывать, если во время ввода возраста
# будет введено что-то некорректное
async def warning_not_age(message: Message):
    await message.answer(
        text='Возраст должен быть целым числом от 4 до 120\n\n'
        'Попробуйте еще раз\n\nЕсли вы хотите прервать '
        'заполнение анкеты - отправьте команду /cancel')


# Этот хэндлер будет срабатывать, если введен корректный возраст
# и переводить в состояние выбора пола
async def process_age_sent(message: Message, state: FSMContext):
    # C помощью менеджера контекста сохраняем возраст
    # в хранилище по ключу "age"
    async with state.proxy() as data:
        data['age'] = int(message.text)
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup()
    # Создаем объекты инлайн-кнопок
    male_button = InlineKeyboardButton(text='Мужской ♂',
                                       callback_data='male')
    female_button = InlineKeyboardButton(text='Женский ♀',
                                         callback_data='female')
    undefined_button = InlineKeyboardButton(text='🤷 Пока не ясно',
                                            callback_data='undefined_gender')
    # Добавляем кнопки в клавиатуру (две в одном ряду и одну в другом)
    markup.add(male_button, female_button).add(undefined_button)
    # Отправляем пользователю сообщение с клавиатурой
    await message.answer(text='Спасибо!\n\nУкажите ваш пол',
                         reply_markup=markup)
    # Устанавливаем состояние ожидания выбора пола
    await FSMFillForm.fill_gender.set()


# Этот хэндлер будет срабатывать, если во время выбора пола
# будет введено/отправлено что-то некорректное
async def warning_not_gender(message: Message):
    await message.answer(text='Пожалуйста, пользуйтесь кнопками '
                              'при выборе пола\n\nЕсли вы хотите прервать '
                              'заполнение анкеты - отправьте команду /cancel')


# Этот хэндлер будет срабатывать на нажатие кнопки при
# выборе пола и переводить в состояние отправки фото
async def process_gender_press(callback: CallbackQuery, state: FSMContext):
    # C помощью менеджера контекста сохраняем пол (callback.data нажатой
    # кнопки) в хранилище, по ключу "gender"
    async with state.proxy() as data:
        data['gender'] = callback.data
    # Удаляем сообщение с кнопками, потому что следующий этап - загрузка фото
    # чтобы у пользователя не было желания тыкать кнопки
    await callback.message.delete()
    await callback.message.answer(text='Спасибо! А теперь загрузите, '
                                       'пожалуйста, ваше фото')
    # Устанавливаем состояние ожидания загрузки фото
    await FSMFillForm.upload_photo.set()


# Этот хэндлер будет срабатывать, если во время отправки фото
# будет введено/отправлено что-то некорректное
async def warning_not_photo(message: Message):
    await message.answer(text='Пожалуйста, на этом шаге отправьте '
                              'ваше фото\n\nЕсли вы хотите прервать '
                              'заполнение анкеты - отправьте команду /cancel')


# Этот хэндлер будет срабатывать, если отправлено фото
# и переводить в состояние выбора образования
async def process_photo_sent(message: Message, state: FSMContext):
    # C помощью менеджера контекста сохраняем данные фото (file_unique_id
    # и file_id) в хранилище по ключам "photo_unique_id" и "photo_id"
    async with state.proxy() as data:
        data['photo_unique_id'] = message.photo[0].file_unique_id
        data['photo_id'] = message.photo[0].file_id
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup()
    # Создаем объекты инлайн-кнопок
    secondary_button = InlineKeyboardButton(text='Среднее',
                                            callback_data='secondary')
    higher_button = InlineKeyboardButton(text='Высшее',
                                         callback_data='higher')
    no_edu_button = InlineKeyboardButton(text='🤷 Нету',
                                         callback_data='no_edu')
    # Добавляем кнопки в клавиатуру (две в одном ряду и одну в другом)
    markup.add(secondary_button, higher_button).add(no_edu_button)
    # Отправляем пользователю сообщение с клавиатурой
    await message.answer(text='Спасибо!\n\nУкажите ваше образование',
                         reply_markup=markup)
    # Устанавливаем состояние ожидания выбора образования
    await FSMFillForm.fill_education.set()


# Этот хэндлер будет срабатывать, если во время выбора образования
# будет введено/отправлено что-то некорректное
async def warning_not_education(message: Message):
    await message.answer(text='Пожалуйста, пользуйтесь кнопками '
                              'при выборе образования\n\nЕсли вы хотите '
                              'прервать заполнение анкеты - отправьте '
                              'команду /cancel')


# Этот хэндлер будет срабатывать, если выбрано образование
# и переводить в состояние согласия получать новости
async def process_education_press(callback: CallbackQuery, state: FSMContext):
    # C помощью менеджера контекста сохраняем данные об
    # образовании по ключу "education"
    async with state.proxy() as data:
        data['education'] = callback.data
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup()
    # Создаем объекты инлайн-кнопок
    yes_news_button = InlineKeyboardButton(text='Да',
                                           callback_data='yes_news')
    no_news_button = InlineKeyboardButton(text='Нет, спасибо',
                                          callback_data='no_news')
    # Добавляем кнопки в клавиатуру в один ряд
    markup.add(yes_news_button, no_news_button)
    # Редактируем предыдущее сообщение с кнопками, отправляя
    # новый текст и новую клавиатуру
    await callback.message.edit_text(text='Спасибо!\n\n'
                                          'Остался последний шаг.\n'
                                          'Хотели бы вы получать новости?',
                                     reply_markup=markup)
    # Устанавливаем состояние ожидания выбора получать новости или нет
    await FSMFillForm.fill_wish_news.set()


# Этот хэндлер будет срабатывать, если во время согласия на получение
# новостей будет введено/отправлено что-то некорректное
async def warning_not_wish_news(message: Message):
    await message.answer(text='Пожалуйста, воспользуйтесь кнопками!\n\n'
                              'Если вы хотите прервать заполнение анкеты - '
                              'отправьте команду /cancel')


# Этот хэндлер будет срабатывать на выбор получать или
# не получать новости и выводить из машины состояний
async def process_wish_news_press(callback: CallbackQuery, state: FSMContext):
    # C помощью менеджера контекста сохраняем данные о
    # получении новостей по ключу "wish_news"
    async with state.proxy() as data:
        if callback.message.text == 'yes_news':
            data['wish_news'] = True
        else:
            data['wish_news'] = False
    # Добавляем в "базу данных" анкету пользователя
    # по ключу id пользователя
    print(await state.get_data()['gender'])
    user_dict[callback.from_user.id] = await state.get_data()
    # Завершаем машину состояний
    await state.finish()
    # Отправляем в чат сообщение о выходе из машины состояний
    await callback.message.edit_text(text='Спасибо! Ваши данные сохранены!\n\n'
                                          'Вы вышли из машины состояний')
    # Отправляем в чат сообщение с предложением посмотреть свою анкету
    await callback.message.answer(text='Чтобы посмотреть данные вашей '
                                       'анкеты - отправьте команду /showdata')


# Этот хэндлер будет срабатывать на отправку команды /showdata
# и отправлять в чат данные анкеты, либо сообщение об отсутствии данных
async def process_showdata_command(message: Message):
    # Отправляем пользователю анкету, если она есть в "базе данных"
    if message.from_user.id in user_dict:
        await message.answer_photo(
            photo=user_dict[message.from_user.id]['photo_id'],
            caption=f'Имя: {user_dict[message.from_user.id]["name"]}\n'
                    f'Возраст: {user_dict[message.from_user.id]["age"]}\n'
                    f'Пол: {user_dict[message.from_user.id]["gender"]}\n'
                    f'Образование: {user_dict[message.from_user.id]["education"]}\n'
                    f'Получать новости: {user_dict[message.from_user.id]["wish_news"]}')
    else:
        # Если анкеты пользователя в базе нет - предлагаем заполнить
        await message.answer(text='Вы еще не заполняли анкету. '
                                  'Чтобы приступить - отправьте '
                                  'команду /fillform')


# Этот хэндлер будет срабатывать на команду "/cancel"
# и отключать машину состояний
async def process_cancel_command(message: Message, state: FSMContext):
    await message.answer(text='Вы вышли из машины состояний\n\n'
                              'Чтобы снова перейти к заполнению анкеты - '
                              'отправьте команду /fillform')
    # Сбрасываем состояние
    await state.reset_state()


# Этот хэндлер будет срабатывать на любые сообщения, кроме тех
# для которых есть отдельные хэндлеры, вне состояний
async def send_echo(message: Message):
    await message.reply(text='Извините, моя твоя не понимать')


# Регистрируем хэндлеры
dp.register_message_handler(process_start_command,
                            commands='start')
dp.register_message_handler(process_fillform_command,
                            commands='fillform')
dp.register_message_handler(process_cancel_command,
                            commands='cancel',
                            state='*')
dp.register_message_handler(process_showdata_command,
                            commands='showdata')

dp.register_message_handler(process_name_sent,
                            lambda x: x.text.isalpha(),
                            state=FSMFillForm.fill_name)
dp.register_message_handler(warning_not_name,
                            content_types='any',
                            state=FSMFillForm.fill_name)

dp.register_message_handler(
    process_age_sent,
    lambda x: x.text.isdigit() and 4 <= int(x.text) <= 120,
    state=FSMFillForm.fill_age)
dp.register_message_handler(warning_not_age,
                            content_types='any',
                            state=FSMFillForm.fill_age)

dp.register_callback_query_handler(process_gender_press,
                                   text=['male', 'female', 'undefined_gender'],
                                   state=FSMFillForm.fill_gender)
dp.register_message_handler(warning_not_gender,
                            content_types='any',
                            state=FSMFillForm.fill_gender)

dp.register_message_handler(process_photo_sent,
                            content_types='photo',
                            state=FSMFillForm.upload_photo)
dp.register_message_handler(warning_not_photo,
                            content_types='any',
                            state=FSMFillForm.upload_photo)

dp.register_callback_query_handler(process_education_press,
                                   text=['secondary', 'higher', 'no_edu'],
                                   state=FSMFillForm.fill_education)
dp.register_message_handler(warning_not_education,
                            content_types='any',
                            state=FSMFillForm.fill_education)

dp.register_callback_query_handler(process_wish_news_press,
                                   text=['yes_news', 'no_news'],
                                   state=FSMFillForm.fill_wish_news)
dp.register_message_handler(warning_not_wish_news,
                            content_types='any',
                            state=FSMFillForm.fill_wish_news)
dp.register_message_handler(send_echo, content_types='any')


# Запускаем поллинг
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
