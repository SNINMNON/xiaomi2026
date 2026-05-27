@echo off
REM ================================================================
REM build_and_flash.bat  -  Build and flash STUDYGUARD_A_U1P
REM Adapter: CMSIS-DAP  |  Target: GD32F470ZK (stm32f4x driver)
REM Requires cmake, ninja, arm-none-eabi-gcc, openocd in system PATH.
REM ================================================================
setlocal
cd /d "%~dp0."

echo [BUILD] Configuring CMake...
cmake -B build_sg -S . -G "Ninja" "-DCMAKE_TOOLCHAIN_FILE=arm-none-eabi.cmake" -DCMAKE_BUILD_TYPE=Release
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] CMake configuration failed!
    pause & exit /b 1
)

echo [BUILD] Compiling...
cmake --build build_sg
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed!
    pause & exit /b 1
)

echo [FLASH] Flashing build_sg\STUDYGUARD_A_U1P.hex ...
openocd -f gd32f470zk.cfg -c "program build_sg/STUDYGUARD_A_U1P.hex verify reset exit"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Flash failed! Is your debugger connected?
    pause & exit /b 1
)

echo [DONE] Build and flash succeeded!
pause
