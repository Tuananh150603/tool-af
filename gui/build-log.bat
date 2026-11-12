@echo off
REM Chay build.bat va ghi TOAN BO ket qua ra file build-log.txt.
REM Cach dung: copy file nay vao thu muc gui (cung cho voi build.bat),
REM bam dup de chay. Sau do mo build-log.txt va gui noi dung cho Muse.
REM (echo. | ... de cac lenh pause ben trong build.bat tu chay tiep,
REM  khong dung lai cho bam phim giua chung.)
setlocal
cd /d "%~dp0"
set LOG=%~dp0build-log.txt
echo Build log - %DATE% %TIME% > "%LOG%"
echo Thu muc: %CD% >> "%LOG%"
echo. >> "%LOG%"
echo. | call build.bat >> "%LOG%" 2>&1
echo. >> "%LOG%"
echo [KET THUC] errorlevel: %ERRORLEVEL% >> "%LOG%"
type "%LOG%"
pause
