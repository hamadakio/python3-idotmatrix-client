using System;
using System.Diagnostics;
using System.IO;
using Microsoft.Win32;

namespace iDotMatrixPro.Services;

public static class StartupHelper
{
    private const string AppName = "iDotMatrixPro";
    private const string RegistryKeyPath = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Run";

    /// <summary>
    /// Checks if the application is currently registered to start with Windows.
    /// </summary>
    public static bool IsStartupEnabled()
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(RegistryKeyPath, false);
            return key?.GetValue(AppName) != null;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Enables or disables automatic startup with Windows via the CurrentUser registry key.
    /// </summary>
    public static bool SetStartup(bool enable, bool startMinimized = false)
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(RegistryKeyPath, true);
            if (key == null) return false;

            if (enable)
            {
                string? exePath = Environment.ProcessPath;
                if (string.IsNullOrEmpty(exePath) || !File.Exists(exePath))
                {
                    exePath = Path.Combine(AppContext.BaseDirectory, "iDotMatrixPro.exe");
                }

                if (File.Exists(exePath))
                {
                    string command = startMinimized ? $"\"{exePath}\" --minimized" : $"\"{exePath}\"";
                    key.SetValue(AppName, command);
                    return true;
                }
                return false;
            }
            else
            {
                key.DeleteValue(AppName, false);
                return true;
            }
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Failed to update startup registry: {ex.Message}");
            return false;
        }
    }
}
