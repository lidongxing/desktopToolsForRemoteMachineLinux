# desktopToolsForRemoteMachineLinux
a new project for xgboost in ascend NPU310B with desktop tools

linux:./main.py
windows:

1. pip install -r requirement.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

python创建软件
1. 首先创建一个 requirements.txt 文件：
PyQt5==5.15.9
paramiko==3.3.1
# 添加其他依赖包

2.创建一个打包脚本 build.py：
import PyInstaller.__main__
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'main.py',  # 主程序入口
    '--name=XGBoost-NPU',  # 程序名称
    '--windowed',  # 使用 GUI 模式
    '--onedir',  # 创建单文件夹
    '--icon=app_icon.ico',  # 程序图标（需要你提供一个.ico文件）
    '--add-data=images;images',  # 如果有图片资源
    '--clean',  # 清理临时文件
    '--noconfirm',  # 不确认覆盖
    f'--workpath={os.path.join(current_dir, "build")}',  # 工作目录
    f'--distpath={os.path.join(current_dir, "dist")}',  # 输出目录
])

3.创建 NSIS 安装脚本 installer.nsi：
!include "MUI2.nsh"

; 基本信息
Name "XGBoost-NPU Training Platform"
OutFile "XGBoost-NPU-Setup.exe"
InstallDir "$PROGRAMFILES\XGBoost-NPU"
RequestExecutionLevel admin

; 界面设置
!define MUI_ABORTWARNING
!define MUI_ICON "app_icon.ico"
!define MUI_UNICON "app_icon.ico"

; 页面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; 语言
!insertmacro MUI_LANGUAGE "SimpChinese"

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    
    ; 添加程序文件
    File /r "dist\XGBoost-NPU\*.*"
    
    ; 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\XGBoost-NPU"
    CreateShortCut "$SMPROGRAMS\XGBoost-NPU\XGBoost-NPU.lnk" "$INSTDIR\XGBoost-NPU.exe"
    CreateShortCut "$DESKTOP\XGBoost-NPU.lnk" "$INSTDIR\XGBoost-NPU.exe"
    
    ; 创建卸载程序
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; 添加卸载信息到控制面板
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\XGBoost-NPU" \
                     "DisplayName" "XGBoost-NPU Training Platform"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\XGBoost-NPU" \
                     "UninstallString" "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
    ; 删除程序文件
    RMDir /r "$INSTDIR"
    
    ; 删除开始菜单快捷方式
    Delete "$SMPROGRAMS\XGBoost-NPU\XGBoost-NPU.lnk"
    RMDir "$SMPROGRAMS\XGBoost-NPU"
    Delete "$DESKTOP\XGBoost-NPU.lnk"
    
    ; 删除注册表项
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\XGBoost-NPU"
SectionEnd

4.创建一个批处理文件 build_installer.bat 来自动化构建过程：

@echo off
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo Installing requirements...
pip install -r requirements.txt
pip install pyinstaller

echo Building application...
python build.py

echo Creating installer...
"C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi

echo Done!
pause

5.使用步骤：
安装必要的工具：
# 安装 NSIS
winget install NSIS

# 安装 Python 依赖
pip install -r requirements.txt
pip install pyinstaller

准备资源：
创建一个 app_icon.ico 文件作为程序图标
确保所有资源文件（图片等）都在正确的目录中

运行构建：
build_installer.bat




########################################
更新
1. 修改 requirements.txt：

pandas==2.2.3
numpy==1.23.2
scikit-learn==1.2.2
PyQt5==5.15.9
PyQt5-Qt5==5.15.2
PyQt5-sip==12.12.2
paramiko==3.3.1
cryptography==41.0.7
bcrypt==4.1.2
pynacl==1.5.0
setuptools>=65.5.1
wheel>=0.38.0
openpyxl==3.1.2

2. 修改 build_installer.bat，添加国内镜像源：
@echo off
chcp 65001
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo Installing requirements...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install --upgrade setuptools wheel -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt --disable-pip-version-check -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple

echo Building application...
python build.py

echo Creating installer...
"C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi

echo Done!
pause

3.清理之前的环境：
rmdir /s /q venv
rmdir /s /q build
rmdir /s /q dist

4. 重新运行构建脚本：
build_installer.bat
