#include "gd32f4xx.h"
#include "gd32f470z_eval.h"
#include "c2_demo.h"
#include "c2.h"
#include "i2c.h"
#include "s5.h"
#include "s7.h"
#include "s8.h"
#include "s1.h"
#include "uart.h"
#include "stdio.h"
#include "string.h"

#define HUMAN_REPORT_MS          1000U
#define ENV_REPORT_MS            3000U
#define HEARTBEAT_REPORT_MS      30000U
#define S7_ACTIVE_HIGH           1U
#define DEFAULT_ACTIVE_SEAT      "A01"
#define C2_FRAME_GAP_MS          120U

static uint16_t uart_print(uint32_t usart_periph, uint8_t *data, uint16_t len);
static void debug_printf(uint32_t usart_periph, char *string);
static void send_frame(const char *frame);
static i2c_addr_def make_missing_addr(void);
static i2c_addr_def find_board_addr(uint8_t base_addr);
static uint8_t same_board_addr(i2c_addr_def a, i2c_addr_def b);
static void refresh_sensor_links(void);
static void log_sensor_link(const char *name, i2c_addr_def addr);
static void print_board_addr(const char *name, i2c_addr_def addr);
static void print_i2c_scan(void);
static void print_c2_probe(void);
static void format_fixed1(char *dst, int32_t scaled10);
static void format_card_id(char *dst, const uint8_t *uid);
static void report_human(void);
static void report_env(void);
static void report_rfid(void);
static void report_heartbeat(void);
static void report_seat_key(void);
static const char *seat_id_from_key(uint8_t key);

static uint8_t print_buffer[160];
static i2c_addr_def s1_addr;
static i2c_addr_def s5_addr;
static i2c_addr_def s7_addr;
static i2c_addr_def s8_addr;
static uint8_t last_s1_link = 0xFF;
static uint8_t last_s7_link = 0xFF;
static uint8_t last_s5_link = 0xFF;
static uint8_t last_s8_link = 0xFF;
static uint8_t last_human = 0xFF;
static uint8_t last_key = SWN;
static char active_seat_id[4] = DEFAULT_ACTIVE_SEAT;
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

	s1_addr = s1_init(HT16K33_ADDRESS_S1);
	s7_addr = s7_init(PCA9557_ADDRESS_S7);
	s5_addr = s5_init(MS523_ADDRESS_S5);
	s8_addr = s8_init(TH_ADDRESS_S8);

	sprintf((char *)print_buffer, "[I2C] S1=%d S7=%d S5=%d S8=%d\r\n",
	        s1_addr.flag, s7_addr.flag, s5_addr.flag, s8_addr.flag);
	debug_printf(EVAL_COM0, (char *)print_buffer);
	print_board_addr("S1", s1_addr);
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

		refresh_sensor_links();
		report_seat_key();
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
	delay_ms(C2_FRAME_GAP_MS);
	sprintf((char *)print_buffer, "[TX] %s\r\n", frame);
	debug_printf(EVAL_COM0, (char *)print_buffer);
}

static i2c_addr_def make_missing_addr(void)
{
	i2c_addr_def addr;

	addr.flag = 0;
	addr.periph = 0;
	addr.addr = 0;
	return addr;
}

static i2c_addr_def find_board_addr(uint8_t base_addr)
{
	uint8_t i;
	i2c_addr_def addr;

	for(i = 0; i < 4; i++) {
		addr = get_board_address(base_addr + i * 2);
		if(addr.flag) {
			return addr;
		}
	}

	return make_missing_addr();
}

static uint8_t same_board_addr(i2c_addr_def a, i2c_addr_def b)
{
	return (a.flag == b.flag) && (a.periph == b.periph) && (a.addr == b.addr);
}

static void log_sensor_link(const char *name, i2c_addr_def addr)
{
	if(addr.flag) {
		print_board_addr(name, addr);
	} else {
		sprintf((char *)print_buffer, "[SCHK] %s disconnected\r\n", name);
		debug_printf(EVAL_COM0, (char *)print_buffer);
	}
}

static void refresh_sensor_links(void)
{
	i2c_addr_def found;

	found = find_board_addr(HT16K33_ADDRESS_S1);
	if(found.flag && !same_board_addr(found, s1_addr)) {
		s1_addr = s1_init(HT16K33_ADDRESS_S1);
		if(!s1_addr.flag) {
			s1_addr = found;
		}
	}
	if(!found.flag) {
		s1_addr = make_missing_addr();
		last_key = SWN;
	}
	if(last_s1_link != s1_addr.flag) {
		last_s1_link = s1_addr.flag;
		log_sensor_link("S1", s1_addr);
	}

	found = find_board_addr(PCA9557_ADDRESS_S7);
	if(found.flag && !same_board_addr(found, s7_addr)) {
		s7_addr = s7_init(PCA9557_ADDRESS_S7);
		if(!s7_addr.flag) {
			s7_addr = found;
		}
	}
	if(!found.flag) {
		s7_addr = make_missing_addr();
		last_human = 0xFF;
	}
	if(last_s7_link != s7_addr.flag) {
		last_s7_link = s7_addr.flag;
		log_sensor_link("S7", s7_addr);
	}

	found = find_board_addr(MS523_ADDRESS_S5);
	if(found.flag && !same_board_addr(found, s5_addr)) {
		s5_addr = s5_init(MS523_ADDRESS_S5);
		if(!s5_addr.flag) {
			s5_addr = found;
		}
	}
	if(!found.flag) {
		s5_addr = make_missing_addr();
		card_present = 0;
		memset(last_card_uid, 0, sizeof(last_card_uid));
	}
	if(last_s5_link != s5_addr.flag) {
		last_s5_link = s5_addr.flag;
		log_sensor_link("S5", s5_addr);
	}

	found = find_board_addr(TH_ADDRESS_S8);
	if(found.flag && !same_board_addr(found, s8_addr)) {
		s8_addr = s8_init(TH_ADDRESS_S8);
		if(!s8_addr.flag) {
			s8_addr = found;
		}
	}
	if(!found.flag) {
		s8_addr = make_missing_addr();
	}
	if(last_s8_link != s8_addr.flag) {
		last_s8_link = s8_addr.flag;
		log_sensor_link("S8", s8_addr);
	}
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
		sprintf(frame, "HUMAN,seat=%s,value=%d", active_seat_id, human);
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
			sprintf(frame, "RFID,seat=%s,card=%s,event=scan", active_seat_id, card_text);
			send_frame(frame);
		}
	} else {
		card_present = 0;
	}

	s5_sleep(s5_addr.periph, s5_addr.addr);
}

static void report_heartbeat(void)
{
	char frame[64];

	sprintf(frame, "HB,u1p=ok,seat=%s,s1=%d,s7=%d,s5=%d,s8=%d",
	        active_seat_id, s1_addr.flag, s7_addr.flag, s5_addr.flag, s8_addr.flag);
	send_frame(frame);
}

static const char *seat_id_from_key(uint8_t key)
{
	switch(key) {
	case SW1:
		return "A01";
	case SW2:
		return "A02";
	case SW3:
		return "A03";
	case SW4:
		return "A04";
	default:
		return 0;
	}
}

static void report_seat_key(void)
{
	uint8_t key;
	const char *seat_id;
	char frame[64];

	if(!s1_addr.flag) {
		return;
	}

	key = s1_key_scan(s1_addr.periph, s1_addr.addr);
	if(key == last_key) {
		return;
	}
	last_key = key;

	seat_id = seat_id_from_key(key);
	if(seat_id == 0) {
		return;
	}

	strcpy(active_seat_id, seat_id);
	last_human = 0xFF;
	sprintf(frame, "SEAT,seat=%s,key=%d", active_seat_id, key);
	send_frame(frame);
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
