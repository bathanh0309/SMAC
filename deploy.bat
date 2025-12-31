@echo off
cd /d "%~dp0"

:: 1. Kich hoat moi truong ao (neu co)
if exist .venv\Scripts\activate (
    echo Dang kich hoat .venv...
    call .venv\Scripts\activate
)

:: 2. Dam bao remote dung
git remote remove origin 2>nul
git remote add origin https://github.com/bathanh0309/SMAC

:: 3. Thuc hien quy trinh Git
:: (File .gitignore da loai tru: __pycache__, .venv, node_modules)
echo Dang them file vao git...
git add .

echo Su dung tieu de: project DUT
git commit -m "project DUT"

echo Dang day code len GitHub...
git branch -M main
git push -u origin main

echo Hoan tat!
pause
