from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
import os
from werkzeug.utils import secure_filename
from random import sample


app = Flask(__name__)
app.secret_key = 'chave-secreta-aqui'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


#@app.after_request
#def set_charset(response):
#    response.headers["Content-Type"] = "text/html; charset=utf-8"
#    return response

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    return pymysql.connect(
        host='localhost',
        user='br7user',
        password='Nexus24$',
        database='br7db',
        cursorclass=pymysql.cursors.DictCursor
    )


conn = get_db()

def buscar_produtos(filtros=None):
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []

    if filtros:
        for campo, valor in filtros.items():
            query += f" AND {campo} = %s"
            params.append(valor)

    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(query, tuple(params))
        produtos = cursor.fetchall()

        for produto in produtos:
            cursor.execute(
                "SELECT caminho FROM imagens_produto WHERE produto_id = %s LIMIT 1",
                (produto['id'],)
            )
            imagem = cursor.fetchone()
            produto['imagem'] = imagem['caminho'] if imagem else None

    return produtos

from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
from dotenv import load_dotenv
load_dotenv()

ADMIN_USER = os.getenv('ADMIN_USER')
ADMIN_PASS = os.getenv('ADMIN_PASS')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        if usuario == ADMIN_USER and senha == ADMIN_PASS:
            session['usuario_logado'] = usuario
            return redirect(url_for('admin'))
        else:
            flash('Usuário ou senha incorretos')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('usuario_logado', None)
    flash('Você saiu com sucesso.')
    return redirect(url_for('login'))


@app.route('/')
def index():
    # Produtos em geral (caso ainda precise no template)
    with get_db() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM produtos")
            produtos = cursor.fetchall()

            for produto in produtos:
                cursor.execute("SELECT caminho FROM imagens_produto WHERE produto_id = %s LIMIT 1", (produto['id'],))
                imagem = cursor.fetchone()
                produto['imagem'] = imagem['caminho'] if imagem else None

    # Chamadas já limitadas no SQL
    mais_vendidos_chuteira = get_produtos_por_filtro(tipo='chuteira', mais_vendidos=1, limit=15)
    mais_vendidos_tenis = get_produtos_por_filtro(tipo='tenis', mais_vendidos=1, limit=15)

    pronta_entrega_chuteira = get_produtos_por_filtro(tipo='chuteira', pronta_entrega=1, limit=15)
    pronta_entrega_tenis = get_produtos_por_filtro(tipo='tenis', pronta_entrega=1, limit=15)

    por_encomenda_chuteira = get_produtos_por_filtro(tipo='chuteira', por_encomenda=1, limit=15)
    por_encomenda_tenis = get_produtos_por_filtro(tipo='tenis', por_encomenda=1, limit=15)

    society_chuteira = get_produtos_por_filtro(tipo='chuteira', categoria='society', limit=15)
    futsal_chuteira = get_produtos_por_filtro(tipo='chuteira', categoria='futsal', limit=15)

    campo_trava = get_produtos_por_filtro(tipo='chuteira', categoria='campo', subcategoria='trava', limit=15)
    campo_trava_mista = get_produtos_por_filtro(tipo='chuteira', categoria='campo', subcategoria='trava-mista', limit=15)
    produtos = buscar_produtos()
    return render_template('index.html',
        produtos=produtos,

        mais_vendidos_chuteira=mais_vendidos_chuteira,
        mais_vendidos_tenis=mais_vendidos_tenis,

        pronta_entrega_chuteira=pronta_entrega_chuteira,
        pronta_entrega_tenis=pronta_entrega_tenis,
        por_encomenda_chuteira=por_encomenda_chuteira,
        por_encomenda_tenis=por_encomenda_tenis,

        society_chuteira=society_chuteira,
        futsal_chuteira=futsal_chuteira,
        campo_trava=campo_trava,
        campo_trava_mista=campo_trava_mista
    )


def get_produtos_por_filtro(tipo=None, categoria=None, subcategoria=None, 
                             pronta_entrega=None, mais_vendidos=None, por_encomenda=None,
                             limit=None):
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []

    if tipo:
        query += " AND tipo = %s"
        params.append(tipo)

    if categoria:
        query += " AND categoria = %s"
        params.append(categoria)

    if subcategoria:
        query += " AND subcategoria = %s"
        params.append(subcategoria)

    if pronta_entrega is not None:
        query += " AND pronta_entrega = %s"
        params.append(pronta_entrega)

    if mais_vendidos is not None:
        query += " AND mais_vendidos = %s"
        params.append(mais_vendidos)

    if por_encomenda is not None:
        query += " AND por_encomenda = %s"
        params.append(por_encomenda)

    if limit:
        query += " ORDER BY RAND() LIMIT %s"
        params.append(limit)

    with get_db() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query, tuple(params))
            produtos = cursor.fetchall()

            for produto in produtos:
                cursor.execute(
                    "SELECT caminho FROM imagens_produto WHERE produto_id = %s LIMIT 1", 
                    (produto['id'],)
                )
                imagem = cursor.fetchone()
                produto['imagem'] = imagem['caminho'] if imagem else None

    return produtos


@app.route('/admin')
def admin():
    nome = request.args.get('busca_nome', '').strip()
    tipo = request.args.get('tipo')
    categoria = request.args.get('categoria')
    subcategoria = request.args.get('subcategoria')
    pronta_entrega = 'pronta_entrega' in request.args
    por_encomenda = 'por_encomenda' in request.args
    mais_vendidos = 'mais_vendidos' in request.args

    filtros = []
    valores = []

    if nome:
        filtros.append("nome LIKE %s")
        valores.append(f"%{nome}%")
    if tipo:
        filtros.append("tipo = %s")
        valores.append(tipo)
    if categoria:
        filtros.append("categoria = %s")
        valores.append(categoria)
    if subcategoria:
        filtros.append("subcategoria = %s")
        valores.append(subcategoria)
    if pronta_entrega:
        filtros.append("pronta_entrega = 1")
    if por_encomenda:
        filtros.append("por_encomenda = 1")
    if mais_vendidos:
        filtros.append("mais_vendidos = 1")

    query = "SELECT * FROM produtos"
    if filtros:
        query += " WHERE " + " AND ".join(filtros)

    with get_db() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query, valores)
            produtos = cursor.fetchall()

            for produto in produtos:
                cursor.execute("SELECT caminho FROM imagens_produto WHERE produto_id = %s", (produto['id'],))
                imagens = cursor.fetchall()
                produto['imagens'] = imagens
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))
    return render_template('admin.html', produtos=produtos)

from PIL import Image

def convert_to_webp(original_path, output_folder):
    try:
        filename = os.path.basename(original_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(output_folder, f"{name}.webp")

        image = Image.open(original_path).convert("RGB")
        image.save(output_path, "webp", quality=85)
        return True
    except Exception as e:
        print(f"Erro ao converter para WebP: {e}")
        return False


@app.route('/salvar-produto', methods=['POST'])
def salvar_produto():
    data = request.form
    tipo = data.get('tipo')
    nome = data.get('nome')
    preco = data.get('preco')
    descricao = data.get('descricao')

    marca = data.get('marca') if tipo in ['chuteira', 'tenis'] else None
    tamanhos = request.form.getlist('tamanho') if tipo in ['chuteira', 'tenis'] else []
    tamanho = ','.join(tamanhos) if tamanhos else None

    cores = request.form.getlist('cor')
    cor = ','.join(cores) if cores else None

    categoria = data.get('categoria') if tipo == 'chuteira' else None
    subcategoria = data.get('subcategoria') if tipo == 'chuteira' else None

    pronta_entrega = 1 if data.get('pronta_entrega') == 'on' else 0
    mais_vendidos = 1 if data.get('mais_vendidos') == 'on' else 0
    por_encomenda = 1 if data.get('por_encomenda') == 'on' else 0

    imagens = request.files.getlist('imagens')

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO produtos 
                (tipo, nome, marca, cor, tamanho, preco, descricao, categoria, subcategoria, pronta_entrega, mais_vendidos, por_encomenda)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tipo, nome, marca, cor, tamanho, preco, descricao,
                categoria, subcategoria, pronta_entrega, mais_vendidos, por_encomenda
            ))
            conn.commit()

            produto_id = cursor.lastrowid

            for imagem in imagens:
                if imagem.filename != '' and allowed_file(imagem.filename):
                    filename = secure_filename(imagem.filename)
                    caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    contador = 1
                    nome_base, ext = os.path.splitext(filename)
                    while os.path.exists(caminho):
                        filename = f"{nome_base}_{contador}{ext}"
                        caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        contador += 1

                    imagem.save(caminho)

                    # ✅ Converte para webp
                    convert_to_webp(caminho, app.config['UPLOAD_FOLDER'])

                    # Salva o nome original no banco
                    cursor.execute(
                        "INSERT INTO imagens_produto (produto_id, caminho) VALUES (%s, %s)",
                        (produto_id, filename)
                    )

            conn.commit()

    return redirect('/admin')




@app.route('/excluir-produto/<int:id>', methods=['POST'])
def excluir_produto(id):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT caminho FROM imagens_produto WHERE produto_id = %s", (id,))
            imagens = cursor.fetchall()

            for img in imagens:
                caminho_img = os.path.join(app.config['UPLOAD_FOLDER'], img['caminho'])
                if os.path.exists(caminho_img):
                    os.remove(caminho_img)

            cursor.execute("DELETE FROM imagens_produto WHERE produto_id = %s", (id,))
            cursor.execute("DELETE FROM produtos WHERE id = %s", (id,))
            conn.commit()

    return redirect('/admin')


# rota produto/<id> (GET)
@app.route('/produto/<int:id>')
def produto(id):
    with get_db() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM produtos WHERE id = %s", (id,))
            produto = cursor.fetchone()
            if not produto:
                return "Produto não encontrado", 404

            cursor.execute("SELECT caminho FROM imagens_produto WHERE produto_id = %s", (id,))
            imagens_bd = cursor.fetchall()

    produto['tamanhos'] = produto['tamanho'].split(',') if produto.get('tamanho') else []
    produto['cores'] = produto['cor'].split(',') if produto.get('cor') else []

    produto['categoria'] = produto.get('categoria') or None
    produto['pronta_entrega'] = int(produto.get('pronta_entrega', 0)) == 1
    produto['mais_vendidos'] = int(produto.get('mais_vendidos', 0)) == 1

            # Define a disponibilidade como texto
    if produto.get('pronta_entrega'):
        produto['disponibilidade'] = 'Pronta Entrega'
    elif produto.get('por_encomenda'):
        produto['disponibilidade'] = 'Por Encomenda'
    else:
        produto['disponibilidade'] = 'Não informado'

    imagens = [img['caminho'] for img in imagens_bd]

    return render_template('produto.html', produto=produto, imagens=imagens)



# editar-produto (GET e POST)
@app.route('/admin/produto/<int:produto_id>/editar', methods=['GET', 'POST'])
def editar_produto(produto_id):
    with get_db() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:  # Use DictCursor para acessar por nome

            cursor.execute("SELECT * FROM produtos WHERE id = %s", (produto_id,))
            produto = cursor.fetchone()
            if not produto:
                flash('Produto não encontrado.')
                return redirect(url_for('admin'))

            cursor.execute("SELECT id, caminho FROM imagens_produto WHERE produto_id = %s", (produto_id,))
            imagens = cursor.fetchall()

            if request.method == 'POST':
                tipo = request.form.get('tipo')
                nome = request.form.get('nome')
                marca = request.form.get('marca')
                tamanho = request.form.get('tamanho')
                cor = request.form.get('cor')
                descricao = request.form.get('descricao')
                preco = request.form.get('preco')
                

                categoria = request.form.get('categoria') if tipo == 'chuteira' else None
                subcategoria = request.form.get('subcategoria') if tipo == 'chuteira' else None
                pronta_entrega = 1 if request.form.get('pronta_entrega') == 'on' else 0
                mais_vendidos = 1 if request.form.get('mais_vendidos') == 'on' else 0
                por_encomenda = 1 if request.form.get('por_encomenda') == 'on' else 0

                cursor.execute("""
                    UPDATE produtos SET tipo=%s, nome=%s, marca=%s, tamanho=%s, cor=%s, descricao=%s, preco=%s, 
                        categoria=%s, subcategoria=%s,
                        pronta_entrega=%s, mais_vendidos=%s, por_encomenda=%s
                    WHERE id=%s
                """, (tipo, nome, marca, tamanho, cor, descricao, preco, 
                      categoria, subcategoria, pronta_entrega, mais_vendidos, por_encomenda, produto_id))
                conn.commit()

                # Excluir imagens
                imagens_para_excluir = request.form.getlist('excluir_imagens')
                for img_id in imagens_para_excluir:
                    cursor.execute("SELECT caminho FROM imagens_produto WHERE id = %s", (img_id,))
                    img = cursor.fetchone()
                    if img:
                        caminho_img = os.path.join(app.config['UPLOAD_FOLDER'], img['caminho'])
                        if os.path.exists(caminho_img):
                            os.remove(caminho_img)
                        cursor.execute("DELETE FROM imagens_produto WHERE id = %s", (img_id,))
                conn.commit()

                # Adicionar novas imagens
                if 'novas_imagens' in request.files:
                    files = request.files.getlist('novas_imagens')
                    for file in files:
                        if file and allowed_file(file.filename):
                            filename = secure_filename(file.filename)
                            caminho_save = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                            contador = 1
                            nome_base, ext = os.path.splitext(filename)
                            while os.path.exists(caminho_save):
                                filename = f"{nome_base}_{contador}{ext}"
                                caminho_save = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                                contador += 1
                            file.save(caminho_save)

                            cursor.execute(
                                "INSERT INTO imagens_produto (produto_id, caminho) VALUES (%s, %s)",
                                (produto_id, filename)
                            )
                    conn.commit()

                flash('Produto atualizado com sucesso!')
                return redirect(url_for('editar_produto', produto_id=produto_id))

        return render_template('editar_produto.html', produto=produto, imagens=imagens)




@app.template_filter('format_brl')
def format_brl(value):
    try:
        return f'{float(value):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except ValueError:
        return value
    




    

@app.route('/loja')
def loja():
    tipo = request.args.get('tipo')  # chuteira, tenis, bolsa
    categoria = request.args.get('categoria')  # campo, society, futsal
    subcategoria = request.args.get('subcategoria')  # trava, trava-mista, etc.

    def buscar_produtos(filtros=None):
        query = "SELECT * FROM produtos WHERE 1=1"
        params = []

        if filtros:
            for campo, valor in filtros.items():
                query += f" AND {campo} = %s"
                params.append(valor)

        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query, tuple(params))
            produtos = cursor.fetchall()

            for produto in produtos:
                cursor.execute(
                    "SELECT caminho FROM imagens_produto WHERE produto_id = %s LIMIT 1",
                    (produto['id'],)
                )
                imagem = cursor.fetchone()
                produto['imagem'] = imagem['caminho'] if imagem else None

        return produtos

    # 🔥 Filtros dinâmicos
    filtros_geral = {}
    if tipo:
        filtros_geral['tipo'] = tipo
    if categoria:
        filtros_geral['categoria'] = categoria
    if subcategoria:
        filtros_geral['subcategoria'] = subcategoria

    context = {
        'filtro_tipo': tipo,
        'filtro_categoria': categoria,
        'filtro_subcategoria': subcategoria,

        'produtos': buscar_produtos(filtros_geral),

        # Mais Vendidos
        'mais_vendidos_chuteira': buscar_produtos({'tipo': 'chuteira', 'mais_vendidos': 1}),
        'mais_vendidos_tenis': buscar_produtos({'tipo': 'tenis', 'mais_vendidos': 1}),
        'mais_vendidos_bolsa': buscar_produtos({'tipo': 'bolsa', 'mais_vendidos': 1}),

        # Pronta Entrega
        'pronta_entrega_chuteira': buscar_produtos({'tipo': 'chuteira', 'pronta_entrega': 1}),
        'pronta_entrega_tenis': buscar_produtos({'tipo': 'tenis', 'pronta_entrega': 1}),
        'pronta_entrega_bolsa': buscar_produtos({'tipo': 'bolsa', 'pronta_entrega': 1}),

        'por_encomenda_chuteira': buscar_produtos({'tipo': 'chuteira', 'por_encomenda': 1}),
        'por_encomenda_tenis': buscar_produtos({'tipo': 'tenis', 'por_encomenda': 1}),
        'por_encomenda_bolsa': buscar_produtos({'tipo': 'bolsa', 'por_encomenda': 1}),



        # Categorias específicas
        'society_chuteira': buscar_produtos({'tipo': 'chuteira', 'categoria': 'society'}),
        'campo_chuteira': buscar_produtos({'tipo': 'chuteira', 'categoria': 'campo'}),
        'campo_trava': buscar_produtos({'tipo': 'chuteira', 'categoria': 'campo', 'subcategoria': 'trava'}),
        'campo_trava_mista': buscar_produtos({'tipo': 'chuteira', 'categoria': 'campo', 'subcategoria': 'trava-mista'}),
        'futsal_chuteira': buscar_produtos({'tipo': 'chuteira', 'categoria': 'futsal'}),
    }
    produtos = buscar_produtos()
    return render_template('index.html', **context, produtos=produtos)

@app.route('/loja/chuteiras/campo/trava')
def chuteiras_trava():
    produtos_pronta_entrega = buscar_produtos({
        'tipo': 'chuteira',
        'categoria': 'campo',
        'subcategoria': 'trava',
        'pronta_entrega': 1
    })

    produtos_por_encomenda = buscar_produtos({
        'tipo': 'chuteira',
        'categoria': 'campo',
        'subcategoria': 'trava',
        'por_encomenda': 1
    })

    produtos_mais_vendidos = buscar_produtos({
        'tipo': 'chuteira',
        'categoria': 'campo',
        'subcategoria': 'trava',
        'mais_vendidos': 1
    })

    return render_template('chuteiras_trava.html',
        pronta_entrega_chuteira_trava=produtos_pronta_entrega,
        por_encomenda_chuteira_trava=produtos_por_encomenda,
        mais_vendidos_chuteira_trava=produtos_mais_vendidos
    )

@app.route('/loja/chuteiras/campo/trava-mista')
def chuteiras_trava_mista():
    produtos_pronta_entrega = buscar_produtos({
        'tipo': 'chuteira',
        'categoria': 'campo',
        'subcategoria': 'trava-mista',
        'pronta_entrega': 1
    })

    produtos_por_encomenda = buscar_produtos({
        'tipo': 'chuteira',
        'categoria': 'campo',
        'subcategoria': 'trava-mista',
        'por_encomenda': 1
    })

    produtos_mais_vendidos = buscar_produtos({
        'tipo': 'chuteira',
        'categoria': 'campo',
        'subcategoria': 'trava-mista',
        'mais_vendidos': 1
    })

    return render_template('chuteiras_trava_mista.html',
        pronta_entrega_chuteira_trava_mista=produtos_pronta_entrega,
        por_encomenda_chuteira_trava_mista=produtos_por_encomenda,
        mais_vendidos_chuteira_trava_mista=produtos_mais_vendidos
    )

@app.route('/loja/chuteiras/society')
def chuteiras_society():
    produtos_pronta_entrega = buscar_produtos({
        'tipo': 'chuteira',
        'categoria': 'society',
        'pronta_entrega': 1
    })

    produtos_por_encomenda = buscar_produtos({
        'tipo': 'chuteira',
        'categoria': 'society',
        'por_encomenda': 1
    })

    produtos_mais_vendidos = buscar_produtos({
        'tipo': 'chuteira',
        'categoria': 'society',
        'mais_vendidos': 1
    })

    return render_template('chuteiras_society.html',
        pronta_entrega_chuteira_society=produtos_pronta_entrega,
        por_encomenda_chuteira_society=produtos_por_encomenda,
        mais_vendidos_chuteira_society=produtos_mais_vendidos
    )

@app.route('/loja/chuteiras/futsal')
def chuteiras_futsal():
    produtos_pronta_entrega = buscar_produtos({
        'tipo': 'chuteira',
        'categoria': 'futsal',
        'pronta_entrega': 1
    })

    produtos_por_encomenda = buscar_produtos({
        'tipo': 'chuteira',
        'categoria': 'futsal',
        'por_encomenda': 1
    })

    produtos_mais_vendidos = buscar_produtos({
        'tipo': 'chuteira',
        'categoria': 'futsal',
        'mais_vendidos': 1
    })

    return render_template('chuteiras_futsal.html',
        pronta_entrega_chuteira_futsal=produtos_pronta_entrega,
        por_encomenda_chuteira_futsal=produtos_por_encomenda,
        mais_vendidos_chuteira_futsal=produtos_mais_vendidos
    )

@app.route('/loja/tenis')
def tenis():
    produtos_pronta_entrega = buscar_produtos({
        'tipo': 'tenis',
        'pronta_entrega': 1
    })

    produtos_por_encomenda = buscar_produtos({
        'tipo': 'tenis',
        'por_encomenda': 1
    })

    produtos_mais_vendidos = buscar_produtos({
        'tipo': 'tenis',
        'mais_vendidos': 1
    })

    return render_template('tenis.html',
        pronta_entrega_tenis=produtos_pronta_entrega,
        por_encomenda_tenis=produtos_por_encomenda,
        mais_vendidos_tenis=produtos_mais_vendidos
    )

@app.route('/loja/bolsas')
def bolsas():
    produtos_pronta_entrega = buscar_produtos({
        'tipo': 'bolsa',
        'pronta_entrega': 1
    })

    produtos_por_encomenda = buscar_produtos({
        'tipo': 'bolsa',
        'por_encomenda': 1
    })

    produtos_mais_vendidos = buscar_produtos({
        'tipo': 'bolsa',
        'mais_vendidos': 1
    })

    return render_template('bolsas.html',
        pronta_entrega_bolsa=produtos_pronta_entrega,
        por_encomenda_bolsa=produtos_por_encomenda,
        mais_vendidos_bolsa=produtos_mais_vendidos
    )

# ROTA: PRONTA ENTREGA
@app.route('/loja/pronta-entrega')
def todos_pronta_entrega():
    chuteiras = buscar_produtos({'tipo': 'chuteira', 'pronta_entrega': 1})
    tenis = buscar_produtos({'tipo': 'tenis', 'pronta_entrega': 1})
    bolsas = buscar_produtos({'tipo': 'bolsa', 'pronta_entrega': 1})

    return render_template(
        'pronta_entrega.html',
        pronta_entrega_chuteira=chuteiras,
        pronta_entrega_tenis=tenis,
        pronta_entrega_bolsa=bolsas
    )


# ROTA: PRONTA ENTREGA
@app.route('/loja/por-encomenda')
def todos_por_encomendaa():
    chuteiras = buscar_produtos({'tipo': 'chuteira', 'por_encomenda': 1})
    tenis = buscar_produtos({'tipo': 'tenis', 'por_encomenda': 1})
    bolsas = buscar_produtos({'tipo': 'bolsa', 'por_encomenda': 1})

    return render_template(
        'por_encomenda.html',
        por_encomenda_chuteira=chuteiras,
        por_encomenda_tenis=tenis,
        por_encomenda_bolsa=bolsas
    )






from unidecode import unidecode

def normalizar(texto):
    return unidecode(texto.strip().lower())


# Com subcategoria (ex: campo/trava/adidas)
@app.route('/loja/chuteiras/<categoria>/<subcategoria>/<marca>')
def filtro_chuteiras_marca_com_subcategoria(categoria, subcategoria, marca):
    categoria = normalizar(categoria)
    subcategoria = normalizar(subcategoria)
    marca = normalizar(marca)

    conn = get_db()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM produtos WHERE tipo = 'chuteira'")
            produtos_raw = cursor.fetchall()

            produtos = [
                p for p in produtos_raw
                if normalizar(p['categoria']) == categoria
                and normalizar(p['subcategoria']) == subcategoria
                and normalizar(p['marca']) == marca
            ]

            # Buscar imagem principal
            for produto in produtos:
                cursor.execute("SELECT caminho FROM imagens_produto WHERE produto_id = %s LIMIT 1", (produto['id'],))
                img = cursor.fetchone()
                produto['imagem'] = img['caminho'] if img else None

    finally:
        conn.close()

    return render_template(
        'produtos_filtrados.html',
        produtos=produtos,
        tipo='chuteira',
        categoria=subcategoria,
        marca=marca
    )


# Sem subcategoria (ex: society/adidas)
@app.route('/loja/chuteiras/<categoria>/<marca>')
def filtro_chuteiras_marca_sem_subcategoria(categoria, marca):
    categoria = normalizar(categoria)
    marca = normalizar(marca)

    conn = get_db()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM produtos WHERE tipo = 'chuteira'")
            produtos_raw = cursor.fetchall()

            produtos = [
                p for p in produtos_raw
                if normalizar(p['categoria']) == categoria
                and not p['subcategoria']  # garante que é sem subcategoria
                and normalizar(p['marca']) == marca
            ]

            for produto in produtos:
                cursor.execute("SELECT caminho FROM imagens_produto WHERE produto_id = %s LIMIT 1", (produto['id'],))
                img = cursor.fetchone()
                produto['imagem'] = img['caminho'] if img else None

    finally:
        conn.close()

    return render_template(
        'produtos_filtrados.html',
        produtos=produtos,
        tipo='chuteira',
        categoria=categoria,
        marca=marca
    )

# --- AJUSTE DA FUNÇÃO buscar_marcas_e_modelos PARA PARAR NA MARCA ---
def buscar_marcas(tipo, categoria, subcategoria=None):
    conn = get_db()
    marcas_dict = {}
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        if subcategoria:
            cursor.execute("""
                SELECT marca
                FROM produtos
                WHERE tipo = %s AND categoria = %s AND subcategoria = %s
            """, (tipo, categoria, subcategoria))
        else:
            cursor.execute("""
                SELECT marca
                FROM produtos
                WHERE tipo = %s AND categoria = %s
            """, (tipo, categoria))

        resultados = cursor.fetchall()
        for row in resultados:
            marca_original = row['marca']
            if marca_original:
                marca_norm = normalizar(marca_original)
                if marca_norm not in marcas_dict:
                    marcas_dict[marca_norm] = marca_original

    # Ordena alfabeticamente pela chave normalizada e retorna nomes originais
    return [marcas_dict[k] for k in sorted(marcas_dict.keys())]

@app.context_processor
def carregar_menu():
    chuteiras_campo_trava = buscar_marcas('chuteira', 'campo', 'trava')
    chuteiras_campo_trava_mista = buscar_marcas('chuteira', 'campo', 'trava-mista')
    chuteiras_society = buscar_marcas('chuteira', 'society')
    chuteiras_futsal = buscar_marcas('chuteira', 'futsal')

    return dict(
        chuteiras_campo_trava=chuteiras_campo_trava,
        chuteiras_campo_trava_mista=chuteiras_campo_trava_mista,
        chuteiras_society=chuteiras_society,
        chuteiras_futsal=chuteiras_futsal
    )


from rapidfuzz import fuzz
from unidecode import unidecode

@app.route('/loja/chuteiras/busca')
def buscar_modelo():
    q = request.args.get('q', '').strip()
    if not q:
        return redirect(url_for('pagina_inicial'))

    termos = [unidecode(t.lower()) for t in q.split() if t]

    conn = get_db()
    produtos = []
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            or_clauses = " OR ".join(["REPLACE(LOWER(nome), '-', ' ') LIKE %s"] * len(termos))
            sql = f"""
                SELECT * FROM produtos
                WHERE tipo = 'chuteira' AND ({or_clauses})
            """
            params = [f"%{termo}%" for termo in termos]
            cursor.execute(sql, params)
            resultados_brutos = cursor.fetchall()

            produtos = []
            busca_normalizada = unidecode(q.lower())
            for produto in resultados_brutos:
                nome_normalizado = unidecode(produto['nome'].lower().replace('-', ' '))
                ratio = fuzz.token_set_ratio(busca_normalizada, nome_normalizado)
                if ratio >= 70:
                    cursor.execute("SELECT caminho FROM imagens_produto WHERE produto_id = %s LIMIT 1", (produto['id'],))
                    img = cursor.fetchone()
                    produto['imagem'] = img['caminho'] if img else None
                    produtos.append(produto)
    finally:
        conn.close()

    return render_template('produtos_filtrados.html', produtos=produtos, tipo='chuteira', busca=q)

        #FOOTER-------------------------------------------------------#



@app.route("/quem-somos")
def quem_somos():
    return render_template("quem-somos.html")

@app.route('/duvidas-frequentes')
def duvidas_frequentes():
    return render_template('duvidas-frequentes.html')

@app.route('/depoimentos')
def depoimentos():
    return render_template('depoimentos.html')

@app.route('/politica-envio')
def politica_envio():
    return render_template('politica-envio.html')

@app.route('/politica-privacidade')
def politica_privacidade():
    return render_template('politica-privacidade.html')

@app.route('/politica-servico')
def politica_servico():
    return render_template('politica-servico.html')

@app.route('/termos-servico')
def termos_servico():
    return render_template('termos-servico.html')

@app.route('/finalizar-pedido')
def finalizar_pedido():
    return render_template('finalizar_pedido.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


