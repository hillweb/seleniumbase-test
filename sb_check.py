import os
import shutil
import seleniumbase

print("SeleniumBase:", seleniumbase.__file__)
print("Chrome:", shutil.which("google-chrome"))
print("Chromium:", shutil.which("chromium"))
print("ChromeDriver:", shutil.which("chromedriver"))
print("PATH:", os.environ.get("PATH"))
