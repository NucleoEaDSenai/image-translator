import streamlit as st
import easyocr
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import tempfile
import os

# ==========================================
# CONFIGURAÇÃO GERAL
# ==========================================
st.set_page_config(page_title="Tradutor Visual Profissional v6", layout="wide")
st.title("🖼️ Tradutor Visual Profissional v6")
st.markdown("""
Upload de uma imagem contendo textos (fluxogramas, slides, prints, manuais, etc.)  
O sistema detecta automaticamente os textos, traduz e gera uma nova imagem **idêntica visualmente**,  
mantendo cor, proporção, layout e fonte equivalente à original.
""")

# ==========================================
# IDIOMAS DISPONÍVEIS
# ==========================================
idiomas = {
    "Português → Inglês": ("pt", "en"),
    "Inglês → Português": ("en", "pt"),
    "Inglês → Espanhol": ("en", "es"),
    "Português → Espanhol": ("pt", "es"),
    "Espanhol → Inglês": ("es", "en")
}
idioma_escolhido = st.selectbox("Escolha o par de tradução", list(idiomas.keys()))
src_lang, tgt_lang = idiomas[idioma_escolhido]

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
    """Carrega o modelo OCR para os idiomas principais."""
    return easyocr.Reader(["pt", "en", "es"])

def preprocessar_imagem(caminho):
    """Aumenta contraste e nitidez da imagem para OCR."""
    img = cv2.imread(caminho)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    _, binaria = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    sharpen_kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharpen = cv2.filter2D(binaria, -1, sharpen_kernel)
    temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    cv2.imwrite(temp_path, sharpen)
    return temp_path

def traduzir_texto(texto, origem, destino):
    """Traduz texto com redundância de endpoints."""
    texto = texto.strip()
    if not texto:
        return texto
    # ignora siglas e blocos curtos
    if texto.isupper() and len(texto.split()) <= 3:
        return texto
    for url in ENDPOINTS:
        try:
            r = requests.post(url, json={"q": texto, "source": origem, "target": destino}, timeout=25)
            if r.status_code == 200:
                return r.json().get("translatedText", texto)
        except Exception:
            continue
    return texto

# ==========================================
# FONTES E RENDERIZAÇÃO
# ==========================================
def carregar_fonte(tamanho=20, bold=False):
    """Carrega a fonte mais próxima visualmente."""
    fontes = [
        "fonts/Roboto-VariableFont_wdth,wght.ttf",
        "fonts/Arial.ttf",
        "fonts/Acme-Regular.ttf"
    ]
    for f in fontes:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, tamanho)
            except:
                continue
    return ImageFont.load_default()

def ajustar_tamanho_fonte(draw, texto, bbox):
    """Ajusta o tamanho da fonte para caber perfeitamente na área."""
    largura_box = bbox[2][0] - bbox[0][0]
    altura_box = bbox[2][1] - bbox[0][1]
    tamanho = 10
    fonte = carregar_fonte(tamanho)
    while draw.textlength(texto, font=fonte) < largura_box * 0.9 and tamanho < altura_box:
        tamanho += 1
        fonte = carregar_fonte(tamanho)
        if tamanho > 100:
            break
    return fonte

def cor_media_regiao(img_np, bbox):
    """Determina a cor média de fundo na área do texto."""
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

# ==========================================
# FUNÇÃO PRINCIPAL
# ==========================================
def traduzir_imagem(caminho, origem, destino):
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

        texto_limpo = texto.strip()
        traducao = traduzir_texto(texto_limpo, origem, destino)
        cor_fundo = cor_media_regiao(img_np, bbox)
        cor_texto = escolher_cor_texto(cor_fundo)
        fonte = ajustar_tamanho_fonte(draw, traducao, bbox)

        # Apaga texto antigo
        draw.polygon(bbox, fill=cor_fundo)

        # Centraliza novo texto
        x0, y0 = bbox[0]
        largura_box = bbox[2][0] - x0
        altura_box = bbox[2][1] - bbox[0][1]
        largura_texto = draw.textlength(traducao, font=fonte)
        altura_fonte = fonte.size
        x_central = x0 + (largura_box - largura_texto) / 2
        y_central = y0 + (altura_box - altura_fonte) / 2
        draw.text((x_central, y_central), traducao, fill=cor_texto, font=fonte)

    out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    img.save(out_path)
    return out_path

# ==========================================
# INTERFACE STREAMLIT
# ==========================================
arquivo = st.file_uploader("📤 Envie a imagem (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if arquivo and st.button("🚀 Traduzir imagem"):
    with st.spinner("Processando imagem e traduzindo textos..."):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp.write(arquivo.read())
        tmp.close()
        out_path = traduzir_imagem(tmp.name, src_lang, tgt_lang)

        col1, col2 = st.columns(2)
        with col1:
            st.image(tmp.name, caption="Imagem original", use_column_width=True)
        with col2:
            st.image(out_path, caption=f"Imagem traduzida ({idioma_escolhido})", use_column_width=True)

        with open(out_path, "rb") as f:
            st.download_button("📥 Baixar imagem traduzida", f, file_name="imagem_traduzida.png")

st.markdown("---")
st.caption("💡 Tradução fiel via LibreTranslate, OCR adaptativo e renderização com fontes equivalentes (Roboto/Arial).")
