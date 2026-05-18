import os
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
# DEFAULT CONFIGURATIONS (Overrideable via .env)
# ==========================================
TEST_MODE = True
REAL_BASE_URL = "https://www.catho.com.br/vagas/programador-python/sao-paulo-sp/?order=dataAtualizacao"
MAX_PAGES_TO_SCRAPE = 50
CATHO_EMAIL = "your_email@example.com"
CATHO_PASSWORD = "your_password"
MIN_DELAY = 1.5
MAX_DELAY = 3.0
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
    global TEST_MODE, REAL_BASE_URL, MAX_PAGES_TO_SCRAPE, CATHO_EMAIL, CATHO_PASSWORD, MIN_DELAY, MAX_DELAY
    
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
                                
            print("[.env Loaded] Configurations and credentials loaded successfully from local .env file.")
        except Exception as e:
            print(f"[.env Read Error] Could not parse .env file: {e}")

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
        print(f"\n[Chrome Profile] Detected custom 'Default' profile inside src. Loading persistent session from: {src_dir}")
        chrome_options.add_argument(f"--user-data-dir={src_dir}")
        chrome_options.add_argument("--profile-directory=Default")
    else:
        # Fallback to root Default folder if exists
        default_profile_path = os.path.join(workspace_dir, "Default")
        if os.path.exists(default_profile_path):
            print(f"\n[Chrome Profile] Detected custom 'Default' profile. Loading persistent session from: {workspace_dir}")
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
        (By.XPATH, "//button[contains(text(), 'Entendi')]"),
        (By.XPATH, "//button[contains(text(), 'Fechar')]"),
        (By.XPATH, "//span[contains(text(), 'Fechar')]")
    ]
    
    for by, selector in popup_selectors:
        try:
            elements = driver.find_elements(by, selector)
            for elem in elements:
                try:
                    is_shown = elem.is_displayed()
                except Exception:
                    is_shown = True
                    
                if is_shown:
                    print(f"  [POPUP DETECTED] Closing popup using: {selector}")
                    driver.execute_script("arguments[0].click();", elem)
                    time.sleep(0.5)
        except Exception:
            continue

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

def process_page_buttons(driver) -> int:
    button_xpath = "//button[contains(text(), 'Quero me candidatar')]"
    close_possible_popups(driver)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    buttons = driver.find_elements(By.XPATH, button_xpath)
    button_count = len(buttons)
    print(f"\n[Page Scraper] Found {button_count} application button(s) on this page.")
    
    for index, button in enumerate(buttons, start=1):
        try:
            close_possible_popups(driver)
            
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                button
            )
            time.sleep(0.5) 
            print(f"  -> Targeting button {index}/{button_count}...")
            highlight_element(driver, button, color="#ff4393" if TEST_MODE else "#3624d6")
            
            try:
                button.click()
                print(f"  [CLICK] Successfully clicked button {index}!")
            except Exception as click_err:
                print(f"  [INFO] Click intercepted or failed: {click_err}. Clearing popups & retrying...")
                close_possible_popups(driver)
                time.sleep(0.6)
                try:
                    button.click()
                    print(f"  [CLICK] Successfully clicked button {index} after clearing popup!")
                except Exception:
                    print(f"  [JS FALLBACK] Standard click blocked. Clicking button via JavaScript...")
                    driver.execute_script("arguments[0].click();", button)
                    print(f"  [CLICK] Successfully clicked button {index} via JS!")
                    
            # Immediately check and dismiss any success/confirmation modal that appeared
            time.sleep(0.6)
            close_possible_popups(driver)
            
            # 4. Human-simulation sleep delay
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            print(f"  [HUMAN DELAY] Waiting {delay:.2f} seconds to simulate natural interaction...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"  [WARN] Failed to click button {index}: {e}")
            
    return button_count

def run_scraper():
    # 1. Load all configurations and credentials dynamically from local .env
    load_env_configurations()
    
    email = CATHO_EMAIL
    password = CATHO_PASSWORD
    
    # Prompt securely in the console if still default placeholders and not found in .env
    if not TEST_MODE:
        if email == "your_email@example.com" or not email:
            print("\n=== Catho Login Credentials ===")
            email = input("Enter your Catho Email/CPF: ").strip()
        if password == "your_password" or not password:
            password = getpass.getpass("Enter your Catho Password (secure input, hidden): ")
            
    credentials = UserCredentials(email=email, password=password)
    
    driver = setup_driver(headless=False)
    current_page = 1
    
    try:
        if TEST_MODE:
            print("\n[[ TEST MODE ACTIVE ]]")
            print("1. Opening Chromium to the default start page/new tab...")
            time.sleep(3.0)
            
            print("2. Locating the Catho shortcut link on Chromium home page...")
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
            
            if catho_link:
                print("  -> Found Catho shortcut button on starting page!")
                delay = random.uniform(1.8, 3.2)
                print(f"  [HUMAN DELAY] Waiting {delay:.2f} seconds to simulate natural interaction...")
                time.sleep(delay)
                highlight_element(driver, catho_link, color="#ff4393")
                
                try:
                    catho_link.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", catho_link)
                    
                print("  [CLICK] Successfully clicked the Catho shortcut button!")
                
                if pyautogui:
                    pyautogui_delay = random.uniform(1.0, 3.0)
                    print(f"  [PyAutoGUI] Waiting {pyautogui_delay:.2f} seconds before pressing ESC...")
                    time.sleep(pyautogui_delay)
                    
                    esc_presses = random.randint(3, 7)
                    print(f"  [PyAutoGUI] Pressing ESC key {esc_presses} times to dismiss initial focus/popovers...")
                    for p in range(1, esc_presses + 1):
                        pyautogui.press('esc')
                        time.sleep(0.15)
                    print("  [PyAutoGUI] ESC key presses completed successfully.")
            else:
                print("  [WARN] Catho shortcut link not found in Chromium startup screen. Navigating directly to URL...")
                time.sleep(1.5)
                driver.get("https://www.catho.com.br/vagas/programador")
                
            print("3. Waiting for redirection to the Catho jobs page...")
            try:
                WebDriverWait(driver, 10).until(
                    EC.url_contains("catho.com.br/vagas/programador")
                )
                print(f"  [SUCCESS] Landing page verified: {driver.current_url}")
            except Exception:
                print(f"  [INFO] Redirection took longer or landed on: {driver.current_url}")
                
            print("4. Redirection verified! Transitioning to the dynamic scraping loop...")
            time.sleep(2.0)
            
        else:
            # 3. Handle Production Login Step (Only in non-TEST_MODE)
            login_to_catho(driver, credentials)
                
            # 4. Determine starting URL/file for job scraping
            start_url = REAL_BASE_URL
            print(f"\n[[ PRODUCTION MODE ACTIVE ]]")
            print(f"Starting with production URL: {start_url}")
            driver.get(start_url)
        
        while current_page <= MAX_PAGES_TO_SCRAPE:
            print(f"\n{'='*50}\nSCRAPING PAGE {current_page}\n{'='*50}")            
            clicked_count = process_page_buttons(driver)
            if current_page >= MAX_PAGES_TO_SCRAPE:
                print(f"\n[Scraper Completed] Reached the cap of {MAX_PAGES_TO_SCRAPE} pages.")
                break
                
            print(f"\n[Pagination] Preparing to move to Page {current_page + 1}...")
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.next-page"))
                )
                print("  -> Found 'Próxima' pagination button. Clicking...")
                next_button.click()
                current_page += 1
                
                time.sleep(random.uniform(2.0, 4.0))
            except Exception as click_err:
                print(f"  [Pagination Fallback] Click failed or blocked: {click_err}")
                connector = "&" if "?" in REAL_BASE_URL else "?"
                next_page_url = f"{REAL_BASE_URL}{connector}page={current_page + 1}"
                print(f"  -> Navigating directly to URL: {next_page_url}")
                driver.get(next_page_url)
                current_page += 1
                time.sleep(random.uniform(2.0, 4.0))

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Scraper execution halted: {e}")
        
    except KeyboardInterrupt:
        print("\n[KeyboardInterrupt] Scraper execution interrupted by user.")
        driver.quit()

    finally:
        print("\nAll tasks completed. Closing browser window...")
        driver.quit()

if __name__ == "__main__":
    run_scraper()
    
