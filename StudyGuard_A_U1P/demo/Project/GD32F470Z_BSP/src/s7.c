#include "i2c.h"
#include "s7.h"

/*********************************************************************************************************
函数名:     pca9557_ir_init
入口参数:   i2c_periph:i2c口选择 i2c_addr:初始地址address 
出口参数:   无 
返回值:     无
作者:       zzz
日期:       2023/4/6
调用描述:   初始化pca9557芯片
**********************************************************************************************************/
void pca9557_ir_init(uint32_t i2c_periph,uint8_t i2c_addr)
{
	   i2c_delay_byte_write(i2c_periph,i2c_addr,PCA9557_POLARITY_INVERSION_REG,0x00);
	   i2c_delay_byte_write(i2c_periph,i2c_addr,PCA9557_CONFIG_REG,0xFF);
}



/*********************************************************************************************************
函数名:     s7_init
入口参数:   i2c初始地址 address 
出口参数:   无 
返回值:     i2c_addr_def定义结构体
作者:       zzz
日期:       2023/4/6
调用描述:   得到s7 i2c地址,若器件不存在则结构体flag值为0,若存在则初始化芯片置结构体flag值为1
**********************************************************************************************************/
i2c_addr_def s7_init(uint8_t address)
{
     uint8_t i;
	   i2c_addr_def e_address;

     for(i=0;i<4;i++)
     {
			    e_address = get_board_address(address + i*2);
			    if(e_address.flag)
					{
						   pca9557_ir_init(e_address.periph,e_address.addr);
						   break;
          }						
     }
		 
		 return e_address;
}



/*********************************************************************************************************
函数名:     s7_all_init
入口参数:   s7_address结构体指针  s7_addr:s7 i2c起始地址 
出口参数:   s7_address结构体指针
返回值:     无
作者:       zzz
日期:       2023/4/6
调用描述:   查找并初始化所有s7子板,并得到相应的地址放在结构体指针s7_address
**********************************************************************************************************/
void s7_all_init(s7_addr_def *s7_address,uint8_t s7_addr)
{
	   uint8_t i;
	  
	   for(i=0;i<4;i++)
     {
			    s7_address->ir_addr[i] = get_board_address(s7_addr+i*2);
			    if(s7_address->ir_addr[i].flag)
			    pca9557_ir_init(s7_address->ir_addr[i].periph,s7_address->ir_addr[i].addr);
		 }
}



/*********************************************************************************************************
函数名:     s7_get_status
入口参数:   i2c_periph:i2c口选择 i2c_addr:初始地址address 
出口参数:   无 
返回值:     有人状态返回1,无人状态返回0
作者:       zzz
日期:       2023/4/6
调用描述:   得到人体传感器的状态
**********************************************************************************************************/
uint8_t s7_get_status(uint32_t i2c_periph,uint8_t i2c_addr)
{
     uint8_t s_status;
     
	   i2c_read(i2c_periph,i2c_addr,0x00,&s_status,1);
     
	   if(s_status & 0x01)
		 {
			   return 1;
		 }	 
     else
		 {	 
         return 0;
     }			 
}









