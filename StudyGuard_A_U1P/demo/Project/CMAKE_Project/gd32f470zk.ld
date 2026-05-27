/*
 * gd32f470zk.ld - Linker script for GD32F470ZK
 *
 * Memory Map:
 *   FLASH : 0x08000000, 3MB
 *   SRAM  : 0x20000000, 192KB  (main SRAM)
 *   TCM   : 0x10000000, 64KB   (ITCM/CCM, used for stack)
 */

/* Entry point */
ENTRY(Reset_Handler)

/* Stack placed in TCM (faster access) */
_estack = ORIGIN(TCM) + LENGTH(TCM);

/* Minimum heap/stack sizes - linker will error if not enough room */
_Min_Heap_Size  = 0x400;
_Min_Stack_Size = 0x400;

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 3072K
    SRAM  (rwx) : ORIGIN = 0x20000000, LENGTH = 192K
    TCM   (rwx) : ORIGIN = 0x10000000, LENGTH = 64K
}

SECTIONS
{
    /*----------------------------------------------------------------------
     * Vector table and code in FLASH
     *----------------------------------------------------------------------*/
    .isr_vector :
    {
        . = ALIGN(4);
        KEEP(*(.isr_vector))
        . = ALIGN(4);
    } >FLASH

    .text :
    {
        . = ALIGN(4);
        *(.text)
        *(.text*)
        *(.glue_7)
        *(.glue_7t)
        *(.eh_frame)
        KEEP(*(.init))
        KEEP(*(.fini))
        . = ALIGN(4);
        _etext = .;
    } >FLASH

    /* Read-only data */
    .rodata :
    {
        . = ALIGN(4);
        *(.rodata)
        *(.rodata*)
        . = ALIGN(4);
    } >FLASH

    /* ARM exception unwind tables */
    .ARM.extab :
    {
        *(.ARM.extab* .gnu.linkonce.armextab.*)
    } >FLASH

    .ARM :
    {
        __exidx_start = .;
        *(.ARM.exidx*)
        __exidx_end = .;
    } >FLASH

    /* C++ pre/post-init arrays */
    .preinit_array :
    {
        PROVIDE_HIDDEN(__preinit_array_start = .);
        KEEP(*(.preinit_array*))
        PROVIDE_HIDDEN(__preinit_array_end = .);
    } >FLASH

    .init_array :
    {
        PROVIDE_HIDDEN(__init_array_start = .);
        KEEP(*(SORT(.init_array.*)))
        KEEP(*(.init_array*))
        PROVIDE_HIDDEN(__init_array_end = .);
    } >FLASH

    .fini_array :
    {
        PROVIDE_HIDDEN(__fini_array_start = .);
        KEEP(*(SORT(.fini_array.*)))
        KEEP(*(.fini_array*))
        PROVIDE_HIDDEN(__fini_array_end = .);
    } >FLASH

    /*----------------------------------------------------------------------
     * Initialized data: stored in FLASH, copied to SRAM at startup
     *----------------------------------------------------------------------*/
    _sidata = LOADADDR(.data);

    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        *(.data)
        *(.data*)
        . = ALIGN(4);
        _edata = .;
    } >SRAM AT> FLASH

    /*----------------------------------------------------------------------
     * Zero-initialized data (BSS) in SRAM
     *----------------------------------------------------------------------*/
    .bss :
    {
        . = ALIGN(4);
        _sbss = .;
        __bss_start__ = _sbss;
        *(.bss)
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
        __bss_end__ = _ebss;
    } >SRAM

    /*----------------------------------------------------------------------
     * Stack and Heap in TCM
     *----------------------------------------------------------------------*/
    .stack (NOLOAD) :
    {
        . = ALIGN(8);
        __StackLimit = .;
        . = . + _Min_Stack_Size;
        . = ALIGN(8);
        __StackTop = .;
    } >TCM

    .heap (NOLOAD) :
    {
        . = ALIGN(8);
        end = .;          /* newlib _sbrk 需要此符号作为堆起点 */
        __HeapBase = .;
        . = . + _Min_Heap_Size;
        . = ALIGN(8);
        __HeapLimit = .;
    } >SRAM

    /* Discard debug/non-essential sections to keep binary clean */
    /DISCARD/ :
    {
        libc.a (*)
        libm.a (*)
        libgcc.a (*)
    }

    .ARM.attributes 0 : { *(.ARM.attributes) }
}

/* Sanity check: verify stack doesn't overflow TCM */
ASSERT(__StackTop <= ORIGIN(TCM) + LENGTH(TCM), "TCM overflow: stack too large!")
/* Sanity check: verify SRAM usage */
ASSERT(_ebss <= ORIGIN(SRAM) + LENGTH(SRAM), "SRAM overflow!")
