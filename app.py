import os
import io
import base64
from flask import Flask, render_template, request
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pytz
from matplotlib.dates import DateFormatter
import matplotlib
import logging

matplotlib.use('Agg')
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Dicionários de dados
MOEDAS = {
    '1': {'nome': 'Dólar Americano', 'sigla': 'USD', 'simbolo': 'US$'},
    '2': {'nome': 'Euro', 'sigla': 'EUR', 'simbolo': '€'},
    '3': {'nome': 'Libra Esterlina', 'sigla': 'GBP', 'simbolo': '£'}
}

PERIODOS = {
    '1': {'nome': '1 Mês', 'dias': 30},
    '2': {'nome': '3 Meses', 'dias': 90},
    '3': {'nome': '6 Meses', 'dias': 180},
    '4': {'nome': '1 Ano', 'dias': 365}
}

def obter_cotacao_atual(moeda_info):
    try:
        sigla = moeda_info['sigla']
        url = f"https://economia.awesomeapi.com.br/json/last/{sigla}-BRL"
        response = requests.get(url)
        
        if response.status_code == 200:
            dados = response.json()
            comercial = float(dados[f"{sigla}BRL"]['bid'])
            turismo = comercial * 1.05
            return {
                'comercial': comercial,
                'turismo': turismo,
                'media': (comercial + turismo) / 2,
                'atualizacao': datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M:%S')
            }
        return None
    except Exception as e:
        logging.error(f"Erro na cotação atual: {e}")
        return None

def obter_historico_moeda(moeda_info, dias):
    try:
        sigla = moeda_info['sigla']
        url = f"https://economia.awesomeapi.com.br/json/daily/{sigla}-BRL/{dias}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            dados = response.json()
            df = pd.DataFrame(dados)
            df['data'] = pd.to_datetime(df['timestamp'], unit='s')
            df['comercial'] = df['bid'].astype(float)
            df['turismo'] = df['comercial'] * 1.05
            df['media'] = (df['comercial'] + df['turismo']) / 2
            return df.sort_values('data')
        return None
    except Exception as e:
        logging.error(f"Erro no histórico: {e}")
        return None

def plot_to_base64(df):
    plt.figure(figsize=(10,6), facecolor='#1a1a1a')
    ax = plt.gca()
    ax.set_facecolor('#1a1a1a')
    
    plt.plot(df['data'], df['comercial'], label='Comercial', color='#3498db', linewidth=2)
    plt.plot(df['data'], df['turismo'], label='Turismo', color='#e74c3c', linewidth=2)
    plt.plot(df['data'], df['media'], label='Média', color='#2ecc71', linewidth=2, linestyle='--')
    
    plt.title('Evolução das Cotações', color='white', pad=20)
    plt.xlabel('Data', color='white')
    plt.ylabel('Valor (R$)', color='white')
    plt.xticks(rotation=45, color='#95a5a6')
    plt.yticks(color='#95a5a6')
    plt.gca().xaxis.set_major_formatter(DateFormatter('%d/%b/%y'))
    plt.grid(color='#2d2d2d', alpha=0.5)
    
    legend = plt.legend(facecolor='#2d2d2d', edgecolor='none')
    for text in legend.get_texts():
        text.set_color('white')
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, facecolor='#1a1a1a')
    plt.close()
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

@app.route('/', methods=['GET', 'POST'])
def index():
    contexto = {
        'moedas': MOEDAS,
        'periodos': PERIODOS,
        'error': None,
        'cotacao': None,
        'graph': None,
        'atualizacao': None
    }

    if request.method == 'POST':
        moeda_key = request.form.get('moeda')
        periodo_key = request.form.get('periodo')

        if moeda_key not in MOEDAS or periodo_key not in PERIODOS:
            contexto['error'] = "Opção inválida selecionada"
        else:
            moeda = MOEDAS.get(moeda_key)
            periodo = PERIODOS.get(periodo_key)
            
            if moeda and periodo:
                contexto['cotacao'] = obter_cotacao_atual(moeda)
                historico = obter_historico_moeda(moeda, periodo['dias'])
                
                if historico is not None:
                    contexto['graph'] = plot_to_base64(historico)
                    contexto['atualizacao'] = contexto['cotacao']['atualizacao'] if contexto['cotacao'] else None
                else:
                    contexto['error'] = "Erro ao obter dados históricos"
            else:
                contexto['error'] = "Opção inválida selecionada"

    return render_template('index.html', **contexto)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
