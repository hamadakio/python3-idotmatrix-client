import asyncio
import io
import logging
import os
import struct
import sys
import time
from typing import Optional, List, Tuple, Union
from PIL import Image as PilImage

from PyQt5.QtCore import QThread, pyqtSignal

# Import idotmatrix primitives
import idotmatrix
from idotmatrix import (
    ConnectionManager,
    Clock,
    Common,
    Chronograph,
    Countdown,
    FullscreenColor,
    Gif,
    Graffiti,
    Image as IdmImage,
    MusicSync,
    Scoreboard,
    Text,
)
from bleak import BleakScanner
from bleak.backends.scanner import AdvertisementData


class BleController(QThread):
    """
    Persistent Bluetooth Controller running in a dedicated QThread with an asyncio loop.
    Keeps the BLE GATT connection alive across instructions for instant response.
    """
    status_changed = pyqtSignal(bool, str)       # (is_connected, message)
    device_discovered = pyqtSignal(str, str)     # (mac_address, device_name)
    scan_finished = pyqtSignal(list)             # list of (mac, name)
    command_completed = pyqtSignal(str, bool, str)  # (command_name, success, message)
    log_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.queue: Optional[asyncio.Queue] = None
        self.is_running = True
        self.current_address: Optional[str] = None
        self.is_connected = False
        self.current_mode: Optional[str] = None
        self._last_sent_png_bytes: Optional[bytes] = None
        self._lock = None

    def run(self):
        """Thread entry point - initializes asyncio loop and processes commands."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.queue = asyncio.Queue()
        self.conn_mgr = ConnectionManager()

        self.loop.run_until_complete(self._worker_loop())

    async def _worker_loop(self):
        self.log("Bluetooth Worker iniciado.")
        while self.is_running:
            try:
                # Wait for next command item: (action_name, args_dict, future_or_callback)
                item = await self.queue.get()
                if item is None:
                    break
                cmd_name, params = item
                await self._execute_command(cmd_name, params)
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log(f"Erro no loop do worker: {e}")

        # Cleanup on exit
        if self.conn_mgr and self.conn_mgr.client and self.conn_mgr.client.is_connected:
            try:
                await self.conn_mgr.disconnect()
            except Exception:
                pass

    def log(self, text: str):
        self.log_message.emit(text)

    # -------------------------------------------------------------
    # Public Thread-Safe API (Called from Qt GUI thread)
    # -------------------------------------------------------------
    def post_command(self, cmd_name: str, **params):
        """Enqueue command from GUI thread to worker thread."""
        if self.loop and self.queue:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, (cmd_name, params))

    def connect_device(self, address: str):
        self.post_command("connect", address=address)

    def disconnect_device(self):
        self.post_command("disconnect")

    def scan_devices(self):
        self.post_command("scan")

    def set_clock(self, style: int, date: bool = True, h24: bool = True, r: int = 255, g: int = 255, b: int = 255):
        self.post_command("set_clock", style=style, date=date, h24=h24, r=r, g=g, b=b)

    def sync_time(self):
        self.post_command("sync_time")

    def set_time(self, year: int, month: int, day: int, hour: int, minute: int, second: int):
        self.post_command("set_time", year=year, month=month, day=day, hour=hour, minute=minute, second=second)

    def set_text(self, text: str, font_size: int = 16, text_mode: int = 1, speed: int = 95,
                 text_color_mode: int = 1, text_color: Tuple[int, int, int] = (255, 0, 0),
                 text_bg_mode: int = 0, text_bg_color: Tuple[int, int, int] = (0, 0, 0)):
        self.post_command("set_text", text=text, font_size=font_size, text_mode=text_mode, speed=speed,
                          text_color_mode=text_color_mode, text_color=text_color,
                          text_bg_mode=text_bg_mode, text_bg_color=text_bg_color)

    def set_fullscreen_color(self, r: int, g: int, b: int):
        self.post_command("set_fullscreen_color", r=r, g=g, b=b)

    def set_brightness(self, percent: int):
        self.post_command("set_brightness", percent=percent)

    def set_screen_power(self, on: bool):
        self.post_command("set_screen_power", on=on)

    def set_flip_screen(self, flip: bool):
        self.post_command("set_flip_screen", flip=flip)

    def send_pixel_art(self, pixel_commands: List[Tuple[int, int, int, int, int]]):
        """List of (x, y, r, g, b)"""
        self.post_command("send_pixel_art", pixels=pixel_commands)

    def upload_pil_image(self, pil_image: PilImage.Image, pixel_size: int = 32):
        self.post_command("upload_pil_image", image=pil_image, pixel_size=pixel_size)

    def upload_image_file(self, file_path: str, pixel_size: int = 32):
        self.post_command("upload_image_file", file_path=file_path, pixel_size=pixel_size)

    def upload_gif_file(self, file_path: str, pixel_size: int = 32):
        self.post_command("upload_gif_file", file_path=file_path, pixel_size=pixel_size)

    def upload_gif_frames(self, frames: List[PilImage.Image], duration_ms: int = 200, pixel_size: int = 32):
        self.post_command("upload_gif_frames", frames=frames, duration_ms=duration_ms, pixel_size=pixel_size)

    def set_scoreboard(self, left_score: int, right_score: int):
        self.post_command("set_scoreboard", left_score=left_score, right_score=right_score)

    def set_chronograph(self, mode: int):
        self.post_command("set_chronograph", mode=mode)

    def set_countdown(self, mode: int, minutes: int = 5, seconds: int = 0):
        self.post_command("set_countdown", mode=mode, minutes=minutes, seconds=seconds)

    def reset_display(self):
        self.post_command("reset")

    def stop_worker(self):
        self.is_running = False
        if self.loop and self.queue:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, None)
        self.wait(2000)

    # -------------------------------------------------------------
    # Internal Async Command Handlers
    # -------------------------------------------------------------
    async def _ensure_connected(self) -> bool:
        """Verifies if connection is active or reconnects."""
        if not self.current_address:
            self.status_changed.emit(False, "Nenhum dispositivo selecionado.")
            return False

        try:
            if not self.conn_mgr:
                self.conn_mgr = ConnectionManager()
            self.conn_mgr.address = self.current_address
            if not self.conn_mgr.client or not self.conn_mgr.client.is_connected:
                self.log(f"Conectando a {self.current_address}...")
                self.status_changed.emit(False, f"Conectando a {self.current_address}...")
                await self.conn_mgr.connect()
                self.is_connected = True
                self.status_changed.emit(True, f"Conectado a {self.current_address}")
                self.log(f"Conexão BLE estabelecida com {self.current_address}")
            else:
                self.is_connected = True
            return True
        except Exception as e:
            self.is_connected = False
            self.status_changed.emit(False, f"Falha ao conectar: {e}")
            self.log(f"Erro de conexão: {e}")
            return False

    async def _execute_command(self, cmd: str, p: dict):
        try:
            if cmd == "scan":
                self.log("Buscando dispositivos iDotMatrix...")
                devices = await BleakScanner.discover(return_adv=True, timeout=5.0)
                found = []
                for addr, (dev, adv) in devices.items():
                    name = adv.local_name or dev.name or "Dispositivo Desconhecido"
                    if "IDM" in name.upper() or "DOT" in name.upper() or "MATRIX" in name.upper():
                        found.append((dev.address, name))
                        self.device_discovered.emit(dev.address, name)
                self.scan_finished.emit(found)
                self.command_completed.emit("scan", True, f"{len(found)} dispositivo(s) encontrado(s)")
                return

            if cmd == "connect":
                self.current_address = p["address"]
                success = await self._ensure_connected()
                self.command_completed.emit("connect", success, "Conectado" if success else "Falha")
                return

            if cmd == "disconnect":
                if self.conn_mgr and self.conn_mgr.client:
                    await self.conn_mgr.disconnect()
                self.is_connected = False
                self.status_changed.emit(False, "Desconectado")
                self.command_completed.emit("disconnect", True, "Desconectado")
                return

            # All other commands require active connection
            if not await self._ensure_connected():
                self.command_completed.emit(cmd, False, "Dispositivo desconectado")
                return

            # Execute specific commands
            if cmd == "set_clock":
                self.current_mode = "clock"
                self._last_sent_png_bytes = None
                await Clock().setMode(
                    style=p["style"],
                    visibleDate=p["date"],
                    hour24=p["h24"],
                    r=p["r"],
                    g=p["g"],
                    b=p["b"],
                )
                self.command_completed.emit(cmd, True, "Relógio configurado")

            elif cmd == "sync_time":
                now = time.localtime()
                await Common().setTime(
                    year=now.tm_year,
                    month=now.tm_mon,
                    day=now.tm_mday,
                    hour=now.tm_hour,
                    minute=now.tm_min,
                    second=now.tm_sec,
                )
                self.command_completed.emit(cmd, True, "Horário sincronizado com sucesso")

            elif cmd == "set_time":
                await Common().setTime(
                    year=p["year"],
                    month=p["month"],
                    day=p["day"],
                    hour=p["hour"],
                    minute=p["minute"],
                    second=p["second"],
                )
                self.command_completed.emit(cmd, True, "Horário definido")

            elif cmd == "set_text":
                self.current_mode = "text"
                self._last_sent_png_bytes = None
                await Text().setMode(
                    text=p["text"],
                    font_size=p["font_size"],
                    text_mode=p["text_mode"],
                    speed=p["speed"],
                    text_color_mode=p["text_color_mode"],
                    text_color=p["text_color"],
                    text_bg_mode=p["text_bg_mode"],
                    text_bg_color=p["text_bg_color"],
                )
                self.command_completed.emit(cmd, True, "Texto enviado")

            elif cmd == "set_fullscreen_color":
                self.current_mode = "color"
                self._last_sent_png_bytes = None
                await FullscreenColor().setMode(
                    r=int(p["r"]),
                    g=int(p["g"]),
                    b=int(p["b"]),
                )
                self.command_completed.emit(cmd, True, f"Cor definida: RGB({p['r']},{p['g']},{p['b']})")

            elif cmd == "set_brightness":
                await Common().setBrightness(p["percent"])
                self.command_completed.emit(cmd, True, f"Brilho ajustado para {p['percent']}%")

            elif cmd == "set_screen_power":
                if p["on"]:
                    await Common().screenOn()
                else:
                    await Common().screenOff()
                self.command_completed.emit(cmd, True, "Tela " + ("Ligada" if p["on"] else "Desligada"))

            elif cmd == "set_flip_screen":
                await Common().flipScreen(p["flip"])
                self.command_completed.emit(cmd, True, "Tela rotacionada")

            elif cmd == "send_pixel_art":
                # Enable draw mode
                await IdmImage().setMode(mode=1)
                for x, y, r, g, b in p["pixels"]:
                    await Graffiti().setPixel(r=r, g=g, b=b, x=x, y=y)
                self.command_completed.emit(cmd, True, f"{len(p['pixels'])} pixels enviados")

            elif cmd == "upload_pil_image":
                img = p["image"]
                pixel_size = p.get("pixel_size", 32)
                if img.size != (pixel_size, pixel_size):
                    img = img.resize((pixel_size, pixel_size), PilImage.NEAREST)
                
                buf = io.BytesIO()
                img.convert("RGB").save(buf, format="PNG")
                png_bytes = buf.getvalue()
                
                # Avoid duplicate uploads
                if png_bytes == self._last_sent_png_bytes:
                    return

                # Only reset mode to image if not already in image mode (prevents screen blanking flicker)
                if self.current_mode != "image":
                    await IdmImage().setMode(mode=1)
                    self.current_mode = "image"

                self._last_sent_png_bytes = png_bytes
                idm_img = IdmImage()
                payload = idm_img._createPayloads(png_bytes)
                if self.conn_mgr:
                    await self.conn_mgr.send(data=payload)
                self.command_completed.emit(cmd, True, "Imagem enviada com sucesso")

            elif cmd == "upload_image_file":
                await IdmImage().setMode(mode=1)
                await IdmImage().uploadProcessed(file_path=p["file_path"], pixel_size=p["pixel_size"])
                self.command_completed.emit(cmd, True, "Arquivo de imagem enviado")

            elif cmd == "upload_gif_file":
                await Gif().uploadProcessed(file_path=p["file_path"], pixel_size=p["pixel_size"])
                self.command_completed.emit(cmd, True, "GIF enviado")

            elif cmd == "upload_gif_frames":
                frames = p["frames"]
                pixel_size = p.get("pixel_size", 32)
                duration_ms = p.get("duration_ms", 200)
                resized_frames = []
                for fr in frames:
                    if fr.size != (pixel_size, pixel_size):
                        fr = fr.resize((pixel_size, pixel_size), PilImage.NEAREST)
                    resized_frames.append(fr.convert("RGB"))

                if resized_frames:
                    buf = io.BytesIO()
                    resized_frames[0].save(
                        buf,
                        format="GIF",
                        save_all=True,
                        append_images=resized_frames[1:],
                        loop=0,
                        duration=duration_ms,
                        disposal=2,
                    )
                    gif_bytes = buf.getvalue()
                    idm_gif = Gif()
                    payloads = idm_gif._createPayloads(gif_bytes)
                    if self.conn_mgr:
                        for chunk in payloads:
                            await self.conn_mgr.send(data=chunk, response=True)
                    self.command_completed.emit(cmd, True, f"Animação ({len(frames)} frames) enviada")

            elif cmd == "set_scoreboard":
                await Scoreboard().setMode(count1=p["left_score"], count2=p["right_score"])
                self.command_completed.emit(cmd, True, f"Placar: {p['left_score']} x {p['right_score']}")

            elif cmd == "set_chronograph":
                await Chronograph().setMode(p["mode"])
                self.command_completed.emit(cmd, True, "Cronômetro atualizado")

            elif cmd == "set_countdown":
                await Countdown().setMode(
                    mode=p["mode"],
                    minutes=p["minutes"],
                    seconds=p["seconds"]
                )
                self.command_completed.emit(cmd, True, "Temporizador atualizado")

            elif cmd == "reset":
                await Common().reset()
                self.command_completed.emit(cmd, True, "Dispositivo reiniciado")

        except Exception as e:
            self.log(f"Erro ao executar '{cmd}': {e}")
            self.command_completed.emit(cmd, False, str(e))
