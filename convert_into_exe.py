import sys
from cx_Freeze import setup, Executable

"""
 cx_Freezeを使ってpygameで作られた.pyファイルを.exeに変換するスクリプト
 ※ このファイルの中身は変更しないでください
"""
base = None

if sys.platform == 'win32':
    base = 'Win32GUI'
setup(name='CHOOOSEFILE',
      version='1.0',
      description='converter',
      executables=[Executable("Main.py", targetName="SyobonAction.exe", icon="res/icon.ico", base=base)])
