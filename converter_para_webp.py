import os
from PIL import Image

# Pasta com as imagens
pasta_imagens = 'static/uploads'

# Extensões que vamos converter
extensoes_suportadas = ['.jpg', '.jpeg', '.png']

# Loop por todos os arquivos da pasta
for nome_arquivo in os.listdir(pasta_imagens):
    nome_completo = os.path.join(pasta_imagens, nome_arquivo)

    # Verifica se é imagem suportada
    if os.path.isfile(nome_completo) and any(nome_arquivo.lower().endswith(ext) for ext in extensoes_suportadas):
        nome_base, _ = os.path.splitext(nome_arquivo)
        novo_caminho = os.path.join(pasta_imagens, f"{nome_base}.webp")

        # Converter para .webp
        try:
            with Image.open(nome_completo) as img:
                img.save(novo_caminho, 'webp')
                print(f"Convertido: {nome_arquivo} -> {nome_base}.webp")
        except Exception as e:
            print(f"Erro ao converter {nome_arquivo}: {e}")
