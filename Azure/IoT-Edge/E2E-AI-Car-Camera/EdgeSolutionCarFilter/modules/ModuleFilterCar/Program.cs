namespace ModuleFilterCar
{
    using System;
    using System.IO;
    using System.Runtime.InteropServices;
    using System.Runtime.Loader;
    using System.Security.Cryptography.X509Certificates;
    using System.Text;
    using System.Threading;
    using System.Threading.Tasks;
    using Microsoft.Azure.Devices.Client;
    using Microsoft.Azure.Devices.Client.Transport.Mqtt;
    using Microsoft.ML;
    using ModuleFilterCar.Models;

    class Program
    {
        static int counter;

        private static string modelOutputPath = "./model/Model.zip";

        static void Main(string[] args)
        {
            Init().Wait();

            // Wait until the app unloads or is cancelled
            var cts = new CancellationTokenSource();
            AssemblyLoadContext.Default.Unloading += (ctx) => cts.Cancel();
            Console.CancelKeyPress += (sender, cpe) => cts.Cancel();
            WhenCancelled(cts.Token).Wait();
        }

        /// <summary>
        /// Handles cleanup operations when app is cancelled or unloads
        /// </summary>
        public static Task WhenCancelled(CancellationToken cancellationToken)
        {
            var tcs = new TaskCompletionSource<bool>();
            cancellationToken.Register(s => ((TaskCompletionSource<bool>)s).SetResult(true), tcs);
            return tcs.Task;
        }

        /// <summary>
        /// Initializes the ModuleClient and sets up the callback to receive
        /// messages containing temperature information
        /// </summary>
        static async Task Init()
        {
            MqttTransportSettings mqttSetting = new MqttTransportSettings(TransportType.Mqtt_Tcp_Only);
            ITransportSettings[] settings = { mqttSetting };

            // Open a connection to the Edge runtime
            ModuleClient ioTHubModuleClient = await ModuleClient.CreateFromEnvironmentAsync(settings);
            await ioTHubModuleClient.OpenAsync();
            Console.WriteLine("IoT Hub module client initialized.");

            // Register callback to be called when a message is received by the module
            await ioTHubModuleClient.SetInputMessageHandlerAsync("input-simulator-car", ProcessSimulatorCarMessages, ioTHubModuleClient);
        }

        /// <summary>
        /// This method is called whenever the module is sent a message from the EdgeHub. 
        /// It just pipe the messages without any change.
        /// It prints all the incoming messages.
        /// </summary>
        static async Task<MessageResponse> ProcessSimulatorCarMessages(Message message, object userContext)
        {
            int counterValue = Interlocked.Increment(ref counter);

            var moduleClient = userContext as ModuleClient;
            if (moduleClient == null)
            {
                throw new InvalidOperationException("UserContext doesn't contain " + "expected values");
            }

            byte[] messageBytes = message.GetBytes();
            string messageString = Encoding.UTF8.GetString(messageBytes);
            var now = DateTime.Now.ToString("g");
            Console.WriteLine($"[Filter][{now}][Message #{counterValue}] {messageString}");

            // If our message is not empty, parse it and send back the prediction to IoT Hub.
            if (!string.IsNullOrEmpty(messageString))
            {
                // Predict the speed
                var splittedMessage = messageString.Split(",");
                var predictedCarSpeed = PredictValue(float.Parse(splittedMessage[7]), float.Parse(splittedMessage[8]), float.Parse(splittedMessage[10]));
                var messageResult = new Message(Encoding.UTF8.GetBytes("" + predictedCarSpeed));

                // Print on Console
                now = DateTime.Now.ToString("g");
                System.Console.WriteLine($"[Filter][{now}] Sending Prediction: {predictedCarSpeed}, Actual Speed: {splittedMessage[5]}");

                // Send to IoT Hub
                await moduleClient.SendEventAsync("output-filter-car", messageResult);
            }

            return MessageResponse.Completed;
        }

        public static float PredictValue(float ThrottlePosition, float Engine_RPM, float Acceleration_GS) 
        {
            // Create ML Context with seed for repeteable/deterministic results
            MLContext mlContext = new MLContext(seed: 0);

            var carPointSample = new CarPoint()
            {
                ThrottlePosition = ThrottlePosition,
                Engine_RPM = Engine_RPM,
                Acceleration_Gs = Acceleration_GS
            };

            ITransformer trainedModel;
            using (var stream = new FileStream(modelOutputPath, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                trainedModel = mlContext.Model.Load(stream, out var modelInputSchema);
            }

            // Create prediction engine related to the loaded trained model
            var predEngine = mlContext.Model.CreatePredictionEngine<CarPoint, CarPointSpeedPrediction>(trainedModel);

            // Score
            var resultprediction = predEngine.Predict(carPointSample);

            return resultprediction.Speed_MPH;
        }
    }
}
