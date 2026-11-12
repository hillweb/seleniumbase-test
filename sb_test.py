from seleniumbase import SB
import logging

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


def login(sb, email, password):
    logger.info("填写登录信息...")
    sb.wait_for_element_visible('input[type="email"]', timeout=10)
    # ---------根据页面情况修改
    sb.press_keys('input[type="email"]', email)
    sb.press_keys('input[type="password"]', password)
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

def check_turnstile_success(sb):
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
    return False
def main(url):
    sb_kwargs = {
        "uc": True,
        "test": True,
        "locale": "en",
        "headed": False,
        "user_data_dir": None,
        "chromium_arg": "--disable-blink-features=AutomationControlled",
        "window_size": "1920,1280",
    }
    with SB(**sb_kwargs) as sb:
        sb.uc_open_with_reconnect(url, reconnect_time=5)
        sb.wait_for_ready_state_complete()
        logger.info("Cloudflare 验证码/Turnstile 验证中...")
        try:
            sb.uc_gui_handle_captcha()
        except Exception:
            logger.info("验证失败，重试中...")

        flag=check_turnstile_success(sb)
        print(f'Turnstile验证结果：{flag}')
        if not flag:
            try:
                sb.uc_gui_click_captcha()
            except Exception as e:
                logger.info(f"验证点击失败: {e}") 
        flag=check_turnstile_success(sb)
        print(f'Turnstile验证结果：{flag}')
        # 验证是否已经通过（标题或页面内容变化）
        logger.info("已通过Turnstile验证或无需验证")
        logger.info(f"当前标题: {sb.get_title()}")
        sb.save_screenshot("1-Turnstile验证.png")
        # loginOk=login(sb,email,password)
        # if not loginOk:
        #     logger.info('登录失败。')
        #     return False
        # else:
        #     logger.info('登录成功。')


if __name__ == "__main__":
    url = "https://betadash.lunes.host/login"
    main(url)
