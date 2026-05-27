#include "string.h"
#include "stdio.h"
#include "uart.h"
#include "c2.h"


/*********************************************************************************************
函数名:    c2_init
功能:      初始化zigbee模块
入口参数:  zigbeemode:zigbee工作模式
出口参数： 无
返回值：   成功返回1,失败返回0
作者：     ZZZ
日期:      2023/4/8
调用描述:  初始化zigbee模块工作模式,协调器或者终端
**********************************************************************************************/
uint8_t c2_init(uint8_t zigbee_mode)
{
	uint8_t result = 0;
	uint8_t recvdata[50];
	uint8_t i;

	uint8_t read_device_data[4] = {0xFE,0x01,0xFE,0xFF};	      //读取设备所有数据
	uint8_t terminal[5] = {0xFD,0x02,0x01,0x02,0xFF};	          //配置设备类型，配置为 02 终端
	uint8_t coordinator[5] = {0xFD,0x02,0x01,0x00,0xFF};          //配置为协调器 
	uint8_t pan_id[6] = {0xFD,0x03,0x03,0x3F,0x2C,0xFF};          //配置PAN_ID 0x3f2c
	uint8_t group_id[5] = {0xFD,0x02,0x09,0x01,0xFF};             //配置网络组

	for(i=0;i<3;i++)
	{
		memset(recvdata,0,50);
		uart_send_bytes(USART0,read_device_data,4);	
		uart_rece_bytes(USART0, recvdata, 10, 1000);	
		if(recvdata[0] == 0xfb)
		{ 
			result = 1;
			break;	
		}	
	}

	if(result)
	{
		result = 0;

		for(i=0;i<3;i++)
		{
			memset(recvdata,0,50);
			if(zigbee_mode == COORDINATOR)
				uart_send_bytes(USART0,coordinator,5);	
			else 
				uart_send_bytes(USART0,terminal,5);	

			uart_rece_bytes(USART0, recvdata, 10, 1000);
			
			if( (recvdata[0] == 0xFA) && (recvdata[1] == 0x01) )
			{
				result = 1;
				break;
			}  
		}
	}	


	if(result)
	{
		result = 0;
		for(i=0;i<3;i++)
		{
			memset(recvdata,0,50);
			uart_send_bytes(USART0,pan_id,6);
			uart_rece_bytes(USART0, recvdata, 10, 1000);
			if( (recvdata[0] == 0xFA) && (recvdata[1] == 0x03) )
			{
				result = 1;
				break;															
			}	
		}
	}

	if(result)
	{
		result = 0;
		for(i=0;i<3;i++)
		{
			memset(recvdata,0,50);
			uart_send_bytes(USART0,group_id,5);
			uart_rece_bytes(USART0, recvdata, 10, 1000);
			if( (recvdata[0] == 0xFA) && (recvdata[1] == 0x09) )
			{
				result = 1;
				break;															
			}	
		}
	}

	return result;
}


/*********************************************************************************************
函数名:    c2_broadcast_data
功能:      c2发送广播数据
入口参数:  *send_data:待发送数据指针 mode:广播模式
           01：广播模式 1 ——该消息广播到全网络中所有设备
           02：广播模式 2 ——该消息广播到只对打开了接收（除休眠模式）的设备
           03：广播模式 3 ——该消息广播到所有全功能设备（路由器和协调器）
出口参数： 无
返回值：   无
作者：     ZZZ
日期:      2023/4/8
调用描述:  发送广播数据
**********************************************************************************************/
void c2_broadcast_data(char *send_data, uint8_t mode)
{
	char sendbuf[100]; 
	uint8_t len;

	sendbuf[0] = 0xFC;
	len = strlen(send_data);
	sendbuf[1] = len + 2;
	sendbuf[2] = 0x01; 
	sendbuf[3] = mode; 
	memcpy(&sendbuf[4],(const char*)send_data,len);
	uart_send_bytes(USART0,(uint8_t *)sendbuf,len+4);
}



/*********************************************************************************************
函数名:    c2_rec_data
功能:      接收zigbee发送数据
入口参数:  *rec_data:接收数据指针  len:接收数据长度  timeout:等待时间
出口参数： *rec_data
返回值：   实际接收长度
作者：     ZZZ
日期:      2023/4/8
调用描述:  接收zigbee发送数据
**********************************************************************************************/
uint8_t c2_rec_data(out uint8_t *rec_data, uint16_t len, uint16_t timeout)
{
	uint8_t recvlen;

	recvlen = uart_rece_bytes(USART0, rec_data, len, timeout);	  

	return recvlen;	
}


