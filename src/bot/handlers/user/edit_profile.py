from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from src.bot.keyboards.reply import main_menu_keyboard, skip_keyboard, sex_selection_horizontal_keyboard_with_skip
from src.bot.states import EditProfileStates, UserRoadmap
from src.repositories.uow import UnitOfWork
from src.schemas.enums import SexEnum
from src.schemas.profile import ProfileUpdateDTO
from src.services.profile_service import ProfileService
from src.static.text.texts import TEXT_SKIP_BUTTON, TEXT_FEMALE, TEXT_MALE

edit_router = Router()


@edit_router.message(EditProfileStates.start)
async def edit_profile_start(message: Message, state: FSMContext, uow: UnitOfWork):
    profile_service = ProfileService(uow)
    profile = await profile_service.get_profile_by_tg_id(message.from_user.id)

    if profile is None:
        await message.answer(
            "Сначала нужно создать анкету...",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()
        return
    await state.update_data(
        original_name=profile.name,
        original_age=profile.age,
        original_sex=profile.sex.value,
        original_town=profile.town,
        original_description=profile.description,
        original_s3_path=profile.s3_path,
    )

    await message.answer(
        f"Начинаем редактирование. Текущее имя: {profile.name}. Введите новое или нажмите 'Оставить как есть'.",
        reply_markup=skip_keyboard()
    )
    await state.set_state(EditProfileStates.name)


@edit_router.message(EditProfileStates.name)
async def edit_profile_name(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text == TEXT_SKIP_BUTTON:
        await state.update_data(name=data["original_name"])
    elif not message.text:
        await message.answer(
            "Это не похоже на имя. Попробуй еще раз или оставь как есть.",
                reply_markup=skip_keyboard()
        )
        return
    elif len(message.text) < 2 or len(message.text) > 64:
        await message.answer("Слишком длинное или короткое имя! Давай по новой или оставь как есть.", reply_markup=skip_keyboard())
        return
    else:
        await state.update_data(name=message.text)

    updated_data = await state.get_data()
    await message.answer(
        f"Текущий возраст: {data['original_age']}. Введите новый или оставьте как есть.",
        reply_markup=skip_keyboard()
    )
    await state.set_state(EditProfileStates.age)


@edit_router.message(EditProfileStates.age)
async def edit_profile_age(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text == TEXT_SKIP_BUTTON:
        await state.update_data(age=data["original_age"])
    elif not message.text or not message.text.isdigit():
        await message.answer(
            "Это точно число? Попробуй еще раз или оставь как есть.",
            reply_markup=skip_keyboard()
        )
        return
    elif int(message.text) < 14 or int(message.text) > 67:
        await message.answer(
            "Странный возраст... Подумай еще или оставь как есть.",
            reply_markup=skip_keyboard()
        )
        return
    else:
        await state.update_data(age=int(message.text))

    updated_data = await state.get_data()
    await message.answer(
        f"Текущий пол: {data['original_sex']}. Выберите новый или оставьте как есть.",
        reply_markup=sex_selection_horizontal_keyboard_with_skip()
    )
    await state.set_state(EditProfileStates.sex)


@edit_router.message(EditProfileStates.sex)
async def edit_profile_sex(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text == TEXT_SKIP_BUTTON:
        await state.update_data(sex=data["original_sex"])

    elif message.text not in [TEXT_FEMALE, TEXT_MALE]:
        await message.answer(
            "Выберите пол из предложенных или оставьте как есть.",
                reply_markup=sex_selection_horizontal_keyboard_with_skip())
        return

    else:
        sex = SexEnum.FEMALE if message.text == TEXT_FEMALE else SexEnum.MALE
        await state.update_data(sex=sex.value)


    await message.answer(
        f"Текущий город: {data['original_town']}. "
        f"Введите новый или оставьте как есть.",
        reply_markup=skip_keyboard(),
    )
    await state.set_state(EditProfileStates.town)


@edit_router.message(EditProfileStates.town)
async def edit_profile_town(message: Message, state: FSMContext):
    data = await state.get_data()

    if len(message.text) < 2 or len(message.text) > 100:
        await message.answer("Города такой длины не существует, попробуй ещё раз")
        return

    if message.text == TEXT_SKIP_BUTTON:
        await state.update_data(town=data["original_town"])
    else:
        await state.update_data(town=message.text)


    await message.answer(
        f"Текущее описание: \"{data['original_description']}\". Напишите новое или оставьте как есть.",
        reply_markup=skip_keyboard()
    )
    await state.set_state(EditProfileStates.description)


@edit_router.message(EditProfileStates.description)
async def edit_profile_description(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text == TEXT_SKIP_BUTTON:
        await state.update_data(description=data["original_description"])
    elif not message.text:
        await message.answer("Пустое описание? Попробуйте еще раз или оставьте как есть.", reply_markup=skip_keyboard())
        return
    else:
        await state.update_data(description=message.text)

    await message.answer(
        f"Текущее фото: (отправлю его следующим сообщением, если есть).\nОтправьте новое фото или нажмите 'Оставить как есть'.",
        reply_markup=skip_keyboard()
    )

    if data.get("original_s3_path"):
        try:
            original_photo = data.get("original_s3_path")
            await message.answer_photo(photo=original_photo, caption="Текущее фото.")
        except TelegramBadRequest as e:
            print(f"Error sending original photo: {e}")
            await message.answer("Не удалось загрузить текущее фото.")

    await state.set_state(EditProfileStates.photo)


@edit_router.message(EditProfileStates.photo)
async def edit_profile_photo(message: Message, state: FSMContext, uow: UnitOfWork):
    data = await state.get_data()
    s3_path = data.get("original_s3_path")

    if message.text == TEXT_SKIP_BUTTON:
        file_id = s3_path
    elif not message.photo:
        await message.answer("Это не фото. Отправьте фото или оставьте старое.", reply_markup=skip_keyboard())
        return
    else:
        file_id = message.photo[-1].file_id

    await state.update_data(s3_path=file_id)

    updated_data = await state.get_data()
    try:
        profile_updated_schema = ProfileUpdateDTO(
            name=updated_data["name"],
            age=updated_data["age"],
            sex=updated_data["sex"],
            town=updated_data["town"],
            description=updated_data["description"],
            s3_path=updated_data["s3_path"],
        )
    except ValidationError:
        await message.answer(
            "Что-то из введённых данных не подходит. Попробуйте пройти редактирование заново.",
            reply_markup=main_menu_keyboard(),
        )
        await state.set_state(UserRoadmap.main_menu)
        return

    profile_service = ProfileService(uow)


    try:
        updated = await profile_service.update_profile(message.from_user.id, profile_updated_schema)
        if updated is None:
            await message.answer("Не удалось найти анкету для обновления. Попробуйте /start.")
            return
    except SQLAlchemyError as e:
        print(f"ERROR during profile photo edit: {e}")
        await message.answer(
            f"Хмм, странно... Что-то нехорошее произошло...",
            reply_markup=main_menu_keyboard()
        )
        await state.set_state(UserRoadmap.main_menu)
        return

    caption_text = (
        f"Анкета обновлена!\n"
        f"Имя: {updated.name}\n"
        f"Возраст: {updated.age}\n"
        f"Пол: {updated.sex.value}\n"
        f"Город: {updated.town}\n"
        f"Описание: {updated.description}"
    )

    if updated_data["s3_path"]:
        try:
            final_profile_image = updated_data["s3_path"]
            await message.answer_photo(
                photo=final_profile_image,
                caption=caption_text,
                reply_markup=main_menu_keyboard(),
            )
        except Exception as e:
            print(f"Error sending final photo: {e}")
            await message.answer(caption_text + "\n\n(Не удалось загрузить фото для показа)",
                                 reply_markup=main_menu_keyboard())
    else:
        await message.answer(caption_text + "\n\n(Фото не установлено)", reply_markup=main_menu_keyboard())

    await state.clear()
    await state.set_state(UserRoadmap.main_menu)
