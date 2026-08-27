# VERSÃO COMPLETA E FINAL DO app.py
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agendamentos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS DO BANCO DE DADOS ---
class Sala(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    capacidade = db.Column(db.Integer, nullable=False)
    def to_json(self):
        return {"id": self.id, "nome": self.nome, "capacidade": self.capacidade}

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    data_inicio = db.Column(db.DateTime, nullable=False)
    data_fim = db.Column(db.DateTime, nullable=False)
    def to_json(self):
        return {"id": self.id, "sala_id": self.sala_id, "responsavel": self.responsavel, "data_inicio": self.data_inicio.isoformat(), "data_fim": self.data_fim.isoformat()}

# --- ROTAS (ENDPOINTS da API) ---
@app.route('/')
def pagina_inicial():
    return render_template('index.html')

@app.route('/salas', methods=['GET'])
def get_salas():
    salas = Sala.query.all()
    return jsonify([sala.to_json() for sala in salas])

@app.route('/salas/<int:sala_id>/agendamentos', methods=['GET'])
def get_agendamentos_por_sala(sala_id):
    agendamentos = Agendamento.query.filter_by(sala_id=sala_id).all()
    return jsonify([ag.to_json() for ag in agendamentos])

@app.route('/agendamentos', methods=['GET'])
def get_agendamentos():
    agendamentos = Agendamento.query.all()
    return jsonify([ag.to_json() for ag in agendamentos])

@app.route('/agendamentos', methods=['POST'])
def create_agendamento():
    data = request.json
    data_inicio_obj = datetime.fromisoformat(data['data_inicio'])
    data_fim_obj = datetime.fromisoformat(data['data_fim'])
    if data_fim_obj <= data_inicio_obj:
        return jsonify({"mensagem": "Erro: O horário de término deve ser posterior ao horário de início."}), 400
    agendamento_existente = Agendamento.query.filter(
        Agendamento.sala_id == data['sala_id'],
        Agendamento.data_inicio < data_fim_obj,
        Agendamento.data_fim > data_inicio_obj
    ).first()
    if agendamento_existente:
        return jsonify({"mensagem": "Horário indisponível! Já existe um agendamento para esta sala que conflita com este período."}), 409
    novo_agendamento = Agendamento(
        sala_id=data['sala_id'],
        responsavel=data['responsavel'],
        data_inicio=data_inicio_obj,
        data_fim=data_fim_obj
    )
    db.session.add(novo_agendamento)
    db.session.commit()
    return jsonify(novo_agendamento.to_json()), 201

@app.route('/agendamentos/<int:agendamento_id>', methods=['PUT'])
def update_agendamento(agendamento_id):
    agendamento_para_editar = Agendamento.query.get_or_404(agendamento_id)
    data = request.json
    data_inicio_obj = datetime.fromisoformat(data['data_inicio'])
    data_fim_obj = datetime.fromisoformat(data['data_fim'])
    if data_fim_obj <= data_inicio_obj:
        return jsonify({"mensagem": "Erro: O horário de término deve ser posterior ao horário de início."}), 400
    sala_id = data.get('sala_id', agendamento_para_editar.sala_id)
    agendamento_conflitante = Agendamento.query.filter(
        Agendamento.id != agendamento_id,
        Agendamento.sala_id == sala_id,
        Agendamento.data_inicio < data_fim_obj,
        Agendamento.data_fim > data_inicio_obj
    ).first()
    if agendamento_conflitante:
        return jsonify({"mensagem": "Horário indisponível! Já existe um agendamento para esta sala que conflita com este período."}), 409
    agendamento_para_editar.sala_id = sala_id
    agendamento_para_editar.responsavel = data['responsavel']
    agendamento_para_editar.data_inicio = data_inicio_obj
    agendamento_para_editar.data_fim = data_fim_obj
    db.session.commit()
    return jsonify(agendamento_para_editar.to_json())

@app.route('/agendamentos/<int:agendamento_id>', methods=['DELETE'])
def delete_agendamento(agendamento_id):
    agendamento_para_deletar = Agendamento.query.get_or_404(agendamento_id)
    db.session.delete(agendamento_para_deletar)
    db.session.commit()
    return jsonify({"mensagem": "Agendamento deletado com sucesso!"})

# --- EXECUÇÃO DO APP ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Sala.query.first():
            print("Criando salas iniciais da universidade...")
            sala1 = Sala(nome='Anfiteatro Principal', capacidade=30)
            sala2 = Sala(nome='Laboratório de Projetos', capacidade=15)
            sala3 = Sala(nome='Sala de Reunião', capacidade=8)
            db.session.add_all([sala1, sala2, sala3])
            db.session.commit()
    app.run(debug=True)