import streamlit as st
import easyocr
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tempfile, os

# ==========================================
# CONFIGURAÇÃO GERAL
# ==========================================
st.set_page_config(page_title="Tradutor de Imagens Profissional", layout="wide")
st.title("🖼️ Tradutor de Imagens Profissional (LibreTranslate + EasyOCR + Fontes Locais)")

st.markdown("""
Faça upload de uma imagem (fluxograma, slide, diagrama, etc.).  
O sistema detecta automaticamente os textos, traduz por blocos  
e gera uma **nova imagem fiel ao layout original** — mantendo cores, fontes e posições.
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
# CONFIGURAÇÃO OCR + API
# ==========================================
ENDPOINTS = [
    "https://libretranslate.com/translate",
    "https://translate.argosopentech.com/translate",
    "https://libretranslate.de/translate"
]

@st.cache_resource
def carregar_ocr():
    return easyocr.Reader(["pt", "en", "es", "fr", "it", "de"])

def traduzir_texto_bloco(texto, destino):
    """Traduz blocos de texto inteiros para manter coerência."""
    for url in ENDPOINTS:
        try:
            r = requests.post(url, json={"q": texto, "source": "auto", "target": destino}, timeout=25)
            if r.status_code == 200:
                return r.json().get("translatedText", texto)
        except Exception:
            continue
    return texto

# ==========================================
# FUNÇÕES VISUAIS
# ==========================================
def cor_media_regiao(img_np, bbox):
    (x0, y0), (x1, y1) = bbox[0], bbox[2]
    x0, y0, x1, y1 = map(int, [x0, y0, x1, y1])
    recorte = img_np[y0:y1, x0:x1]
    if recorte.size == 0:
        return (255, 255, 255)
    media = tuple(map(int, np.mean(recorte, axis=(0, 1))))
    return media

def escolher_cor_texto(cor_fundo):
    luminancia = (0.299*cor_fundo[0] + 0.587*cor_fundo[1] + 0.114*cor_fundo[2])
    return (0, 0, 0) if luminancia > 128 else (255, 255, 255)

def carregar_fonte_variavel(tamanho=20):
    fontes = [
        "fonts/Roboto-VariableFont_wdth,wght.ttf",
        "fonts/Roboto-Italic-VariableFont_wdth,wght.ttf",
        "fonts/Acme-Regular.ttf"
    ]
    for fpath in fontes:
        if os.path.exists(fpath):
            try:
                return ImageFont.truetype(fpath, tamanho)
            except:
                continue
    return ImageFont.load_default()

def ajustar_tamanho_fonte(draw, texto, bbox):
    largura_box = bbox[2][0] - bbox[0][0]
    altura_box = bbox[2][1] - bbox[0][1]
    tamanho = 10
    fonte = carregar_fonte_variavel(tamanho)
    while draw.textlength(texto, font=fonte) < largura_box * 0.9 and tamanho < altura_box:
        tamanho += 1
        fonte = carregar_fonte_variavel(tamanho)
        if tamanho > 120:
            break
    return fonte

def traduzir_imagem(img_path, destino):
    reader = carregar_ocr()
    results = reader.readtext(img_path, detail=1, paragraph=True)
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    img_np = np.array(img)

    for (bbox, texto, conf) in results:
        if conf < 0.5 or not texto.strip():
            continue
        texto_limpo = " ".join(texto.split())
        traducao = traduzir_texto_bloco(texto_limpo, destino)
        cor_fundo = cor_media_regiao(img_np, bbox)
        cor_texto = escolher_cor_texto(cor_fundo)
        draw.polygon(bbox, fill=cor_fundo)
        fonte = ajustar_tamanho_fonte(draw, traducao, bbox)

        # Centralização dentro da caixa detectada
        x0, y0 = bbox[0]
        largura_texto = draw.textlength(traducao, font=fonte)
        largura_box = bbox[2][0] - x0
        altura_box = bbox[2][1] - bbox[0][1]
        altura_fonte = fonte.size
        x_central = x0 + (largura_box - largura_texto) / 2
        y_central = y0 + (altura_box - altura_fonte) / 2

        draw.text((x_central, y_central), traducao, fill=cor_texto, font=fonte)

    out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    img.save(out_path)
    return out_path

# ==========================================
# UPLOAD E EXIBIÇÃO
# ==========================================
arquivo = st.file_uploader("📤 Envie uma imagem (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if arquivo and st.button("🚀 Traduzir imagem"):
    with st.spinner("Detectando blocos e traduzindo..."):
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
st.caption("💡 Tradução por blocos — ideal para fluxogramas, manuais e slides técnicos.")
