#ifndef S8_H
#define S8_H

#include "i2c.h"

#define	TH_ADDRESS_S8		       0x88 
#define	ICM20_TEMP_OUT_H			     0x41
#define	ICM20_TEMP_OUT_L			     0x42

typedef struct
{
	  float temperature;
	  float humidity;
}s8_para;	



i2c_addr_def s8_init(uint8_t address);
s8_para s8_read_sht3x(uint32_t i2c_periph,uint8_t i2c_addr);
#endif /* S8_H */

