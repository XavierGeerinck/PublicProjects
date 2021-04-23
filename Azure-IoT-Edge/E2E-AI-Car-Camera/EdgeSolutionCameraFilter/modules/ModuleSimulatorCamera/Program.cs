namespace ModuleSimulatorCamera
{
    using System;
    using System.IO;
    using System.Runtime.InteropServices;
    using System.Runtime.Loader;
    using System.Security.Cryptography.X509Certificates;
    using System.Text;
    using System.Threading;
    using System.Threading.Tasks;
    using System.Diagnostics;
    using Microsoft.Azure.Devices.Client;
    using Microsoft.Azure.Devices.Client.Transport.Mqtt;

    class Program
    {
        static string videoDestinationPath = "/app/stream/out.mp4";

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
            StartSimulator(ioTHubModuleClient, "data/");
        }

        static void StartSimulator(ModuleClient ioTHubModuleClient, string filePath)
        {
            // Get the images that we want to convert to a video stream
            string [] fileEntries = Directory.GetFiles(filePath);

            var process = new Process()
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = "ffmpeg",
                    Arguments = $"-y -framerate 1 -pattern_type glob -i {filePath}/*.png -c:v libx264 -r 30 -pix_fmt yuv420p -vf \"pad=ceil(iw/2)*2:ceil(ih/2)*2\" {videoDestinationPath}",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                }
            };

            // Compile the video
            // Console.WriteLine($"ffmpeg -y -framerate 1 -pattern_type glob -i {Directory.GetCurrentDirectory()}/{filePath}*.png -c:v libx264 -r 30 -pix_fmt yuv420p -vf \"pad=ceil(iw/2)*2:ceil(ih/2)*2\" {videoDestinationPath}");
            Console.WriteLine($"[Simulator][{DateTime.Now.ToString("g")}] Creating video file from images in {filePath}*.png");   
            process.Start();
            process.WaitForExit();
            Console.WriteLine($"[Simulator][{DateTime.Now.ToString("g")}] Wrote video file to {videoDestinationPath}");

            // Wait a minute before we repeat
            Console.WriteLine($"[Simulator][{DateTime.Now.ToString("g")}] Waiting 60 seconds before repeating");
            System.Threading.Thread.Sleep(60 * 1000);
            StartSimulator(ioTHubModuleClient, filePath);
        }
    }
}
