import requests
from PIL import Image, ImageDraw


class WeatherService:
    """
    Fetches weather data (auto-location or custom city) and renders
    crisp 32x32 pixel art weather cards for the iDotMatrix.
    """

    @classmethod
    def get_weather(cls, city: str = "") -> dict:
        """
        Fetches current weather via wttr.in or returns a safe fallback.
        """
        try:
            target = f"https://wttr.in/{city}?format=j1" if city.strip() else "https://wttr.in/?format=j1"
            res = requests.get(target, timeout=5)
            if res.status_code == 200:
                data = res.json()
                current = data["current_condition"][0]
                area = data["nearest_area"][0]
                city_name = area["areaName"][0]["value"]
                temp_c = int(current["temp_C"])
                temp_f = int(current["temp_F"])
                desc = current["weatherDesc"][0]["value"]
                code = int(current.get("weatherCode", "113"))
                humidity = int(current.get("humidity", "50"))
                return {
                    "city": city_name,
                    "temp_c": temp_c,
                    "temp_f": temp_f,
                    "desc": desc,
                    "code": code,
                    "humidity": humidity,
                    "success": True,
                }
        except Exception as e:
            print(f"Weather fetch error: {e}")

        # Safe fallback
        return {
            "city": city or "Local",
            "temp_c": 22,
            "temp_f": 72,
            "desc": "Ensolarado",
            "code": 113,
            "humidity": 55,
            "success": False,
        }

    @staticmethod
    def get_health_tip(temp_c: int) -> str:
        """Returns health/care advisory based on temperature."""
        if temp_c <= 18:
            return "O tempo está friozinho lá fora! Lembre-se de se agasalhar bem nos dias frios para não pegar friagem e continuar sempre quentinho e saudável. 🧣🧤☕"
        elif temp_c >= 30:
            return "Dia bem quente! Beba bastante água, procure lugares arejados e hidrate-se bem. 💧🧴🕶️"
        else:
            return "Temperatura muito agradável! Aproveite seu dia e continue sempre bem disposto e saudável. ☀️✨"

    @classmethod
    def render_weather_card(cls, weather_data: dict, unit: str = "C", size: int = 32) -> Image.Image:
        """
        Renders a 32x32 pixel art weather card.
        """
        temp = weather_data["temp_c"] if unit == "C" else weather_data["temp_f"]
        desc = weather_data.get("desc", "").lower()
        code = weather_data.get("code", 113)

        img = Image.new("RGB", (size, size), color=(12, 16, 24))
        draw = ImageDraw.Draw(img)

        # Border
        draw.rectangle([0, 0, 31, 31], outline=(30, 40, 60))

        # Determine icon type
        is_rain = "rain" in desc or "drizzle" in desc or code in [296, 302, 308, 353, 356, 359]
        is_snow = "snow" in desc or code in [326, 332, 338, 368, 371]
        is_cloudy = "cloud" in desc or "overcast" in desc or code in [116, 119, 122]
        is_thunder = "thunder" in desc or code in [200, 386, 389]

        # Draw Pixel Icon in upper half (center x=16, y=8)
        if is_thunder:
            # Cloud + Bolt
            draw.rectangle([9, 3, 23, 7], fill=(130, 140, 160))
            draw.line([16, 8, 14, 11], fill=(255, 235, 59))
            draw.line([14, 11, 17, 11], fill=(255, 235, 59))
            draw.line([17, 11, 15, 15], fill=(255, 235, 59))
        elif is_rain:
            # Cloud + Rain drops
            draw.rectangle([9, 3, 23, 7], fill=(120, 140, 170))
            draw.ellipse([8, 2, 14, 8], fill=(130, 150, 180))
            draw.ellipse([16, 1, 24, 7], fill=(150, 170, 200))
            draw.point([(11, 10), (16, 10), (21, 10)], fill=(33, 150, 243))
            draw.point([(10, 13), (15, 13), (20, 13)], fill=(33, 150, 243))
        elif is_snow:
            # Snowflake
            draw.rectangle([9, 3, 23, 7], fill=(160, 180, 200))
            draw.point([(11, 10), (16, 10), (21, 10)], fill=(225, 245, 254))
            draw.point([(12, 12), (15, 12), (18, 12)], fill=(255, 255, 255))
        elif is_cloudy:
            # Fluffy cloud
            draw.rectangle([9, 4, 23, 10], fill=(140, 150, 170))
            draw.ellipse([7, 4, 15, 11], fill=(160, 175, 195))
            draw.ellipse([15, 2, 25, 11], fill=(180, 195, 215))
        else:
            # Bright Sun
            draw.ellipse([11, 3, 21, 13], fill=(255, 193, 7))
            draw.ellipse([12, 4, 20, 12], fill=(255, 235, 59))
            # Sun rays
            draw.point([(16, 1), (16, 15), (9, 8), (23, 8)], fill=(255, 160, 0))
            draw.point([(11, 3), (21, 3), (11, 13), (21, 13)], fill=(255, 160, 0))

        # Bottom section: Temperature Digits
        temp_str = f"{temp}°{unit}"
        # Temperature color
        if temp <= 15:
            tc = (0, 229, 255) # cool cyan
        elif temp <= 26:
            tc = (0, 230, 118) # fresh green
        else:
            tc = (255, 82, 82) # hot red

        # Draw centered-ish temperature text
        draw.text((4, 17), temp_str, fill=tc)

        # Bottom mini bar for humidity
        hum = weather_data.get("humidity", 50)
        hum_w = int((hum / 100.0) * 26)
        draw.rectangle([3, 28, 28, 29], fill=(20, 30, 45))
        if hum_w > 0:
            draw.rectangle([3, 28, 3 + hum_w, 29], fill=(33, 150, 243))

        return img
