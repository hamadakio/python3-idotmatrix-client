using System;
using System.Drawing;
using System.IO;
using System.Windows;
using System.Windows.Forms;
using Application = System.Windows.Application;

namespace iDotMatrixPro.Services;

public class TrayManager : IDisposable
{
    private readonly NotifyIcon _notifyIcon;
    private readonly Window _mainWindow;
    private readonly BluetoothManager _bluetoothManager;

    public bool IsScreenOn { get; private set; } = true;

    public TrayManager(Window mainWindow, BluetoothManager bluetoothManager)
    {
        _mainWindow = mainWindow;
        _bluetoothManager = bluetoothManager;

        _notifyIcon = new NotifyIcon
        {
            Text = "iDotMatrix Pro - Pixel Control",
            Visible = true
        };

        // Load Icon
        try
        {
            string iconPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "idmc.ico");
            if (File.Exists(iconPath))
            {
                _notifyIcon.Icon = new Icon(iconPath);
            }
            else
            {
                _notifyIcon.Icon = SystemIcons.Application;
            }
        }
        catch
        {
            _notifyIcon.Icon = SystemIcons.Application;
        }

        // Context Menu
        var contextMenu = new ContextMenuStrip();

        var openItem = new ToolStripMenuItem("Abrir Painel iDotMatrix Pro", null, (s, e) => RestoreWindow());
        openItem.Font = new Font(openItem.Font, System.Drawing.FontStyle.Bold);
        contextMenu.Items.Add(openItem);

        contextMenu.Items.Add(new ToolStripSeparator());

        var togglePowerItem = new ToolStripMenuItem("Ligar / Desligar Display", null, async (s, e) =>
        {
            if (_bluetoothManager.IsConnected)
            {
                IsScreenOn = !IsScreenOn;
                await _bluetoothManager.SetScreenPowerAsync(IsScreenOn);
            }
        });
        contextMenu.Items.Add(togglePowerItem);

        var syncTimeItem = new ToolStripMenuItem("Sincronizar Relógio", null, async (s, e) =>
        {
            if (_bluetoothManager.IsConnected)
            {
                await _bluetoothManager.SyncTimeAsync();
            }
        });
        contextMenu.Items.Add(syncTimeItem);

        contextMenu.Items.Add(new ToolStripSeparator());

        var exitItem = new ToolStripMenuItem("Sair do Programa", null, (s, e) =>
        {
            _notifyIcon.Visible = false;
            Application.Current.Shutdown();
        });
        contextMenu.Items.Add(exitItem);

        _notifyIcon.ContextMenuStrip = contextMenu;
        _notifyIcon.DoubleClick += (s, e) => RestoreWindow();
    }

    public void ShowNotification(string title, string text, ToolTipIcon icon = ToolTipIcon.Info)
    {
        _notifyIcon.ShowBalloonTip(3000, title, text, icon);
    }

    public void RestoreWindow()
    {
        _mainWindow.Show();
        _mainWindow.WindowState = WindowState.Normal;
        _mainWindow.Activate();
    }

    public void MinimizeToTray()
    {
        _mainWindow.Hide();
    }

    public void Dispose()
    {
        _notifyIcon.Visible = false;
        _notifyIcon.Dispose();
    }
}
