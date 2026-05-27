#ifndef S7_H
#define S7_H

#include "i2c.h"

typedef struct
{
   i2c_addr_def ir_addr[4];
}s7_addr_def;

#define PCA9557_ADDRESS_S7              0x30	//0x30,0x32,0x34,0x36


#define PCA9557_INPUT_PORT_REG          0x00	//输入寄存器
#define PCA9557_OUTPUT_PORT_REG         0x01	//输出寄存器
#define PCA9557_POLARITY_INVERSION_REG  0x02	//极性反转寄存器
#define PCA9557_CONFIG_REG              0x03	//配置寄存器

#define POLARITY_INVERSION_DEFAULT      0xF0	//极性反转默认
#define CONFIG_DEFAULT                  0xFF	//配置


i2c_addr_def s7_init(uint8_t address);
void s7_all_init(s7_addr_def *s7_address,uint8_t s7_addr);
uint8_t s7_get_status(uint32_t i2c_periph,uint8_t i2c_addr);

#endif


