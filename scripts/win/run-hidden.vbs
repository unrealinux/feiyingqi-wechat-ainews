' ============================================================================
'  Hidden-window launcher for Windows Task Scheduler.
'
'  Why this exists:
'    Task Scheduler starts a .cmd under the logged-on user, which pops up a
'    console window. WScript.Shell.Run with window style 0 keeps it hidden.
'
'  The third argument (True) means WAIT for completion, so Task Scheduler's
'  "Last Run Result" records the real exit code of the worker script instead
'  of always reporting success.
'
'  Usage: wscript.exe run-hidden.vbs "<program>" [args...]
'
'  NOTE: ASCII-only on purpose. Batch/console hosts on a Chinese Windows mix
'        GBK and UTF-8; keeping this file ASCII avoids mojibake in logs.
' ============================================================================
Option Explicit

Dim shell, command, i, rc

If WScript.Arguments.Count = 0 Then
  WScript.Echo "Usage: run-hidden.vbs <program> [args...]"
  WScript.Quit 2
End If

' First argument is the program path; quote it to survive spaces in the path
command = """" & WScript.Arguments(0) & """"

For i = 1 To WScript.Arguments.Count - 1
  command = command & " " & WScript.Arguments(i)
Next

Set shell = CreateObject("WScript.Shell")

' 0 = hidden window, True = wait and capture the exit code
rc = shell.Run(command, 0, True)

WScript.Quit rc
