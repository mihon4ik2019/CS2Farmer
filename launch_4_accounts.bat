@echo off
chcp 65001 >nul
title CS2Farmer - 4 Account Multi-Instance Launcher

echo =====================================================
echo    CS2Farmer - Запуск 4 аккаунтов параллельно
echo    Режим: Без Sandboxie, с IPC изоляцией
echo =====================================================
echo.

:: Проверка прав администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] ВНИМАНИЕ: Программа требует прав администратора
    echo [!] Перезапуск с повышенными правами...
    echo.
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo [✅] Запущено от имени администратора
echo.

:: Пути
set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=python"
set "MAIN_SCRIPT=src\python\main.py"

:: Проверка Python
echo [*] Проверка Python...
%PYTHON_EXE% --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Python не найден. Установите Python 3.11+
    echo [!] https://www.python.org/downloads/
    pause
    exit /b 1
)
%PYTHON_EXE% --version
echo.

:: Установка зависимостей
echo [*] Установка зависимостей...
%PYTHON_EXE% -m pip install -q -r requirements.txt
if %errorLevel% neq 0 (
    echo [!] Ошибка установки зависимостей
    pause
    exit /b 1
)
echo [✅] Зависимости установлены
echo.

:: Проверка mafiles
echo [*] Проверка mafiles...
if not exist "mafiles" (
    echo [!] Папка mafiles не найдена
    echo [!] Добавьте .maFile файлы аккаунтов в папку mafiles/
    pause
    exit /b 1
)

set "MAFILE_COUNT=0"
for %%f in (mafiles\*.maFile) do set /a MAFILE_COUNT+=1
echo [✅] Найдено аккаунтов: %MAFILE_COUNT%
echo.

:: Информация
echo =====================================================
echo   ИНСТРУКЦИЯ:
echo   1. Добавьте минимум 4 аккаунта в mafiles/
echo   2. В панели выберите 4 аккаунта для запуска
echo   3. Нажмите "Start All" или "Start Selected"
echo   4. Окна расположатся в сетке 2x2 автоматически
echo =====================================================
echo.
echo [i] Параметры CS2 применены из config.py
echo [i] Параметры Steam применены из config.py
echo [i] Каждый аккаунт использует уникальный IPC
echo [i] BES применится автоматически (50%% CPU лимит)
echo.

:: Запуск
echo [*] Запуск панели управления...
echo.
%PYTHON_EXE% "%MAIN_SCRIPT%"

echo.
echo [*] Панель закрыта
echo [*] При необходимости завершите процессы:
echo     taskkill /f /im cs2.exe
echo     taskkill /f /im steam.exe
echo.
pause