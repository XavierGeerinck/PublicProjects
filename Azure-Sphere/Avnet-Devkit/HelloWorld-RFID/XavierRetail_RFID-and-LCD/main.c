#include <stdbool.h>
#include <errno.h>
#include <string.h>
#include <time.h>
#include <signal.h> // sig_atomic_t
#include <unistd.h> // for Sleep

// applibs_versions.h defines the API struct versions to use for applibs APIs.
#include "applibs_versions.h"

#include <applibs/log.h>

#include "mfrc522.h"

void delay(int s)
{
	sleep(s);
}

int main(void)
{
	Log_Debug("IPC RFID RC522 Application Starting\n");

	// Start the RFID Scanner
	if (mfrc522_init())
	{
		Log_Debug("RFID Scanner not found!\n");
	}
	else
	{
		Log_Debug("RFID Scanner found!\n");
		return -1;
	}

	// Look for a card
	while (1)
	{
		Log_Debug("Trying to get version\n");
		// Check version of the reader
		// Can be 0x91 for 1.0 or 0x92 for 2.0 -> https://www.nxp.com/docs/en/data-sheet/MFRC522.pdf (p66 - VersionReg register)
		uint8_t byte = mfrc522_read(VersionReg);

		Log_Debug("Detected version %d (Hex: %x)\n", byte, byte);

		delay(5);
	}

	return 0;
}