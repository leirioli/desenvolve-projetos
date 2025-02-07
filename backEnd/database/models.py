from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'  # Nome da tabela no banco de dados
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    senha = db.Column(db.String(255))

    def __repr__(self):
        return f'<Usuario {self.nome}>'

class Servico(db.Model):
    __tablename__ = 'servicos'  # Nome da tabela no banco de dados
    id_servico = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_servico = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(150))
    valor = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<Servico {self.nome_servico}>'

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'  # Nome da tabela no banco de dados
    id_agendamento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_servico = db.Column(db.Integer, db.ForeignKey('servicos.id_servico'))
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))
    formato = db.Column(db.String(15))
    estado = db.Column(db.String(20))
    data_hora = db.Column(db.DateTime)
    observacoes = db.Column(db.String(150))

    def __repr__(self):
        return f'<Agendamento {self.id_agendamento}>'