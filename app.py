from __future__ import annotations

from datetime import date, datetime
import csv
import io

from flask import Flask, flash, redirect, render_template, request, url_for

from config import Config, TIPOS_RODADO
from models import (
    db,
    Motorista,
    Veiculo,
    DispVeiculo,
    DispMotoristaDia,
)

# ---------------- Utils ----------------

def parse_date(s: str | None) -> date:
    if not s:
        return date.today()
    return datetime.strptime(s, "%Y-%m-%d").date()

def today_iso() -> str:
    return date.today().isoformat()

def norm(s: str | None) -> str:
    return (s or "").strip()


# ---------------- App Factory ----------------

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ---------- Navegação ----------
    @app.get("/")
    def index():
        return redirect(url_for("consolidado", data=today_iso()))

    # ---------- Cadastros ----------
    @app.get("/veiculos")
    def veiculos():
        rows = Veiculo.query.order_by(Veiculo.base.asc(), Veiculo.tipo_rodado.asc(), Veiculo.placa.asc()).all()
        return render_template("veiculos.html", veiculos=rows, tipos_rodado=TIPOS_RODADO)

    @app.post("/veiculos")
    def veiculos_add():
        placa = norm(request.form.get("placa"))
        modelo = norm(request.form.get("modelo"))
        base = norm(request.form.get("base"))
        tipo = norm(request.form.get("tipo_rodado"))

        if not placa or not base or not tipo:
            flash("Preencha Placa, Base e Tipo.", "err")
            return redirect(url_for("veiculos"))

        exists = Veiculo.query.filter_by(placa=placa).first()
        if exists:
            flash("Já existe veículo com essa placa.", "err")
            return redirect(url_for("veiculos"))

        db.session.add(Veiculo(placa=placa, modelo=modelo or None, base=base, tipo_rodado=tipo))
        db.session.commit()
        flash("Veículo cadastrado.", "ok")
        return redirect(url_for("veiculos"))

    @app.get("/motoristas")
    def motoristas():
        rows = Motorista.query.order_by(Motorista.base.asc(), Motorista.nome.asc()).all()
        return render_template("motoristas.html", motoristas=rows)

    @app.post("/motoristas")
    def motoristas_add():
        nome = norm(request.form.get("nome"))
        base = norm(request.form.get("base"))

        if not nome or not base:
            flash("Preencha Nome e Base.", "err")
            return redirect(url_for("motoristas"))

        exists = Motorista.query.filter_by(nome=nome).first()
        if exists:
            flash("Já existe motorista com esse nome.", "err")
            return redirect(url_for("motoristas"))

        db.session.add(Motorista(nome=nome, base=base))
        db.session.commit()
        flash("Motorista cadastrado.", "ok")
        return redirect(url_for("motoristas"))

    # ---------- Importar ----------
    @app.get("/importar")
    def importar():
        return render_template("importar.html")

    @app.post("/importar/veiculos")
    def importar_veiculos():
        """
        CSV (colunas esperadas):
        placa,modelo,base,tipo_rodado
        """
        csv_text = request.form.get("csv_veiculos", "")
        if not norm(csv_text):
            flash("Cole o CSV de veículos.", "err")
            return redirect(url_for("importar"))

        f = io.StringIO(csv_text)
        reader = csv.DictReader(f)
        count = 0

        for row in reader:
            placa = norm(row.get("placa"))
            modelo = norm(row.get("modelo"))
            base = norm(row.get("base"))
            tipo = norm(row.get("tipo_rodado"))

            if not placa or not base or not tipo:
                continue

            if not Veiculo.query.filter_by(placa=placa).first():
                db.session.add(Veiculo(placa=placa, modelo=modelo or None, base=base, tipo_rodado=tipo))
                count += 1

        db.session.commit()
        flash(f"Veículos importados: {count}", "ok")
        return redirect(url_for("veiculos"))

    @app.post("/importar/motoristas")
    def importar_motoristas():
        """
        CSV (colunas esperadas):
        nome,base
        """
        csv_text = request.form.get("csv_motoristas", "")
        if not norm(csv_text):
            flash("Cole o CSV de motoristas.", "err")
            return redirect(url_for("importar"))

        f = io.StringIO(csv_text)
        reader = csv.DictReader(f)
        count = 0

        for row in reader:
            nome = norm(row.get("nome"))
            base = norm(row.get("base"))
            if not nome or not base:
                continue

            if not Motorista.query.filter_by(nome=nome).first():
                db.session.add(Motorista(nome=nome, base=base))
                count += 1

        db.session.commit()
        flash(f"Motoristas importados: {count}", "ok")
        return redirect(url_for("motoristas"))

    # ---------- Disponibilidade: Veículos ----------
    @app.get("/disponibilidade/veiculos")
    def disp_veiculos():
        data_ref = parse_date(request.args.get("data"))
        veics = Veiculo.query.order_by(Veiculo.base.asc(), Veiculo.tipo_rodado.asc(), Veiculo.placa.asc()).all()

        regs = (
            DispVeiculo.query.filter_by(data_operacao=data_ref).all()
        )
        reg_map = {r.veiculo_id: r for r in regs}

        return render_template(
            "disp_veiculos.html",
            data_ref=data_ref,
            veiculos=veics,
            regs_map=reg_map,
        )

    @app.post("/disponibilidade/veiculos/salvar")
    def disp_veiculos_salvar():
        data_ref = parse_date(request.form.get("data_operacao"))

        # Checkbox: se marcado, veículo está DISPONÍVEL.
        ids_disp = set(request.form.getlist("disponivel"))

        veics = Veiculo.query.all()
        veic_ids = [v.id for v in veics]

        # Remove registros existentes da data (recria tudo para ficar simples e consistente)
        DispVeiculo.query.filter(DispVeiculo.data_operacao == data_ref, DispVeiculo.veiculo_id.in_(veic_ids)).delete(
            synchronize_session=False
        )
        db.session.commit()

        for v in veics:
            is_disp = str(v.id) in ids_disp

            st = norm(request.form.get(f"status_{v.id}"))
            pr = norm(request.form.get(f"previsao_{v.id}"))
            ob = norm(request.form.get(f"obs_{v.id}"))

            if is_disp:
                st_final = "Disponível"
                pr_final = None
                ob_final = None
            else:
                # Se não marcou, considera indisponível e usa status selecionado.
                st_final = st or "Indisponível"
                pr_final = pr or None
                ob_final = ob or None

            db.session.add(
                DispVeiculo(
                    data_operacao=data_ref,
                    veiculo_id=v.id,
                    status=st_final,
                    previsao_liberacao=pr_final,
                    obs=ob_final,
                )
            )

        db.session.commit()
        flash("Disponibilidade de veículos salva.", "ok")
        return redirect(url_for("disp_veiculos", data=data_ref.isoformat()))

    # ---------- Disponibilidade: Motoristas ----------
    @app.get("/disponibilidade/motoristas")
    def disp_motoristas():
        data_ref = parse_date(request.args.get("data"))
        mots = Motorista.query.order_by(Motorista.base.asc(), Motorista.nome.asc()).all()

        regs = DispMotoristaDia.query.filter_by(data_operacao=data_ref).all()
        reg_map = {r.motorista_id: r for r in regs}

        return render_template(
            "disp_motoristas.html",
            data_ref=data_ref,
            motoristas=mots,
            regs_map=reg_map,
        )

    @app.post("/disponibilidade/motoristas/salvar")
    def disp_motoristas_salvar():
        data_ref = parse_date(request.form.get("data_operacao"))

        # Checkbox: se marcado, motorista está DISPONÍVEL.
        ids_disp = set(request.form.getlist("disponivel"))

        mots = Motorista.query.all()
        mot_ids = [m.id for m in mots]

        DispMotoristaDia.query.filter(
            DispMotoristaDia.data_operacao == data_ref, DispMotoristaDia.motorista_id.in_(mot_ids)
        ).delete(synchronize_session=False)
        db.session.commit()

        for m in mots:
            is_disp = str(m.id) in ids_disp

            st = norm(request.form.get(f"status_{m.id}"))
            pr = norm(request.form.get(f"previsao_{m.id}"))
            ob = norm(request.form.get(f"obs_{m.id}"))

            if is_disp:
                st_final = "Disponível"
                pr_final = None
                ob_final = None
            else:
                st_final = st or "Indisponível"
                pr_final = pr or None
                ob_final = ob or None

            db.session.add(
                DispMotoristaDia(
                    data_operacao=data_ref,
                    motorista_id=m.id,
                    status=st_final,
                    previsao_liberacao=pr_final,
                    obs=ob_final,
                )
            )

        db.session.commit()
        flash("Disponibilidade de motoristas salva.", "ok")
        return redirect(url_for("disp_motoristas", data=data_ref.isoformat()))

    # ---------- Consolidado ----------
    @app.get("/consolidado")
    def consolidado():
        data_ref = parse_date(request.args.get("data"))

        # Veículos: disponíveis e indisponíveis por tipo
        veic_disp = (
            db.session.query(Veiculo.tipo_rodado, db.func.count(DispVeiculo.id))
            .join(DispVeiculo, DispVeiculo.veiculo_id == Veiculo.id)
            .filter(DispVeiculo.data_operacao == data_ref)
            .filter(DispVeiculo.status == "Disponível")
            .group_by(Veiculo.tipo_rodado)
            .all()
        )
        veic_ind = (
            db.session.query(Veiculo.tipo_rodado, db.func.count(DispVeiculo.id))
            .join(DispVeiculo, DispVeiculo.veiculo_id == Veiculo.id)
            .filter(DispVeiculo.data_operacao == data_ref)
            .filter(DispVeiculo.status != "Disponível")
            .group_by(Veiculo.tipo_rodado)
            .all()
        )
        veic_disp_map = {t: c for t, c in veic_disp}
        veic_ind_map = {t: c for t, c in veic_ind}

        # Motoristas: total disponíveis e indisponíveis (não por tipo)
        mot_disp = (
            db.session.query(db.func.count(DispMotoristaDia.id))
            .filter(DispMotoristaDia.data_operacao == data_ref)
            .filter(DispMotoristaDia.status == "Disponível")
            .scalar()
        ) or 0

        mot_ind = (
            db.session.query(db.func.count(DispMotoristaDia.id))
            .filter(DispMotoristaDia.data_operacao == data_ref)
            .filter(DispMotoristaDia.status != "Disponível")
            .scalar()
        ) or 0

        linhas = []
        for tipo in TIPOS_RODADO:
            vd = int(veic_disp_map.get(tipo, 0))
            vi = int(veic_ind_map.get(tipo, 0))

            # Regra simples (mantém seu comportamento atual):
            # compara veículos do tipo vs motoristas totais.
            if vd <= 0 and mot_disp <= 0:
                status = ("Indisponível", "bad")
            elif vd <= 0 and mot_disp > 0:
                status = ("Falta veículo", "bad")
            elif vd > 0 and mot_disp <= 0:
                status = ("Falta motorista", "warn")
            else:
                status = ("OK", "ok")

            linhas.append(
                {
                    "tipo": tipo,
                    "veic_disp": vd,
                    "veic_ind": vi,
                    "mot_disp": mot_disp,
                    "mot_ind": mot_ind,
                    "status_txt": status[0],
                    "status_cls": status[1],
                }
            )

        return render_template("consolidado.html", data_ref=data_ref, linhas=linhas)

    return app


# Para rodar local: python app.py
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
