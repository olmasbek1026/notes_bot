import asyncio
import logging
import sys
from os import getenv
from typing import List

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.handlers import message
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv
from sqlalchemy import select, insert
from sqlalchemy.orm import query, Session


from models import Base, engine, Note, User
from dotenv import load_dotenv
load_dotenv()

TOKEN = getenv("BOT_TOKEN")
dp = Dispatcher()
session = Session(bind=engine)



def button_menu():
    rkb = ReplyKeyboardBuilder()
    rkb.add(*[
        KeyboardButton(text="Add note"),
        KeyboardButton(text="My Notes"),
        KeyboardButton(text="last note")
    ])
    rkb.adjust(2,1)
    return rkb.as_markup(resize_keyboard = True)

class NoteForm(StatesGroup):
    note = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    query=select(User).where(User.id==message.from_user.id)
    data = list(session.execute(query).scalars())
    if  not data:
        # insert(User).values(id=message.from_user.id, first_name = message.from_user.first_name)
        # session.execute(query)
        query = insert(User).values(
            id=message.from_user.id,
            first_name=message.from_user.first_name
        )
        session.execute(query)
        session.commit()
    btn = button_menu()
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!", reply_markup=btn)

@dp.message(F.text == "Add note")
async def add_note_handler(message: Message, state : FSMContext) -> None:
    await state.set_state(NoteForm.note)
    await message.answer("Eslatma qo'shing")


@dp.message(F.text, NoteForm.note)
async def new_note_handler(message: Message, state : FSMContext) -> None:
    note=message.text
    query = insert(Note).values(note=note, user_id=message.from_user.id)
    session.execute(query)
    session.commit()
    await state.clear()
    btn = button_menu()
    await message.answer("Mofaqiyatli qo'shildi", reply_markup=btn)

@dp.message(F.text == "My Notes")
async def my_note_handler(message: Message, state : FSMContext) -> None:
    query = select(Note).where(Note.user_id==message.from_user.id)
    notes = List(session.execute(query).scalars())
    for note in notes:
        await message.answer(text=note.note)


@dp.message(F.text == "last note")
async def my_note_handler(message: Message, state : FSMContext) -> None:
       query = select(Note).where(Note.user_id==message.from_user.id).order_by("id")
       note = List(session.execute(query).scalars())[-1]
       session.delete(note)
       await message.answer("Note o'chirildi")





async def main() -> None:
    Base.metadata.create_all(engine)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())