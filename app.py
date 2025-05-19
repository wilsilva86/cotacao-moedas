import io
import base64
from flask import Flask, render_template, request
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import locale
import matplotlib
matplotlib.rcParams['axes.formatter.use_locale'] = True
from matplotlib.dates import DateFormatter

app = Flask(__name__)

# Configurar localização para formato brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')  # Para Windows
    except:
        pass

# Dicionário de moedas disponíveis
MOEDAS = {
    '1': {'nome': 'Dólar Americano', 'sigla': 'USD', 'simbolo': 'US$'},
    '2': {'nome': 'Euro', 'sigla': 'EUR', 'simbolo': '€'},
    '3': {'nome': 'Libra Esterlina', 'sigla': 'GBP', 'simbolo': '£'}
}

# Dicionário de períodos disponíveis
PERIODOS = {
    '1': {'nome': '1 Mês', 'dias': 30},
    '2': {'nome': '3 Meses', 'dias': 90},
    '3': {'nome': '6 Meses', 'dias': 180},
    '4': {'nome': '1 Ano', 'dias': 365}
}

def obter_cotacao_atual(moeda_info):
    """Função para obter a cotação atual da moeda selecionada"""
    try:
        sigla = moeda_info['sigla']
        url_comercial = f"https://economia.awesomeapi.com.br/json/last/{sigla}-BRL"
        
        response = requests.get(url_comercial)
        
        if response.status_code == 200:
            dados = response.json()
            chave_moeda = f"{sigla}BRL"
            
            cotacao_comercial = float(dados[chave_moeda]["bid"])
            
            try:
                url_turismo = f"https://economia.awesomeapi.com.br/json/last/{sigla}-BRLT"
                resp_turismo = requests.get(url_turismo)
                
                if resp_turismo.status_code == 200:
                    dados_turismo = resp_turismo.json()
                    chave_turismo = f"{sigla}BRLT"
                    
                    if chave_turismo in dados_turismo:
                        cotacao_turismo = float(dados_turismo[chave_turismo]["bid"])
                    else:
                        cotacao_turismo = cotacao_comercial * 1.05
                else:
                    cotacao_turismo = cotacao_comercial * 1.05
            except Exception:
                cotacao_turismo = cotacao_comercial * 1.05
            
            media = (cotacao_comercial + cotacao_turismo) / 2
            
            return {
                "comercial": cotacao_comercial,
                "turismo": cotacao_turismo,
                "media": media
            }
        else:
            return None
    except Exception as e:
        print(f"Erro: {e}")
        return None

def obter_historico_moeda(moeda_info, dias=180):
    """Função para obter o histórico de cotações dos últimos N dias"""
    try:
        sigla = moeda_info['sigla']
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=dias)
        
        url_comercial = f"https://economia.awesomeapi.com.br/json/daily/{sigla}-BRL/{dias}"
        
        resp_comercial = requests.get(url_comercial)
        
        if resp_comercial.status_code == 200:
            dados_comercial = resp_comercial.json()
            
            df_comercial = pd.DataFrame(dados_comercial)
            df_comercial['data'] = pd.to_datetime(df_comercial['timestamp'].astype(int), unit='s')
            df_comercial['comercial'] = df_comercial['bid'].astype(float)
            
            df = df_comercial[['data', 'comercial']].sort_values('data')
            df['turismo'] = df['comercial'] * 1.05
            df['media'] = (df['comercial'] + df['turismo']) / 2
            
            return df
        else:
            return None
    except Exception as e:
        print(f"Erro histórico: {e}")
        return None

def plot_to_base64(df, moeda_info, periodo_info):
    plt.switch_backend('Agg')
    plt.figure(figsize=(12, 6))
    
    # Mantém as casas decimais originais
    plt.plot(df['data'], df['media'], label='Média (Comercial/Turismo)', color='green', linewidth=2)
    plt.plot(df['data'], df['comercial'], label=f"{moeda_info['nome']} Comercial", color='blue', alpha=0.6)
    plt.plot(df['data'], df['turismo'], label=f"{moeda_info['nome']} Turismo", color='red', alpha=0.6)
    
    plt.title(f'Cotação do {moeda_info["nome"]} - Últimos {periodo_info["nome"]}', fontsize=16)
    plt.xlabel('Data', fontsize=12)
    plt.ylabel('Valor em R$', fontsize=12)
    
    # Formatação do eixo Y com 3 casas decimais e vírgula
    plt.gca().yaxis.set_major_formatter(plt.FormatStrFormatter('%.2f'))
    plt.gca().yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: locale.format_string('%.2f', x))
    )
    
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.gca().xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return image_base64

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        moeda_key = request.form.get('moeda')
        periodo_key = request.form.get('periodo')
        
        moeda_info = MOEDAS.get(moeda_key)
        periodo_info = PERIODOS.get(periodo_key)
        
        if not moeda_info or not periodo_info:
            return render_template('index.html', 
                                 moedas=MOEDAS, 
                                 periodos=PERIODOS, 
                                 error="Selecione opções válidas!")
        
        cotacao_atual = obter_cotacao_atual(moeda_info)
        historico = obter_historico_moeda(moeda_info, periodo_info['dias'])
        
        graph = plot_to_base64(historico, moeda_info, periodo_info) if historico is not None else None
        
        return render_template('resultado.html',
                             moeda=moeda_info,
                             periodo=periodo_info,
                             cotacao=cotacao_atual,
                             graph=graph)
    
    return render_template('index.html', moedas=MOEDAS, periodos=PERIODOS)

if __name__ == '__main__':
    app.run(debug=True)
