from flask import Flask, request, jsonify
import pdfplumber
import pandas as pd
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def pdf_a_excel(pdf_path):
    all_data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                all_data.extend(table)
    df = pd.DataFrame(all_data)
    df.columns = df.iloc[2]  # Usa encabezados reales (fila 3)
    df = df[3:]              # Elimina encabezados
    return df

def contar_por_ph(df):
    if 'PH' not in df.columns:
        return {"error": "No se encontró columna PH"}
    return df['PH'].value_counts().to_dict()

def contar_por_cliente(df):
    if 'CLIENTE' not in df.columns:
        return {"error": "No se encontró columna CLIENTE"}
    df['cliente'] = df['CLIENTE'].apply(lambda x: ' '.join(x.split()[:-1]))
    df['id'] = df['CLIENTE'].apply(lambda x: x.split()[-1])
    clientes = df.groupby(['cliente', 'id']).size().reset_index(name='cantidad')
    return clientes.to_dict(orient='records')

@app.route('/procesar', methods=['POST'])
def procesar():
    archivo = request.files['archivo']
    modo = request.form.get('modo')  # 'ph' o 'cliente'

    if not archivo or not modo:
        return jsonify({'error': 'Faltan datos (archivo o modo)'}), 400

    ruta_pdf = os.path.join(UPLOAD_FOLDER, archivo.filename)
    archivo.save(ruta_pdf)

    try:
        df = pdf_a_excel(ruta_pdf)
    except Exception as e:
        return jsonify({'error': f'Error al leer PDF: {str(e)}'}), 500

    if modo == 'ph':
        resultado = contar_por_ph(df)
    elif modo == 'cliente':
        resultado = contar_por_cliente(df)
    else:
        return jsonify({'error': 'Modo inválido'}), 400

    return jsonify({'resultado': resultado})

@app.route('/')
def home():
    return "✅ API Flask activa en Render"

# ✅ Esta parte es clave para Render:
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
