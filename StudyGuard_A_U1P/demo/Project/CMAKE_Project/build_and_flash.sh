#!/bin/bash
# ================================================================
# build_and_flash.sh  -  Build and flash C2_DEMO
# Requires: arm-none-eabi-gcc and OpenOCD in PATH.
# Edit gd32f470zk.cfg to choose your debug adapter.
# ================================================================
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "[BUILD] Configuring CMake..."
cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE=arm-none-eabi.cmake -DCMAKE_BUILD_TYPE=Release
[ $? -ne 0 ] && { echo '[ERROR] CMake config failed!'; exit 1; }

echo "[BUILD] Compiling..."
cmake --build build -j$(nproc 2>/dev/null || echo 4)
[ $? -ne 0 ] && { echo '[ERROR] Build failed!'; exit 1; }

echo "[FLASH] Flashing build/C2_DEMO.hex ..."
openocd -f gd32f470zk.cfg -c "program build/C2_DEMO.hex verify reset exit"
[ $? -ne 0 ] && { echo '[ERROR] Flash failed! Is your debugger connected?'; exit 1; }

echo "[DONE] Build and flash succeeded!"
