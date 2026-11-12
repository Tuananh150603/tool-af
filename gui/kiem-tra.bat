@echo off
REM Kiem tra moi truong truoc khi build Tool AF GUI.
REM Cach dung: copy file nay vao thu muc gui (cung cho voi build.bat),
REM bam dup de chay. Ket qua ghi ra file ket-qua.txt trong cung thu muc.
setlocal
cd /d "%~dp0"
set LOG=%~dp0ket-qua.txt
echo Tool AF - kiem tra moi truong > "%LOG%"
echo Ngay gio: %DATE% %TIME% >> "%LOG%"
echo. >> "%LOG%"
echo [1] Thu muc dang chay: %CD% >> "%LOG%"
echo [2] File trong thu muc gui: >> "%LOG%"
dir /b >> "%LOG%"
echo. >> "%LOG%"
echo [3] Python: >> "%LOG%"
python --version >> "%LOG%" 2>&1
echo errorlevel: %ERRORLEVEL% >> "%LOG%"
where python >> "%LOG%" 2>&1
echo. >> "%LOG%"
echo [4] File o thu muc cha (tool root): >> "%LOG%"
if exist "..\captions.txt" (echo CO - ..\captions.txt >> "%LOG%") else (echo KHONG CO - ..\captions.txt >> "%LOG%")
if exist "..\comments.txt" (echo CO - ..\comments.txt >> "%LOG%") else (echo KHONG CO - ..\comments.txt >> "%LOG%")
if exist "..\Uploadvideo_multipage.py" (echo CO - ..\Uploadvideo_multipage.py >> "%LOG%") else (echo KHONG CO - ..\Uploadvideo_multipage.py >> "%LOG%")
echo. >> "%LOG%"
echo [5] requirements.txt trong thu muc gui: >> "%LOG%"
if exist "requirements.txt" (echo CO >> "%LOG%") else (echo KHONG CO >> "%LOG%")
echo. >> "%LOG%"
echo [XONG] Mo file ket-qua.txt de xem ket qua. >> "%LOG%"
type "%LOG%"
pause
