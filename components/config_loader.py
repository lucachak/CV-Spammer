import os
from dataclasses import dataclass, field

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
    CHROME_PROFILE_DIR: str = ""
    DEFAULT_DESCRIPTION_TEXT: str = "Tenho ampla experiência na área, sempre focado em entregar resultados com qualidade técnica e alinhamento aos objetivos da empresa. Sou proativo e busco melhorar continuamente."
    MAX_DAILY_APPLICATIONS: int = 12

@dataclass
class UserCredentials:
    email: str = "your_email@example.com"
    password: str = "your_password"
    linkedin_password: str = ""

def load_env_configurations():
    """
    Helper function to safely parse all configuration variables from the local .env
    and override defaults if they exist.
    """
    from components.browser_engine import Colors
    
    config = ScraperConfig()
    credentials = UserCredentials()
    
    # Busca .env na raiz do projeto
    workspace_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    env_path = os.path.join(workspace_dir, ".env")
    
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
                        elif key_str == "linkedin_passwd":
                            credentials.linkedin_password = val_str
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
                        elif key_str == "CHROME_PROFILE_DIR":
                            config.CHROME_PROFILE_DIR = val_str
                        elif key_str == "DEFAULT_DESCRIPTION_TEXT":
                            config.DEFAULT_DESCRIPTION_TEXT = val_str
                        elif key_str == "MAX_DAILY_APPLICATIONS":
                            try:
                                config.MAX_DAILY_APPLICATIONS = int(val_str)
                            except ValueError:
                                pass
                                
            print(f"{Colors.GREEN}✔{Colors.END} {Colors.BOLD}[.env Loaded]{Colors.END} Configurations and credentials loaded successfully from local .env file.")
        except Exception as e:
            print(f"{Colors.RED}✘{Colors.END} {Colors.BOLD}[.env Read Error]{Colors.END} Could not parse .env file: {e}")
            
    return config, credentials
