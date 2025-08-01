from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, QApplication)
from PyQt5.QtCore import Qt
import paramiko
from ssh_manager import SSHManager

class SystemConfigWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ssh_manager = SSHManager.get_instance()
        self.initUI()
        
    def initUI(self):
        # 使用垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(20)
        
        # 标题
        title = QLabel("系统配置")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # 表单容器
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(15)
        
        # 创建输入框组
        self.ip_input = self.create_input_group("IP地址：")
        self.port_input = self.create_input_group("端口号：")
        self.username_input = self.create_input_group("用户名：")
        self.password_input = self.create_input_group("密码：", is_password=True)
        
        # 添加所有输入组到表单布局
        form_layout.addWidget(self.ip_input)
        form_layout.addWidget(self.port_input)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)
        
        # 添加表单到主布局
        main_layout.addWidget(form_widget)
        
        # 连接按钮
        self.connect_btn = QPushButton("连接")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 24px;
                font-weight: bold;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.connect_btn.clicked.connect(self.try_connect)
        main_layout.addWidget(self.connect_btn, alignment=Qt.AlignCenter)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: white; font-size: 14px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
    def create_input_group(self, label_text, is_password=False):
        group = QWidget()
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(label_text)
        label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        label.setFixedWidth(150)
        
        input_field = QLineEdit()
        if is_password:
            input_field.setEchoMode(QLineEdit.Password)
        
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid white;
                border-radius: 5px;
                padding: 8px;
                font-size: 18px;
                min-width: 300px;
            }
        """)
        
        layout.addWidget(label)
        layout.addWidget(input_field)
        layout.setSpacing(20)
        
        return group
        
    def try_connect(self):
        """尝试SSH连接"""
        # 获取输入值
        ip = self.ip_input.findChild(QLineEdit).text().strip()
        port = self.port_input.findChild(QLineEdit).text().strip()
        username = self.username_input.findChild(QLineEdit).text().strip()
        password = self.password_input.findChild(QLineEdit).text().strip()
        
        # 基本输入验证
        if not all([ip, port, username, password]):
            QMessageBox.warning(self, "输入错误", "请填写所有字段")
            return
        
        try:
            port = int(port)
        except ValueError:
            QMessageBox.warning(self, "输入错误", "端口号必须是数字")
            return
        
        # 更新状态
        self.status_label.setText("正在连接...")
        self.status_label.setStyleSheet("color: white; font-size: 14px;")
        QApplication.processEvents()
        
        # 尝试连接
        ssh_client = None
        try:
            # 创建SSH客户端
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 设置更详细的连接参数
            connect_kwargs = {
                'hostname': ip,
                'port': port,
                'username': username,
                'password': password,
                'timeout': 15,  # 增加超时时间
                'allow_agent': False,  # 禁用SSH agent
                'look_for_keys': False,  # 不查找密钥文件
                'auth_timeout': 30,  # 认证超时
                'banner_timeout': 60,  # banner超时
            }
            
            # 尝试连接
            self.status_label.setText("正在建立SSH连接...")
            QApplication.processEvents()
            
            ssh_client.connect(**connect_kwargs)
            
            # 获取连接信息
            transport = ssh_client.get_transport()
            if transport:
                remote_version = transport.remote_version
                local_version = transport.local_version
                self.status_label.setText("连接建立，正在验证...")
                QApplication.processEvents()
            
            # 测试连接并获取用户信息
            stdin, stdout, stderr = ssh_client.exec_command('whoami && pwd && id && echo "SSH_TEST_SUCCESS"')
            user_info = stdout.read().decode().strip()
            error_info = stderr.read().decode().strip()
            
            if stdout.channel.recv_exit_status() == 0 and "SSH_TEST_SUCCESS" in user_info:
                # 连接成功，保存到全局管理器
                self.ssh_manager.ssh_client = ssh_client
                
                # 更新状态
                self.status_label.setText("连接成功!")
                self.status_label.setStyleSheet("color: #00ff00; font-size: 14px;")
                
                # 禁用输入框和连接按钮
                self.disable_inputs()
                
                # 查找MainPage实例并更新状态
                main_page = None
                parent = self.parent()
                while parent is not None:
                    if hasattr(parent, 'step_completed'):
                        main_page = parent
                        break
                    parent = parent.parent()
                
                if main_page:
                    main_page.step_completed[0] = True
                    main_page.set_button_enabled(main_page.buttons[1], True)
                    
                    # 构建成功消息
                    success_msg = f'SSH连接已建立\n'
                    if transport:
                        success_msg += f'SSH版本: {remote_version}\n'
                    success_msg += f'用户信息:\n{user_info.replace("SSH_TEST_SUCCESS", "")}'
                    
                    QMessageBox.information(self, "连接成功", success_msg)
                else:
                    QMessageBox.warning(self, "警告", "无法更新任务状态，但SSH连接已建立。")
            
            else:
                raise Exception(f"连接测试失败: {error_info}")
                
        except Exception as e:
            # 连接失败
            error_msg = str(e)
            self.status_label.setText("连接失败")
            self.status_label.setStyleSheet("color: #ff0000; font-size: 14px;")
            
            detailed_error = ""
            if "Authentication failed" in error_msg:
                detailed_error = f"用户名或密码错误\n用户名: {username}\n\n请检查:\n1. 用户名是否正确\n2. 密码是否正确\n3. 用户是否有SSH登录权限\n\n建议:\n- 尝试使用root用户登录\n- 检查用户密码是否正确\n- 确认用户没有被锁定"
            elif "timeout" in error_msg.lower():
                detailed_error = "连接超时，请检查:\n1. IP地址是否正确\n2. 端口号是否正确\n3. 网络连接是否正常\n4. 防火墙设置"
            elif "Connection refused" in error_msg:
                detailed_error = "连接被拒绝，请检查:\n1. 服务器是否开启SSH服务\n2. 防火墙是否阻止连接\n3. 端口号是否正确\n4. SSH服务是否在指定端口监听"
            elif "No such file or directory" in error_msg:
                detailed_error = "用户目录不存在，请检查:\n1. 用户是否已创建\n2. 用户主目录是否存在\n3. 用户shell是否正确设置"
            elif "Permission denied" in error_msg:
                detailed_error = "权限被拒绝，请检查:\n1. 用户是否有SSH登录权限\n2. 用户是否被禁用\n3. SSH配置是否允许该用户登录\n4. 用户shell是否正确"
            elif "Host key verification failed" in error_msg:
                detailed_error = "主机密钥验证失败\n这通常是正常的，程序会自动处理"
            else:
                detailed_error = f"连接错误: {error_msg}\n\n可能的解决方案:\n1. 检查SSH服务器配置\n2. 确认用户权限\n3. 尝试使用root用户登录\n4. 检查paramiko版本兼容性\n\n调试信息:\n- 用户名: {username}\n- 服务器: {ip}:{port}"
            
            QMessageBox.critical(self, "连接错误", detailed_error)
            
            if ssh_client:
                try:
                    ssh_client.close()
                except:
                    pass
            
            # 重新启用所有输入框和连接按钮
            self.enable_inputs()

    def disable_inputs(self):
        """连接成功后禁用输入框和连接按钮"""
        for input_group in [self.ip_input, self.port_input, self.username_input, self.password_input]:
            input_field = input_group.findChild(QLineEdit)
            input_field.setEnabled(False)
            input_field.setStyleSheet("""
                QLineEdit {
                    background-color: rgba(255, 255, 255, 0.05);
                    color: #888888;
                    border: 1px solid #888888;
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 14px;
                    min-width: 200px;
                }
            """)
        
        self.connect_btn.setEnabled(False)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: 2px solid #888888;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 24px;
                font-weight: bold;
                min-width: 150px;
            }
        """)

    def enable_inputs(self):
        """重新启用输入框和连接按钮"""
        for input_group in [self.ip_input, self.port_input, self.username_input, self.password_input]:
            input_field = input_group.findChild(QLineEdit)
            input_field.setEnabled(True)
            input_field.setStyleSheet("""
                QLineEdit {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: white;
                    border: 1px solid white;
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 14px;
                    min-width: 200px;
                }
            """)
        
        self.connect_btn.setEnabled(True)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 24px;
                font-weight: bold;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)

    def closeEvent(self, event):
        """窗口关闭时不断开SSH连接"""
        event.accept() 