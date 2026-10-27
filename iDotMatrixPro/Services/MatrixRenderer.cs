using System;
using System.Collections.Generic;
using System.IO;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using iDotMatrixPro.Models;

namespace iDotMatrixPro.Services;

public class MatrixRenderer
{
    public const int Width = 32;
    public const int Height = 32;

    // 3x5 Pixel Font: 5 rows of 3 bits each (ushort or byte)
    private static readonly Dictionary<char, byte[]> Font3x5 = new()
    {
        { '0', [0b111, 0b101, 0b101, 0b101, 0b111] },
        { '1', [0b010, 0b110, 0b010, 0b010, 0b111] },
        { '2', [0b111, 0b001, 0b111, 0b100, 0b111] },
        { '3', [0b111, 0b001, 0b111, 0b001, 0b111] },
        { '4', [0b101, 0b101, 0b111, 0b001, 0b001] },
        { '5', [0b111, 0b100, 0b111, 0b001, 0b111] },
        { '6', [0b111, 0b100, 0b111, 0b101, 0b111] },
        { '7', [0b111, 0b001, 0b010, 0b010, 0b010] },
        { '8', [0b111, 0b101, 0b111, 0b101, 0b111] },
        { '9', [0b111, 0b101, 0b111, 0b001, 0b111] },
        { 'C', [0b111, 0b100, 0b100, 0b100, 0b111] },
        { 'P', [0b111, 0b101, 0b111, 0b100, 0b100] },
        { 'U', [0b101, 0b101, 0b101, 0b101, 0b111] },
        { 'G', [0b111, 0b100, 0b101, 0b101, 0b111] },
        { 'R', [0b111, 0b101, 0b111, 0b110, 0b101] },
        { 'A', [0b111, 0b101, 0b111, 0b101, 0b101] },
        { 'M', [0b101, 0b111, 0b101, 0b101, 0b101] },
        { 'T', [0b111, 0b010, 0b010, 0b010, 0b010] },
        { 'E', [0b111, 0b100, 0b111, 0b100, 0b111] },
        { '%', [0b101, 0b001, 0b010, 0b100, 0b101] },
        { ':', [0b000, 0b010, 0b000, 0b010, 0b000] },
        { '.', [0b000, 0b000, 0b000, 0b000, 0b010] },
        { '/', [0b001, 0b001, 0b010, 0b100, 0b100] },
        { '-', [0b000, 0b000, 0b111, 0b000, 0b000] },
        { '°', [0b110, 0b110, 0b000, 0b000, 0b000] },
        { ' ', [0b000, 0b000, 0b000, 0b000, 0b000] }
    };

    // 5x7 Big Pixel Font for Clock
    private static readonly Dictionary<char, byte[]> Font5x7 = new()
    {
        { '0', [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110] },
        { '1', [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110] },
        { '2', [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111] },
        { '3', [0b11110, 0b00001, 0b00001, 0b01110, 0b00001, 0b00001, 0b11110] },
        { '4', [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010] },
        { '5', [0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110] },
        { '6', [0b01110, 0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110] },
        { '7', [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000] },
        { '8', [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110] },
        { '9', [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00001, 0b01110] },
        { ':', [0b00000, 0b00100, 0b00000, 0b00000, 0b00100, 0b00000, 0b00000] },
        { ' ', [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000] }
    };

    public uint[,] Canvas { get; } = new uint[Width, Height];

    public void Clear(uint color = 0xFF000000)
    {
        for (int y = 0; y < Height; y++)
        {
            for (int x = 0; x < Width; x++)
            {
                Canvas[x, y] = color;
            }
        }
    }

    public void SetPixel(int x, int y, uint color)
    {
        if (x >= 0 && x < Width && y >= 0 && y < Height)
        {
            Canvas[x, y] = color;
        }
    }

    public uint GetPixel(int x, int y)
    {
        if (x >= 0 && x < Width && y >= 0 && y < Height)
        {
            return Canvas[x, y];
        }
        return 0;
    }

    public void DrawRect(int x, int y, int w, int h, uint color, bool fill = true)
    {
        for (int py = y; py < y + h; py++)
        {
            for (int px = x; px < x + w; px++)
            {
                if (fill || px == x || px == x + w - 1 || py == y || py == y + h - 1)
                {
                    SetPixel(px, py, color);
                }
            }
        }
    }

    public void DrawProgressBar(int x, int y, int width, int height, int percent, uint barColor, uint bgColor = 0xFF222222)
    {
        if (width <= 0 || height <= 0) return;
        DrawRect(x, y, width, height, bgColor, true);
        int fillWidth = (int)Math.Round((double)percent * width / 100.0);
        fillWidth = Math.Clamp(fillWidth, 0, width);
        if (fillWidth > 0)
        {
            DrawRect(x, y, fillWidth, height, barColor, true);
        }
    }

    public int DrawText3x5(string text, int startX, int startY, uint color, int spacing = 1)
    {
        int curX = startX;
        foreach (char ch in text.ToUpperInvariant())
        {
            if (Font3x5.TryGetValue(ch, out var rows))
            {
                for (int row = 0; row < 5; row++)
                {
                    byte b = rows[row];
                    for (int col = 0; col < 3; col++)
                    {
                        if ((b & (1 << (2 - col))) != 0)
                        {
                            SetPixel(curX + col, startY + row, color);
                        }
                    }
                }
                curX += 3 + spacing;
            }
            else
            {
                curX += 3 + spacing;
            }
        }
        return curX;
    }

    public int DrawText5x7(string text, int startX, int startY, uint color, int spacing = 1)
    {
        int curX = startX;
        foreach (char ch in text.ToUpperInvariant())
        {
            if (Font5x7.TryGetValue(ch, out var rows))
            {
                for (int row = 0; row < 7; row++)
                {
                    byte b = rows[row];
                    for (int col = 0; col < 5; col++)
                    {
                        if ((b & (1 << (4 - col))) != 0)
                        {
                            SetPixel(curX + col, startY + row, color);
                        }
                    }
                }
                curX += 5 + spacing;
            }
            else
            {
                curX += 5 + spacing;
            }
        }
        return curX;
    }

    public static uint ParseHexColor(string hex, uint fallback = 0xFFFFFFFF)
    {
        if (string.IsNullOrWhiteSpace(hex)) return fallback;
        string clean = hex.Trim().TrimStart('#');
        if (clean.Length == 6)
        {
            if (uint.TryParse(clean, System.Globalization.NumberStyles.HexNumber, null, out uint rgb))
            {
                return 0xFF000000 | rgb;
            }
        }
        else if (clean.Length == 8)
        {
            if (uint.TryParse(clean, System.Globalization.NumberStyles.HexNumber, null, out uint argb))
            {
                return argb;
            }
        }
        return fallback;
    }

    public void RenderHardwareStats(HardwareStats stats, DisplayLayoutConfig config)
    {
        uint bg = ParseHexColor(config.BackgroundColorHex, 0xFF000000);
        Clear(bg);

        // CPU
        if (config.Cpu.Enabled)
        {
            uint cpuColor = ParseHexColor(config.Cpu.ColorHex, 0xFF00E5FF);
            DrawText3x5("C", config.Cpu.X, config.Cpu.Y, cpuColor);
            string val = $"{stats.CpuPercent}%";
            DrawText3x5(val, config.Cpu.X + 5, config.Cpu.Y, cpuColor);

            if (config.Cpu.ShowBar)
            {
                uint barCol = ParseHexColor(config.Cpu.BarColorHex, cpuColor);
                DrawProgressBar(config.Cpu.BarX, config.Cpu.BarY, config.Cpu.BarWidth, config.Cpu.BarHeight, stats.CpuPercent, barCol);
            }
        }

        // GPU
        if (config.Gpu.Enabled)
        {
            uint gpuColor = ParseHexColor(config.Gpu.ColorHex, 0xFF76FF03);
            DrawText3x5("G", config.Gpu.X, config.Gpu.Y, gpuColor);
            string val = $"{stats.GpuPercent}%";
            DrawText3x5(val, config.Gpu.X + 5, config.Gpu.Y, gpuColor);

            if (config.Gpu.ShowBar)
            {
                uint barCol = ParseHexColor(config.Gpu.BarColorHex, gpuColor);
                DrawProgressBar(config.Gpu.BarX, config.Gpu.BarY, config.Gpu.BarWidth, config.Gpu.BarHeight, stats.GpuPercent, barCol);
            }
        }

        // RAM
        if (config.Ram.Enabled)
        {
            uint ramColor = ParseHexColor(config.Ram.ColorHex, 0xFFFFD600);
            DrawText3x5("R", config.Ram.X, config.Ram.Y, ramColor);
            string val = $"{stats.RamPercent}%";
            DrawText3x5(val, config.Ram.X + 5, config.Ram.Y, ramColor);

            if (config.Ram.ShowBar)
            {
                uint barCol = ParseHexColor(config.Ram.BarColorHex, ramColor);
                DrawProgressBar(config.Ram.BarX, config.Ram.BarY, config.Ram.BarWidth, config.Ram.BarHeight, stats.RamPercent, barCol);
            }
        }

        // TEMP
        if (config.Temp.Enabled)
        {
            uint tempColor = ParseHexColor(config.Temp.ColorHex, 0xFFFF3D00);
            DrawText3x5("T", config.Temp.X, config.Temp.Y, tempColor);
            int displayTemp = stats.GpuTemp > 0 ? stats.GpuTemp : stats.CpuTemp;
            string val = $"{displayTemp}°";
            DrawText3x5(val, config.Temp.X + 5, config.Temp.Y, tempColor);

            if (config.Temp.ShowBar)
            {
                uint barCol = ParseHexColor(config.Temp.BarColorHex, tempColor);
                DrawProgressBar(config.Temp.BarX, config.Temp.BarY, config.Temp.BarWidth, config.Temp.BarHeight, displayTemp, barCol);
            }
        }
    }

    public void RenderClock(DateTime dt, ClockLayoutConfig config)
    {
        uint bg = ParseHexColor(config.BackgroundColorHex, 0xFF000000);
        Clear(bg);

        string timeStr;
        if (config.Is24Hours)
        {
            timeStr = config.ShowSeconds ? dt.ToString("HH:mm:ss") : dt.ToString("HH:mm");
        }
        else
        {
            timeStr = config.ShowSeconds ? dt.ToString("hh:mm:ss") : dt.ToString("hh:mm");
        }

        uint timeCol = ParseHexColor(config.TimeColorHex, 0xFFFFFFFF);
        uint colonCol = ParseHexColor(config.ColonColorHex, 0xFF00E5FF);

        if (config.StyleIndex == 1) // Big 5x7 Font
        {
            int curX = config.TimeX;
            for (int i = 0; i < timeStr.Length; i++)
            {
                char c = timeStr[i];
                uint cCol = c == ':' ? colonCol : timeCol;
                curX = DrawText5x7(c.ToString(), curX, config.TimeY, cCol, 1);
            }
        }
        else // Retro 3x5 Font
        {
            int curX = config.TimeX;
            for (int i = 0; i < timeStr.Length; i++)
            {
                char c = timeStr[i];
                uint cCol = c == ':' ? colonCol : timeCol;
                curX = DrawText3x5(c.ToString(), curX, config.TimeY, cCol, 1);
            }
        }

        if (config.ShowDate)
        {
            uint dateCol = ParseHexColor(config.DateColorHex, 0xFFFFD600);
            string dateStr = dt.ToString("dd/MM");
            DrawText3x5(dateStr, config.DateX, config.DateY, dateCol, 1);
        }
    }

    public byte[] ToPngBytes()
    {
        var writeable = ToBitmapSource();
        var encoder = new PngBitmapEncoder();
        encoder.Frames.Add(BitmapFrame.Create(writeable));

        using var ms = new MemoryStream();
        encoder.Save(ms);
        return ms.ToArray();
    }

    public WriteableBitmap ToBitmapSource()
    {
        var writeable = new WriteableBitmap(Width, Height, 96, 96, PixelFormats.Bgra32, null);
        byte[] pixels = new byte[Width * Height * 4];

        for (int y = 0; y < Height; y++)
        {
            for (int x = 0; x < Width; x++)
            {
                uint col = Canvas[x, y];
                int idx = (y * Width + x) * 4;
                pixels[idx] = (byte)(col & 0xFF);         // Blue
                pixels[idx + 1] = (byte)((col >> 8) & 0xFF);  // Green
                pixels[idx + 2] = (byte)((col >> 16) & 0xFF); // Red
                pixels[idx + 3] = (byte)((col >> 24) & 0xFF); // Alpha
            }
        }

        writeable.WritePixels(new System.Windows.Int32Rect(0, 0, Width, Height), pixels, Width * 4, 0);
        writeable.Freeze(); // Freeze for high performance multi-thread rendering
        return writeable;
    }
}
