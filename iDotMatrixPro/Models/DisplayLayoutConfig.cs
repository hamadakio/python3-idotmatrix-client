using System;
using System.IO;
using System.Text.Json;

namespace iDotMatrixPro.Models;

public class MetricItemConfig
{
    public bool Enabled { get; set; } = true;
    public int X { get; set; } = 1;
    public int Y { get; set; } = 1;
    public string ColorHex { get; set; } = "#00FFFF";
    public bool ShowBar { get; set; } = true;
    public int BarX { get; set; } = 17;
    public int BarY { get; set; } = 2;
    public int BarWidth { get; set; } = 14;
    public int BarHeight { get; set; } = 3;
    public string BarColorHex { get; set; } = "#00FF88";
}

public class ClockLayoutConfig
{
    public int StyleIndex { get; set; } = 0; // 0: Retro 3x5, 1: Big Digital, 2: Minimalist
    public int TimeX { get; set; } = 2;
    public int TimeY { get; set; } = 6;
    public string TimeColorHex { get; set; } = "#FFFFFF";
    public string ColonColorHex { get; set; } = "#00FFFF";
    public bool ShowDate { get; set; } = true;
    public int DateX { get; set; } = 4;
    public int DateY { get; set; } = 18;
    public string DateColorHex { get; set; } = "#FFCC00";
    public bool Is24Hours { get; set; } = true;
    public bool ShowSeconds { get; set; } = false;
    public string BackgroundColorHex { get; set; } = "#000000";
}

public class DisplayLayoutConfig
{
    public MetricItemConfig Cpu { get; set; } = new()
    {
        Enabled = true,
        X = 1,
        Y = 2,
        ColorHex = "#00E5FF", // Cyan
        ShowBar = true,
        BarX = 17,
        BarY = 3,
        BarWidth = 14,
        BarHeight = 3,
        BarColorHex = "#00E5FF"
    };

    public MetricItemConfig Gpu { get; set; } = new()
    {
        Enabled = true,
        X = 1,
        Y = 9,
        ColorHex = "#76FF03", // Lime/NVIDIA Green
        ShowBar = true,
        BarX = 17,
        BarY = 10,
        BarWidth = 14,
        BarHeight = 3,
        BarColorHex = "#76FF03"
    };

    public MetricItemConfig Ram { get; set; } = new()
    {
        Enabled = true,
        X = 1,
        Y = 16,
        ColorHex = "#FFD600", // Yellow
        ShowBar = true,
        BarX = 17,
        BarY = 17,
        BarWidth = 14,
        BarHeight = 3,
        BarColorHex = "#FFD600"
    };

    public MetricItemConfig Temp { get; set; } = new()
    {
        Enabled = true,
        X = 1,
        Y = 24,
        ColorHex = "#FF3D00", // Orange-Red
        ShowBar = true,
        BarX = 17,
        BarY = 25,
        BarWidth = 14,
        BarHeight = 3,
        BarColorHex = "#FF3D00"
    };

    public ClockLayoutConfig Clock { get; set; } = new();

    public int UpdateIntervalSeconds { get; set; } = 2;
    public string BackgroundColorHex { get; set; } = "#000000";
    public string LastMacAddress { get; set; } = "";
    public bool AutoConnect { get; set; } = true;
    public bool MinimizeToTray { get; set; } = true;

    private static readonly string ConfigPath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "iDotMatrixPro",
        "layout_config.json"
    );

    public static DisplayLayoutConfig Load()
    {
        try
        {
            if (File.Exists(ConfigPath))
            {
                string json = File.ReadAllText(ConfigPath);
                var config = JsonSerializer.Deserialize<DisplayLayoutConfig>(json);
                if (config != null) return config;
            }
        }
        catch { }

        return new DisplayLayoutConfig();
    }

    public void Save()
    {
        try
        {
            string dir = Path.GetDirectoryName(ConfigPath)!;
            if (!Directory.Exists(dir))
            {
                Directory.CreateDirectory(dir);
            }
            string json = JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(ConfigPath, json);
        }
        catch { }
    }
}
