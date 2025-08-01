from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
                           QMessageBox, QApplication, QLabel, QComboBox, QGroupBox, QListWidget, QDialog, QVBoxLayout as QVBoxLayoutDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from global_state import GlobalState
import time
import os
import subprocess
import sys

class LocalFileDialog(QDialog):
    """本地文件选择对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = None
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("选择本地脚本文件")
        self.setFixedSize(600, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: white;
            }
        """)
        
        layout = QVBoxLayoutDialog(self)
        
        # 当前路径显示
        self.path_label = QLabel("当前路径: /home")
        self.path_label.setStyleSheet("color: white; font-size: 14px; padding: 5px;")
        layout.addWidget(self.path_label)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #666666;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #444444;
            }
            QListWidget::item:selected {
                background-color: #404040;
            }
        """)
        self.file_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.file_list)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.select_btn = QPushButton("选择文件")
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:disabled {
                color: #888888;
                border: 2px solid #888888;
            }
        """)
        self.select_btn.clicked.connect(self.select_file)
        self.select_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.select_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # 加载文件列表
        self.load_files("/home")
        
    def load_files(self, path):
        """加载指定路径的文件列表"""
        try:
            files = os.listdir(path)
            
            self.current_path = path
            self.path_label.setText(f"当前路径: {path}")
            self.file_list.clear()
            
            # 添加返回上级目录选项
            if path != "/":
                self.file_list.addItem(".. (返回上级目录)")
            
            # 添加文件和目录
            for file in sorted(files):
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path) and file.endswith('.py'):
                    self.file_list.addItem(f"📄 {file}")
                elif os.path.isdir(file_path):
                    self.file_list.addItem(f"📁 {file}")
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载目录内容: {str(e)}")
    
    def on_item_double_clicked(self, item):
        """双击项目处理"""
        text = item.text()
        
        if text == ".. (返回上级目录)":
            # 返回上级目录
            parent_path = os.path.dirname(self.current_path)
            if parent_path:
                self.load_files(parent_path)
        elif text.startswith("📁 "):
            dir_name = text[2:]  # emoji+空格
            new_path = os.path.join(self.current_path, dir_name)
            self.load_files(new_path)
        elif text.startswith("📄 "):
            file_name = text[2:]  # emoji+空格
            self.selected_file = os.path.join(self.current_path, file_name)
            self.select_btn.setEnabled(True)
    
    def select_file(self):
        """选择文件"""
        if self.selected_file:
            self.accept()

class ExecutionThread(QThread):
    """脚本执行进程"""
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path
    
    def run(self):
        try:
            # 执行本地脚本
            self.update_signal.emit(f"\n开始执行本地脚本: {self.script_path}")
            
            # 获取脚本所在目录和文件名
            script_dir = os.path.dirname(self.script_path)
            script_name = os.path.basename(self.script_path)
            
            # 确保路径格式正确（使用正斜杠）
            script_dir = script_dir.replace('\\', '/')
            script_path = self.script_path.replace('\\', '/')
            
            self.update_signal.emit(f"脚本目录: {script_dir}")
            self.update_signal.emit(f"脚本名称: {script_name}")
            self.update_signal.emit(f"完整路径: {script_path}")
            
            # 构建执行命令
            command = f"cd {script_dir} && python3 {script_name}"
            
            self.update_signal.emit(f"执行命令: {command}")
            
            # 使用subprocess执行命令
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 实时获取输出
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.update_signal.emit(output.strip())
            
            # 获取退出状态
            exit_status = process.poll()
            if exit_status != 0:
                # 获取错误输出
                stderr_output = process.stderr.read()
                if stderr_output:
                    self.update_signal.emit(f"错误输出: {stderr_output}")
                self.update_signal.emit(f"脚本执行失败，退出状态码: {exit_status}")
                self.finished_signal.emit(False)
            else:
                self.update_signal.emit("脚本执行完成！")
                self.finished_signal.emit(True)
                
        except Exception as e:
            self.update_signal.emit(f"执行出错: {str(e)}")
            self.finished_signal.emit(False)

class TrainingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.global_state = GlobalState.get_instance()
        self.selected_script_path = None
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        self.setMinimumSize(1000, 700)
        
        # 脚本选择区域
        script_group = QGroupBox("本地脚本选择")
        script_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 18px;
                border: 1px solid white;
                border-radius: 5px;
                padding: 10px;
                margin-top: 10px;
            }
        """)
        script_layout = QVBoxLayout(script_group)
        
        # 脚本选择说明
        script_label = QLabel("请选择要执行的本地脚本文件:")
        script_label.setStyleSheet("color: white; font-size: 18px; margin-bottom: 10px;")
        script_layout.addWidget(script_label)
        
        # 脚本选择按钮和显示区域
        script_select_layout = QHBoxLayout()
        
        self.select_script_btn = QPushButton("浏览本地文件")
        self.select_script_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 18px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:disabled {
                color: #888888;
                border: 2px solid #888888;
            }
        """)
        self.select_script_btn.clicked.connect(self.select_local_file)
        script_select_layout.addWidget(self.select_script_btn)
        
        # 显示选中的脚本文件路径
        self.script_path_label = QLabel("未选择脚本文件")
        self.script_path_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                padding: 10px;
                border: 1px solid #666666;
                border-radius: 5px;
                background-color: #2d2d2d;
            }
        """)
        self.script_path_label.setWordWrap(True)
        script_select_layout.addWidget(self.script_path_label, 1)
        
        script_layout.addLayout(script_select_layout)
        
        layout.addWidget(script_group)
        
        # 输出显示区域
        output_group = QGroupBox("执行输出")
        output_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 18px;
                border: 1px solid white;
                border-radius: 5px;
                padding: 10px;
                margin-top: 10px;
            }
        """)
        output_layout = QVBoxLayout(output_group)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumSize(1000, 500)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: white;
                font-family: Consolas, Monaco, monospace;
                font-size: 14px;
                border: 1px solid #333333;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        output_layout.addWidget(self.output_text)
        
        layout.addWidget(output_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 开始执行按钮
        self.start_btn = QPushButton("开始执行")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 24px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:disabled {
                color: #888888;
                border: 2px solid #888888;
            }
        """)
        self.start_btn.clicked.connect(self.start_execution)
        self.start_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn, alignment=Qt.AlignCenter)
        
        # 清空输出按钮
        self.clear_btn = QPushButton("清空输出")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 24px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:disabled {
                color: #888888;
                border: 2px solid #888888;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_output)
        button_layout.addWidget(self.clear_btn, alignment=Qt.AlignCenter)
        
        layout.addLayout(button_layout)
    
    def select_local_file(self):
        """选择本地文件"""
        try:
            dialog = LocalFileDialog(self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_file:
                self.selected_script_path = dialog.selected_file
                self.script_path_label.setText(f"已选择: {self.selected_script_path}")
                self.script_path_label.setStyleSheet("""
                    QLabel {
                        color: #00ff00;
                        font-size: 16px;
                        padding: 10px;
                        border: 1px solid #00ff00;
                        border-radius: 5px;
                        background-color: #2d2d2d;
                    }
                """)
                self.start_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法浏览本地文件: {str(e)}")
    
    def start_execution(self):
        """开始执行脚本"""
        if not self.selected_script_path:
            QMessageBox.warning(self, "警告", "请先选择要执行的脚本文件")
            return
            
        script_path = self.selected_script_path
        
        self.start_btn.setEnabled(False)
        self.output_text.clear()
        self.output_text.append(f"正在开始执行本地脚本: {script_path}\n")
        
        # 创建并启动执行线程
        self.execution_thread = ExecutionThread(script_path)
        self.execution_thread.update_signal.connect(self.update_output)
        self.execution_thread.finished_signal.connect(self.execution_finished)
        self.execution_thread.start()
    
    def clear_output(self):
        """清空输出"""
        self.output_text.clear()
    
    def update_output(self, text):
        """更新输出显示"""
        self.output_text.insertPlainText(text + '\n')
        self.output_text.moveCursor(self.output_text.textCursor().End)
        self.output_text.ensureCursorVisible()
        self.output_text.repaint()
        QApplication.processEvents()
    
    def execution_finished(self, success):
        """脚本执行完成处理"""
        # 1. 获取终端输出
        result_text = self.output_text.toPlainText()
        idx = result_text.find("评估指标")
        if idx != -1:
            # 2. 增加upload_id并保存结果
            global_state = GlobalState.get_instance()
            global_state.upload_id = getattr(global_state, 'upload_id', 0) + 1
            upload_id = global_state.upload_id - 1  # 使用增加前的ID作为文件名
            cache_path = f"/tmp/classification_result_cache_{upload_id}.txt"
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(result_text[idx:])

        if success:
            self.output_text.append("\n脚本执行完成！")
            QMessageBox.information(self, "完成", "脚本执行完成！")
            
            # 通知主窗口执行完成
            main_page = None
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, 'step_completed'):
                    main_page = parent
                    break
                parent = parent.parent()
            
            if main_page:
                main_page.step_completed[3] = True
                main_page.set_button_enabled(main_page.buttons[4], True)
        else:
            self.output_text.append("\n脚本执行失败！")
            QMessageBox.critical(self, "错误", "脚本执行过程中出现错误，请检查输出日志。")
            self.start_btn.setEnabled(True)