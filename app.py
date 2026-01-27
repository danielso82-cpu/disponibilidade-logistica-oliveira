from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, date
from config import Config, TIPOS_RODADO
from models import db, Motorista, Veiculo, DispMotoristaDia, DispVeiculo

def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.get("/")
    def index():
        # data padrão = amanhã (D-1 preenchendo)
        d = request.args.get("data")
        if d:
            data_ref = parse_date(d)
        else:
            data_ref = date.today()
        return render_template("index.html", data_ref=data_ref)

    # ---------------- Motoristas ----------------
    @app.get("/disponibilidade/motoristas")
def disp_motoristas():
    d = request.args.get("data")
    if not d:
        return redirect(url_for("index"))
    data_ref = parse_date(d)

    motoristas = Motorista.query.order_by(Motorista.base, Motorista.nome).all()
    regs = DispMotoristaDia.query.filter_by(data_operacao=data_ref).all()
    regs_map = {r.motorista_id: r for r in regs}

    return render_template(
        "disp_motoristas.html",
        data_ref=data_ref,
        motoristas=motoristas,
        regs_map=regs_map,
    )


    # ---------------- Veículos ----------------
    @app.get("/disponibilidade/veiculos")
def disp_veiculos():
    d = request.args.get("data")
    if not d:
        return redirect(url_for("index"))
    data_ref = parse_date(d)

    veiculos = Veiculo.query.order_by(Veiculo.base, Veiculo.tipo_rodado, Veiculo.placa).all()
    regs = DispVeiculo.query.filter_by(data_operacao=data_ref).all()
    regs_map = {r.veiculo_id: r for r in regs}

    return render_template("disp_veiculos.html", data_ref=data_ref, veiculos=veiculos, regs_map=regs_map)


    # ---------------- Disponibilidade Motoristas ----------------
    @app.get("/disponibilidade/motoristas")
    def disp_motoristas():
        d = request.args.get("data")
        if not d:
            return redirect(url_for("index"))
        data_ref = parse_date(d)

        motoristas = Motorista.query.order_by(Motorista.base, Motorista.nome).all()
        regs = DispMotorista.query.filter_by(data_operacao=data_ref).all()
        regs_map = {(r.motorista_id, r.tipo_rodado): r for r in regs}

        return render_template(
            "disp_motoristas.html",
            data_ref=data_ref,
            motoristas=motoristas,
            tipos=TIPOS_RODADO,
            regs_map=regs_map,
        )

    @app.post("/disponibilidade/motoristas/salvar")
    @app.post("/disponibilidade/motoristas/salvar")
def disp_motoristas_salvar():
    data_ref = parse_date(request.form["data_operacao"])

    # limpa e recria o dia (MVP simples e robusto)
    DispMotoristaDia.query.filter_by(data_operacao=data_ref).delete()
    db.session.commit()

    motorista_ids = request.form.getlist("motorista_id")
    disponiveis = set(request.form.getlist("disponivel"))  # ids marcados

    statuses = request.form.getlist("status")
    periodos = request.form.getlist("periodo")
    obs_list = request.form.getlist("obs")

    for mid, st, p, ob in zip(motorista_ids, statuses, periodos, obs_list):
        # se está marcado como disponível, força status "Disponível"
        if mid in disponiveis:
            st_final = "Disponível"
        else:
            st_final = st or "Falta"

        db.session.add(
            DispMotoristaDia(
                data_operacao=data_ref,
                motorista_id=int(mid),
                status=st_final,
                periodo=(p or None),
                obs=(ob or "").strip() or None,
            )
        )

    db.session.commit()
    flash("Disponibilidade de motoristas salva.", "ok")
    return redirect(url_for("disp_motoristas", data=data_ref.isoformat()))


    # ---------------- Disponibilidade Veículos ----------------
    @app.get("/disponibilidade/veiculos")
    def disp_veiculos():
        d = request.args.get("data")
        if not d:
            return redirect(url_for("index"))
        data_ref = parse_date(d)

        veiculos = Veiculo.query.order_by(Veiculo.base, Veiculo.tipo_rodado, Veiculo.placa).all()
        regs = DispVeiculo.query.filter_by(data_operacao=data_ref).all()
        regs_map = {r.veiculo_id: r for r in regs}

        return render_template(
            "disp_veiculos.html",
            data_ref=data_ref,
            veiculos=veiculos,
            regs_map=regs_map,
        )

    @app.post("/disponibilidade/veiculos/salvar")
def disp_veiculos_salvar():
    data_ref = parse_date(request.form["data_operacao"])

    DispVeiculo.query.filter_by(data_operacao=data_ref).delete()
    db.session.commit()

    veiculo_ids = request.form.getlist("veiculo_id")
    disponiveis = set(request.form.getlist("disponivel_veic"))

    statuses = request.form.getlist("status")
    previsoes = request.form.getlist("previsao_liberacao")
    obs_list = request.form.getlist("obs")

    for vid, st, pr, ob in zip(veiculo_ids, statuses, previsoes, obs_list):
        if vid in disponiveis:
            st_final = "Disponível"
        else:
            st_final = st or "Manutenção"

        db.session.add(
            DispVeiculo(
                data_operacao=data_ref,
                veiculo_id=int(vid),
                status=st_final,
                previsao_liberacao=(pr or "").strip() or None,
                obs=(ob or "").strip() or None,
            )
        )

    db.session.commit()
    flash("Disponibilidade de veículos salva.", "ok")
    return redirect(url_for("disp_veiculos", data=data_ref.isoformat()))

    # ---------------- Consolidado ----------------
    @app.get("/consolidado")
    def consolidado():
        d = request.args.get("data")
        if not d:
            return redirect(url_for("index"))
        data_ref = parse_date(d)

        # Veículos disponíveis por tipo
        veiculos_disp = (
            db.session.query(Veiculo.tipo_rodado, db.func.count(Veiculo.id))
            .join(DispVeiculo, DispVeiculo.veiculo_id == Veiculo.id)
            .filter(DispVeiculo.data_operacao == data_ref)
            .filter(DispVeiculo.status == "Disponível")
            .group_by(Veiculo.tipo_rodado)
            .all()
        )
        veic_map = {t: c for t, c in veiculos_disp}

        # Motoristas disponíveis por tipo
mot_disp = (
    db.session.query(DispMotoristaDia.status, db.func.count(DispMotoristaDia.id))
    .filter(DispMotoristaDia.data_operacao == data_ref)
    .filter(DispMotoristaDia.status == "Disponível")
    .count()
)

        mot_map = {t: c for t, c in mot_disp}

        linhas = []
        for t in TIPOS_RODADO:
            v = int(veic_map.get(t, 0))
            m = int(mot_map.get(t, 0))
            if v == 0 and m == 0:
                status = "⛔ Indisponível"
            elif v < m:
                status = "🔴 Falta veículo"
            elif v > m:
                status = "⚠️ Falta motorista"
            else:
                status = "✅ OK"
            linhas.append({"tipo": t, "veiculos": v, "motoristas": m, "status": status})

        return render_template("consolidado.html", data_ref=data_ref, linhas=linhas)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)



