typedef enum SPI_ChipSelectPolarity {
	SPI_ChipSelectPolarity_Invalid = 0x0,
	SPI_ChipSelectPolarity_ActiveLow = 0x1,
	SPI_ChipSelectPolarity_ActiveHigh = 0x2
} SPI_ChipSelectPolarity;

struct SPIMaster_Config {
	uint32_t z__magicAndVersion;
	SPI_ChipSelectPolarity csPolarity;
};