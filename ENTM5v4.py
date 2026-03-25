import M5
from M5 import *
from hardware import *
from machine import RTC, I2C, Pin
from unit import ENVUnit
import time

SW = 240
SH = 135

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
NUM_PAGES = 5
page = 0

rtc_0 = None
i2c0 = None
env_0 = None
env_ready = False

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
        ts = time.time() + TIMEZONE_OFFSET * 3600
        y, mo, d, hh, mm, ss, wd, yd = time.localtime(ts)
        return y, mo, d, wd, hh, mm, ss
    except Exception as e:
        print("get_time error:", e)
        return 2026, 3, 22, 0, 12, 0, 0


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


def beep_end():
    """倒计时结束专用蜂鸣：三长声提醒"""
    try:
        Speaker.tone(2600, 400)
        time.sleep_ms(500)
        Speaker.tone(2600, 400)
        time.sleep_ms(500)
        Speaker.tone(3000, 600)
    except Exception as e:
        print("beep_end error:", e)


# =========================
# CLOCK  (局部刷新，不闪烁)
# =========================
_clock_last_hms = None   # 记录上一次绘制的 hh:mm:ss，避免重复渲染
_clock_inited  = False   # 是否已经画过静态部分

def draw_clock_static():
    """只在首次进入时钟页面时绘制不变的静态部分"""
    global _clock_inited
    cls()
    yr, mo, dy, wd, hr, mn, sc = get_time()

    # 日期框（静态）
    M5.Lcd.fillRect(20, 65, 200, 35, C_DKGREY)
    M5.Lcd.drawRect(20, 65, 200, 35, C_CYAN)
    month_str = "{:02d}".format(mo)
    day_str   = "{:02d}".format(dy)
    year_str  = str(yr)
    txt(35,  72, month_str, C_YELLOW, C_DKGREY, 2)
    txt(85,  75, "/",       C_CYAN,   C_DKGREY, 1)
    txt(100, 72, day_str,   C_GREEN,  C_DKGREY, 2)
    txt(150, 75, "/",       C_CYAN,   C_DKGREY, 1)
    txt(165, 75, year_str,  C_GREY,   C_DKGREY, 1)

    _clock_inited = True


def draw_clock_realtime():
    global _clock_last_hms, _clock_inited

    yr, mo, dy, wd, hr, mn, sc = get_time()

    # 首次进入或切换回来时，先画静态部分
    if not _clock_inited:
        draw_clock_static()

    hms = (hr, mn, sc)
    if hms == _clock_last_hms:
        return   # 秒数没变就不重绘，彻底消除闪烁
    _clock_last_hms = hms

    # 只擦掉时间数字区域，局部刷新
    M5.Lcd.fillRect(0, 18, SW, 45, C_BG)
    t = "{:02d}:{:02d}:{:02d}".format(hr, mn, sc)
    M5.Lcd.setTextColor(C_CYAN, C_BG)
    M5.Lcd.setTextSize(3)
    w = len(t) * 18
    M5.Lcd.setCursor((SW - w) // 2, 22)
    M5.Lcd.print(t)

    # ENV 传感器（每秒刷新一次，局部区域）
    t_env, h_env, _ = read_env()
    M5.Lcd.fillRect(0, 107, SW, 28, C_BG)
    if t_env is not None:
        M5.Lcd.setTextColor(C_CYAN, C_BG)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(10, 113)
        M5.Lcd.print("T:{:.1f}C  H:{:.1f}%".format(t_env, h_env))
    else:
        txt(60, 113, "Sensor Error", C_RED, C_BG, 1)


# =========================
# CALENDAR
# =========================
DAYS_IN_MONTH = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
WEEKDAY_NAMES = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
MONTH_NAMES = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def is_leap(yr):
    return (yr % 4 == 0 and yr % 100 != 0) or (yr % 400 == 0)

def days_in_month(yr, mo):
    if mo == 2 and is_leap(yr):
        return 29
    return DAYS_IN_MONTH[mo]

def weekday_of(yr, mo, day):
    # Zeller 公式，返回 0=Mon .. 6=Sun（与 MicroPython time.localtime 一致）
    if mo < 3:
        mo += 12
        yr -= 1
    k = yr % 100
    j = yr // 100
    h = (day + (13 * (mo + 1)) // 5 + k + k // 4 + j // 4 - 2 * j) % 7
    # h: 0=Sat,1=Sun,2=Mon...6=Fri → 转成 0=Mon..6=Sun
    return (h + 5) % 7

def draw_calendar():
    cls()
    yr, mo, dy, wd, hr, mn, sc = get_time()

    # ── 顶部标题：月份 + 年份
    M5.Lcd.fillRect(0, 0, SW, 18, C_DKGREY)
    title = "{} {}".format(MONTH_NAMES[mo], yr)
    txt(6, 4, title, C_CYAN, C_DKGREY, 1)

    # ── 星期行
    col_w = 34          # 每列宽度
    row_start = 20      # 星期行 y
    for i, name in enumerate(WEEKDAY_NAMES):
        x = i * col_w + 2
        c = C_RED if i >= 5 else C_GREY   # 周六日红色
        txt(x, row_start, name, c, C_BG, 1)

    # ── 日期格子
    first_wd = weekday_of(yr, mo, 1)   # 本月 1 号是周几(0=Mon)
    total    = days_in_month(yr, mo)
    col      = first_wd
    row      = 0
    row_h    = 18       # 行高
    y_off    = 32       # 日期区域起始 y

    for day in range(1, total + 1):
        x = col * col_w + 2
        y = y_off + row * row_h

        if day == dy:
            # 今天：青色高亮圆角背景
            M5.Lcd.fillRect(x - 1, y - 1, 20, 14, C_CYAN)
            txt(x, y, "{:2d}".format(day), C_BG, C_CYAN, 1)
        else:
            c = C_RED if col >= 5 else C_WHITE
            txt(x, y, "{:2d}".format(day), c, C_BG, 1)

        col += 1
        if col > 6:
            col = 0
            row += 1

    # ── 底部：今天是星期几
    DAY_FULL = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    M5.Lcd.fillRect(0, SH - 16, SW, 16, C_DKGREY)
    today_label = "Today: " + DAY_FULL[wd]
    txt(6, SH - 12, today_label, C_YELLOW, C_DKGREY, 1)


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
    yr, mo, dy, wd, hr, mn, sc = get_time()
    now_mins = hr * 60 + mn  # 当前时间（分钟数）

    # ── 顶部标题栏
    M5.Lcd.fillRect(0, 0, SW, 20, 0x001A33)
    M5.Lcd.setTextColor(C_CYAN, 0x001A33)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setCursor(8, 6)
    M5.Lcd.print("SCHEDULE")
    # 右侧显示当前时间
    M5.Lcd.setTextColor(C_YELLOW, 0x001A33)
    now_str = "NOW {:02d}:{:02d}".format(hr, mn)
    M5.Lcd.setCursor(SW - len(now_str) * 6 - 6, 6)
    M5.Lcd.print(now_str)

    # ── 找出当前和下一个事项
    current_idx = -1
    for i in range(len(schedule) - 1):
        s_mins = schedule[i][0] * 60 + schedule[i][1]
        n_mins = schedule[i + 1][0] * 60 + schedule[i + 1][1]
        if s_mins <= now_mins < n_mins:
            current_idx = i
            break

    # ── 绘制事项列表
    ICONS = [">", "*", "~", "#", "+", "@", "z"]
    y = 22
    row_h = 16
    for i, s in enumerate(schedule):
        s_mins = s[0] * 60 + s[1]
        is_current = (i == current_idx)
        is_past = (s_mins < now_mins) and (i != current_idx)

        if is_current:
            # 当前事项：高亮背景
            M5.Lcd.fillRect(0, y, SW, row_h - 1, 0x002244)
            M5.Lcd.drawRect(0, y, SW, row_h - 1, C_CYAN)
            time_col = C_CYAN
            text_col = C_WHITE
            icon = ">>>"
        elif is_past:
            # 已过去：灰暗
            time_col = 0x444444
            text_col = 0x444444
            icon = " - "
        else:
            # 未来
            time_col = C_YELLOW
            text_col = C_WHITE
            icon = ICONS[i % len(ICONS)]

        # 时间
        M5.Lcd.setTextColor(time_col, 0x002244 if is_current else C_BG)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(4, y + 4)
        M5.Lcd.print("{:02d}:{:02d}".format(s[0], s[1]))

        # 图标
        M5.Lcd.setTextColor(C_CYAN if is_current else (0x444444 if is_past else C_GREEN), 0x002244 if is_current else C_BG)
        M5.Lcd.setCursor(52, y + 4)
        M5.Lcd.print(icon)

        # 事项名
        M5.Lcd.setTextColor(text_col, 0x002244 if is_current else C_BG)
        M5.Lcd.setCursor(76, y + 4)
        M5.Lcd.print(s[2])

        y += row_h

    # ── 底部提示栏
    M5.Lcd.fillRect(0, SH - 14, SW, 14, 0x001A33)
    M5.Lcd.setTextColor(C_GREY, 0x001A33)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setCursor(6, SH - 10)
    M5.Lcd.print("A:next")


# =========================
# ENV 页面
# =========================
def draw_env():
    cls()

    # ── 顶部标题栏
    M5.Lcd.fillRect(0, 0, SW, 20, 0x003344)
    M5.Lcd.setTextColor(C_CYAN, 0x003344)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setCursor(8, 6)
    M5.Lcd.print("ENV III  SENSOR")
    # 右侧小装饰点（用 fillRect 兼容 UIFlow2）
    M5.Lcd.fillRect(223, 7, 5, 5, C_CYAN)
    M5.Lcd.fillRect(230, 7, 5, 5, 0x006688)

    t, h, p = read_env()

    if t is not None:
        # ══════════════════════════════
        # 温度卡片
        # ══════════════════════════════
        M5.Lcd.fillRect(4, 24, 112, 50, 0x001A2A)
        M5.Lcd.drawRect(4, 24, 112, 50, C_CYAN)
        # 标签
        M5.Lcd.setTextColor(C_CYAN, 0x001A2A)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(10, 29)
        M5.Lcd.print("TEMP")
        # 数值（大字）
        M5.Lcd.setTextColor(C_WHITE, 0x001A2A)
        M5.Lcd.setTextSize(2)
        M5.Lcd.setCursor(10, 43)
        M5.Lcd.print("{:.1f}".format(t))
        # 单位
        M5.Lcd.setTextColor(C_CYAN, 0x001A2A)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(80, 46)
        M5.Lcd.print("deg C")

        # ══════════════════════════════
        # 湿度卡片
        # ══════════════════════════════
        M5.Lcd.fillRect(122, 24, 112, 50, 0x001A2A)
        M5.Lcd.drawRect(122, 24, 112, 50, 0x44AAFF)
        # 标签
        M5.Lcd.setTextColor(0x44AAFF, 0x001A2A)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(128, 29)
        M5.Lcd.print("HUMID")
        # 数值（大字）
        M5.Lcd.setTextColor(C_WHITE, 0x001A2A)
        M5.Lcd.setTextSize(2)
        M5.Lcd.setCursor(128, 43)
        M5.Lcd.print("{:.1f}".format(h))
        # 单位
        M5.Lcd.setTextColor(0x44AAFF, 0x001A2A)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(196, 46)
        M5.Lcd.print("%")

        # ══════════════════════════════
        # 压强卡片（宽幅，底部）
        # ══════════════════════════════
        M5.Lcd.fillRect(4, 80, 230, 42, 0x1A1A00)
        M5.Lcd.drawRect(4, 80, 230, 42, C_YELLOW)
        # 标签
        M5.Lcd.setTextColor(C_YELLOW, 0x1A1A00)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(10, 84)
        M5.Lcd.print("PRESSURE")
        # 数值（大字）
        M5.Lcd.setTextColor(C_WHITE, 0x1A1A00)
        M5.Lcd.setTextSize(2)
        M5.Lcd.setCursor(10, 97)
        if p is not None:
            M5.Lcd.print("{:.1f}".format(p))
            M5.Lcd.setTextColor(C_YELLOW, 0x1A1A00)
            M5.Lcd.setTextSize(1)
            M5.Lcd.setCursor(148, 102)
            M5.Lcd.print("hPa")
        else:
            M5.Lcd.setTextColor(C_GREY, 0x1A1A00)
            M5.Lcd.print("N / A")

    else:
        # 传感器错误提示
        M5.Lcd.fillRect(30, 45, 180, 50, 0x220000)
        M5.Lcd.drawRect(30, 45, 180, 50, C_RED)
        txt(52, 58, "Sensor Error", C_RED, 0x220000, 1)
        txt(38, 76, "Check connection", C_GREY, 0x220000, 1)

    # ── 底部提示栏
    M5.Lcd.fillRect(0, SH - 14, SW, 14, 0x003344)
    M5.Lcd.setTextColor(C_GREY, 0x003344)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setCursor(6, SH - 10)
    M5.Lcd.print("A:next")


# =========================
# POMODORO
# =========================
_pomo_inited = False   # 是否已画过番茄钟静态部分
_pomo_last_mode = None # 上次绘制时的模式，模式切换时重绘静态


def draw_pomodoro_static():
    """只在首次进入或模式切换时绘制不变的静态部分"""
    global _pomo_inited, _pomo_last_mode
    is_work = pomo_mode == "WORK"
    bg_accent = 0x2A0000 if is_work else 0x002A0A
    border_col = C_RED if is_work else C_GREEN

    cls()

    # ── 顶部标题栏
    M5.Lcd.fillRect(0, 0, SW, 20, 0x1A1A1A)
    M5.Lcd.setTextColor(C_GREY, 0x1A1A1A)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setCursor(8, 6)
    M5.Lcd.print("POMODORO TIMER")
    M5.Lcd.setTextColor(C_RED, 0x1A1A1A)
    M5.Lcd.setCursor(194, 6)
    M5.Lcd.print("(o^.^o)")

    # ── 模式标签卡片
    M5.Lcd.fillRect(55, 23, 130, 22, bg_accent)
    M5.Lcd.drawRect(55, 23, 130, 22, border_col)
    mode_label = "(>_<)  WORK" if is_work else "(^_^)  BREAK"
    M5.Lcd.setTextColor(border_col, bg_accent)
    M5.Lcd.setTextSize(1)
    lx = 55 + (130 - len(mode_label) * 6) // 2
    M5.Lcd.setCursor(lx, 30)
    M5.Lcd.print(mode_label)

    # ── 倒计时边框（不含数字，数字由局部刷新填写）
    M5.Lcd.fillRect(20, 50, 200, 46, bg_accent)
    M5.Lcd.drawRect(20, 50, 200, 46, border_col)
    M5.Lcd.fillRect(24, 52, 2, 42, border_col)
    M5.Lcd.fillRect(213, 52, 2, 42, border_col)

    # ── 底部提示栏
    M5.Lcd.fillRect(0, SH - 14, SW, 14, 0x1A1A1A)
    M5.Lcd.setTextColor(C_GREY, 0x1A1A1A)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setCursor(6, SH - 10)
    M5.Lcd.print("A:next   DblClick:start/pause")

    _pomo_inited = True
    _pomo_last_mode = pomo_mode


def draw_pomodoro():
    global _pomo_inited, _pomo_last_mode
    is_work = pomo_mode == "WORK"
    bg_accent = 0x2A0000 if is_work else 0x002A0A

    # 首次进入或模式切换时重绘静态部分
    if not _pomo_inited or _pomo_last_mode != pomo_mode:
        draw_pomodoro_static()

    # ── 局部刷新：只更新倒计时数字
    m = pomo_time // 60
    s = pomo_time % 60
    ts = "{:02d}:{:02d}".format(m, s)
    # 只擦掉数字区域（边框内侧），不动边框
    M5.Lcd.fillRect(27, 53, 183, 40, bg_accent)
    M5.Lcd.setTextColor(C_WHITE, bg_accent)
    M5.Lcd.setTextSize(3)
    w = len(ts) * 18
    M5.Lcd.setCursor((SW - w) // 2, 57)
    M5.Lcd.print(ts)

    # ── 局部刷新：状态行
    M5.Lcd.fillRect(0, 100, SW, 21, 0x111111)
    if pomo_running:
        status_icon = "[ * Running * ]"
        status_col  = C_GREEN
    else:
        status_icon = "[ || Paused  ]"
        status_col  = C_YELLOW
    M5.Lcd.setTextColor(status_col, 0x111111)
    M5.Lcd.setTextSize(1)
    sx = (SW - len(status_icon) * 6) // 2
    M5.Lcd.setCursor(sx, 107)
    M5.Lcd.print(status_icon)


# =========================
# SETUP
# =========================
def setup():
    global rtc_0

    M5.begin()
    M5.Lcd.setRotation(3)
    M5.Lcd.setBrightness(100)

    rtc_0 = RTC()
    init_env_sensor()

    cls()
    txt(55, 35, "CuteWatch", C_CYAN, C_BG, 2)
    txt(30, 70, "Initializing...", C_YELLOW, C_BG, 1)
    time.sleep(1)


# =========================
# LOOP
# =========================
def loop():
    global page, pomo_time, pomo_last, pomo_running, pomo_mode
    global _clock_inited, _clock_last_hms, _pomo_inited

    pages = [
        draw_clock_realtime,
        draw_calendar,
        draw_schedule,
        draw_env,
        draw_pomodoro
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

            else:
                waiting_double = True
                last_btn_press = now_ms

        if waiting_double and time.ticks_diff(time.ticks_ms(), last_btn_press) > double_click_threshold:
            waiting_double = False
            page = (page + 1) % NUM_PAGES
            if page == 0:
                # 切回时钟页时重置静态标志，触发完整重绘
                _clock_inited = False
                _clock_last_hms = None
                draw_clock_realtime()  # 立即刷新，不等 1 秒
            if page == 4:
                # 切入番茄钟页时重置静态标志，触发完整重绘
                _pomo_inited = False
            pages[page]()

        if pomo_running and time.time() - pomo_last >= 1:
            pomo_last = time.time()
            pomo_time -= 1
            if pomo_time <= 0:
                # 倒计时结束：蜂鸣提醒
                pomo_running = False
                beep_end()
                if pomo_mode == "WORK":
                    pomo_mode = "BREAK"
                    pomo_time = BREAK_TIME
                else:
                    pomo_mode = "WORK"
                    pomo_time = WORK_TIME
            # 番茄钟页面每秒实时刷新倒计时
            if page == 4:
                draw_pomodoro()

        if time.ticks_diff(time.ticks_ms(), last_draw) > 1000:
            last_draw = time.ticks_ms()
            # 无论在哪个页面，时钟都在后台持续走
            # 只有在时钟页面时才刷新 LCD 显示
            if page == 0:
                draw_clock_realtime()
            else:
                # 后台静默更新时间状态，保持 _clock_last_hms 同步
                yr, mo, dy, wd, hr, mn, sc = get_time()
                _clock_last_hms = (hr, mn, sc)

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
