using System.Diagnostics;
using System.Drawing;
using System.Net.Http;
using System.Windows.Forms;

namespace CortexDebuggerLauncher;

internal static class Program
{
    [STAThread]
    private static int Main(string[] args)
    {
        // Native, headless release integrity self-test. No browser or UI.
        if (args.Contains("--self-test"))
        {
            var root = AppContext.BaseDirectory;
            return File.Exists(Path.Combine(root, "start.ps1"))
                && File.Exists(Path.Combine(root, "apps", "web", "dist", "index.html"))
                ? 0 : 2;
        }
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new CortexWindow());
        return 0;
    }
}

internal sealed class CortexWindow : Form
{
    private readonly Label status;
    private readonly Button start;
    private readonly Button stop;
    private readonly Button open;
    private readonly HttpClient http = new() { Timeout = TimeSpan.FromSeconds(4) };
    private Process? process;
    private readonly CancellationTokenSource closed = new();

    public CortexWindow()
    {
        Text = "Cortex Debugger";
        ClientSize = new Size(550, 290);
        MinimumSize = new Size(480, 290);
        BackColor = Color.FromArgb(16, 23, 35);
        ForeColor = Color.FromArgb(235, 241, 251);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;

        var title = new Label
        {
            Text = "Cortex Debugger",
            Font = new Font("Segoe UI", 23, FontStyle.Bold),
            ForeColor = ForeColor,
            AutoSize = true,
            Location = new Point(30, 25)
        };
        var subtitle = new Label
        {
            Text = "Local-first AI model analysis  ·  v0.9.0-rc1",
            Font = new Font("Segoe UI", 10),
            ForeColor = Color.FromArgb(151, 168, 194),
            AutoSize = true,
            Location = new Point(32, 82)
        };
        status = new Label
        {
            Text = "Ready to start · localhost only",
            Font = new Font("Segoe UI", 10),
            ForeColor = Color.FromArgb(143, 214, 197),
            AutoSize = true,
            Location = new Point(32, 133)
        };
        start = CreateButton("Start Cortex", 32, 190, 155, Color.FromArgb(61, 141, 232));
        stop = CreateButton("Stop", 197, 190, 110, Color.FromArgb(64, 75, 91));
        open = CreateButton("Open browser", 317, 190, 180, Color.FromArgb(64, 75, 91));
        stop.Enabled = false;
        open.Enabled = false;
        start.Click += async (_, _) => await StartAsync();
        stop.Click += (_, _) => StopWorker();
        open.Click += (_, _) => OpenBrowser();
        Controls.AddRange(new Control[] { title, subtitle, status, start, stop, open });
        FormClosing += (_, _) => { closed.Cancel(); StopWorker(); http.Dispose(); };
    }

    private static Button CreateButton(string text, int x, int y, int w, Color background)
    {
        return new Button
        {
            Text = text,
            Size = new Size(w, 44),
            Location = new Point(x, y),
            BackColor = background,
            ForeColor = Color.White,
            FlatStyle = FlatStyle.Flat,
            Font = new Font("Segoe UI", 10, FontStyle.Bold),
            TabStop = true
        };
    }

    private async Task StartAsync()
    {
        if (process is { HasExited: false }) return;
        string script = Path.Combine(AppContext.BaseDirectory, "start.ps1");
        if (!File.Exists(script))
        {
            MessageBox.Show("Missing start.ps1. Extract the complete Windows ZIP.",
                "Cortex Debugger", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        start.Enabled = false;
        stop.Enabled = true;
        status.Text = "Installing local dependencies / starting model API…";
        try
        {
            process = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = "powershell.exe",
                    Arguments = "-NoProfile -ExecutionPolicy Bypass -File \"" + script + "\"",
                    WorkingDirectory = AppContext.BaseDirectory,
                    CreateNoWindow = true,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                },
                EnableRaisingEvents = true
            };
            process.Start();
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            for (int i = 0; i < 180 && !closed.IsCancellationRequested; i++)
            {
                if (process.HasExited)
                {
                    status.Text = "Startup failed. Check Python 3.11 and internet access.";
                    return;
                }
                try
                {
                    using var response = await http.GetAsync(
                        "http://127.0.0.1:8000/api/v1/health", closed.Token);
                    if (response.IsSuccessStatusCode)
                    {
                        status.Text = "Running locally · http://127.0.0.1:8000";
                        open.Enabled = true;
                        OpenBrowser();
                        return;
                    }
                }
                catch (HttpRequestException) { }
                catch (TaskCanceledException) when (!closed.IsCancellationRequested) { }
                await Task.Delay(2000, closed.Token);
            }
            status.Text = "Startup timed out. Stop and check dependencies.";
        }
        catch (OperationCanceledException) when (closed.IsCancellationRequested) { }
        catch (Exception ex)
        {
            status.Text = "Cannot start Cortex Debugger.";
            MessageBox.Show(ex.Message, "Launch error",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        finally
        {
            if (open.Enabled == false) start.Enabled = true;
        }
    }

    private static void OpenBrowser()
    {
        Process.Start(new ProcessStartInfo
        {
            FileName = "http://127.0.0.1:8000/",
            UseShellExecute = true
        });
    }

    private void StopWorker()
    {
        try
        {
            if (process is { HasExited: false })
                process.Kill(entireProcessTree: true);
        }
        catch (InvalidOperationException) { }
        catch (System.ComponentModel.Win32Exception) { }
        finally
        {
            process?.Dispose();
            process = null;
            open.Enabled = false;
            stop.Enabled = false;
            start.Enabled = true;
            status.Text = "Stopped. Local model process ended.";
        }
    }
}
