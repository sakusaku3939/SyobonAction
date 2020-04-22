Set shell = WScript.CreateObject("WScript.Shell")

Set shortCut = shell.CreateShortcut("..\‚µ‚å‚Ú‚ñ‚ÌƒAƒNƒVƒ‡ƒ“.lnk")
path = Left(shell.CurrentDirectory, InStrRev(shell.CurrentDirectory, "\") - 1)
shortCut.TargetPath = path & "\build\exe.win-amd64-3.8\Main.exe"
shortCut.IconLocation = path & "\build\exe.win-amd64-3.8\res\icon.ico"
shortCut.Save