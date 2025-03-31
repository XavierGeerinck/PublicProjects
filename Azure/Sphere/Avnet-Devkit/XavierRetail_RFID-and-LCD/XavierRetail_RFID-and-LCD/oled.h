#pragma once

#ifndef OLED_H
#define OLED_H

#include <stdio.h>
#include <stdint.h>
#include "sd1306.h"
#include "applibs_versions.h"


#define OLED_NUM_SCREEN 7

#define OLED_TITLE_X      0
#define OLED_TITLE_Y      0 
#define OLED_RECT_TITLE_X 0
#define OLED_RECT_TITLE_Y 0
#define OLED_RECT_TITLE_W 127
#define OLED_RECT_TITLE_H 18

#define OLED_LINE_1_X     0
#define OLED_LINE_1_Y     16

#define OLED_LINE_2_X     0
#define OLED_LINE_2_Y     26

#define OLED_LINE_3_X     0
#define OLED_LINE_3_Y     36


#define OLED_LINE_4_X     0
#define OLED_LINE_4_Y     46


#define OLED_LINE_5_X     0
#define OLED_LINE_5_Y     56

#define FONT_SIZE_TITLE   2
#define FONT_SIZE_LINE    1

#define SSID_MAX_LEGTH    15


const unsigned char Image_avnet_bmp[1024];

extern uint8_t oled_state;

extern uint8_t oled_init(void);

extern void oled_i2c_bus_status(uint8_t lsmod_status);

extern void update_oled(void);

extern void oled_draw_logo(void);

/**
  * @brief  Converts a given integer x to string uint8_t[]
  * @param  n: float number to convert
  * @param  res:
  * @param  afterpoint:
  * @retval None.
  */
extern void ftoa(float n, uint8_t* res, int32_t afterpoint);

/**
  * @brief  Converts a given integer x to string uint8_t[]
  * @param  x: x integer input
  * @param  str: uint8_t array output
  * @param  d: Number of zeros added
  * @retval i: number of digits
  */
extern int32_t intToStr(int32_t x, uint8_t str[], int32_t d);

uint8_t get_str_size(uint8_t* str);

#endif