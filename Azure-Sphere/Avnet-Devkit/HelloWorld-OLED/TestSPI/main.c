#include <errno.h>
#include <signal.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

// applibs_versions.h defines the API struct versions to use for applibs APIs.
#include "applibs_versions.h"

#include <applibs/log.h>
#include <applibs/i2c.h>

#include "oled.h"

int main(int argc, char* argv[])
{
	// Start the OLED Screen
	if (oled_init())
	{
		Log_Debug("OLED not found!\n");
	}
	else
	{
		Log_Debug("OLED found!\n");
	}

	// Clear the buffer
	oled_buffer_clear();

	// Draw the strings
	sd1306_draw_string(0, 0, "Test", FONT_SIZE_TITLE, white_pixel);
	sd1306_draw_string(OLED_LINE_1_X, OLED_LINE_1_Y, "Hello World", FONT_SIZE_LINE, white_pixel);
	sd1306_draw_string(OLED_LINE_2_X, OLED_LINE_2_Y, "Hello World", FONT_SIZE_LINE, white_pixel);
	sd1306_draw_string(OLED_LINE_3_X, OLED_LINE_3_Y, "Hello World", FONT_SIZE_LINE, white_pixel);
	sd1306_draw_string(OLED_LINE_4_X, OLED_LINE_4_Y, "Hello World", FONT_SIZE_LINE, white_pixel);

	// Send the buffer to OLED RAM
	sd1306_refresh();

	return 0;
}