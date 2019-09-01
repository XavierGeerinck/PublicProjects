/*
 * mfrc522.c
 *
 * Copyright 2013 Shimon <shimon@monistit.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301, USA.
 *
 *
 */


// #include "applibs_versions.h"
#include <errno.h>
#include <string.h>
#include <stdbool.h>

#include "applibs_versions.h" // without this we can not use functions such as SPIMaster, ...
#include "avnet_mt3620_sk.h"

#include <applibs/spi.h>
#include <applibs/log.h>

#include "mfrc522.h"

#include <unistd.h>

//#if 1
//#include <lcd.h>
//#endif

static int spiFd = -1;

/// <summary>
///    Checks the number of transferred bytes for SPI functions and prints an error
///    message if the functions failed or if the number of bytes is different than
///    expected number of bytes to be transferred.
/// </summary>
/// <returns>true on success, or false on failure</returns>
static bool CheckTransferSize(const char* desc, size_t expectedBytes, ssize_t actualBytes)
{
	if (actualBytes < 0) {
		Log_Debug("ERROR: %s: errno=%d (%s)\n", desc, errno, strerror(errno));
		return false;
	}

	if (actualBytes != (ssize_t)expectedBytes) {
		Log_Debug("ERROR: %s: transferred %zd bytes; expected %zd\n", desc, actualBytes,
			expectedBytes);
		return false;
	}

	return true;
}

uint8_t mfrc522_init(void)
{
	// Initialize the SPIMaster Config struct
	// https://docs.microsoft.com/en-us/azure-sphere/reference/applibs-reference/applibs-spi/function-spimaster-initconfig
	// https://docs.microsoft.com/en-us/azure-sphere/reference/applibs-reference/applibs-spi/function-spimaster-open
	// Note: MT3620_SPI_CS_A = Clickbus 1 (A = 1, B = 2)
	// Note: SPIMaster_TransferSequential  will enable the chip select before sequence and disable when it ends
	// Follow config as in the datasheet and a raspberry pi implementation for the CPHA and CPOL
	//	https://www.nxp.com/docs/en/data-sheet/MFRC522.pdf
	//	https://github.com/paguz/RPi-RFID/blob/master/MFRC522.cpp
	Log_Debug("[MFRC522][SPI][INFO] Initializing\n");

	SPIMaster_Config config;
	int ret = SPIMaster_InitConfig(&config);
	if (ret != 0) {
		Log_Debug("[MFRC522][SPI][ERROR] SPIMaster_InitConfig = %d errno = %s (%d)\n", ret, strerror(errno), errno);
		return;
	}

	config.csPolarity = SPI_ChipSelectPolarity_ActiveLow;

	spiFd = SPIMaster_Open(AVNET_MT3620_SK_ISU1_SPI, MT3620_SPI_CS_A, &config);
	Log_Debug("[MFRC522][SPI][INFO] Opened SPI Interface\n");
	if (spiFd < 0) {
		Log_Debug("[MFRC522][SPI][ERROR] SPIMaster_Open: errno=%d (%s)\n", errno, strerror(errno));
		return;
	}

	int busSpeed = 4 * 1000 * 1000; // in Hz
	int result = SPIMaster_SetBusSpeed(spiFd, busSpeed);
	Log_Debug("[MFRC522][SPI][INFO] BusSpeed = %d\n", busSpeed);
	if (result != 0) {
		Log_Debug("[MFRC522][SPI][ERROR] SPIMaster_SetBusSpeed: errno=%d (%s)\n", errno, strerror(errno));
		return -1;
	}

	result = SPIMaster_SetMode(spiFd, SPI_Mode_0);
	Log_Debug("[MFRC522][SPI][INFO] SPIMode = %x\n", SPI_Mode_0);
	if (result != 0) {
		Log_Debug("[MFRC522][SPI][ERROR] SPIMaster_SetMode: errno=%d (%s)\n", errno, strerror(errno));
		return -1;
	}

	result = SPIMaster_SetBitOrder(spiFd, SPI_BitOrder_MsbFirst);
	Log_Debug("[MFRC522][SPI][INFO] BitOrder = SPI_BitOrder_MsbFirst\n");
	if (result != 0) {
		Log_Debug("[MFRC522][SPI][ERROR] SPIMaster_SetBitOrder: errno=%d (%s)\n", errno, strerror(errno));
		return -1;
	}

	// TODO: https://docs.microsoft.com/en-us/azure-sphere/reference/applibs-reference/applibs-spi/function-spimaster-setbitorder -> set MSB first!

	Log_Debug("[MFRC522][SPI][INFO] FD Set on %d\n", spiFd);

	sleep(2);

	// Init the RFID Reader
	uint8_t byte;
	mfrc522_reset();

	mfrc522_write(TModeReg, 0x8D);
	mfrc522_write(TPrescalerReg, 0x3E);
	mfrc522_write(TReloadReg_1, 30);
	mfrc522_write(TReloadReg_2, 0);
	mfrc522_write(TxASKReg, 0x40);
	mfrc522_write(ModeReg, 0x3D);

	Log_Debug("[MFRC522][SPI][INFO] Initialized\n");

	byte = mfrc522_read(TxControlReg);
	if (!(byte & 0x03))
	{
		mfrc522_write(TxControlReg, byte | 0x03);
	}

	// Success
	return 0;
}

void mfrc522_write(uint8_t reg, uint8_t data)
{
	const size_t transferCount = 1;
	SPIMaster_Transfer transfer;

	int result = SPIMaster_InitTransfers(&transfer, transferCount);
	if (result != 0) {
		return;
	}

	//const uint8_t command[] = { (reg << 1) & 0x7E, data };
	const uint8_t command[] = { (reg << 1) & 0x7E, data };
	transfer.flags = SPI_TransferFlags_Write;
	transfer.writeData = command;
	transfer.length = sizeof(command);

	ssize_t transferredBytes = SPIMaster_TransferSequential(spiFd, &transfer, transferCount);

	if (!CheckTransferSize("SPIMaster_TransferSequential (CTRL3_C)", transfer.length, transferredBytes)) {
		Log_Debug("Transfer size is not correct");
		return;
	}
}

uint8_t mfrc522_read(uint8_t reg)
{
	uint8_t readDataResult;
	//uint8_t readCmd = ((reg << 1) & 0x7E) | 0x80; // Set bit 7 indicating it's a read command -> 0x80
	uint8_t readCmd = ((reg << 1) & 0x7E | 0x80); // Set bit 7 indicating it's a read command -> 0x80
	ssize_t transferredBytes = SPIMaster_WriteThenRead(spiFd, &readCmd, sizeof(readCmd), &readDataResult, sizeof(readDataResult));

	if (!CheckTransferSize("SPIMaster_WriteThenRead (CTRL3_C)", sizeof(readCmd) + sizeof(readDataResult), transferredBytes)) {
		Log_Debug("Transfer size is not correct");
		return -1;
	}

	return readDataResult;
}


//uint8_t mfrc522_read(uint8_t reg)
//{
//	uint8_t readDataResult;
//	//uint8_t readCmd = ((reg << 1) & 0x7E) | 0x80; // Set bit 7 indicating it's a read command -> 0x80
//	uint8_t readCmd = (reg | 0x80); // Set bit 7 indicating it's a read command -> 0x80
//
//	static const size_t transferCount = 2;
//	SPIMaster_Transfer transfers[transferCount];
//
//	int result = SPIMaster_InitTransfers(transfers, transferCount);
//	if (result != 0) {
//		return -1;
//	}
//
//	transfers[0].flags = SPI_TransferFlags_Write;
//	transfers[0].writeData = &readCmd;
//	transfers[0].length = sizeof(readCmd);
//
//	transfers[1].flags = SPI_TransferFlags_Read;
//	transfers[1].readData = &readDataResult;
//	transfers[1].length = sizeof(readDataResult);
//
//	ssize_t transferredBytes = SPIMaster_TransferSequential(spiFd, transfers, transferCount);
//	if (!CheckTransferSize("SPIMaster_TransferSequential (CTRL3_C)", sizeof(readDataResult) + sizeof(readCmd), transferredBytes)) {
//		return -1;
//	}
//
//	return readDataResult;
//}

// BKP
//void mfrc522_write(uint8_t reg, uint8_t data)
//{
//	ENABLE_CHIP();
//	spi_transmit((reg << 1) & 0x7E);
//	spi_transmit(data);
//	DISABLE_CHIP();
//}
//
//uint8_t mfrc522_read(uint8_t reg)
//{
//	uint8_t data;
//	ENABLE_CHIP();
//	spi_transmit(((reg << 1) & 0x7E) | 0x80);
//	data = spi_transmit(0x00);
//	DISABLE_CHIP();
//	return data;
//}

void mfrc522_reset()
{
	mfrc522_write(CommandReg, SoftReset_CMD);
}

uint8_t	mfrc522_request(uint8_t req_mode, uint8_t* tag_type)
{
	uint8_t  status;
	uint32_t backBits;//The received data bits

	mfrc522_write(BitFramingReg, 0x07);//TxLastBists = BitFramingReg[2..0]	???

	tag_type[0] = req_mode;
	status = mfrc522_to_card(Transceive_CMD, tag_type, 1, tag_type, &backBits);

	if ((status != CARD_FOUND) || (backBits != 0x10))
	{
		status = ERROR;
	}

	return status;
}

uint8_t mfrc522_to_card(uint8_t cmd, uint8_t* send_data, uint8_t send_data_len, uint8_t* back_data, uint32_t* back_data_len)
{
	uint8_t status = ERROR;
	uint8_t irqEn = 0x00;
	uint8_t waitIRq = 0x00;
	uint8_t lastBits;
	uint8_t n;
	uint8_t	tmp;
	uint32_t i;

	switch (cmd)
	{
	case MFAuthent_CMD:		//Certification cards close
	{
		irqEn = 0x12;
		waitIRq = 0x10;
		break;
	}
	case Transceive_CMD:	//Transmit FIFO data
	{
		irqEn = 0x77;
		waitIRq = 0x30;
		break;
	}
	default:
		break;
	}

	//mfrc522_write(ComIEnReg, irqEn|0x80);	//Interrupt request
	n = mfrc522_read(ComIrqReg);
	mfrc522_write(ComIrqReg, n & (~0x80));//clear all interrupt bits
	n = mfrc522_read(FIFOLevelReg);
	mfrc522_write(FIFOLevelReg, n | 0x80);//flush FIFO data

	mfrc522_write(CommandReg, Idle_CMD);	//NO action; Cancel the current cmd???

	//Writing data to the FIFO
	for (i = 0; i < send_data_len; i++)
	{
		mfrc522_write(FIFODataReg, send_data[i]);
	}

	//Execute the cmd
	mfrc522_write(CommandReg, cmd);
	if (cmd == Transceive_CMD)
	{
		n = mfrc522_read(BitFramingReg);
		mfrc522_write(BitFramingReg, n | 0x80);
	}

	//Waiting to receive data to complete
	i = 2000;	//i according to the clock frequency adjustment, the operator M1 card maximum waiting time 25ms???
	do
	{
		//CommIrqReg[7..0]
		//Set1 TxIRq RxIRq IdleIRq HiAlerIRq LoAlertIRq ErrIRq TimerIRq
		n = mfrc522_read(ComIrqReg);
		i--;
	} while ((i != 0) && !(n & 0x01) && !(n & waitIRq));

	tmp = mfrc522_read(BitFramingReg);
	mfrc522_write(BitFramingReg, tmp & (~0x80));

	if (i != 0)
	{
		if (!(mfrc522_read(ErrorReg) & 0x1B))	//BufferOvfl Collerr CRCErr ProtecolErr
		{
			status = CARD_FOUND;
			if (n & irqEn & 0x01)
			{
				status = CARD_NOT_FOUND;			//??   
			}

			if (cmd == Transceive_CMD)
			{
				n = mfrc522_read(FIFOLevelReg);
				lastBits = mfrc522_read(ControlReg) & 0x07;
				if (lastBits)
				{
					*back_data_len = (n - 1) * 8 + lastBits;
				}
				else
				{
					*back_data_len = n * 8;
				}

				if (n == 0)
				{
					n = 1;
				}
				if (n > MAX_LEN)
				{
					n = MAX_LEN;
				}

				//Reading the received data in FIFO
				for (i = 0; i < n; i++)
				{
					back_data[i] = mfrc522_read(FIFODataReg);
				}
			}
		}
		else
		{
			status = ERROR;
		}

	}

	//SetBitMask(ControlReg,0x80);           //timer stops
	//mfrc522_write(cmdReg, PCD_IDLE); 

	return status;
}


uint8_t mfrc522_get_card_serial(uint8_t* serial_out)
{
	uint8_t status;
	uint8_t i;
	uint8_t serNumCheck = 0;
	uint32_t unLen;

	mfrc522_write(BitFramingReg, 0x00);		//TxLastBists = BitFramingReg[2..0]

	serial_out[0] = PICC_ANTICOLL;
	serial_out[1] = 0x20;
	status = mfrc522_to_card(Transceive_CMD, serial_out, 2, serial_out, &unLen);

	if (status == CARD_FOUND)
	{
		//Check card serial number
		for (i = 0; i < 4; i++)
		{
			serNumCheck ^= serial_out[i];
		}
		if (serNumCheck != serial_out[i])
		{
			status = ERROR;
		}
	}
	return status;
}