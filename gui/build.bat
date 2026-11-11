@echo off
REM Build Tool AF GUI thanh file .exe chay tren Windows 10/11.
REM Chay file nay 1 lan tren may Han (bam dup build.bat trong thu muc gui\).
REM Ket qua: gui\dist\ToolAF.exe — copy file .exe ra cho nao cung chay duoc,
REM mien la cung may (du lieu page/pool nam o tool root + pool root da cau hinh).
setlocal

cd /d %~dp0

echo [1/4] Kiem tra Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo [!] Chua cai Python. Cai Python 3.10+ tu python.org (tick "Add python to PATH") roi chay lai.
  pause
  exit /b 1
)

echo [2/4] Tao venv (.venv-gui) neu chua co...
if not exist .venv-gui\Scripts\python.exe (
  python -m venv .venv-gui
)

echo [3/4] Cai thu vien (customtkinter, requests, imageio-ffmpeg, PyInstaller)...
.venv-gui\Scripts\python.exe -m pip install --upgrade pip
.venv-gui\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo [!] pip install loi. Kiem tra mang roi chay lai.
  pause
  exit /b 1
)

echo [4/4] Dong goi .exe bang PyInstaller (onefile, khong hien console)...
.venv-gui\Scripts\pyinstaller.exe --noconfirm --onefile --noconsole ^
  --name ToolAF --collect-all customtkinter ^
  --add-data "..\captions.txt;." --add-data "..\comments.txt;." ^
  app.py
if errorlevel 1 (
  echo [!] PyInstaller loi.
  pause
  exit /b 1
)

echo.
echo [XONG] File chay: %~dp0dist\ToolAF.exe
echo Luu y: .exe tim du lieu o thu muc chua no (tool root). De .exe cung cho
echo voi Uploadvideo_multipage.py (VD: D:\Tool AF\) hoac chay truc tiep trong
echo thu muc repo nay. Token luu trong gui_config.json (khong commit len git).
pause
