
from database import db


Dict = {None: [None, 0]}

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