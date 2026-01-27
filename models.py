from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Motorista(db.Model):
    __tablename__ = "motoristas"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    base = db.Column(db.String(50), nullable=False)  # Rio Tavares / Costeira
    cnh_categoria = db.Column(db.String(10), nullable=True)

class Veiculo(db.Model):
    __tablename__ = "veiculos"
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(10), unique=True, nullable=False)
    modelo = db.Column(db.String(120), nullable=True)
    base = db.Column(db.String(50), nullable=False)
    tipo_rodado = db.Column(db.String(60), nullable=False)

class DispMotorista(db.Model):
    __tablename__ = "disp_motoristas"
    id = db.Column(db.Integer, primary_key=True)
    data_operacao = db.Column(db.Date, nullable=False, index=True)
    motorista_id = db.Column(db.Integer, db.ForeignKey("motoristas.id"), nullable=False)
    tipo_rodado = db.Column(db.String(60), nullable=False)
    status = db.Column(db.String(30), nullable=False)  # Disponível, Folga, Férias...
    periodo = db.Column(db.String(20), nullable=True)  # Integral/Manhã/Tarde
    obs = db.Column(db.String(300), nullable=True)

    motorista = db.relationship("Motorista")

class DispVeiculo(db.Model):
    __tablename__ = "disp_veiculos"
    id = db.Column(db.Integer, primary_key=True)
    data_operacao = db.Column(db.Date, nullable=False, index=True)
    veiculo_id = db.Column(db.Integer, db.ForeignKey("veiculos.id"), nullable=False)
    status = db.Column(db.String(30), nullable=False)  # Disponível, Manutenção...
    previsao_liberacao = db.Column(db.String(20), nullable=True)
    obs = db.Column(db.String(300), nullable=True)

    veiculo = db.relationship("Veiculo")
