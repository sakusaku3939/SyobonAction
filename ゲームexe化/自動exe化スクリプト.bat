@echo off

echo --- スクリプトを開始します。

cd /d %~dp0
cd ../
Convert_to_exe.py build
xcopy .\res .\build\exe.win-amd64-3.8\res /s/e/i/y
xcopy .\SE .\build\exe.win-amd64-3.8\SE /s/e/i/y
xcopy .\BGM .\build\exe.win-amd64-3.8\BGM /s/e/i/y
cd /d %~dp0

cscript shortcut.vbs

echo --- スクリプトが完了しました。続行するには何かキーを押してください(´・ω・`)
pause > NUL