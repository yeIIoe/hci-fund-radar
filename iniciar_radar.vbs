' Sobe o painel sem janela. A pasta vem de ScriptFullName, nunca escrita a mao,
' porque o caminho tem acento e o Windows Script Host le este arquivo como ANSI.
Dim fso, pasta, alvo
Set fso = CreateObject("Scripting.FileSystemObject")
pasta = fso.GetParentFolderName(WScript.ScriptFullName)
alvo = fso.BuildPath(pasta, "manter_radar.bat")
If Not fso.FileExists(alvo) Then
  WScript.Echo "nao achei: " & alvo
  WScript.Quit 1
End If
CreateObject("WScript.Shell").Run """" & alvo & """", 0, False
