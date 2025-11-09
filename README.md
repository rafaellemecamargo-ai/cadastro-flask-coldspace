# Cadastro Inteligente — Flask + SQLite (Pronto para Coldspace)

Projeto de exemplo para a disciplina que integra: bases numéricas, arquitetura computacional, sistemas operacionais, bancos de dados e redes.

## Conteúdo
- `app.py` — aplicação Flask com SQLite usando SQLAlchemy
- `templates/index.html` — interface com Jinja2
- `static/style.css` — estilos
- `requirements.txt` — dependências
- `README.md` — este arquivo

## Rodando no Coldspace (passo a passo)
1. Faça upload do conteúdo deste repositório ou extraia o ZIP em um workspace do Coldspace.
2. No terminal do Coldspace, instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Rode a aplicação:
   ```bash
   python app.py
   ```
4. Clique na aba de Preview ou abra o link público gerado para ver o app.

## Notas para apresentação (ligando à ementa)
- **Bases numéricas:** os dados de idade são armazenados como inteiros.  
- **Arquitetura:** a CPU executa o servidor Flask; memória e I/O são usados no processamento e armazenamento do arquivo SQLite.  
- **Sistemas Operacionais:** o SO gerencia processos (Flask), threads e arquivos.  
- **Bancos de Dados:** SQLite organiza os dados no arquivo `usuarios.db`.  
- **Redes:** o navegador faz requisições HTTP ao servidor Flask.

---
Professor: Isaque Katahira
