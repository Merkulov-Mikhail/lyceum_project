import datetime
import os
import stat
import sys
from hashlib import sha256
from random import randint
from string import ascii_uppercase
from threading import Thread

import psutil
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QTreeWidgetItem, QProgressBar, QFileIconProvider, \
    QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout, QFileDialog

from lyceum_project import normal_value, Dict, omega_secret, cur, db
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


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        dlg = QDialog()
        dlg.setGeometry(500, 500, 200, 200)
        label_1 = QLabel(parent=dlg)
        label_1.setText("Имя пользователя")
        label_1.move(10, 0)

        self.login = QLineEdit(parent=dlg)
        self.login.move(10, 25)
        self.password = QLineEdit(parent=dlg)
        self.password.move(10, 100)

        label_2 = QLabel(parent=dlg)
        label_2.setText("Пароль")
        label_2.move(10, 75)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dlg)
        buttons.move(10, 170)
        layout = QVBoxLayout(self)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout.addWidget(label_1)
        layout.addWidget(self.login)
        layout.addWidget(label_2)
        layout.addWidget(self.password)
        layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def _getData(self):
        return self.login.text(), self.password.text()

    def getLogin(parent=None):
        dialog = LoginDialog(parent)
        res = dialog.exec_()
        ans = dialog._getData()
        return *ans, res == QDialog.Accepted


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.base_QDialog_directory = "C:/"
        log, pas, res = LoginDialog.getLogin()
        if not res:
            exit()
        if cur.execute(f"SELECT password FROM users WHERE login='{log}'").fetchone()[0] == sha256(
                (pas + omega_secret).encode()).hexdigest():
            pass
        else:
            exit()
        a = [f"[{ext}:/] диск" for ext in ascii_uppercase if os.path.exists(f"{ext}:/")]
        a.append("<Выбрать файл>")
        self.comboBox.addItems(a)  # Добавление всех существующих дисков в comboBox

        self.icon_provider = QFileIconProvider()
        self.msg = QMessageBox()  # QMessageBox для вывода информации/ошибок
        self.pushButton.clicked.connect(self.preparations)  # Запуск анализа выбранной дирректории

        self.choose.hide()
        self.size_text.hide()
        self.occupied_text.hide()
        self.free_text.hide()
        # добавление/изменение пользователей
        self.change_user_password.clicked.connect(self.change_password)
        self.create_user.clicked.connect(self.new_user)

        self.icon.setPixmap(QPixmap("cool_image.jpg"))

        cur.execute("CREATE TABLE IF NOT EXISTS users(login TEXT, password TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS cool_data(login TEXT, date TEXT)")

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

            if text == "<Выбрать файл>":
                dialog = QFileDialog()
                dialog.setFileMode(dialog.DirectoryOnly)
                file_name = dialog.getExistingDirectory(self, 'Open file', self.base_QDialog_directory)
                text = f"[{file_name}]"
                self.base_QDialog_directory = file_name
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
            print(ex.args)
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
            _, used, free, _ = psutil.disk_usage(dr)

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

    def _recurion(self, parent, directory):

        try:
            dr = directory.replace("\\", "/")
            branch = self.create_item(dr, parent, 0)
            if os.path.isfile(dr):
                Dict[branch] = [parent, os.stat(dr).st_size]
                branch.setText(2, self.to_human_vision(Dict[branch][1]))
                branch.setText(4, f"{Dict[branch][1]}")
                Dict[parent][1] += os.stat(dr).st_size
                return
            Dict[branch] = [parent, 0]
            files = os.scandir(dr)

            for file_name in files:
                if file_name.name[0].isalpha():
                    if os.access(file_name, os.R_OK & os.F_OK):
                        thr = Thread(target=self._recurion, kwargs={'parent': branch, 'directory': os.path.join(dr, file_name)})
                        thr.run()
            # Так как дерево создаётся рекурсивно, мы не знаем размер рассматриваемой папки, пока все подкаталоги не будут проверены
            # Поэтому после прохода по всем подкаталогам, надо обновить процент занимаемого ими места в текущей папке

            if parent == None:
                for child in range(branch.childCount()):
                    self._update_children(branch.child(child), Dict[branch][1], Dict[branch.child(child)][1])
            else:
                for child in range(branch.childCount()):
                    self._update_children(branch.child(child), Dict[branch][1], Dict[branch.child(child)][1])
            if parent == None:
                Dict[parent][1] += Dict[branch][1]
                branch.setText(2, self.to_human_vision(Dict[branch][1]))
                branch.setText(4, f"{Dict[branch][1]}")
            else:
                Dict[parent][1] += Dict[branch][1]
                branch.setText(2, self.to_human_vision(Dict[branch][1]))
                branch.setText(4, f"{Dict[branch][1]}")
        except Exception as e: # В поисках бага я устал, так что вся функция теперь защищается except Exception, сейчас 1:40, 13.12.2022
            print(e.args)
            print(e)
            print(directory)
            print(directory.replace("\\", "/"))
            return

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
        :return: QtreeWidget(путь_до_папки)
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
                                   f"{size_}"])
        item_.setIcon(0, self.get_ico(path))

        if parent is None:
            self.treeWidget.addTopLevelItem(item_)
        else:
            parent.addChild(item_)

        self.treeWidget.setItemWidget(item_, 1, self.create_progress_bar(percent))
        return item_

    r"""
    |-----------------------------------------------|
    | Second tab part, made for galochka            |
    |-----------------------------------------------|
    """

    def new_user(self):
        log, pas = self.lineEdit_4.text(), self.lineEdit_5.text()
        if not (log and pas) or not self.check_login(log):
            self.msg.setText("Данные введены некорректно")
            self.msg.show()
            return
        if cur.execute(f"SELECT * FROM users WHERE login='{log}'").fetchall():
            self.msg.setText("Пользователь существует")
            self.msg.show()
            return
        cur.execute(
            f"INSERT INTO users(login, password) VALUES('{log}', '{sha256((pas + omega_secret).encode()).hexdigest()}')")  # NOQA:501
        cur.execute(
            f"INSERT INTO cool_data(login, date) VALUES('{log}', '{datetime.datetime.today().strftime('%d.%m.%Y %H:%m:%S')}')")  # NOQA:501
        db.commit()

    def change_password(self):
        log, prev, curr = self.lineEdit.text(), self.lineEdit_2.text(), self.lineEdit_3.text()
        if not (log and prev and curr) or not self.check_login(log):
            self.msg.setText("Данные введены некорректно")
            self.msg.show()
            return
        if not cur.execute(f"SELECT * FROM users WHERE login='{log}'").fetchall():
            self.msg.setText("Пользователь не существует")
            self.msg.show()
            return
        if sha256((prev + omega_secret).encode()).hexdigest() != \
                cur.execute(f"SELECT * FROM users WHERE login='{log}'").fetchone()[1]:  # NOQA:501
            self.msg.setText("Старый пароль некорректный")
            self.msg.show()
            return
        cur.execute(
            f"UPDATE users SET password = '{sha256((curr + omega_secret).encode()).hexdigest()}' WHERE login='{log}'")  # NOQA:501
        db.commit()

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

    def check_login(self, lg: str):
        # function for galochka
        from string import digits, ascii_lowercase

        alphabet = set(digits + ascii_lowercase)
        for letter in lg:
            if letter not in alphabet:
                return False
        return True


if __name__ == '__main__':
    app = QApplication(sys.argv)
    M = Main()
    M.show()
    app.exec()
