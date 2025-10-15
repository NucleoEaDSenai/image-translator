import streamlit as st
import easyocr
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tempfile, cv2, os

# ==========================================
# CONFIGURAÇÃO GERAL
# ==========================================
st.set_page_config(page_title="Tradutor Visual Profissional", layout="wide")
st.title("🖼️ Tradutor Visual Profissional (OCR + LibreTranslate)")

st.markdown("""
Envie uma imagem (fluxograma, slide, manual etc.)  
O sistema detecta automaticamente os textos, traduz e recria a imagem fiel ao original.
""")

# ==========================================
# IDIOMAS
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
# OCR E TRADUÇÃO
# ==========================================
ENDPOINTS = [
    "https://libretranslate.com/translate",
    "https://translate.argosopentech.com/translate",
    "https://libretranslate.de/translate"
]

@st.cache_resource
def carregar_ocr():
    """Carrega o modelo OCR com suporte pt/en."""
    return easyocr.Reader(["pt", "en"])

def preprocessar_imagem(caminho):
    """Aumenta contraste e binariza imagem para OCR mais limpo."""
    img = cv2.imread(caminho)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binaria = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contr = cv2.convertScaleAbs(binaria, alpha=1.5, beta=30)
    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    cv2.imwrite(tmp_path, contr)
    return tmp_path

def traduzir_texto(texto, destino):
    """Traduz texto com fallback automático."""
    # Mantém siglas como TAP, CQ etc.
    if texto.strip().isupper() and len(texto.split()) <= 3:
        return texto
    for url in ENDPOINTS:
        try:
            r = requests.post(url, json={"q": texto, "source": "auto", "target": destino}, timeout=20)
            if r.status_code == 200:
                return r.json().get("translatedText", texto)
        except:
            continue
    return texto

# ==========================================
# FUNÇÕES VISUAIS
# ==========================================
def cor_media_regiao(img_np, bbox):
    (x0, y0, x1, y1) = map(int, bbox)
    recorte = img_np[y0:y1, x0:x1]
    if recorte.size == 0:
        return (255, 255, 255)
    media = tuple(map(int, np.mean(recorte, axis=(0, 1))))
    return media

def escolher_cor_texto(cor_fundo):
    luminancia = (0.299*cor_fundo[0] + 0.587*cor_fundo[1] + 0.114*cor_fundo[2])
    return (0, 0, 0) if luminancia > 128 else (255, 255, 255)

def carregar_fonte(tamanho=22):
    fontes = [
        "fonts/Roboto-VariableFont_wdth,wght.ttf",
        "fonts/Roboto-Italic-VariableFont_wdth,wght.ttf",
        "fonts/Acme-Regular.ttf"
    ]
    for f in fontes:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, tamanho)
            except:
                continue
    return ImageFont.load_default()

# ==========================================
# TRADUÇÃO DA IMAGEM
# ==========================================
def traduzir_imagem(caminho, destino):
    reader = carregar_ocr()
    caminho_pre = preprocessar_imagem(caminho)
    results = reader.readtext(caminho_pre, detail=1, paragraph=False)

    img = Image.open(caminho).convert("RGB")
    draw = ImageDraw.Draw(img)
    img_np = np.array(img)

    for res in results:
        if len(res) == 3:
            bbox, texto, conf = res
        else:
            continue

        if conf < 0.6 or not texto.strip():
            continue

        # bounding box para área simples
        (x0, y0) = np.min(bbox, axis=0)
        (x2, y2) = np.max(bbox, axis=0)
        bbox_rect = [x0, y0, x2, y2]

        traducao = traduzir_texto(texto, destino)
        cor_fundo = cor_media_regiao(img_np, bbox_rect)
        cor_texto = escolher_cor_texto(cor_fundo)

        draw.rectangle(bbox_rect, fill=cor_fundo)
        fonte = carregar_fonte(24)

        # Centralizar texto
        largura_texto = draw.textlength(traducao, font=fonte)
        largura_box = bbox_rect[2] - bbox_rect[0]
        altura_box = bbox_rect[3] - bbox_rect[1]
        altura_fonte = fonte.size
        x_central = bbox_rect[0] + (largura_box - largura_texto) / 2
        y_central = bbox_rect[1] + (altura_box - altura_fonte) / 2

        draw.text((x_central, y_central), traducao, fill=cor_texto, font=fonte)

    out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    img.save(out_path)
    return out_path

# ==========================================
# INTERFACE STREAMLIT
# ==========================================
arquivo = st.file_uploader("📤 Envie a imagem (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

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
st.caption("💡 Tradução automática via LibreTranslate, OCR otimizado e preservação visual completa.")
