import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GreenDeal Configuration
GREENDEAL_EMAIL = os.getenv("GREENDEAL_EMAIL")
GREENDEAL_PASSWORD = os.getenv("GREENDEAL_PASSWORD")
GREENDEAL_LOGIN_URL = os.getenv("GREENDEAL_LOGIN_URL")
GREENDEAL_CREATE_JOB_URL = os.getenv("GREENDEAL_CREATE_JOB_URL")

# GreenSketch (Playwright scraper — signed projects / job sheets)
GREENSKETCH_EMAIL = os.getenv("GREENSKETCH_EMAIL")
GREENSKETCH_PASSWORD = os.getenv("GREENSKETCH_PASSWORD")
GREENSKETCH_SIGNIN_URL = os.getenv("GREENSKETCH_SIGNIN_URL", "https://greensketch.ai/au/sign-in")
GREENSKETCH_PROJECTS_URL = os.getenv("GREENSKETCH_PROJECTS_URL", "https://greensketch.ai/au/projects")

# BridgeSelect Configuration
BRIDGESELECT_USERNAME = os.getenv("BRIDGESELECT_USERNAME")
BRIDGESELECT_OTP = os.getenv("BRIDGESELECT_OTP")
BRIDGESELECT_LOGIN_URL = "https://bridgeselect.com.au/sunvault/web/login.html"
BRIDGESELECT_JOBS_URL = "https://bridgeselect.com.au/sunvault/web/jobs.html"
