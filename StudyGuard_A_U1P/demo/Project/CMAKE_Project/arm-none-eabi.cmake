# arm-none-eabi.cmake
# CMake Toolchain file for ARM Cortex-M4 (GD32F470ZK) with arm-none-eabi-gcc
#
# Usage:
#   cmake -B build -DCMAKE_TOOLCHAIN_FILE=<path>/cmake/arm-none-eabi.cmake
#
# Prerequisites:
#   - arm-none-eabi-gcc in PATH (or set ARM_TOOLCHAIN_DIR below)
#   - Download from: https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads

# -- Optional: set explicit toolchain path (leave empty to use PATH) ----------
set(ARM_TOOLCHAIN_DIR "" CACHE PATH "Path to arm-none-eabi toolchain bin directory")

if(ARM_TOOLCHAIN_DIR)
    set(TOOLCHAIN_PREFIX "${ARM_TOOLCHAIN_DIR}/arm-none-eabi-")
else()
    set(TOOLCHAIN_PREFIX "arm-none-eabi-")
endif()

# -- System / CMake cross-compile settings ------------------------------------
set(CMAKE_SYSTEM_NAME      Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

set(CMAKE_C_COMPILER   "${TOOLCHAIN_PREFIX}gcc")
set(CMAKE_CXX_COMPILER "${TOOLCHAIN_PREFIX}g++")
set(CMAKE_ASM_COMPILER "${TOOLCHAIN_PREFIX}gcc")
set(CMAKE_OBJCOPY      "${TOOLCHAIN_PREFIX}objcopy")
set(CMAKE_OBJDUMP      "${TOOLCHAIN_PREFIX}objdump")
set(CMAKE_SIZE         "${TOOLCHAIN_PREFIX}size")
set(CMAKE_DEBUGGER     "${TOOLCHAIN_PREFIX}gdb")

# Prevent CMake from trying to link a test executable (cross-compile mode)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

# -- CPU flags shared across C / C++ / ASM ------------------------------------
set(CPU_FLAGS "-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")

set(CMAKE_C_FLAGS_INIT   "${CPU_FLAGS}")
set(CMAKE_CXX_FLAGS_INIT "${CPU_FLAGS}")
set(CMAKE_ASM_FLAGS_INIT "${CPU_FLAGS} -x assembler-with-cpp")
set(CMAKE_EXE_LINKER_FLAGS_INIT "${CPU_FLAGS} -specs=nano.specs -specs=nosys.specs")

# -- Search paths (only look inside the sysroot) ------------------------------
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
