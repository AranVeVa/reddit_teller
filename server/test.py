import os
import psycopg2
from dotenv import load_dotenv

# Carga el archivo .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    print("Conexión exitosa a la base de datos de Neon")
    
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print("Versión de PostgreSQL:", cur.fetchone())
    
    cur.close()
    conn.close()
except Exception as error:
    print("Error de conexión:", error)