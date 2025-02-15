from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
import pymysql

app = Flask(__name__, static_folder='static')
app.secret_key = 'sua_chave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/espacosilmarabd' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'
    id_agendamento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_servico = db.Column(db.Integer, db.ForeignKey('servicos.id_servico'), nullable=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=True) 
    nome_usuario = db.Column(db.String(100), nullable=True)  
    formato = db.Column(db.String(15), nullable=True)
    estado = db.Column(db.String(20), nullable=True)
    data = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    observacoes = db.Column(db.String(150), nullable=True)

    def __repr__(self):
        return f"<Agendamento {self.id_agendamento} - Serviço {self.id_servico} - {self.data} {self.hora}>"

class Servico(db.Model):
    __tablename__ = 'servicos'
    id_servico = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_servico = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Servico {self.id_servico} - {self.nome_servico}>"

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    senha = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Usuario {self.id_usuario} - {self.nome}>"

@app.context_processor
def inject_user():
    return dict(user_logged_in='user_id' in session, user_name=session.get('user_name', ''))

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        database='espacosilmarabd',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# Página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT id_usuario, nome FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
                user = cursor.fetchone()

            if user:
                session['user_id'] = user['id_usuario']
                session['user_name'] = user['nome']
                flash(f"Bem-vindo, {user['nome']}!", 'success')
                return redirect(url_for('perfil'))
            else:
                flash("E-mail ou senha incorretos.", 'error')

        except Exception as e:
            print(f"Erro ao fazer login: {e}")
            flash(f"Erro ao fazer login: {e}", 'error')
        
        finally:
            connection.close()

    return render_template('login.html')

# Rota de agendamento
@app.route('/agendamento', methods=['GET', 'POST'])
def agendamento():
    if 'user_id' not in session:
        flash("Você precisa estar logado para agendar.", 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        id_servico = request.form['id_servico']
        formato = request.form['formato']
        data = request.form['data']
        hora = request.form['hora']
        observacoes = request.form['observacoes']

        if not id_servico or not formato or not data or not hora:
            flash("Por favor, preencha todos os campos.", 'error')
            return redirect(url_for('agendamento'))

        # Criar novo agendamento
        novo_agendamento = Agendamento(
            id_servico=id_servico,
            id_usuario=session['user_id'],
            nome_usuario=session['user_name'],
            formato=formato,
            estado="Pendente",
            data=datetime.strptime(data, "%Y-%m-%d").date(),
            hora=datetime.strptime(hora, "%H:%M").time(),
            observacoes=observacoes
        )

        try:
            db.session.add(novo_agendamento)
            db.session.commit()
            flash("Agendamento realizado com sucesso!", 'success')
            return redirect(url_for('perfil'))  # Redireciona para a página de perfil após o agendamento
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao agendar: {e}")
            flash(f"Erro ao agendar: {e}", 'error')

    servicos = Servico.query.all()
    return render_template('agendamento.html', servicos=servicos)

# Rota para buscar horários ocupados
@app.route('/horarios_disponiveis', methods=['GET'])
def horarios_disponiveis():
    data_str = request.args.get('data')
    id_servico = request.args.get('id_servico')

    try:
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Data inválida"}), 400

    horarios_fixos = [f"{h:02d}:00" for h in range(7, 18)]  # Gera de 07:00 até 17:00

    agendamentos_ocupados = Agendamento.query.filter(
        Agendamento.data == data,
        Agendamento.id_servico == id_servico
    ).all()

    horarios_ocupados = [agendamento.hora.strftime('%H:%M') for agendamento in agendamentos_ocupados]

    horarios_disponiveis = [hora for hora in horarios_fixos if hora not in horarios_ocupados]

    return jsonify({'disponiveis': horarios_disponiveis})

# Rota de logout
@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for('index'))

# Página de perfil
@app.route('/perfil')
def perfil():
    if 'user_id' not in session:
        flash("Faça login para acessar o perfil.", "warning")
        return redirect(url_for('login'))
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT nome, email FROM usuarios WHERE id_usuario = %s", (session['user_id'],))
            usuario = cursor.fetchone()

        if not usuario:
            flash("Usuário não encontrado.", "error")
            return redirect(url_for('logout'))

        # Consultar os próximos agendamentos (futuros) com nome do serviço
        proximos_agendamentos = db.session.query(Agendamento, Servico.nome_servico).join(Servico).filter(
            Agendamento.id_usuario == session['user_id'],
            Agendamento.data >= datetime.today().date()
        ).order_by(Agendamento.data, Agendamento.hora).all()

        # Consultar o histórico de agendamentos (passados) com nome do serviço
        historico_agendamentos = db.session.query(Agendamento, Servico.nome_servico).join(Servico).filter(
            Agendamento.id_usuario == session['user_id'],
            Agendamento.data < datetime.today().date()
        ).order_by(Agendamento.data.desc(), Agendamento.hora.desc()).all()

    finally:
        connection.close()

    return render_template('tela_perfil.html', usuario=usuario, proximos_agendamentos=proximos_agendamentos, historico_agendamentos=historico_agendamentos)

# Página de cadastro
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT email FROM usuarios WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash("Este e-mail já está cadastrado.", 'error')
                    return redirect(url_for('cadastro'))

                sql = "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)"
                cursor.execute(sql, (nome, email, senha))
                connection.commit()

            flash("Cadastro realizado com sucesso!", 'success')
            return redirect(url_for('login'))

        except Exception as e:
            print(f"Erro ao cadastrar: {e}")
            flash(f"Erro ao cadastrar: {e}", "error")

        finally:
            connection.close()

    return render_template('cadastro.html')

# Outras páginas
@app.route('/servicos')
def servicos():
    return render_template('servicos.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/contato')
def contato():
    return render_template('contato.html')

# Rodar a aplicação
if __name__ == '__main__':
    app.run(debug=True)
