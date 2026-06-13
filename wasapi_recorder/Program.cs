using System;
using System.IO;
using System.Threading;
using NAudio.Wave;
using NAudio.CoreAudioApi;

class WasapiRecorder
{
    [STAThread]
    static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.Error.WriteLine("Usage: WasapiRecorder <duration_secs> <output_path> [device_name]");
            return 1;
        }

        int duration = int.Parse(args[0]);
        string outputPath = args[1];
        string searchName = args.Length > 2 ? args[2] : "VoiceMeeter";

        var enumerator = new MMDeviceEnumerator();
        MMDevice captureDevice = null;

        // Try to find VoiceMeeter device first
        foreach (var dev in enumerator.EnumerateAudioEndPoints(DataFlow.All, DeviceState.Active))
        {
            Console.Error.WriteLine($"  [{dev.DataFlow}] {dev.FriendlyName}");
            if (dev.FriendlyName.Contains(searchName) && dev.DataFlow == DataFlow.Render)
            {
                captureDevice = dev;
            }
        }

        // Fallback to default
        if (captureDevice == null)
        {
            captureDevice = enumerator.GetDefaultAudioEndpoint(DataFlow.Render, Role.Console);
            Console.Error.WriteLine($"Using default: {captureDevice.FriendlyName}");
        }
        else
        {
            Console.Error.WriteLine($"Using: {captureDevice.FriendlyName}");
        }

        using (var capture = new WasapiLoopbackCapture(captureDevice))
        {
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outputPath)));

            using (var writer = new WaveFileWriter(outputPath, capture.WaveFormat))
            {
                var resetEvent = new AutoResetEvent(false);
                long totalBytes = 0;
                int packets = 0;

                Console.Error.WriteLine($"Format: {capture.WaveFormat.SampleRate}Hz, {capture.WaveFormat.Channels}ch");
                Console.Error.WriteLine($"Recording {duration}s...");

                capture.DataAvailable += (s, e) =>
                {
                    writer.Write(e.Buffer, 0, e.BytesRecorded);
                    totalBytes += e.BytesRecorded;
                    packets++;
                };

                capture.RecordingStopped += (s, e) =>
                {
                    resetEvent.Set();
                };

                capture.StartRecording();
                Thread.Sleep((duration + 1) * 1000);
                capture.StopRecording();
                resetEvent.WaitOne(3000);
                writer.Close();

                Console.Error.WriteLine($"Done: {totalBytes} bytes, {packets} packets");
                Console.WriteLine(totalBytes > 44 ? $"OK:{totalBytes}" : "SILENT");
            }
        }
        return 0;
    }
}
