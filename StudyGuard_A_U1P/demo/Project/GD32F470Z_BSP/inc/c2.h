#ifndef C2_H
#define C2_H

#include "gd32f4xx.h"
#include "stdint.h"


#define  out
#define  TERMINAL   		0		//终端模式
#define  COORDINATOR      	1		//协调器模式

uint8_t c2_init(uint8_t zigbee_mode);
void c2_broadcast_data(char *send_data,uint8_t mode);
uint8_t c2_rec_data(uint8_t *rec_data, uint16_t len, uint16_t timeout);

#endif



