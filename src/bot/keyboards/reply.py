from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from src.static.text.texts import (
    TEXT_MALE, TEXT_FEMALE, TEXT_YES, TEXT_SEARCH_PROFILES, TEXT_EDIT_PROFILE, TEXT_MY_PROFILE, TEXT_MY_LIKES,
    TEXT_FILTER_SEX, TEXT_DELETE_PROFILE, TEXT_SKIP_BUTTON
)


def welcome_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Начать")]
        ],
        resize_keyboard=True,
    )


def understand_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Понял!")]
        ],
        resize_keyboard=True,
    )


def go_to_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Перейти в главное меню")]
        ],
        resize_keyboard=True,
    )


def sex_selection_vertical_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXT_MALE)],
            [KeyboardButton(text=TEXT_FEMALE)],
        ],
        resize_keyboard=True,
    )


def sex_selection_horizontal_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
                KeyboardButton(text=TEXT_MALE),
                KeyboardButton(text=TEXT_FEMALE)
        ]],
        resize_keyboard=True,
    )


def yes_or_no_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
                KeyboardButton(text=TEXT_YES),
        ]],
        resize_keyboard=True,
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXT_SEARCH_PROFILES), KeyboardButton(text=TEXT_EDIT_PROFILE)],
            [KeyboardButton(text=TEXT_MY_LIKES), KeyboardButton(text=TEXT_MY_PROFILE)],
            [KeyboardButton(text=TEXT_FILTER_SEX)],
            [KeyboardButton(text=TEXT_DELETE_PROFILE)],
        ],
        resize_keyboard=True,
    )


def skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=TEXT_SKIP_BUTTON)]],
        resize_keyboard=True,
        one_time_keyboard=True
        )


def sex_selection_horizontal_keyboard_with_skip() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXT_MALE), KeyboardButton(text=TEXT_FEMALE)],
            [KeyboardButton(text=TEXT_SKIP_BUTTON)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
