from aiogram.fsm.state import State, StatesGroup


class TransactionState(StatesGroup):
    waiting_input = State()  # Kirim yoki Chiqim tanlangandan so'ng kiritiladigan xabar
    amount = State()         # Summa
    category = State()       # Toifa / Kategoriya
    comment = State()        # Izoh


class PendingEditState(StatesGroup):
    """Vaqtinchalik tranzaksiyani to'g'rilash (Fix) holatlari"""
    edit_amount = State()    # Yangi summani kutish
    edit_comment = State()   # Yangi izohni kutish
