using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Shapes;
using System.Windows.Threading;
using iDotMatrixPro.Models;
using iDotMatrixPro.Services;
using Point = System.Windows.Point;
using MouseEventArgs = System.Windows.Input.MouseEventArgs;
using Rectangle = System.Windows.Shapes.Rectangle;
using Color = System.Windows.Media.Color;
using Brushes = System.Windows.Media.Brushes;
using Cursors = System.Windows.Input.Cursors;
using Image = System.Windows.Controls.Image;
using Button = System.Windows.Controls.Button;
using WpfAlign = System.Windows.HorizontalAlignment;

namespace iDotMatrixPro;

public partial class MainWindow : Window
{
    private readonly BluetoothManager _bluetooth = new();
    private readonly HardwareMonitorService _hardwareMonitor = new();
    private readonly MatrixRenderer _monitorRenderer = new();
    private readonly MatrixRenderer _clockRenderer = new();
    private readonly MatrixRenderer _drawingRenderer = new();
    private TrayManager? _trayManager;

    private DisplayLayoutConfig _config = DisplayLayoutConfig.Load();
    private HardwareStats _lastStats = new();

    private readonly DispatcherTimer _monitorTimer = new();
    private readonly DispatcherTimer _clockTimer = new();

    private bool _isMonitorStreaming;
    private bool _isClockStreaming;
    private bool _isScreenOn = true;
    private bool _isUpdatingUiFromConfig;
    private bool _isInitialized;

    // DIY Studio Drawing State
    private const int CellSize = 12; // 384 / 32 = 12 px per cell
    private uint _activeDrawColor = 0xFF00E5FF; // Default Cyan
    private readonly Rectangle[,] _canvasCells = new Rectangle[32, 32];
    private bool _isDrawingMouseDown;
    private readonly bool _startMinimized;
    private bool _autoConnectFirstFound;

    // Scoreboard
    private int _score1 = 0;
    private int _score2 = 0;

    public MainWindow(bool startMinimized = false)
    {
        _startMinimized = startMinimized;
        InitializeComponent();
        Loaded += MainWindow_Loaded;
        Closing += MainWindow_Closing;
    }

    private void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        _trayManager = new TrayManager(this, _bluetooth);

        // Setup Bluetooth Events
        _bluetooth.StatusChanged += (connected, msg) => Dispatcher.Invoke(() =>
        {
            StatusDot.Fill = connected ? new SolidColorBrush(Color.FromRgb(0x00, 0xE6, 0x76)) : new SolidColorBrush(Color.FromRgb(0xFF, 0x17, 0x44));
            StatusText.Text = connected ? "Conectado" : "Desconectado";
            ConnectBtn.Content = connected ? "Desconectar" : "Conectar";
            ConnectBtn.Background = connected ? new SolidColorBrush(Color.FromRgb(0xFF, 0x52, 0x52)) : new SolidColorBrush(Color.FromRgb(0x00, 0xE5, 0xFF));
            Log(msg);

            if (connected)
            {
                _ = ExecuteOnConnectActionAsync();
            }
        });

        _bluetooth.DeviceDiscovered += (item) => Dispatcher.Invoke(() =>
        {
            if (!DeviceComboBox.Items.Contains(item.Address))
            {
                DeviceComboBox.Items.Add(item.Address);
                if (DeviceComboBox.SelectedIndex < 0)
                {
                    DeviceComboBox.SelectedIndex = 0;
                }
            }

            // Auto-connect to first found device if requested
            if (_autoConnectFirstFound && !_bluetooth.IsConnected)
            {
                _autoConnectFirstFound = false;
                DeviceComboBox.Text = item.Address;
                _config.LastMacAddress = item.Address;
                _config.Save();
                Log($"Auto-conexão: conectando automaticamente a {item.Name} ({item.Address})...");
                _ = _bluetooth.ConnectAsync(item.Address);
            }
        });

        _bluetooth.ScanFinished += () => Dispatcher.Invoke(() =>
        {
            ScanBtn.IsEnabled = true;
            ScanBtn.Content = "Escanear";
            Log("Busca por dispositivos BLE concluída.");
        });

        // Initialize UI from Saved Config
        LoadConfigIntoUi();
        LoadSettingsIntoUi();

        // Initialize DIY Canvas & Palette
        InitializeDiyCanvas();
        InitializePalette();

        // Initialize Preset Gallery
        PopulatePresets();

        // Setup Timers
        _monitorTimer.Interval = TimeSpan.FromSeconds(_config.UpdateIntervalSeconds);
        _monitorTimer.Tick += MonitorTimer_Tick;

        _clockTimer.Interval = TimeSpan.FromSeconds(1);
        _clockTimer.Tick += ClockTimer_Tick;

        // Start initial preview updates
        _ = UpdateMonitorPreviewAsync();
        UpdateClockPreview();

        // Auto-connect / Auto-scan logic on startup
        if (_config.AutoScanAndConnectOnStartup)
        {
            if (!string.IsNullOrWhiteSpace(_config.LastMacAddress))
            {
                DeviceComboBox.Text = _config.LastMacAddress;
                Log($"Auto-conexão: conectando ao display salvo ({_config.LastMacAddress})...");
                _ = _bluetooth.ConnectAsync(_config.LastMacAddress);
            }
            else
            {
                Log("Auto-conexão: buscando displays iDotMatrix próximos...");
                _autoConnectFirstFound = true;
                ScanBtn_Click(this, new RoutedEventArgs());
            }
        }

        // Handle initial minimized state
        if (_startMinimized || (_config.StartMinimizedToTray && _startMinimized))
        {
            Hide();
            _trayManager?.ShowNotification("iDotMatrix Pro", "Iniciado silenciosamente na bandeja do sistema.");
        }

        _isInitialized = true;
    }

    private void MainWindow_Closing(object? sender, CancelEventArgs e)
    {
        if (_config.MinimizeToTray)
        {
            e.Cancel = true;
            _trayManager?.MinimizeToTray();
            _trayManager?.ShowNotification("iDotMatrix Pro", "O aplicativo continua rodando na bandeja do sistema.");
        }
        else
        {
            _trayManager?.Dispose();
        }
    }

    private void Log(string message)
    {
        FooterLogText.Text = $"{DateTime.Now:HH:mm:ss} :: {message}";
    }

    #region Config & UI Sync

    private void LoadConfigIntoUi()
    {
        _isUpdatingUiFromConfig = true;

        // Monitor Interval
        MonitorIntervalSlider.Value = _config.UpdateIntervalSeconds;
        MonitorIntervalLabel.Text = $"{_config.UpdateIntervalSeconds}s";

        // CPU
        CpuEnabledCheck.IsChecked = _config.Cpu.Enabled;
        CpuXSlider.Value = _config.Cpu.X;
        CpuYSlider.Value = _config.Cpu.Y;
        CpuColorText.Text = _config.Cpu.ColorHex;
        CpuBarCheck.IsChecked = _config.Cpu.ShowBar;
        CpuBarXSlider.Value = _config.Cpu.BarX;
        CpuBarYSlider.Value = _config.Cpu.BarY;

        // GPU
        GpuEnabledCheck.IsChecked = _config.Gpu.Enabled;
        GpuXSlider.Value = _config.Gpu.X;
        GpuYSlider.Value = _config.Gpu.Y;
        GpuColorText.Text = _config.Gpu.ColorHex;
        GpuBarCheck.IsChecked = _config.Gpu.ShowBar;
        GpuBarXSlider.Value = _config.Gpu.BarX;
        GpuBarYSlider.Value = _config.Gpu.BarY;

        // RAM
        RamEnabledCheck.IsChecked = _config.Ram.Enabled;
        RamXSlider.Value = _config.Ram.X;
        RamYSlider.Value = _config.Ram.Y;
        RamColorText.Text = _config.Ram.ColorHex;
        RamBarCheck.IsChecked = _config.Ram.ShowBar;
        RamBarXSlider.Value = _config.Ram.BarX;
        RamBarYSlider.Value = _config.Ram.BarY;

        // Temp
        TempEnabledCheck.IsChecked = _config.Temp.Enabled;
        TempXSlider.Value = _config.Temp.X;
        TempYSlider.Value = _config.Temp.Y;
        TempColorText.Text = _config.Temp.ColorHex;
        TempBarCheck.IsChecked = _config.Temp.ShowBar;
        TempBarXSlider.Value = _config.Temp.BarX;
        TempBarYSlider.Value = _config.Temp.BarY;

        // Clock
        ClockFontRetroRadio.IsChecked = _config.Clock.StyleIndex == 0;
        ClockFontBigRadio.IsChecked = _config.Clock.StyleIndex == 1;
        Clock24hCheck.IsChecked = _config.Clock.Is24Hours;
        ClockSecondsCheck.IsChecked = _config.Clock.ShowSeconds;
        ClockDateCheck.IsChecked = _config.Clock.ShowDate;
        ClockTimeXSlider.Value = _config.Clock.TimeX;
        ClockTimeYSlider.Value = _config.Clock.TimeY;
        ClockDateXSlider.Value = _config.Clock.DateX;
        ClockDateYSlider.Value = _config.Clock.DateY;
        ClockTimeColorText.Text = _config.Clock.TimeColorHex;
        ClockColonColorText.Text = _config.Clock.ColonColorHex;
        ClockDateColorText.Text = _config.Clock.DateColorHex;

        _isUpdatingUiFromConfig = false;
    }

    private void SaveUiIntoConfig()
    {
        if (!_isInitialized || _isUpdatingUiFromConfig) return;

        // Interval
        _config.UpdateIntervalSeconds = (int)MonitorIntervalSlider.Value;

        // CPU
        _config.Cpu.Enabled = CpuEnabledCheck.IsChecked ?? true;
        _config.Cpu.X = (int)CpuXSlider.Value;
        _config.Cpu.Y = (int)CpuYSlider.Value;
        _config.Cpu.ColorHex = CpuColorText.Text.Trim();
        _config.Cpu.ShowBar = CpuBarCheck.IsChecked ?? true;
        _config.Cpu.BarX = (int)CpuBarXSlider.Value;
        _config.Cpu.BarY = (int)CpuBarYSlider.Value;

        // GPU
        _config.Gpu.Enabled = GpuEnabledCheck.IsChecked ?? true;
        _config.Gpu.X = (int)GpuXSlider.Value;
        _config.Gpu.Y = (int)GpuYSlider.Value;
        _config.Gpu.ColorHex = GpuColorText.Text.Trim();
        _config.Gpu.ShowBar = GpuBarCheck.IsChecked ?? true;
        _config.Gpu.BarX = (int)GpuBarXSlider.Value;
        _config.Gpu.BarY = (int)GpuBarYSlider.Value;

        // RAM
        _config.Ram.Enabled = RamEnabledCheck.IsChecked ?? true;
        _config.Ram.X = (int)RamXSlider.Value;
        _config.Ram.Y = (int)RamYSlider.Value;
        _config.Ram.ColorHex = RamColorText.Text.Trim();
        _config.Ram.ShowBar = RamBarCheck.IsChecked ?? true;
        _config.Ram.BarX = (int)RamBarXSlider.Value;
        _config.Ram.BarY = (int)RamBarYSlider.Value;

        // Temp
        _config.Temp.Enabled = TempEnabledCheck.IsChecked ?? true;
        _config.Temp.X = (int)TempXSlider.Value;
        _config.Temp.Y = (int)TempYSlider.Value;
        _config.Temp.ColorHex = TempColorText.Text.Trim();
        _config.Temp.ShowBar = TempBarCheck.IsChecked ?? true;
        _config.Temp.BarX = (int)TempBarXSlider.Value;
        _config.Temp.BarY = (int)TempBarYSlider.Value;

        // Clock
        _config.Clock.StyleIndex = ClockFontBigRadio.IsChecked == true ? 1 : 0;
        _config.Clock.Is24Hours = Clock24hCheck.IsChecked ?? true;
        _config.Clock.ShowSeconds = ClockSecondsCheck.IsChecked ?? false;
        _config.Clock.ShowDate = ClockDateCheck.IsChecked ?? true;
        _config.Clock.TimeX = (int)ClockTimeXSlider.Value;
        _config.Clock.TimeY = (int)ClockTimeYSlider.Value;
        _config.Clock.DateX = (int)ClockDateXSlider.Value;
        _config.Clock.DateY = (int)ClockDateYSlider.Value;
        _config.Clock.TimeColorHex = ClockTimeColorText.Text.Trim();
        _config.Clock.ColonColorHex = ClockColonColorText.Text.Trim();
        _config.Clock.DateColorHex = ClockDateColorText.Text.Trim();
    }

    private void LayoutSettingChanged(object sender, RoutedEventArgs e)
    {
        if (!_isInitialized || _isUpdatingUiFromConfig) return;
        SaveUiIntoConfig();
        RenderMonitorPreview();
    }

    private void ClockSettingChanged(object sender, RoutedEventArgs e)
    {
        if (!_isInitialized || _isUpdatingUiFromConfig) return;
        SaveUiIntoConfig();
        UpdateClockPreview();
    }

    private void MonitorIntervalSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
    {
        if (!_isInitialized || _isUpdatingUiFromConfig) return;
        int val = (int)e.NewValue;
        if (MonitorIntervalLabel != null)
        {
            MonitorIntervalLabel.Text = $"{val}s";
        }
        _config.UpdateIntervalSeconds = val;
        _monitorTimer.Interval = TimeSpan.FromSeconds(val);
    }

    private void SaveLayout_Click(object sender, RoutedEventArgs e)
    {
        SaveUiIntoConfig();
        _config.Save();
        Log("Layout salvo com sucesso!");
    }

    private void ResetLayout_Click(object sender, RoutedEventArgs e)
    {
        _config = new DisplayLayoutConfig();
        LoadConfigIntoUi();
        RenderMonitorPreview();
        Log("Layout restaurado para os padrões de fábrica.");
    }

    private void SetColorPreset_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is string tag)
        {
            string[] parts = tag.Split(':');
            if (parts.Length == 2)
            {
                string target = parts[0];
                string color = parts[1];
                if (target == "Cpu") CpuColorText.Text = color;
                else if (target == "Gpu") GpuColorText.Text = color;
                else if (target == "Ram") RamColorText.Text = color;
                else if (target == "Temp") TempColorText.Text = color;
            }
        }
    }

    private void SetClockColor_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is string tag)
        {
            string[] parts = tag.Split(':');
            if (parts.Length == 2)
            {
                string target = parts[0];
                string color = parts[1];
                if (target == "Time") ClockTimeColorText.Text = color;
                else if (target == "Colon") ClockColonColorText.Text = color;
                else if (target == "Date") ClockDateColorText.Text = color;
            }
        }
    }

    #endregion

    #region Hardware Monitor

    private async Task UpdateMonitorPreviewAsync()
    {
        _lastStats = await _hardwareMonitor.GetAllStatsAsync();

        // Update labels
        CpuStatsLabel.Text = $"{_lastStats.CpuPercent}%";
        GpuStatsLabel.Text = $"{_lastStats.GpuPercent}%";
        RamStatsLabel.Text = $"{_lastStats.RamPercent}%";
        int dispTemp = _lastStats.GpuTemp > 0 ? _lastStats.GpuTemp : _lastStats.CpuTemp;
        TempStatsLabel.Text = $"{dispTemp}°C";

        RenderMonitorPreview();
    }

    private void RenderMonitorPreview()
    {
        _monitorRenderer.RenderHardwareStats(_lastStats, _config);
        MonitorPreviewImage.Source = _monitorRenderer.ToBitmapSource();
    }

    private async void MonitorTimer_Tick(object? sender, EventArgs e)
    {
        await UpdateMonitorPreviewAsync();

        if (_isMonitorStreaming && _bluetooth.IsConnected)
        {
            byte[] png = _monitorRenderer.ToPngBytes();
            await _bluetooth.SendPngImageAsync(png);
        }
    }

    public void StartMonitorStreaming()
    {
        _isMonitorStreaming = true;
        _isClockStreaming = false;
        _monitorTimer.Start();
        ToggleMonitorStreamBtn.Content = "⏹ Pausar Monitoramento";
        ToggleMonitorStreamBtn.Background = new SolidColorBrush(Color.FromRgb(0xFF, 0x52, 0x52));
        Log("Transmissão contínua de estatísticas do PC ativada.");
    }

    public void StopMonitorStreaming()
    {
        _isMonitorStreaming = false;
        _monitorTimer.Stop();
        ToggleMonitorStreamBtn.Content = "▶ Iniciar Monitoramento no Display";
        ToggleMonitorStreamBtn.Background = new SolidColorBrush(Color.FromRgb(0x00, 0xE5, 0xFF));
        Log("Transmissão pausada.");
    }

    private void ToggleMonitorStreamBtn_Click(object sender, RoutedEventArgs e)
    {
        if (!_isMonitorStreaming)
            StartMonitorStreaming();
        else
            StopMonitorStreaming();
    }

    #endregion

    #region Clock

    private void UpdateClockPreview()
    {
        _clockRenderer.RenderClock(DateTime.Now, _config.Clock);
        ClockPreviewImage.Source = _clockRenderer.ToBitmapSource();
    }

    private async void ClockTimer_Tick(object? sender, EventArgs e)
    {
        UpdateClockPreview();

        if (_isClockStreaming && _bluetooth.IsConnected)
        {
            byte[] png = _clockRenderer.ToPngBytes();
            await _bluetooth.SendPngImageAsync(png);
        }
    }

    public void StartClockStreaming()
    {
        _isClockStreaming = true;
        _isMonitorStreaming = false;
        _clockTimer.Start();
        ToggleClockStreamBtn.Content = "⏹ Parar Relógio Customizado";
        ToggleClockStreamBtn.Background = new SolidColorBrush(Color.FromRgb(0xFF, 0x52, 0x52));
        Log("Transmissão do relógio customizado ativada.");
    }

    public void StopClockStreaming()
    {
        _isClockStreaming = false;
        _clockTimer.Stop();
        ToggleClockStreamBtn.Content = "▶ Transmitir Relógio ao Display";
        ToggleClockStreamBtn.Background = new SolidColorBrush(Color.FromRgb(0x00, 0xE5, 0xFF));
        Log("Transmissão do relógio interrompida.");
    }

    private void ToggleClockStreamBtn_Click(object sender, RoutedEventArgs e)
    {
        if (!_isClockStreaming)
            StartClockStreaming();
        else
            StopClockStreaming();
    }

    private async Task ExecuteOnConnectActionAsync()
    {
        try
        {
            await Task.Delay(500); // Give BLE connection a moment to stabilize
            string action = _config.OnConnectAction ?? "HardwareMonitor";
            Log($"Executando rotina pós-conexão: {GetActionFriendlyName(action)}");

            switch (action)
            {
                case "HardwareMonitor":
                    StartMonitorStreaming();
                    break;

                case "Clock":
                    StartClockStreaming();
                    break;

                case "SyncTime":
                    await _bluetooth.SyncTimeAsync();
                    await _bluetooth.SetClockAsync(0, true, true, 255, 255, 255);
                    Log("Horário do hardware sincronizado e mantido.");
                    break;

                case "LastDrawing":
                    await SendDrawingToDisplayAsync();
                    break;

                case "None":
                default:
                    Log("Dispositivo conectado. Nenhuma ação automática configurada.");
                    break;
            }
        }
        catch (Exception ex)
        {
            Log($"Erro ao executar ação pós-conexão: {ex.Message}");
        }
    }

    private string GetActionFriendlyName(string action) => action switch
    {
        "HardwareMonitor" => "Monitor de Hardware do PC",
        "Clock" => "Relógio Digital Customizado",
        "SyncTime" => "Sincronização de Hora do Hardware",
        "LastDrawing" => "Envio da Última Arte DIY",
        "None" => "Nenhuma (Apenas manter conectado)",
        _ => action
    };

    private async void SyncHardwareClock_Click(object sender, RoutedEventArgs e)
    {
        if (_bluetooth.IsConnected)
        {
            await _bluetooth.SyncTimeAsync();
            await _bluetooth.SetClockAsync(0, true, true, 255, 255, 255);
            Log("Horário do hardware do display sincronizado com sucesso!");
        }
        else
        {
            Log("Conecte ao display antes de sincronizar.");
        }
    }

    #endregion

    #region DIY Pixel Art Studio

    private void InitializeDiyCanvas()
    {
        DrawingCanvas.Children.Clear();
        for (int y = 0; y < 32; y++)
        {
            for (int x = 0; x < 32; x++)
            {
                var rect = new Rectangle
                {
                    Width = CellSize,
                    Height = CellSize,
                    Fill = Brushes.Black,
                    Stroke = new SolidColorBrush(Color.FromArgb(20, 255, 255, 255)),
                    StrokeThickness = 0.5
                };
                Canvas.SetLeft(rect, x * CellSize);
                Canvas.SetTop(rect, y * CellSize);
                DrawingCanvas.Children.Add(rect);
                _canvasCells[x, y] = rect;
            }
        }
    }

    private void InitializePalette()
    {
        PalettePanel.Children.Clear();
        uint[] colors = [
            0xFF000000, 0xFFFFFFFF, 0xFFFF1744, 0xFFFF5252,
            0xFFFF6D00, 0xFFFFD600, 0xFF76FF03, 0xFF00E676,
            0xFF00E5FF, 0xFF2979FF, 0xFF651FFF, 0xFFD500F9,
            0xFFFF007F, 0xFF795548, 0xFF607D8B, 0xFF9E9E9E
        ];

        foreach (uint col in colors)
        {
            byte a = (byte)((col >> 24) & 0xFF);
            byte r = (byte)((col >> 16) & 0xFF);
            byte g = (byte)((col >> 8) & 0xFF);
            byte b = (byte)(col & 0xFF);

            var border = new Border
            {
                Width = 26,
                Height = 26,
                CornerRadius = new CornerRadius(4),
                Margin = new Thickness(3),
                Background = new SolidColorBrush(Color.FromArgb(a, r, g, b)),
                Cursor = Cursors.Hand,
                BorderBrush = new SolidColorBrush(Color.FromArgb(50, 255, 255, 255)),
                BorderThickness = new Thickness(1)
            };

            border.MouseDown += (s, e) =>
            {
                _activeDrawColor = col;
                ActiveColorHexText.Text = $"#{r:X2}{g:X2}{b:X2}";
                ActiveColorPreview.Background = border.Background;
            };

            PalettePanel.Children.Add(border);
        }
    }

    private void ActiveColorHexText_TextChanged(object sender, TextChangedEventArgs e)
    {
        uint col = MatrixRenderer.ParseHexColor(ActiveColorHexText.Text, 0xFF00E5FF);
        _activeDrawColor = col;
        byte a = (byte)((col >> 24) & 0xFF);
        byte r = (byte)((col >> 16) & 0xFF);
        byte g = (byte)((col >> 8) & 0xFF);
        byte b = (byte)(col & 0xFF);
        ActiveColorPreview.Background = new SolidColorBrush(Color.FromArgb(a, r, g, b));
    }

    private void DrawingCanvas_MouseDown(object sender, MouseButtonEventArgs e)
    {
        if (e.LeftButton == MouseButtonState.Pressed)
        {
            _isDrawingMouseDown = true;
            Point pt = e.GetPosition(DrawingCanvas);
            ApplyDrawingTool(pt);
        }
    }

    private void DrawingCanvas_MouseMove(object sender, MouseEventArgs e)
    {
        if (_isDrawingMouseDown && e.LeftButton == MouseButtonState.Pressed)
        {
            Point pt = e.GetPosition(DrawingCanvas);
            ApplyDrawingTool(pt);
        }
        else
        {
            _isDrawingMouseDown = false;
        }
    }

    private void ApplyDrawingTool(Point pt)
    {
        int cellX = (int)(pt.X / CellSize);
        int cellY = (int)(pt.Y / CellSize);
        if (cellX < 0 || cellX >= 32 || cellY < 0 || cellY >= 32) return;

        if (ToolPencilRadio.IsChecked == true)
        {
            SetDiyPixel(cellX, cellY, _activeDrawColor);
        }
        else if (ToolEraserRadio.IsChecked == true)
        {
            SetDiyPixel(cellX, cellY, 0xFF000000);
        }
        else if (ToolFillRadio.IsChecked == true)
        {
            FloodFill(cellX, cellY, _drawingRenderer.GetPixel(cellX, cellY), _activeDrawColor);
        }
    }

    private void SetDiyPixel(int x, int y, uint col)
    {
        _drawingRenderer.SetPixel(x, y, col);
        byte a = (byte)((col >> 24) & 0xFF);
        byte r = (byte)((col >> 16) & 0xFF);
        byte g = (byte)((col >> 8) & 0xFF);
        byte b = (byte)(col & 0xFF);
        _canvasCells[x, y].Fill = new SolidColorBrush(Color.FromArgb(a, r, g, b));
    }

    private void FloodFill(int startX, int startY, uint targetCol, uint replacementCol)
    {
        if (targetCol == replacementCol) return;
        var queue = new Queue<(int, int)>();
        queue.Enqueue((startX, startY));

        while (queue.Count > 0)
        {
            var (cx, cy) = queue.Dequeue();
            if (cx < 0 || cx >= 32 || cy < 0 || cy >= 32) continue;
            if (_drawingRenderer.GetPixel(cx, cy) != targetCol) continue;

            SetDiyPixel(cx, cy, replacementCol);
            queue.Enqueue((cx + 1, cy));
            queue.Enqueue((cx - 1, cy));
            queue.Enqueue((cx, cy + 1));
            queue.Enqueue((cx, cy - 1));
        }
    }

    private void ClearDrawingCanvas_Click(object sender, RoutedEventArgs e)
    {
        _drawingRenderer.Clear(0xFF000000);
        for (int y = 0; y < 32; y++)
        {
            for (int x = 0; x < 32; x++)
            {
                _canvasCells[x, y].Fill = Brushes.Black;
            }
        }
        Log("Tela de desenho limpa.");
    }

    public async Task SendDrawingToDisplayAsync()
    {
        if (_bluetooth.IsConnected)
        {
            byte[] png = _drawingRenderer.ToPngBytes();
            await _bluetooth.SendPngImageAsync(png);
            Log("Arte DIY enviada ao display com sucesso!");
        }
        else
        {
            Log("Conecte ao display antes de enviar.");
        }
    }

    private async void SendDrawingToDisplay_Click(object sender, RoutedEventArgs e)
    {
        await SendDrawingToDisplayAsync();
    }

    public void LoadPixelsIntoDiyCanvas(uint[,] pixels)
    {
        for (int y = 0; y < 32; y++)
        {
            for (int x = 0; x < 32; x++)
            {
                SetDiyPixel(x, y, pixels[x, y]);
            }
        }
    }

    #endregion

    #region Preset Gallery

    private void PopulatePresets()
    {
        PresetWrapPanel.Children.Clear();
        var presets = PresetGallery.GetPresets();

        foreach (var preset in presets)
        {
            var card = new Border
            {
                Width = 220,
                Margin = new Thickness(10),
                Background = new SolidColorBrush(Color.FromRgb(0x1E, 0x1E, 0x2C)),
                CornerRadius = new CornerRadius(10),
                BorderBrush = new SolidColorBrush(Color.FromRgb(0x2E, 0x2E, 0x44)),
                BorderThickness = new Thickness(1),
                Padding = new Thickness(14)
            };

            var sp = new StackPanel();

            // Preset miniature preview image
            var miniRenderer = new MatrixRenderer();
            for (int y = 0; y < 32; y++)
            {
                for (int x = 0; x < 32; x++)
                {
                    miniRenderer.SetPixel(x, y, preset.Pixels[x, y]);
                }
            }

            var img = new Image
            {
                Width = 120,
                Height = 120,
                Source = miniRenderer.ToBitmapSource(),
                Margin = new Thickness(0, 0, 0, 10),
                HorizontalAlignment = WpfAlign.Center
            };
            RenderOptions.SetBitmapScalingMode(img, BitmapScalingMode.NearestNeighbor);
            sp.Children.Add(img);

            // Title & Category
            var title = new TextBlock
            {
                Text = preset.Name,
                FontSize = 13,
                FontWeight = FontWeights.Bold,
                Foreground = Brushes.White,
                HorizontalAlignment = WpfAlign.Center
            };
            sp.Children.Add(title);

            var cat = new TextBlock
            {
                Text = preset.Category,
                FontSize = 10,
                Foreground = new SolidColorBrush(Color.FromRgb(0x88, 0x88, 0x99)),
                HorizontalAlignment = WpfAlign.Center,
                Margin = new Thickness(0, 2, 0, 10)
            };
            sp.Children.Add(cat);

            // Action: Project to display
            var projBtn = new Button
            {
                Content = "🚀 Projetar no Display",
                Height = 32,
                Background = new SolidColorBrush(Color.FromRgb(0x00, 0xE5, 0xFF)),
                Foreground = new SolidColorBrush(Color.FromRgb(0x0A, 0x0A, 0x10)),
                FontWeight = FontWeights.Bold,
                FontSize = 11,
                Margin = new Thickness(0, 0, 0, 6)
            };
            projBtn.Click += async (s, e) =>
            {
                if (_bluetooth.IsConnected)
                {
                    byte[] png = miniRenderer.ToPngBytes();
                    await _bluetooth.SendPngImageAsync(png);
                    Log($"Preset '{preset.Name}' projetado no display!");
                }
                else
                {
                    Log("Conecte ao display antes de projetar.");
                }
            };
            sp.Children.Add(projBtn);

            // Action: Edit in Studio
            var editBtn = new Button
            {
                Content = "✏️ Editar no Estúdio",
                Height = 30,
                Style = (Style)FindResource("MaterialDesignOutlinedButton"),
                BorderBrush = new SolidColorBrush(Color.FromRgb(0x55, 0x55, 0x66)),
                Foreground = new SolidColorBrush(Color.FromRgb(0xAA, 0xAA, 0xAA)),
                FontSize = 11
            };
            editBtn.Click += (s, e) =>
            {
                LoadPixelsIntoDiyCanvas(preset.Pixels);
                Log($"Preset '{preset.Name}' carregado no Estúdio DIY.");
            };
            sp.Children.Add(editBtn);

            card.Child = sp;
            PresetWrapPanel.Children.Add(card);
        }
    }

    #endregion

    #region Text & Marquee

    private void SetTextColor_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is string hex)
        {
            TextColorInput.Text = hex;
        }
    }

    private async void SendTextMessage_Click(object sender, RoutedEventArgs e)
    {
        string text = TextMessageInput.Text.Trim();
        if (string.IsNullOrEmpty(text)) return;

        var textRenderer = new MatrixRenderer();
        textRenderer.Clear(0xFF000000);
        uint col = MatrixRenderer.ParseHexColor(TextColorInput.Text, 0xFF00E5FF);
        
        // Centered horizontally if short
        int textW = text.Length * 4;
        int startX = Math.Max(1, (32 - textW) / 2);
        textRenderer.DrawText3x5(text, startX, 13, col);

        if (_bluetooth.IsConnected)
        {
            byte[] png = textRenderer.ToPngBytes();
            await _bluetooth.SendPngImageAsync(png);
            Log($"Mensagem '{text}' enviada ao display!");
        }
        else
        {
            Log("Conecte ao display antes de enviar.");
        }
    }

    #endregion

    #region Scoreboard & Extras

    private void Score1Minus_Click(object sender, RoutedEventArgs e)
    {
        if (_score1 > 0) _score1--;
        Score1Label.Text = _score1.ToString();
    }

    private void Score1Plus_Click(object sender, RoutedEventArgs e)
    {
        _score1++;
        Score1Label.Text = _score1.ToString();
    }

    private void Score2Minus_Click(object sender, RoutedEventArgs e)
    {
        if (_score2 > 0) _score2--;
        Score2Label.Text = _score2.ToString();
    }

    private void Score2Plus_Click(object sender, RoutedEventArgs e)
    {
        _score2++;
        Score2Label.Text = _score2.ToString();
    }

    private async void UpdateScoreboard_Click(object sender, RoutedEventArgs e)
    {
        if (_bluetooth.IsConnected)
        {
            await _bluetooth.SetScoreboardAsync(_score1, _score2);
            Log($"Placar atualizado: {_score1} x {_score2}");
        }
        else
        {
            Log("Conecte ao display antes de atualizar o placar.");
        }
    }

    private void ResetScoreboard_Click(object sender, RoutedEventArgs e)
    {
        _score1 = 0;
        _score2 = 0;
        Score1Label.Text = "0";
        Score2Label.Text = "0";
        UpdateScoreboard_Click(sender, e);
    }

    private async void FillColor_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is string hex)
        {
            uint col = MatrixRenderer.ParseHexColor(hex);
            byte r = (byte)((col >> 16) & 0xFF);
            byte g = (byte)((col >> 8) & 0xFF);
            byte b = (byte)(col & 0xFF);

            if (_bluetooth.IsConnected)
            {
                await _bluetooth.SetFullscreenColorAsync(r, g, b);
                Log($"Cor sólida {hex} aplicada.");
            }
            else
            {
                Log("Conecte ao display antes de aplicar cor.");
            }
        }
    }

    private async void ResetDevice_Click(object sender, RoutedEventArgs e)
    {
        if (_bluetooth.IsConnected)
        {
            await _bluetooth.ResetAsync();
            Log("Comando de reset de fábrica enviado ao display.");
        }
    }

    #endregion

    #region Top Bar BLE & Tray Controls

    private void ScanBtn_Click(object sender, RoutedEventArgs e)
    {
        ScanBtn.IsEnabled = false;
        ScanBtn.Content = "Buscando...";
        DeviceComboBox.Items.Clear();
        _bluetooth.StartScan();
        Log("Buscando dispositivos iDotMatrix por BLE...");
    }

    private async void ConnectBtn_Click(object sender, RoutedEventArgs e)
    {
        if (_bluetooth.IsConnected)
        {
            await _bluetooth.DisconnectAsync();
        }
        else
        {
            string mac = DeviceComboBox.Text.Trim();
            if (string.IsNullOrEmpty(mac))
            {
                Log("Por favor, selecione ou digite o endereço MAC do dispositivo.");
                return;
            }

            _config.LastMacAddress = mac;
            _config.Save();

            bool ok = await _bluetooth.ConnectAsync(mac);
            if (ok)
            {
                Log($"Conectado com sucesso a {mac}!");
            }
        }
    }

    private async void BrightnessSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
    {
        if (_bluetooth.IsConnected)
        {
            await _bluetooth.SetBrightnessAsync((int)e.NewValue);
        }
    }

    private async void PowerBtn_Click(object sender, RoutedEventArgs e)
    {
        if (_bluetooth.IsConnected)
        {
            _isScreenOn = !_isScreenOn;
            await _bluetooth.SetScreenPowerAsync(_isScreenOn);
            PowerBtn.Content = _isScreenOn ? "Tela On" : "Tela Off";
            PowerBtn.BorderBrush = _isScreenOn ? new SolidColorBrush(Color.FromRgb(0x76, 0xFF, 0x03)) : new SolidColorBrush(Color.FromRgb(0xFF, 0x17, 0x44));
            PowerBtn.Foreground = PowerBtn.BorderBrush;
            Log(_isScreenOn ? "Display ligado." : "Display desligado.");
        }
    }

    private void MinimizeTrayBtn_Click(object sender, RoutedEventArgs e)
    {
        _trayManager?.MinimizeToTray();
        _trayManager?.ShowNotification("iDotMatrix Pro", "Minimizado para a bandeja do sistema. Clique duas vezes no ícone para restaurar.");
    }

    #endregion

    #region Settings Tab Handlers

    private void LoadSettingsIntoUi()
    {
        ConfigStartWithWindowsCheck.IsChecked = StartupHelper.IsStartupEnabled();
        ConfigStartMinimizedCheck.IsChecked = _config.StartMinimizedToTray;
        ConfigMinimizeToTrayCheck.IsChecked = _config.MinimizeToTray;
        ConfigAutoConnectCheck.IsChecked = _config.AutoScanAndConnectOnStartup;
        ConfigAutoReconnectCheck.IsChecked = _config.AutoReconnect;
        ConfigSavedMacText.Text = _config.LastMacAddress;

        // Select Action in ComboBox
        string act = _config.OnConnectAction ?? "HardwareMonitor";
        foreach (ComboBoxItem item in ConfigOnConnectActionCombo.Items)
        {
            if (item.Tag?.ToString() == act)
            {
                ConfigOnConnectActionCombo.SelectedItem = item;
                break;
            }
        }
        UpdateActionDescription();
    }

    private void ConfigSettingChanged(object sender, RoutedEventArgs e)
    {
        if (!_isInitialized || _isUpdatingUiFromConfig) return;
    }

    private void ConfigOnConnectActionCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        UpdateActionDescription();
    }

    private void UpdateActionDescription()
    {
        if (ConfigActionDescriptionText == null || ConfigOnConnectActionCombo == null) return;
        if (ConfigOnConnectActionCombo.SelectedItem is ComboBoxItem item && item.Tag is string tag)
        {
            ConfigActionDescriptionText.Text = tag switch
            {
                "None" => "O display apenas manterá a conexão Bluetooth aberta aguardando comandos manuais sem enviar nenhuma tela automática.",
                "HardwareMonitor" => "O monitoramento ao vivo de CPU, GPU, RAM e temperatura do seu PC será iniciado automaticamente na matriz LED assim que conectar.",
                "Clock" => "O relógio digital customizado configurado no estúdio será renderizado e transmitido continuamente ao display.",
                "SyncTime" => "O horário do hardware do display será sincronizado com o relógio do seu computador e o relógio embutido nativo do display será ativado.",
                "LastDrawing" => "O desenho ou pixel art atual da tela de pintura DIY será projetado no display assim que a conexão for estabelecida.",
                _ => ""
            };
        }
    }

    private void SetCurrentAsSavedMac_Click(object sender, RoutedEventArgs e)
    {
        string current = DeviceComboBox.Text.Trim();
        if (!string.IsNullOrEmpty(current))
        {
            ConfigSavedMacText.Text = current;
            _config.LastMacAddress = current;
            _config.Save();
            SettingsFeedbackText.Text = $"✓ Dispositivo {current} definido como padrão!";
            Log($"Dispositivo padrão configurado para {current}");
        }
        else
        {
            SettingsFeedbackText.Text = "⚠️ Nenhum dispositivo selecionado no topo.";
        }
    }

    private void SaveSettingsBtn_Click(object sender, RoutedEventArgs e)
    {
        bool startWithWin = ConfigStartWithWindowsCheck.IsChecked == true;
        bool startMin = ConfigStartMinimizedCheck.IsChecked == true;

        _config.StartWithWindows = startWithWin;
        _config.StartMinimizedToTray = startMin;
        _config.MinimizeToTray = ConfigMinimizeToTrayCheck.IsChecked == true;
        _config.AutoScanAndConnectOnStartup = ConfigAutoConnectCheck.IsChecked == true;
        _config.AutoReconnect = ConfigAutoReconnectCheck.IsChecked == true;
        _config.LastMacAddress = ConfigSavedMacText.Text.Trim();

        if (ConfigOnConnectActionCombo.SelectedItem is ComboBoxItem selItem && selItem.Tag is string actionTag)
        {
            _config.OnConnectAction = actionTag;
        }

        // Apply Windows Autostart in registry
        bool regOk = StartupHelper.SetStartup(startWithWin, startMin);

        _config.Save();
        SettingsFeedbackText.Text = regOk 
            ? "✓ Configurações salvas e aplicadas com sucesso!" 
            : "✓ Configurações salvas!";
        Log("Configurações gerais do programa salvas.");
    }

    private void ResetSettingsBtn_Click(object sender, RoutedEventArgs e)
    {
        ConfigStartWithWindowsCheck.IsChecked = false;
        ConfigStartMinimizedCheck.IsChecked = false;
        ConfigMinimizeToTrayCheck.IsChecked = true;
        ConfigAutoConnectCheck.IsChecked = true;
        ConfigAutoReconnectCheck.IsChecked = true;

        foreach (ComboBoxItem item in ConfigOnConnectActionCombo.Items)
        {
            if (item.Tag?.ToString() == "HardwareMonitor")
            {
                ConfigOnConnectActionCombo.SelectedItem = item;
                break;
            }
        }

        SaveSettingsBtn_Click(sender, e);
        SettingsFeedbackText.Text = "✓ Configurações restauradas para os padrões recomendados.";
    }

    #endregion
}