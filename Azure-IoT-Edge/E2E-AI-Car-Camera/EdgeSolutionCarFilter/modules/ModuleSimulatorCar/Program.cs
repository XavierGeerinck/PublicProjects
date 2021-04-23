namespace ModuleSimulatorCar
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

    class Program
    {
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

            // Start our simulator
            // Note: this is not async, we can run on the main thread
            StartSimulator(ioTHubModuleClient, "data/car.csv");
        }

        static async void StartSimulator(ModuleClient ioTHubModuleClient, string filePath)
        {
            int lineCount = 0;
            string line;

            System.IO.StreamReader file = new System.IO.StreamReader(filePath);

            while ((line = file.ReadLine()) != null)
            {
                // Skip the first line -> it's the header
                if (lineCount == 0) {
                    lineCount++;
                    continue;
                }

                // Send message
                var now = DateTime.Now.ToString("g");
                System.Console.WriteLine($"[Simulator][{now}] {line}");
                var message = new Message(Encoding.UTF8.GetBytes(line));
                await ioTHubModuleClient.SendEventAsync("output-simulator-car", message);

                // Sleep for a second and go to the next line
                lineCount++;
                System.Threading.Thread.Sleep(5000);
            }

            file.Close();

            // Loop infinitely
            System.Console.WriteLine("[Simulator] Reached end of CSV file, restarting");
            StartSimulator(ioTHubModuleClient, filePath);
        }
    }
}
