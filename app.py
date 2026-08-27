import os
from datetime import datetime

from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()

CAMPOS_OBRIGATORIOS_AGENDAMENTO = {"sala_id", "responsavel", "data_inicio", "data_fim"}


# --- MODELOS DO BANCO DE DADOS ---
class Sala(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    capacidade = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {"id": self.id, "nome": self.nome, "capacidade": self.capacidade}


class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sala_id = db.Column(db.Integer, db.ForeignKey("sala.id"), nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    data_inicio = db.Column(db.DateTime, nullable=False)
    data_fim = db.Column(db.DateTime, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "sala_id": self.sala_id,
            "responsavel": self.responsavel,
            "data_inicio": self.data_inicio.isoformat(),
            "data_fim": self.data_fim.isoformat(),
        }


# --- SERIALIZAÇÃO DE TRANSAÇÕES NO SQLITE ---
# Por padrão o SQLite abre transações em modo "deferred": duas requisições podem
# fazer o SELECT de conflito antes de qualquer uma delas ter commitado o INSERT,
# permitindo double-booking. Forçando BEGIN IMMEDIATE, a segunda transação que
# tentar escrever fica bloqueada até a primeira commitar, e ao rodar sua própria
# checagem de conflito já enxerga o agendamento recém-criado.
@event.listens_for(Engine, "connect")
def _sqlite_desliga_transacao_implicita(dbapi_connection, connection_record):
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        dbapi_connection.isolation_level = None


@event.listens_for(Engine, "begin")
def _sqlite_begin_immediate(conn):
    if conn.dialect.name == "sqlite":
        conn.exec_driver_sql("BEGIN IMMEDIATE")


def _erro(mensagem, status):
    return jsonify({"mensagem": mensagem}), status


def _validar_payload_agendamento(data):
    if not isinstance(data, dict):
        return "Corpo da requisição deve ser um JSON válido."
    faltantes = CAMPOS_OBRIGATORIOS_AGENDAMENTO - data.keys()
    if faltantes:
        return f"Campos obrigatórios ausentes: {', '.join(sorted(faltantes))}."
    if not isinstance(data.get("responsavel"), str) or not data["responsavel"].strip():
        return "O campo 'responsavel' não pode ser vazio."
    return None


def _parse_sala_id(data):
    try:
        return int(data["sala_id"]), None
    except (TypeError, ValueError):
        return None, "Campo 'sala_id' inválido."


def _parse_datas(data):
    try:
        inicio = datetime.fromisoformat(data["data_inicio"])
        fim = datetime.fromisoformat(data["data_fim"])
    except (TypeError, ValueError):
        return None, None, "Datas inválidas. Use o formato ISO (ex.: 2026-08-27T09:00)."
    if fim <= inicio:
        return None, None, "Erro: O horário de término deve ser posterior ao horário de início."
    return inicio, fim, None


def create_app(config=None):
    app = Flask(__name__)
    CORS(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///agendamentos.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if config:
        app.config.update(config)

    db.init_app(app)
    _registrar_rotas(app)
    return app


def _registrar_rotas(app):
    @app.route("/")
    def pagina_inicial():
        return render_template("index.html")

    @app.route("/salas", methods=["GET"])
    def get_salas():
        salas = Sala.query.all()
        return jsonify([sala.to_json() for sala in salas])

    @app.route("/salas/<int:sala_id>/agendamentos", methods=["GET"])
    def get_agendamentos_por_sala(sala_id):
        agendamentos = Agendamento.query.filter_by(sala_id=sala_id).all()
        return jsonify([ag.to_json() for ag in agendamentos])

    @app.route("/agendamentos", methods=["GET"])
    def get_agendamentos():
        agendamentos = Agendamento.query.all()
        return jsonify([ag.to_json() for ag in agendamentos])

    @app.route("/agendamentos", methods=["POST"])
    def create_agendamento():
        data = request.get_json(silent=True)
        erro = _validar_payload_agendamento(data)
        if erro:
            return _erro(erro, 400)

        sala_id, erro = _parse_sala_id(data)
        if erro:
            return _erro(erro, 400)

        inicio, fim, erro = _parse_datas(data)
        if erro:
            return _erro(erro, 400)

        if not Sala.query.get(sala_id):
            return _erro("Sala não encontrada.", 404)

        conflito = Agendamento.query.filter(
            Agendamento.sala_id == sala_id,
            Agendamento.data_inicio < fim,
            Agendamento.data_fim > inicio,
        ).first()
        if conflito:
            return _erro(
                "Horário indisponível! Já existe um agendamento para esta sala que conflita com este período.",
                409,
            )

        novo_agendamento = Agendamento(
            sala_id=sala_id,
            responsavel=data["responsavel"].strip(),
            data_inicio=inicio,
            data_fim=fim,
        )
        db.session.add(novo_agendamento)
        db.session.commit()
        return jsonify(novo_agendamento.to_json()), 201

    @app.route("/agendamentos/<int:agendamento_id>", methods=["PUT"])
    def update_agendamento(agendamento_id):
        agendamento_para_editar = Agendamento.query.get_or_404(agendamento_id)
        data = request.get_json(silent=True)
        erro = _validar_payload_agendamento(data)
        if erro:
            return _erro(erro, 400)

        sala_id, erro = _parse_sala_id(data)
        if erro:
            return _erro(erro, 400)

        inicio, fim, erro = _parse_datas(data)
        if erro:
            return _erro(erro, 400)

        if not Sala.query.get(sala_id):
            return _erro("Sala não encontrada.", 404)

        conflito = Agendamento.query.filter(
            Agendamento.id != agendamento_id,
            Agendamento.sala_id == sala_id,
            Agendamento.data_inicio < fim,
            Agendamento.data_fim > inicio,
        ).first()
        if conflito:
            return _erro(
                "Horário indisponível! Já existe um agendamento para esta sala que conflita com este período.",
                409,
            )

        agendamento_para_editar.sala_id = sala_id
        agendamento_para_editar.responsavel = data["responsavel"].strip()
        agendamento_para_editar.data_inicio = inicio
        agendamento_para_editar.data_fim = fim
        db.session.commit()
        return jsonify(agendamento_para_editar.to_json())

    @app.route("/agendamentos/<int:agendamento_id>", methods=["DELETE"])
    def delete_agendamento(agendamento_id):
        agendamento_para_deletar = Agendamento.query.get_or_404(agendamento_id)
        db.session.delete(agendamento_para_deletar)
        db.session.commit()
        return jsonify({"mensagem": "Agendamento deletado com sucesso!"})


def _seed_salas_iniciais():
    if not Sala.query.first():
        print("Criando salas iniciais da universidade...")
        db.session.add_all([
            Sala(nome="Anfiteatro Principal", capacidade=30),
            Sala(nome="Laboratório de Projetos", capacidade=15),
            Sala(nome="Sala de Reunião", capacidade=8),
        ])
        db.session.commit()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        _seed_salas_iniciais()
    app.run(debug=True)
