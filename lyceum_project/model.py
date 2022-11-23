import os
import sys
import datetime
from string import ascii_uppercase

import psutil
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QTreeWidgetItem, QProgressBar, QFileIconProvider

from lyceum_project.ui_file import Ui_MainWindow


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        a = [f"[{ext}:] диск" for ext in ascii_uppercase if os.path.exists(f"{ext}:/")]
        self.comboBox.addItems(a)  # Добавление всех существующих дисков в comboBox

        self.icon_provider = QFileIconProvider()
        self.msg = QMessageBox()  # QMessageBox для вывода информации/ошибок
        self.pushButton.clicked.connect(self.preparations)  # Запуск анализа выбранной дирректории

        self.choose_text.hide()
        self.size_text.hide()
        self.occupied_text.hide()
        self.free_text.hide()

    def preparations(self):
        if not self.comboBox.currentText():  # Если ничего не выбрано
            self.msg.setText("Выберите дирректорию")
            self.msg.show()
            return

        text = self.comboBox.currentText()
        try:
            if not os.path.exists(text[text.find("[") + 1:text.rfind("]")]):
                self.msg.setText("Дирректория неккоректна")
                self.msg.show()
                return

            self.choose_text.show()
            self.size_text.show()
            self.occupied_text.show()
            self.free_text.show()

            self.choose_value.setText(text)

            self.build_tree(text[text.find("[") + 1:text.rfind("]")])
        except Exception as ex:
            print(ex)

    def normal_value(self, size: int):
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

    def build_tree(self, dr: str):

        total, used, free, percent = psutil.disk_usage(dr)

        sz, tp = self.normal_value(total)
        self.size_value.setText(f"{sz:.1f}{tp}")

        sz, tp = self.normal_value(used)
        self.occupied_value.setText(f"{sz:.1f}{tp}")

        sz, tp = self.normal_value(free)
        self.free_value.setText(f"{sz:.1f}{tp}")

        highest = self.create_item(dr, parent=None, per=100)
        another = self.create_item('C:/Windows', parent=highest)

    def create_item(self, path, parent, per=None, tree=True):
        """
        :param path: Путь до рассматриваемой папки
        :param parent:
        :param per: Процент от занимаемого места, может быть установлен вручную
        :return: QtreeWidget(путь_до_папки, )
        """

        _, used, _, percent = psutil.disk_usage(path)
        psutil.

        if path.count('/') > 1:
            name = path[path.rfind('/') + 1:]
        else:
            name = path

        size_, type_ = self.normal_value(used)

        if per is not None:
            percent = per

        if tree:
            item_ = QTreeWidgetItem([str(name), f"{percent}%", f"{size_:.1f}{type_}",
                                     datetime.datetime.fromtimestamp(os.stat(path).st_atime).strftime(
                                         "%d.%m.%Y %H:%m:%S")])

        item_.setIcon(0, self.get_ico(path))

        if parent is None:
            self.treeWidget.addTopLevelItem(item_)
        else:
            parent.addChild(item_)

        self.treeWidget.setItemWidget(item_, 1, self.create_progress_bar(percent))
        return item_

    def create_progress_bar(self, percent):
        pr = QProgressBar()
        pr.setValue(percent)
        pr.setStyleSheet("QProgressBar{text-align: center;active: 0}")
        return pr

    def get_ico(self, file_name=""):
        icon = self.icon_provider.icon(QtCore.QFileInfo(file_name))
        return icon


app = QApplication(sys.argv)
M = Main()
M.show()
app.exec()
