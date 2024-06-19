import streamlit as st
from fpdf import FPDF

# Função para gerar um PDF simples
def create_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=content, ln=True, align='C')
    return pdf

# Exemplo de conteúdo do dashboard
st.title("Meu Dashboard")
content = st.text_area("Conteúdo do Relatório", "Este é o conteúdo do relatório.")

# Botão para gerar o PDF
if st.button("Gerar PDF"):
    pdf = create_pdf(content)
    pdf_output = pdf.output(dest='S').encode('latin1')
    st.download_button(label="Baixar PDF", data=pdf_output, file_name="relatorio.pdf", mime="application/pdf")
