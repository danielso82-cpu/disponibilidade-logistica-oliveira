# Disponibilidade - Logística Oliveira (MVP)

Controle D-1 de disponibilidade de frota e motoristas + consolidado por tipo de rodado.

## Rodar local
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env  # no Windows, crie manual
python app.py
