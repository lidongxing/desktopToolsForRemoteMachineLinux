import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QSplashScreen, QWidget,
                           QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont
import time
from system_config import SystemConfigWidget
from ssh_manager import SSHManager
from task_selection import TaskSelectionWidget
from upload_data import UploadDataWidget
from training_widget import TrainingWidget
from result_viewer import ResultViewer

# 定义全局样式
GLOBAL_STYLE = """
QWidget {
    background-color: #1a2634;
    color: white;
}

QPushButton {
    background-color: transparent;
    color: white;
    border: 2px solid white;
    border-radius: 10px;
    padding: 15px 30px;
    min-width: 200px;
}

QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.1);
}

QLabel {
    color: white;
}
"""

class WelcomeScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        pixmap = QPixmap("welcome.png")
        self.setPixmap(pixmap)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.showMessage("欢迎使用 XGBoost-NPU 软件", Qt.AlignBottom | Qt.AlignCenter, Qt.white)

class WelcomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置全局样式
        # self.setStyleSheet("""
        #     QLabel, QPushButton, QTextEdit, QLineEdit, QComboBox {
        #         font-size: 14pt;
        #     }
        #     QMessageBox {
        #         font-size: 14pt;
        #     }
        #     QMessageBox QPushButton {
        #         font-size: 14pt;
        #         min-width: 80px;
        #         padding: 5px;
        #     }
        # """)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setSpacing(0)
        
        # 添加中间的大文字
        title_label = QLabel("Welcome to XGBoost-NPU")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 96px;
                font-family: Arial;
                margin-bottom: 100px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        content_layout.addStretch(1)
        content_layout.addWidget(title_label)
        content_layout.addSpacing(5)
        
        # 添加"点击进入"按钮
        enter_button = QPushButton("点击进入>>")
        enter_button.setFixedSize(200, 65)
        enter_button.setFont(QFont("Arial", 14))
        content_layout.addWidget(enter_button, 0, Qt.AlignCenter)
        content_layout.addStretch(1)
        
        layout.addWidget(content_container)
        
        # 连接按钮点击事件
        enter_button.clicked.connect(self.parent().showMainPage)

    def create_welcome_page(self):
        """创建欢迎页面"""
        welcome_widget = QWidget()
        layout = QVBoxLayout(welcome_widget)
        
        # 欢迎标题
        title = QLabel("Welcome to XGBoost-NPU")
        # 直接设置字体
        font = QFont()
        font.setPointSize(48)  # 设置字体大小
        font.setBold(True)     # 设置粗体
        title.setFont(font)
        title.setStyleSheet("color: white;")  # 只设置颜色
        title.setAlignment(Qt.AlignCenter)
        
        # 进入按钮
        enter_button = QPushButton("点击进入")
        button_font = QFont()
        button_font.setPointSize(24)  # 设置按钮字体大小
        enter_button.setFont(button_font)
        enter_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 15px 30px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        enter_button.clicked.connect(self.show_main_interface)
        
        # 调整布局
        layout.addStretch(2)
        layout.addWidget(title)
        layout.addSpacing(90)
        layout.addWidget(enter_button, alignment=Qt.AlignCenter)
        layout.addStretch(3)
        
        return welcome_widget

class MainPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.step_completed = [False] * 5
        self.current_right_widget = None
        self.initUI()
        
    def initUI(self):
        # 使用水平布局
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(50)
        main_layout.setContentsMargins(200, 20, 200, 20)
        
        # 左侧按钮区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(0, 0, 0, 0)  # 移除左侧容器的边距
        
        button_texts = [
            "1. 系统配置",
            "2. 选择任务",
            "3. 上传数据",
            "4. 开始训练",
            "5. 查看结果",
            "6. 退出"
        ]
        
        self.buttons = []
        left_layout.addStretch(1)
        
        for i, text in enumerate(button_texts):
            # 创建一个容器来包含按钮，确保按钮不会超出容器
            button_container = QWidget()
            button_container.setFixedWidth(380)  # 设置容器宽度
            container_layout = QVBoxLayout(button_container)
            container_layout.setContentsMargins(0, 0, 0, 0)  # 移除容器内边距
            
            button = QPushButton(text)
            self.buttons.append(button)
            button.setFont(QFont("Arial", 24, QFont.Bold))
            button.setFixedSize(380, 60)  # 设置按钮固定大小
            
            if i < 5:
                if i == 0:
                    self.set_button_enabled(button, True)
                else:
                    self.set_button_enabled(button, False)
                button.clicked.connect(lambda checked, index=i: self.handle_step_button(index))
            else:
                self.set_button_enabled(button, True)
                button.clicked.connect(self.handle_quit)
            
            container_layout.addWidget(button)
            left_layout.addWidget(button_container)
            
            if i < len(button_texts) - 1:
                arrow_label = QLabel("⬇")
                arrow_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
                arrow_label.setAlignment(Qt.AlignCenter)
                left_layout.addWidget(arrow_label)
        
        left_layout.addStretch(1)
        
        # 右侧内容区域
        self.right_widget = QWidget()
        self.right_widget.setMinimumSize(800, 600)
        
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.setContentsMargins(30, 30, 30, 30)
        self.right_layout.setSpacing(20)
        self.right_layout.setAlignment(Qt.AlignCenter)
        
        main_layout.addWidget(left_widget, alignment=Qt.AlignLeft)
        main_layout.addWidget(self.right_widget, 1)
        
    def handle_step_button(self, step_index):
        """处理步骤按钮的点击事件"""
        try:
            if self.current_right_widget:
                self.right_layout.removeWidget(self.current_right_widget)
                self.current_right_widget.deleteLater()
                self.current_right_widget = None
            
            # 创建新的部件
            if step_index == 0:  # 系统配置
                self.current_right_widget = SystemConfigWidget(self)
            elif step_index == 1:  # 任务选择
                self.current_right_widget = TaskSelectionWidget(self)
            elif step_index == 2:  # 上传数据
                self.current_right_widget = UploadDataWidget(self)
            elif step_index == 3:  # 开始训练
                self.current_right_widget = TrainingWidget(self)
            elif step_index == 4:  # 查看结果
                self.current_right_widget = ResultViewer(self)
            
            if self.current_right_widget:
                # 设置右侧部件的大小策略和最小尺寸
                self.current_right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                self.current_right_widget.setMinimumSize(700, 500)  # 设置内容区域的最小尺寸
                # 添加到布局并设置对齐方式
                self.right_layout.addWidget(self.current_right_widget, alignment=Qt.AlignCenter)
                
        except Exception as e:
            print(f"创建步骤 {step_index} 的界面时出错: {e}")
            # 显示错误信息
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "错误", f"创建界面时出错: {str(e)}")

    def set_button_enabled(self, button, enabled):
        """设置按钮的启用状态和样式"""
        button.setEnabled(enabled)
        base_style = """
            QPushButton {
                background-color: transparent;
                color: %s;
                border: 2px solid %s;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 24px;
                text-align: left;
                padding-left: 20px;
            }
        """
        
        if enabled:
            button.setStyleSheet(
                base_style % ("white", "white") +
                """
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
                """
            )
        else:
            button.setStyleSheet(base_style % ("gray", "gray"))

    def handle_quit(self):
        """处理退出按钮点击事件"""
        try:
            # 关闭SSH连接
            ssh_manager = SSHManager.get_instance()
            if ssh_manager.ssh_client:
                ssh_manager.close()
                print("SSH连接已关闭")
        except Exception as e:
            print(f"关闭SSH连接时出错: {e}")
        finally:
            # 退出应用程序
            QApplication.instance().quit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('XGBoost-NPU 训练平台')
        self.setGeometry(100, 100, 1960, 1050)
        
        # 设置最小窗口大小
        # self.setMinimumSize(800, 600)
        
        # 应用全局样式
        self.setStyleSheet(GLOBAL_STYLE)
        
        # 创建堆叠部件来管理页面
        self.welcome_page = WelcomePage(self)
        self.main_page = MainPage(self)
        
        # 初始显示欢迎页面
        self.setCentralWidget(self.welcome_page)
        
    def showMainPage(self):
        # 切换到主页面
        self.setCentralWidget(self.main_page)

def main():
    app = QApplication(sys.argv)
    
    # # 显示欢迎界面
    # splash = WelcomeScreen()
    # splash.show()
    
    # 创建主窗口但先不显示
    main_window = MainWindow()
    
    # 10秒后关闭欢迎界面，显示主窗口
    # QTimer.singleShot(10000, splash.close)
    QTimer.singleShot(10000, main_window.show)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 


# # 在其他模块中使用SSH连接
# ssh_manager = SSHManager.get_instance()
# output, error = ssh_manager.execute_command('your_command_here')