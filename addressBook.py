"""PPT 36~51쪽 PyQt5 주소록. 데이터는 이 파일 옆 addbook.txt에 저장합니다."""
import csv
import os
import sys
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel,
    QAbstractItemView, QDialog, QDialogButtonBox, QMessageBox, QMenu, QHBoxLayout)


class ContactStore:
    def __init__(self, path):
        self.path = Path(path)
        self.contacts = {}

    @staticmethod
    def validate(name, phone):
        name, phone = name.strip(), phone.strip()
        if not name or not phone:
            raise ValueError('이름과 전화번호를 모두 입력하세요.')
        if any(c in name + phone for c in '\r\n'):
            raise ValueError('줄바꿈은 입력할 수 없습니다.')
        return name, phone

    def add(self, name, phone):
        name, phone = self.validate(name, phone)
        if name in self.contacts:
            raise ValueError('같은 이름이 있습니다. 목록을 더블클릭하여 수정하세요.')
        self.contacts[name] = phone

    def edit(self, old, name, phone):
        name, phone = self.validate(name, phone)
        if old not in self.contacts:
            raise ValueError('연락처를 다시 선택하세요.')
        if name != old and name in self.contacts:
            raise ValueError('같은 이름이 이미 있습니다.')
        self.contacts = {name if k == old else k: phone if k == old else v
                         for k, v in self.contacts.items()}

    def search(self, query):
        q = query.strip().casefold()
        return [n for n, p in self.contacts.items()
                if q and (q in n.casefold() or q in p.casefold())]

    def save(self):
        tmp = self.path.with_suffix('.tmp')
        try:
            with tmp.open('w', newline='', encoding='utf-8-sig') as f:
                csv.writer(f).writerows(self.contacts.items())
            os.replace(tmp, self.path)
        finally:
            if tmp.exists():
                tmp.unlink()

    def load(self):
        loaded = {}
        with self.path.open(newline='', encoding='utf-8-sig') as f:
            for line, row in enumerate(csv.reader(f), 1):
                if not row:
                    continue
                if len(row) != 2:
                    raise ValueError(f'{line}행: 이름,전화번호 형식이 아닙니다.')
                name, phone = self.validate(*row)
                if name in loaded:
                    raise ValueError(f'{line}행: 중복된 이름입니다.')
                loaded[name] = phone
        self.contacts = loaded  # 읽기 전체가 성공한 뒤에만 교체


class EditDialog(QDialog):
    def __init__(self, name, phone, parent=None):
        super().__init__(parent)
        self.setWindowTitle('연락처 수정')
        self.name_input = QLineEdit(name)
        self.phone_input = QLineEdit(phone)
        layout = QFormLayout(self)
        layout.addRow('이름', self.name_input)
        layout.addRow('전화번호', self.phone_input)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class AddressBook(QWidget):
    def __init__(self, path=None):
        super().__init__()
        self.store = ContactStore(path or Path(__file__).with_name('addbook.txt'))
        self.dirty = False
        self.setWindowTitle('주소록 프로그램 · Python 수업')
        self.resize(500, 620)
        self.setStyleSheet('QWidget {font-family:Malgun Gothic;font-size:14px;} '
                           'QLineEdit,QPushButton {padding:7px;} QListWidget {padding:5px;}')
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('내 주소록'))
        self.name_input, self.phone_input = QLineEdit(), QLineEdit()
        form = QFormLayout()
        form.addRow('이름', self.name_input)
        form.addRow('전화번호', self.phone_input)
        layout.addLayout(form)
        self.add_button = QPushButton('추가')
        self.add_button.clicked.connect(self.add_contact)
        layout.addWidget(self.add_button)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('이름 일부 또는 전화번호 입력 후 Enter')
        self.search_input.returnPressed.connect(self.search_contact)
        layout.addWidget(QLabel('찾기 (검색 버튼 없이 Enter)'))
        layout.addWidget(self.search_input)
        self.contact_list = QListWidget()
        self.contact_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.contact_list.itemDoubleClicked.connect(self.edit_contact)
        self.contact_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.contact_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.contact_list)
        layout.addWidget(QLabel('더블클릭: 수정 / 마우스 오른쪽: 삭제'))
        row = QHBoxLayout()
        for title, callback in [('저장', self.save_to_file), ('불러오기', self.load_from_file)]:
            button = QPushButton(title)
            button.clicked.connect(callback)
            row.addWidget(button)
        layout.addLayout(row)
        self.status = QLabel('새 주소록 · 불러오기를 누르면 저장한 목록을 읽습니다.')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    def update_contact_list(self):
        self.contact_list.clear()
        for name, phone in self.store.contacts.items():
            item = QListWidgetItem(f'{name}: {phone}')
            item.setData(Qt.UserRole, name)
            self.contact_list.addItem(item)

    def error(self, e):
        QMessageBox.warning(self, '확인해 주세요', str(e))

    def add_contact(self):
        try:
            self.store.add(self.name_input.text(), self.phone_input.text())
        except ValueError as e:
            return self.error(e)
        self.dirty = True
        self.update_contact_list()
        self.name_input.clear()
        self.phone_input.clear()
        self.status.setText(f'{len(self.store.contacts)}명 · 저장하지 않은 변경 있음')
        self.name_input.setFocus()

    def search_contact(self):
        matches = set(self.store.search(self.search_input.text()))
        first = None
        for i in range(self.contact_list.count()):
            item = self.contact_list.item(i)
            found = item.data(Qt.UserRole) in matches
            item.setSelected(found)
            if found and first is None:
                first = item
        if first:
            self.contact_list.scrollToItem(first)
        self.status.setText(f'검색 결과 {len(matches)}명' if self.search_input.text().strip()
                            else '검색어를 입력하세요. 이름 일부·전화번호를 검색할 수 있습니다.')

    def edit_contact(self, item):
        old = item.data(Qt.UserRole)
        dialog = EditDialog(old, self.store.contacts[old], self)
        while dialog.exec_() == QDialog.Accepted:
            try:
                self.store.edit(old, dialog.name_input.text(), dialog.phone_input.text())
            except ValueError as e:
                self.error(e)
                continue
            self.dirty = True
            self.update_contact_list()
            self.status.setText('수정 완료 · 저장 버튼을 눌러 주세요.')
            break

    def delete_contact(self, name):
        if QMessageBox.question(self, '삭제 확인', f'{name} 연락처를 삭제할까요?') != QMessageBox.Yes:
            return
        self.store.contacts.pop(name, None)
        self.dirty = True
        self.update_contact_list()
        self.status.setText('삭제 완료 · 저장 전에는 불러오기로 되돌릴 수 있습니다.')

    def show_context_menu(self, pos):
        item = self.contact_list.itemAt(pos)
        if item is None:
            return
        menu = QMenu(self)
        action = menu.addAction('삭제')
        if menu.exec_(self.contact_list.mapToGlobal(pos)) == action:
            self.delete_contact(item.data(Qt.UserRole))

    def save_to_file(self):
        try:
            self.store.save()
        except (OSError, ValueError) as e:
            return self.error(e)
        self.dirty = False
        self.status.setText(f'저장 완료: {self.store.path.name}')

    def load_from_file(self):
        if self.dirty and QMessageBox.question(self, '불러오기', '저장하지 않은 변경을 버리고 불러올까요?') != QMessageBox.Yes:
            return
        try:
            self.store.load()
        except (OSError, ValueError, UnicodeError, csv.Error) as e:
            return self.error(e)
        self.dirty = False
        self.update_contact_list()
        self.status.setText(f'{len(self.store.contacts)}명 불러오기 완료')

    def closeEvent(self, event):
        if self.dirty:
            choice = QMessageBox.question(self, '닫기', '변경 사항을 저장할까요?',
                       QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if choice == QMessageBox.Cancel:
                return event.ignore()
            if choice == QMessageBox.Save:
                self.save_to_file()
                if self.dirty:
                    return event.ignore()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AddressBook()
    window.show()
    sys.exit(app.exec_())
