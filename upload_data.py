from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QMessageBox, QFileDialog, QGroupBox,
                           QApplication)
from PyQt5.QtCore import Qt
from ssh_manager import SSHManager
import paramiko
import os
import pandas as pd
from global_state import GlobalState

class UploadDataWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ssh_manager = SSHManager.get_instance()
        # 存储选择的文件路径
        self.selected_file = None
        # 从全局状态获取任务类型
        global_state = GlobalState.get_instance()
        self.task_type = global_state.task_type
        print(f"Retrieved task type from global state: {self.task_type}")  # 调试信息
        self.remote_dir = self.get_remote_dir()
        print(f"Remote directory set to: {self.remote_dir}")
        self.initUI()
        
    def get_remote_dir(self):
        """根据任务类型确定远程目录"""
        base_dir = "/home/HwHiAiUser/Desktop/2t"
        print(f"Current task type: {self.task_type}")  # 调试信息
        
        if not self.task_type:
            print("Warning: Task type is None")
            return base_dir
        
        if self.task_type == "二分类":
            remote_dir = f"{base_dir}/binary"
        elif self.task_type == "多分类":
            remote_dir = f"{base_dir}/multiclass"
        elif self.task_type == "回归":
            remote_dir = f"{base_dir}/regression"
        else:
            remote_dir = base_dir
        
        print(f"Selected remote directory: {remote_dir}")  # 调试信息
        return remote_dir
        
    def initUI(self):
        layout = QHBoxLayout(self)
        layout.addStretch(1)
        
        # 中间表单
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(20)
        
        # 标题 - 根据任务类型动态显示
        title_text = self.get_title_text()
        title = QLabel(title_text)
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
            }
        """)
        form_layout.addWidget(title, alignment=Qt.AlignCenter)
        
        # 创建文件上传组
        group = QGroupBox("数据集文件")
        group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 24px;
                border: 1px solid white;
                border-radius: 5px;
                padding: 10px;
                margin-top: 10px;
            }
        """)
        group_layout = QVBoxLayout(group)
        
        # 文件选择按钮
        select_btn_text = self.get_select_button_text()
        select_btn = QPushButton(select_btn_text)
        select_btn.setStyleSheet(self.get_button_style())
        select_btn.clicked.connect(self.select_file)
        
        # 文件名标签
        self.file_label = QLabel("")
        self.file_label.setStyleSheet("color: white; font-size: 24px;")
        self.file_label.setWordWrap(True)
        
        group_layout.addWidget(select_btn)
        group_layout.addWidget(self.file_label)
        form_layout.addWidget(group)
        
        # 上传按钮
        self.upload_btn = QPushButton("上传文件")
        self.upload_btn.setStyleSheet(self.get_button_style())
        self.upload_btn.clicked.connect(self.upload_file)
        self.upload_btn.setEnabled(False)
        form_layout.addWidget(self.upload_btn, alignment=Qt.AlignCenter)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: white; font-size: 24px;")
        form_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        
        layout.addWidget(form_widget)
        layout.addStretch(1)
        form_widget.setFixedWidth(400)
        
    def get_button_style(self):
        return """
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 24px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:disabled {
                color: #888888;
                border: 2px solid #888888;
            }
        """
        
    def select_file(self):
        """选择数据文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据文件",
            "",
            "Data Files (*.csv *.xlsx *.xls *.txt)"
        )
        
        if file_path:
            try:
                # 验证文件格式
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext == '.csv':
                    df = pd.read_csv(file_path)
                elif file_ext in ['.xlsx', '.xls']:
                    df = pd.read_excel(file_path)
                elif file_ext == '.txt':
                    df = pd.read_csv(file_path, sep='\t')
                else:
                    raise Exception("不支持的文件格式")
                
                self.selected_file = file_path
                self.file_label.setText(f"已选择: {os.path.basename(file_path)}")
                
                # 启用上传按钮
                self.upload_btn.setEnabled(True)
                
            except Exception as e:
                self.selected_file = None
                self.file_label.setText("")
                QMessageBox.critical(self, "错误", f"无法读取文件：{str(e)}")
    
    def upload_file(self):
        """上传文件到远程服务器"""
        if not self.selected_file:
            QMessageBox.warning(self, "警告", "请先选择要上传的文件")
            return
            
        try:
            # 获取SFTP客户端
            sftp = self.ssh_manager.ssh_client.open_sftp()
            
            # 获取文件名（不含后缀）
            file_name = os.path.splitext(os.path.basename(self.selected_file))[0]
            
            # 构建远程路径
            remote_dir_path = f"{self.remote_dir}/{file_name}"
            remote_file_path = f"{remote_dir_path}/{os.path.basename(self.selected_file)}"
            
            # 创建远程目录结构并验证
            try:
                # 创建主目录
                try:
                    sftp.mkdir('/home/HwHiAiUser/Desktop/2t')
                except:
                    pass
                
                # 确保任务类型目录存在
                try:
                    sftp.mkdir(self.remote_dir)
                except:
                    pass
                
                # 创建文件专属目录
                try:
                    sftp.mkdir(remote_dir_path)
                except:
                    pass
                
                # 验证目录是否存在
                try:
                    sftp.stat(remote_dir_path)
                except IOError:
                    raise Exception(f"无法创建或访问目录: {remote_dir_path}")
                
            except Exception as e:
                raise Exception(f"目录创建失败: {str(e)}")
            
            # 更新状态
            self.status_label.setText("正在上传...")
            self.status_label.setStyleSheet("color: white; font-size: 24px;")
            QApplication.processEvents()
            
            # 上传文件
            try:
                self.status_label.setText(f"正在上传: {os.path.basename(self.selected_file)}...")
                QApplication.processEvents()
                sftp.put(self.selected_file, remote_file_path)
                
                # 验证文件是否成功上传
                try:
                    stats = sftp.stat(remote_file_path)
                    local_size = os.path.getsize(self.selected_file)
                    if stats.st_size != local_size:
                        raise Exception(f"文件大小不匹配: {os.path.basename(self.selected_file)}")
                except IOError:
                    raise Exception(f"文件上传后无法访问: {os.path.basename(self.selected_file)}")
                
            except Exception as e:
                raise Exception(f"文件上传失败: {str(e)}")
            
            # 列出目录内容进行确认
            try:
                dir_content = sftp.listdir(remote_dir_path)
                if not dir_content:
                    raise Exception("目录为空，上传可能失败")
                print(f"远程目录内容: {dir_content}")  # 调试信息
            except Exception as e:
                raise Exception(f"无法验证目录内容: {str(e)}")
            
            # 关闭SFTP连接
            sftp.close()
            
            # 更新状态
            self.status_label.setText("上传成功!")
            self.status_label.setStyleSheet("color: #00ff00; font-size: 24px;")
            
            # 禁用所有按钮
            self.disable_inputs()
            
            # 通知父窗口上传完成
            main_page = None
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, 'step_completed'):
                    main_page = parent
                    break
                parent = parent.parent()
            
            if main_page:
                main_page.step_completed[2] = True
                main_page.set_button_enabled(main_page.buttons[3], True)
                success_msg = (f'文件已上传至 {remote_file_path}\n'
                             f'上传文件: {os.path.basename(self.selected_file)}')
                QMessageBox.information(self, "上传成功", success_msg)
            else:
                QMessageBox.warning(self, "警告", "无法更新任务状态。")
                
        except Exception as e:
            self.status_label.setText("上传失败")
            self.status_label.setStyleSheet("color: #ff0000; font-size: 24px;")
            error_msg = f"文件上传失败：{str(e)}\n请检查：\n1. 远程目录权限\n2. 磁盘空间\n3. 网络连接"
            QMessageBox.critical(self, "错误", error_msg)
            self.enable_inputs()
    
    def disable_inputs(self):
        """禁用所有输入和上传按钮"""
        for child in self.findChildren(QPushButton):
            child.setEnabled(False)
            child.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #888888;
                    border: 2px solid #888888;
                    border-radius: 10px;
                    padding: 10px 20px;
                    font-size: 24px;
                    min-width: 150px;
                }
            """)
    
    def enable_inputs(self):
        """启用所有输入和上传按钮"""
        for child in self.findChildren(QPushButton):
            if child != self.upload_btn:
                child.setEnabled(True)
                child.setStyleSheet(self.get_button_style())
        
        # 只有在文件选择后才启用上传按钮
        if self.selected_file:
            self.upload_btn.setEnabled(True)
            self.upload_btn.setStyleSheet(self.get_button_style())
    
    def get_title_text(self):
        """根据任务类型获取标题文本"""
        if not self.task_type:
            return "上传数据"
        
        if self.task_type == "二分类":
            return "上传二分类任务数据"
        elif self.task_type == "多分类":
            return "上传多分类任务数据"
        elif self.task_type == "回归":
            return "上传回归任务数据"
        else:
            return "上传数据"

    def get_select_button_text(self):
        """根据任务类型获取文件选择按钮的文本"""
        if not self.task_type:
            return "选择数据文件"
        
        if self.task_type == "二分类":
            return "选择二分类任务数据文件"
        elif self.task_type == "多分类":
            return "选择多分类任务数据文件"
        elif self.task_type == "回归":
            return "选择回归任务数据文件"
        else:
            return "选择数据文件" 