import datetime
import psutil
import os
import stat
import sys
from random import randint
from string import ascii_uppercase
from threading import Thread

import psutil
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QTreeWidgetItem, QProgressBar, QFileIconProvider

from lyceum_project import normal_value, Dict
from lyceum_project.ui_file import Ui_MainWindow


class MyQTreeWidgetItem(QTreeWidgetItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__indicator = randint(int(1e3), int(1e100))

    def __hash__(self):
        return hash(self.__indicator)

    def __lt__(self, other):
        col = self.treeWidget().sortColumn()
        try:
            return int(self.text(col)) > float(other.text(col))
        except ValueError:
            return self.text(col) > other.text(col)


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        a = [f"[{ext}:/] диск" for ext in ascii_uppercase if os.path.exists(f"{ext}:/")]
        a.append("[D:/lyceum]")
        self.comboBox.addItems(a)  # Добавление всех существующих дисков в comboBox

        self.icon_provider = QFileIconProvider()
        self.msg = QMessageBox()  # QMessageBox для вывода информации/ошибок
        self.pushButton.clicked.connect(self.preparations)  # Запуск анализа выбранной дирректории

        self.choose.hide()
        self.size_text.hide()
        self.occupied_text.hide()
        self.free_text.hide()

    r"""
    |-----------------------------------------------|
    | Main part, logic before creating Tree         |
    |-----------------------------------------------|
    """

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

            if len(text) <= 4:
                d = psutil.disk_usage(text[1:-1])
                self.size_value.setText(d.total)
                self.occupied_value.setText(d.used)
                self.free_value.setText(d.free)
            else:
                self.occupied_value.setText('н/д')
                self.free_value.setText('н/д')
            self.treeWidget.clear()
            self.treeWidget.setSortingEnabled(False)

            self.build_tree(text[text.find("[") + 1:text.rfind("]")])

            self.treeWidget.setSortingEnabled(True)
            self.choose.show()
            self.size_text.show()
            self.occupied_text.show()
            self.free_text.show()
            self.disk_chosen.setText(text)
            dat = self.treeWidget.topLevelItem(0)
            self.size_value.setText(self.to_human_vision(int(dat.data(4, 0))))

            with open("file", "a") as f:
                # Ну а почему и не добавить 'логгер' проверок дирректорий
                f.write(f"[{datetime.datetime.today().strftime('%d.%m.%Y %H:%m:%S')}] {text}\n")

            self.treeWidget.sortItems(4, QtCore.Qt.AscendingOrder)
        except Exception as ex:
            print(ex)
            self.msg.setText(str(ex))
            self.msg.show()

    r"""
    |-----------------------------------------------|
    | Main part, creating Tree                      |
    |-----------------------------------------------|
    """

    def build_tree(self, dr: str):
        self._recurion(None, dr)
        if len(dr) <= 3:
            total, used, free, _ = psutil.disk_usage(dr)
            sz, tp = normal_value(total)
            self.size_value.setText(f"{sz:.1f}{tp}")

            sz, tp = normal_value(used)
            self.occupied_value.setText(f"{sz:.1f}{tp}")

            sz, tp = normal_value(free)
            self.free_value.setText(f"{sz:.1f}{tp}")
        self.treeWidget.sortItems(2, 1)

    r"""
    |-----------------------------------------------|
    | Main part, recursive creation of a Tree       |
    |-----------------------------------------------|
    """

    def _recurion(self, parent, dr):
        self.treeWidget.update()
        branch = self.create_item(dr, parent, 0)
        if os.path.isfile(dr):
            Dict[branch] = [parent, os.stat(dr).st_size]
            branch.setText(2, self.to_human_vision(Dict[branch][1]))
            branch.setText(4, f"{Dict[branch][1]}")
            Dict[parent][1] += os.stat(dr).st_size
            return

        try:
            files = os.scandir(dr)
        except OSError:
            return
        Dict[branch] = [parent, 0]

        for file_name in files:
            if file_name.name[0].isalpha():
                if os.access(file_name, os.R_OK & os.F_OK):
                    thr = Thread(target=self._recurion, kwargs={'parent': branch, 'dr': os.path.join(dr, file_name)})
                    thr.run()

        # Так как дерево создаётся рекурсивно, мы не знаем размер рассматриваемой папки, пока все подкаталоги не будут проверены
        # Поэтому после прохода под всем подкаталогам, надо обновить процент занимаемого ими места в текущей папке
        for child in range(branch.childCount()):
            self._update_children(branch.child(child), Dict[branch][1], Dict[branch.child(child)][1])
        Dict[parent][1] += Dict[branch][1]
        branch.setText(2, self.to_human_vision(Dict[branch][1]))
        branch.setText(4, f"{Dict[branch][1]}")

    def _update_children(self, item, total, curr):
        """
        Обновляет параметр % для этого элемента
        :param item:
        :param total:
        :param curr:
        :return:
        """
        self.treeWidget.setItemWidget(item, 1, self.create_progress_bar(int(curr / total * 100) if total else 0))

    r"""
    |-----------------------------------------------|
    | Main part, sample to create QTreeWidget       |
    |-----------------------------------------------|
    """

    def create_item(self, path, parent, used, per=None):
        """
        :param path: Путь до рассматриваемой папки
        :param parent:
        :param per: Процент от занимаемого места, может быть установлен вручную
        :return: QtreeWidget(путь_до_папки, )
        """

        used_ = used
        if parent is not None:
            if Dict[parent][1]:
                percent = used_ // Dict[parent][1] * 100
            else:
                percent = 0
        elif per is not None:
            percent = per
        else:
            percent = 100

        if path.count('\\') > 0:
            name = path[path.rfind('\\') + 1:]
        elif path.count('/') > 0:
            name = path[path.rfind('/') + 1:]
        else:
            name = path
        size_, type_ = normal_value(used_)
        item_ = MyQTreeWidgetItem([name, f"{percent}%",
                                   f"{size_:.1f}{type_}",
                                   datetime.datetime.fromtimestamp(os.stat(path).st_atime).strftime(
                                       "%d.%m.%Y %H:%m:%S"),  # NOQA:501
                                   f"{size_:.1f}{type_}"])
        item_.setIcon(0, self.get_ico(path))

        if parent is None:
            self.treeWidget.addTopLevelItem(item_)
        else:
            parent.addChild(item_)

        self.treeWidget.setItemWidget(item_, 1, self.create_progress_bar(percent))
        return item_

    r"""
    |-----------------------------------------------|
    | Secondary functions                           |
    |-----------------------------------------------|
    """

    def to_human_vision(self, value):
        size_, type_ = normal_value(value)
        return f'{size_:.1f}{type_}'

    def create_progress_bar(self, percent: int):
        pr = QProgressBar()
        pr.setValue(percent)
        pr.setStyleSheet("QProgressBar{text-align: center;active: 0}")
        return pr

    def get_ico(self, file_name=""):
        icon = self.icon_provider.icon(QtCore.QFileInfo(file_name))
        return icon

    def is_accessible(self, dr):
        return os.access(dr, os.R_OK & os.F_OK) and not (os.stat(dr).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)


app = QApplication(sys.argv)
M = Main()
M.show()
app.exec()
