#include <signal.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdio.h>
#include <stdarg.h>
#include <errno.h>

// applibs_versions.h defines the API struct versions to use for applibs APIs
#include "applibs_versions.h"
#include <applibs/log.h>
#include <applibs/networking.h>
#include <applibs/gpio.h>
#include <applibs/storage.h>

#include "parson.h" // used to parse Device Twin messages.
#include "epoll_timerfd_utilities.h"

#include "avnet_mt3620_sk.h"

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

// LED
static int deviceTwinStatusLedGpioFd = -1;
static bool statusLedOn = false;
#define DEVICE_TWIN_LED_KEY "MyGreenLED" // Which device key will we update to change the LED?

// Timer / polling
static int azureTimerFd = -1;
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

// Method definitions
static void SendMessageCallback(IOTHUB_CLIENT_CONFIRMATION_RESULT result, void* context);
static void TwinCallback(DEVICE_TWIN_UPDATE_STATE updateState, const unsigned char* payload, size_t payloadSize, void* userContextCallback);
static void TwinReportBoolState(const char* propertyName, bool propertyValue);
static void ReportStatusCallback(int result, void* context);
static const char* GetReasonString(IOTHUB_CLIENT_CONNECTION_STATUS_REASON reason);
static const char* getAzureSphereProvisioningResultString(AZURE_SPHERE_PROV_RETURN_VALUE provisioningResult);
static void SendTelemetry(const unsigned char* key, const unsigned char* value);
static void SetupAzureClient(void);
static void HubConnectionStatusCallback(IOTHUB_CLIENT_CONNECTION_STATUS result, IOTHUB_CLIENT_CONNECTION_STATUS_REASON reason, void* userContextCallback);
static void TerminationHandler(int signalNumber);

int main(int argc, char *argv[])
{
	Log_Debug("Application Starting\n");

	// Set the Scope Id
	if (argc == 2) {
		Log_Debug("Setting Azure Scope ID %s\n", argv[1]);
		strncpy(scopeId, argv[1], SCOPEID_LENGTH);
	} else {
		Log_Debug("ScopeId needs to be set in the app_manifest CmdArgs\n");
	}

	// Start our Peripherals
	if (InitPeripheralsAndHandlers() != 0) {
		Log_Debug("Failure in InitPeripheralsAndHandlers()\n");
		terminationRequired = true;
	}

	// Main loop
	while (!terminationRequired) {
		if (WaitForEventAndCallHandler(epollFd) != 0) {
			Log_Debug("Failure in WaitForEventAndCallHandler()\n");
			terminationRequired = true;
		}
	}

	ClosePeripheralsAndHandlers();

	Log_Debug("Application exiting.\n");

	return 0;
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
	Log_Debug("[IoTHub][INFO] IoTHubDeviceClient_LL_CreateWithAzureSphereDeviceAuthProvisioning returned '%s'.\n",	getAzureSphereProvisioningResultString(provResult));

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
static void HubConnectionStatusCallback(IOTHUB_CLIENT_CONNECTION_STATUS result,	IOTHUB_CLIENT_CONNECTION_STATUS_REASON reason,void* userContextCallback)
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
	Log_Debug("[IoTHub][INFO] Received IoT Twin Update from IoT Hub");

	size_t nullTerminatedJsonSize = payloadSize + 1;
	char* nullTerminatedJsonString = (char*)malloc(nullTerminatedJsonSize);
	if (nullTerminatedJsonString == NULL) {
		Log_Debug("ERROR: Could not allocate buffer for twin update payload.\n");
		abort();
	}

	// Copy the provided buffer to a null terminated buffer.
	memcpy(nullTerminatedJsonString, payload, payloadSize);
	// Add the null terminator at the end.
	nullTerminatedJsonString[nullTerminatedJsonSize - 1] = 0;

	JSON_Value* rootProperties = NULL;
	rootProperties = json_parse_string(nullTerminatedJsonString);
	if (rootProperties == NULL) {
		Log_Debug("WARNING: Cannot parse the string as JSON content.\n");
		goto cleanup;
	}

	JSON_Object* rootObject = json_value_get_object(rootProperties);
	JSON_Object* desiredProperties = json_object_dotget_object(rootObject, "desired");
	if (desiredProperties == NULL) {
		desiredProperties = rootObject;
	}

	// Handle the Device Twin Desired Properties here.
	JSON_Object* LEDState = json_object_dotget_object(desiredProperties, DEVICE_TWIN_LED_KEY);
	if (LEDState != NULL) {
		statusLedOn = (bool)json_object_get_boolean(LEDState, "value");
		Log_Debug("[IoTHub] Changing Status LED to %s\n", (json_object_get_boolean(LEDState, "value") ? "true" : "false"));
		GPIO_SetValue(deviceTwinStatusLedGpioFd, (statusLedOn == true ? GPIO_Value_Low : GPIO_Value_High));
		TwinReportBoolState(DEVICE_TWIN_LED_KEY, statusLedOn);
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
		Log_Debug("Failed to get Network state\n");
	}

	if (iothubAuthenticated) {
		// Send something
		SendTelemetry("Test", "Hello World");
		IoTHubDeviceClient_LL_DoWork(iothubClientHandle);
	}
}

static EventData azureEventData = { .eventHandler = &AzureTimerEventHandler };

static int InitPeripheralsAndHandlers(void)
{
	struct sigaction action;
	memset(&action, 0, sizeof(struct sigaction));
	action.sa_handler = TerminationHandler;
	sigaction(SIGTERM, &action, NULL);

	epollFd = CreateEpollFd();
	if (epollFd < 0) {
		Log_Debug("Could not CreateEpollFd()");
		return -1;
	}

	// Open the LED as output
	Log_Debug("Opening GREEN LED as output\n");
	deviceTwinStatusLedGpioFd = GPIO_OpenAsOutput(AVNET_MT3620_SK_USER_LED_GREEN, GPIO_OutputMode_PushPull, GPIO_Value_High);
	if (deviceTwinStatusLedGpioFd < 0) {
		Log_Debug("ERROR: Could not open LED: %s (%d).\n", strerror(errno), errno);
		return -1;
	}

	azureIoTPollPeriodSeconds = AzureIoTDefaultPollPeriodSeconds;
	struct timespec azureTelemetryPeriod = { azureIoTPollPeriodSeconds, 0 };
	azureTimerFd = CreateTimerFdAndAddToEpoll(epollFd, &azureTelemetryPeriod, &azureEventData, EPOLLIN);

	return 0;
}

/// <summary>
///     Close peripherals and handlers.
/// </summary>
static void ClosePeripheralsAndHandlers(void)
{
	Log_Debug("Closing file descriptors\n");

	// Leave the LEDs off
	if (deviceTwinStatusLedGpioFd >= 0) {
		GPIO_SetValue(deviceTwinStatusLedGpioFd, GPIO_Value_High);
	}

	CloseFdAndPrintError(azureTimerFd, "AzureTimer");
	CloseFdAndPrintError(deviceTwinStatusLedGpioFd, "StatusLed");
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