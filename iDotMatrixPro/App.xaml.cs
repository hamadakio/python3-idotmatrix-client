using System;
using System.IO;
using System.Windows;

namespace iDotMatrixPro;

public partial class App : System.Windows.Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        // Keep app running in background even when window is hidden/minimized to system tray
        ShutdownMode = ShutdownMode.OnExplicitShutdown;

        AppDomain.CurrentDomain.UnhandledException += (s, args) =>
        {
            File.WriteAllText("crash.log", args.ExceptionObject.ToString());
        };

        DispatcherUnhandledException += (s, args) =>
        {
            File.WriteAllText("crash_dispatcher.log", args.Exception.ToString());
            System.Windows.MessageBox.Show(args.Exception.ToString(), "Erro iDotMatrix Pro", MessageBoxButton.OK, MessageBoxImage.Error);
            args.Handled = true;
        };

        try
        {
            var mainWindow = new MainWindow();
            MainWindow = mainWindow;
            mainWindow.Show();
        }
        catch (Exception ex)
        {
            File.WriteAllText("startup_error.log", ex.ToString());
            System.Windows.MessageBox.Show(ex.ToString(), "Erro de Inicialização");
        }
    }
}
