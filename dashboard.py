import subprocess
import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import locale
import plotly.express as px

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


# locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
# 3. Gráfico de linha do tempo: Itens criados por Tipo de Item
df_selected = df[['Pai', 'Tipo de item', 'Status', 'Responsável', 'Criado']].copy()
df_selected['Criado'] = pd.to_datetime(df_selected['Criado'], format='%d/%b/%y %I:%M %p', errors='coerce')
df_filtered = df_selected.dropna(subset=['Criado'])
df_filtered['Criado'] = df_filtered['Criado'].dt.to_period('M').dt.start_time

# Criar um índice com todos os meses no intervalo de datas
all_months = pd.date_range(start=df_filtered['Criado'].min(), end=df_filtered['Criado'].max(), freq='MS')

# Criar uma tabela pivô e reindexar para garantir todos os meses presentes
df_pivot = df_filtered.groupby(['Criado', 'Tipo de item']).size().unstack(fill_value=0).reindex(all_months, fill_value=0, method=None).stack().reset_index(name='Count')

# Renomear a coluna 'level_0' de volta para 'Criado'
df_pivot = df_pivot.rename(columns={'level_0': 'Criado'})

fig3 = px.line(df_pivot, x='Criado', y='Count', color='Tipo de item',
               title='Linha do Tempo de Itens Criados por Tipo de Item',
               labels={'Criado': 'Data', 'Count': 'Quantidade de Itens Criados', 'Tipo de item': 'Tipo de Item'},
               text='Count')  # Mostra o valor de 'Count' em cada ponto
fig3.update_traces(texttemplate='%{text:.2s}', textposition='top center')  # Posiciona o texto acima dos pontos
fig3.update_xaxes(dtick="M1", tickformat="%b\n%Y")

# Configurar a página do Streamlit
st.set_page_config(layout='wide')
st.title("Dashboard Análise de Dados Jira")

# Exibir os gráficos no Streamlit
st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)

# Carregar e processar o arquivo HTML
def load_html_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', {'id': 'issuetable'})
    headers = [header.text.strip() for header in table.find_all('th')]
    rows = [[cell.text.strip() for cell in row.find_all('td')] for row in table.find('tbody').find_all('tr')]
    df = pd.DataFrame(rows, columns=headers)
    df['Criado'] = df['Criado'].apply(replace_month)
    df['Resolvido'] = df['Resolvido'].apply(replace_month)
    df['[CHART] Date of First Response'] = df['[CHART] Date of First Response'].apply(replace_month)
    df['Criado'] = pd.to_datetime(df['Criado'], format='%d/%b/%y %I:%M %p', errors='coerce')
    df['Resolvido'] = pd.to_datetime(df['Resolvido'], format='%d/%b/%y %I:%M %p', errors='coerce')
    df['[CHART] Date of First Response'] = pd.to_datetime(df['[CHART] Date of First Response'],
                                                          format='%d/%b/%y %I:%M %p', errors='coerce')

    # Filtrando registros inválidos
    df = df[df['Criado'].notnull() & df['Resolvido'].notnull() & (df['Resolvido'] >= df['Criado'])]

    df['Tempo da Primeira Resposta'] = (df['[CHART] Date of First Response'] - df['Criado']).dt.total_seconds() / (
                3600 * 24)  # Convertendo para dias
    df['Tempo da Primeira Resposta'] = df['Tempo da Primeira Resposta'].fillna(0).astype(
        int)  # Substituindo NaNs por 0 e convertendo para inteiros
    df['Tempo de Solução'] = (df['Resolvido'] - df['Criado']).dt.total_seconds() / (3600 * 24)  # Convertendo para dias
    df['Tempo de Solução'] = df['Tempo de Solução'].fillna(0).astype(
        int)  # Substituindo NaNs por 0 e convertendo para inteiros
    return df


# # Iniciar a aplicação Streamlit
# st.title('Dashboard de Análise de Dados do Jira')

# Carregar os dados
jira_data = load_html_data('Jira (3).html')

# Filtros no sidebar
st.sidebar.title('Filtros')
tipo_selecionado_sidebar = st.sidebar.multiselect('Selecione o Tipo de Item (para gráficos)',
                                                  jira_data['Tipo de item'].unique(),
                                                  default=jira_data['Tipo de item'].unique())
prioridade_selecionada = st.sidebar.multiselect('Selecione a Prioridade', jira_data['Prioridade'].unique(),
                                                default=jira_data['Prioridade'].unique())

# Filtro para selecionar média ou total
metrica_selecionada = st.sidebar.radio('Selecione a Métrica', ['Média', 'Total'])

df_filtrado = jira_data[
    (jira_data['Tipo de item'].isin(tipo_selecionado_sidebar)) & (jira_data['Prioridade'].isin(prioridade_selecionada))]


# Gráfico de Tempo da Primeira Resposta por Mês
st.write('## Tempo da Primeira Resposta por Mês')

df_filtrado['Mês'] = df_filtrado['Criado'].dt.to_period('M').astype(str)

if metrica_selecionada == 'Média':
    resposta_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])[
        'Tempo da Primeira Resposta'].mean().reset_index()
    fig_resposta = px.line(resposta_por_mes, x='Mês', y='Tempo da Primeira Resposta', color='Tipo de item',
                           title='Tempo da Primeira Resposta por Mês (Média em dias)')
else:
    resposta_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])[
        'Tempo da Primeira Resposta'].sum().reset_index()
    fig_resposta = px.line(resposta_por_mes, x='Mês', y='Tempo da Primeira Resposta', color='Tipo de item',
                           title='Tempo da Primeira Resposta por Mês (Total em dias)')

st.plotly_chart(fig_resposta)

# Gráfico de Tempo de Solução por Mês
st.write('## Tempo de Solução por Mês')

if metrica_selecionada == 'Média':
    solucao_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])[
        'Tempo de Solução'].mean().reset_index()
    fig_solucao = px.line(solucao_por_mes, x='Mês', y='Tempo de Solução', color='Tipo de item',
                          title='Tempo de Solução por Mês (Média em dias)')
else:
    solucao_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])['Tempo de Solução'].sum().reset_index()
    fig_solucao = px.line(solucao_por_mes, x='Mês', y='Tempo de Solução', color='Tipo de item',
                          title='Tempo de Solução por Mês (Total em dias)')

st.plotly_chart(fig_solucao)

# Filtro de Tipo de Item para Tabela
tipo_selecionado_tabela = st.selectbox('Selecione o Tipo de Item (para tabela)', jira_data['Tipo de item'].unique())

# Tabela com filtro de Tipo de Item
st.write('## Tabela de Itens Filtrados')
df_tabela_filtrado = jira_data[jira_data['Tipo de item'] == tipo_selecionado_tabela]
st.dataframe(df_tabela_filtrado[['Chave', 'Status', 'Resumo', 'Descrição']])

# Carregar e processar o arquivo HTML


# Carregar e processar o arquivo backlog
def load_backlog_data(file_path):
    xls = pd.ExcelFile(file_path)
    sheets = []
    for sheet_name in xls.sheet_names:
        sheet = pd.read_excel(xls, sheet_name)
        sheets.append(sheet)
    backlog_data = pd.concat(sheets, ignore_index=True)
    return backlog_data

# Iniciar a aplicação Streamlit
st.title('Dashboard de Análise de Dados Backlog')

# Carregar os dados
backlog_data = load_backlog_data('backlog.xlsx')

# Exibir colunas do backlog para depuração
# st.write('Colunas disponíveis no backlog:', backlog_data.columns.tolist())

# Combinando dados do backlog com dados do Jira
if '#JIRA\nCard' in backlog_data.columns:
    jira_data = jira_data.merge(backlog_data, left_on='Chave', right_on='#JIRA\nCard', how='left')
else:
    st.error("A coluna '#JIRA\nCard' não está presente no backlog.")
# jira_data.to_csv('jira_data.csv', index=False, encoding='utf-8', sep=';')

# tipo_selecionado_sidebar = st.sidebar.multiselect('Selecione o Tipo de Item (para gráficos)', jira_data['Tipo de item'].unique(), default=jira_data['Tipo de item'].unique())
# prioridade_selecionada = st.sidebar.multiselect('Selecione a Prioridade', jira_data['Prioridade'].unique(), default=jira_data['Prioridade'].unique())

# df_filtrado = jira_data[(jira_data['Tipo de item'].isin(tipo_selecionado_sidebar)) & (jira_data['Prioridade'].isin(prioridade_selecionada))]
df_filtrado = jira_data[jira_data['Prioridade'].isin(prioridade_selecionada)]

df_filtrado = df_filtrado[df_filtrado['Tipo de item'].isin(['Bug', 'Melhoria'])]

# Gráfico de Tempo da Primeira Resposta por Mês
st.write('## Tempo da Primeira Resposta por Mês (apenas Bug e Melhoria)')

df_filtrado['Mês'] = df_filtrado['Criado'].dt.to_period('M').astype(str)

if metrica_selecionada == 'Média':
    resposta_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])['Tempo da Primeira Resposta'].mean().reset_index()
    fig_resposta = px.line(resposta_por_mes, x='Mês', y='Tempo da Primeira Resposta', color='Tipo de item', title='Tempo da Primeira Resposta por Mês (Média em dias)',color_discrete_map={'Melhoria': 'blue', 'Bug': 'red'})
else:
    resposta_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])['Tempo da Primeira Resposta'].sum().reset_index()
    fig_resposta = px.line(resposta_por_mes, x='Mês', y='Tempo da Primeira Resposta', color='Tipo de item', title='Tempo da Primeira Resposta por Mês (Total em dias)',color_discrete_map={'Melhoria': 'blue', 'Bug': 'red'})

st.plotly_chart(fig_resposta)

# Gráfico de Tempo de Solução por Mês
st.write('## Tempo de Solução por Mês')

if metrica_selecionada == 'Média':
    solucao_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])['Tempo de Solução'].mean().reset_index()
    fig_solucao = px.line(solucao_por_mes, x='Mês', y='Tempo de Solução', color='Tipo de item', title='Tempo de Solução por Mês (Média em dias)',color_discrete_map={'Melhoria': 'blue', 'Bug': 'red'})
else:
    solucao_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])['Tempo de Solução'].sum().reset_index()
    fig_solucao = px.line(solucao_por_mes, x='Mês', y='Tempo de Solução', color='Tipo de item', title='Tempo de Solução por Mês (Total em dias)',color_discrete_map={'Melhoria': 'blue', 'Bug': 'red'})

st.plotly_chart(fig_solucao)

# Verificar se as colunas estão presentes antes de exibir a tabela
colunas_tabela = ['Chave', 'Status', 'Resumo', 'Descrição', 'Análise x Documentação/Desenvolvimento/QA/Entrega', 'Responsável']
colunas_presentes = [col for col in colunas_tabela if col in jira_data.columns]

if len(colunas_presentes) < len(colunas_tabela):
    st.warning("Algumas colunas não estão presentes nos dados combinados: " + str([col for col in colunas_tabela if col not in colunas_presentes]))

# Tabela com filtro de Tipo de Item
st.write('## Tabela de Itens Filtrados')
df_tabela_filtrado = jira_data[jira_data['Tipo de item'] == tipo_selecionado_tabela]
st.dataframe(df_tabela_filtrado[colunas_presentes])

# Gráfico de Barras da Quantidade de Bugs e Melhorias por Mês
st.write('## Quantidade de Bugs e Melhorias sem Data Pré ou Data Produção (Gráfico de Barras)')

df_filtrado_sem_data = df_filtrado[(df_filtrado['Data Pré'].isnull()) & (df_filtrado['Data Produção'].isnull())]
quantidade_por_mes_sem_data = df_filtrado_sem_data.groupby(['Mês', 'Tipo de item']).size().reset_index(
    name='Quantidade')

fig_barras_sem_data = px.bar(quantidade_por_mes_sem_data, x='Mês', y='Quantidade', color='Tipo de item',
                             barmode='group',
                             title='Quantidade de Bugs e Melhorias sem Data Pré ou Data Produção por Mês',
                             color_discrete_map={'Melhoria': 'blue', 'Bug': 'red'})

st.plotly_chart(fig_barras_sem_data)

# Gráfico de Barras da Quantidade de Bugs e Melhorias com Data Pré ou Data Produção
st.write('## Quantidade de Bugs e Melhorias com Data Pré ou Data Produção (Gráfico de Barras)')

df_filtrado_data = df_filtrado[(df_filtrado['Data Pré'].notnull()) | (df_filtrado['Data Produção'].notnull())]
quantidade_por_mes_data = df_filtrado_data.groupby(['Mês', 'Tipo de item']).size().reset_index(name='Quantidade')

fig_barras_data = px.bar(quantidade_por_mes_data, x='Mês', y='Quantidade', color='Tipo de item',
                         barmode='group', title='Quantidade de Bugs e Melhorias com Data Pré ou Data Produção por Mês',
                         color_discrete_map={'Melhoria': 'blue', 'Bug': 'red'})
st.plotly_chart(fig_barras_data)

# Gráfico de Linha do Tempo de Versões
st.write('## Linha do Tempo de Versões')

# Filtrar as colunas necessárias do backlog
df_versoes = jira_data[['Versão', 'Criado', 'Data Pré']]
df_versoes = df_versoes.dropna(subset=['Versão', 'Criado', 'Data Pré'])

# Convertendo colunas para datetime
df_versoes['Criado'] = pd.to_datetime(df_versoes['Criado'], errors='coerce')
df_versoes['Data Pré'] = pd.to_datetime(df_versoes['Data Pré'], errors='coerce')

# Filtrar versões únicas
df_versoes = df_versoes.groupby('Versão').agg({'Criado': 'min', 'Data Pré': 'max'}).reset_index()

fig_versoes = px.timeline(df_versoes, x_start='Criado', x_end='Data Pré', y='Versão', title='Linha do Tempo das Versões')
st.plotly_chart(fig_versoes)
