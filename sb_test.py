from seleniumbase import SB
import logging
import time

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

def wait_for_turnstile_success(sb, timeout: int = 30) -> bool:
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
def login(sb, email, password):
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


def main(url):
    sb_kwargs = {
        "uc": True,
        "test": True,
        "locale": "en",
        "headed": False,
        "user_data_dir": None,
        "chromium_arg": "--disable-blink-features=AutomationControlled"
    }
    with SB(**sb_kwargs) as sb:
        sb.uc_open_with_reconnect(url, reconnect_time=5)
        sb.wait_for_ready_state_complete()

        logger.info("填写登录信息...")
        sb.wait_for_element_visible('input[type="email"]', timeout=10)
        # ---------根据页面情况修改
        sb.press_keys('input[type="email"]', 'abc@abc.com')
        sb.press_keys('input[type="password"]', 'password')
        sb.sleep(1)
        sb.save_screenshot("1-填写表单.png")
        time.sleep(3)
        
        logger.info("处理 Turnstile 验证码...")
        already_done = wait_for_turnstile_success(sb, timeout=5)
        if already_done:
            logger.info("Turnstile 已自动完成，直接提交")
        else:
            logger.info("Turnstile 未自动完成，尝试点击...")
            for click_attempt in range(3):
                try:
                    sb.uc_gui_click_captcha()
                    logger.info(f"点击验证码第 {click_attempt + 1} 次")
                except Exception as e:
                    logger.warning(f"点击验证码异常 (第 {click_attempt + 1} 次): {e}")
                time.sleep(2)
                if wait_for_turnstile_success(sb, timeout=10):
                    break
            else:
                logger.warning("Turnstile 多次尝试后仍未通过，尝试强制提交...")
        sb.save_screenshot("2-Turnstile验证.png")
        # loginOk=login(sb,email,password)
        # if not loginOk:
        #     logger.info('登录失败。')
        #     return False
        # else:
        #     logger.info('登录成功。')


if __name__ == "__main__":
    url = "https://betadash.lunes.host/login"
    main(url)
