import subprocess
import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import locale
import plotly.express as px
from filelock import FileLock, Timeout


# Função para converter datas
def replace_month(date_str):
    month_map = {
        'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr', 'mai': 'May', 'jun': 'Jun',
        'jul': 'Jul', 'ago': 'Aug', 'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'
    }
    for pt, en in month_map.items():
        date_str = date_str.replace(pt, en)
    return date_str

# Carregar o arquivo HTML
with open('Jira (3).html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# Analisar o conteúdo HTML usando BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Extrair os cabeçalhos da tabela
table = soup.find('table', {'id': 'issuetable'})
headers = [header.text.strip() for header in table.find_all('th')]

# Extrair as linhas da tabela
rows = []
for row in table.find('tbody').find_all('tr'):
    cells = row.find_all('td')
    row_data = [cell.text.strip() for cell in cells]
    rows.append(row_data)

# Criar um DataFrame a partir dos dados extraídos
df = pd.DataFrame(rows, columns=headers)
df['Criado'] = df['Criado'].apply(replace_month)
df['Criado'] = pd.to_datetime(df['Criado'], format='%d/%b/%y %I:%M %p', errors='coerce')

# Selecionar as colunas relevantes
df_selected = df[['Pai', 'Tipo de item', 'Status', 'Responsável', 'Criado']].copy()
df_selected['Criado'] = pd.to_datetime(df_selected['Criado'], format='%d/%b/%y %I:%M %p', errors='coerce')

# 1. Gráfico de barras: Quantidade de itens por "Tipo de Item" e "Status" para cada "Pai"
item_status_count = df_selected.groupby(['Pai', 'Status']).size().reset_index(name='Count')

fig1 = px.bar(item_status_count, x='Pai', y='Count', color='Status',
              title='Quantidade de itens por Tipo de Item e Status para cada Módulo',
              labels={'Count': 'Quantidade de Itens', 'Pai': 'Módulo', 'Status': 'Status'},
              text='Count')  # Mostra o valor de 'Count' em cada barra
fig1.update_traces(texttemplate='%{text:.2s}', textposition='outside')  # Formatação dos textos


# 2. Gráfico de barras empilhadas: Distribuição de Responsável por Tipo de Item
responsible_item_count = df_selected.groupby(['Responsável', 'Tipo de item']).size().reset_index(name='Count')

fig2 = px.bar(responsible_item_count, x='Responsável', y='Count', color='Tipo de item',
              title='Distribuição de Responsável por Tipo de Item',
              labels={'Count': 'Quantidade de Itens', 'Responsável': 'Responsável', 'Tipo de item': 'Tipo de Item'},
              text='Count')  # Mostra o valor de 'Count' em cada segmento de barra
fig2.update_traces(texttemplate='%{text:.2s}', textposition='inside')  # Mantém o texto dentro das barras


locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
# 3. Gráfico de linha do tempo: Itens criados por Tipo de Item
df_filtered = df_selected.dropna(subset=['Criado'])
df_filtered['Criado'] = df_filtered['Criado'].dt.to_period('M').dt.to_timestamp()
df_timeline = df_filtered.groupby(['Criado', 'Tipo de item']).size().reset_index(name='Count')

fig3 = px.line(df_timeline, x='Criado', y='Count', color='Tipo de item',
               title='Linha do Tempo de Itens Criados por Tipo de Item',
               labels={'Criado': 'Data', 'Count': 'Quantidade de Itens Criados', 'Tipo de item': 'Tipo de Item'},
               text='Count')  # Mostra o valor de 'Count' em cada ponto
fig3.update_traces(texttemplate='%{text:.2s}', textposition='top center')  # Posiciona o texto acima dos pontos


fig3.update_xaxes(
    dtick="M1",
    tickformat="%b\n%Y"
)

# Configurar a página do Streamlit
st.set_page_config(layout='wide')

# Título da página
st.title("Dashboard de Itens")

# Exibir os gráficos no Streamlit
st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)
def run_streamlit(script_path):
    subprocess.run(["streamlit", "run", script_path])

if __name__ == '__main__':
    script_path = "dashboard.py"
    lock = FileLock("streamlit.lock")

    try:
        with lock.acquire(timeout=10):
            run_streamlit(script_path)
    except Timeout:
        print("Another instance of Streamlit is already running.")