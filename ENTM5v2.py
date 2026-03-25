import M5
from M5 import *
from hardware import *
from machine import RTC, I2C, Pin
from unit import ENVUnit
import ntptime
import network
import time
import requests

SW = 240
SH = 135

WIFI_SSID = "云宝的小苹果"
WIFI_PASS = "88888888"

# ---------- 天气 API ----------
WEATHER_API_URL = "https://api.seniverse.com/v3/weather/now.json"
WEATHER_API_KEY = ""   # 有 key 就填这里
WEATHER_LOCATION = "suzhou"

# ---------- 颜色 ----------
C_BG = 0x000000
C_WHITE = 0xFFFFFF
C_CYAN = 0x00FFEE
C_YELLOW = 0xFFDD00
C_GREEN = 0x44FF88
C_RED = 0xFF4444
C_GREY = 0x888888
C_DKGREY = 0x222222

# ---------- 页面 ----------
NUM_PAGES = 8
page = 0

rtc_0 = None
i2c0 = None
env_0 = None
env_ready = False

# ---------- WIFI 状态 ----------
wifi_connected = False
wifi_ip = ""
wifi_signal = "N/A"
wifi_status_text = "Idle"
wlan = None

# ---------- 天气数据 ----------
weather_temp = "--"
weather_desc = "--"
weather_humidity = "--"
last_weather_update = 0
weather_update_interval = 600
weather_fetched = False

# ---------- 提醒数据 ----------
last_water_reminder = 0
water_reminder_interval = 3600
water_alert_pending = False

# ---------- 番茄钟 ----------
WORK_TIME = 25 * 60
BREAK_TIME = 5 * 60
pomo_time = WORK_TIME
pomo_mode = "WORK"
pomo_running = False
pomo_last = 0

# ---------- 时区修正 ----------
TIMEZONE_OFFSET = 8


# ---------- UI ----------
def cls():
    M5.Lcd.fillScreen(C_BG)

def txt(x, y, s, c, bg, size):
    M5.Lcd.setTextColor(c, bg)
    M5.Lcd.setTextSize(size)
    M5.Lcd.setCursor(x, y)
    M5.Lcd.print(str(s))

def bar_top(title):
    M5.Lcd.fillRect(0, 0, SW, 18, C_DKGREY)
    txt(6, 4, title, C_CYAN, C_DKGREY, 1)

def bar_bot(hint):
    M5.Lcd.fillRect(0, SH - 16, SW, 16, C_DKGREY)
    txt(6, SH - 12, hint, C_GREY, C_DKGREY, 1)


# ---------- 时间 ----------
def get_time():
    try:
        yr, mo, dy, wd, hr, mn, sc, _ = rtc_0.datetime()
        # 将 UTC 时间加上时区偏移，正确处理跨天情况
        total_min = hr * 60 + mn + TIMEZONE_OFFSET * 60
        hr = (total_min // 60) % 24
        # 跨天处理
        day_offset = total_min // (24 * 60)
        if day_offset > 0:
            # 简单跨天：只处理加一天，对大多数情况足够
            days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            if (yr % 4 == 0 and yr % 100 != 0) or (yr % 400 == 0):
                days_in_month[2] = 29
            dy += day_offset
            if dy > days_in_month[mo]:
                dy = 1
                mo += 1
                if mo > 12:
                    mo = 1
                    yr += 1
        return yr, mo, dy, wd, hr, mn, sc
    except Exception as e:
        print("get_time error:", e)
        return 2026, 3, 19, 0, 12, 0, 0


# ---------- ENV III ----------
def init_env_sensor():
    global i2c0, env_0, env_ready

    env_ready = False
    env_0 = None
    i2c0 = None

    try:
        print("Init I2C...")
        i2c0 = I2C(0, scl=Pin(33), sda=Pin(32), freq=100000)
        time.sleep_ms(200)

        try:
            devs = i2c0.scan()
            print("I2C scan:", devs)
        except Exception as e:
            print("I2C scan error:", e)

        print("Init ENV III...")
        env_0 = ENVUnit(i2c=i2c0, type=3)
        time.sleep_ms(200)

        # 试读一次确认初始化成功
        try:
            t = env_0.read_temperature()
            h = env_0.read_humidity()
            print("ENV test read OK:", t, h)
            env_ready = True
        except Exception as e:
            print("ENV test read failed:", e)
            env_ready = False

    except Exception as e:
        print("init_env_sensor fatal:", e)
        env_ready = False
        env_0 = None

def read_env():
    try:
        if not env_ready or env_0 is None:
            return None, None, None

        t = round(env_0.read_temperature(), 1)
        h = round(env_0.read_humidity(), 1)

        # 某些版本 pressure 可能没有，单独保护
        try:
            p = round(env_0.read_pressure(), 1)
        except Exception:
            p = None

        return t, h, p
    except Exception as e:
        print("read_env error:", e)
        return None, None, None


# ---------- 蜂鸣 ----------
def beep():
    try:
        Speaker.tone(2000, 150)
        time.sleep_ms(200)
        Speaker.tone(2000, 150)
        time.sleep_ms(200)
        Speaker.tone(2000, 150)
    except Exception as e:
        print("beep error:", e)

def beep_short():
    try:
        Speaker.tone(1500, 100)
    except Exception as e:
        print("beep_short error:", e)


# ---------- 智能提醒逻辑 ----------
def get_temp_warning():
    t_env, _, _ = read_env()
    if t_env is None:
        return "Sensor unavailable", C_GREY
    if t_env >= 32:
        return "Heat risk! Drink water!", C_RED
    elif t_env >= 28:
        return "Stay cool & hydrated!", C_YELLOW
    elif t_env <= 5:
        return "Wear more clothes!", C_CYAN
    elif t_env <= 10:
        return "Add layers!", C_YELLOW
    else:
        return "Comfortable temp", C_GREEN

def get_weather_warning():
    if not weather_fetched:
        return "No weather data", C_GREY
    desc = str(weather_desc).lower()
    if "rain" in desc or "shower" in desc or "drizzle" in desc:
        return "Bring umbrella!", C_CYAN
    elif "snow" in desc:
        return "Snowing! Wear warm!", C_CYAN
    elif "cloud" in desc or "overcast" in desc:
        return "Might rain later", C_GREY
    elif "sunny" in desc or "clear" in desc:
        return "Apply sunscreen!", C_YELLOW
    else:
        return "Check weather app", C_GREY

def check_water_reminder():
    global last_water_reminder, water_alert_pending
    now = time.time()
    if now - last_water_reminder > water_reminder_interval:
        last_water_reminder = now
        water_alert_pending = True


# ---------- CLOCK ----------
def draw_clock_realtime():
    yr, mo, dy, wd, hr, mn, sc = get_time()
    t = "{:02d}:{:02d}:{:02d}".format(hr, mn, sc)
    M5.Lcd.fillRect(0, 40, SW, 40, C_BG)
    M5.Lcd.setTextColor(C_CYAN, C_BG)
    M5.Lcd.setTextSize(3)
    w = len(t) * 18
    M5.Lcd.setCursor((SW - w) // 2, 40)
    M5.Lcd.print(t)

    d = "{}-{}-{}".format(yr, mo, dy)
    M5.Lcd.fillRect(70, 85, 150, 15, C_BG)
    txt(70, 85, d, C_YELLOW, C_BG, 1)

    t_env, h_env, _ = read_env()
    M5.Lcd.fillRect(10, 115, 220, 20, C_BG)
    if t_env is not None:
        M5.Lcd.setTextColor(C_CYAN, C_BG)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(10, 118)
        M5.Lcd.print("T:{:.1f}C H:{:.1f}%".format(t_env, h_env))
    else:
        txt(60, 118, "Sensor Error", C_RED, C_BG, 1)


# ---------- CALENDAR ----------
def draw_calendar():
    cls()
    bar_top("CALENDAR")
    yr, mo, dy, wd, hr, mn, sc = get_time()
    txt(95, 40, "Month " + str(mo), C_WHITE, C_BG, 2)
    txt(105, 70, "Day " + str(dy), C_CYAN, C_BG, 2)
    bar_bot("A:next")


# ---------- SCHEDULE ----------
schedule = [
    (8, 30, "Morning class"),
    (10, 0, "Studio"),
    (12, 0, "Lunch"),
    (14, 0, "Meeting"),
    (16, 30, "Lab"),
    (19, 0, "Study"),
    (22, 0, "Sleep")
]

def draw_schedule():
    cls()
    bar_top("SCHEDULE")
    y = 25
    for s in schedule:
        txt(10, y, "{:02d}:{:02d}".format(s[0], s[1]), C_YELLOW, C_BG, 1)
        txt(80, y, s[2], C_WHITE, C_BG, 1)
        y += 15
    bar_bot("A:next")


# ---------- ENV 页面 ----------
def draw_env():
    cls()
    bar_top("ENV III")
    t, h, p = read_env()
    if t is not None:
        M5.Lcd.setTextColor(C_CYAN, C_BG)
        M5.Lcd.setTextSize(2)
        M5.Lcd.setCursor(55, 28)
        M5.Lcd.print("T: " + str(t) + "C")

        txt(40, 65, "Humidity: " + str(h) + "%", C_WHITE, C_BG, 1)

        if p is not None:
            txt(40, 85, "Pressure: " + str(p) + " hPa", C_YELLOW, C_BG, 1)
        else:
            txt(40, 85, "Pressure: N/A", C_YELLOW, C_BG, 1)
    else:
        txt(60, 60, "Sensor Error", C_RED, C_BG, 1)
    bar_bot("A:next")


# ---------- POMODORO ----------
def draw_pomodoro():
    cls()
    bar_top("POMODORO")
    col = C_RED if pomo_mode == "WORK" else C_GREEN
    txt(95, 20, pomo_mode, col, C_BG, 2)

    m = pomo_time // 60
    s = pomo_time % 60
    ts = "{:02d}:{:02d}".format(m, s)

    M5.Lcd.setTextColor(C_WHITE, C_BG)
    M5.Lcd.setTextSize(3)
    w = len(ts) * 18
    M5.Lcd.setCursor((SW - w) // 2, 55)
    M5.Lcd.print(ts)

    status = "Running" if pomo_running else "Paused"
    txt(95, 110, status, C_GREY, C_BG, 1)
    bar_bot("A:next  Dbl:start/pause")


# ---------- REMINDERS 页面 ----------
def draw_reminders():
    cls()
    bar_top("REMINDERS")

    temp_warn, temp_color = get_temp_warning()
    txt(10, 25, "Temp:", C_CYAN, C_BG, 1)
    txt(10, 40, temp_warn, temp_color, C_BG, 1)

    weather_warn, weather_color = get_weather_warning()
    txt(10, 65, "Weather:", C_CYAN, C_BG, 1)
    txt(10, 80, weather_warn, weather_color, C_BG, 1)

    if water_alert_pending:
        txt(10, 105, "Drink water! (^_^)", C_YELLOW, C_BG, 1)
    else:
        txt(10, 105, "Stay hydrated!", C_GREEN, C_BG, 1)

    bar_bot("A:next")


# ---------- WIFI ----------
def wifi_reset_state():
    global wifi_connected, wifi_ip, wifi_signal, wifi_status_text
    wifi_connected = False
    wifi_ip = ""
    wifi_signal = "N/A"
    wifi_status_text = "Idle"

def adopt_existing_wifi():
    global wlan
    try:
        wlan = network.WLAN(network.STA_IF)
        try:
            wlan.active(True)
            time.sleep_ms(100)
        except Exception as e:
            print("wlan active warning:", e)
        return refresh_wifi_state()
    except Exception as e:
        print("adopt_existing_wifi error:", e)
        wifi_reset_state()
        return False

def refresh_wifi_state():
    global wifi_connected, wifi_ip, wifi_signal, wifi_status_text, wlan
    try:
        if wlan is None:
            wlan = network.WLAN(network.STA_IF)

        if wlan.active() and wlan.isconnected():
            wifi_connected = True
            wifi_ip = wlan.ifconfig()[0]
            wifi_signal = "N/A"
            wifi_status_text = "Connected"
            return True
        else:
            wifi_connected = False
            wifi_ip = ""
            wifi_signal = "N/A"
            if wifi_status_text == "Connected":
                wifi_status_text = "Disconnected"
            elif wifi_status_text == "Idle":
                wifi_status_text = "Not connected"
            return False
    except Exception as e:
        print("refresh_wifi_state error:", e)
        wifi_connected = False
        wifi_ip = ""
        wifi_signal = "N/A"
        wifi_status_text = "State error"
        return False

def connect_wifi():
    global wlan, wifi_status_text

    cls()
    txt(40, 50, "Connecting...", C_YELLOW, C_BG, 2)
    txt(30, 90, "Please wait", C_GREY, C_BG, 1)

    try:
        if wlan is None:
            wlan = network.WLAN(network.STA_IF)

        if refresh_wifi_state():
            cls()
            txt(40, 50, "Connected!", C_GREEN, C_BG, 2)
            txt(20, 90, "IP: " + wifi_ip, C_CYAN, C_BG, 1)
            # 连接成功后同步时间
            try:
                txt(20, 108, "Syncing time...", C_YELLOW, C_BG, 1)
                ntptime.settime()
                txt(20, 108, "Time synced!   ", C_GREEN, C_BG, 1)
            except Exception as e:
                print("NTP after connect failed:", e)
            time.sleep(1)
            return True

        wlan.active(True)
        time.sleep_ms(300)
        wifi_status_text = "Connecting"

        try:
            wlan.disconnect()
            time.sleep_ms(200)
        except:
            pass

        wlan.connect(WIFI_SSID, WIFI_PASS)

        start_ms = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_ms) < 15000:
            time.sleep_ms(300)
            M5.update()
            if refresh_wifi_state():
                cls()
                txt(40, 50, "Connected!", C_GREEN, C_BG, 2)
                txt(20, 90, "IP: " + wifi_ip, C_CYAN, C_BG, 1)
                time.sleep(1)
                return True

        wifi_status_text = "Timeout"
        cls()
        txt(30, 50, "Connect Failed", C_RED, C_BG, 2)
        txt(20, 90, "Check SSID/Password", C_GREY, C_BG, 1)
        time.sleep(1.5)
        return False

    except Exception as e:
        print("connect_wifi error:", e)
        wifi_status_text = "Error"
        cls()
        txt(30, 50, "WiFi Error", C_RED, C_BG, 2)
        txt(10, 90, str(e)[:28], C_GREY, C_BG, 1)
        time.sleep(1.5)
        return False

def disconnect_wifi():
    global wifi_connected, wifi_ip, wifi_signal, wifi_status_text, wlan
    try:
        if wlan is not None:
            try:
                wlan.disconnect()
                time.sleep_ms(200)
            except Exception as e:
                print("disconnect error:", e)
        wifi_connected = False
        wifi_ip = ""
        wifi_signal = "N/A"
        wifi_status_text = "Disconnected"
    except Exception as e:
        print("disconnect_wifi error:", e)

def sync_ntp():
    if not refresh_wifi_state():
        return False
    try:
        ntptime.settime()
        return True
    except Exception as e:
        print("NTP sync error:", e)
        return False


# ---------- WIFI 页面 ----------
def draw_wifi():
    cls()
    bar_top("WIFI")
    refresh_wifi_state()

    if wifi_connected:
        txt(50, 25, "Connected", C_GREEN, C_BG, 2)
        txt(20, 55, "SSID: " + WIFI_SSID, C_WHITE, C_BG, 1)
        txt(20, 75, "IP: " + wifi_ip, C_CYAN, C_BG, 1)
        txt(20, 95, "Signal: " + str(wifi_signal), C_YELLOW, C_BG, 1)
        txt(20, 112, "State: " + wifi_status_text, C_GREY, C_BG, 1)
    else:
        txt(40, 25, "Disconnected", C_RED, C_BG, 2)
        txt(20, 65, "State: " + wifi_status_text, C_YELLOW, C_BG, 1)
        txt(20, 90, "Double click to connect", C_GREY, C_BG, 1)

    bar_bot("A:next  Dbl:connect")

def update_wifi_signal():
    if page != 6:
        return
    M5.Lcd.fillRect(20, 95, 210, 25, C_BG)
    txt(20, 95, "Signal: " + str(wifi_signal), C_YELLOW, C_BG, 1)
    txt(20, 112, "State: " + wifi_status_text, C_GREY, C_BG, 1)


# ---------- WEATHER ----------
def draw_weather():
    cls()
    bar_top("WEATHER")
    refresh_wifi_state()

    if not wifi_connected:
        txt(20, 55, "WiFi not connected", C_RED, C_BG, 1)
        txt(20, 80, "Go to WiFi page", C_GREY, C_BG, 1)
    else:
        if weather_fetched:
            txt(20, 25, "Outdoor: " + str(weather_temp) + "C", C_YELLOW, C_BG, 1)
            txt(20, 45, "Weather: " + str(weather_desc), C_WHITE, C_BG, 1)
            weather_warn, warn_color = get_weather_warning()
            txt(10, 65, weather_warn, warn_color, C_BG, 1)
            temp_warn, temp_color = get_temp_warning()
            txt(10, 85, temp_warn, temp_color, C_BG, 1)
        else:
            txt(40, 55, "No data", C_GREY, C_BG, 2)
            txt(10, 90, "Double click to fetch", C_GREY, C_BG, 1)

    bar_bot("A:next  Dbl:refresh")

def update_weather():
    if page != 7:
        return
    if not wifi_connected or not weather_fetched:
        return
    M5.Lcd.fillRect(0, 20, SW, 100, C_BG)
    txt(20, 25, "Outdoor: " + str(weather_temp) + "C", C_YELLOW, C_BG, 1)
    txt(20, 45, "Weather: " + str(weather_desc), C_WHITE, C_BG, 1)
    weather_warn, warn_color = get_weather_warning()
    txt(10, 65, weather_warn, warn_color, C_BG, 1)
    temp_warn, temp_color = get_temp_warning()
    txt(10, 85, temp_warn, temp_color, C_BG, 1)

def fetch_weather():
    global weather_temp, weather_desc, weather_humidity, last_weather_update, weather_fetched

    if not refresh_wifi_state():
        print("fetch_weather: wifi not connected")
        return False

    if WEATHER_API_KEY == "":
        print("Weather API key missing")
        weather_temp = "--"
        weather_desc = "API key missing"
        weather_humidity = "--"
        weather_fetched = False
        return False

    response = None
    try:
        url = (
            WEATHER_API_URL
            + "?key=" + WEATHER_API_KEY
            + "&location=" + WEATHER_LOCATION
            + "&language=en"
            + "&unit=c"
        )

        print("Weather URL:", url)
        response = requests.get(url, timeout=5)
        print("Weather status:", response.status_code)

        if response.status_code == 200:
            data = response.json()
            if "results" in data and len(data["results"]) > 0:
                now = data["results"][0]["now"]
                weather_temp = now.get("temperature", "--")
                weather_desc = now.get("text", "--")
                weather_humidity = now.get("humidity", "--")
                last_weather_update = time.time()
                weather_fetched = True
                return True

        weather_fetched = False
        return False

    except Exception as e:
        print("Weather fetch error:", e)
        weather_fetched = False
        return False

    finally:
        try:
            if response is not None:
                response.close()
        except:
            pass


# ---------- SETUP ----------
def setup():
    global rtc_0

    M5.begin()
    M5.Lcd.setRotation(3)
    M5.Lcd.setBrightness(100)

    rtc_0 = RTC()

    # 初始化传感器
    init_env_sensor()

    # 接管当前 WiFi 状态
    adopt_existing_wifi()

    cls()
    txt(55, 45, "CuteWatch", C_CYAN, C_BG, 2)

    # 如果 WiFi 已连接，自动同步时间
    if wifi_connected:
        txt(50, 80, "Syncing NTP...", C_YELLOW, C_BG, 1)
        try:
            ntptime.settime()
            txt(55, 95, "Time synced!", C_GREEN, C_BG, 1)
        except Exception as e:
            print("NTP sync failed:", e)
            txt(40, 95, "NTP sync failed", C_RED, C_BG, 1)
    else:
        txt(30, 80, "No WiFi - time may", C_GREY, C_BG, 1)
        txt(30, 95, "be incorrect", C_GREY, C_BG, 1)

    time.sleep(1.5)


# ---------- LOOP ----------
def loop():
    global page, pomo_time, pomo_last, pomo_running, pomo_mode
    global last_weather_update, water_alert_pending

    pages = [
        draw_clock_realtime,
        draw_calendar,
        draw_schedule,
        draw_env,
        draw_pomodoro,
        draw_reminders,
        draw_wifi,
        draw_weather
    ]

    cls()
    draw_clock_realtime()

    last_draw = time.ticks_ms()
    last_btn_press = 0
    double_click_threshold = 400
    waiting_double = False

    while True:
        M5.update()

        if BtnA.wasPressed():
            now_ms = time.ticks_ms()

            if waiting_double and time.ticks_diff(now_ms, last_btn_press) < double_click_threshold:
                waiting_double = False

                if page == 4:
                    pomo_running = not pomo_running
                    pomo_last = time.time()
                    draw_pomodoro()

                elif page == 6:
                    refresh_wifi_state()
                    if not wifi_connected:
                        connect_wifi()
                    else:
                        disconnect_wifi()
                    draw_wifi()

                elif page == 7:
                    cls()
                    txt(40, 60, "Fetching...", C_YELLOW, C_BG, 2)
                    if fetch_weather():
                        draw_weather()
                    else:
                        txt(30, 60, "Fetch Failed", C_RED, C_BG, 2)
                        time.sleep(1)
                        draw_weather()

            else:
                waiting_double = True
                last_btn_press = now_ms

        if waiting_double and time.ticks_diff(time.ticks_ms(), last_btn_press) > double_click_threshold:
            waiting_double = False
            page = (page + 1) % NUM_PAGES
            pages[page]()

            if page == 7:
                refresh_wifi_state()
                if wifi_connected and not weather_fetched:
                    cls()
                    txt(40, 60, "Fetching...", C_YELLOW, C_BG, 2)
                    fetch_weather()
                    draw_weather()

        if pomo_running and time.time() - pomo_last >= 1:
            pomo_last = time.time()
            pomo_time -= 1
            if pomo_time <= 0:
                beep()
                if pomo_mode == "WORK":
                    pomo_mode = "BREAK"
                    pomo_time = BREAK_TIME
                else:
                    pomo_mode = "WORK"
                    pomo_time = WORK_TIME
                if page == 4:
                    draw_pomodoro()

        check_water_reminder()
        if water_alert_pending:
            beep_short()
            water_alert_pending = False

        if time.ticks_diff(time.ticks_ms(), last_draw) > 1000:
            if page == 0:
                draw_clock_realtime()
            elif page == 5:
                draw_reminders()
            elif page == 6:
                refresh_wifi_state()
                update_wifi_signal()
            elif page == 7:
                refresh_wifi_state()
                if wifi_connected and time.time() - last_weather_update > weather_update_interval:
                    fetch_weather()
                update_weather()
            last_draw = time.ticks_ms()

        time.sleep_ms(50)


# ---------- RUN ----------
if __name__ == "__main__":
    try:
        setup()
        loop()
    except Exception as e:
        print("FATAL ERROR:", e)
        try:
            cls()
            txt(10, 50, "Fatal Error", C_RED, C_BG, 2)
            txt(10, 90, str(e)[:30], C_GREY, C_BG, 1)
        except:
            pass