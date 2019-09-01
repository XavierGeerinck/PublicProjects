#include <stdbool.h>
#include <errno.h>
#include <string.h>
#include <time.h>
#include <signal.h> // sig_atomic_t
#include <unistd.h> // for Sleep

// applibs_versions.h defines the API struct versions to use for applibs APIs.
#include "applibs_versions.h"
#include <applibs/log.h>
#include <applibs/networking.h>
#include <applibs/gpio.h>
#include <applibs/storage.h>

#include "mfrc522.h" // RFID scanner
#include "oled.h" // Oled screen
#include "parson.h" // used to parse Device Twin messages.
#include "epoll_timerfd_utilities.h" // Poller
#include "avnet_mt3620_sk.h" // Device bindings
#include "map.h" // Map Datastructure

// Azure IoT SDK
#include <azureiot/iothub_client_core_common.h>
#include <azureiot/iothub_device_client_ll.h>
#include <azureiot/iothub_client_options.h>
#include <azureiot/iothubtransportmqtt.h>
#include <azureiot/iothub.h>
#include <azureiot/azure_sphere_provisioning.h>

static volatile sig_atomic_t terminationRequired = false;

// Initialization/Cleanup
static int InitPeripheralsAndHandlers(void);
static void ClosePeripheralsAndHandlers(void);

// Price Map
map_str_t priceMap;

// Timer / polling
static int azureTimerFd = -1;
static int rfidTimerFd = -1;
static int epollFd = -1;

// Azure IoT Poll Periods
static const int AzureIoTDefaultPollPeriodSeconds = 5;
static const int AzureIoTMinReconnectPeriodSeconds = 60;
static const int AzureIoTMaxReconnectPeriodSeconds = 10 * 60;
static int azureIoTPollPeriodSeconds = -1;

// Azure IoT Hub Defines
#define SCOPEID_LENGTH 20
static char scopeId[SCOPEID_LENGTH]; // ScopeId for the Azure IoT Central application, set in app_manifest.json, CmdArgs
static IOTHUB_DEVICE_CLIENT_LL_HANDLE iothubClientHandle = NULL;
static const int keepalivePeriodSeconds = 20;
static bool iothubAuthenticated = false;

// Method Definitions - Generic
void delay(int s);

// Method definitions - Azure IOT 
static void SendMessageCallback(IOTHUB_CLIENT_CONFIRMATION_RESULT result, void* context);
static void TwinCallback(DEVICE_TWIN_UPDATE_STATE updateState, const unsigned char* payload, size_t payloadSize, void* userContextCallback);
static void TwinReportBoolState(const char* propertyName, bool propertyValue);
static void TwinReportStringState(const char* propertyNam, const char* propertyValue);
static void ReportStatusCallback(int result, void* context);
static const char* GetReasonString(IOTHUB_CLIENT_CONNECTION_STATUS_REASON reason);
static const char* getAzureSphereProvisioningResultString(AZURE_SPHERE_PROV_RETURN_VALUE provisioningResult);
static void SendTelemetry(const unsigned char* key, const unsigned char* value);
static void SendTelemetryCustomEventBuffer(const unsigned char* eventBuffer);
static void SetupAzureClient(void);
static void HubConnectionStatusCallback(IOTHUB_CLIENT_CONNECTION_STATUS result, IOTHUB_CLIENT_CONNECTION_STATUS_REASON reason, void* userContextCallback);
static void TerminationHandler(int signalNumber);

// Method Definitions - OLED
void oled_template_waiting_for_rfc(void);
void oled_template_waiting_for_rfc_with_version(uint8_t version);
void oled_template_show_serial(char* serial);
void oled_template_show_serial_and_price(char* serial, char* price);
void btox(char* xp, const char* bb, int n);

// Timer Event Data and Handlers
static const int RFIDDefaultPollPeriodNanoSeconds = 100 * 1000 * 1000; // Poll every 100ms
static void RFIDTimerEventHandler(void);
static void AzureTimerEventHandler(EventData* eventData);
static EventData azureEventData = { .eventHandler = &AzureTimerEventHandler };
static EventData rfidPollEventData = { .eventHandler = &RFIDTimerEventHandler };

// Variables
static bool rfidVersionDetected = false;
static uint8_t rfidVersion = -1;

// Start Code
void delay(int s)
{
	sleep(s);
}

int main(int argc, char *argv[])
{
	Log_Debug("[Application][INFO] Starting\n");

	// Set the DPS Scope Id
	if (argc == 2) {
		Log_Debug("[Application][INFO] Setting Azure Scope ID %s\n", argv[1]);
		strncpy(scopeId, argv[1], SCOPEID_LENGTH);
	}
	else {
		Log_Debug("[Application][ERROR] ScopeId needs to be set in the app_manifest CmdArgs\n");
	}

	// Init the price map
	map_init(&priceMap);
	map_set(&priceMap, "7908C820", "Normal: $10.00"); // Normal Tag
	map_set(&priceMap, "8804399D", "Zombie: $15.50"); // Zombie
	map_set(&priceMap, "88041B9D", "Skeleton: $20.00"); // Skeleton

	// Start our Peripherals
	if (InitPeripheralsAndHandlers() != 0) {
		Log_Debug("[Application][ERROR] Failure in InitPeripheralsAndHandlers()\n");
		terminationRequired = true;
	}

	while (!terminationRequired) {
		if (WaitForEventAndCallHandler(epollFd) != 0) {
			Log_Debug("[Application][ERROR] Failure in WaitForEventAndCallHandler()\n");
			terminationRequired = true;
		}
	}

	ClosePeripheralsAndHandlers();
	map_deinit(&priceMap);
	Log_Debug("[Application][ERROR] Application exiting.\n");

	return 0;
}

void btox(char* xp, const char* bb, int n)
{
	const char xx[] = "0123456789ABCDEF";
	while (--n >= 0) xp[n] = xx[(bb[n >> 1] >> ((1 - (n & 1)) << 2)) & 0xF];
}

void oled_template_waiting_for_iothub(void)
{
	// Clear the buffer
	oled_buffer_clear();

	// Draw the strings
	sd1306_draw_string(0, 0, "Information", FONT_SIZE_TITLE, white_pixel);
	sd1306_draw_string(OLED_LINE_1_X, OLED_LINE_1_Y, "Waiting for IoTHub", FONT_SIZE_LINE, white_pixel);
	sd1306_draw_string(OLED_LINE_2_X, OLED_LINE_2_Y, "to be connected", FONT_SIZE_LINE, white_pixel);

	// Send the buffer to OLED RAM
	sd1306_refresh();
}

void oled_template_waiting_for_rfc(void)
{
	// Clear the buffer
	oled_buffer_clear();

	// Draw the strings
	sd1306_draw_string(0, 0, "Information", FONT_SIZE_TITLE, white_pixel);
	sd1306_draw_string(OLED_LINE_1_X, OLED_LINE_1_Y, "Waiting for tag to", FONT_SIZE_LINE, white_pixel);
	sd1306_draw_string(OLED_LINE_2_X, OLED_LINE_2_Y, "be detected", FONT_SIZE_LINE, white_pixel);

	// Send the buffer to OLED RAM
	sd1306_refresh();
}

void oled_template_waiting_for_rfc_with_version(uint8_t version)
{
	// Clear the buffer
	oled_buffer_clear();

	// Draw the strings
	sd1306_draw_string(0, 0, "Information", FONT_SIZE_TITLE, white_pixel);
	sd1306_draw_string(OLED_LINE_1_X, OLED_LINE_1_Y, "Waiting for tag to", FONT_SIZE_LINE, white_pixel);
	sd1306_draw_string(OLED_LINE_2_X, OLED_LINE_2_Y, "be detected", FONT_SIZE_LINE, white_pixel);

	char versionBuffer[20];
	sprintf(versionBuffer, "MIFARE Version = %x", version);
	sd1306_draw_string(OLED_LINE_3_X, OLED_LINE_3_Y, versionBuffer, FONT_SIZE_LINE, white_pixel);

	// Send the buffer to OLED RAM
	sd1306_refresh();
}

void oled_template_show_serial(char* serial)
{
	// Clear the buffer
	oled_buffer_clear();

	// Draw the strings
	sd1306_draw_string(0, 0, "Information", FONT_SIZE_TITLE, white_pixel);
	sd1306_draw_string(OLED_LINE_1_X, OLED_LINE_1_Y, "Serial:", FONT_SIZE_LINE, white_pixel);
	sd1306_draw_string(OLED_LINE_2_X, OLED_LINE_2_Y, serial, FONT_SIZE_LINE, white_pixel);

	// Send the buffer to OLED RAM
	sd1306_refresh();
}

void oled_template_show_serial_and_price(char* serial, char* price)
{
	// Clear the buffer
	oled_buffer_clear();

	// Draw the strings
	sd1306_draw_string(0, 0, "Information", FONT_SIZE_TITLE, white_pixel);
	sd1306_draw_string(OLED_LINE_1_X, OLED_LINE_1_Y, "Serial:", FONT_SIZE_LINE, white_pixel);
	sd1306_draw_string(OLED_LINE_2_X, OLED_LINE_2_Y, serial, FONT_SIZE_LINE, white_pixel);
	sd1306_draw_string(OLED_LINE_3_X, OLED_LINE_3_Y, "", FONT_SIZE_LINE, white_pixel);
	sd1306_draw_string(OLED_LINE_4_X, OLED_LINE_4_Y, "Price:", FONT_SIZE_LINE, white_pixel);
	sd1306_draw_string(OLED_LINE_5_X, OLED_LINE_5_Y, price, FONT_SIZE_LINE, white_pixel);

	// Send the buffer to OLED RAM
	sd1306_refresh();
}

/// <summary>
///     Callback confirming message delivered to IoT Hub.
/// </summary>
/// <param name="result">Message delivery status</param>
/// <param name="context">User specified context</param>
static void SendMessageCallback(IOTHUB_CLIENT_CONFIRMATION_RESULT result, void* context)
{
	Log_Debug("[IoTHub][INFO] Message received by IoT Hub. Result is: %d\n", result);
}

static void SendTelemetryCustomEventBuffer(const unsigned char* eventBuffer)
{
	Log_Debug("[IoTHub][INFO] Sending IoT Hub Message: %s\n", eventBuffer);

	IOTHUB_MESSAGE_HANDLE messageHandle = IoTHubMessage_CreateFromString(eventBuffer);

	if (messageHandle == 0) {
		Log_Debug("[IoTHub][WARNING] unable to create a new IoTHubMessage\n");
		return;
	}

	if (IoTHubDeviceClient_LL_SendEventAsync(iothubClientHandle, messageHandle, SendMessageCallback, /*&callback_param*/ 0) != IOTHUB_CLIENT_OK) {
		Log_Debug("[IoTHub][WARNING] failed to hand over the message to IoTHubClient\n");
	}
	else {
		Log_Debug("[IoTHub][INFO] IoTHubClient accepted the message for delivery\n");
	}

	IoTHubMessage_Destroy(messageHandle);
}

/// <summary>
///     Sends telemetry to IoT Hub
/// </summary>
/// <param name="key">The telemetry item to update</param>
/// <param name="value">new telemetry value</param>
static void SendTelemetry(const unsigned char* key, const unsigned char* value)
{
	static char eventBuffer[100] = { 0 };
	static const char* EventMsgTemplate = "{ \"%s\": \"%s\" }";
	int len = snprintf(eventBuffer, sizeof(eventBuffer), EventMsgTemplate, key, value);
	if (len < 0)
		return;

	Log_Debug("[IoTHub][INFO] Sending IoT Hub Message: %s\n", eventBuffer);

	IOTHUB_MESSAGE_HANDLE messageHandle = IoTHubMessage_CreateFromString(eventBuffer);

	if (messageHandle == 0) {
		Log_Debug("[IoTHub][WARNING] unable to create a new IoTHubMessage\n");
		return;
	}

	if (IoTHubDeviceClient_LL_SendEventAsync(iothubClientHandle, messageHandle, SendMessageCallback,
		/*&callback_param*/ 0) != IOTHUB_CLIENT_OK) {
		Log_Debug("[IoTHub][WARNING] failed to hand over the message to IoTHubClient\n");
	}
	else {
		Log_Debug("[IoTHub][INFO] IoTHubClient accepted the message for delivery\n");
	}

	IoTHubMessage_Destroy(messageHandle);
}

/// <summary>
///     Sets up the Azure IoT Hub connection (creates the iothubClientHandle)
///     When the SAS Token for a device expires the connection needs to be recreated
///     which is why this is not simply a one time call.
/// </summary>
static void SetupAzureClient(void)
{
	if (iothubClientHandle != NULL)
		IoTHubDeviceClient_LL_Destroy(iothubClientHandle);

	AZURE_SPHERE_PROV_RETURN_VALUE provResult = IoTHubDeviceClient_LL_CreateWithAzureSphereDeviceAuthProvisioning(scopeId, 10000, &iothubClientHandle);
	Log_Debug("[IoTHub][INFO] IoTHubDeviceClient_LL_CreateWithAzureSphereDeviceAuthProvisioning returned '%s'.\n", getAzureSphereProvisioningResultString(provResult));

	if (provResult.result != AZURE_SPHERE_PROV_RESULT_OK) {

		// If we fail to connect, reduce the polling frequency, starting at
		// AzureIoTMinReconnectPeriodSeconds and with a backoff up to
		// AzureIoTMaxReconnectPeriodSeconds
		if (azureIoTPollPeriodSeconds == AzureIoTDefaultPollPeriodSeconds) {
			azureIoTPollPeriodSeconds = AzureIoTMinReconnectPeriodSeconds;
		}
		else {
			azureIoTPollPeriodSeconds *= 2;
			if (azureIoTPollPeriodSeconds > AzureIoTMaxReconnectPeriodSeconds) {
				azureIoTPollPeriodSeconds = AzureIoTMaxReconnectPeriodSeconds;
			}
		}

		struct timespec azureTelemetryPeriod = { azureIoTPollPeriodSeconds, 0 };
		SetTimerFdToPeriod(azureTimerFd, &azureTelemetryPeriod);

		Log_Debug("[IoTHub][ERROR] failure to create IoTHub Handle - will retry in %i seconds.\n", azureIoTPollPeriodSeconds);
		return;
	}

	// Successfully connected, so make sure the polling frequency is back to the default
	azureIoTPollPeriodSeconds = AzureIoTDefaultPollPeriodSeconds;
	struct timespec azureTelemetryPeriod = { azureIoTPollPeriodSeconds, 0 };
	SetTimerFdToPeriod(azureTimerFd, &azureTelemetryPeriod);

	iothubAuthenticated = true;

	// Now update the screen to show waiting for tag
	// We do this here since else we overwrite it every time
	oled_template_waiting_for_rfc_with_version(rfidVersion);

	if (IoTHubDeviceClient_LL_SetOption(iothubClientHandle, OPTION_KEEP_ALIVE, &keepalivePeriodSeconds) != IOTHUB_CLIENT_OK) {
		Log_Debug("[IoTHub][ERROR] failure setting option \"%s\"\n", OPTION_KEEP_ALIVE);
		return;
	}

	Log_Debug("[IoTHub][INFO] Configuring Device Twin Callback and Connection Status Callback\n");
	IoTHubDeviceClient_LL_SetDeviceTwinCallback(iothubClientHandle, TwinCallback, NULL);
	IoTHubDeviceClient_LL_SetConnectionStatusCallback(iothubClientHandle, HubConnectionStatusCallback, NULL);
}

/// <summary>
///     Creates and enqueues a report containing the name and value pair of a Device Twin reported
///     property. The report is not sent immediately, but it is sent on the next invocation of
///     IoTHubDeviceClient_LL_DoWork().
/// </summary>
/// <param name="propertyName">the IoT Hub Device Twin property name</param>
/// <param name="propertyValue">the IoT Hub Device Twin property value</param>
static void TwinReportBoolState(const char* propertyName, bool propertyValue)
{
	if (iothubClientHandle == NULL) {
		Log_Debug("[IoTHub][ERROR] client not initialized\n");
	}
	else {
		static char reportedPropertiesString[30] = { 0 };
		int len = snprintf(reportedPropertiesString, 30, "{\"%s\":%s}", propertyName,
			(propertyValue == true ? "true" : "false"));
		if (len < 0)
			return;

		if (IoTHubDeviceClient_LL_SendReportedState(
			iothubClientHandle, (unsigned char*)reportedPropertiesString,
			strlen(reportedPropertiesString), ReportStatusCallback, 0) != IOTHUB_CLIENT_OK) {
			Log_Debug("[IoTHub][ERROR] failed to set reported state for '%s'.\n", propertyName);
		}
		else {
			Log_Debug("[IoTHub][ERROR] Reported state for '%s' to value '%s'.\n", propertyName,
				(propertyValue == true ? "true" : "false"));
		}
	}
}

/// <summary>
///     Creates and enqueues a report containing the name and value pair of a Device Twin reported
///     property. The report is not sent immediately, but it is sent on the next invocation of
///     IoTHubDeviceClient_LL_DoWork().
/// </summary>
/// <param name="propertyName">the IoT Hub Device Twin property name</param>
/// <param name="propertyValue">the IoT Hub Device Twin property value</param>
static void TwinReportStringState(const char* propertyName, const char* propertyValue)
{
	if (iothubClientHandle == NULL) {
		Log_Debug("[IoTHub][ERROR] client not initialized\n");
	} else {
		static char reportedPropertiesString[50] = { 0 };
		int len = snprintf(reportedPropertiesString, 50, "{\"%s\":%s}", propertyName, propertyValue);

		if (len < 0)
			return;

		if (IoTHubDeviceClient_LL_SendReportedState(iothubClientHandle, (unsigned char*)reportedPropertiesString, strlen(reportedPropertiesString), ReportStatusCallback, 0) != IOTHUB_CLIENT_OK) {
			Log_Debug("[IoTHub][ERROR] failed to set reported state for '%s'.\n", propertyName);
		} else {
			Log_Debug("[IoTHub][ERROR] Reported state for '%s' to value '%s'.\n", propertyName,	propertyValue);
		}
	}
}

/// <summary>
///     Callback invoked when the Device Twin reported properties are accepted by IoT Hub.
/// </summary>
static void ReportStatusCallback(int result, void* context)
{
	Log_Debug("[IoTHub][INFO] Device Twin reported properties update result: HTTP status code %d\n", result);
}

/// <summary>
///     Sets the IoT Hub authentication state for the app
///     The SAS Token expires which will set the authentication state
/// </summary>
static void HubConnectionStatusCallback(IOTHUB_CLIENT_CONNECTION_STATUS result, IOTHUB_CLIENT_CONNECTION_STATUS_REASON reason, void* userContextCallback)
{
	iothubAuthenticated = (result == IOTHUB_CLIENT_CONNECTION_AUTHENTICATED);
	Log_Debug("[IoTHub][INFO] IoT Hub Authenticated: %s\n", GetReasonString(reason));
}

/// <summary>
///     Callback invoked when a Device Twin update is received from IoT Hub.
///     Updates local state for 'showEvents' (bool).
/// </summary>
/// <param name="payload">contains the Device Twin JSON document (desired and reported)</param>
/// <param name="payloadSize">size of the Device Twin JSON document</param>
static void TwinCallback(DEVICE_TWIN_UPDATE_STATE updateState, const unsigned char* payload, size_t payloadSize, void* userContextCallback)
{
	Log_Debug("[IoTHub][INFO] Received IoT Twin Update from IoT Hub\n");

	size_t nullTerminatedJsonSize = payloadSize + 1;
	char* nullTerminatedJsonString = (char*)malloc(nullTerminatedJsonSize);
	if (nullTerminatedJsonString == NULL) {
		Log_Debug("[IoTHub][ERROR] Could not allocate buffer for twin update payload.\n");
		abort();
	}

	// Copy the provided buffer to a null terminated buffer.
	memcpy(nullTerminatedJsonString, payload, payloadSize);
	// Add the null terminator at the end.
	nullTerminatedJsonString[nullTerminatedJsonSize - 1] = 0;

	JSON_Value* rootProperties = NULL;
	rootProperties = json_parse_string(nullTerminatedJsonString);
	if (rootProperties == NULL) {
		Log_Debug("[IoTHub][WARNING] Cannot parse the string as JSON content.\n");
		goto cleanup;
	}

	JSON_Object* rootObject = json_value_get_object(rootProperties);
	JSON_Object* desiredProperties = json_object_dotget_object(rootObject, "desired");
	if (desiredProperties == NULL) {
		desiredProperties = rootObject;
	}

	// Handle the Price Update (go over all the serials)
	const char* key;
	map_iter_t iter = map_iter(&priceMap);

	Log_Debug("[IoTHub][Twin][INFO] Updating PriceMap\n");
	while ((key = map_next(&priceMap, &iter))) {
		// In our loop, get the JSON object from the twin
		JSON_Object* PriceState = json_object_dotget_object(desiredProperties, key);
		if (PriceState != NULL) {
			const char* priceValue = json_object_get_string(PriceState, "value");
			map_set(&priceMap, key, priceValue);
			Log_Debug("[IoTHub][Twin][INFO] Updating price for %s to %s\n", key, priceValue);

			//TwinReportStringState(key, json_object_get_string(PriceState, "value"));
		}
		else {
			Log_Debug("[IoTHub][Twin][INFO] %s -> %s\n", key, *map_get(&priceMap, key));
		}
	}

cleanup:
	// Release the allocated memory.
	json_value_free(rootProperties);
	free(nullTerminatedJsonString);
}

/// <summary>
/// Azure timer event:  Check connection status and send telemetry
/// </summary>
static void AzureTimerEventHandler(EventData* eventData)
{
	if (ConsumeTimerFdEvent(azureTimerFd) != 0) {
		terminationRequired = true;
		return;
	}

	bool isNetworkReady = false;
	if (Networking_IsNetworkingReady(&isNetworkReady) != -1) {
		if (isNetworkReady && !iothubAuthenticated) {
			SetupAzureClient();
		}
	}
	else {
		Log_Debug("[IoTHub][ERROR] Failed to get Network state\n");
	}

	if (iothubAuthenticated) {
		// Send something
		//SendTelemetry("Test", "Hello World");
		IoTHubDeviceClient_LL_DoWork(iothubClientHandle);
	}
}

static int InitPeripheralsAndHandlers(void)
{
	Log_Debug("[OLED][INFO] Initializing\n");
	if (oled_init())
	{
		Log_Debug("[OLED][INFO] OLED not found!\n");
		return -1;
	}
	else
	{
		Log_Debug("[OLED][INFO] OLED found!\n");
	}

	Log_Debug("[MFRC522][INFO] Initializing\n");
	if (mfrc522_init())
	{
		Log_Debug("[MFRC522][ERROR] RFID Scanner not found!\n");
		return -1;
	}
	else
	{
		Log_Debug("[MFRC522][INFO] RFID Scanner found!\n");
	}

	Log_Debug("[ePoll][INFO] Initializing\n");
	struct sigaction action;
	memset(&action, 0, sizeof(struct sigaction));
	action.sa_handler = TerminationHandler;
	sigaction(SIGTERM, &action, NULL);

	epollFd = CreateEpollFd();
	if (epollFd < 0) {
		Log_Debug("[ePoll][ERROR] Could not CreateEpollFd()");
		return -1;
	}

	// Poll Azure IoT
	azureIoTPollPeriodSeconds = AzureIoTDefaultPollPeriodSeconds;
	struct timespec azureTelemetryPeriod = { azureIoTPollPeriodSeconds, 0 };
	azureTimerFd = CreateTimerFdAndAddToEpoll(epollFd, &azureTelemetryPeriod, &azureEventData, EPOLLIN);

	// Poll RFID Tag
	struct timespec rfidCheckPeriod = { 0, RFIDDefaultPollPeriodNanoSeconds };
	rfidTimerFd = CreateTimerFdAndAddToEpoll(epollFd, &rfidCheckPeriod, &rfidPollEventData, EPOLLIN);

	return 0;
}

static void RFIDTimerEventHandler(void)
{
	// Consume the event!
	if (ConsumeTimerFdEvent(rfidTimerFd) != 0) {
		terminationRequired = true;
		return;
	}

	// If we did not detect the version yet, detect it
	if (!rfidVersionDetected) {
		oled_template_waiting_for_rfc();

		Log_Debug("[MFRC522][INFO] Trying to get version\n"); // 0x91 = 1.0, 0x92 = 0.2 -> https://www.nxp.com/docs/en/data-sheet/MFRC522.pdf (p66 - VersionReg register)
		rfidVersion = mfrc522_read(VersionReg);

		Log_Debug("[MFRC522][INFO] Detected version %d (Hex: %x)\n", rfidVersion, rfidVersion);
		oled_template_waiting_for_rfc_with_version(rfidVersion);

		// Prepare for reading tags
		uint8_t byte;
		byte = mfrc522_read(ComIEnReg);
		mfrc522_write(ComIEnReg, byte | 0x20);
		byte = mfrc522_read(DivIEnReg);
		mfrc522_write(DivIEnReg, byte | 0x80);

		rfidVersionDetected = true;
	}

	// Wait for IoTHub to be online
	if (!iothubAuthenticated) {
		oled_template_waiting_for_iothub();
		Log_Debug("[MFRC522][INFO] Waiting for IoTHub Connection\n");
		return;
	}

	// Try to read the RFID card
	uint8_t str[MAX_LEN]; // Commands: https://www.nxp.com/docs/en/data-sheet/MFRC522.pdf P36
	uint8_t byte = mfrc522_request(PICC_REQALL, str); // Find all the cards antenna area

	if (byte == CARD_FOUND)
	{
		Log_Debug("[MFRC522][INFO] Found a card: %x\n", byte);

		byte = mfrc522_get_card_serial(str);

		if (byte == CARD_FOUND)
		{
			for (byte = 0; byte < 8; byte++)
			{
				Log_Debug("[MFRC522][INFO] Dumping: %x\n", str[byte]);
			}

			// Convert the byte array to a string of bytes
			char hexstr[8];
			btox(hexstr, str, 8);
			hexstr[8] = 0;
			oled_template_show_serial(hexstr);

			// Get the price
			int* val = map_get(&priceMap, hexstr);

			Log_Debug("[MFRC522][INFO] Serial: %s\n", hexstr);
			Log_Debug("[MAP][INFO] Map Price: %s\n", *val);

			// Send the price to IoT Hub
			static char eventBuffer[255] = { 0 };
			static const char* msgTemplate = "{ \"%s\": { \"%s\": \"%s\", \"%s\": \"%s\" } }";
			int len = snprintf(eventBuffer, sizeof(eventBuffer), msgTemplate, "Tag", "Serial", hexstr, "Price", *val);
			if (len < 0)
				return;

			SendTelemetryCustomEventBuffer(eventBuffer);

			// Show the price on the screen
			oled_template_show_serial_and_price(hexstr, *val);
		}
		else
		{
			Log_Debug("[MFRC522][ERROR] Problem while reading card\n");
		}
	}
}

/// <summary>
///     Close peripherals and handlers.
/// </summary>
static void ClosePeripheralsAndHandlers(void)
{
	Log_Debug("[Application][INFO] Closing file descriptors\n");

	CloseFdAndPrintError(azureTimerFd, "AzureTimer");
	CloseFdAndPrintError(rfidTimerFd, "RFIDTimer");
	CloseFdAndPrintError(epollFd, "Epoll");
}

/// <summary>
///     Signal handler for termination requests. This handler must be async-signal-safe.
/// </summary>
static void TerminationHandler(int signalNumber)
{
	// Don't use Log_Debug here, as it is not guaranteed to be async-signal-safe.
	terminationRequired = true;
}

/// <summary>
///     Converts the IoT Hub connection status reason to a string.
/// </summary>
static const char* GetReasonString(IOTHUB_CLIENT_CONNECTION_STATUS_REASON reason)
{
	static char* reasonString = "unknown reason";
	switch (reason) {
	case IOTHUB_CLIENT_CONNECTION_EXPIRED_SAS_TOKEN:
		reasonString = "IOTHUB_CLIENT_CONNECTION_EXPIRED_SAS_TOKEN";
		break;
	case IOTHUB_CLIENT_CONNECTION_DEVICE_DISABLED:
		reasonString = "IOTHUB_CLIENT_CONNECTION_DEVICE_DISABLED";
		break;
	case IOTHUB_CLIENT_CONNECTION_BAD_CREDENTIAL:
		reasonString = "IOTHUB_CLIENT_CONNECTION_BAD_CREDENTIAL";
		break;
	case IOTHUB_CLIENT_CONNECTION_RETRY_EXPIRED:
		reasonString = "IOTHUB_CLIENT_CONNECTION_RETRY_EXPIRED";
		break;
	case IOTHUB_CLIENT_CONNECTION_NO_NETWORK:
		reasonString = "IOTHUB_CLIENT_CONNECTION_NO_NETWORK";
		break;
	case IOTHUB_CLIENT_CONNECTION_COMMUNICATION_ERROR:
		reasonString = "IOTHUB_CLIENT_CONNECTION_COMMUNICATION_ERROR";
		break;
	case IOTHUB_CLIENT_CONNECTION_OK:
		reasonString = "IOTHUB_CLIENT_CONNECTION_OK";
		break;
	}
	return reasonString;
}

/// <summary>
///     Converts AZURE_SPHERE_PROV_RETURN_VALUE to a string.
/// </summary>
static const char* getAzureSphereProvisioningResultString(AZURE_SPHERE_PROV_RETURN_VALUE provisioningResult)
{
	switch (provisioningResult.result) {
	case AZURE_SPHERE_PROV_RESULT_OK:
		return "AZURE_SPHERE_PROV_RESULT_OK";
	case AZURE_SPHERE_PROV_RESULT_INVALID_PARAM:
		return "AZURE_SPHERE_PROV_RESULT_INVALID_PARAM";
	case AZURE_SPHERE_PROV_RESULT_NETWORK_NOT_READY:
		return "AZURE_SPHERE_PROV_RESULT_NETWORK_NOT_READY";
	case AZURE_SPHERE_PROV_RESULT_DEVICEAUTH_NOT_READY:
		return "AZURE_SPHERE_PROV_RESULT_DEVICEAUTH_NOT_READY";
	case AZURE_SPHERE_PROV_RESULT_PROV_DEVICE_ERROR:
		return "AZURE_SPHERE_PROV_RESULT_PROV_DEVICE_ERROR";
	case AZURE_SPHERE_PROV_RESULT_GENERIC_ERROR:
		return "AZURE_SPHERE_PROV_RESULT_GENERIC_ERROR";
	default:
		return "UNKNOWN_RETURN_VALUE";
	}
}