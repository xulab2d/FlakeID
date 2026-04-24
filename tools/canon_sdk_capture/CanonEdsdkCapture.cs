using System;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;

namespace FlakeMl.CanonEdsdkCapture
{
    internal static class Program
    {
        public static int Main(string[] args)
        {
            try
            {
                Options options = Options.Parse(args);
                using (CanonEdsdkClient client = new CanonEdsdkClient(options.DllDirectory))
                {
                    if (options.ProbeOnly)
                    {
                        ProbeResult probe = client.Probe();
                        Console.WriteLine(
                            "probe_ok=true camera_count={0} session_opened={1}",
                            probe.CameraCount,
                            probe.SessionOpened ? "true" : "false"
                        );
                        return 0;
                    }

                    if (string.IsNullOrWhiteSpace(options.OutputPath))
                    {
                        throw new ArgumentException("An --output path is required unless --probe is used.");
                    }

                    string outputPath = Path.GetFullPath(options.OutputPath);
                    client.Capture(outputPath, TimeSpan.FromSeconds(options.TimeoutSeconds));
                    Console.WriteLine("captured={0}", outputPath);
                    return 0;
                }
            }
            catch (Exception exception)
            {
                Console.Error.WriteLine(exception.Message);
                return 1;
            }
        }
    }

    internal sealed class Options
    {
        public string DllDirectory { get; private set; }
        public string OutputPath { get; private set; }
        public double TimeoutSeconds { get; private set; }
        public bool ProbeOnly { get; private set; }

        public Options()
        {
            DllDirectory = @"C:\Program Files (x86)\Canon\EOS Utility\EU3";
            OutputPath = string.Empty;
            TimeoutSeconds = 45.0;
            ProbeOnly = false;
        }

        public static Options Parse(string[] args)
        {
            Options options = new Options();
            for (int index = 0; index < args.Length; index++)
            {
                string token = args[index];
                switch (token)
                {
                    case "--dll-dir":
                        options.DllDirectory = RequireValue(args, ref index, token);
                        break;
                    case "--output":
                        options.OutputPath = RequireValue(args, ref index, token);
                        break;
                    case "--timeout-s":
                        options.TimeoutSeconds = double.Parse(
                            RequireValue(args, ref index, token),
                            CultureInfo.InvariantCulture
                        );
                        break;
                    case "--probe":
                        options.ProbeOnly = true;
                        break;
                    default:
                        throw new ArgumentException("Unknown argument: " + token);
                }
            }

            return options;
        }

        private static string RequireValue(string[] args, ref int index, string option)
        {
            if (index + 1 >= args.Length)
            {
                throw new ArgumentException("Missing value for " + option);
            }

            index++;
            return args[index];
        }
    }

    internal sealed class CanonEdsdkClient : IDisposable
    {
        private const uint EdsErrorOk = 0x00000000;
        private const uint EdsPropIdSaveTo = 0x0000000B;
        private const uint EdsSaveToHost = 2;
        private const uint EdsCameraCommandTakePicture = 0x00000000;
        private const uint EdsObjectEventDirItemRequestTransfer = 0x00000208;
        private const uint EdsFileCreateDispositionCreateAlways = 1;
        private const uint EdsAccessReadWrite = 2;

        private readonly EdsObjectEventHandler _objectEventHandler;
        private readonly string _dllDirectory;
        private IntPtr _cameraList = IntPtr.Zero;
        private IntPtr _camera = IntPtr.Zero;
        private bool _sessionOpened;

        private ManualResetEventSlim _downloadCompleted = new ManualResetEventSlim(false);
        private Exception _downloadException;
        private string _pendingOutputPath = string.Empty;

        public CanonEdsdkClient(string dllDirectory)
        {
            _dllDirectory = dllDirectory;
            if (!Directory.Exists(_dllDirectory))
            {
                throw new DirectoryNotFoundException("Canon EOS Utility SDK directory not found: " + _dllDirectory);
            }

            NativeMethods.SetDllDirectory(_dllDirectory);
            Check(NativeMethods.EdsInitializeSDK(), "Failed to initialize Canon EDSDK.");
            _objectEventHandler = new EdsObjectEventHandler(OnObjectEvent);
        }

        public ProbeResult Probe()
        {
            OpenFirstCamera();
            return new ProbeResult
            {
                CameraCount = GetCameraCount(),
                SessionOpened = _sessionOpened,
            };
        }

        public void Capture(string outputPath, TimeSpan timeout)
        {
            if (timeout.TotalSeconds <= 0)
            {
                throw new ArgumentOutOfRangeException("timeout", "Timeout must be positive.");
            }

            OpenFirstCamera();
            Directory.CreateDirectory(Path.GetDirectoryName(outputPath) ?? ".");
            if (File.Exists(outputPath))
            {
                File.Delete(outputPath);
            }

            _pendingOutputPath = outputPath;
            _downloadException = null;
            _downloadCompleted.Dispose();
            _downloadCompleted = new ManualResetEventSlim(false);

            ConfigureHostCapture();
            Check(
                NativeMethods.EdsSendCommand(_camera, EdsCameraCommandTakePicture, 0),
                "Failed to trigger the Canon shutter. Close EOS Utility or live view if it is still holding the camera."
            );

            DateTime deadline = DateTime.UtcNow.Add(timeout);
            while (!_downloadCompleted.IsSet)
            {
                Check(NativeMethods.EdsGetEvent(), "EDSDK event pump failed while waiting for the downloaded image.");
                if (DateTime.UtcNow >= deadline)
                {
                    throw new TimeoutException(
                        "Timed out waiting for the camera to download the captured image. " +
                        "Check that EOS Utility is closed and the camera is not in a conflicting remote-control mode."
                    );
                }

                Thread.Sleep(50);
            }

            if (_downloadException != null)
            {
                throw _downloadException;
            }

            if (!File.Exists(outputPath))
            {
                throw new FileNotFoundException("The capture completed but no output file was written.", outputPath);
            }
        }

        public void Dispose()
        {
            if (_sessionOpened && _camera != IntPtr.Zero)
            {
                NativeMethods.EdsCloseSession(_camera);
                _sessionOpened = false;
            }

            SafeRelease(_camera);
            SafeRelease(_cameraList);
            NativeMethods.EdsTerminateSDK();
            _downloadCompleted.Dispose();
            GC.SuppressFinalize(this);
        }

        private void OpenFirstCamera()
        {
            if (_sessionOpened && _camera != IntPtr.Zero)
            {
                return;
            }

            if (_cameraList == IntPtr.Zero)
            {
                Check(
                    NativeMethods.EdsGetCameraList(out _cameraList),
                    "Failed to enumerate Canon cameras via EDSDK."
                );
            }

            uint count = GetCameraCount();
            if (count == 0)
            {
                throw new InvalidOperationException(
                    "No Canon cameras were detected by EDSDK. Make sure the camera is on, connected by USB, and visible to Windows."
                );
            }

            if (_camera == IntPtr.Zero)
            {
                Check(
                    NativeMethods.EdsGetChildAtIndex(_cameraList, 0, out _camera),
                    "Failed to open the first Canon camera reference."
                );
            }

            Check(
                NativeMethods.EdsOpenSession(_camera),
                "Failed to open the Canon camera session. Close EOS Utility or any live-view/remote window that may still own the camera."
            );
            _sessionOpened = true;
        }

        private uint GetCameraCount()
        {
            uint count;
            Check(NativeMethods.EdsGetChildCount(_cameraList, out count), "Failed to read the Canon camera count.");
            return count;
        }

        private void ConfigureHostCapture()
        {
            Check(
                NativeMethods.EdsSetObjectEventHandler(
                    _camera,
                    EdsObjectEventDirItemRequestTransfer,
                    _objectEventHandler,
                    IntPtr.Zero
                ),
                "Failed to register the Canon download event handler."
            );

            uint saveTo = EdsSaveToHost;
            Check(
                NativeMethods.EdsSetPropertyData(
                    _camera,
                    EdsPropIdSaveTo,
                    0,
                    Marshal.SizeOf(typeof(uint)),
                    ref saveTo
                ),
                "Failed to switch the Canon save destination to host."
            );

            EdsCapacity capacity = new EdsCapacity
            {
                NumberOfFreeClusters = int.MaxValue,
                BytesPerSector = 512,
                Reset = 1,
            };
            Check(NativeMethods.EdsSetCapacity(_camera, capacity), "Failed to update Canon host storage capacity.");
        }

        private uint OnObjectEvent(uint eventCode, IntPtr reference, IntPtr context)
        {
            if (eventCode != EdsObjectEventDirItemRequestTransfer || reference == IntPtr.Zero)
            {
                return EdsErrorOk;
            }

            IntPtr stream = IntPtr.Zero;
            try
            {
                EdsDirectoryItemInfo info;
                Check(
                    NativeMethods.EdsGetDirectoryItemInfo(reference, out info),
                    "Failed to read Canon directory item information."
                );
                Check(
                    NativeMethods.EdsCreateFileStream(
                        _pendingOutputPath,
                        EdsFileCreateDispositionCreateAlways,
                        EdsAccessReadWrite,
                        out stream
                    ),
                    "Failed to create the output file stream for the downloaded Canon image."
                );
                Check(
                    NativeMethods.EdsDownload(reference, info.Size, stream),
                    string.Format(
                        CultureInfo.InvariantCulture,
                        "Failed while downloading the Canon image to disk. directory_item_size={0} file_name={1}",
                        info.Size,
                        info.FileName ?? string.Empty
                    )
                );
                Check(
                    NativeMethods.EdsDownloadComplete(reference),
                    "Failed to finalize the Canon image download."
                );
            }
            catch (Exception exception)
            {
                _downloadException = exception;
            }
            finally
            {
                SafeRelease(stream);
                SafeRelease(reference);
                _downloadCompleted.Set();
            }

            return EdsErrorOk;
        }

        private static void Check(uint errorCode, string context)
        {
            if (errorCode == EdsErrorOk)
            {
                return;
            }

            throw new InvalidOperationException(string.Format(
                CultureInfo.InvariantCulture,
                "{0} Canon error=0x{1:X8}.",
                context,
                errorCode
            ));
        }

        private static void SafeRelease(IntPtr reference)
        {
            if (reference != IntPtr.Zero)
            {
                NativeMethods.EdsRelease(reference);
            }
        }
    }

    internal sealed class ProbeResult
    {
        public uint CameraCount { get; set; }
        public bool SessionOpened { get; set; }
    }

    [StructLayout(LayoutKind.Sequential)]
    internal struct EdsCapacity
    {
        public int NumberOfFreeClusters;
        public int BytesPerSector;
        public int Reset;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]
    internal struct EdsDirectoryItemInfo
    {
        public ulong Size;
        public int IsFolder;
        public uint GroupId;
        public uint Option;

        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 256)]
        public string FileName;

        public uint Format;
        public uint DateTime;
    }

    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    internal delegate uint EdsObjectEventHandler(uint eventCode, IntPtr reference, IntPtr context);

    internal static class NativeMethods
    {
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern bool SetDllDirectory(string pathName);

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsInitializeSDK();

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsTerminateSDK();

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsGetEvent();

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsGetCameraList(out IntPtr cameraListRef);

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsGetChildCount(IntPtr parentRef, out uint count);

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsGetChildAtIndex(IntPtr parentRef, int index, out IntPtr childRef);

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsOpenSession(IntPtr cameraRef);

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsCloseSession(IntPtr cameraRef);

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsSendCommand(IntPtr cameraRef, uint command, int parameter);

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsSetObjectEventHandler(
            IntPtr cameraRef,
            uint eventCode,
            EdsObjectEventHandler handler,
            IntPtr context
        );

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsSetPropertyData(
            IntPtr reference,
            uint propertyId,
            int parameter,
            int size,
            ref uint data
        );

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsSetCapacity(IntPtr cameraRef, EdsCapacity capacity);

        [DllImport("EDSDK.dll", CharSet = CharSet.Ansi, CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsCreateFileStream(
            string fileName,
            uint createDisposition,
            uint desiredAccess,
            out IntPtr streamRef
        );

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsGetDirectoryItemInfo(
            IntPtr directoryItemRef,
            out EdsDirectoryItemInfo directoryItemInfo
        );

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsDownload(IntPtr directoryItemRef, ulong readSize, IntPtr streamRef);

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsDownloadComplete(IntPtr directoryItemRef);

        [DllImport("EDSDK.dll", CallingConvention = CallingConvention.StdCall)]
        public static extern uint EdsRelease(IntPtr reference);
    }
}
