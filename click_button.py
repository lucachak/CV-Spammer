import os
import sys
import re
import time
import random
import getpass
# pyrefly: ignore [missing-import]
from dataclasses import dataclass
# pyrefly: ignore [missing-import]
from selenium import webdriver
# pyrefly: ignore [missing-import]
from selenium.webdriver.chrome.options import Options
# pyrefly: ignore [missing-import]
from selenium.webdriver.common.by import By
# pyrefly: ignore [missing-import]
from selenium.webdriver.support.ui import WebDriverWait
# pyrefly: ignore [missing-import]
from selenium.webdriver.support import expected_conditions as EC

try:
    import pyautogui
except Exception:
    pyautogui = None

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
TEST_MODE = True
REAL_BASE_URL = "https://www.catho.com.br/vagas/programador-python/sao-paulo-sp/?order=dataAtualizacao"
MAX_PAGES_TO_SCRAPE = 50
CATHO_EMAIL = "your_email@example.com"
CATHO_PASSWORD = "your_password"
MIN_DELAY = 1.5
MAX_DELAY = 3.0
KEYWORDS_WORKLIST = ["programador-python", "java", "backend", "programador-junior", "programador-jr", "estagio"]
SENIOR_TERMS = ["senior", "sênior", "sn", "sr"]
VERBOSE = False
# ==========================================

@dataclass
class UserCredentials:
    email: str
    password: str

def load_env_configurations():
    """
    Helper function to safely parse all configuration variables from the local .env
    and override global constants if they exist.
    """
    global TEST_MODE, REAL_BASE_URL, MAX_PAGES_TO_SCRAPE, CATHO_EMAIL, CATHO_PASSWORD, MIN_DELAY, MAX_DELAY, KEYWORDS_WORKLIST, SENIOR_TERMS, VERBOSE
    
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
                            CATHO_EMAIL = val_str
                        elif key_str == "passwd":
                            CATHO_PASSWORD = val_str
                        elif key_str == "TEST_MODE":
                            TEST_MODE = val_str.lower() in ("true", "1", "yes", "on")
                        elif key_str == "REAL_BASE_URL":
                            REAL_BASE_URL = val_str
                        elif key_str == "MAX_PAGES_TO_SCRAPE":
                            try:
                                MAX_PAGES_TO_SCRAPE = int(val_str)
                            except ValueError:
                                pass
                        elif key_str == "MIN_DELAY":
                            try:
                                MIN_DELAY = float(val_str)
                            except ValueError:
                                pass
                        elif key_str == "MAX_DELAY":
                            try:
                                MAX_DELAY = float(val_str)
                            except ValueError:
                                pass
                        elif key_str == "KEYWORDS_WORKLIST":
                            KEYWORDS_WORKLIST = [k.strip() for k in val_str.split(",") if k.strip()]
                        elif key_str == "SENIOR_TERMS":
                            SENIOR_TERMS = [s.strip().lower() for s in val_str.split(",") if s.strip()]
                        elif key_str == "VERBOSE":
                            VERBOSE = val_str.lower() in ("true", "1", "yes", "on")
                                
            print(f"{Colors.GREEN}✔{Colors.END} {Colors.BOLD}[.env Loaded]{Colors.END} Configurations and credentials loaded successfully from local .env file.")
        except Exception as e:
            print(f"{Colors.RED}✘{Colors.END} {Colors.BOLD}[.env Read Error]{Colors.END} Could not parse .env file: {e}")

def setup_driver(headless: bool = False) -> webdriver.Chrome:
    "fucking driver do caralho"
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,800")
    

    # pega o dir do chrome no subfolder src
    workspace_dir = os.path.abspath(os.path.dirname(__file__))
    src_profile_path = os.path.join(workspace_dir, "src", "Default")
    if os.path.exists(src_profile_path):
        src_dir = os.path.join(workspace_dir, "src")
        print(f"\n{Colors.BLUE}🌐{Colors.END} {Colors.BOLD}[Chrome Profile]{Colors.END} Detected custom 'Default' profile inside src. Loading persistent session from: {Colors.DIM}{src_dir}{Colors.END}")
        chrome_options.add_argument(f"--user-data-dir={src_dir}")
        chrome_options.add_argument("--profile-directory=Default")
    else:
        # Fallback to root Default folder if exists
        default_profile_path = os.path.join(workspace_dir, "Default")
        if os.path.exists(default_profile_path):
            print(f"\n{Colors.BLUE}🌐{Colors.END} {Colors.BOLD}[Chrome Profile]{Colors.END} Detected custom 'Default' profile. Loading persistent session from: {Colors.DIM}{workspace_dir}{Colors.END}")
            chrome_options.add_argument(f"--user-data-dir={workspace_dir}")
            chrome_options.add_argument("--profile-directory=Default")
    
    # -------------------------------------------------------------------------
    # ANTI-DETECTION (STEALTH) CONFIGURATIONS (FUNCIONA PORRA)
    # -------------------------------------------------------------------------
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # pra escapar de flaggin
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Super Ultra Mega realistic, modern Linux Chrome User-Agent 
    chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })
    driver = webdriver.Chrome(options=chrome_options)
    
    # Overwrite navigator.webdriver to 'undefined' on page-load before any website script runs
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    # Fake standard browser features (plugins count, languages, webgl) to bypass advanced fingerprinting
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            // Overwrite languages
            Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en-US', 'en']});
            // Overwrite plugins count to look real
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            // Overwrite WebGL renderer info to look like a standard GPU instead of virtualized drivers
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Open Source Technology Center';
                if (parameter === 37446) return 'Mesa DRI Intel(R) HD Graphics 620 (Kaby Lake GT2)';
                return getParameter.apply(this, arguments);
            };
        """
    })
    


    # if that mf does not work... 
    return driver

def highlight_element(driver, element, color="#ff4393"):
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
        pass  

def close_possible_popups(driver):
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
        if VERBOSE:
            print(f"  {Colors.YELLOW}⚠️ [POPUP]{Colors.END} Active modal container found. Attempting ESC dismissal fallback...")
        try:
            # pyrefly: ignore [missing-import]
            from selenium.webdriver.common.keys import Keys
            active_elem = driver.switch_to.active_element
            if active_elem:
                active_elem.send_keys(Keys.ESCAPE)
                if VERBOSE:
                    print(f"  {Colors.DIM}  -> Sent native Keys.ESCAPE to active element.{Colors.END}")
        except Exception:
            pass
            
        if pyautogui:
            try:
                pyautogui.press('esc')
                if VERBOSE:
                    print(f"  {Colors.DIM}  -> Pressed physical ESC key via PyAutoGUI.{Colors.END}")
            except Exception:
                pass

def login_to_catho(driver, credentials: UserCredentials):

    wait = WebDriverWait(driver, 15)
    
    try:
        if TEST_MODE:
            login_file_path = os.path.abspath("Catho Login.html")
            if not os.path.exists(login_file_path):
                print(f"[TEST MODE] Error: Could not find 'Catho Login.html' at {login_file_path}")
                return
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
                    return
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
                    highlight_element(driver, cookie_btn, color="#25D366")
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
                    highlight_element(driver, signin_link, color="#3624d6")
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
        highlight_element(driver, email_field, color="#25D366" if TEST_MODE else "#3624d6")
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
        highlight_element(driver, password_field, color="#25D366" if TEST_MODE else "#3624d6")
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
        highlight_element(driver, submit_btn, color="#25D366" if TEST_MODE else "#3624d6")
        
        # If in TEST_MODE, pause briefly to show fields filled, then click
        if TEST_MODE:
            time.sleep(2.0)
            
        submit_btn.click()
        print("  -> Login form submitted successfully!")
        
        if TEST_MODE:
            print("  [TEST MODE] Successfully simulated login flow locally. Settle delay...")
            time.sleep(3.0)
            return
            
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
            
    except Exception as e:
        print(f"\n[Login Failed] Could not automate the login flow: {e}")
        print("Continuing directly to the scraping page in case you are already logged in or want to log in manually.")

def contains_senior_terms(text: str) -> bool:
    """
    Checks if the given text contains any senior-related keywords as distinct words.
    Uses regex word boundaries to avoid false positives.
    """
    joined = "|".join([re.escape(term) for term in SENIOR_TERMS])
    pattern = re.compile(rf'\b({joined})\b', re.IGNORECASE)
    return bool(pattern.search(text))

def process_page_buttons(driver) -> int:
    close_possible_popups(driver)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Locate all job card items (li tags) on the page
    cards = driver.find_elements(By.XPATH, "//li[@data-offer-item]")
    
    # Filter only cards that contain a clickable "Quero me candidatar" button
    valid_targets = []
    for card in cards:
        buttons = card.find_elements(By.XPATH, ".//button[contains(text(), 'Quero me candidatar')]")
        if buttons:
            valid_targets.append((card, buttons[0]))
            
    total_valid = len(valid_targets)
    print(f"\n{Colors.BLUE}🔍 [Page Scraper]{Colors.END} Found {Colors.BOLD}{len(cards)}{Colors.END} total job cards. {Colors.BOLD}{total_valid}{Colors.END} are active for application.")
    
    clicked_count = 0
    skipped_count = 0
    
    for index, (card, button) in enumerate(valid_targets, start=1):
        try:
            close_possible_popups(driver)
            
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
            if contains_senior_terms(card_text):
                skipped_count += 1
                if VERBOSE:
                    matched_term = "SENIOR/SN"
                    for term in SENIOR_TERMS:
                        if re.search(rf'\b{re.escape(term)}\b', card_text, re.IGNORECASE):
                            matched_term = term.upper()
                            break
                    print(f"  {Colors.YELLOW}⏭ [SKIPPED]{Colors.END} Skipping Senior role: '{Colors.BOLD}{job_title}{Colors.END}' (Matched: {Colors.YELLOW}{matched_term}{Colors.END})")
                continue
                
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                button
            )
            time.sleep(0.5) 
            print(f"  {Colors.CYAN}➤{Colors.END} Targeting: '{Colors.BOLD}{job_title}{Colors.END}' ({index}/{total_valid})... ", end="", flush=True)
            highlight_element(driver, button, color="#ff4393" if TEST_MODE else "#3624d6")
            
            try:
                button.click()
                print(f"{Colors.GREEN}✔ [CLICK]{Colors.END}")
                clicked_count += 1
            except Exception as click_err:
                if VERBOSE:
                    print(f"\n  {Colors.YELLOW}⚡ [INFO]{Colors.END} Click intercepted or failed. Clearing popups & retrying...")
                close_possible_popups(driver)
                time.sleep(0.6)
                try:
                    button.click()
                    print(f"{Colors.GREEN}✔ [CLICK (Retry)]{Colors.END}")
                    clicked_count += 1
                except Exception:
                    if VERBOSE:
                        print(f"\n  {Colors.YELLOW}⚙ [JS FALLBACK]{Colors.END} Standard click blocked. Clicking button via JavaScript...")
                    driver.execute_script("arguments[0].click();", button)
                    print(f"{Colors.GREEN}✔ [CLICK (JS)]{Colors.END}")
                    clicked_count += 1
                    
            # Immediately check and dismiss any success/confirmation modal that appeared
            time.sleep(0.6)
            close_possible_popups(driver)
            
            # 4. Human-simulation sleep delay
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            if VERBOSE:
                print(f"  {Colors.BLUE}⏳ [HUMAN DELAY]{Colors.END} Waiting {Colors.BOLD}{delay:.2f}{Colors.END} seconds...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"\n  {Colors.RED}✘ [WARN]{Colors.END} Failed to process card {index}: {e}")
            
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
    load_env_configurations()
    print_banner()
    
    email = CATHO_EMAIL
    password = CATHO_PASSWORD
    
    # Prompt securely in the console if still default placeholders and not found in .env
    if not TEST_MODE:
        if email == "your_email@example.com" or not email:
            print(f"\n{Colors.BOLD}=== Catho Login Credentials ==={Colors.END}")
            email = input("Enter your Catho Email/CPF: ").strip()
        if password == "your_password" or not password:
            password = getpass.getpass("Enter your Catho Password (secure input, hidden): ")
            
    credentials = UserCredentials(email=email, password=password)
    
    driver = setup_driver(headless=False)
    
    try:
        if TEST_MODE:
            print(f"\n{Colors.HEADER}{Colors.BOLD}⚙️ [[ TEST MODE ACTIVE ]]{Colors.END}")
            print(f"{Colors.CYAN}➤ 1.{Colors.END} Opening Chromium to the default start page/new tab...")
            time.sleep(2.0)
            
            print(f"{Colors.CYAN}➤ 2.{Colors.END} Locating the Catho shortcut link on Chromium home page...")
            catho_link = None
            
            # Since standard chrome://newtab uses Shadow DOM,search via standard DOM selectors first
            catho_link_selectors = [
                (By.CSS_SELECTOR, "a[aria-label='Catho']"),
                (By.XPATH, "//a[contains(@href, 'vagas/programador')]"),
                (By.CSS_SELECTOR, "a[href*='catho.com.br']")
            ]
            
            for by, selector in catho_link_selectors:
                try:
                    catho_link = WebDriverWait(driver, 4).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    break
                except Exception:
                    continue
            
            # If not directly in global DOM, deep recursive Shadow DOM via JS
            if not catho_link:
                try:
                    catho_link = driver.execute_script("""
                        function findInShadows(root, selector) {
                            if (!root) return null;
                            const el = root.querySelector(selector);
                            if (el) return el;
                            const shadowHosts = root.querySelectorAll('*');
                            for (const host of shadowHosts) {
                                if (host.shadowRoot) {
                                    const found = findInShadows(host.shadowRoot, selector);
                                    if (found) return found;
                                }
                            }
                            return null;
                        }
                        return findInShadows(document, "a[aria-label='Catho']") || 
                               findInShadows(document, "a[href*='catho.com.br']");
                    """)
                except Exception:
                    pass
            
            clicked_shortcut = False
            if catho_link:
                print(f"  {Colors.GREEN}✔{Colors.END} Found Catho shortcut button on starting page!")
                delay = random.uniform(1.8, 3.2)
                print(f"  {Colors.BLUE}⏳ [HUMAN DELAY]{Colors.END} Waiting {Colors.BOLD}{delay:.2f}{Colors.END} seconds to simulate natural interaction...")
                time.sleep(delay)
                highlight_element(driver, catho_link, color="#ff4393")
                
                try:
                    catho_link.click()
                    clicked_shortcut = True
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", catho_link)
                        clicked_shortcut = True
                    except Exception as e:
                        print(f"  {Colors.YELLOW}⚠ [WARN]{Colors.END} Failed to click shortcut: {e}")
                    
                if clicked_shortcut:
                    print(f"  {Colors.GREEN}✔ [CLICK]{Colors.END} Successfully clicked the Catho shortcut button!")
                    
                    if pyautogui:
                        pyautogui_delay = random.uniform(1.0, 2.0)
                        print(f"  {Colors.BLUE}⏳ [PyAutoGUI]{Colors.END} Waiting {Colors.BOLD}{pyautogui_delay:.2f}{Colors.END} seconds before pressing ESC...")
                        time.sleep(pyautogui_delay)
                        
                        esc_presses = random.randint(3, 7)
                        print(f"  {Colors.BLUE}⌨ [PyAutoGUI]{Colors.END} Pressing ESC key {Colors.BOLD}{esc_presses}{Colors.END} times to dismiss initial focus/popovers...")
                        for p in range(1, esc_presses + 1):
                            pyautogui.press('esc')
                            time.sleep(0.15)
                        print(f"  {Colors.GREEN}✔ [PyAutoGUI]{Colors.END} ESC key presses completed successfully.")
            
            if not clicked_shortcut:
                print(f"  {Colors.YELLOW}⚠ [WARN]{Colors.END} Catho shortcut link not found in Chromium startup screen. Will navigate directly to search URLs...")
                time.sleep(1.5)
            else:
                print(f"{Colors.CYAN}➤ 3.{Colors.END} Waiting for redirection to the Catho jobs page...")
                try:
                    WebDriverWait(driver, 10).until(
                        EC.url_contains("catho.com.br/vagas/programador")
                    )
                    print(f"  {Colors.GREEN}✔ [SUCCESS]{Colors.END} Landing page verified: {Colors.UNDERLINE}{driver.current_url}{Colors.END}")
                except Exception:
                    print(f"  {Colors.YELLOW}ℹ [INFO]{Colors.END} Redirection took longer or landed on: {Colors.UNDERLINE}{driver.current_url}{Colors.END}")
                
            print(f"{Colors.CYAN}➤ 4.{Colors.END} Redirection verified! Transitioning to the dynamic scraping loop...")
            time.sleep(1.5)
            
        else:
            # 3. Handle Production Login Step (Only in non-TEST_MODE)
            login_to_catho(driver, credentials)
            
        # ==========================================
        # WORKLIST LOOP
        # ==========================================
        for keyword in KEYWORDS_WORKLIST:
            formatted_keyword = keyword.lower().replace(" ", "-")
            target_url = get_url_for_keyword(REAL_BASE_URL, keyword)
            
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
            while current_page <= MAX_PAGES_TO_SCRAPE:
                print(f"\n{Colors.HEADER}{Colors.BOLD}{'-'*50}\n📄 SCRAPING {keyword.upper()} - PAGE {current_page}\n{'-'*50}{Colors.END}")            
                clicked_count = process_page_buttons(driver)
                
                # If we applied to 0 jobs, we either hit already applied ones or there are no more jobs for this keyword.
                if clicked_count == 0:
                    print(f"\n{Colors.YELLOW}📋 [Worklist]{Colors.END} Found 0 application buttons on page {current_page} for '{keyword}'. Moving to next keyword in worklist...")
                    break
                    
                if current_page >= MAX_PAGES_TO_SCRAPE:
                    print(f"\n{Colors.GREEN}📋 [Worklist]{Colors.END} Reached the cap of {Colors.BOLD}{MAX_PAGES_TO_SCRAPE}{Colors.END} pages for '{keyword}'.")
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
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button)
                        time.sleep(0.5)
                        next_button.click()
                        current_page += 1
                        time.sleep(random.uniform(2.0, 4.0))
                    except Exception as click_err:
                        print(f"  {Colors.YELLOW}⚠️ [Pagination Click Failed]{Colors.END} Click blocked: {click_err}. Navigating directly...")
                        next_button = None
                
                if not next_button:
                    connector = "&" if "?" in target_url else "?"
                    next_page_url = f"{target_url}{connector}page={current_page + 1}"
                    print(f"  {Colors.CYAN}➤{Colors.END} Pagination button not clickable/found. Navigating directly to URL: {Colors.UNDERLINE}{next_page_url}{Colors.END}")
                    driver.get(next_page_url)
                    current_page += 1
                    time.sleep(random.uniform(2.0, 4.0))

    except Exception as e:
        print(f"\n{Colors.RED}❌ [CRITICAL ERROR]{Colors.END} Scraper execution halted: {e}")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🛑 [KeyboardInterrupt]{Colors.END} Scraper execution interrupted by user.")
        driver.quit()

    finally:
        print(f"\n{Colors.GREEN}🏁 All tasks completed.{Colors.END} Closing browser window...")
        driver.quit()

if __name__ == "__main__":
    run_scraper()
    
