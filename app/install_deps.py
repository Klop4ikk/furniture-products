import sys
import subprocess

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Устанавливаем необходимые библиотеки
install("sqlalchemy")
install("psycopg[binary]")
install("fastapi")
install("uvicorn[standard]")
install("pydantic")
install("python-dotenv")
