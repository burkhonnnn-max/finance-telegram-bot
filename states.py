from aiogram.fsm.state import State, StatesGroup


class TransactionState(StatesGroup):
    type = State()       # 'income' yoki 'expense'
    amount = State()     # Summa
    category = State()   # Toifa / Kategoriya
    comment = State()    # Izoh
