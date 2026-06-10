#include "i2c.h"
#include "s1.h"

/*********************************************************************************************************
函数名:     s1_init
入口参数:   i2c初始地址 address 
出口参数:   无 
返回值:     i2c_addr_def定义结构体
作者:       zzz
日期:       2023/4/1
调用描述:   得到s1 i2c地址,若器件不存在则结构体flag值为0,若存在则初始化芯片置结构体flag值为1
**********************************************************************************************************/
i2c_addr_def s1_init(uint8_t address)
{
	i2c_addr_def e_addess;

	e_addess = get_board_address(address);

	if(e_addess.flag)
	{
		i2c_cmd_write(e_addess.periph,e_addess.addr,S1_SYSTEM_ON);
	}
	return e_addess;		 
}



/*********************************************************************************************************
函数名:     s1_all_init
入口参数:   s1_address结构体指针  s1_addr:s1 i2c起始地址 
出口参数:   s1_address结构体指针
返回值:     无
作者:       zzz
日期:       2023/4/1
调用描述:   查找并初始化所有s1子板,并得到相应的地址放在结构体指针s1_address
**********************************************************************************************************/
void s1_all_init(out s1_addr_def *s1_address,uint8_t s1_addr)
{
	uint8_t i;

	for(i=0;i<4;i++)
	{
		s1_address->key_addr[i] = get_board_address(s1_addr+i*2);
		if(s1_address->key_addr[i].flag)
		i2c_cmd_write(s1_address->key_addr[i].periph,s1_address->key_addr[i].addr,S1_SYSTEM_ON);	
	}
}



/*********************************************************************************************
函数名:      s1_key_scan
功能:        按键扫描功能,得到键值
入口参数:    i2c_periph:i2c口  i2c_addr:i2c起始地址
出口参数:    无
返回值：     返回按键扫描键值
作者：       ZZZ
日期:        2023/4/1
调用描述:    调用此函数,得到键值
**********************************************************************************************/
uint8_t s1_key_scan(uint32_t i2c_periph,uint8_t i2c_addr)
{
	uint8_t key_value;
	uint8_t keyvalue[6];

	i2c_read(i2c_periph,i2c_addr,KEYKS0,keyvalue,6);


	if(keyvalue[0]&0x01)
	{
		key_value = SW1;
	}	
	else if(keyvalue[2]&0x01)
	{	
		key_value = SW2;	 
	}
	else if(keyvalue[4]&0x01)
	{
		key_value = SW3;
	}	
	else if(keyvalue[0]&0x02)
	{
		key_value = SW4;
	}	
	else if(keyvalue[2]&0x02)
	{
		key_value = SW5; 
	}	
	else if(keyvalue[4]&0x02)
	{
		key_value = SW6; 
	}
	else if(keyvalue[0]&0x04)
	{
		key_value = SW7;
	}
	else if(keyvalue[2]&0x04)
	{
		key_value = SW8;
	}
	else if(keyvalue[4]&0x04)
	{
		key_value = SW9;
	}
	else if(keyvalue[0]&0x08)
	{
		key_value = SWA;
	}
	else if(keyvalue[2]&0x08)
	{
		key_value = SW0;
	}
	else if(keyvalue[4]&0x08)
	{
		key_value = SWC;
	}	
	else 
	{
		key_value = SWN;
	}	

	return key_value;		
}


