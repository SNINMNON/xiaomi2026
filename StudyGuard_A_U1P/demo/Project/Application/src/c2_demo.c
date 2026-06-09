#include "gd32f4xx.h"
#include "gd32f470z_eval.h"
#include "c2_demo.h"
#include "c2.h"
#include "i2c.h"
#include "s5.h"
#include "s7.h"
#include "s8.h"
#include "uart.h"
#include "stdio.h"
#include "string.h"

#define STUDYGUARD_SEAT_ID       "A01"
#define HUMAN_REPORT_MS          1000U
#define ENV_REPORT_MS            3000U
#define HEARTBEAT_REPORT_MS      10000U
#define S7_ACTIVE_HIGH           1U

static uint16_t uart_print(uint32_t usart_periph, uint8_t *data, uint16_t len);
static void debug_printf(uint32_t usart_periph, char *string);
static void send_frame(const char *frame);
static void print_board_addr(const char *name, i2c_addr_def addr);
static void print_i2c_scan(void);
static void print_c2_probe(void);
static void format_fixed1(char *dst, int32_t scaled10);
static void format_card_id(char *dst, const uint8_t *uid);
static void report_human(void);
static void report_env(void);
static void report_rfid(void);
static void report_heartbeat(void);

static uint8_t print_buffer[160];
static i2c_addr_def s5_addr;
static i2c_addr_def s7_addr;
static i2c_addr_def s8_addr;
static uint8_t last_human = 0xFF;
static uint8_t card_present = 0;
static uint8_t last_card_uid[4] = {0};

int main(void)
{
	nvic_priority_group_set(NVIC_PRIGROUP_PRE4_SUB0);
	gd_eval_com_init(EVAL_COM0);
	timer3_init();
	init_i2c();
	uart_init(USART0);

	sprintf((char *)print_buffer, "[BOOT] StudyGuard A U1P start\r\n");
	debug_printf(EVAL_COM0, (char *)print_buffer);

	s7_addr = s7_init(PCA9557_ADDRESS_S7);
	s5_addr = s5_init(MS523_ADDRESS_S5);
	s8_addr = s8_init(TH_ADDRESS_S8);

	sprintf((char *)print_buffer, "[I2C] S7=%d S5=%d S8=%d\r\n",
	        s7_addr.flag, s5_addr.flag, s8_addr.flag);
	debug_printf(EVAL_COM0, (char *)print_buffer);
	print_board_addr("S7", s7_addr);
	print_board_addr("S5", s5_addr);
	print_board_addr("S8", s8_addr);
	print_i2c_scan();
	print_c2_probe();

	if(c2_init(TERMINAL)) {
		debug_printf(EVAL_COM0, "[C2] init ok, mode=TERMINAL\r\n");
	} else {
		debug_printf(EVAL_COM0, "[C2] init failed, frames still print to debug COM\r\n");
	}

	report_heartbeat();

	while(1)
	{
		static uint32_t elapsed_ms = 0;

		delay_ms(HUMAN_REPORT_MS);
		elapsed_ms += HUMAN_REPORT_MS;

		report_human();
		report_rfid();

		if((elapsed_ms % ENV_REPORT_MS) == 0U) {
			report_env();
		}

		if((elapsed_ms % HEARTBEAT_REPORT_MS) == 0U) {
			report_heartbeat();
		}
	}
}

static void send_frame(const char *frame)
{
	c2_broadcast_data((char *)frame, 0x01);
	sprintf((char *)print_buffer, "[TX] %s\r\n", frame);
	debug_printf(EVAL_COM0, (char *)print_buffer);
}

static void print_board_addr(const char *name, i2c_addr_def addr)
{
	const char *bus = "-";

	if(addr.flag) {
		if(addr.periph == I2C0) {
			bus = "I2C0";
		} else if(addr.periph == I2C1) {
			bus = "I2C1";
		}
		sprintf((char *)print_buffer, "[I2C] %s found bus=%s addr=0x%02X\r\n",
		        name, bus, addr.addr);
	} else {
		sprintf((char *)print_buffer, "[I2C] %s not found\r\n", name);
	}
	debug_printf(EVAL_COM0, (char *)print_buffer);
}

static void print_i2c_scan(void)
{
	uint8_t addr;
	uint8_t found = 0;

	debug_printf(EVAL_COM0, "[I2C_SCAN] begin\r\n");
	for(addr = 0x20; addr <= 0x96; addr += 2) {
		if(i2c_addr_poll(I2C0, addr)) {
			sprintf((char *)print_buffer, "[I2C_SCAN] I2C0 addr=0x%02X\r\n", addr);
			debug_printf(EVAL_COM0, (char *)print_buffer);
			found = 1;
		}
		if(i2c_addr_poll(I2C1, addr)) {
			sprintf((char *)print_buffer, "[I2C_SCAN] I2C1 addr=0x%02X\r\n", addr);
			debug_printf(EVAL_COM0, (char *)print_buffer);
			found = 1;
		}
	}
	if(!found) {
		debug_printf(EVAL_COM0, "[I2C_SCAN] none\r\n");
	}
	debug_printf(EVAL_COM0, "[I2C_SCAN] end\r\n");
}

static void print_c2_probe(void)
{
	uint8_t i;
	uint8_t len;
	uint8_t recvdata[50];
	uint8_t read_device_data[4] = {0xFE, 0x01, 0xFE, 0xFF};

	memset(recvdata, 0, sizeof(recvdata));
	uart_send_bytes(USART0, read_device_data, sizeof(read_device_data));
	len = uart_rece_bytes(USART0, recvdata, sizeof(recvdata), 1000);

	sprintf((char *)print_buffer, "[C2_PROBE] len=%d data=", len);
	debug_printf(EVAL_COM0, (char *)print_buffer);
	for(i = 0; i < len; i++) {
		sprintf((char *)print_buffer, "%02X", recvdata[i]);
		debug_printf(EVAL_COM0, (char *)print_buffer);
	}
	debug_printf(EVAL_COM0, "\r\n");
}

static void format_fixed1(char *dst, int32_t scaled10)
{
	if(scaled10 < 0) {
		scaled10 = -scaled10;
		sprintf(dst, "-%ld.%ld", (long)(scaled10 / 10), (long)(scaled10 % 10));
	} else {
		sprintf(dst, "%ld.%ld", (long)(scaled10 / 10), (long)(scaled10 % 10));
	}
}

static void format_card_id(char *dst, const uint8_t *uid)
{
	sprintf(dst, "%02X%02X%02X%02X", uid[0], uid[1], uid[2], uid[3]);
}

static void report_human(void)
{
	uint8_t human = 0;
	uint8_t raw = 0;
	char frame[64];

	if(!s7_addr.flag) {
		debug_printf(EVAL_COM0, "[S7] not found\r\n");
		return;
	}

	if(i2c_read(s7_addr.periph, s7_addr.addr, PCA9557_INPUT_PORT_REG, &raw, 1)) {
#if S7_ACTIVE_HIGH
		human = (raw & 0x01U) ? 1U : 0U;
#else
		human = (raw & 0x01U) ? 0U : 1U;
#endif
	} else {
		debug_printf(EVAL_COM0, "[S7] read failed\r\n");
		return;
	}

	if(human != last_human) {
		last_human = human;
		sprintf(frame, "HUMAN,seat=%s,value=%d", STUDYGUARD_SEAT_ID, human);
		send_frame(frame);
	} else {
		sprintf((char *)print_buffer, "[S7] raw=0x%02X d0=%d human=%d\r\n",
		        raw, raw & 0x01U, human);
		debug_printf(EVAL_COM0, (char *)print_buffer);
	}
}

static void report_env(void)
{
	s8_para value;
	char temp_text[16];
	char hum_text[16];
	char frame[80];

	value.temperature = 0.0f;
	value.humidity = 0.0f;

	if(!s8_addr.flag) {
		debug_printf(EVAL_COM0, "[S8] not found\r\n");
		return;
	}

	value = s8_read_sht3x(s8_addr.periph, s8_addr.addr);
	format_fixed1(temp_text, (int32_t)(value.temperature * 10.0f));
	format_fixed1(hum_text, (int32_t)(value.humidity * 10.0f));

	sprintf(frame, "ENV,temp=%s,humi=%s", temp_text, hum_text);
	send_frame(frame);
}

static void report_rfid(void)
{
	uint8_t uid[6] = {0};
	char card_text[16];
	char frame[80];

	if(!s5_addr.flag) {
		return;
	}

	if(s5_detect(s5_addr.periph, s5_addr.addr, uid)) {
		if(!card_present || memcmp(last_card_uid, uid, 4) != 0) {
			memcpy(last_card_uid, uid, 4);
			card_present = 1;
			format_card_id(card_text, uid);
			sprintf(frame, "RFID,seat=%s,card=%s,event=scan", STUDYGUARD_SEAT_ID, card_text);
			send_frame(frame);
		}
	} else {
		card_present = 0;
	}

	s5_sleep(s5_addr.periph, s5_addr.addr);
}

static void report_heartbeat(void)
{
	send_frame("HB,u1p=ok");
}

static uint16_t uart_print(uint32_t usart_periph, uint8_t *data, uint16_t len)
{
	uint16_t i;
	for(i = 0; i < len; i++)
	{
		while(usart_flag_get(usart_periph, USART_FLAG_TC) == RESET);
		usart_data_transmit(usart_periph, data[i]);
	}
	while(usart_flag_get(usart_periph, USART_FLAG_TC) == RESET);
	return len;
}

static void debug_printf(uint32_t usart_periph, char *string)
{
	uart_print(usart_periph, (uint8_t *)string, strlen(string));
}
