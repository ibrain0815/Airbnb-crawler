@echo off
chcp 65001 > nul
echo ========================================
echo  에어비앤비 크롤러 설치 파일 빌드
echo ========================================
echo.

REM 1. exe가 없으면 먼저 빌드
if not exist "dist\AirbnbCrawler.exe" (
    echo [1/2] dist\AirbnbCrawler.exe 가 없습니다. 먼저 exe를 빌드합니다...
    call build.bat
    if not exist "dist\AirbnbCrawler.exe" (
        echo 오류: exe 빌드 실패. build.bat을 먼저 실행하세요.
        pause
        exit /b 1
    )
) else (
    echo [1/2] dist\AirbnbCrawler.exe 확인됨
)

REM 2. Inno Setup 컴파일러 찾기
set ISCC=
if exist "%ProgramFiles(x86)\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles(x86)\Inno Setup 5\ISCC.exe" set "ISCC=%ProgramFiles(x86)\Inno Setup 5\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles%\Inno Setup 5\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 5\ISCC.exe"

if "%ISCC%"=="" (
    echo.
    echo [2/2] Inno Setup이 설치되어 있지 않습니다.
    echo.
    echo 설치 방법:
    echo   1. https://jrsoftware.org/isinfo.php 에서 Inno Setup 다운로드
    echo   2. 설치 후 build_installer.bat 을 다시 실행
    echo.
    pause
    exit /b 1
)

echo [2/2] 설치 파일 생성 중...
"%ISCC%" "AirbnbCrawler.iss"
if %ERRORLEVEL% neq 0 (
    echo 오류: 설치 파일 빌드 실패
    pause
    exit /b 1
)

echo.
echo ========================================
echo  완료: output\AirbnbCrawler_Setup.exe
echo ========================================
pause
