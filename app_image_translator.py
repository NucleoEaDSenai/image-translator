import streamlit as st
import easyocr
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tempfile, os, statistics

# ==========================================
# CONFIGURAÇÃO GERAL
# ==========================================
st.set_page_config(page_title="Tradutor de Imagens Avançado", layout="wide")
st.title("🖼️ Tradutor de Imagens Avançado (LibreTranslate + EasyOCR + IA Visual)")

st.markdown("""
Faça upload de uma imagem com textos em português (ou outro idioma).  
O sistema detecta automaticamente o texto, traduz para o idioma escolhido  
e gera uma **nova imagem fiel ao original** — mantendo cores, tamanho e posição.
""")

# ==========================================
# SELEÇÃO DE IDIOMA
# ==========================================
idiomas = {
    "Inglês": "en",
    "Espanhol": "es",
    "Francês": "fr",
    "Italiano": "it",
    "Alemão": "de",
    "Português": "pt"
}
idioma_destino = st.selectbox("Idioma de destino", list(idiomas.keys()))
lang_code = idiomas[idioma_destino]

# ==========================================
# FUNÇÕES BASE
# ==========================================
ENDPOINTS = [
    "https://libretranslate.com/translate",
    "https://translate.argosopentech.com/translate",
    "https://libretranslate.de/translate"
]

@st.cache_resource
def carregar_ocr():
    return easyocr.Reader(["pt", "en", "es", "fr", "it", "de"])

def traduzir_texto(texto, destino):
    for url in ENDPOINTS:
        try:
            r = requests.post(url, json={"q": texto, "source": "auto", "target": destino}, timeout=25)
            if r.status_code == 200:
                return r.json().get("translatedText", texto)
        except Exception:
            continue
    return texto

def cor_media_regiao(img_np, bbox):
    """Calcula a cor média da região (usada para pintar fundo)."""
    (x0, y0), (x1, y1) = bbox[0], bbox[2]
    x0, y0, x1, y1 = map(int, [x0, y0, x1, y1])
    recorte = img_np[y0:y1, x0:x1]
    if recorte.size == 0:
        return (255, 255, 255)
    media = tuple(map(int, np.mean(recorte, axis=(0, 1))))
    return media

def escolher_cor_texto(cor_fundo):
    """Escolhe preto ou branco com melhor contraste."""
    luminancia = (0.299*cor_fundo[0] + 0.587*cor_fundo[1] + 0.114*cor_fundo[2])
    return (0, 0, 0) if luminancia > 128 else (255, 255, 255)

def ajustar_tamanho_fonte(draw, texto, bbox, fonte_base):
    """Redimensiona fonte para caber dentro do box original."""
    largura_box = bbox[2][0] - bbox[0][0]
    tamanho = 20
    fonte = ImageFont.truetype(fonte_base, tamanho)
    while draw.textlength(texto, font=fonte) < largura_box * 0.9:
        tamanho += 1
        fonte = ImageFont.truetype(fonte_base, tamanho)
        if tamanho > 120:
            break
    return fonte

def traduzir_imagem(img_path, destino):
    reader = carregar_ocr()
    results = reader.readtext(img_path, detail=1)
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    img_np = np.array(img)
    fonte_base = os.path.join("fonts", "Roboto-Regular.ttf")

    for (bbox, texto, conf) in results:
        if conf < 0.4 or not texto.strip():
            continue
        traducao = traduzir_texto(texto, destino)
        cor_fundo = cor_media_regiao(img_np, bbox)
        cor_texto = escolher_cor_texto(cor_fundo)

        # Apaga o texto original
        draw.polygon(bbox, fill=cor_fundo)

        # Ajusta fonte
        fonte = ajustar_tamanho_fonte(draw, traducao, bbox, fonte_base)

        # Centraliza verticalmente
        x0, y0 = bbox[0]
        y0_adj = y0 + ((bbox[2][1] - bbox[0][1]) - fonte.size) / 2

        # Desenha o texto traduzido
        draw.text((x0, y0_adj), traducao, fill=cor_texto, font=fonte)

    out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    img.save(out_path)
    return out_path

# ==========================================
# UPLOAD E EXIBIÇÃO
# ==========================================
arquivo = st.file_uploader("📤 Envie uma imagem (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if arquivo and st.button("🚀 Traduzir imagem"):
    with st.spinner("Detectando e traduzindo textos..."):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp.write(arquivo.read())
        tmp.close()

        out_path = traduzir_imagem(tmp.name, lang_code)

        col1, col2 = st.columns(2)
        with col1:
            st.image(tmp.name, caption="Imagem original", use_column_width=True)
        with col2:
            st.image(out_path, caption=f"Imagem traduzida ({idioma_destino})", use_column_width=True)

        with open(out_path, "rb") as f:
            st.download_button("📥 Baixar imagem traduzida", f, file_name="imagem_traduzida.png")

st.markdown("---")
st.caption("💡 Tradutor visual com LibreTranslate + EasyOCR + Reconstrução de cor e layout • 100 % gratuito.")
