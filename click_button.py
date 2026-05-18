import os
import sys
import re
import time
import random
import getpass
import platform
import glob
import traceback
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

# Modern Python (3.12+) compatibility patch for undetected_chromedriver
import types
try:
    import distutils.version
except ImportError:
    class LooseVersion:
        def __init__(self, versionstring):
            self.version = versionstring
            self.vstring = versionstring
            self.parts = [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', versionstring) if x]
        def __str__(self):
            return self.version
        def __repr__(self):
            return f"LooseVersion('{self.version}')"
        def __eq__(self, other):
            if not isinstance(other, LooseVersion):
                return NotImplemented
            return self.parts == other.parts
        def __lt__(self, other):
            if not isinstance(other, LooseVersion):
                return NotImplemented
            return self.parts < other.parts
        def __le__(self, other):
            if not isinstance(other, LooseVersion):
                return NotImplemented
            return self.parts <= other.parts
        def __gt__(self, other):
            if not isinstance(other, LooseVersion):
                return NotImplemented
            return self.parts > other.parts
        def __ge__(self, other):
            if not isinstance(other, LooseVersion):
                return NotImplemented
            return self.parts >= other.parts

    distutils = types.ModuleType("distutils")
    distutils_version = types.ModuleType("distutils.version")
    distutils_version.LooseVersion = LooseVersion
    distutils.version = distutils_version
    sys.modules["distutils"] = distutils
    sys.modules["distutils.version"] = distutils_version

# pyrefly: ignore [missing-import]
from dataclasses import dataclass, field
# pyrefly: ignore [missing-import]
from selenium import webdriver
# pyrefly: ignore [missing-import]
from selenium.webdriver.chrome.options import Options as ChromeOptions
# pyrefly: ignore [missing-import]
from selenium.webdriver.firefox.options import Options as FirefoxOptions
# pyrefly: ignore [missing-import]
from selenium.webdriver.common.by import By
# pyrefly: ignore [missing-import]
from selenium.webdriver.support.ui import WebDriverWait
# pyrefly: ignore [missing-import]
from selenium.webdriver.support import expected_conditions as EC
# pyrefly: ignore [missing-import]
from selenium.webdriver.common.action_chains import ActionChains
# pyrefly: ignore [missing-import]
from selenium.common.exceptions import StaleElementReferenceException
# pyrefly: ignore [missing-import]
from selenium.webdriver.common.keys import Keys
# pyrefly: ignore [missing-import]
import undetected_chromedriver as uc

# ==========================================
# BEAUTIFUL TERMINAL STYLING
# ==========================================
def supports_color():
    supported_platform = sys.platform != 'win32' or 'ANSICON' in os.environ
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    return supported_platform and is_a_tty

USE_COLOR = supports_color()

class Colors:
    HEADER = '\033[95m' if USE_COLOR else ''
    BLUE = '\033[94m' if USE_COLOR else ''
    CYAN = '\033[96m' if USE_COLOR else ''
    GREEN = '\033[92m' if USE_COLOR else ''
    YELLOW = '\033[93m' if USE_COLOR else ''
    RED = '\033[91m' if USE_COLOR else ''
    BOLD = '\033[1m' if USE_COLOR else ''
    DIM = '\033[2m' if USE_COLOR else ''
    UNDERLINE = '\033[4m' if USE_COLOR else ''
    END = '\033[0m' if USE_COLOR else ''

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}   ⚡======================================================================⚡
{Colors.BLUE}{Colors.BOLD}    ██████╗ █████╗ ████████╗██╗  ██╗ ██████╗     ███████╗██████╗ ███╗   ███╗
    ██╔══██╗██╔══██╗╚══██╔══╝██║  ██║██╔═══██╗    ██╔════╝██╔══██╗████╗ ████║
    ██║  ╚═╝███████║   ██║   ███████║██║   ██║    ███████╗██████╔╝██╔████╔██║
    ██║  ██╗██╔══██║   ██║   ██╔══██║██║   ██║    ╚════██║██╔═══╝ ██║╚██╔╝██║
    ╚██████╔╝██║  ██║   ██║   ██║  ██║╚██████╔╝    ███████║██║     ██║ ╚═╝ ██║
     ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝     ╚══════╝╚═╝     ╚═╝     ╚═╝
{Colors.CYAN}{Colors.BOLD}   ⚡======================================================================⚡
                        {Colors.GREEN}{Colors.BOLD}Catho Invincible Stealth Scraper{Colors.END}
    """
    print(banner)

# ==========================================
# DEFAULT CONFIGURATIONS (Overrideable via .env)
# ==========================================

@dataclass
class ScraperConfig:
    TEST_MODE: bool = True
    REAL_BASE_URL: str = "https://www.catho.com.br/vagas/programador-python/sao-paulo-sp/?order=dataAtualizacao"
    MAX_PAGES_TO_SCRAPE: int = 50
    MIN_DELAY: float = 1.5
    MAX_DELAY: float = 3.0
    KEYWORDS_WORKLIST: list = field(default_factory=lambda: ["programador-python", "java", "backend", "programador-junior", "programador-jr", "estagio"])
    SENIOR_TERMS: list = field(default_factory=lambda: ["senior", "sênior", "sn", "sr"])
    VERBOSE: bool = False

@dataclass
class UserCredentials:
    email: str = "your_email@example.com"
    password: str = "your_password"

def load_env_configurations():
    """
    Helper function to safely parse all configuration variables from the local .env
    and override defaults if they exist.
    """
    config = ScraperConfig()
    credentials = UserCredentials()
    
    env_path = os.path.abspath(".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    cleaned_line = line.strip()
                    if not cleaned_line or cleaned_line.startswith("#"):
                        continue
                    if "=" in cleaned_line:
                        key, val = cleaned_line.split("=", 1)
                        key_str = key.strip()
                        val_str = val.strip().strip("'").strip('"')
                        
                        if key_str == "email":
                            credentials.email = val_str
                        elif key_str == "passwd":
                            credentials.password = val_str
                        elif key_str == "TEST_MODE":
                            config.TEST_MODE = val_str.lower() in ("true", "1", "yes", "on")
                        elif key_str == "REAL_BASE_URL":
                            config.REAL_BASE_URL = val_str
                        elif key_str == "MAX_PAGES_TO_SCRAPE":
                            try:
                                config.MAX_PAGES_TO_SCRAPE = int(val_str)
                            except ValueError:
                                pass
                        elif key_str == "MIN_DELAY":
                            try:
                                config.MIN_DELAY = float(val_str)
                            except ValueError:
                                pass
                        elif key_str == "MAX_DELAY":
                            try:
                                config.MAX_DELAY = float(val_str)
                            except ValueError:
                                pass
                        elif key_str == "KEYWORDS_WORKLIST":
                            config.KEYWORDS_WORKLIST = [k.strip() for k in val_str.split(",") if k.strip()]
                        elif key_str == "SENIOR_TERMS":
                            config.SENIOR_TERMS = [s.strip().lower() for s in val_str.split(",") if s.strip()]
                        elif key_str == "VERBOSE":
                            config.VERBOSE = val_str.lower() in ("true", "1", "yes", "on")
                                
            print(f"{Colors.GREEN}✔{Colors.END} {Colors.BOLD}[.env Loaded]{Colors.END} Configurations and credentials loaded successfully from local .env file.")
        except Exception as e:
            print(f"{Colors.RED}✘{Colors.END} {Colors.BOLD}[.env Read Error]{Colors.END} Could not parse .env file: {e}")
            
    return config, credentials

def setup_driver(config: ScraperConfig, headless: bool = False):
    """
    Elite browser initialization module using undetected_chromedriver.
    """
    workspace_dir = os.path.abspath(os.path.dirname(__file__))
    bot_profile = os.path.join(workspace_dir, "src")
    
    try:
        chrome_options = uc.ChromeOptions()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1280,800")
        
        chrome_options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
        
        print(f"\n{Colors.BLUE}🌐{Colors.END} {Colors.BOLD}[Chrome]{Colors.END} Starting undetected-chromedriver with profile: {Colors.DIM}{bot_profile}{Colors.END}")
        
        driver = uc.Chrome(
            options=chrome_options,
            user_data_dir=bot_profile
        )
        return driver
        
    except Exception as chrome_err:
        print(f"\n{Colors.RED}❌ [FATAL]{Colors.END} Chromium initialization failed: {chrome_err}")
        if config.VERBOSE:
            traceback.print_exc()
        raise

def highlight_element(driver, element, config: ScraperConfig, color="#ff4393"):
    #obs, eu tentei nao usar isso, mas pqp... 

    try:
        original_style = element.get_attribute("style")
        driver.execute_script(
            f"arguments[0].setAttribute('style', 'border: 3px dashed {color} !important; box-shadow: 0 0 10px {color} !important;');", 
            element
        )
        time.sleep(0.8) 
        driver.execute_script("arguments[0].setAttribute('style', arguments[1]);", element, original_style)
    except Exception:
        if config.VERBOSE:
            traceback.print_exc()

def close_possible_popups(driver, config: ScraperConfig):
    # Detect visible modal/popup/consent/dialog containers first to avoid false-positive clicks on layout filter tags
    modal_container_selectors = [
        "div[class*='modal' i]", 
        "div[class*='popup' i]", 
        "div[role='dialog']", 
        "div[role='alertdialog']",
        "div[class*='dialog' i]",
        "div[class*='overlay' i]",
        "div[id*='modal' i]",
        "div[id*='popup' i]",
        "div[id*='dialog' i]",
        "[class*='cookie' i]",
        "[id*='cookie' i]",
        "[class*='consent' i]",
        "[class*='lgpd' i]"
    ]
    
    visible_containers = []
    for selector in modal_container_selectors:
        try:
            containers = driver.find_elements(By.CSS_SELECTOR, selector)
            for container in containers:
                if container.is_displayed():
                    visible_containers.append(container)
        except Exception:
            continue
            
    if not visible_containers:
        return
        
    popup_selectors = [
        (By.CSS_SELECTOR, "button[data-modal-close='modal-killerquestions-container']"),
        (By.CSS_SELECTOR, "button.button_close"),
        (By.CSS_SELECTOR, "span.i_close"),
        (By.CSS_SELECTOR, ".i_close"),
        (By.CSS_SELECTOR, "button[data-modal-close]"),
        (By.CSS_SELECTOR, "button[aria-label*='Fechar']"),
        (By.CSS_SELECTOR, "button[aria-label='Fechar']"),
        (By.CSS_SELECTOR, "button[aria-label='Close']"),
        (By.CSS_SELECTOR, ".modal-close"),
        (By.CSS_SELECTOR, ".close-button"),
        (By.CSS_SELECTOR, "[data-testid='modal-close']"),
        (By.XPATH, ".//*[self::button or self::span or self::a or self::div][text()='x' or text()='X']"),
        (By.XPATH, ".//button[contains(text(), 'Entendi')]"),
        (By.XPATH, ".//button[contains(text(), 'Fechar')]"),
        (By.XPATH, ".//span[contains(text(), 'Fechar')]"),
        (By.XPATH, ".//*[contains(@class, 'close') or contains(@class, 'fechar') or contains(@class, 'Popup')]//button")
    ]
    
    closed_any = False
    for container in visible_containers:
        for by, selector in popup_selectors:
            try:
                # Find elements relative to this specific container
                elements = container.find_elements(by, selector)
                for elem in elements:
                    try:
                        is_shown = elem.is_displayed()
                    except Exception:
                        is_shown = True
                        
                    if is_shown:
                        print(f"  {Colors.RED}🚨 [POPUP]{Colors.END} Closing popup inside container using: {Colors.DIM}{selector}{Colors.END}")
                        driver.execute_script("arguments[0].click();", elem)
                        closed_any = True
                        time.sleep(0.5)
            except Exception:
                continue
                
    # Fallback: ESC key dismissal if we detected active containers but couldn't click any specific close button
    if not closed_any:
        if config.VERBOSE:
            print(f"  {Colors.YELLOW}⚠️ [POPUP]{Colors.END} Active modal container found. Attempting ESC dismissal fallback...")
        try:
            active_elem = driver.switch_to.active_element
            if active_elem:
                active_elem.send_keys(Keys.ESCAPE)
                if config.VERBOSE:
                    print(f"  {Colors.DIM}  -> Sent native Keys.ESCAPE to active element.{Colors.END}")
        except Exception:
            if config.VERBOSE:
                traceback.print_exc()

def login_to_catho(driver, credentials: UserCredentials, config: ScraperConfig) -> bool:

    wait = WebDriverWait(driver, 15)
    
    try:
        if config.TEST_MODE:
            login_file_path = os.path.abspath("Catho Login.html")
            if not os.path.exists(login_file_path):
                print(f"[TEST MODE] Error: Could not find 'Catho Login.html' at {login_file_path}")
                return False
            login_url = f"file://{login_file_path}"
            print(f"\n[Login Process - TEST MODE] Loading local login template: {login_url}")
            driver.get(login_url)
            time.sleep(1.5)
        else:
            home_url = "https://www.catho.com.br/"
            print(f"\n[Login Process] Navigating to Catho homepage: {home_url}")
            driver.get(home_url)
            
            print("  -> Checking if already logged in via persistent session...")
            try:
                time.sleep(1.5)
                if driver.find_elements(By.CLASS_NAME, "i_signout") or \
                   driver.find_elements(By.CLASS_NAME, "avatar") or \
                   driver.find_elements(By.CSS_SELECTOR, "a.user-avatar") or \
                   ("signin" not in driver.current_url.lower() and "login" not in driver.current_url.lower() and len(driver.find_elements(By.ID, "signin")) == 0):
                    print("  [SUCCESS] Already logged in via persistent Chrome session! Skipping login flow.")
                    return True
            except Exception:
                pass
            
            # Step 1: mandar se foder, mas depois clica em aceitar 
            print("  -> Checking for Cookie Consent Banner...")
            cookie_button_selectors = [
                (By.CSS_SELECTOR, "button.acceptAll"),
                (By.XPATH, "//button[contains(text(), 'Aceitar todos os cookies')]"),
                (By.XPATH, "//button[contains(@class, 'acceptAll')]")
            ]
            
            cookie_accepted = False
            for by, selector in cookie_button_selectors:
                try:
                    cookie_btn = WebDriverWait(driver, 6).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    highlight_element(driver, cookie_btn, config, color="#25D366")
                    cookie_btn.click()
                    print("  [COOKIES] Clicked 'Aceitar todos os cookies' successfully.")
                    cookie_accepted = True
                    break
                except Exception:
                    continue
                    
            if not cookie_accepted:
                print("  [COOKIES] Cookie consent banner not found or already accepted. Proceeding...")
                
            time.sleep(1.0)
            
            print("  -> Locating 'Entrar' link to navigate to sign-in page...")
            signin_link_selectors = [
                (By.ID, "signin"),
                (By.CSS_SELECTOR, "a#signin"),
                (By.CSS_SELECTOR, 'a[data-event="entrar_link"]'),
                (By.XPATH, "//a[contains(@href, '/signin/')]"),
                (By.XPATH, "//a[text()='Entrar']")
            ]
            
            signin_clicked = False
            for by, selector in signin_link_selectors:
                try:
                    signin_link = wait.until(EC.element_to_be_clickable((by, selector)))
                    highlight_element(driver, signin_link, config, color="#3624d6")
                    signin_link.click()
                    print("  -> Clicked 'Entrar' link successfully.")
                    signin_clicked = True
                    break
                except Exception:
                    continue
                    
            if not signin_clicked:
                print("  [WARN] Could not click 'Entrar' link. Navigating directly to sign-in URL...")
                driver.get("https://www.catho.com.br/signin/")
            else:
                try:
                    wait.until(EC.url_contains("/signin/"))
                    print(f"  -> Redirection successful. Current URL: {driver.current_url}")
                except Exception:
                    print(f"  [INFO] URL did not change immediately. Current URL: {driver.current_url}")
                    
            time.sleep(2.0) 
        
        # ----------------------------------------------------
        # Inject email/username and password
        # ----------------------------------------------------
        email_selectors = [
            (By.NAME, "email"),
            (By.ID, "login"),
            (By.NAME, "login"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[name='email']"),
            (By.XPATH, "//input[@placeholder='Ex: Raquel@gmail.com']"),
            (By.XPATH, "//input[contains(@placeholder, 'E-mail')]")
        ]
        
        email_field = None
        for by, selector in email_selectors:
            try:
                email_field = wait.until(EC.element_to_be_clickable((by, selector)))
                break
            except Exception:
                continue
                
        if not email_field:
            raise Exception("Could not find the email/login input field.")
            
        print("  -> Entering email/CPF...")
        highlight_element(driver, email_field, config, color="#25D366" if config.TEST_MODE else "#3624d6")
        email_field.clear()
        email_field.send_keys(credentials.email)
        password_selectors = [
            (By.NAME, "password"),
            (By.ID, "password"),
            (By.ID, "senha"),
            (By.NAME, "senha"),
            (By.CSS_SELECTOR, "input[type='password']")
        ]
        
        password_field = None
        for by, selector in password_selectors:
            try:
                password_field = driver.find_element(by, selector)
                if password_field.is_displayed():
                    break
                else:
                    password_field = None
            except Exception:
                continue
                
        if not password_field:
            print("  -> Password field not immediately visible. Attempting multi-step 'Avançar' flow...")
            continue_selectors = [
                (By.XPATH, "//button[contains(text(), 'Avançar')]"),
                (By.XPATH, "//button[contains(text(), 'Continuar')]"),
                (By.XPATH, "//button[@type='submit']"),
                (By.CSS_SELECTOR, "button.button_primary")
            ]
            
            continue_btn = None
            for by, selector in continue_selectors:
                try:
                    continue_btn = wait.until(EC.element_to_be_clickable((by, selector)))
                    break
                except Exception:
                    continue
                    
            if not continue_btn:
                raise Exception("Could not locate the 'Avançar/Continuar' button.")
                
            continue_btn.click()
            print("  -> Clicked 'Avançar'. Waiting for password field to load...")
            time.sleep(1.5)  # Allow transition animation
            
            # Re-locate the password field now that it should be visible
            for by, selector in password_selectors:
                try:
                    password_field = wait.until(EC.visibility_of_element_located((by, selector)))
                    break
                except Exception:
                    continue
                    
        if not password_field:
            raise Exception("Could not locate the password field.")
            
        print("  -> Entering password...")
        highlight_element(driver, password_field, config, color="#25D366" if config.TEST_MODE else "#3624d6")
        password_field.clear()
        password_field.send_keys(credentials.password)
        
        submit_selectors = [
            (By.XPATH, "//button[text()='Entrar']"),
            (By.XPATH, "//button[contains(text(), 'Entrar')]"),
            (By.XPATH, "//button[@type='submit']"),
            (By.CSS_SELECTOR, "button[type='submit']")
        ]
        
        submit_btn = None
        for by, selector in submit_selectors:
            try:
                submit_btn = wait.until(EC.element_to_be_clickable((by, selector)))
                break
            except Exception:
                continue
                
        if not submit_btn:
            raise Exception("Could not locate the submit/login button.")
            
        print("  -> Clicking final 'Entrar' button...")
        highlight_element(driver, submit_btn, config, color="#25D366" if config.TEST_MODE else "#3624d6")
        
        # If in TEST_MODE, pause briefly to show fields filled, then click
        if config.TEST_MODE:
            time.sleep(2.0)
            
        submit_btn.click()
        print("  -> Login form submitted successfully!")
        
        if config.TEST_MODE:
            print("  [TEST MODE] Successfully simulated login flow locally. Settle delay...")
            time.sleep(3.0)
            return True
            
        # Step 6: ''''Gracefully'''' handle Captchas/security checkpoints
        print("\n[Security Check] Monitoring for CAPTCHAs or manual verifications...")
        print("  >> We ARE SO FUCKED UP...")
        print("  >> If a CAPTCHA or 'Prove que você é humano' check appears, please solve it manually in the Chrome window!")
        print("  >> The script will monitor the session and proceed once successful login is detected.")
        
        # We wait up to 45 seconds for a successful login indicator.
        success = False
        start_time = time.time()
        while time.time() - start_time < 45:
            current_url = driver.current_url.lower()
            if "login" not in current_url and "auth" not in current_url and "signin" not in current_url:
                print("  [SUCCESS] Successfully logged in! Redirected away from login page.")
                success = True
                break
            
            try:
                if driver.find_elements(By.CLASS_NAME, "i_signout") or driver.find_elements(By.CLASS_NAME, "avatar"):
                    print("  [SUCCESS] Successfully logged in! Candidate profile indicators found.")
                    success = True
                    break
            except Exception:
                pass
                
            time.sleep(1.5)
            
        if not success:
            print("\n  [INFO] Timeout waiting for automatic login redirection.")
            print("  Continuing to the scraper. If login was successful, it will run correctly.")
        else:
            time.sleep(2.0)  # Settle session cookies
            
        return True
            
    except Exception as e:
        print(f"\n[Login Failed] Could not automate the login flow: {e}")
        print("Continuing directly to the scraping page in case you are already logged in or want to log in manually.")
        return False

def contains_senior_terms(text: str, config: ScraperConfig) -> bool:
    """
    Checks if the given text contains any senior-related keywords as distinct words.
    Uses regex word boundaries to avoid false positives.
    """
    joined = "|".join([re.escape(term) for term in config.SENIOR_TERMS])
    pattern = re.compile(rf'\b({joined})\b', re.IGNORECASE)
    return bool(pattern.search(text))

def process_page_buttons(driver, config: ScraperConfig) -> int:
    close_possible_popups(driver, config)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # 1. Count the total valid items on the page to set our loop boundary
    initial_cards = driver.find_elements(By.XPATH, "//li[@data-offer-item]")
    total_cards_count = len(initial_cards)
    
    # Pre-scan just to get an accurate total_valid count for the UI
    total_valid = 0
    card_ids = []
    
    for card in initial_cards:
        try:
            # Extract unique identifier to prevent index shifting
            c_id = card.get_attribute("data-offer-item")
            if c_id:
                card_ids.append(c_id)
        except Exception:
            pass
            
        if card.find_elements(By.XPATH, ".//button[contains(text(), 'Quero me candidatar')]"):
            total_valid += 1
            
    print(f"\n{Colors.BLUE}🔍 [Page Scraper]{Colors.END} Found {Colors.BOLD}{total_cards_count}{Colors.END} total job cards. {Colors.BOLD}{total_valid}{Colors.END} are active for application.")
    
    clicked_count = 0
    skipped_count = 0
    valid_processed_count = 0
    
    for card_id in card_ids:
        try:
            close_possible_popups(driver, config)
            
            # Re-fetch the specific card by ID to ensure it is fresh in the DOM
            try:
                card = driver.find_element(By.XPATH, f"//li[@data-offer-item='{card_id}']")
            except Exception:
                continue # Card vanished from DOM
            
            # Check if this card actually has an application button
            buttons = card.find_elements(By.XPATH, ".//button[contains(text(), 'Quero me candidatar')]")
            if not buttons:
                continue
                
            button = buttons[0]
            valid_processed_count += 1
            
            # Get card text to check for senior keywords
            card_text = card.text
            
            # Extract job title if possible for clean logging
            job_title = "Vaga Desconhecida"
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, "h2.title_offer a")
                job_title = title_elem.text
            except Exception:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, "h2.title_offer")
                    job_title = title_elem.text
                except Exception:
                    pass
            
            # Check for Senior keywords
            if contains_senior_terms(card_text, config):
                skipped_count += 1
                if config.VERBOSE:
                    matched_term = "SENIOR/SN"
                    for term in config.SENIOR_TERMS:
                        if re.search(rf'\b{re.escape(term)}\b', card_text, re.IGNORECASE):
                            matched_term = term.upper()
                            break
                    print(f"  {Colors.YELLOW}⏭ [SKIPPED]{Colors.END} Skipping Senior role: '{Colors.BOLD}{job_title}{Colors.END}' (Matched: {Colors.YELLOW}{matched_term}{Colors.END})")
                continue
                
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", 
                button
            )
            print(f"  {Colors.CYAN}➤{Colors.END} Targeting: '{Colors.BOLD}{job_title}{Colors.END}' ({valid_processed_count}/{total_valid})... ", end="", flush=True)
            highlight_element(driver, button, config, color="#ff4393" if config.TEST_MODE else "#3624d6")
            
            try:
                # PHANTOM: Realistic behavioral interaction pattern (Hover -> Small Delay -> Click)
                actions = ActionChains(driver)
                actions.move_to_element(button).pause(random.uniform(0.1, 0.4)).click().perform()
                print(f"{Colors.GREEN}✔ [CLICK]{Colors.END}")
                clicked_count += 1
            except Exception as click_err:
                if config.VERBOSE:
                    print(f"\n  {Colors.YELLOW}⚡ [INFO]{Colors.END} Click intercepted or failed. Clearing popups & retrying...")
                close_possible_popups(driver, config)
                time.sleep(0.6)
                
                # Because we cleared a popup, the DOM might have shifted. Re-fetch the exact button to prevent StaleElement!
                try:
                    card = driver.find_element(By.XPATH, f"//li[@data-offer-item='{card_id}']")
                    retry_buttons = card.find_elements(By.XPATH, ".//button[contains(text(), 'Quero me candidatar')]")
                    if retry_buttons:
                        button = retry_buttons[0]
                except Exception:
                    pass
                        
                try:
                    actions = ActionChains(driver)
                    actions.move_to_element(button).pause(0.2).click().perform()
                    print(f"{Colors.GREEN}✔ [CLICK (Retry)]{Colors.END}")
                    clicked_count += 1
                except Exception:
                    if config.VERBOSE:
                        print(f"\n  {Colors.YELLOW}⚙ [JS FALLBACK]{Colors.END} Standard click blocked. Clicking button via JavaScript...")
                    driver.execute_script("arguments[0].click();", button)
                    print(f"{Colors.GREEN}✔ [CLICK (JS)]{Colors.END}")
                    clicked_count += 1
                    
            # Immediately check and dismiss any success/confirmation modal that appeared
            time.sleep(0.6)
            close_possible_popups(driver, config)
            
            # 4. Human-simulation sleep delay
            delay = random.uniform(config.MIN_DELAY, config.MAX_DELAY)
            if config.VERBOSE:
                print(f"  {Colors.BLUE}⏳ [HUMAN DELAY]{Colors.END} Waiting {Colors.BOLD}{delay:.2f}{Colors.END} seconds...")
            time.sleep(delay)
            
        except StaleElementReferenceException:
            if config.VERBOSE:
                print(f"\n  {Colors.YELLOW}⚠️ [DOM Update]{Colors.END} Element went stale.")
            continue
        except Exception as e:
            print(f"\n  {Colors.RED}✘ [WARN]{Colors.END} Failed to process card {card_id}: {e}")
            
    print(f"\n{Colors.GREEN}✔ [Page Summary]{Colors.END} Applied: {Colors.BOLD}{clicked_count}{Colors.END} | Skipped Senior: {Colors.BOLD}{skipped_count}{Colors.END}")
    return clicked_count

def get_url_for_keyword(base_url: str, keyword: str) -> str:
    """
    Safely replaces the job title segment in the Catho URL.
    Example: .../vagas/programador-python/sao-paulo-sp/... -> .../vagas/java/sao-paulo-sp/...
    """
    if "/vagas/" in base_url:
        parts = base_url.split("/vagas/")
        subparts = parts[1].split("/", 1)
        original_slug = subparts[0]
        # Format the keyword to be URL friendly (replace spaces with hyphens, lowercase)
        formatted_keyword = keyword.lower().replace(" ", "-")
        return parts[0] + "/vagas/" + formatted_keyword + "/" + subparts[1]
    return base_url

def run_scraper():
    # 1. Load all configurations and credentials dynamically from local .env
    config, credentials = load_env_configurations()
    print_banner()
    
    # Prompt securely in the console if still default placeholders and not found in .env
    if not config.TEST_MODE:
        if credentials.email == "your_email@example.com" or not credentials.email:
            print(f"\n{Colors.BOLD}=== Catho Login Credentials ==={Colors.END}")
            credentials.email = input("Enter your Catho Email/CPF: ").strip()
        if credentials.password == "your_password" or not credentials.password:
            credentials.password = getpass.getpass("Enter your Catho Password (secure input, hidden): ")
            
    driver = setup_driver(config, headless=False)
    
    try:
        # Check login status and break if failed
        if not login_to_catho(driver, credentials, config):
            print(f"\n{Colors.RED}❌ [EXIT]{Colors.END} Login flow failed. Halting scraper to prevent loops on blank/login pages.")
            return
            
        # ==========================================
        # WORKLIST LOOP
        # ==========================================
        for keyword in config.KEYWORDS_WORKLIST:
            formatted_keyword = keyword.lower().replace(" ", "-")
            target_url = get_url_for_keyword(config.REAL_BASE_URL, keyword)
            
            print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}\n📋 STARTING SCRAPING FOR KEYWORD: {Colors.YELLOW}{keyword.upper()}{Colors.CYAN}\n{'='*60}{Colors.END}")
            print(f"{Colors.BLUE}🎯 Target URL:{Colors.END} {Colors.UNDERLINE}{target_url}{Colors.END}")
            
            driver.get(target_url)
            time.sleep(2.5)
            
            # Double check URL again to be absolutely sure we are on the correct search page
            if formatted_keyword not in driver.current_url or "order=dataAtualizacao" not in driver.current_url:
                print(f"\n{Colors.YELLOW}⚠️ [URL VERIFICATION]{Colors.END} Currently on: {Colors.UNDERLINE}{driver.current_url}{Colors.END}")
                print(f"-> Redirecting to target URL: {Colors.UNDERLINE}{target_url}{Colors.END}")
                driver.get(target_url)
                time.sleep(2.5)
                
            current_page = 1
            while current_page <= config.MAX_PAGES_TO_SCRAPE:
                print(f"\n{Colors.HEADER}{Colors.BOLD}{'-'*50}\n📄 SCRAPING {keyword.upper()} - PAGE {current_page}\n{'-'*50}{Colors.END}")            
                clicked_count = process_page_buttons(driver, config)
                
                # If we applied to 0 jobs, we either hit already applied ones or there are no more jobs for this keyword.
                if clicked_count == 0:
                    print(f"\n{Colors.YELLOW}📋 [Worklist]{Colors.END} Found 0 application buttons on page {current_page} for '{keyword}'. Moving to next keyword in worklist...")
                    break
                    
                if current_page >= config.MAX_PAGES_TO_SCRAPE:
                    print(f"\n{Colors.GREEN}📋 [Worklist]{Colors.END} Reached the cap of {Colors.BOLD}{config.MAX_PAGES_TO_SCRAPE}{Colors.END} pages for '{keyword}'.")
                    break
                    
                print(f"\n{Colors.BLUE}📄 [Pagination]{Colors.END} Preparing to move to Page {current_page + 1}...")
                next_button = None
                next_selectors = [
                    (By.CSS_SELECTOR, "a.next-page"),
                    (By.CSS_SELECTOR, "a[class*='next' i]"),
                    (By.CSS_SELECTOR, "a[aria-label*='Próxima' i]"),
                    (By.CSS_SELECTOR, "a[title*='Próxima' i]"),
                    (By.XPATH, "//a[contains(text(), 'Próxima')]"),
                    (By.XPATH, "//a[contains(text(), 'Proxima')]"),
                    (By.XPATH, "//button[contains(text(), 'Próxima')]")
                ]
                
                for by, selector in next_selectors:
                    try:
                        next_button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        if next_button:
                            break
                    except Exception:
                        continue
                        
                if next_button:
                    try:
                        print(f"  {Colors.GREEN}✔{Colors.END} Found 'Próxima' pagination button. Clicking...")
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", next_button)
                        next_button.click()
                        current_page += 1
                        time.sleep(random.uniform(2.0, 4.0))
                    except Exception as click_err:
                        print(f"  {Colors.YELLOW}⚠️ [Pagination Click Failed]{Colors.END} Click blocked: {click_err}. Navigating directly...")
                        next_button = None
                
                if not next_button:
                    parsed_url = urlparse(target_url)
                    query_params = parse_qs(parsed_url.query)
                    query_params["page"] = [str(current_page + 1)]
                    new_query = urlencode(query_params, doseq=True)
                    next_page_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, new_query, parsed_url.fragment))
                    print(f"  {Colors.CYAN}➤{Colors.END} Pagination button not clickable/found. Navigating directly to URL: {Colors.UNDERLINE}{next_page_url}{Colors.END}")
                    driver.get(next_page_url)
                    current_page += 1
                    time.sleep(random.uniform(2.0, 4.0))

    except Exception as e:
        print(f"\n{Colors.RED}❌ [CRITICAL ERROR]{Colors.END} Scraper execution halted: {e}")
        if config.VERBOSE:
            traceback.print_exc()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🛑 [KeyboardInterrupt]{Colors.END} Scraper execution interrupted by user.")
        driver.quit()

    finally:
        print(f"\n{Colors.GREEN}🏁 All tasks completed.{Colors.END} Closing browser window...")
        driver.quit()




if __name__ == "__main__":
    run_scraper()
