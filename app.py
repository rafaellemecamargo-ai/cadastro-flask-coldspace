from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash 
import os

app = Flask(__name__)
# Configurações de Segurança e Banco de Dados
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_forte_e_aleatoria' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Modelos de Banco de Dados ---

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

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
    produto = db.relationship('Produto')

# --- Inicialização do DB e População de Dados (para teste) ---

def popular_dados_iniciais():
    if not Usuario.query.filter_by(email='admin@site.com').first():
        senha_hashed = generate_password_hash('123', method='pbkdf2:sha256')
        admin_user = Usuario(nome='Admin Teste', idade=30, email='admin@site.com', senha_hash=senha_hashed)
        db.session.add(admin_user)
        db.session.commit()
    
    if not Produto.query.first():
        produto1 = Produto(nome='Monitor 27"', descricao='Monitor Gamer 144hz', preco=1300.00)
        produto2 = Produto(nome='Teclado Mecânico', descricao='Teclado RGB, switch blue', preco=250.00)
        db.session.add_all([produto1, produto2])
        db.session.commit()

    if not Pedido.query.first():
        admin_user = Usuario.query.filter_by(email='admin@site.com').first()
        produto1 = Produto.query.filter_by(nome='Monitor 27"').first()
        produto2 = Produto.query.filter_by(nome='Teclado Mecânico').first()

        if admin_user and produto1 and produto2:
            pedido1 = Pedido(id=48392, usuario_id=admin_user.id, data_pedido=datetime(2025, 11, 12, 19, 37), status='Entregue')
            db.session.add(pedido1)
            db.session.flush()

            item1 = ItemPedido(pedido_id=pedido1.id, produto_id=produto1.id, quantidade=1, preco_unitario=produto1.preco)
            item2 = ItemPedido(pedido_id=pedido1.id, produto_id=produto2.id, quantidade=2, preco_unitario=produto2.preco)
            db.session.add_all([item1, item2])
            db.session.commit()

# Adiciona 5 usuários fictícios para testar a paginação
    if Usuario.query.count() < 6:
        for i, nome_ficticio in enumerate(['Ana Silva', 'Bruno Mendes', 'Carla Souza', 'David Lima', 'Erica Santos']):
            if not Usuario.query.filter_by(email=f'usuario{i+1}@temp.com').first():
                senha_hashed = generate_password_hash('123', method='pbkdf2:sha256')
                temp_user = Usuario(nome=nome_ficticio, idade=20+i, email=f'usuario{i+1}@temp.com', senha_hash=senha_hashed)
                db.session.add(temp_user)
        db.session.commit()


with app.app_context():
    db.create_all()
    popular_dados_iniciais()

# --- Decorador de Segurança ---

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return wrap

# --- Rotas de Autenticação (A rota raiz '/' agora é o LOGIN) ---

@app.route('/', methods=['GET', 'POST'])
def login_page():
    # Tela 1: Login
    if 'usuario_id' in session:
        return redirect(url_for('cadastro_usuarios'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha_hash, senha):
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            # Redireciona para o cadastro (Tela 2) após o login
            return redirect(url_for('cadastro_usuarios'))
        
        return render_template('login.html', erro='Email ou senha incorretos.')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    session.pop('usuario_nome', None)
    return redirect(url_for('login_page'))


# --- Rotas de CRUD de Usuários (Protegidas) ---

@app.route('/cadastro')
@login_required
def cadastro_usuarios():
    # Parâmetros de Filtro e Ordenação
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'nome') # Padrão: nome
    direction = request.args.get('direction', 'asc') # Padrão: ascendente
    page = request.args.get('page', 1, type=int)
    per_page = 5 
    
    query = Usuario.query
    
    # 1. Filtro de Busca (por Nome)
    if search_query:
        query = query.filter(Usuario.nome.ilike(f'%{search_query}%'))
        
    # 2. Ordenação
    if sort_by == 'nome':
        if direction == 'desc':
            query = query.order_by(Usuario.nome.desc())
        else:
            query = query.order_by(Usuario.nome.asc())
    elif sort_by == 'idade':
        if direction == 'desc':
            query = query.order_by(Usuario.idade.desc())
        else:
            query = query.order_by(Usuario.idade.asc())

    # 3. Paginação
    pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        'cadastro_usuarios.html', 
        usuarios=pagination.items, 
        pagination=pagination, 
        usuario_logado=session.get('usuario_nome'),
        search_query=search_query,
        sort_by=sort_by,
        direction=direction
    )

@app.route('/adicionar', methods=['POST'])
@login_required 
def adicionar():
    nome = request.form.get('nome', '').strip()
    idade = request.form.get('idade', '').strip()
    email = request.form.get('email', '').strip() 
    
    try:
        idade = int(idade)
    except ValueError:
        idade = None

    if nome and isinstance(idade, int) and idade >= 0 and email:
        senha_hashed = generate_password_hash("novasenha123", method='pbkdf2:sha256') 

        novo_usuario = Usuario(nome=nome, idade=idade, email=email, senha_hash=senha_hashed)
        try:
            db.session.add(novo_usuario)
            db.session.commit()
        except Exception:
            # Trata erro de email duplicado (unique=True)
            return "Erro: Email já cadastrado ou dados inválidos.", 400
            
        return redirect(url_for('cadastro_usuarios'))
    
    return "Erro: Dados incompletos ou inválidos.", 400


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required 
def editar(id):
    usuario = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        idade = request.form.get('idade', '').strip()
        email = request.form.get('email', '').strip() # NOVO: Captura o email
        
        try:
            idade = int(idade)
        except ValueError:
            idade = None
        
        # NOVO: Verifica se o email é válido
        if nome and isinstance(idade, int) and idade >= 0 and email:
            usuario.nome = nome
            usuario.idade = idade
            usuario.email = email # NOVO: Atualiza o email
            
            try:
                db.session.commit()
            except Exception:
                # Retorna erro se o email for duplicado
                return "Erro: Falha ao atualizar dados. O e-mail pode já estar em uso.", 400
                
        return redirect(url_for('cadastro_usuarios'))
    # Tela 6: Editar Usuário
    return render_template('editar.html', usuario=usuario)

@app.route('/deletar/<int:id>')
@login_required 
def deletar(id):
    usuario = Usuario.query.get_or_404(id)
    
    if usuario.id == 1:
        return "Você não pode deletar este usuário de teste.", 403

    db.session.delete(usuario)
    db.session.commit()
    return redirect(url_for('cadastro_usuarios'))

# --- Rotas do Módulo de Pedidos ---

@app.route('/pedidos')
@login_required
def pedidos_lista():
    # Lista de pedidos do Admin logado
    usuario_logado_id = session['usuario_id']
    pedidos = Pedido.query.filter_by(usuario_id=usuario_logado_id).order_by(Pedido.data_pedido.desc()).all()
    # Tela 3: Detalhes do Pedido (Adaptado para lista)
    return render_template('pedidos.html', pedidos=pedidos, usuario_alvo=None) 

@app.route('/pedidos_usuario/<int:user_id>')
@login_required
def pedidos_usuario(user_id):
    # A rota "Ver pedido" redireciona para a lista de pedidos do Admin por simplicidade.
    return redirect(url_for('pedidos_lista')) 


@app.route('/pedido/<int:id>')
@login_required
def detalhe_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    # Tela 4: Detalhes do pedido
    return render_template('detalhe_pedido.html', pedido=pedido)

@app.route('/produto/<int:id>')
def detalhe_produto(id):
    produto = Produto.query.get_or_404(id)
    # Tela 5: Detalhes do Produto
    return render_template('detalhe_produto.html', produto=produto)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)