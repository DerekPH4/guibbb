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
    df.columns = df.iloc[2]
    df = df[3:]
    return df

def contar_por_ph(df):
    ph_counts = df['PH'].value_counts().to_dict()
    return ph_counts

def contar_por_cliente(df):
    df['cliente'] = df['CLIENTE'].apply(lambda x: ' '.join(x.split()[:-1]))
    df['id'] = df['CLIENTE'].apply(lambda x: x.split()[-1])
    clientes = df.groupby(['cliente', 'id']).size().reset_index(name='cantidad')
    return clientes.to_dict(orient='records')

@app.route('/procesar', methods=['POST'])
def procesar():
    archivo = request.files['archivo']
    modo = request.form.get('modo')  # 'ph' o 'cliente'

    ruta_pdf = os.path.join(UPLOAD_FOLDER, archivo.filename)
    archivo.save(ruta_pdf)

    df = pdf_a_excel(ruta_pdf)

    if modo == 'ph':
        resultado = contar_por_ph(df)
    elif modo == 'cliente':
        resultado = contar_por_cliente(df)
    else:
        return jsonify({'error': 'Modo inválido'}), 400

    return jsonify({'resultado': resultado})

@app.route('/')
def home():
    return "API Flask para app Android - Activa ✅"

if __name__ == '__main__':
    app.run(debug=True)

