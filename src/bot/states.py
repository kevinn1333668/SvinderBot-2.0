from aiogram.fsm.state import StatesGroup, State


class UserRoadmap(StatesGroup):
    start = State()
    get_token = State()
    check_token = State()
    main_menu = State()
    llm_chat = State()


class SearchProfileStates(StatesGroup):
    start = State()
    viewing_profile = State()


class CreateProfileStates(StatesGroup):
    start = State()
    name = State()
    age = State()
    sex = State()
    town = State()
    description = State()
    photo = State()


class EditProfileStates(StatesGroup):
    start = State()
    name = State()
    age = State()
    sex = State()
    town = State()
    description = State()
    photo = State()


class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_advertisement = State()


class ViewLikesStates(StatesGroup):
    choose_view_type = State()
    viewing_pending_likes = State()
    viewing_accepted_likes = State()