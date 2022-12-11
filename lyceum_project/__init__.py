import sqlite3


db = sqlite3.connect("main.db")
cur = db.cursor()

Dict = {None: [None, 0]}
omega_secret = 'omega_secret_salt_for_hash_to_be_very_strong'

def normal_value(size: int):
    """
    :param size: Кол-во байтов
    :return: tuple(float, str) -> перевод введённого кол-ва байтов в максимально возможные единицы информации
    """
    types = ["Б", "КБ", "МБ", "ГБ", "ТБ"]
    st = 0

    while size // 1024:
        size /= 1024
        st += 1

    return size, types[st]