using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices.WindowsRuntime;
using System.Threading.Tasks;
using Windows.Devices.Bluetooth;
using Windows.Devices.Bluetooth.Advertisement;
using Windows.Devices.Bluetooth.GenericAttributeProfile;
using Windows.Storage.Streams;

namespace iDotMatrixPro.Services;

public class BluetoothDeviceItem
{
    public string Name { get; set; } = "";
    public string Address { get; set; } = "";
    public ulong RawAddress { get; set; }
}

public class BluetoothManager
{
    public static readonly Guid WriteCharUuid = Guid.Parse("0000fa02-0000-1000-8000-00805f9b34fb");
    public static readonly Guid ReadCharUuid = Guid.Parse("0000fa03-0000-1000-8000-00805f9b34fb");

    private BluetoothLEDevice? _device;
    private GattCharacteristic? _writeCharacteristic;
    private BluetoothLEAdvertisementWatcher? _watcher;
    private string? _currentMode;
    private byte[]? _lastSentPngBytes;

    public bool IsConnected => _device != null && _device.ConnectionStatus == BluetoothConnectionStatus.Connected && _writeCharacteristic != null;
    public string? CurrentAddress { get; private set; }

    public event Action<bool, string>? StatusChanged;
    public event Action<BluetoothDeviceItem>? DeviceDiscovered;
    public event Action? ScanFinished;

    public void StartScan()
    {
        _watcher = new BluetoothLEAdvertisementWatcher
        {
            ScanningMode = BluetoothLEScanningMode.Active
        };

        _watcher.Received += (sender, args) =>
        {
            string name = args.Advertisement.LocalName;
            if (string.IsNullOrEmpty(name))
            {
                name = "Dispositivo BLE";
            }

            if (name.Contains("IDM", StringComparison.OrdinalIgnoreCase) || 
                name.Contains("DOT", StringComparison.OrdinalIgnoreCase) || 
                name.Contains("MATRIX", StringComparison.OrdinalIgnoreCase))
            {
                string mac = FormatMacAddress(args.BluetoothAddress);
                DeviceDiscovered?.Invoke(new BluetoothDeviceItem
                {
                    Name = name,
                    Address = mac,
                    RawAddress = args.BluetoothAddress
                });
            }
        };

        _watcher.Stopped += (sender, args) => ScanFinished?.Invoke();
        _watcher.Start();

        Task.Delay(5000).ContinueWith(_ =>
        {
            try { _watcher.Stop(); } catch { }
            ScanFinished?.Invoke();
        });
    }

    public static string FormatMacAddress(ulong address)
    {
        byte[] bytes = BitConverter.GetBytes(address);
        return $"{bytes[5]:X2}:{bytes[4]:X2}:{bytes[3]:X2}:{bytes[2]:X2}:{bytes[1]:X2}:{bytes[0]:X2}";
    }

    public static ulong ParseMacAddress(string mac)
    {
        string clean = mac.Replace(":", "").Replace("-", "").Trim();
        return Convert.ToUInt64(clean, 16);
    }

    public async Task<bool> ConnectAsync(string macAddress)
    {
        try
        {
            StatusChanged?.Invoke(false, $"Conectando a {macAddress}...");
            CurrentAddress = macAddress;
            ulong addr = ParseMacAddress(macAddress);

            _device = await BluetoothLEDevice.FromBluetoothAddressAsync(addr);
            if (_device == null)
            {
                StatusChanged?.Invoke(false, "Falha ao obter dispositivo Bluetooth.");
                return false;
            }

            _device.ConnectionStatusChanged += (dev, args) =>
            {
                bool conn = dev.ConnectionStatus == BluetoothConnectionStatus.Connected;
                StatusChanged?.Invoke(conn, conn ? $"Conectado a {CurrentAddress}" : "Desconectado");
            };

            var servicesResult = await _device.GetGattServicesAsync(BluetoothCacheMode.Uncached);
            if (servicesResult.Status != GattCommunicationStatus.Success)
            {
                StatusChanged?.Invoke(false, "Falha ao consultar serviços GATT.");
                return false;
            }

            foreach (var service in servicesResult.Services)
            {
                var charsResult = await service.GetCharacteristicsAsync(BluetoothCacheMode.Uncached);
                if (charsResult.Status == GattCommunicationStatus.Success)
                {
                    foreach (var ch in charsResult.Characteristics)
                    {
                        if (ch.Uuid == WriteCharUuid)
                        {
                            _writeCharacteristic = ch;
                            break;
                        }
                    }
                }
                if (_writeCharacteristic != null) break;
            }

            if (_writeCharacteristic == null)
            {
                StatusChanged?.Invoke(false, "Característica de escrita não encontrada.");
                return false;
            }

            StatusChanged?.Invoke(true, $"Conectado a {macAddress}");
            return true;
        }
        catch (Exception ex)
        {
            StatusChanged?.Invoke(false, $"Erro de conexão: {ex.Message}");
            return false;
        }
    }

    public Task DisconnectAsync()
    {
        try
        {
            _writeCharacteristic = null;
            if (_device != null)
            {
                _device.Dispose();
                _device = null;
            }
        }
        catch { }
        finally
        {
            StatusChanged?.Invoke(false, "Desconectado");
        }
        return Task.CompletedTask;
    }

    public async Task<bool> SendDataAsync(byte[] data)
    {
        if (_writeCharacteristic == null || !IsConnected) return false;
        try
        {
            int chunkSize = 240;
            for (int i = 0; i < data.Length; i += chunkSize)
            {
                int len = Math.Min(chunkSize, data.Length - i);
                byte[] chunk = new byte[len];
                Array.Copy(data, i, chunk, 0, len);
                using var writer = new DataWriter();
                writer.WriteBytes(chunk);
                await _writeCharacteristic.WriteValueAsync(writer.DetachBuffer(), GattWriteOption.WriteWithoutResponse);
            }
            return true;
        }
        catch
        {
            return false;
        }
    }

    public async Task SetClockAsync(int style, bool date, bool h24, byte r, byte g, byte b)
    {
        _currentMode = "clock";
        _lastSentPngBytes = null;
        byte modeByte = (byte)(style | (date ? 128 : 0) | (h24 ? 64 : 0));
        byte[] packet = [8, 0, 6, 1, modeByte, r, g, b];
        await SendDataAsync(packet);
    }

    public async Task SetScreenPowerAsync(bool on)
    {
        byte[] packet = [5, 0, 7, 1, (byte)(on ? 1 : 0)];
        await SendDataAsync(packet);
    }

    public async Task SetBrightnessAsync(int percent)
    {
        byte[] packet = [5, 0, 4, 128, (byte)Math.Clamp(percent, 5, 100)];
        await SendDataAsync(packet);
    }

    public async Task SetFullscreenColorAsync(byte r, byte g, byte b)
    {
        _currentMode = "color";
        _lastSentPngBytes = null;
        byte[] packet = [7, 0, 2, 2, r, g, b];
        await SendDataAsync(packet);
    }

    public async Task SetScoreboardAsync(int s1, int s2)
    {
        _currentMode = "scoreboard";
        _lastSentPngBytes = null;
        ushort count1 = (ushort)Math.Clamp(s1, 0, 999);
        ushort count2 = (ushort)Math.Clamp(s2, 0, 999);
        byte[] packet = [
            8, 0, 10, 128,
            (byte)(count1 & 0xFF), (byte)(count1 >> 8),
            (byte)(count2 & 0xFF), (byte)(count2 >> 8)
        ];
        await SendDataAsync(packet);
    }

    public async Task SyncTimeAsync()
    {
        DateTime now = DateTime.Now;
        byte[] packet = [
            11, 0, 1, 128,
            (byte)(now.Year % 100), (byte)now.Month, (byte)now.Day,
            (byte)(((int)now.DayOfWeek + 6) % 7 + 1),
            (byte)now.Hour, (byte)now.Minute, (byte)now.Second
        ];
        await SendDataAsync(packet);
    }

    public async Task ResetAsync()
    {
        byte[] p1 = [0x04, 0x00, 0x03, 0x80];
        byte[] p2 = [0x05, 0x00, 0x04, 0x80, 0x50];
        await SendDataAsync(p1);
        await Task.Delay(100);
        await SendDataAsync(p2);
    }

    public static byte[] CreatePngPayloads(byte[] pngData)
    {
        var chunks = new List<byte[]>();
        int chunkSize = 4096;
        for (int i = 0; i < pngData.Length; i += chunkSize)
        {
            int len = Math.Min(chunkSize, pngData.Length - i);
            byte[] chunk = new byte[len];
            Array.Copy(pngData, i, chunk, 0, len);
            chunks.Add(chunk);
        }

        short idkBytes = (short)(pngData.Length + chunks.Count);
        int pngLen = pngData.Length;

        using var ms = new MemoryStream();
        using var bw = new BinaryWriter(ms);

        for (int i = 0; i < chunks.Count; i++)
        {
            bw.Write(idkBytes);
            bw.Write((byte)0);
            bw.Write((byte)0);
            bw.Write((byte)(i > 0 ? 2 : 0));
            bw.Write(pngLen);
            bw.Write(chunks[i]);
        }

        return ms.ToArray();
    }

    public async Task SendPngImageAsync(byte[] pngData)
    {
        if (pngData == null || pngData.Length == 0) return;

        // Skip sending if exactly identical to prevent redundant transmission
        if (_lastSentPngBytes != null && _lastSentPngBytes.AsSpan().SequenceEqual(pngData))
        {
            return;
        }

        // Only transition mode once to completely eliminate the black screen flash/flicker!
        if (_currentMode != "image")
        {
            byte[] setModePacket = [5, 0, 4, 1, 1];
            await SendDataAsync(setModePacket);
            _currentMode = "image";
        }

        _lastSentPngBytes = pngData;
        byte[] payloads = CreatePngPayloads(pngData);
        await SendDataAsync(payloads);
    }
}
