from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QMessageBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from ssh_manager import SSHManager
from global_state import GlobalState

class TaskSelectionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ssh_manager = SSHManager.get_instance()
        self.selected_task = None
        self.initUI()
        
    def initUI(self):
        layout = QHBoxLayout(self)
        
        # 左侧保持空白
        layout.addStretch(1)
        
        # 中间配置表单
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(20)
        
        # 标题
        title = QLabel("选择任务")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
            }
        """)
        form_layout.addWidget(title, alignment=Qt.AlignCenter)
        
        # 任务类型标签
        task_label = QLabel("任务类型：")
        task_label.setStyleSheet("color: white; font-size: 24px;")
        form_layout.addWidget(task_label)
        
        # 单选按钮组
        self.button_group = QButtonGroup(self)
        
        # 单选按钮样式
        radio_style = """
            QRadioButton {
                color: white;
                font-size: 24px;
                padding: 5px;
            }
            QRadioButton::indicator {
                width: 15px;
                height: 15px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid white;
                border-radius: 9px;
                background-color: transparent;
            }
            QRadioButton::indicator:checked {
                border: 2px solid white;
                border-radius: 9px;
                background-color: white;
            }
        """
        
        # 创建单选按钮
        tasks = ["二分类", "多分类", "回归"]
        for i, task in enumerate(tasks):
            radio = QRadioButton(task)
            radio.setStyleSheet(radio_style)
            self.button_group.addButton(radio, i)
            form_layout.addWidget(radio)
        
        # 默认选择第一个选项
        self.button_group.button(0).setChecked(True)
        
        # 添加一些垂直间距
        form_layout.addSpacing(20)
        
        # 确认按钮
        self.confirm_btn = QPushButton("确认选择")
        self.confirm_btn.setStyleSheet("""
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
        """)
        self.confirm_btn.clicked.connect(self.confirm_task)
        form_layout.addWidget(self.confirm_btn, alignment=Qt.AlignCenter)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: white; font-size: 24px;")
        form_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        
        # 添加表单到布局
        layout.addWidget(form_widget)
        
        # 右侧保持空白
        layout.addStretch(1)
        
        # 设置表单的最大宽度
        form_widget.setFixedWidth(400)
        
    def confirm_task(self):
        """确认任务选择"""
        selected_button = self.button_group.checkedButton()
        if selected_button:
            self.selected_task = selected_button.text()
            
            try:
                # 保存任务类型到全局状态
                global_state = GlobalState.get_instance()
                global_state.task_type = self.selected_task
                print(f"Task type saved globally: {global_state.task_type}")  # 调试信息
                
                # 可以在这里通过SSH执行一些任务相关的初始化命令
                output, error = self.ssh_manager.execute_command('echo "Task initialization test"')
                if error:
                    raise Exception(error)
                
                # 更新状态
                self.status_label.setText("任务选择成功!")
                self.status_label.setStyleSheet("color: #00ff00; font-size: 24px;")
                
                # 禁用选择和确认按钮
                self.disable_inputs()
                
                # 通知父窗口任务选择完成
                main_page = None
                parent = self.parent()
                while parent is not None:
                    if hasattr(parent, 'step_completed'):
                        main_page = parent
                        break
                    parent = parent.parent()
                
                if main_page:
                    main_page.step_completed[1] = True
                    main_page.set_button_enabled(main_page.buttons[2], True)
                    QMessageBox.information(self, "选择成功", f'已选择{self.selected_task}任务，请点击"上传数据"继续。')
                else:
                    QMessageBox.warning(self, "警告", "无法更新任务状态。")
                    
            except Exception as e:
                self.status_label.setText("任务选择失败")
                self.status_label.setStyleSheet("color: #ff0000; font-size: 24px;")
                QMessageBox.critical(self, "错误", f"任务选择失败：{str(e)}")
                self.enable_inputs()
    
    def disable_inputs(self):
        """禁用输入和确认按钮"""
        for button in self.button_group.buttons():
            button.setEnabled(False)
            button.setStyleSheet("""
                QRadioButton {
                    color: #888888;
                    font-size: 24px;
                    padding: 5px;
                }
                QRadioButton::indicator {
                    width: 15px;
                    height: 15px;
                }
                QRadioButton::indicator:unchecked {
                    border: 2px solid #888888;
                    border-radius: 9px;
                    background-color: transparent;
                }
                QRadioButton::indicator:checked {
                    border: 2px solid #888888;
                    border-radius: 9px;
                    background-color: #888888;
                }
            """)
        
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: 2px solid #888888;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 24px;
                min-width: 120px;
            }
        """)
    
    def enable_inputs(self):
        """启用输入和确认按钮"""
        for button in self.button_group.buttons():
            button.setEnabled(True)
            button.setStyleSheet("""
                QRadioButton {
                    color: white;
                    font-size: 24px;
                    padding: 5px;
                }
                QRadioButton::indicator {
                    width: 15px;
                    height: 15px;
                }
                QRadioButton::indicator:unchecked {
                    border: 2px solid white;
                    border-radius: 9px;
                    background-color: transparent;
                }
                QRadioButton::indicator:checked {
                    border: 2px solid white;
                    border-radius: 9px;
                    background-color: white;
                }
            """)
        
        self.confirm_btn.setEnabled(True)
        self.confirm_btn.setStyleSheet("""
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
        """) 