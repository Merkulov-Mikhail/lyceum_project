import os
import sys
import datetime
import psutil
import stat
from random import randint
from threading import Thread
from string import ascii_uppercase

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

        self.choose_text.hide()
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

            self.choose_text.show()
            self.size_text.show()
            self.occupied_text.show()
            self.free_text.show()

            self.choose_value.setText(text)

            self.build_tree(text[text.find("[") + 1:text.rfind("]")])
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
        if len(dr) <= 3:
            total, used, free, _ = psutil.disk_usage(dr)
            self._recurion(None, dr)
            sz, tp = normal_value(total)
            self.size_value.setText(f"{sz:.1f}{tp}")

            sz, tp = normal_value(used)
            self.occupied_value.setText(f"{sz:.1f}{tp}")

            sz, tp = normal_value(free)
            self.free_value.setText(f"{sz:.1f}{tp}")
        else:
            self._recurion(None, dr)
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

    def _update_children(self, item, total, curr):
        """
        Обновляет параметр % для этого элемента
        :param item:
        :param total:
        :param curr:
        :return:
        """
        self.treeWidget.setItemWidget(item, 1, self.create_progress_bar((curr // total) if total else 0))

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

        if path.count('/') > 0:
            name = path[path.rfind('/') + 1:]
        else:
            name = path

        size_, type_ = normal_value(used_)

        item_ = MyQTreeWidgetItem([name, f"{percent}%", f"{size_:.1f}{type_}",
                                 datetime.datetime.fromtimestamp(os.stat(path).st_atime).strftime(
                                     "%d.%m.%Y %H:%m:%S")])
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
