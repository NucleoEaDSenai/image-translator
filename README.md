# 🖼️ Tradutor Visual de Imagens

Aplicativo em [Streamlit](https://streamlit.io/) que traduz o texto de imagens, como fluxogramas, slides, prints e manuais, mantendo o layout original.

Ele lê o texto da imagem com OCR ([EasyOCR](https://github.com/JaidedAI/EasyOCR)), traduz cada trecho com o [LibreTranslate](https://libretranslate.com/), apaga o texto original e escreve a tradução no mesmo lugar, com cor de fundo e tamanho de fonte ajustados.

## Idiomas suportados

- Português → Inglês
- Inglês → Português
- Inglês → Espanhol
- Português → Espanhol
- Espanhol → Inglês

## Requisitos

- **Python 3.10 ou superior** (recomendado: 3.12)
- Conexão com a internet: a tradução usa servidores públicos do LibreTranslate e, na primeira execução, o EasyOCR baixa os modelos de OCR
- Cerca de 2 GB livres em disco para as dependências (PyTorch, OpenCV etc.)

## Como rodar

### Windows (automático)

1. Instale o Python pelo [python.org](https://www.python.org/downloads/). Durante a instalação, marque **"Add Python to PATH"**.
2. Dê dois cliques em **`rodar_app.bat`**.

Na primeira vez, o script cria o ambiente virtual (`.venv`) e instala as dependências, o que leva alguns minutos. Nas próximas vezes, o app abre direto. As dependências só são reinstaladas se o `requirements.txt` mudar.

O navegador abre sozinho em **http://localhost:8501**. Para encerrar, feche a janela do terminal.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
# PyTorch apenas para CPU (opcional, mas bem menor que a versão com CUDA)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

streamlit run app_image_translator.py
```

Nas próximas vezes, basta rodar:

```bash
source .venv/bin/activate
streamlit run app_image_translator.py
```

## Como usar

1. Escolha o par de idiomas.
2. Envie uma imagem PNG, JPG ou JPEG.
3. Clique em **🚀 Traduzir imagem**.
4. Compare a imagem original com a traduzida e clique em **📥 Baixar imagem traduzida**.

## Estrutura do projeto

```
image-translator/
├── app_image_translator.py   # aplicativo Streamlit
├── requirements.txt          # dependências Python
├── rodar_app.bat             # inicializador automático para Windows
└── fonts/                    # fontes usadas para escrever a tradução
```

## Problemas comuns

| Problema | Solução |
|---|---|
| `Python nao encontrado` ao abrir o `.bat` | Reinstale o Python marcando **"Add Python to PATH"** |
| A primeira execução demora muito | É normal: o PyTorch e os modelos do EasyOCR são baixados uma única vez |
| A imagem sai sem tradução, com o texto original | Os servidores públicos do LibreTranslate podem estar fora do ar ou exigir chave de API. Tente novamente mais tarde |
| Erro ao instalar o `torch` | Use o Python 3.12. Versões muito novas podem ainda não ter pacotes do PyTorch |
| Quero reinstalar tudo do zero | Apague a pasta `.venv` e rode o app de novo |

## Limitações

- Só reconhece textos com confiança de OCR acima de 60%.
- Palavras curtas em MAIÚSCULAS (até 3 palavras) não são traduzidas, para preservar siglas.
- Imagens com mais de 2000 px são reduzidas antes do processamento.
- O processamento é feito na CPU, então imagens com muito texto podem demorar.
