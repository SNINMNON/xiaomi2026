#include "i2c.h"
#include "s8.h"

/*********************************************************************************************
函数名:      delay_s8_ms
功能:        s2子板延时函数
入口参数:    count
出口参数:    无
返回值：     无
作者：       ZZZ
日期:        2023/4/1
**********************************************************************************************/
void delay_s8_ms(uint16_t count)
{
	uint16_t i;
	uint32_t decount;
	for(i=0;i<count;i++)
	{
		for(decount=0;decount<50000;decount++)
		{
		}	
	}	 
}

/*********************************************************************************************
函数名:      s8_sht3x_softreset
功能:        软件复位sht3x
入口参数:    i2c_periph:i2c口   i2c_addr:i2c地址
出口参数:    无
返回值：     无
作者：       ZZZ
日期:        2023/4/1
**********************************************************************************************/
void s8_sht3x_softreset(uint32_t i2c_periph,uint8_t i2c_addr)
{
     i2c_delay_byte_write(i2c_periph,i2c_addr,0x30,0xA2);
}


/*********************************************************************************************************
函数名:     s8_init
入口参数:   i2c初始地址 address 
出口参数:   无 
返回值:     i2c_addr_def定义结构体
作者:       zzz
日期:       2023/4/6
调用描述:   得到s7 i2c地址,若器件不存在则结构体flag值为0,若存在则初始化芯片置结构体flag值为1
**********************************************************************************************************/
i2c_addr_def s8_init(uint8_t address)
{
     uint8_t i;
	   i2c_addr_def e_address;

     for(i=0;i<4;i++)
     {
			    e_address = get_board_address(address + i*2);
			    if(e_address.flag)
					{
						   s8_sht3x_softreset(e_address.periph,e_address.addr);
						   break;
          }						
     }
		 
		 return e_address;
		
}


/*********************************************************************************************************
函数名:     s8_sht3x_crc_cal
入口参数:   DAT
出口参数:   无 
返回值:     函数执行结果
作者:       zzz
日期:       2023/4/6
调用描述:  计算CRC_BYTE
**********************************************************************************************************/
uint8_t s8_sht3x_crc_cal(uint16_t DAT)
{
		uint8_t i,t,temp;
		uint8_t CRC_BYTE;

		CRC_BYTE = 0xFF;
		temp = (DAT>>8) & 0xFF;

		for(t = 0; t < 2; t++)
		{
				CRC_BYTE ^= temp;
				for(i = 0;i < 8;i ++)
				{
						if(CRC_BYTE & 0x80)
						{
							  CRC_BYTE <<= 1;
							  CRC_BYTE ^= 0x31;
						}
						else
						{
							  CRC_BYTE <<= 1;
						}
				}

				if(t == 0)
				{
					  temp = DAT & 0xFF;
				}
		}

	  return CRC_BYTE;
}
/*********************************************************************************************************
函数名:     s8_read_sht3x
入口参数:   i2c_addr	硬件设备地址 
出口参数:   无
返回值:     s8_para 温湿度数据
作者:       zzz
日期:       2023/4/6
调用描述:   获取sht3x数据
**********************************************************************************************************/
s8_para s8_read_sht3x(uint32_t i2c_periph,uint8_t i2c_addr)
{
		uint8_t  th_value[6];
		s8_para  sht_para;
		uint16_t tmp;

		sht_para.temperature = 0.0f;
		sht_para.humidity = 0.0f;
	
		i2c_delay_byte_write(i2c_periph,i2c_addr,0x2C,0x0D);
		delay_s8_ms(100);
    i2c_delay_read(i2c_periph,i2c_addr,0x00,th_value,6);

		tmp = (th_value[0]<<8) + th_value[1];
		if(s8_sht3x_crc_cal(tmp) == th_value[2])
		{
			sht_para.temperature=5.5;
			sht_para.temperature = (float)tmp*175/(65536-1)-45;
		
		}
		 
		tmp = (th_value[3]<<8) + th_value[4];
		if(s8_sht3x_crc_cal(tmp) == th_value[5])
		{
			sht_para.humidity = (float)tmp*100/(65536-1);

		}
		 
	return sht_para;
}














