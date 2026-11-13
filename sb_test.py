from datetime import datetime, timedelta, timezone
from seleniumbase import SB
import requests
import logging
import time
import json
import os
# ----------------------配置SeleniumBase参数
SB_KWARGS = {
        'uc': True, 
        'test': True, 
        'locale': 'en', 
        'headed': False, 
        'user_data_dir': None, 
        'chromium_arg': '--disable-blink-features=AutomationControlled'
        }
ALLOW_SCREENSHOT = False
#------------------配置logging
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
    formatter = TimezoneFormatter(fmt='%(asctime)s - %(levelname)s - %(message)s', tz_offset=8)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    file_handler = logging.FileHandler(logfile,'w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logging()
# ------------------安全截图函数
def safe_screenshot(sb, filename: str):
    if not ALLOW_SCREENSHOT:
        return
    try:
        logger.info(f"📸 截图 → {filename}")
        sb.save_screenshot(f"{filename}")
    except Exception as e:
        logger.warning(f"截图失败: {e}")

# ------------------TG通知函数
def tg_message(msg):
    try:
        # 自建TGAPI发送通知
        TG_API=os.getenv('TG_API')
        requests.post(TG_API,data=msg)
        logger.info(f"TG通知：{msg}")
    except  Exception as e:
        # 使用TG_TOKEN发送通知
        tg_config=json.loads(os.getenv('TG_TOKEN'))
        token = tg_config.get("token")
        chatid = tg_config.get("chatid")
        data={
            "chat_id": chatid,
            "text": msg
        }
        response = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",json=data)
        response.raise_for_status()
        logger.info(f"TG通知：{msg}")
    except Exception as e:
        logger.warning(f"TG通知失败：{e}")
    
# ------------------Turnstile验证函数
def wait_for_turnstile_success(sb,timeout: int = 30) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            success = sb.execute_script('''
                var resp = document.querySelector('input[name="cf-turnstile-response"]');
                if (resp && resp.value && resp.value.length > 20) return true;
                var grecap = document.querySelector('textarea[name="g-recaptcha-response"]');
                if (grecap && grecap.value && grecap.value.length > 20) return true;
                var iframe = document.querySelector('iframe[src*="challenges.cloudflare.com"]');
                if (iframe && iframe.getAttribute("data-state") === "solved") return true;
                return false;
            ''')
            if success:
                logger.info("✅ Turnstile 验证成功")
                return True
        except:
            pass
        time.sleep(1)
    logger.warning("⏰ Turnstile 验证超时")
    return False

# ------------------Turnstile验证处理函数
def handle_captcha(sb):
    already_done = wait_for_turnstile_success(sb, timeout=5)
    if already_done:
        logger.info("Turnstile 已自动完成，直接提交")
    else:
        logger.info("Turnstile 未自动完成，尝试点击...")
        for click_attempt in range(3):
            try:
                sb.uc_gui_click_captcha()
                logger.info(f"点击验证框第 {click_attempt + 1} 次")
            except Exception as e:
                logger.warning(f"点击验证码异常 (第 {click_attempt + 1} 次): {e}")
            time.sleep(2)
            if wait_for_turnstile_success(sb, timeout=10):
                break
        else:
            sb.uc_gui_handle_captcha()
            logger.warning("Turnstile 多次尝试后仍未通过，尝试强制提交...")

# ------------------业务操作函数
def my_jobs(sb,data=None):
    logger.info(f"业务操作...{data}")
    sucess=False
    # 业务操作逻辑
    # ...
    # ...
    safe_screenshot(sb,'4-Business.png')
    return sucess


# ------------------主函数
def main(account):
    email=account['email']
    password=account['password']

    with SB(**SB_KWARGS) as sb:
        # 打开登录页面
        url="https://betadash.lunes.host/login"
        sb.uc_open_with_reconnect(url, reconnect_time=5)
        sb.wait_for_ready_state_complete()
        safe_screenshot(sb,'0-Homepage.png')
        
        # 第一步：填写登录信息
        logger.info("填写登录信息...")
        sb.wait_for_element_visible('input[type="email"]', timeout=10)
        sb.press_keys('input[type="email"]', email)
        sb.press_keys('input[type="password"]', password)
        safe_screenshot(sb,'1-Account.png')
        
        # 第二步：处理Turnstile验证
        logger.info("处理 Turnstile 验证...")
        handle_captcha(sb)
        safe_screenshot(sb,'2-Turnstile.png')
        
        # 第三步：提交登录
        submit_button = "button[type=submit]"
        sb.click(submit_button)
        sb.wait_for_ready_state_complete()
        current_url = sb.get_current_url()
        logger.info(f"登录后URL: {current_url}")
        safe_screenshot(sb,'3-Login.png')

        # 第四步：业务操作
        logger.info("业务操作...")
        sucess=my_jobs(sb,data=email)

        # 第五步：TG通知
        if sucess:
            logger.info("TG通知...")
            msg=f"业务操作成功：{email}"
            tg_message(msg)



if __name__ == "__main__":
    # 判断是否在GitHub Actions中运行
    if 'GITHUB_ENV' not in os.environ:
        logger.info("当前环境不是 GitHub Actions，无法运行。")
        exit(1)    
    account={'email':'abc@abc.com','password':'abcabc'}

    main(account)
