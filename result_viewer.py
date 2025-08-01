from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QTextEdit, QLabel
from PyQt5.QtCore import Qt
from ssh_manager import SSHManager
from global_state import GlobalState
import re
import os

class ResultViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_type = GlobalState.get_instance().task_type
        self.upload_id = GlobalState.get_instance().upload_id
        
        # 检查task_type是否已设置
        if self.task_type is None:
            self.init_error_ui("请先选择任务类型")
            return
            
        self.section_titles, self.section_patterns = self.get_sections(self.task_type)
        self.initUI()
        self.load_results()

    def init_error_ui(self, error_message):
        """初始化错误界面"""
        layout = QVBoxLayout(self)
        error_label = QLabel(error_message)
        error_label.setStyleSheet("color: red; font-size: 18px;")
        error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(error_label)
        
        # 添加提示信息
        hint_label = QLabel("请先完成以下步骤：\n1. 选择任务类型\n2. 上传数据\n3. 开始训练")
        hint_label.setStyleSheet("color: white; font-size: 14px; margin-top: 20px;")
        hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint_label)

    def get_sections(self, task_type):
        if task_type == "二分类":
            titles = ["评估指标", "混淆矩阵分析", "保存结果", "可视化图表", "详细分类报告", "主要特点", "时间性能", "最终性能", "输出文件"]
            patterns = [r"评估指标", r"混淆矩阵分析", r"保存结果", r"生成可视化图表", r"详细分类报告",
                        r"信用卡违约预测总结", r"时间性能:", r"最终性能:", r"输出文件:"]
        elif task_type == "多分类":
            titles = ["评估指标", "混淆矩阵分析", "保存结果", "可视化图表", "详细分类报告", "主要特点", "时间性能", "最终性能", "输出文件"]
            patterns = [r"评估指标", r"混淆矩阵分析", r"保存结果", r"生成可视化图表", r"详细分类报告",
                        r"多分类任务总结", r"时间性能:", r"最终性能:", r"输出文件:"]
        elif task_type == "回归":
            titles = ["评估指标", "预测值分析", "相对误差分析", "保存结果", "可视化图表", "主要改进", "时间性能", "最终性能", "输出文件"]
            patterns = [r"评估指标", r"预测值分析", r"相对误差分析", r"保存结果", r"生成可视化图表",
                        r"SGemm回归预测总结", r"时间性能:", r"最终性能:", r"输出文件:"]
        else:
            titles, patterns = [], []
        return titles, patterns

    def initUI(self):
        main_layout = QVBoxLayout(self)
        # 两排按钮
        btn_layout1 = QHBoxLayout()
        btn_layout2 = QHBoxLayout()
        self.buttons = []
        for i, title in enumerate(self.section_titles):
            btn = QPushButton(title)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=i: self.switch_section(idx))
            btn.setStyleSheet("font-size:18px; min-width:120px; min-height:36px;")
            self.buttons.append(btn)
            if i < 5:
                btn_layout1.addWidget(btn)
            else:
                btn_layout2.addWidget(btn)
        main_layout.addLayout(btn_layout1)
        main_layout.addLayout(btn_layout2)
        # 内容区
        self.stacked = QStackedWidget()
        for _ in self.section_titles:
            text = QTextEdit()
            text.setReadOnly(True)
            self.stacked.addWidget(text)
        main_layout.addWidget(self.stacked)
        # 默认选中第一个
        self.switch_section(0)

    def load_results(self):
        try:
            # 查找最新的缓存文件（upload_id最大的）
            cache_dir = "/tmp"
            cache_files = []
            
            # 检查目录是否存在
            if not os.path.exists(cache_dir):
                self.stacked.widget(0).setText("缓存目录不存在")
                return
                
            for file in os.listdir(cache_dir):
                if file.startswith("classification_result_cache_") and file.endswith(".txt"):
                    try:
                        upload_id = int(file.replace("classification_result_cache_", "").replace(".txt", ""))
                        cache_files.append((upload_id, file))
                    except ValueError:
                        continue
            
            if not cache_files:
                self.stacked.widget(0).setText("未找到结果缓存文件\n请先完成训练")
                return
            
            # 使用upload_id最大的缓存文件（最新的训练结果）
            latest_upload_id, latest_file = max(cache_files, key=lambda x: x[0])
            cache_path = os.path.join(cache_dir, latest_file)
            
            # 更新global_state中的upload_id为最新值
            global_state = GlobalState.get_instance()
            global_state.upload_id = latest_upload_id
            
            print(f"正在读取最新的训练结果: {latest_file} (upload_id: {latest_upload_id})")
            
            with open(cache_path, "r", encoding="utf-8") as f:
                content = f.read()
            tab_contents = self.split_sections(content, self.section_patterns)
            for idx, text in tab_contents.items():
                self.stacked.widget(idx).setText(text.strip())
                
        except Exception as e:
            print(f"加载结果时出错: {e}")
            self.stacked.widget(0).setText(f"加载结果时出错: {str(e)}")

    def split_sections(self, content, patterns):
        tab_contents = {}
        
        # 确保第一个分栏（评估指标）总是有内容
        if content.strip():
            tab_contents[0] = content
        
        # 尝试匹配其他分栏
        for i, pattern in enumerate(patterns[1:], 1):
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                start = match.start()
                # 找到下一个匹配项的位置
                end = len(content)
                for j, next_pattern in enumerate(patterns[i+1:], i+1):
                    next_match = re.search(next_pattern, content, re.MULTILINE)
                    if next_match and next_match.start() > start:
                        end = next_match.start()
                        break
                tab_contents[i] = content[start:end].strip()
        
        return tab_contents

    def switch_section(self, idx):
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == idx)
            btn.setStyleSheet(
                "font-size:18px; min-width:120px; min-height:36px;"
                + ("background-color:#444; color:#00ff00;" if i == idx else "")
            )
        self.stacked.setCurrentIndex(idx)

    def set_section_content(self, idx, content):
        widget = self.stacked.widget(idx)
        widget.setText(content) 