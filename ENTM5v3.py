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

# =========================
# WiFi 配置
# =========================
WIFI_SSID = "云宝的小苹果"
WIFI_PASS = "88888888"

# =========================
# 天气 API
# =========================
WEATHER_API_URL = "https://api.seniverse.com/v3/weather/now.json"
WEATHER_API_KEY = ""     # 这里填你的心知天气 key
WEATHER_LOCATION = "suzhou"

# =========================
# 颜色
# =========================
C_BG = 0x000000
C_WHITE = 0xFFFFFF
C_CYAN = 0x00FFEE
C_YELLOW = 0xFFDD00
C_GREEN = 0x44FF88
C_RED = 0xFF4444
C_GREY = 0x888888
C_DKGREY = 0x222222

# =========================
# 页面
# =========================
NUM_PAGES = 8
page = 0

rtc_0 = None
i2c0 = None
env_0 = None
env_ready = False

# =========================
# WIFI 状态
# =========================
wifi_connected = False
wifi_ip = ""
wifi_signal = "N/A"
wifi_status_text = "Idle"
wlan = None
wifi_connect_started = False
wifi_last_try_ms = 0

# =========================
# 天气数据
# =========================
weather_temp = "--"
weather_desc = "--"
weather_humidity = "--"
last_weather_update = 0
weather_update_interval = 600
weather_fetched = False

# =========================
# 提醒数据
# =========================
last_water_reminder = 0
water_reminder_interval = 3600
water_alert_pending = False

# =========================
# 番茄钟
# =========================
WORK_TIME = 25 * 60
BREAK_TIME = 5 * 60
pomo_time = WORK_TIME
pomo_mode = "WORK"
pomo_running = False
pomo_last = 0

# =========================
# 时区
# =========================
TIMEZONE_OFFSET = 8


# =========================
# UI
# =========================
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


# =========================
# 时间
# =========================
def get_time():
    try:
        # 用 NTP 同步后的 epoch 时间再加时区偏移，避免你原来手动处理年月日出错
        ts = time.time() + TIMEZONE_OFFSET * 3600
        y, mo, d, hh, mm, ss, wd, yd = time.localtime(ts)
        return y, mo, d, wd, hh, mm, ss
    except Exception as e:
        print("get_time error:", e)
        return 2026, 3, 19, 0, 12, 0, 0


def sync_ntp():
    if not refresh_wifi_state():
        return False
    try:
        ntptime.host = "ntp.aliyun.com"
    except Exception:
        pass
    try:
        ntptime.settime()
        print("NTP synced")
        return True
    except Exception as e:
        print("NTP sync error:", e)
        return False


# =========================
# ENV III
# =========================
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

        try:
            p = round(env_0.read_pressure(), 1)
        except Exception:
            p = None

        return t, h, p
    except Exception as e:
        print("read_env error:", e)
        return None, None, None


# =========================
# 蜂鸣
# =========================
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
        Speaker.tone(1500, 80)
    except Exception as e:
        print("beep_short error:", e)


# =========================
# 智能提醒逻辑
# =========================
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


# =========================
# CLOCK
# =========================
def draw_clock_realtime():
    yr, mo, dy, wd, hr, mn, sc = get_time()
    t = "{:02d}:{:02d}:{:02d}".format(hr, mn, sc)
    M5.Lcd.fillRect(0, 40, SW, 40, C_BG)
    M5.Lcd.setTextColor(C_CYAN, C_BG)
    M5.Lcd.setTextSize(3)
    w = len(t) * 18
    M5.Lcd.setCursor((SW - w) // 2, 40)
    M5.Lcd.print(t)

    d = "{}-{:02d}-{:02d}".format(yr, mo, dy)
    M5.Lcd.fillRect(55, 85, 160, 15, C_BG)
    txt(55, 85, d, C_YELLOW, C_BG, 1)

    t_env, h_env, _ = read_env()
    M5.Lcd.fillRect(10, 115, 220, 20, C_BG)
    if t_env is not None:
        M5.Lcd.setTextColor(C_CYAN, C_BG)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(10, 118)
        M5.Lcd.print("T:{:.1f}C H:{:.1f}%".format(t_env, h_env))
    else:
        txt(60, 118, "Sensor Error", C_RED, C_BG, 1)


# =========================
# CALENDAR
# =========================
def draw_calendar():
    cls()
    bar_top("CALENDAR")
    yr, mo, dy, wd, hr, mn, sc = get_time()
    txt(95, 40, "Month " + str(mo), C_WHITE, C_BG, 2)
    txt(105, 70, "Day " + str(dy), C_CYAN, C_BG, 2)
    bar_bot("A:next")


# =========================
# SCHEDULE
# =========================
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


# =========================
# ENV 页面
# =========================
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


# =========================
# POMODORO
# =========================
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


# =========================
# REMINDERS 页面
# =========================
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


# =========================
# WIFI 工具函数
# =========================
def wifi_status_name(st):
    if st == 1000:
        return "Idle"
    elif st == 1001:
        return "Connecting"
    elif st == 1010:
        return "Got IP"
    elif st == 200:
        return "Beacon timeout"
    elif st == 201:
        return "No AP found"
    elif st == 202:
        return "Wrong password"
    elif st == 203:
        return "Assoc fail"
    elif st == 204:
        return "Handshake timeout"
    else:
        return str(st)


def init_wifi():
    global wlan
    try:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        time.sleep_ms(200)
        return True
    except Exception as e:
        print("init_wifi error:", e)
        return False


def refresh_wifi_state():
    global wifi_connected, wifi_ip, wifi_signal, wifi_status_text, wlan
    try:
        if wlan is None:
            wlan = network.WLAN(network.STA_IF)

        if not wlan.active():
            wifi_connected = False
            wifi_ip = ""
            wifi_signal = "N/A"
            wifi_status_text = "WiFi off"
            return False

        try:
            st = wlan.status()
            wifi_status_text = wifi_status_name(st)
        except Exception:
            pass

        if wlan.isconnected():
            wifi_connected = True
            try:
                wifi_ip = wlan.ifconfig()[0]
            except Exception:
                wifi_ip = "0.0.0.0"
            try:
                wifi_signal = str(wlan.status("rssi"))
            except Exception:
                wifi_signal = "N/A"
            if wifi_status_text == "1010":
                wifi_status_text = "Connected"
            return True
        else:
            wifi_connected = False
            wifi_ip = ""
            try:
                wifi_signal = str(wlan.status("rssi"))
            except Exception:
                wifi_signal = "N/A"
            return False

    except Exception as e:
        print("refresh_wifi_state error:", e)
        wifi_connected = False
        wifi_ip = ""
        wifi_signal = "N/A"
        wifi_status_text = "State error"
        return False


def start_wifi_connect_block_style():
    global wlan, wifi_status_text, wifi_connect_started, wifi_last_try_ms
    try:
        if not init_wifi():
            wifi_status_text = "Init failed"
            return False

        try:
            wlan.connect(WIFI_SSID, WIFI_PASS)
            wifi_connect_started = True
            wifi_last_try_ms = time.ticks_ms()
            wifi_status_text = "Connecting"
            print("WiFi connect start (block style)")
            return True
        except Exception as e:
            print("start_wifi_connect_block_style error:", e)
            wifi_status_text = "Connect call fail"
            return False
    except Exception as e:
        print("start wifi fatal:", e)
        wifi_status_text = "Error"
        return False


def connect_wifi_wait(max_wait_ms=15000):
    cls()
    txt(40, 40, "Connecting...", C_YELLOW, C_BG, 2)
    txt(12, 72, "SSID: " + WIFI_SSID, C_WHITE, C_BG, 1)
    txt(12, 96, "Please wait...", C_GREY, C_BG, 1)

    start_wifi_connect_block_style()
    start_ms = time.ticks_ms()

    while time.ticks_diff(time.ticks_ms(), start_ms) < max_wait_ms:
        M5.update()
        refresh_wifi_state()

        M5.Lcd.fillRect(12, 112, 220, 15, C_BG)
        txt(12, 112, "State: " + wifi_status_text, C_GREY, C_BG, 1)

        if wifi_connected:
            cls()
            txt(48, 38, "Connected!", C_GREEN, C_BG, 2)
            txt(12, 70, "IP: " + wifi_ip, C_CYAN, C_BG, 1)
            txt(12, 92, "Syncing time...", C_YELLOW, C_BG, 1)
            if sync_ntp():
                txt(12, 110, "Time synced", C_GREEN, C_BG, 1)
            else:
                txt(12, 110, "Time sync failed", C_RED, C_BG, 1)
            time.sleep(1.2)
            return True

        time.sleep_ms(300)

    cls()
    txt(26, 40, "Connect Failed", C_RED, C_BG, 2)
    txt(12, 75, "State: " + wifi_status_text, C_YELLOW, C_BG, 1)
    txt(12, 98, "Check hotspot / signal", C_GREY, C_BG, 1)
    time.sleep(1.5)
    return False


def disconnect_wifi():
    global wifi_connected, wifi_ip, wifi_signal, wifi_status_text, wlan, wifi_connect_started
    try:
        if wlan is not None:
            try:
                wlan.disconnect()
            except Exception as e:
                print("disconnect warning:", e)
        wifi_connected = False
        wifi_ip = ""
        wifi_signal = "N/A"
        wifi_status_text = "Disconnected"
        wifi_connect_started = False
        return True
    except Exception as e:
        print("disconnect_wifi error:", e)
        return False


# =========================
# WIFI 页面
# =========================
def draw_wifi():
    cls()
    bar_top("WIFI")
    refresh_wifi_state()

    if wifi_connected:
        txt(50, 24, "Connected", C_GREEN, C_BG, 2)
        txt(16, 50, "SSID: " + WIFI_SSID, C_WHITE, C_BG, 1)
        txt(16, 70, "IP: " + wifi_ip, C_CYAN, C_BG, 1)
        txt(16, 90, "Signal: " + str(wifi_signal), C_YELLOW, C_BG, 1)
        txt(16, 110, "State: " + wifi_status_text, C_GREY, C_BG, 1)
        bar_bot("A:next  Dbl:disconnect")
    else:
        txt(34, 24, "Disconnected", C_RED, C_BG, 2)
        txt(16, 56, "SSID: " + WIFI_SSID, C_WHITE, C_BG, 1)
        txt(16, 78, "State: " + wifi_status_text, C_YELLOW, C_BG, 1)
        txt(16, 102, "Double click to connect", C_GREY, C_BG, 1)
        bar_bot("A:next  Dbl:connect")


def update_wifi_signal():
    if page != 6:
        return
    refresh_wifi_state()
    M5.Lcd.fillRect(16, 86, 220, 32, C_BG)
    txt(16, 90, "Signal: " + str(wifi_signal), C_YELLOW, C_BG, 1)
    txt(16, 110, "State: " + wifi_status_text, C_GREY, C_BG, 1)


# =========================
# WEATHER
# =========================
def draw_weather():
    cls()
    bar_top("WEATHER")
    refresh_wifi_state()

    if not wifi_connected:
        txt(20, 45, "WiFi not connected", C_RED, C_BG, 1)
        txt(20, 70, "Go to WiFi page first", C_GREY, C_BG, 1)
    else:
        if WEATHER_API_KEY == "":
            txt(10, 35, "Weather API key missing", C_RED, C_BG, 1)
            txt(10, 60, "Set WEATHER_API_KEY first", C_GREY, C_BG, 1)
        elif weather_fetched:
            txt(20, 20, "Outdoor: " + str(weather_temp) + "C", C_YELLOW, C_BG, 1)
            txt(20, 40, "Weather: " + str(weather_desc), C_WHITE, C_BG, 1)
            txt(20, 60, "Humidity: " + str(weather_humidity), C_CYAN, C_BG, 1)
            weather_warn, warn_color = get_weather_warning()
            txt(10, 82, weather_warn, warn_color, C_BG, 1)
            temp_warn, temp_color = get_temp_warning()
            txt(10, 102, temp_warn, temp_color, C_BG, 1)
        else:
            txt(55, 50, "No data", C_GREY, C_BG, 2)
            txt(20, 85, "Double click to fetch", C_GREY, C_BG, 1)

    bar_bot("A:next  Dbl:refresh")


def update_weather():
    if page != 7:
        return
    if not wifi_connected or not weather_fetched:
        return
    M5.Lcd.fillRect(0, 18, SW, 100, C_BG)
    txt(20, 20, "Outdoor: " + str(weather_temp) + "C", C_YELLOW, C_BG, 1)
    txt(20, 40, "Weather: " + str(weather_desc), C_WHITE, C_BG, 1)
    txt(20, 60, "Humidity: " + str(weather_humidity), C_CYAN, C_BG, 1)
    weather_warn, warn_color = get_weather_warning()
    txt(10, 82, weather_warn, warn_color, C_BG, 1)
    temp_warn, temp_color = get_temp_warning()
    txt(10, 102, temp_warn, temp_color, C_BG, 1)


def fetch_weather():
    global weather_temp, weather_desc, weather_humidity, last_weather_update, weather_fetched

    if not refresh_wifi_state():
        print("fetch_weather: wifi not connected")
        weather_fetched = False
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
                now_data = data["results"][0]["now"]
                weather_temp = now_data.get("temperature", "--")
                weather_desc = now_data.get("text", "--")
                weather_humidity = now_data.get("humidity", "--")
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
        except Exception:
            pass


# =========================
# SETUP
# =========================
def setup():
    global rtc_0, wifi_last_try_ms

    M5.begin()
    M5.Lcd.setRotation(3)
    M5.Lcd.setBrightness(100)

    rtc_0 = RTC()

    init_env_sensor()
    init_wifi()

    # 按老师 block 的思路：开机直接 active(True) 后 connect()
    start_wifi_connect_block_style()

    cls()
    txt(55, 35, "CuteWatch", C_CYAN, C_BG, 2)
    txt(18, 70, "WiFi auto connecting...", C_YELLOW, C_BG, 1)
    txt(24, 92, "Time will sync after IP", C_GREY, C_BG, 1)
    wifi_last_try_ms = time.ticks_ms()
    time.sleep(1.2)


# =========================
# LOOP
# =========================
def loop():
    global page, pomo_time, pomo_last, pomo_running, pomo_mode
    global last_weather_update, water_alert_pending, wifi_last_try_ms

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
    ntp_done = False

    while True:
        M5.update()

        # 后台自动等待 WiFi 成功，成功后自动同步时间
        refresh_wifi_state()
        if wifi_connected and not ntp_done:
            sync_ntp()
            ntp_done = True

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
                        connect_wifi_wait()
                        ntp_done = False
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
                if wifi_connected and not weather_fetched and WEATHER_API_KEY != "":
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
                update_wifi_signal()
            elif page == 7:
                refresh_wifi_state()
                if wifi_connected and WEATHER_API_KEY != "":
                    if time.time() - last_weather_update > weather_update_interval:
                        fetch_weather()
                update_weather()
            last_draw = time.ticks_ms()

        time.sleep_ms(50)


# =========================
# RUN
# =========================
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
        except Exception:
            pass
