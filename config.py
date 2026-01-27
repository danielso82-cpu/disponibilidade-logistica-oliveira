import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///oliveira.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

TIPOS_RODADO = [
    "Caçamba 5m³",
    "HR 4x4 Basculante",
    "HR Carroceria",
    "Caçamba / Carroceria 3m³",
    "Carroceria 6m (VUC)",
    "Munck",
]

MAPA_TIPO_RODADO = {
    "02-Toco": "Caçamba 5m³",
    "04-VAN": "HR 4x4 Basculante",
    "05-Utilitário": "HR Carroceria",
    "06-Outros": "Caçamba / Carroceria 3m³",
    "07-VUC": "Carroceria 6m (VUC)",
    "00-Não Aplicável": "Munck",
}
