from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    usuarios = Usuario.query.all()
    return render_template('index.html', usuarios=usuarios)

@app.route('/adicionar', methods=['POST'])
def adicionar():
    nome = request.form.get('nome', '').strip()
    idade = request.form.get('idade', '').strip()
    try:
        idade = int(idade)
    except ValueError:
        idade = None

    if nome and isinstance(idade, int) and idade >= 0:
        novo_usuario = Usuario(nome=nome, idade=idade)
        db.session.add(novo_usuario)
        db.session.commit()
        return redirect('/')
    
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    usuario = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        idade = request.form.get('idade', '').strip()
        try:
            idade = int(idade)
        except ValueError:
            idade = None
        
        if nome and isinstance(idade, int) and idade >= 0:
            usuario.nome = nome
            usuario.idade = idade
            db.session.commit()
        return redirect('/')
    return render_template('editar.html', usuario=usuario)

@app.route('/deletar/<int:id>')
def deletar(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=True)

# ATUALIZAÇÃO

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash # Importação de segurança

app = Flask(__name__)
# Chave secreta é necessária para usar a sessão do Flask (essencial para login)
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_forte_e_aleatoria' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Modelos de Banco de Dados (DB Models) ---

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False) # Novo campo
    senha_hash = db.Column(db.String(255), nullable=False) # Novo campo (Hash da Senha)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento de volta para Pedidos (backref='pedidos')

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255))
    preco = db.Column(db.Float, nullable=False)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_pedido = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Pendente')
    
    usuario = db.relationship('Usuario', backref=db.backref('pedidos', lazy=True))

class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    
    pedido = db.relationship('Pedido', backref=db.backref('itens', lazy=True))
    produto = db.relationship('Produto') # Relação para acessar os detalhes do produto

# --- Inicialização do DB e População de Dados (para teste) ---

def popular_dados_iniciais():
    if not Usuario.query.first():
        senha_hashed = generate_password_hash('123', method='pbkdf2:sha256')
        admin_user = Usuario(nome='Admin Teste', idade=30, email='admin@site.com', senha_hash=senha_hashed)
        db.session.add(admin_user)
        db.session.commit()
    
    if not Produto.query.first():
        produto1 = Produto(nome='Monitor 27"', descricao='Monitor Gamer 144hz', preco=999.99)
        produto2 = Produto(nome='Teclado Mecânico', descricao='Teclado RGB, switch blue', preco=250.00)
        db.session.add_all([produto1, produto2])
        db.session.commit()

    if not Pedido.query.first():
        admin_user = Usuario.query.filter_by(email='admin@site.com').first()
        produto1 = Produto.query.filter_by(nome='Monitor 27"').first()
        produto2 = Produto.query.filter_by(nome='Teclado Mecânico').first()

        if admin_user and produto1 and produto2:
            pedido1 = Pedido(usuario_id=admin_user.id, status='Entregue')
            db.session.add(pedido1)
            db.session.flush() # Força a inserção para obter o ID do pedido

            item1 = ItemPedido(pedido_id=pedido1.id, produto_id=produto1.id, quantidade=1, preco_unitario=produto1.preco)
            item2 = ItemPedido(pedido_id=pedido1.id, produto_id=produto2.id, quantidade=2, preco_unitario=produto2.preco)
            db.session.add_all([item1, item2])
            db.session.commit()

with app.app_context():
    db.create_all()
    popular_dados_iniciais() # Popula dados para teste

# --- Rotas de Autenticação ---

def login_required(f):
    def wrap(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha_hash, senha):
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            return redirect(url_for('pedidos_lista'))
        
        return render_template('login.html', erro='Email ou senha incorretos.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    session.pop('usuario_nome', None)
    return redirect(url_for('home'))

# --- Rotas de Pedidos e Detalhes ---

@app.route('/pedidos')
@login_required
def pedidos_lista():
    usuario_logado_id = session['usuario_id']
    pedidos = Pedido.query.filter_by(usuario_id=usuario_logado_id).order_by(Pedido.data_pedido.desc()).all()
    return render_template('pedidos.html', pedidos=pedidos)

@app.route('/pedido/<int:id>')
@login_required
def detalhe_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    # Segurança: garante que apenas o dono do pedido pode ver os detalhes
    if pedido.usuario_id != session['usuario_id']:
        return "Acesso negado.", 403
        
    return render_template('detalhe_pedido.html', pedido=pedido)

@app.route('/produto/<int:id>')
def detalhe_produto(id):
    produto = Produto.query.get_or_404(id)
    return render_template('detalhe_produto.html', produto=produto)


# --- Rotas de CRUD de Usuários (Mantidas e Atualizadas) ---

# Rota Home agora passa a variável de sessão para o template
@app.route('/')
def home():
    usuarios = Usuario.query.all()
    return render_template('index.html', usuarios=usuarios, usuario_logado=session.get('usuario_nome'))

@app.route('/adicionar', methods=['POST'])
def adicionar():
    nome = request.form.get('nome', '').strip()
    idade = request.form.get('idade', '').strip()
    email = request.form.get('email', '').strip() # Novo campo
    senha = request.form.get('senha', '') # Novo campo
    
    try:
        idade = int(idade)
    except ValueError:
        idade = None

    if nome and isinstance(idade, int) and idade >= 0 and email and senha:
        senha_hashed = generate_password_hash(senha, method='pbkdf2:sha256')
        novo_usuario = Usuario(nome=nome, idade=idade, email=email, senha_hash=senha_hashed)
        try:
            db.session.add(novo_usuario)
            db.session.commit()
        except Exception: # Trata erro de email duplicado (unique=True)
            return "Erro: Email já cadastrado ou dados inválidos.", 400
        return redirect('/')
    
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    usuario = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        idade = request.form.get('idade', '').strip()
        email = request.form.get('email', '').strip()
        
        try:
            idade = int(idade)
        except ValueError:
            idade = None
        
        if nome and isinstance(idade, int) and idade >= 0 and email:
            usuario.nome = nome
            usuario.idade = idade
            usuario.email = email
            # Não permite alterar a senha por esta rota, para simplificar.
            
            try:
                db.session.commit()
            except Exception:
                return "Erro: Email já cadastrado ou dados inválidos.", 400
                
        return redirect('/')
    return render_template('editar.html', usuario=usuario)

@app.route('/deletar/<int:id>')
def deletar(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    return redirect('/')

if __name__ == '__main__':
    # A porta padrão foi movida para o run.sh para evitar conflito com variáveis de ambiente do Coldspace.
    app.run(debug=True)