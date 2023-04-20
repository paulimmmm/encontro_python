# %%
from datetime import date
import requests

import pandas as pd
import streamlit as st

# st.markdown('## Calculadora de preço de multas vencidas.')
# %%
def check_password():
    '''Returns `True` if the user had the correct password.'''

    def password_entered():
        '''Checks whether a password entered by the user is correct.'''
        if st.session_state['password'] == st.secrets['password']:
            st.session_state['password_correct'] = True
            del st.session_state['password']  # don't store password
        else:
            st.session_state['password_correct'] = False

    if 'password_correct' not in st.session_state:
        # First run, show input for password.
        st.text_input(
            'Password', type='password', on_change=password_entered, key='password'
        )
        return False
    elif not st.session_state['password_correct']:
        # Password not correct, show input + error.
        st.text_input(
            'Password', type='password', on_change=password_entered, key='password'
        )
        st.error('😕 Password incorrect')
        return False
    else:
        # Password correct.
        return True


def create_selic_df():
    response = requests.get('https://api.bcb.gov.br/dados/serie/bcdata.sgs.4390/dados?formato=json').json()

    selic_df = pd.DataFrame.from_records(response)
    selic_df['data'] = pd.to_datetime(selic_df['data'], format='%d/%m/%Y')
    selic_df['valor'] = selic_df['valor'].astype('float') / 100

    return selic_df


def recalculate_fine_price(due_date, payment_dt, original_value):
    acc_selic = selic_df[(selic_df['data'] > pd.to_datetime(due_date)) &
                (selic_df['data'] < pd.to_datetime(payment_dt) - pd.offsets.MonthBegin(1))]['valor'].sum()

    return round(original_value*(acc_selic+1.01), 2)


def create_attendance_metrics(df, column, metric):
    return df.groupby(column).agg(metric).reset_index()


def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')
# %%
valores_multas_df = pd.read_csv('valores_multas.csv')
selic_df = create_selic_df()
# %%
if check_password():
    multa = st.selectbox(
        label='Selecione a multa',
        options=valores_multas_df['descricao'],
    )

    valor_tabelado_multa = list(valores_multas_df[valores_multas_df['descricao'] == multa]['valor'])[0]
    st.warning(f'O valor tabelado da multa é {valor_tabelado_multa}')

    data_vencimento_multa = st.date_input(
            label='Data de Vencimento da Multa',
            value=date(2023, 1, 1)
    )

    data_pagamento_multa = st.date_input(
            label='Data de Pagamento da Multa',
            value=date(2023, 4, 20)
    )

    preco_recalculado_multa = recalculate_fine_price(
        due_date=data_vencimento_multa,
        payment_dt=data_pagamento_multa,
        original_value=valor_tabelado_multa
    )

    if st.button(label='Recalcular valor'):
        st.code(f'O valor recalculado com juros é {preco_recalculado_multa}')

    uploaded_file = st.file_uploader(
        label='Insira uma planilha',
        help='#HELP',
        accept_multiple_files=False
    )

    if uploaded_file:
        attendace_df = pd.read_csv(uploaded_file)
        attendace_metrics_df = create_attendance_metrics(
            df=attendace_df,
            column='atendente',
            metric='sum'
        )
        attendance_metrics_csv = convert_df_to_csv(attendace_metrics_df)
        attendace_metrics_df_download_button = st.download_button(
            label='Download do Relatório dos Atendentes',
            data=attendance_metrics_csv,
            file_name='report_attendance.csv',
            mime='csv'
        )



    