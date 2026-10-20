@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
call "C:\Users\504\miniconda1\condabin\conda.bat" activate addressbook
cd /d "%~dp0"
python addressBook.py
pause
