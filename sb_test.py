from seleniumbase import SB
import logging
import time
#------------------配置SB
sb_kwargs = {
    "uc": True,
    "test": True,
    "locale": "en",
    "headed": False,
    "user_data_dir": None,
    "chromium_arg": "--disable-blink-features=AutomationControlled"
}
sb=SB(**sb_kwargs)
#------------------配置logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("history.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger()

def wait_for_turnstile_success(timeout: int = 30) -> bool:
    logger.info("等待 Turnstile 验证...")
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
def login(email, password):
    logger.info("填写登录信息...")
    sb.wait_for_element_visible('input[type="email"]', timeout=10)
    # ---------根据页面情况修改
    sb.press_keys('input[type="email"]', 'abc@abc.com')
    sb.press_keys('input[type="password"]', 'abcabc')
    safe_screenshot(sb, "2-填写表单.png")

    logger.info("点击登录按钮...")
    # submit_button="form>button"
    submit_button = "button[type='submit']"
    sb.uc_click(submit_button)
    sb.wait_for_ready_state_complete()
    current_url = sb.get_current_url()
    logger.info(f"登录后URL: {current_url}")
    safe_screenshot(sb, "3-提交登录.png")
    if "/dashboard" in current_url:
        return True
    else:
        return False

def handle_captcha():
    logger.info("处理 Turnstile 验证...")
    sb.uc_gui_handle_captcha()
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
            logger.warning("Turnstile 多次尝试后仍未通过，尝试强制提交...")
def main(account):
    email=account['email']
    password=account['password']
    # 打开登录页面
    url="https://betadash.lunes.host/login"
    sb.uc_open_with_reconnect(url, reconnect_time=5)
    sb.wait_for_ready_state_complete()
    # 第一步：填写登录信息
    logger.info("填写登录信息...")
    sb.wait_for_element_visible('input[type="email"]', timeout=10)
    sb.press_keys('input[type="email"]', email)
    sb.press_keys('input[type="password"]', password)
    sb.save_screenshot('1-Account.png')
    
    # 第二步：处理Turnstile验证
    logger.info("处理 Turnstile 验证...")
    handle_captcha()
    sb.save_screenshot('2-Turnstile.png')
    
    # 第三步：提交登录
    submit_button = "button[type=submit]"
    sb.click(submit_button)
    sb.wait_for_ready_state_complete()
    current_url = sb.get_current_url()
    logger.info(f"登录后URL: {current_url}")
    sb.save_screenshot('3-Login.png')


    



if __name__ == "__main__":
    account={'email':'abc@abc.com','password':'abcabc'}
    main(account)
