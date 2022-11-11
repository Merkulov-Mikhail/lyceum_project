import os
import sys
import datetime
from string import ascii_uppercase

import psutil
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QTreeWidgetItem, QProgressBar, QFileIconProvider
from PyQt5.QtGui import QIcon

from lyceum_project.ui_file import Ui_MainWindow


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        a = [f"[{ext}:] диск" for ext in ascii_uppercase if os.path.exists(f"{ext}:/")]
        self.comboBox.addItems(a)  # Добавление всех существующих дисков в comboBox

        self.icon_provider = QFileIconProvider()
        self.msg = QMessageBox() # QMessageBox для вывода информации/ошибок
        self.pushButton.clicked.connect(self.preparations) # Запуск анализа выбранной дирректории

        self.choose_text.hide()
        self.size_text.hide()
        self.occupied_text.hide()
        self.free_text.hide()


    def preparations(self):
        if not self.comboBox.currentText(): # Если ничего не выбрано
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

        # Папка     Занятый_процент     Размер_на_диске     Дата_изменения
        sz, tp = self.normal_value(used)
        highest = QTreeWidgetItem([str(dr), "100%", f"{sz:.1f}{tp}",
                                   datetime.datetime.fromtimestamp(os.stat(dr).st_atime).strftime("%d.%m.%Y %H:%m:%S")])

        highest.setIcon(0, self._get_ico("C:"))
        self.treeWidget.addTopLevelItem(highest)
        self.treeWidget.setItemWidget(highest, 1, self.create_progress_bar(100))

    def _get_ico(self, file_name=""):
        icon = self.icon_provider.icon(QtCore.QFileInfo(file_name))
        return icon

    def create_progress_bar(self, percent):
        pr = QProgressBar()
        pr.setValue(percent)
        pr.setStyleSheet("QProgressBar{text-align: center;}")
        return pr

app = QApplication(sys.argv)
M = Main()
M.show()
app.exec()
