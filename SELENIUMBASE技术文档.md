# SeleniumBase 技术文档

> 基于项目 `seleniumbase-test` 实际用法整理，涵盖配置参数、常用操作、验证码处理及 CI/CD 集成。

---

## 目录

1. [简介](#1-简介)
2. [安装与环境](#2-安装与环境)
3. [配置参数详解](#3-配置参数详解)
4. [常用操作 API](#4-常用操作-api)
5. [Cloudflare Turnstile 验证码处理](#5-cloudflare-turnstile-验证码处理)
6. [截图与日志](#6-截图与日志)
7. [GitHub Actions CI/CD 集成](#7-github-actions-cicd-集成)
8. [最佳实践与避坑](#8-最佳实践与避坑)

---

## 1. 简介

[SeleniumBase](https://seleniumbase.io/) 是一个基于 Selenium 的全栈 Web 自动化测试框架，封装了大量实用方法，支持：

- 自动化网页操作（点击、输入、等待等）
- Undetected Chromedriver（UC 模式），绕过 Cloudflare 等反爬检测
- 多种浏览器（Chrome、Edge、Firefox 等）
- 无头模式 / 有头模式
- 截图、JS 执行、Cookie 管理等
- 集成测试框架（pytest）

本项目使用 SeleniumBase 实现网站自动登录 + Cloudflare Turnstile 验证 + 业务操作。

---

## 2. 安装与环境

### 2.1 Python 依赖

```bash
pip install seleniumbase requests
```

### 2.2 Linux 无头运行依赖（xvfb）

在无图形界面的 Linux 服务器（如 GitHub Actions）上运行时，需要安装 `xvfb` 提供虚拟显示：

```bash
sudo apt-get update && sudo apt-get install -y xvfb
```

> 说明：即使使用 `headed=False` 无头模式，Chrome/Chromium 在 Linux 上仍可能需要 Xvfb 来初始化图形上下文。

### 2.3 浏览器驱动

SeleniumBase 会自动下载和管理 Chromedriver，无需手动配置。使用 `uc=True` 时会自动使用 Undetected Chromedriver。

---

## 3. 配置参数详解

SeleniumBase 通过 `SB(**kwargs)` 上下文管理器创建浏览器实例，所有参数以关键字传入。

### 3.1 项目中使用的配置

```python
from seleniumbase import SB

SB_KWARGS = {
    'uc': True,                              # 启用 Undetected Chromedriver 模式
    'test': True,                            # 测试模式（自动处理弹窗等）
    'locale': 'en',                          # 浏览器语言环境
    'headed': False,                         # 无头模式（不显示浏览器窗口）
    'user_data_dir': None,                   # 用户数据目录（None = 临时目录）
    'chromium_arg': '--disable-blink-features=AutomationControlled'  # 隐藏自动化特征
}

with SB(**SB_KWARGS) as sb:
    # 自动化操作...
    pass
```

### 3.2 关键参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `uc` | bool | `False` | 启用 Undetected Chromedriver，绕过反爬检测（Cloudflare 等） |
| `headed` | bool | `False` | `True`=显示浏览器窗口（调试用）；`False`=无头模式（CI/生产） |
| `locale_code` / `locale` | str | 系统默认 | 浏览器语言，如 `'en'`、`'zh-CN'` |
| `user_data_dir` | str/None | `None` | Chrome 用户数据目录，用于持久化 Cookie/登录态；`None` 则每次用临时目录 |
| `chromium_arg` | str | 无 | 传递给 Chromium 的启动参数，可多次使用列表 |
| `test` | bool | `False` | 测试模式，自动关闭弹窗、处理 alert |
| `browser` | str | `'chrome'` | 浏览器类型：`chrome`、`edge`、`firefox` 等 |
| `headless` | bool | `False` | 另一种无头模式写法（与 `headed` 相反） |
| `window_size` | str | 无 | 窗口大小，如 `'1920,1080'` |
| `incognito` | bool | `False` | 无痕模式 |
| `guest` | bool | `False` | Guest 模式 |
| `agent` | str | 无 | 自定义 User-Agent |
| `proxy` | str | 无 | 代理，如 `'http://user:pass@host:port'` |
| `no_sandbox` | bool | `False` | Linux root 环境需要设为 `True` |
| `disable_dev_shm_usage` | bool | `False` | CI 环境建议开启，防止 /dev/shm 不足 |

### 3.3 反检测相关参数

绕过 Cloudflare 等检测时，推荐组合：

```python
SB_KWARGS = {
    'uc': True,
    'headed': False,
    'chromium_arg': [
        '--disable-blink-features=AutomationControlled',
        '--disable-infobars',
        '--no-sandbox',
        '--disable-dev-shm-usage',
    ],
    'locale': 'en',
}
```

---

## 4. 常用操作 API

以下所有方法均通过 `sb` 实例调用。

### 4.1 页面导航

| 方法 | 说明 | 示例 |
|------|------|------|
| `sb.open(url)` | 打开 URL | `sb.open('https://example.com')` |
| `sb.uc_open(url)` | UC 模式打开（带重连机制） | `sb.uc_open('https://example.com')` |
| `sb.uc_open_with_reconnect(url, reconnect_time=5)` | UC 打开并重连等待（反爬关键） | 见下方示例 |
| `sb.get_current_url()` | 获取当前页面 URL | `url = sb.get_current_url()` |
| `sb.go_back()` | 后退 | `sb.go_back()` |
| `sb.go_forward()` | 前进 | `sb.go_forward()` |
| `sb.refresh()` | 刷新页面 | `sb.refresh()` |

**UC 模式打开页面（反爬推荐）：**

```python
sb.uc_open_with_reconnect('https://betadash.lunes.host/login', reconnect_time=5)
```

> `reconnect_time` 表示打开页面后等待的秒数，让页面充分加载并完成 Cloudflare 挑战。

### 4.2 等待操作

| 方法 | 说明 |
|------|------|
| `sb.wait_for_ready_state_complete(timeout=30)` | 等待页面 `document.readyState` 为 `complete` |
| `sb.wait_for_element_visible(selector, timeout=10)` | 等待元素可见 |
| `sb.wait_for_element_present(selector, timeout=10)` | 等待元素出现在 DOM 中 |
| `sb.wait_for_element_clickable(selector, timeout=10)` | 等待元素可点击 |
| `sb.wait_for_element_absent(selector, timeout=10)` | 等待元素消失 |
| `sb.sleep(seconds)` | 休眠（`sb` 的 sleep 会自动处理） |

**示例：**

```python
# 等待页面加载完成
sb.wait_for_ready_state_complete()

# 等待邮箱输入框可见
sb.wait_for_element_visible('input[type="email"]', timeout=10)
```

### 4.3 元素定位与交互

| 方法 | 说明 | 示例 |
|------|------|------|
| `sb.click(selector)` | 点击元素 | `sb.click('button[type=submit]')` |
| `sb.press_keys(selector, text)` | 向元素输入文本 | `sb.press_keys('input[type="email"]', email)` |
| `sb.type(selector, text)` | 输入文本（先清空） | `sb.type('#username', 'admin')` |
| `sb.update_text(selector, text)` | 更新文本内容 | `sb.update_text('#msg', 'hello')` |
| `sb.clear(selector)` | 清空输入框 | `sb.clear('input[type="email"]')` |
| `sb.select_option_by_text(selector, text)` | 下拉框选文本 | `sb.select_option_by_text('#country', 'China')` |
| `sb.select_option_by_value(selector, value)` | 下拉框选值 | `sb.select_option_by_value('#city', 'BJ')` |
| `sb.get_text(selector)` | 获取元素文本 | `text = sb.get_text('h1')` |
| `sb.get_attribute(selector, attr)` | 获取属性 | `val = sb.get_attribute('#id', 'value')` |
| `sb.is_element_visible(selector)` | 元素是否可见 | `if sb.is_element_visible('.error'):` |
| `sb.is_element_present(selector)` | 元素是否存在 | `if sb.is_element_present('#login'):` |

**选择器支持：** CSS 选择器、XPath、SeleniumBase 简化语法（如 `'#id'`、`'.class'`、`'tag'`）。

**输入文本示例：**

```python
# 填写邮箱
sb.press_keys('input[type="email"]', email)
# 填写密码
sb.press_keys('input[type="password"]', password)
# 点击提交
sb.click('button[type=submit]')
```

### 4.4 JavaScript 执行

| 方法 | 说明 |
|------|------|
| `sb.execute_script(script, *args)` | 执行 JS 并返回结果 |
| `sb.execute_async_script(script, *args)` | 执行异步 JS |

**示例 — 检测 Turnstile 验证状态：**

```python
success = sb.execute_script('''
    var resp = document.querySelector('input[name="cf-turnstile-response"]');
    if (resp && resp.value && resp.value.length > 20) return true;
    var grecap = document.querySelector('textarea[name="g-recaptcha-response"]');
    if (grecap && grecap.value && grecap.value.length > 20) return true;
    var iframe = document.querySelector('iframe[src*="challenges.cloudflare.com"]');
    if (iframe && iframe.getAttribute("data-state") === "solved") return true;
    return false;
''')
```

### 4.5 Cookie 与会话

| 方法 | 说明 |
|------|------|
| `sb.get_cookies()` | 获取所有 Cookie |
| `sb.get_cookie(name)` | 获取指定 Cookie |
| `sb.add_cookie(cookie_dict)` | 添加 Cookie |
| `sb.delete_cookie(name)` | 删除指定 Cookie |
| `sb.delete_all_cookies()` | 删除所有 Cookie |
| `sb.save_cookies(name)` | 保存 Cookie 到文件 |
| `sb.load_cookies(name)` | 从文件加载 Cookie |

### 4.6 截图

| 方法 | 说明 | 示例 |
|------|------|------|
| `sb.save_screenshot(filename)` | 保存截图 | `sb.save_screenshot('login.png')` |
| `sb.get_screenshot_as_png()` | 获取截图二进制 | `data = sb.get_screenshot_as_png()` |

**封装的安全截图函数：**

```python
ALLOW_SCREENSHOT = False

def safe_screenshot(sb, filename: str):
    if not ALLOW_SCREENSHOT:
        return
    try:
        sb.save_screenshot(filename)
    except Exception as e:
        print(f"截图失败: {e}")
```

> CI 环境中可关闭截图以减少 artifacts 体积，调试时设为 `True`。

---

## 5. Cloudflare Turnstile 验证码处理

### 5.1 UC 模式自动处理

启用 `uc=True` 后，SeleniumBase 提供专门的验证码处理方法：

| 方法 | 说明 |
|------|------|
| `sb.uc_gui_click_captcha()` | 点击验证码（如 Turnstile 复选框） |
| `sb.uc_gui_handle_captcha()` | 尝试自动处理整个验证码流程 |
| `sb.uc_click(selector)` | UC 模式的安全点击（绕过检测） |

### 5.2 项目中的处理流程

```python
def wait_for_turnstile_success(sb, timeout: int = 30) -> bool:
    """轮询检测 Turnstile 验证是否成功"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            success = sb.execute_script('''
                var resp = document.querySelector('input[name="cf-turnstile-response"]');
                if (resp && resp.value && resp.value.length > 20) return true;
                var iframe = document.querySelector('iframe[src*="challenges.cloudflare.com"]');
                if (iframe && iframe.getAttribute("data-state") === "solved") return true;
                return false;
            ''')
            if success:
                return True
        except:
            pass
        time.sleep(1)
    return False

def handle_captcha(sb):
    # 先等待自动完成（UC 模式可能自动通过）
    if wait_for_turnstile_success(sb, timeout=5):
        return
    # 自动点击验证码
    for click_attempt in range(3):
        sb.uc_gui_click_captcha()
        time.sleep(2)
        if wait_for_turnstile_success(sb, timeout=10):
            break
    else:
        # 兜底：强制处理
        sb.uc_gui_handle_captcha()
```

### 5.3 Turnstile 成功判断依据

1. `input[name="cf-turnstile-response"]` 有值且长度 > 20
2. Cloudflare iframe 的 `data-state` 属性为 `"solved"`
3. `textarea[name="g-recaptcha-response"]` 有值（兼容 reCAPTCHA）

---

## 6. 截图与日志

### 6.1 日志配置

项目使用 Python 标准 `logging`，配置时区为东八区（+0800）：

```python
import logging
from datetime import datetime, timedelta, timezone

def setup_logging(logfile: str = 'history.log'):
    class TimezoneFormatter(logging.Formatter):
        def __init__(self, fmt=None, datefmt=None, tz_offset=0):
            super().__init__(fmt=fmt, datefmt=datefmt)
            self.tz = timezone(timedelta(hours=tz_offset))
        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created, self.tz)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S %z')

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = TimezoneFormatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s', tz_offset=8
    )
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    # 文件输出
    file_handler = logging.FileHandler(logfile, 'w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logging()
```

### 6.2 通知集成（Telegram）

```python
import requests, os

def tg_message(msg):
    try:
        TG_API = os.getenv('TG_API')
        requests.post(TG_API, data=msg)
    except Exception as e:
        logger.info(f"TG通知失败：{e}")
```

> `TG_API` 为 Telegram Bot API 的完整 URL（含 chat_id），通过环境变量传入。

---

## 7. GitHub Actions CI/CD 集成

### 7.1 完整工作流示例

```yaml
name: SB测试

on:
  schedule:
    - cron: '0 6 * * 3'    # 每周三 06:00 UTC
  workflow_dispatch: null   # 支持手动触发

permissions:
  contents: write

jobs:
  seleniumbase:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7

      - name: 配置Python环境
        uses: actions/setup-python@v7
        with:
          python-version: "3.11"

      - name: 安装SeleniumBase
        run: |
          sudo apt-get update && sudo apt-get install -y xvfb
          pip3 install seleniumbase requests

      - name: 执行脚本
        run: python3 sb_test.py

      - name: 保存调试截图
        uses: actions/upload-artifact@v7
        with:
          name: screenshots-SB
          path: ./*.png
          retention-days: 3
```

### 7.2 关键要点

1. **必须安装 xvfb**：Linux 无 GUI 环境下 Chrome 运行需要虚拟显示。
2. **无头模式**：CI 中 `headed=False`。
3. **截图上传**：通过 `actions/upload-artifact` 保存 PNG 截图便于排查。
4. **环境变量**：敏感信息（如 `TG_API`、账号密码）通过 `secrets` 或 `vars` 传入。

### 7.3 通过仓库变量管理账号

```yaml
- name: 更新账号数据
  env:
    GH_TOKEN: ${{ secrets.WORKFLOW }}
    ACCOUNTS: ${{ vars.ACCOUNTS_BAK }}
  run: |
    gh variable set ACCOUNTS --body "$ACCOUNTS"
```

---

## 8. 最佳实践与避坑

### 8.1 反检测

- **必须使用 `uc=True`**：普通 Chromedriver 容易被 Cloudflare 识别。
- **使用 `uc_open_with_reconnect`**：带重连的打开方式更稳定。
- **添加 `--disable-blink-features=AutomationControlled`**：隐藏 `navigator.webdriver` 特征。
- **设置 `locale='en'`**：部分站点对非英语环境更敏感。

### 8.2 稳定性

- **多用 `wait_for_*` 方法**，少用 `time.sleep()`。
- **操作后调用 `wait_for_ready_state_complete()`** 确保页面就绪。
- **关键步骤加 try/except**，避免单点失败导致全流程崩溃。
- **合理设置 timeout**，不要过大导致调试困难。

### 8.3 资源管理

- 使用 `with SB(...) as sb:` 上下文管理器，确保浏览器自动关闭。
- CI 中关闭非必要截图，控制 artifact 大小。
- `user_data_dir=None` 时每次启动为干净环境，适合无状态任务。

### 8.4 调试技巧

- 本地调试时设 `headed=True` 观察浏览器行为。
- 截图命名带步骤编号（如 `0-Homepage.png`、`1-Account.png`）便于时序排查。
- 日志中记录关键 URL 和操作结果。

### 8.5 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| Cloudflare 验证卡住 | 未用 UC 模式 | 设 `uc=True`，用 `uc_open_with_reconnect` |
| Linux 上 Chrome 崩溃 | 缺少 Xvfb 或 /dev/shm 不足 | 安装 xvfb，加 `--no-sandbox --disable-dev-shm-usage` |
| 元素定位失败 | 元素未加载或在 iframe 内 | 用 `wait_for_element_visible`，必要时 `sb.switch_to_frame()` |
| `uc_gui_click_captcha` 报错 | 验证码 iframe 未加载 | 先等待 iframe 出现，再重试 |
| 登录态丢失 | `user_data_dir=None` | 指定持久化目录或用 Cookie 文件 |

---

## 附录：完整登录流程示例

```python
from seleniumbase import SB
import time

SB_KWARGS = {
    'uc': True,
    'test': True,
    'locale': 'en',
    'headed': False,
    'user_data_dir': None,
    'chromium_arg': '--disable-blink-features=AutomationControlled'
}

def login(sb, email, password):
    # 1. 打开登录页
    sb.uc_open_with_reconnect('https://example.com/login', reconnect_time=5)
    sb.wait_for_ready_state_complete()

    # 2. 填写表单
    sb.wait_for_element_visible('input[type="email"]', timeout=10)
    sb.press_keys('input[type="email"]', email)
    sb.press_keys('input[type="password"]', password)

    # 3. 处理验证码
    handle_captcha(sb)

    # 4. 提交
    sb.click('button[type=submit]')
    sb.wait_for_ready_state_complete()

    return sb.get_current_url()

with SB(**SB_KWARGS) as sb:
    login(sb, 'user@example.com', 'password123')
```

---

*文档版本：v1.0 | 更新日期：2026-11-13*
