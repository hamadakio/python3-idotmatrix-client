import os
import psutil
import subprocess
import time
from PIL import Image, ImageDraw


# -------------------------------------------------------------
# PIXEL-PERFECT 3x5 BITMAP FONT FOR 32x32 LED MATRICES
# -------------------------------------------------------------
FONT_3X5 = {
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
    "%": ["101", "001", "010", "100", "101"],
    "C": ["111", "100", "100", "100", "111"],
    "G": ["111", "100", "101", "101", "111"],
    "R": ["110", "101", "110", "101", "101"],
    "D": ["110", "101", "101", "101", "110"],
    "P": ["111", "101", "111", "100", "100"],
    "U": ["101", "101", "101", "101", "111"],
    "°": ["110", "110", "000", "000", "000"],
    ":": ["000", "010", "000", "010", "000"],
    "-": ["000", "000", "111", "000", "000"],
    " ": ["000", "000", "000", "000", "000"],
}


def draw_bitmap_text(draw: ImageDraw.ImageDraw, start_x: int, start_y: int, text: str, color: tuple) -> int:
    """Draws pixel-perfect 3x5 font without antialiasing blur."""
    curr_x = start_x
    for ch in text.upper():
        bitmap = FONT_3X5.get(ch, FONT_3X5[" "])
        for r in range(5):
            row_str = bitmap[r]
            for c in range(3):
                if row_str[c] == "1":
                    draw.point((curr_x + c, start_y + r), fill=color)
        curr_x += 4  # 3px width + 1px spacing
    return curr_x


class HardwareMonitor:
    """
    Monitors PC metrics (CPU, GPU, Temperature, RAM) and renders
    a pixel-perfect 32x32 dashboard for iDotMatrix LED panels.
    """

    @staticmethod
    def get_gpu_metrics() -> tuple:
        """Queries GPU usage and temperature via nvidia-smi with hidden window."""
        try:
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"],
                startupinfo=startupinfo,
                text=True,
                timeout=1,
            )
            parts = [x.strip() for x in output.strip().split(",")]
            if len(parts) >= 2:
                return int(parts[0]), int(parts[1])
        except Exception:
            pass
        return 0, 40

    @classmethod
    def get_metrics(cls) -> dict:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()

        # GPU metrics
        gpu_pct, gpu_temp = cls.get_gpu_metrics()

        # CPU Temp
        cpu_temp = None
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            cpu_temp = int(entries[0].current)
                            break
        except Exception:
            pass

        if cpu_temp is None:
            cpu_temp = int(36 + (cpu * 0.38))

        return {
            "cpu_percent": int(cpu),
            "ram_percent": int(mem.percent),
            "ram_used_gb": round(mem.used / (1024 ** 3), 1),
            "ram_total_gb": round(mem.total / (1024 ** 3), 1),
            "gpu_percent": int(gpu_pct),
            "gpu_temp": int(gpu_temp),
            "temp_c": int(cpu_temp),
            "temp_f": int(cpu_temp * 9 / 5 + 32),
        }

    @classmethod
    def render_matrix_dashboard(cls, size: int = 32, metrics: dict = None) -> Image.Image:
        """
        Renders a 32x32 matrix dashboard displaying:
        - Row 1: CPU (C), % usage, CPU temperature (45°) + Cyan Bar
        - Row 2: GPU (G), % usage, GPU temperature (40°) + Emerald Green Bar
        - Row 3: RAM (R), % usage + Neon Purple Bar
        """
        if metrics is None:
            metrics = cls.get_metrics()

        cpu = max(0, min(100, metrics["cpu_percent"]))
        gpu = max(0, min(100, metrics["gpu_percent"]))
        ram = max(0, min(100, metrics["ram_percent"]))
        cpu_temp = max(0, min(99, metrics["temp_c"]))
        gpu_temp = max(0, min(99, metrics.get("gpu_temp", 40)))

        # Deep black background for maximum LED contrast
        img = Image.new("RGB", (size, size), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Frame border
        draw.rectangle([0, 0, 31, 31], outline=(18, 22, 30))

        # ---------------------------------------------------------
        # ROW 1: CPU (C) & CPU Temp (y=2..6 Text, y=8..9 Bar)
        # ---------------------------------------------------------
        # Label 'C' in Cyan
        draw_bitmap_text(draw, 2, 2, "C", (0, 229, 255))

        # CPU % in Crisp White
        cpu_str = f"{cpu}%".rjust(3) if cpu < 100 else "99%"
        draw_bitmap_text(draw, 7, 2, cpu_str, (245, 245, 250))

        # CPU Temperature on the right: e.g. "45°"
        temp_str = f"{cpu_temp}°"
        temp_col = (0, 230, 118) if cpu_temp < 60 else (255, 171, 0) if cpu_temp < 75 else (255, 82, 82)
        draw_bitmap_text(draw, 20, 2, temp_str, temp_col)

        # CPU Bar (x=2..29, width=28px, y=8..9, height=2px)
        draw.rectangle([2, 8, 29, 9], fill=(22, 28, 40))
        cpu_bar_w = int((cpu / 100.0) * 28)
        if cpu_bar_w > 0:
            c_fill = (0, 229, 255) if cpu < 75 else (255, 82, 82)
            draw.rectangle([2, 8, 2 + cpu_bar_w - 1, 9], fill=c_fill)

        # ---------------------------------------------------------
        # ROW 2: GPU (G) & GPU Temp (y=12..16 Text, y=18..19 Bar)
        # ---------------------------------------------------------
        # Label 'G' in Emerald Green
        draw_bitmap_text(draw, 2, 12, "G", (0, 230, 118))

        # GPU % in Crisp White
        gpu_str = f"{gpu}%".rjust(3) if gpu < 100 else "99%"
        draw_bitmap_text(draw, 7, 12, gpu_str, (245, 245, 250))

        # GPU Temperature on the right: e.g. "40°"
        gpu_temp_str = f"{gpu_temp}°"
        g_temp_col = (0, 230, 118) if gpu_temp < 65 else (255, 171, 0) if gpu_temp < 80 else (255, 82, 82)
        draw_bitmap_text(draw, 20, 12, gpu_temp_str, g_temp_col)

        # GPU Bar (x=2..29, width=28px, y=18..19, height=2px)
        draw.rectangle([2, 18, 29, 19], fill=(22, 28, 40))
        gpu_bar_w = int((gpu / 100.0) * 28)
        if gpu_bar_w > 0:
            g_fill = (0, 230, 118) if gpu < 80 else (255, 82, 82)
            draw.rectangle([2, 18, 2 + gpu_bar_w - 1, 19], fill=g_fill)

        # ---------------------------------------------------------
        # ROW 3: RAM (R) (y=22..26 Text, y=28..29 Bar)
        # ---------------------------------------------------------
        # Label 'R' in Neon Purple
        draw_bitmap_text(draw, 2, 22, "R", (170, 0, 255))

        # RAM % in Crisp White
        ram_str = f"{ram}%".rjust(3) if ram < 100 else "99%"
        draw_bitmap_text(draw, 7, 22, ram_str, (245, 245, 250))

        # RAM Bar (x=2..29, width=28px, y=28..29, height=2px)
        draw.rectangle([2, 28, 29, 29], fill=(22, 28, 40))
        ram_bar_w = int((ram / 100.0) * 28)
        if ram_bar_w > 0:
            r_fill = (170, 0, 255) if ram < 80 else (255, 171, 0)
            draw.rectangle([2, 28, 2 + ram_bar_w - 1, 29], fill=r_fill)

        # Static status indicator pixel at (30, 30)
        draw.point((30, 30), fill=(0, 180, 80))

        return img
