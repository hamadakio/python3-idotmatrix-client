import os
import sys
import copy
from typing import List, Tuple
from PIL import Image, ImageQt

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QSlider, QStackedWidget,
    QCheckBox, QSpinBox, QColorDialog, QFileDialog, QMessageBox, QFrame,
    QTabWidget, QScrollArea, QSplitter, QProgressBar, QButtonGroup, QRadioButton
)
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap, QImage, QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

# Core modules
from core.ble_controller import BleController
from core.hardware_monitor import HardwareMonitor
from core.weather_service import WeatherService
from core.presets import (
    CLOCK_FACES, FEED_PRESETS, SnakeGameEngine,
    render_sound_eq_frame, render_campfire_pattern, render_ocean_waves_pattern,
    create_notification_art
)

PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(PROJ_DIR, "idmc.ico")


# -------------------------------------------------------------
# MODERN DARK GLASSMORPHIC STYLESHEET
# -------------------------------------------------------------
MODERN_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #161b22;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #58a6ff;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Headers & Cards */
QFrame.Card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 12px;
}
QFrame.Card:hover {
    border-color: #58a6ff;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #30363d;
    background-color: #0d1117;
    border-radius: 8px;
    padding: 6px;
}
QTabBar::tab {
    background: #161b22;
    color: #8b949e;
    padding: 10px 18px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #21262d;
    color: #58a6ff;
    border-bottom: 2px solid #58a6ff;
}
QTabBar::tab:hover {
    color: #f0f6fc;
}

/* Buttons */
QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #30363d;
    color: #f0f6fc;
    border-color: #8b949e;
}
QPushButton:pressed {
    background-color: #161b22;
}

QPushButton.Primary {
    background-color: #1f6feb;
    color: #ffffff;
    border: 1px solid #388bfd;
}
QPushButton.Primary:hover {
    background-color: #388bfd;
}

QPushButton.Success {
    background-color: #238636;
    color: #ffffff;
    border: 1px solid #2ea043;
}
QPushButton.Success:hover {
    background-color: #2ea043;
}

QPushButton.Danger {
    background-color: #da3633;
    color: #ffffff;
    border: 1px solid #f85149;
}
QPushButton.Danger:hover {
    background-color: #f85149;
}

/* Inputs & Combos */
QLineEdit, QSpinBox, QComboBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f0f6fc;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #58a6ff;
}
QComboBox::drop-down {
    border: none;
}

/* Sliders */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #21262d;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #58a6ff;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #f0f6fc;
    width: 16px;
    height: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}
"""


# -------------------------------------------------------------
# PIXEL CANVAS WIDGET (FRAME-BY-FRAME DIY EDITOR)
# -------------------------------------------------------------
class PixelCanvasWidget(QWidget):
    pixel_changed = pyqtSignal()

    def __init__(self, grid_size=32, parent=None):
        super().__init__(parent)
        self.grid_size = grid_size
        self.grid = [[QColor(15, 18, 26) for _ in range(grid_size)] for _ in range(grid_size)]
        self.current_color = QColor(0, 229, 255)
        self.tool = "pencil"  # pencil, eraser, fill, picker
        self.is_drawing = False
        self.setMouseTracking(True)
        self.setMinimumSize(320, 320)

    def set_grid_size(self, size: int):
        self.grid_size = size
        self.grid = [[QColor(15, 18, 26) for _ in range(size)] for _ in range(size)]
        self.update()

    def get_pil_image(self) -> Image.Image:
        img = Image.new("RGB", (self.grid_size, self.grid_size), (0, 0, 0))
        draw_pixels = img.load()
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                qc = self.grid[y][x]
                draw_pixels[x, y] = (qc.red(), qc.green(), qc.blue())
        return img

    def load_pil_image(self, img: Image.Image):
        img_rgb = img.resize((self.grid_size, self.grid_size), Image.NEAREST).convert("RGB")
        pixels = img_rgb.load()
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                r, g, b = pixels[x, y]
                self.grid[y][x] = QColor(r, g, b)
        self.update()
        self.pixel_changed.emit()

    def clear(self):
        self.grid = [[QColor(15, 18, 26) for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.update()
        self.pixel_changed.emit()

    def mirror_horizontal(self):
        for y in range(self.grid_size):
            self.grid[y].reverse()
        self.update()
        self.pixel_changed.emit()

    def mirror_vertical(self):
        self.grid.reverse()
        self.update()
        self.pixel_changed.emit()

    def flood_fill(self, target_x, target_y, new_color):
        old_color = self.grid[target_y][target_x]
        if old_color == new_color:
            return
        stack = [(target_x, target_y)]
        while stack:
            cx, cy = stack.pop()
            if 0 <= cx < self.grid_size and 0 <= cy < self.grid_size:
                if self.grid[cy][cx] == old_color:
                    self.grid[cy][cx] = new_color
                    stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])
        self.update()
        self.pixel_changed.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        w = self.width()
        h = self.height()
        side = min(w, h)
        cell_size = side / self.grid_size

        # Draw grid cells
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                rect_x = int(x * cell_size)
                rect_y = int(y * cell_size)
                rect_w = int((x + 1) * cell_size) - rect_x
                rect_h = int((y + 1) * cell_size) - rect_y
                painter.fillRect(rect_x, rect_y, rect_w, rect_h, self.grid[y][x])

        # Grid lines (subtle)
        pen = QPen(QColor(30, 36, 48, 120))
        pen.setWidth(1)
        painter.setPen(pen)
        for i in range(self.grid_size + 1):
            pos = int(i * cell_size)
            painter.drawLine(pos, 0, pos, side)
            painter.drawLine(0, pos, side, pos)

    def _apply_tool_at(self, event):
        side = min(self.width(), self.height())
        cell_size = side / self.grid_size
        x = int(event.x() / cell_size)
        y = int(event.y() / cell_size)

        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            if self.tool == "pencil":
                self.grid[y][x] = self.current_color
                self.update()
                self.pixel_changed.emit()
            elif self.tool == "eraser":
                self.grid[y][x] = QColor(15, 18, 26)
                self.update()
                self.pixel_changed.emit()
            elif self.tool == "fill":
                self.flood_fill(x, y, self.current_color)
            elif self.tool == "picker":
                self.current_color = self.grid[y][x]

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_drawing = True
            self._apply_tool_at(event)

    def mouseMoveEvent(self, event):
        if self.is_drawing and (event.buttons() & Qt.LeftButton):
            self._apply_tool_at(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_drawing = False


# -------------------------------------------------------------
# MAIN WINDOW: MODERN iDOTMATRIX CONTROLLER PRO
# -------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("iDotMatrix Studio Pro")
        self.resize(1180, 820)
        self.setMinimumSize(960, 680)
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        # Core Services
        self.ble = BleController()
        self.ble.status_changed.connect(self.on_ble_status)
        self.ble.device_discovered.connect(self.on_device_discovered)
        self.ble.scan_finished.connect(self.on_scan_finished)
        self.ble.command_completed.connect(self.on_command_completed)
        self.ble.start()

        # State
        self.devices_dict = {}  # mac -> name
        self.current_mac = None
        self.is_transmitting_hardware = False
        self.is_carousel_running = False
        self.playlist_images = []
        self.playlist_index = 0

        # DIY Frames for animation
        self.diy_frames: List[Image.Image] = []
        self.diy_frame_idx = 0
        self.diy_anim_timer = QTimer(self)
        self.diy_anim_timer.timeout.connect(self.step_diy_animation)

        # Snake mini-game engine
        self.snake_engine = SnakeGameEngine(32)
        self.snake_timer = QTimer(self)
        self.snake_timer.timeout.connect(self.step_snake_game)

        # Ambient & Hardware timers
        self.hw_timer = QTimer(self)
        self.hw_timer.timeout.connect(self.update_hardware_monitor)
        self.hw_timer.start(1500)

        self.carousel_timer = QTimer(self)
        self.carousel_timer.timeout.connect(self.step_carousel)

        self.ambient_timer = QTimer(self)
        self.ambient_tick = 0
        self.ambient_type = "campfire"
        self.ambient_timer.timeout.connect(self.step_ambient_mode)

        # Setup Interface
        self.setStyleSheet(MODERN_STYLESHEET)
        self.init_ui()
        self.load_settings()

    def closeEvent(self, event):
        self.save_settings()
        self.ble.stop_worker()
        super().closeEvent(event)

    # ---------------------------------------------------------
    # UI SETUP
    # ---------------------------------------------------------
    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        # 1. Top Header Bar (Connection, Status, Quick Controls)
        header_bar = self.create_header_bar()
        main_layout.addWidget(header_bar)

        # 2. Main Tabbed Feature Suites
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_tab_overview(), "⚡ Início & Hardware")
        self.tabs.addTab(self.create_tab_clock_weather(), "🕒 Relógio & Clima")
        self.tabs.addTab(self.create_tab_diy_studio(), "🎨 Estúdio DIY & Animação")
        self.tabs.addTab(self.create_tab_gallery_playlists(), "🖼️ Galeria & Playlists")
        self.tabs.addTab(self.create_tab_text_scroll(), "✍️ Letreiro de Texto")
        self.tabs.addTab(self.create_tab_audio_relax(), "🎵 Áudio & Relaxamento")
        self.tabs.addTab(self.create_tab_games_utilities(), "🎮 Games & Utilitários")
        main_layout.addWidget(self.tabs, stretch=1)

        # 3. Status Footer Bar
        self.footer_label = QLabel("Pronto.")
        self.footer_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        main_layout.addWidget(self.footer_label)

    # --- Header Bar ---
    def create_header_bar(self) -> QWidget:
        header = QFrame()
        header.setObjectName("HeaderBar")
        header.setStyleSheet("background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 6px 12px;")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(14)

        # Logo / Brand
        title_box = QHBoxLayout()
        title_icon = QLabel("💡")
        title_icon.setFont(QFont("Segoe UI", 16))
        title_text = QLabel("iDotMatrix Pro")
        title_text.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_text.setStyleSheet("color: #58a6ff;")
        title_box.addWidget(title_icon)
        title_box.addWidget(title_text)
        layout.addLayout(title_box)

        # Device selector
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        self.device_combo.currentIndexChanged.connect(self.on_device_selected)
        layout.addWidget(self.device_combo)

        self.btn_scan = QPushButton("🔍 Buscar")
        self.btn_scan.clicked.connect(self.start_scan)
        layout.addWidget(self.btn_scan)

        # Connect / Disconnect button
        self.btn_connect = QPushButton("Conectar")
        self.btn_connect.setProperty("class", "Primary")
        self.btn_connect.clicked.connect(self.toggle_connection)
        layout.addWidget(self.btn_connect)

        # Status badge
        self.status_badge = QLabel("🔴 Desconectado")
        self.status_badge.setStyleSheet("color: #f85149; font-weight: bold; padding: 4px 10px; background: #21262d; border-radius: 12px;")
        layout.addWidget(self.status_badge)

        layout.addStretch()

        # Quick Screen power & Brightness
        lbl_bright = QLabel("Brilho:")
        layout.addWidget(lbl_bright)

        self.slider_brightness = QSlider(Qt.Horizontal)
        self.slider_brightness.setRange(5, 100)
        self.slider_brightness.setValue(80)
        self.slider_brightness.setFixedWidth(100)
        self.slider_brightness.sliderReleased.connect(self.on_brightness_changed)
        layout.addWidget(self.slider_brightness)

        self.btn_screen_toggle = QPushButton("☀️ Tela On/Off")
        self.screen_on_state = True
        self.btn_screen_toggle.clicked.connect(self.toggle_screen_power)
        layout.addWidget(self.btn_screen_toggle)

        return header

    # ---------------------------------------------------------
    # TAB 1: OVERVIEW & HARDWARE MONITOR
    # ---------------------------------------------------------
    def create_tab_overview(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(16)

        # Left Column: PC Hardware Stats Cards
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        lbl_section = QLabel("💻 Monitor de Hardware do Computador")
        lbl_section.setFont(QFont("Segoe UI", 13, QFont.Bold))
        left_col.addWidget(lbl_section)

        # CPU Card
        self.card_cpu = QFrame()
        self.card_cpu.setProperty("class", "Card")
        cpu_l = QVBoxLayout(self.card_cpu)
        self.lbl_cpu_title = QLabel("Processador (CPU): 0%")
        self.lbl_cpu_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.bar_cpu = QProgressBar()
        self.bar_cpu.setRange(0, 100)
        self.bar_cpu.setStyleSheet("QProgressBar::chunk { background-color: #00e5ff; }")
        self.lbl_cpu_temp = QLabel("Temp CPU: --°C")
        self.lbl_cpu_temp.setStyleSheet("color: #8b949e; font-size: 11px;")
        cpu_l.addWidget(self.lbl_cpu_title)
        cpu_l.addWidget(self.bar_cpu)
        cpu_l.addWidget(self.lbl_cpu_temp)
        left_col.addWidget(self.card_cpu)

        # GPU Card
        self.card_gpu = QFrame()
        self.card_gpu.setProperty("class", "Card")
        gpu_l = QVBoxLayout(self.card_gpu)
        self.lbl_gpu_title = QLabel("Placa de Vídeo (GPU): 0%")
        self.lbl_gpu_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.bar_gpu = QProgressBar()
        self.bar_gpu.setRange(0, 100)
        self.bar_gpu.setStyleSheet("QProgressBar::chunk { background-color: #00e676; }")
        self.lbl_gpu_temp = QLabel("Temp GPU: --°C")
        self.lbl_gpu_temp.setStyleSheet("color: #8b949e; font-size: 11px;")
        gpu_l.addWidget(self.lbl_gpu_title)
        gpu_l.addWidget(self.bar_gpu)
        gpu_l.addWidget(self.lbl_gpu_temp)
        left_col.addWidget(self.card_gpu)

        # RAM Card
        self.card_ram = QFrame()
        self.card_ram.setProperty("class", "Card")
        ram_l = QVBoxLayout(self.card_ram)
        self.lbl_ram_title = QLabel("Memória RAM: 0%")
        self.lbl_ram_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.bar_ram = QProgressBar()
        self.bar_ram.setRange(0, 100)
        self.bar_ram.setStyleSheet("QProgressBar::chunk { background-color: #7c4dff; }")
        self.lbl_ram_detail = QLabel("Uso: -- GB / -- GB")
        self.lbl_ram_detail.setStyleSheet("color: #8b949e; font-size: 11px;")
        ram_l.addWidget(self.lbl_ram_title)
        ram_l.addWidget(self.bar_ram)
        ram_l.addWidget(self.lbl_ram_detail)
        left_col.addWidget(self.card_ram)

        # Transmission Toggle Button
        self.btn_stream_hw = QPushButton("📡 Iniciar Transmissão Contínua para o Painel")
        self.btn_stream_hw.setProperty("class", "Success")
        self.btn_stream_hw.clicked.connect(self.toggle_hardware_streaming)
        left_col.addWidget(self.btn_stream_hw)

        btn_send_hw_once = QPushButton("🖼️ Enviar Foto Atual do Monitor para Display")
        btn_send_hw_once.clicked.connect(self.send_hardware_snapshot)
        left_col.addWidget(btn_send_hw_once)

        left_col.addStretch()
        layout.addLayout(left_col, stretch=1)

        # Right Column: Live Matrix Preview
        right_col = QVBoxLayout()
        right_col.setAlignment(Qt.AlignCenter)
        lbl_preview = QLabel("Pré-visualização do Display (32x32)")
        lbl_preview.setFont(QFont("Segoe UI", 12, QFont.Bold))
        right_col.addWidget(lbl_preview)

        self.lbl_hw_preview = QLabel()
        self.lbl_hw_preview.setFixedSize(256, 256)
        self.lbl_hw_preview.setStyleSheet("border: 2px solid #30363d; background: #000; border-radius: 8px;")
        right_col.addWidget(self.lbl_hw_preview)

        right_col.addStretch()
        layout.addLayout(right_col, stretch=1)

        return widget

    # ---------------------------------------------------------
    # TAB 2: CLOCK & DYNAMIC WEATHER
    # ---------------------------------------------------------
    def create_tab_clock_weather(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        sub_tabs = QTabWidget()

        # SubTab 1: Clock Faces Gallery
        tab_clocks = QWidget()
        clocks_layout = QVBoxLayout(tab_clocks)

        lbl_gallery = QLabel("Galeria de Mostradores (Clock Faces)")
        lbl_gallery.setFont(QFont("Segoe UI", 13, QFont.Bold))
        clocks_layout.addWidget(lbl_gallery)

        # Grid of Clock Styles
        scroll_clocks = QScrollArea()
        scroll_clocks.setWidgetResizable(True)
        container_clocks = QWidget()
        grid_clocks = QGridLayout(container_clocks)
        grid_clocks.setSpacing(12)

        self.clock_btn_group = QButtonGroup(self)
        for i, face in enumerate(CLOCK_FACES):
            card = QFrame()
            card.setProperty("class", "Card")
            card_l = QVBoxLayout(card)

            radio = QRadioButton(f"{face['icon']} {face['name']}")
            radio.setFont(QFont("Segoe UI", 11, QFont.Bold))
            if i == 0:
                radio.setChecked(True)
            self.clock_btn_group.addButton(radio, face["id"])

            desc = QLabel(face["description"])
            desc.setStyleSheet("color: #8b949e; font-size: 11px;")
            desc.setWordWrap(True)

            card_l.addWidget(radio)
            card_l.addWidget(desc)
            grid_clocks.addWidget(card, i // 2, i % 2)

        scroll_clocks.setWidget(container_clocks)
        clocks_layout.addWidget(scroll_clocks)

        # Options Bar
        opt_box = QHBoxLayout()
        self.chk_clock_date = QCheckBox("Exibir Data")
        self.chk_clock_date.setChecked(True)
        self.chk_clock_24h = QCheckBox("Formato 24 Horas")
        self.chk_clock_24h.setChecked(True)

        self.btn_clock_color = QPushButton("🎨 Cor dos Dígitos")
        self.clock_color = QColor(0, 229, 255)
        self.btn_clock_color.clicked.connect(self.choose_clock_color)

        btn_apply_clock = QPushButton("⚡ Aplicar Mostrador no Display")
        btn_apply_clock.setProperty("class", "Primary")
        btn_apply_clock.clicked.connect(self.apply_clock_face)

        btn_sync_now = QPushButton("🕒 Sincronizar Horário do PC")
        btn_sync_now.clicked.connect(lambda: self.ble.sync_time())

        opt_box.addWidget(self.chk_clock_date)
        opt_box.addWidget(self.chk_clock_24h)
        opt_box.addWidget(self.btn_clock_color)
        opt_box.addWidget(btn_sync_now)
        opt_box.addWidget(btn_apply_clock)
        clocks_layout.addLayout(opt_box)

        sub_tabs.addTab(tab_clocks, "🕒 Mostradores de Relógio")

        # SubTab 2: Dynamic Weather & Temperature
        tab_weather = QWidget()
        weather_layout = QVBoxLayout(tab_weather)

        w_top = QHBoxLayout()
        self.txt_city = QLineEdit()
        self.txt_city.setPlaceholderText("Digite uma cidade (ou deixe vazio para detecção automática)")
        btn_refresh_weather = QPushButton("🔄 Atualizar Clima")
        btn_refresh_weather.clicked.connect(self.update_weather)

        self.unit_c_radio = QRadioButton("°C")
        self.unit_c_radio.setChecked(True)
        self.unit_f_radio = QRadioButton("°F")
        self.unit_c_radio.toggled.connect(self.update_weather)

        w_top.addWidget(QLabel("Cidade:"))
        w_top.addWidget(self.txt_city, stretch=1)
        w_top.addWidget(self.unit_c_radio)
        w_top.addWidget(self.unit_f_radio)
        w_top.addWidget(btn_refresh_weather)
        weather_layout.addLayout(w_top)

        # Weather Card Details
        w_card = QFrame()
        w_card.setProperty("class", "Card")
        w_card_l = QHBoxLayout(w_card)

        self.lbl_weather_preview = QLabel()
        self.lbl_weather_preview.setFixedSize(160, 160)
        self.lbl_weather_preview.setStyleSheet("border: 1px solid #30363d; background: #000; border-radius: 8px;")
        w_card_l.addWidget(self.lbl_weather_preview)

        w_info = QVBoxLayout()
        self.lbl_weather_temp = QLabel("--°C")
        self.lbl_weather_temp.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.lbl_weather_desc = QLabel("Condição: Carregando...")
        self.lbl_weather_desc.setFont(QFont("Segoe UI", 12))
        self.lbl_weather_tip = QLabel("Carregando recomendações de saúde...")
        self.lbl_weather_tip.setWordWrap(True)
        self.lbl_weather_tip.setStyleSheet("background: #1f2937; padding: 10px; border-radius: 8px; color: #6ee7b7; font-weight: 500;")

        btn_project_weather = QPushButton("🚀 Projetar Clima no Display")
        btn_project_weather.setProperty("class", "Primary")
        btn_project_weather.clicked.connect(self.project_weather_card)

        w_info.addWidget(self.lbl_weather_temp)
        w_info.addWidget(self.lbl_weather_desc)
        w_info.addWidget(self.lbl_weather_tip)
        w_info.addWidget(btn_project_weather)
        w_card_l.addLayout(w_info, stretch=1)

        weather_layout.addWidget(w_card)
        weather_layout.addStretch()
        sub_tabs.addTab(tab_weather, "🌦️ Clima & Temperatura")

        # SubTab 3: Sleep Routine & Timers
        tab_sleep = QWidget()
        sleep_l = QVBoxLayout(tab_sleep)

        lbl_sleep_title = QLabel("🌙 Rotina de Sono e Desligamento Programado")
        lbl_sleep_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        sleep_l.addWidget(lbl_sleep_title)

        sleep_card = QFrame()
        sleep_card.setProperty("class", "Card")
        sc_l = QVBoxLayout(sleep_card)
        sc_l.addWidget(QLabel("Defina um tempo para a tela se desligar automaticamente com animação relaxante:"))

        timer_row = QHBoxLayout()
        self.spin_sleep_min = QSpinBox()
        self.spin_sleep_min.setRange(1, 180)
        self.spin_sleep_min.setValue(30)
        self.spin_sleep_min.setSuffix(" minutos")
        timer_row.addWidget(self.spin_sleep_min)

        btn_start_sleep = QPushButton("🌙 Iniciar Modo Sono (Relaxar & Desligar)")
        btn_start_sleep.setProperty("class", "Primary")
        btn_start_sleep.clicked.connect(self.start_sleep_routine)
        timer_row.addWidget(btn_start_sleep)
        sc_l.addLayout(timer_row)

        sleep_l.addWidget(sleep_card)
        sleep_l.addStretch()
        sub_tabs.addTab(tab_sleep, "🌙 Rotina de Sono")

        layout.addWidget(sub_tabs)
        return widget

    # ---------------------------------------------------------
    # TAB 3: DIY STUDIO & FRAME-BY-FRAME ANIMATION
    # ---------------------------------------------------------
    def create_tab_diy_studio(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(14)

        # Left Column: Tools & Colors
        tools_col = QVBoxLayout()
        tools_col.setSpacing(8)

        lbl_tools = QLabel("🛠️ Ferramentas")
        lbl_tools.setFont(QFont("Segoe UI", 11, QFont.Bold))
        tools_col.addWidget(lbl_tools)

        self.btn_pencil = QPushButton("✏️ Lápis")
        self.btn_pencil.clicked.connect(lambda: self.set_diy_tool("pencil"))
        self.btn_eraser = QPushButton("🧹 Borracha")
        self.btn_eraser.clicked.connect(lambda: self.set_diy_tool("eraser"))
        self.btn_fill = QPushButton("🪣 Preencher")
        self.btn_fill.clicked.connect(lambda: self.set_diy_tool("fill"))
        self.btn_picker = QPushButton("💧 Conta-gotas")
        self.btn_picker.clicked.connect(lambda: self.set_diy_tool("picker"))

        tools_col.addWidget(self.btn_pencil)
        tools_col.addWidget(self.btn_eraser)
        tools_col.addWidget(self.btn_fill)
        tools_col.addWidget(self.btn_picker)

        # Color picker
        lbl_color = QLabel("Cores Rápidas:")
        tools_col.addWidget(lbl_color)

        color_grid = QGridLayout()
        colors = [
            "#ff0055", "#ff5500", "#ffcc00", "#00ff66",
            "#00ffff", "#0066ff", "#cc00ff", "#ffffff"
        ]
        for idx, col in enumerate(colors):
            btn_col = QPushButton()
            btn_col.setFixedSize(30, 30)
            btn_col.setStyleSheet(f"background-color: {col}; border: 1px solid #30363d; border-radius: 4px;")
            btn_col.clicked.connect(lambda _, c=col: self.set_diy_color(QColor(c)))
            color_grid.addWidget(btn_col, idx // 4, idx % 4)
        tools_col.addLayout(color_grid)

        btn_more_colors = QPushButton("🎨 Mais Cores...")
        btn_more_colors.clicked.connect(self.open_diy_color_dialog)
        tools_col.addWidget(btn_more_colors)

        # Mirror / Clear
        btn_mirror_h = QPushButton("↔️ Espelhar H")
        btn_mirror_h.clicked.connect(lambda: self.canvas.mirror_horizontal())
        btn_mirror_v = QPushButton("↕️ Espelhar V")
        btn_mirror_v.clicked.connect(lambda: self.canvas.mirror_vertical())
        btn_clear = QPushButton("🗑️ Limpar")
        btn_clear.clicked.connect(lambda: self.canvas.clear())

        tools_col.addWidget(btn_mirror_h)
        tools_col.addWidget(btn_mirror_v)
        tools_col.addWidget(btn_clear)

        tools_col.addStretch()
        layout.addLayout(tools_col)

        # Center Column: Pixel Canvas & Frame Timeline
        center_col = QVBoxLayout()
        self.canvas = PixelCanvasWidget(grid_size=32)
        center_col.addWidget(self.canvas, stretch=1)

        # Frame Animation Timeline bar
        timeline_bar = QHBoxLayout()
        self.lbl_frame_counter = QLabel("Frame: 1 / 1")
        self.lbl_frame_counter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        btn_add_frame = QPushButton("➕ Novo Frame")
        btn_add_frame.clicked.connect(self.add_diy_frame)
        btn_dup_frame = QPushButton("📋 Duplicar")
        btn_dup_frame.clicked.connect(self.dup_diy_frame)
        btn_del_frame = QPushButton("❌ Excluir")
        btn_del_frame.clicked.connect(self.del_diy_frame)

        self.btn_play_anim = QPushButton("▶️ Play Preview")
        self.btn_play_anim.clicked.connect(self.toggle_diy_playback)

        timeline_bar.addWidget(self.lbl_frame_counter)
        timeline_bar.addWidget(btn_add_frame)
        timeline_bar.addWidget(btn_dup_frame)
        timeline_bar.addWidget(btn_del_frame)
        timeline_bar.addWidget(self.btn_play_anim)
        center_col.addLayout(timeline_bar)

        # Send buttons
        send_row = QHBoxLayout()
        btn_send_frame = QPushButton("🚀 Projetar Frame no Display")
        btn_send_frame.setProperty("class", "Primary")
        btn_send_frame.clicked.connect(self.send_current_diy_frame)

        btn_send_anim = QPushButton("🎬 Enviar Animação Completa")
        btn_send_anim.setProperty("class", "Success")
        btn_send_anim.clicked.connect(self.send_diy_animation)

        send_row.addWidget(btn_send_frame)
        send_row.addWidget(btn_send_anim)
        center_col.addLayout(send_row)

        layout.addLayout(center_col, stretch=1)
        return widget

    # ---------------------------------------------------------
    # TAB 4: GALLERY, CONVERTER & PLAYLISTS
    # ---------------------------------------------------------
    def create_tab_gallery_playlists(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        sub_tabs = QTabWidget()

        # SubTab 1: Community Pixel Art Feed
        tab_feed = QWidget()
        feed_l = QVBoxLayout(tab_feed)
        lbl_feed = QLabel("Feed de Artes & Presets da Comunidade")
        lbl_feed.setFont(QFont("Segoe UI", 12, QFont.Bold))
        feed_l.addWidget(lbl_feed)

        scroll_feed = QScrollArea()
        scroll_feed.setWidgetResizable(True)
        container_feed = QWidget()
        grid_feed = QGridLayout(container_feed)
        grid_feed.setSpacing(14)

        for i, item in enumerate(FEED_PRESETS):
            card = QFrame()
            card.setProperty("class", "Card")
            c_layout = QVBoxLayout(card)

            img_art = item["render"](32)
            pix = self.pil_to_qpixmap(img_art).scaled(96, 96, Qt.KeepAspectRatio, Qt.FastTransformation)
            lbl_img = QLabel()
            lbl_img.setPixmap(pix)
            lbl_img.setAlignment(Qt.AlignCenter)

            lbl_title = QLabel(f"{item['icon']} {item['name']}")
            lbl_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
            lbl_cat = QLabel(item["category"])
            lbl_cat.setStyleSheet("color: #8b949e; font-size: 10px;")

            btn_proj = QPushButton("Projetar")
            btn_proj.setProperty("class", "Primary")
            btn_proj.clicked.connect(lambda _, img=img_art: self.ble.upload_pil_image(img, 32))

            c_layout.addWidget(lbl_img)
            c_layout.addWidget(lbl_title)
            c_layout.addWidget(lbl_cat)
            c_layout.addWidget(btn_proj)
            grid_feed.addWidget(card, i // 3, i % 3)

        scroll_feed.setWidget(container_feed)
        feed_l.addWidget(scroll_feed)
        sub_tabs.addTab(tab_feed, "🌐 Feed Pixel Art")

        # SubTab 2: Image & GIF Converter
        tab_conv = QWidget()
        conv_l = QVBoxLayout(tab_conv)

        btn_select_file = QPushButton("📁 Escolher Foto ou GIF do Computador")
        btn_select_file.clicked.connect(self.open_image_converter_dialog)
        conv_l.addWidget(btn_select_file)

        self.lbl_conv_preview = QLabel("Nenhuma imagem selecionada")
        self.lbl_conv_preview.setFixedSize(160, 160)
        self.lbl_conv_preview.setStyleSheet("border: 2px dashed #30363d; border-radius: 8px;")
        self.lbl_conv_preview.setAlignment(Qt.AlignCenter)
        conv_l.addWidget(self.lbl_conv_preview, alignment=Qt.AlignCenter)

        self.btn_send_converted = QPushButton("🚀 Enviar Imagem Convertida para Display")
        self.btn_send_converted.setProperty("class", "Primary")
        self.btn_send_converted.setEnabled(False)
        self.btn_send_converted.clicked.connect(self.send_converted_image)
        conv_l.addWidget(self.btn_send_converted)
        conv_l.addStretch()

        sub_tabs.addTab(tab_conv, "🔄 Conversor de Fotos/GIFs")

        # SubTab 3: Playlists & Auto-Carousel
        tab_play = QWidget()
        play_l = QVBoxLayout(tab_play)
        play_l.addWidget(QLabel("Playlists & Modo Carrossel Automático"))

        car_card = QFrame()
        car_card.setProperty("class", "Card")
        cc_l = QVBoxLayout(car_card)
        cc_l.addWidget(QLabel("Alterna automaticamente entre as artes a cada intervalo de tempo:"))

        c_row = QHBoxLayout()
        self.spin_carousel_sec = QSpinBox()
        self.spin_carousel_sec.setRange(3, 300)
        self.spin_carousel_sec.setValue(10)
        self.spin_carousel_sec.setSuffix(" segundos")

        self.btn_carousel_toggle = QPushButton("▶️ Iniciar Carrossel Contínuo")
        self.btn_carousel_toggle.setProperty("class", "Success")
        self.btn_carousel_toggle.clicked.connect(self.toggle_carousel)

        c_row.addWidget(QLabel("Intervalo:"))
        c_row.addWidget(self.spin_carousel_sec)
        c_row.addWidget(self.btn_carousel_toggle)
        cc_l.addLayout(c_row)

        play_l.addWidget(car_card)
        play_l.addStretch()
        sub_tabs.addTab(tab_play, "🎠 Carrossel Automático")

        layout.addWidget(sub_tabs)
        return widget

    # ---------------------------------------------------------
    # TAB 5: TEXT SCROLL & BILLBOARD
    # ---------------------------------------------------------
    def create_tab_text_scroll(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)

        lbl_title = QLabel("Letreiros e Ferramentas de Texto (Text Scroll)")
        lbl_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        layout.addWidget(lbl_title)

        card = QFrame()
        card.setProperty("class", "Card")
        c_l = QGridLayout(card)
        c_l.setSpacing(12)

        # Text input
        c_l.addWidget(QLabel("Texto a exibir:"), 0, 0)
        self.txt_billboard = QLineEdit("Seja Bem-vindo ao iDotMatrix!")
        c_l.addWidget(self.txt_billboard, 0, 1, 1, 3)

        # Mode / Animation Style
        c_l.addWidget(QLabel("Efeito Visual:"), 1, 0)
        self.combo_text_mode = QComboBox()
        self.combo_text_mode.addItems([
            "0: Estático / Substituição",
            "1: Rolagem para Esquerda (Marquee)",
            "2: Rolagem Reversa (Direita)",
            "3: Rolagem Vertical Subindo",
            "4: Rolagem Vertical Descendo",
            "5: Piscando (Blink)",
            "6: Respiração (Breathe)",
            "7: Efeito Laser / Tetris",
        ])
        self.combo_text_mode.setCurrentIndex(1)
        c_l.addWidget(self.combo_text_mode, 1, 1)

        # Color Effect Mode
        c_l.addWidget(QLabel("Efeito de Cor:"), 1, 2)
        self.combo_text_color_mode = QComboBox()
        self.combo_text_color_mode.addItems([
            "0: Branco Fixo",
            "1: Cor Sólida Personalizada",
            "2: Arco-íris (Rainbow Horizontal)",
            "3: Arco-íris (Rainbow Vertical)",
            "4: Sunset / Pôr do Sol",
            "5: Neon Neonwave",
        ])
        self.combo_text_color_mode.setCurrentIndex(1)
        c_l.addWidget(self.combo_text_color_mode, 1, 3)

        # Speed Slider
        c_l.addWidget(QLabel("Velocidade do Scroll:"), 2, 0)
        self.slider_text_speed = QSlider(Qt.Horizontal)
        self.slider_text_speed.setRange(10, 100)
        self.slider_text_speed.setValue(90)
        c_l.addWidget(self.slider_text_speed, 2, 1)

        # Text Color & Background Color Buttons
        color_btn_row = QHBoxLayout()
        self.text_color = QColor(255, 60, 60)
        self.text_bg_color = QColor(0, 0, 0)

        self.btn_txt_col = QPushButton("🎨 Cor do Texto")
        self.btn_txt_col.clicked.connect(self.choose_text_color)
        self.btn_bg_col = QPushButton("⬛ Cor de Fundo")
        self.btn_bg_col.clicked.connect(self.choose_text_bg_color)

        color_btn_row.addWidget(self.btn_txt_col)
        color_btn_row.addWidget(self.btn_bg_col)
        c_l.addLayout(color_btn_row, 2, 2, 1, 2)

        # Send Button
        btn_send_text = QPushButton("🚀 Enviar Letreiro para o Display")
        btn_send_text.setProperty("class", "Primary")
        btn_send_text.clicked.connect(self.send_text_billboard)
        c_l.addWidget(btn_send_text, 3, 0, 1, 4)

        layout.addWidget(card)
        layout.addStretch()
        return widget

    # ---------------------------------------------------------
    # TAB 6: AUDIO & RELAXATION
    # ---------------------------------------------------------
    def create_tab_audio_relax(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)

        lbl_title = QLabel("Áudio e Reatividade Visual")
        lbl_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        layout.addWidget(lbl_title)

        grid = QGridLayout()

        # Card 1: Equalizer Frequency Visualizer
        c_eq = QFrame()
        c_eq.setProperty("class", "Card")
        eq_l = QVBoxLayout(c_eq)
        eq_l.addWidget(QLabel("📊 Visualizador de Espectro / Equalizador"))
        desc_eq = QLabel("Gera barras de som dinâmicas e pulsantes para acompanhar suas músicas no quarto.")
        desc_eq.setStyleSheet("color: #8b949e;")
        desc_eq.setWordWrap(True)
        eq_l.addWidget(desc_eq)

        self.btn_toggle_eq = QPushButton("🎵 Iniciar Equalizador no Display")
        self.btn_toggle_eq.setProperty("class", "Primary")
        self.is_eq_running = False
        self.btn_toggle_eq.clicked.connect(self.toggle_eq_visualizer)
        eq_l.addWidget(self.btn_toggle_eq)
        grid.addWidget(c_eq, 0, 0)

        # Card 2: White Noise / Relaxing Ambient
        c_relax = QFrame()
        c_relax.setProperty("class", "Card")
        rx_l = QVBoxLayout(c_relax)
        rx_l.addWidget(QLabel("🕯️ Máquina de Ruído Branco & Ambientes"))
        desc_rx = QLabel("Padrões visuais suaves e acolhedores para concentração ou sono:")
        desc_rx.setStyleSheet("color: #8b949e;")
        rx_l.addWidget(desc_rx)

        rx_btns = QHBoxLayout()
        btn_fire = QPushButton("🔥 Fogueira")
        btn_fire.clicked.connect(lambda: self.start_ambient_mode("campfire"))
        btn_ocean = QPushButton("🌊 Ondas do Mar")
        btn_ocean.clicked.connect(lambda: self.start_ambient_mode("ocean"))
        btn_stop_amb = QPushButton("⏹️ Parar")
        btn_stop_amb.clicked.connect(self.stop_ambient_mode)

        rx_btns.addWidget(btn_fire)
        rx_btns.addWidget(btn_ocean)
        rx_btns.addWidget(btn_stop_amb)
        rx_l.addLayout(rx_btns)
        grid.addWidget(c_relax, 0, 1)

        layout.addLayout(grid)
        layout.addStretch()
        return widget

    # ---------------------------------------------------------
    # TAB 7: GAMES & UTILITIES
    # ---------------------------------------------------------
    def create_tab_games_utilities(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)

        lbl_title = QLabel("Widgets de Produtividade, Games e Dia a Dia")
        lbl_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        layout.addWidget(lbl_title)

        grid = QGridLayout()

        # Scoreboard Card
        c_score = QFrame()
        c_score.setProperty("class", "Card")
        sc_l = QVBoxLayout(c_score)
        sc_l.addWidget(QLabel("⚽ Placar Digital (Scoreboard)"))

        score_row = QHBoxLayout()
        self.score_a = 0
        self.score_b = 0

        # Team A
        t_a = QVBoxLayout()
        self.lbl_score_a = QLabel("0")
        self.lbl_score_a.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.lbl_score_a.setAlignment(Qt.AlignCenter)
        btn_a_up = QPushButton("+1")
        btn_a_up.clicked.connect(lambda: self.change_score(1, 0))
        btn_a_dn = QPushButton("-1")
        btn_a_dn.clicked.connect(lambda: self.change_score(-1, 0))
        t_a.addWidget(QLabel("Time A"))
        t_a.addWidget(self.lbl_score_a)
        t_a.addWidget(btn_a_up)
        t_a.addWidget(btn_a_dn)

        # Team B
        t_b = QVBoxLayout()
        self.lbl_score_b = QLabel("0")
        self.lbl_score_b.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.lbl_score_b.setAlignment(Qt.AlignCenter)
        btn_b_up = QPushButton("+1")
        btn_b_up.clicked.connect(lambda: self.change_score(0, 1))
        btn_b_dn = QPushButton("-1")
        btn_b_dn.clicked.connect(lambda: self.change_score(0, -1))
        t_b.addWidget(QLabel("Time B"))
        t_b.addWidget(self.lbl_score_b)
        t_b.addWidget(btn_b_up)
        t_b.addWidget(btn_b_dn)

        score_row.addLayout(t_a)
        score_row.addLayout(t_b)
        sc_l.addLayout(score_row)

        btn_send_score = QPushButton("📡 Enviar Placar para o Painel")
        btn_send_score.setProperty("class", "Primary")
        btn_send_score.clicked.connect(lambda: self.ble.set_scoreboard(self.score_a, self.score_b))
        sc_l.addWidget(btn_send_score)
        grid.addWidget(c_score, 0, 0)

        # Retro Snake Game Card
        c_snake = QFrame()
        c_snake.setProperty("class", "Card")
        sn_l = QVBoxLayout(c_snake)
        sn_l.addWidget(QLabel("🐍 Mini-Game: Jogo da Cobrinha (Snake)"))

        self.lbl_snake_score = QLabel("Pontos: 0")
        sn_l.addWidget(self.lbl_snake_score)

        # D-pad controls
        dpad = QGridLayout()
        btn_up = QPushButton("⬆️")
        btn_up.clicked.connect(lambda: self.snake_engine.change_direction(0, -1))
        btn_down = QPushButton("⬇️")
        btn_down.clicked.connect(lambda: self.snake_engine.change_direction(0, 1))
        btn_left = QPushButton("⬅️")
        btn_left.clicked.connect(lambda: self.snake_engine.change_direction(-1, 0))
        btn_right = QPushButton("➡️")
        btn_right.clicked.connect(lambda: self.snake_engine.change_direction(1, 0))

        dpad.addWidget(btn_up, 0, 1)
        dpad.addWidget(btn_left, 1, 0)
        dpad.addWidget(btn_right, 1, 2)
        dpad.addWidget(btn_down, 2, 1)
        sn_l.addLayout(dpad)

        btn_start_snake = QPushButton("🎮 Iniciar / Reiniciar Jogo no Painel")
        btn_start_snake.setProperty("class", "Success")
        btn_start_snake.clicked.connect(self.start_snake_game)
        sn_l.addWidget(btn_start_snake)
        grid.addWidget(c_snake, 0, 1)

        # App Notifications Card
        c_notif = QFrame()
        c_notif.setProperty("class", "Card")
        nt_l = QVBoxLayout(c_notif)
        nt_l.addWidget(QLabel("🔔 Notificações no Display"))

        nt_combo = QComboBox()
        nt_combo.addItems(["WhatsApp", "Instagram", "Discord", "Email", "Chamada"])
        nt_l.addWidget(nt_combo)

        btn_send_notif = QPushButton("📢 Projetar Alerta com Logo")
        btn_send_notif.setProperty("class", "Primary")
        btn_send_notif.clicked.connect(lambda: self.send_app_notification(nt_combo.currentText()))
        nt_l.addWidget(btn_send_notif)
        grid.addWidget(c_notif, 1, 0, 1, 2)

        layout.addLayout(grid)
        layout.addStretch()
        return widget

    # ---------------------------------------------------------
    # CONTROLLER LOGIC & SLOTS
    # ---------------------------------------------------------
    def on_ble_status(self, connected: bool, message: str):
        if connected:
            self.status_badge.setText(f"🟢 Conectado")
            self.status_badge.setStyleSheet("color: #3fb950; font-weight: bold; padding: 4px 10px; background: #21262d; border-radius: 12px;")
            self.btn_connect.setText("Desconectar")
            self.btn_connect.setProperty("class", "Danger")
        else:
            self.status_badge.setText("🔴 Desconectado")
            self.status_badge.setStyleSheet("color: #f85149; font-weight: bold; padding: 4px 10px; background: #21262d; border-radius: 12px;")
            self.btn_connect.setText("Conectar")
            self.btn_connect.setProperty("class", "Primary")
        self.btn_connect.style().unpolish(self.btn_connect)
        self.btn_connect.style().polish(self.btn_connect)
        self.footer_label.setText(message)

    def on_device_discovered(self, address: str, name: str):
        if address not in self.devices_dict:
            self.devices_dict[address] = name
            self.device_combo.addItem(f"{name} ({address})", address)

    def on_scan_finished(self, found: list):
        self.btn_scan.setText("🔍 Buscar")
        self.btn_scan.setEnabled(True)
        if not found:
            QMessageBox.information(self, "Busca Bluetooth", "Nenhum novo dispositivo iDotMatrix encontrado no alcance.")

    def on_command_completed(self, cmd: str, success: bool, msg: str):
        prefix = "✅" if success else "⚠️"
        self.footer_label.setText(f"{prefix} {cmd}: {msg}")

    def start_scan(self):
        self.btn_scan.setText("Buscando...")
        self.btn_scan.setEnabled(False)
        self.ble.scan_devices()

    def toggle_connection(self):
        if self.ble.is_connected:
            self.ble.disconnect_device()
        else:
            idx = self.device_combo.currentIndex()
            if idx >= 0:
                mac = self.device_combo.itemData(idx)
                if mac:
                    self.current_mac = mac
                    self.ble.connect_device(mac)

    def on_device_selected(self, idx):
        if idx >= 0:
            mac = self.device_combo.itemData(idx)
            if mac and mac != self.current_mac:
                self.current_mac = mac

    def on_brightness_changed(self):
        val = self.slider_brightness.value()
        self.ble.set_brightness(val)

    def toggle_screen_power(self):
        self.screen_on_state = not self.screen_on_state
        self.ble.set_screen_power(self.screen_on_state)
        self.btn_screen_toggle.setText("☀️ Tela On" if not self.screen_on_state else "🌙 Tela Off")

    # --- Hardware Monitor ---
    def update_hardware_monitor(self):
        metrics = HardwareMonitor.get_metrics()
        self.lbl_cpu_title.setText(f"Processador (CPU): {metrics['cpu_percent']}%")
        self.bar_cpu.setValue(metrics["cpu_percent"])
        self.lbl_cpu_temp.setText(f"Temperatura CPU: {metrics['temp_c']}°C ({metrics['temp_f']}°F)")

        self.lbl_gpu_title.setText(f"Placa de Vídeo (GPU): {metrics['gpu_percent']}%")
        self.bar_gpu.setValue(metrics["gpu_percent"])
        self.lbl_gpu_temp.setText(f"Temperatura GPU: {metrics.get('gpu_temp', 40)}°C")

        self.lbl_ram_title.setText(f"Memória RAM: {metrics['ram_percent']}%")
        self.bar_ram.setValue(metrics["ram_percent"])
        self.lbl_ram_detail.setText(f"Uso: {metrics['ram_used_gb']} GB / {metrics['ram_total_gb']} GB")

        # Update preview image
        hw_img = HardwareMonitor.render_matrix_dashboard(32, metrics)
        pix = self.pil_to_qpixmap(hw_img).scaled(256, 256, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.lbl_hw_preview.setPixmap(pix)

        # Transmit continuous stream if enabled
        if self.is_transmitting_hardware and self.ble.is_connected:
            self.ble.upload_pil_image(hw_img, 32)

    def toggle_hardware_streaming(self):
        self.is_transmitting_hardware = not self.is_transmitting_hardware
        if self.is_transmitting_hardware:
            self.btn_stream_hw.setText("⏹️ Parar Transmissão do Monitor")
            self.btn_stream_hw.setProperty("class", "Danger")
        else:
            self.btn_stream_hw.setText("📡 Iniciar Transmissão Contínua para o Painel")
            self.btn_stream_hw.setProperty("class", "Success")
        self.btn_stream_hw.style().unpolish(self.btn_stream_hw)
        self.btn_stream_hw.style().polish(self.btn_stream_hw)

    def send_hardware_snapshot(self):
        img = HardwareMonitor.render_matrix_dashboard(32)
        self.ble.upload_pil_image(img, 32)

    # --- Clock & Weather ---
    def choose_clock_color(self):
        col = QColorDialog.getColor(self.clock_color, self, "Escolher Cor dos Dígitos")
        if col.isValid():
            self.clock_color = col
            self.btn_clock_color.setStyleSheet(f"background-color: {col.name()}; color: #000;")

    def apply_clock_face(self):
        face_id = self.clock_btn_group.checkedId()
        date = self.chk_clock_date.isChecked()
        h24 = self.chk_clock_24h.isChecked()
        r, g, b = self.clock_color.red(), self.clock_color.green(), self.clock_color.blue()
        self.ble.set_clock(face_id, date, h24, r, g, b)

    def update_weather(self):
        city = self.txt_city.text().strip()
        data = WeatherService.get_weather(city)
        unit = "C" if self.unit_c_radio.isChecked() else "F"
        temp = data["temp_c"] if unit == "C" else data["temp_f"]

        self.lbl_weather_temp.setText(f"{temp}°{unit}")
        self.lbl_weather_desc.setText(f"Condição: {data['desc']} em {data['city']}")
        self.lbl_weather_tip.setText(WeatherService.get_health_tip(data["temp_c"]))

        card_img = WeatherService.render_weather_card(data, unit, 32)
        pix = self.pil_to_qpixmap(card_img).scaled(160, 160, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.lbl_weather_preview.setPixmap(pix)
        self.current_weather_img = card_img

    def project_weather_card(self):
        if hasattr(self, "current_weather_img"):
            self.ble.upload_pil_image(self.current_weather_img, 32)
        else:
            self.update_weather()
            if hasattr(self, "current_weather_img"):
                self.ble.upload_pil_image(self.current_weather_img, 32)

    def start_sleep_routine(self):
        minutes = self.spin_sleep_min.value()
        # Start calm ocean waves
        self.start_ambient_mode("ocean")
        QTimer.singleShot(minutes * 60 * 1000, lambda: self.ble.set_screen_power(False))
        QMessageBox.information(self, "Modo Sono Ativado", f"Animação relaxante iniciada. O painel se desligará automaticamente em {minutes} minutos. Durma bem! 😴")

    # --- DIY Editor ---
    def set_diy_tool(self, tool_name: str):
        self.canvas.tool = tool_name
        self.btn_pencil.setProperty("class", "Primary" if tool_name == "pencil" else "")
        self.btn_eraser.setProperty("class", "Primary" if tool_name == "eraser" else "")
        self.btn_fill.setProperty("class", "Primary" if tool_name == "fill" else "")
        self.btn_picker.setProperty("class", "Primary" if tool_name == "picker" else "")
        for b in [self.btn_pencil, self.btn_eraser, self.btn_fill, self.btn_picker]:
            b.style().unpolish(b)
            b.style().polish(b)

    def set_diy_color(self, qc: QColor):
        self.canvas.current_color = qc

    def open_diy_color_dialog(self):
        col = QColorDialog.getColor(self.canvas.current_color, self, "Escolher Cor do Pincel")
        if col.isValid():
            self.set_diy_color(col)

    def add_diy_frame(self):
        current_img = self.canvas.get_pil_image()
        self.diy_frames.append(current_img)
        self.diy_frame_idx = len(self.diy_frames)
        self.canvas.clear()
        self.lbl_frame_counter.setText(f"Frame: {self.diy_frame_idx + 1} / {len(self.diy_frames) + 1}")

    def dup_diy_frame(self):
        current_img = self.canvas.get_pil_image()
        self.diy_frames.append(current_img.copy())
        self.lbl_frame_counter.setText(f"Frame: {len(self.diy_frames)} / {len(self.diy_frames)}")

    def del_diy_frame(self):
        if self.diy_frames:
            self.diy_frames.pop()
            self.lbl_frame_counter.setText(f"Frame: {max(1, len(self.diy_frames))} / {max(1, len(self.diy_frames))}")

    def toggle_diy_playback(self):
        if self.diy_anim_timer.isActive():
            self.diy_anim_timer.stop()
            self.btn_play_anim.setText("▶️ Play Preview")
        else:
            all_frames = self.diy_frames + [self.canvas.get_pil_image()]
            if len(all_frames) > 1:
                self.diy_playback_frames = all_frames
                self.diy_playback_idx = 0
                self.diy_anim_timer.start(250)
                self.btn_play_anim.setText("⏸️ Pausar")

    def step_diy_animation(self):
        if hasattr(self, "diy_playback_frames") and self.diy_playback_frames:
            self.canvas.load_pil_image(self.diy_playback_frames[self.diy_playback_idx])
            self.diy_playback_idx = (self.diy_playback_idx + 1) % len(self.diy_playback_frames)

    def send_current_diy_frame(self):
        img = self.canvas.get_pil_image()
        self.ble.upload_pil_image(img, 32)

    def send_diy_animation(self):
        all_frames = self.diy_frames + [self.canvas.get_pil_image()]
        self.ble.upload_gif_frames(all_frames, duration_ms=250, pixel_size=32)

    # --- Gallery & Playlists ---
    def open_image_converter_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Escolher Imagem ou GIF", "", "Imagens (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            self.converted_path = path
            try:
                with Image.open(path) as img:
                    scaled = img.resize((32, 32), Image.LANCZOS)
                    pix = self.pil_to_qpixmap(scaled).scaled(160, 160, Qt.KeepAspectRatio, Qt.FastTransformation)
                    self.lbl_conv_preview.setPixmap(pix)
                    self.btn_send_converted.setEnabled(True)
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível abrir a imagem: {e}")

    def send_converted_image(self):
        if hasattr(self, "converted_path"):
            if self.converted_path.lower().endswith(".gif"):
                self.ble.upload_gif_file(self.converted_path, 32)
            else:
                self.ble.upload_image_file(self.converted_path, 32)

    def toggle_carousel(self):
        self.is_carousel_running = not self.is_carousel_running
        if self.is_carousel_running:
            self.btn_carousel_toggle.setText("⏹️ Parar Carrossel")
            self.btn_carousel_toggle.setProperty("class", "Danger")
            self.playlist_images = [item["render"](32) for item in FEED_PRESETS]
            sec = self.spin_carousel_sec.value()
            self.carousel_timer.start(sec * 1000)
            self.step_carousel()
        else:
            self.btn_carousel_toggle.setText("▶️ Iniciar Carrossel Contínuo")
            self.btn_carousel_toggle.setProperty("class", "Success")
            self.carousel_timer.stop()
        self.btn_carousel_toggle.style().unpolish(self.btn_carousel_toggle)
        self.btn_carousel_toggle.style().polish(self.btn_carousel_toggle)

    def step_carousel(self):
        if self.playlist_images and self.ble.is_connected:
            img = self.playlist_images[self.playlist_index]
            self.ble.upload_pil_image(img, 32)
            self.playlist_index = (self.playlist_index + 1) % len(self.playlist_images)

    # --- Text Billboard ---
    def choose_text_color(self):
        col = QColorDialog.getColor(self.text_color, self, "Cor do Texto")
        if col.isValid():
            self.text_color = col
            self.btn_txt_col.setStyleSheet(f"background-color: {col.name()}; color: #000;")

    def choose_text_bg_color(self):
        col = QColorDialog.getColor(self.text_bg_color, self, "Cor de Fundo")
        if col.isValid():
            self.text_bg_color = col
            self.btn_bg_col.setStyleSheet(f"background-color: {col.name()}; color: #fff;")

    def send_text_billboard(self):
        txt = self.txt_billboard.text().strip()
        mode_idx = self.combo_text_mode.currentIndex()
        color_mode_idx = self.combo_text_color_mode.currentIndex()
        speed = self.slider_text_speed.value()
        tc = (self.text_color.red(), self.text_color.green(), self.text_color.blue())
        bgc = (self.text_bg_color.red(), self.text_bg_color.green(), self.text_bg_color.blue())

        self.ble.set_text(
            text=txt,
            font_size=16,
            text_mode=mode_idx,
            speed=speed,
            text_color_mode=color_mode_idx,
            text_color=tc,
            text_bg_mode=0 if bgc == (0, 0, 0) else 1,
            text_bg_color=bgc
        )

    # --- Audio & Ambient ---
    def toggle_eq_visualizer(self):
        self.is_eq_running = not self.is_eq_running
        if self.is_eq_running:
            self.btn_toggle_eq.setText("⏹️ Parar Equalizador")
            self.ambient_type = "eq"
            self.ambient_timer.start(120)
        else:
            self.btn_toggle_eq.setText("🎵 Iniciar Equalizador no Display")
            self.ambient_timer.stop()

    def start_ambient_mode(self, mode_name: str):
        self.ambient_type = mode_name
        self.ambient_tick = 0
        self.ambient_timer.start(150)

    def stop_ambient_mode(self):
        self.ambient_timer.stop()

    def step_ambient_mode(self):
        self.ambient_tick += 1
        if self.ambient_type == "campfire":
            img = render_campfire_pattern(self.ambient_tick, 32)
        elif self.ambient_type == "ocean":
            img = render_ocean_waves_pattern(self.ambient_tick, 32)
        elif self.ambient_type == "eq":
            import random
            bars = [min(1.0, max(0.1, random.random())) for _ in range(8)]
            img = render_sound_eq_frame(bars, 32)
        else:
            return

        if self.ble.is_connected:
            self.ble.upload_pil_image(img, 32)

    # --- Games & Scores ---
    def change_score(self, delta_a, delta_b):
        self.score_a = max(0, self.score_a + delta_a)
        self.score_b = max(0, self.score_b + delta_b)
        self.lbl_score_a.setText(str(self.score_a))
        self.lbl_score_b.setText(str(self.score_b))
        self.ble.set_scoreboard(self.score_a, self.score_b)

    def start_snake_game(self):
        self.snake_engine.reset()
        self.snake_timer.start(300)

    def step_snake_game(self):
        self.snake_engine.step()
        self.lbl_snake_score.setText(f"Pontos: {self.snake_engine.score}")
        img = self.snake_engine.render()
        if self.ble.is_connected:
            self.ble.upload_pil_image(img, 32)
        if self.snake_engine.game_over:
            self.snake_timer.stop()
            self.lbl_snake_score.setText(f"Fim de Jogo! Pontos: {self.snake_engine.score}")

    def send_app_notification(self, app_name: str):
        img = create_notification_art(app_name, 32)
        self.ble.upload_pil_image(img, 32)

    # --- Helpers & Storage ---
    def pil_to_qpixmap(self, pil_image: Image.Image) -> QPixmap:
        img_rgb = pil_image.convert("RGB")
        data = img_rgb.tobytes("raw", "RGB")
        qim = QImage(data, img_rgb.size[0], img_rgb.size[1], QImage.Format_RGB888)
        return QPixmap.fromImage(qim)

    def load_settings(self):
        from PyQt5.QtCore import QSettings
        settings = QSettings("MyCompany", "iDotMatrixController")
        saved_devices = settings.value("devices", [])
        for dev in saved_devices:
            if len(dev) == 2:
                mac, name = dev
                self.devices_dict[mac] = name
                self.device_combo.addItem(f"{name} ({mac})", mac)
        if self.device_combo.count() > 0:
            self.device_combo.setCurrentIndex(0)
            self.current_mac = self.device_combo.itemData(0)
        # Load weather immediately
        QTimer.singleShot(800, self.update_weather)

    def save_settings(self):
        from PyQt5.QtCore import QSettings
        settings = QSettings("MyCompany", "iDotMatrixController")
        devs = [(mac, name) for mac, name in self.devices_dict.items()]
        settings.setValue("devices", devs)


# -------------------------------------------------------------
# APPLICATION ENTRY POINT
# -------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
