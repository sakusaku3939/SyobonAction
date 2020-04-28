cd /d %~dp0
setup.py build
xcopy .\res .\build\exe.win-amd64-3.8\res /s/e/i/y
xcopy .\SE .\build\exe.win-amd64-3.8\SE /s/e/i/y
xcopy .\BGM .\build\exe.win-amd64-3.8\BGM /s/e/i/y
pause