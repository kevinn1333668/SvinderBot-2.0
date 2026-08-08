from aiogram import Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from src.bot.keyboards.reply import sex_selection_horizontal_keyboard, main_menu_keyboard, without_town_keyboard
from src.bot.states import CreateProfileStates, UserRoadmap
from src.repositories.uow import UnitOfWork
from src.schemas.enums import SexEnum
from src.schemas.profile import ProfileCreateDTO
from src.services.profile_service import ProfileService
from src.static.text.texts import TEXT_FEMALE, TEXT_MALE

profile_router = Router()



@profile_router.message(CreateProfileStates.start)
async def profile_start(message: Message, state: FSMContext):
    await message.answer(
        "Введи свой никнейм на сервере",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CreateProfileStates.name)


@profile_router.message(CreateProfileStates.name)
async def profile_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Боюсь ты где-то ошибся, попробуй еще раз", reply_markup=ReplyKeyboardRemove())
        return

    if len(message.text) < 2 or len(message.text) > 64:
        await message.answer("Слишком длинное или короткое имя! Давай по новой..", reply_markup=ReplyKeyboardRemove())
        return

    await state.update_data(name=message.text)
    await message.answer(f"Отлично, {message.text}, теперь твой возраст", reply_markup=ReplyKeyboardRemove())
    await state.set_state(CreateProfileStates.age)


@profile_router.message(CreateProfileStates.age)
async def profile_age(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer(
            "Странный возратс... Это точно число, не могу понять? Давай ещё раз",
            reply_markup = ReplyKeyboardRemove()
        )
        return

    age = int(message.text)
    if age < 14 or age > 67:
        await message.answer(
            "Странный возраст... Подумай ещё",
            reply_markup = ReplyKeyboardRemove()
        )
        return

    await state.update_data(age=age)
    await message.answer(
        f"Отлично, тебе {age}, фиксирую. Теперь укажи, ты парень или девушка?",
        reply_markup = sex_selection_horizontal_keyboard(),
    )
    await state.set_state(CreateProfileStates.sex)


@profile_router.message(CreateProfileStates.sex)
async def profile_sex(message: Message, state: FSMContext):
    if message.text not in (TEXT_FEMALE, TEXT_MALE):
        await message.answer(
            "Боюсь ты где-то ошибся, попробуй еще раз",
            reply_markup=sex_selection_horizontal_keyboard(),
        )
        return

    sex = SexEnum.FEMALE if message.text == TEXT_FEMALE else SexEnum.MALE
    await state.update_data(sex=sex.value)
    await message.answer(
        "Записал. Теперь скажи свой город на сервре",
        reply_markup=without_town_keyboard()
    )
    await state.set_state(CreateProfileStates.town)

@profile_router.message(CreateProfileStates.town)
async def profile_town(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Боюсь ты где-то ошибся, попробуй еще раз", reply_markup=ReplyKeyboardRemove())
        return

    if len(message.text) < 2 or len(message.text) > 30:
        await message.answer("Города такой длины не существует, попробуй ещё раз")
        return

    await state.update_data(town=message.text)
    await message.answer(
        "Напиши о себе: хобби, интересы и увлечения на сервере (реальные данные по желанию)",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(CreateProfileStates.description)


@profile_router.message(CreateProfileStates.description)
async def profile_description(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Боюсь ты где-то ошибся, попробуй еще раз", reply_markup=ReplyKeyboardRemove())
        return

    await state.update_data(description=message.text)
    await message.answer(
        "Последний этап! Отправь одно фото себя (своего скина) на СЕРВЕРЕ для своей анкеты.\n\n"
        "Любые другие фото приведут к удалению анкеты и блокировке аккаунта\n"
        "Если бот завис после отправки фото - /start",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(CreateProfileStates.photo)


@profile_router.message(CreateProfileStates.photo)
async def profile_photo(message: Message, state: FSMContext, bot: Bot, uow: UnitOfWork):
    if not message.photo:
        await message.answer("Вряд ли это фотка! Попробуй еще раз", reply_markup=ReplyKeyboardRemove())
        return

    file_id = message.photo[-1].file_id
    data = await state.get_data()

    profile_service = ProfileService(uow)

    create_dto = ProfileCreateDTO(
        tg_id=message.from_user.id,
        name=data["name"],
        age=data["age"],
        sex=data["sex"],
        town=data["town"],
        description=data["description"],
        s3_path=file_id,
    )

    profile = await profile_service.create_profile(create_dto)

    if profile is None:
        await message.answer(
            "У тебя уже есть анкета. Используй /edit_profile, чтобы её изменить.",
            reply_markup=main_menu_keyboard(),
        )
        await state.set_state(UserRoadmap.main_menu)
        return

    await message.answer_photo(
        photo=file_id,
        caption=f"Анкета создана.\n{profile.name}, {profile.age}, {profile.town}\n{profile.description}",
        reply_markup=main_menu_keyboard(),
    )
    await state.set_state(UserRoadmap.main_menu)

