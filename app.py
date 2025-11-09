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
