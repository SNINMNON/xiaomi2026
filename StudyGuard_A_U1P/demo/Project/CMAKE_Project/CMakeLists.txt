cmake_minimum_required(VERSION 3.20)

# =============================================================================
# 此文件由 gen_cmake.py 自动生成。
# 本 CMAKE_Project 目录是完全自包含的，无需依赖上级目录即可独立构建。
#
# 一键构建（推荐）：
#   Windows : 双击 build.bat
#   Linux   : bash build.sh
#
# 手动构建：
#   cmake -B build -DCMAKE_TOOLCHAIN_FILE=arm-none-eabi.cmake
#   cmake --build build -j8
#
# 手动烧录（需 OpenOCD）：
#   openocd -f gd32f470zk.cfg -c "program build/C2_DEMO.hex verify reset exit"
#
# 调试（GDB server，另开终端后用 GDB 连接 :3333）：
#   openocd -f gd32f470zk.cfg
# =============================================================================

project(STUDYGUARD_A_U1P C ASM)

# 导出 compile_commands.json，供 clangd 智能提示使用
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# -----------------------------------------------------------------------------
# 可执行目标
# -----------------------------------------------------------------------------
add_executable(${PROJECT_NAME}
    ${CMAKE_CURRENT_SOURCE_DIR}/../Application/src/c2_demo.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../GD32F470Z_BSP/src/uart.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../GD32F470Z_BSP/src/c2.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../GD32F470Z_BSP/src/i2c.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../GD32F470Z_BSP/src/s5.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../GD32F470Z_BSP/src/s7.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../GD32F470Z_BSP/src/s8.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../GD32F470Z_BSP/src/gd32f470z_eval.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_adc.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_can.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_crc.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_ctc.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_dac.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_dbg.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_dci.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_dma.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_enet.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_exmc.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_exti.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_fmc.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_fwdgt.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_gpio.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_i2c.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_ipa.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_iref.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_misc.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_pmu.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_rcu.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_rtc.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_sdio.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_spi.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_syscfg.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_timer.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_tli.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_trng.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_usart.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Source/gd32f4xx_wwdgt.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/CMSIS/GD/GD32F4xx/Source/system_gd32f4xx.c
    ${CMAKE_CURRENT_SOURCE_DIR}/startup_gd32f470_gcc.S
)

# -----------------------------------------------------------------------------
# 编译宏
# -----------------------------------------------------------------------------
target_compile_definitions(${PROJECT_NAME} PRIVATE
    USE_STDPERIPH_DRIVER
    GD32F450
    USE_USB_HS
    USE_USB_FS
    USE_ULPI_PHY
)

# -----------------------------------------------------------------------------
# 头文件路径
# -----------------------------------------------------------------------------
target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../../Project
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_standard_peripheral/Include
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Utilities
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/CMSIS/GD/GD32F4xx/Include
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/CMSIS
    ${CMAKE_CURRENT_SOURCE_DIR}/../Application/inc
    ${CMAKE_CURRENT_SOURCE_DIR}/../GD32F470Z_BSP/inc
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_usb_library/device/class/hid/Include
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_usb_library/device/core/Include
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_usb_library/driver/Include
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_usb_library/ustd/common
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_usb_library/ustd/class/hid
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_usb_library/host/core/Include
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../Library/Firmware/GD32F4xx_usb_library/host/class/hid/Include
)

# -----------------------------------------------------------------------------
# 编译选项
# -----------------------------------------------------------------------------
target_compile_options(${PROJECT_NAME} PRIVATE
    -ffunction-sections
    -fdata-sections
    -Wall
    -Wno-unused-function
    -O2
    $<$<COMPILE_LANGUAGE:ASM>:-x assembler-with-cpp>
)

# -----------------------------------------------------------------------------
# 链接选项（使用本地链接脚本）
# -----------------------------------------------------------------------------
target_link_options(${PROJECT_NAME} PRIVATE
    -T${CMAKE_CURRENT_SOURCE_DIR}/gd32f470zk.ld
    -Wl,--gc-sections
    -Wl,--no-warn-rwx-segments
    -Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.map,--cref
    -lc -lm -lnosys
)

# -----------------------------------------------------------------------------
# 构建后：显示大小 + 生成 .hex / .bin
# -----------------------------------------------------------------------------
add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE:${PROJECT_NAME}>
    COMMENT "Firmware size:"
)

add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O ihex   $<TARGET_FILE:${PROJECT_NAME}> ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.hex
    COMMAND ${CMAKE_OBJCOPY} -O binary -S $<TARGET_FILE:${PROJECT_NAME}> ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.bin
    COMMENT "Generated: ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.hex"
)
