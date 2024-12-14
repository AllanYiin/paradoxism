import sys
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QTreeWidget, \
    QTreeWidgetItem, QMessageBox, QInputDialog


class JSONEditorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('LLM 模型與 Azure OpenAI 資訊維護工具')
        self.setGeometry(100, 100, 800, 600)
        self.layout = QVBoxLayout()

        self.load_button_model = QPushButton('載入 LLM 模型 JSON 檔案')
        self.load_button_model.clicked.connect(lambda: self.load_json('model'))
        self.layout.addWidget(self.load_button_model)

        self.load_button_azure = QPushButton('載入 Azure OpenAI JSON 檔案')
        self.load_button_azure.clicked.connect(lambda: self.load_json('azure'))
        self.layout.addWidget(self.load_button_azure)

        self.save_button = QPushButton('保存 JSON 檔案')
        self.save_button.clicked.connect(self.save_json)
        self.layout.addWidget(self.save_button)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(['LLM 提供商', '模型清單'])
        self.layout.addWidget(self.tree)

        self.add_button = QPushButton('新增條目')
        self.add_button.clicked.connect(self.add_entry)
        self.layout.addWidget(self.add_button)

        self.add_model_button = QPushButton('新增模型')
        self.add_model_button.clicked.connect(self.add_model)
        self.layout.addWidget(self.add_model_button)

        self.edit_button = QPushButton('編輯條目')
        self.edit_button.clicked.connect(self.edit_entry)
        self.layout.addWidget(self.edit_button)

        self.delete_button = QPushButton('刪除條目')
        self.delete_button.clicked.connect(self.delete_entry)
        self.layout.addWidget(self.delete_button)

        self.setLayout(self.layout)
        self.json_data_model = None
        self.json_data_azure = None
        self.current_json_type = None

    def load_json(self, json_type):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, '開啟 JSON 檔案', '', 'JSON 檔案 (*.json);;所有檔案 (*)',
                                                   options=options)
        if file_name:
            try:
                with open(file_name, 'r') as file:
                    json_data = json.load(file)
                    if json_type == 'model':
                        self.json_data_model = json_data
                        self.current_json_type = 'model'
                    elif json_type == 'azure':
                        self.json_data_azure = json_data
                        self.current_json_type = 'azure'
                    self.populate_tree()
            except Exception as e:
                QMessageBox.critical(self, '錯誤', f'載入 JSON 檔案失敗: {e}')

    def save_json(self):
        if self.current_json_type is None:
            QMessageBox.warning(self, '警告', '沒有可保存的 JSON 資料!')
            return

        json_data = self.json_data_model if self.current_json_type == 'model' else self.json_data_azure
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, '保存 JSON 檔案', '', 'JSON 檔案 (*.json);;所有檔案 (*)',
                                                   options=options)
        if file_name:
            try:
                with open(file_name, 'w') as file:
                    json.dump(json_data, file, indent=4)
                    QMessageBox.information(self, '成功', 'JSON 檔案保存成功!')
            except Exception as e:
                QMessageBox.critical(self, '錯誤', f'保存 JSON 檔案失敗: {e}')

    def populate_tree(self):
        self.tree.clear()
        json_data = self.json_data_model if self.current_json_type == 'model' else self.json_data_azure
        self.add_items(self.tree.invisibleRootItem(), json_data)

    def add_items(self, parent, data):
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem([key, '模型清單' if isinstance(value, list) else str(value)])
                parent.addChild(item)
                self.add_items(item, value)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                item = QTreeWidgetItem([str(index), '模型' if isinstance(value, dict) else str(value)])
                parent.addChild(item)
                self.add_items(item, value)

    def add_entry(self):
        if self.current_json_type is None:
            QMessageBox.warning(self, '警告', '尚未載入任何 JSON 資料!')
            return

        json_data = self.json_data_model if self.current_json_type == 'model' else self.json_data_azure
        key, ok = QInputDialog.getText(self, '新增條目', '輸入 LLM 提供商:')
        if ok and key:
            if key in json_data:
                reply = QMessageBox.question(self, '鍵已存在', f'鍵 "{key}" 已存在，是否要覆蓋其值？',
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            json_data[key] = []  # 使用空的清單作為初始值
            self.populate_tree()

    def add_model(self):
        if self.current_json_type is None:
            QMessageBox.warning(self, '警告', '尚未載入任何 JSON 資料!')
            return

        json_data = self.json_data_model if self.current_json_type == 'model' else self.json_data_azure
        selected = self.tree.currentItem()
        if selected and isinstance(json_data.get(selected.text(0)), list):
            model_name, ok = QInputDialog.getText(self, '新增模型', '輸入模型名稱:')
            if ok and model_name:
                default_model = {
                    "model": model_name,
                    "max_tokens": 0,
                    "max_output_tokens": 0
                }
                json_data[selected.text(0)].append(default_model)
                self.populate_tree()
        else:
            QMessageBox.warning(self, '警告', '請選擇一個 LLM 提供商以新增模型!')

    def edit_entry(self):
        if self.current_json_type is None:
            QMessageBox.warning(self, '警告', '尚未載入任何 JSON 資料!')
            return

        json_data = self.json_data_model if self.current_json_type == 'model' else self.json_data_azure
        selected = self.tree.currentItem()
        if selected:
            key = selected.text(0)
            value, ok = QInputDialog.getText(self, '編輯條目', '輸入新值:', text=selected.text(1))
            if ok:
                parent = selected.parent()
                if parent is None:
                    json_data[key] = value
                else:
                    if parent.text(0) in json_data:
                        try:
                            index_or_key = int(key) if key.isdigit() else key
                            json_data[parent.text(0)][index_or_key] = value
                        except (KeyError, ValueError) as e:
                            QMessageBox.critical(self, '錯誤', f'更新條目失敗: {e}')
                self.populate_tree()
        else:
            QMessageBox.warning(self, '警告', '未選擇任何條目!')

    def delete_entry(self):
        if self.current_json_type is None:
            QMessageBox.warning(self, '警告', '尚未載入任何 JSON 資料!')
            return

        json_data = self.json_data_model if self.current_json_type == 'model' else self.json_data_azure
        selected = self.tree.currentItem()
        if selected:
            key = selected.text(0)
            reply = QMessageBox.question(self, '刪除條目', f'確定要刪除 "{key}" 嗎?', QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)
            if reply == QMessageBox.Yes:
                parent = selected.parent()
                if parent is None:
                    del json_data[key]
                else:
                    if parent.text(0) in json_data:
                        try:
                            index_or_key = int(key) if key.isdigit() else key
                            del json_data[parent.text(0)][index_or_key]
                        except (KeyError, ValueError) as e:
                            QMessageBox.critical(self, '錯誤', f'刪除條目失敗: {e}')
                self.populate_tree()
        else:
            QMessageBox.warning(self, '警告', '未選擇任何條目!')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = JSONEditorApp()
    window.show()
    sys.exit(app.exec_())