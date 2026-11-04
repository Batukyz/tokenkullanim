@echo off
start "" pythonw "%~dp0widget.py"
if errorlevel 1 (
    start "" python "%~dp0widget.py"
)
exit
