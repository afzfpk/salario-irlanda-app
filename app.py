import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página otimizada para telemóvel e desktop
st.set_page_config(
    page_title="Salário & Gastos Irlanda by AFZF",
    page_icon="💶",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização CSS refinada (design moderno executivo)
st.markdown("""
<style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
        max-width: 650px;
    }
    
    .metric-card-highlight {
        background-color: #0f172a;
        color: white;
        padding: 1.25rem;
        border-radius: 14px;
        text-align: center;
        border: 1px solid #1e293b;
        margin: 1rem 0;
    }
    .metric-card-highlight .label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    .metric-card-highlight .value {
        font-size: 2.2rem;
        font-weight: 800;
        font-family: monospace;
        margin: 0;
        color: #ffffff;
    }
    .metric-card-highlight .sub {
        font-size: 0.8rem;
        color: #cbd5e1;
        margin-top: 0.35rem;
    }

    div.stButton > button:first-child {
        width: 100%;
        border-radius: 10px;
        height: 2.7rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. FUNÇÕES FISCAIS OFICIAIS IRLANDA 2026 (REVENUE.IE)
# -------------------------------------------------------------
def calcular_impostos_irlanda_2026(bruto_anual: float, tem_rent_credit: bool = False):
    bruto = max(0.0, float(bruto_anual))
    
    # 1. PAYE (Standard Rate Cut-Off: €44.000 para solteiro)
    limite_paye = 44000.0
    if bruto <= limite_paye:
        paye_bruto = bruto * 0.20
    else:
        paye_bruto = (limite_paye * 0.20) + ((bruto - limite_paye) * 0.40)
        
    # Créditos Fiscais: €4.000 base (€2.000 pessoal + €2.000 empregado) + €1.000 Rent Credit
    tax_credits = 4000.0 + (1000.0 if tem_rent_credit else 0.0)
    paye_liquido = max(0.0, paye_bruto - tax_credits)
    
    # 2. USC (Universal Social Charge - taxas 2026)
    usc = 0.0
    faixa1, faixa2, faixa3 = 12012.0, 28700.0, 70044.0
    
    if bruto > 0:
        if bruto <= faixa1:
            usc += bruto * 0.005
        else:
            usc += faixa1 * 0.005
            if bruto <= faixa2:
                usc += (bruto - faixa1) * 0.02
            else:
                usc += (faixa2 - faixa1) * 0.02
                if bruto <= faixa3:
                    usc += (bruto - faixa2) * 0.03
                else:
                    usc += (faixa3 - faixa2) * 0.03
                    usc += (bruto - faixa3) * 0.08

    # 3. PRSI (4.35% para 2026)
    prsi = bruto * 0.0435

    total_deducoes_anual = paye_liquido + usc + prsi
    salario_liquido_anual = max(0.0, bruto - total_deducoes_anual)
    
    return {
        "bruto_anual": bruto,
        "bruto_mensal": bruto / 12,
        "bruto_semanal": bruto / 52,
        "paye_bruto_anual": paye_bruto,
        "tax_credits_anual": tax_credits,
        "paye_anual": paye_liquido,
        "paye_mensal": paye_liquido / 12,
        "paye_semanal": paye_liquido / 52,
        "usc_anual": usc,
        "usc_mensal": usc / 12,
        "usc_semanal": usc / 52,
        "prsi_anual": prsi,
        "prsi_mensal": prsi / 12,
        "prsi_semanal": prsi / 52,
        "deducoes_mensal": total_deducoes_anual / 12,
        "deducoes_semanal": total_deducoes_anual / 52,
        "liquido_anual": salario_liquido_anual,
        "liquido_mensal": salario_liquido_anual / 12,
        "liquido_semanal": salario_liquido_anual / 52,
    }

def calcular_liquido_semanal_pelo_bruto(bruto_semanal: float, tem_rent_credit: bool = False):
    anual = bruto_semanal * 52
    calc = calcular_impostos_irlanda_2026(anual, tem_rent_credit)
    return calc["liquido_semanal"]

# -------------------------------------------------------------
# 2. INICIALIZAÇÃO DO ESTADO (st.session_state)
# -------------------------------------------------------------
if "salario_bruto_anual" not in st.session_state:
    st.session_state.salario_bruto_anual = 48000.0

if "tem_rent_credit" not in st.session_state:
    st.session_state.tem_rent_credit = False

if "pagamentos_semanais" not in st.session_state:
    st.session_state.pagamentos_semanais = [
        {"descricao": "Semana 1 - Pagamento", "valor_bruto": 923.08, "valor_liquido": 760.00, "data": "2026-09-05"},
        {"descricao": "Semana 2 - Pagamento", "valor_bruto": 923.08, "valor_liquido": 760.00, "data": "2026-09-12"}
    ]

if "gastos" not in st.session_state:
    st.session_state.gastos = [
        {"descricao": "Quarto / Renda em Dublin", "valor": 950.0, "categoria": "Renda", "data": "2026-09-01"},
        {"descricao": "Supermercado (Tesco / Lidl)", "valor": 280.0, "categoria": "Supermercado", "data": "2026-09-05"},
        {"descricao": "Passe Leap Card (Transportes)", "valor": 80.0, "categoria": "Transportes", "data": "2026-09-02"},
        {"descricao": "Jantar & Pub com amigos", "valor": 95.0, "categoria": "Lazer", "data": "2026-09-12"},
    ]

# -------------------------------------------------------------
# 3. INTERFACE PRINCIPAL
# -------------------------------------------------------------
st.title("💶 Salário & Gastos Irlanda 2026")
st.caption("Controlo de pagamentos semanais, deduções e poupança pessoal")

aba1, aba2 = st.tabs(["Salário & Deduções", "Gastos & Poupança"])

with aba1:
    st.subheader("Simulador Salarial (2026)")
    
    st.session_state.tem_rent_credit = st.checkbox(
        "🏠 Arrendo quarto ou casa na Irlanda (Rent Tax Credit: +€1.000/ano no teu bolso)",
        value=st.session_state.tem_rent_credit
    )
    if st.session_state.tem_rent_credit:
        st.caption("✅ Crédito fiscal ativado: +€83,33/mês (+€19,23/semana) a mais no teu salário líquido.")

    tipo_insercao = st.radio(
        "Como preferes definir o salário base?",
        ["Semanal (€/semana)", "Mensal (€/mês)", "Anual (€/ano)"],
        horizontal=True
    )

    if tipo_insercao == "Semanal (€/semana)":
        val_inicial = float(st.session_state.salario_bruto_anual / 52)
        sem_input = st.number_input("Salário Bruto Semanal (€)", min_value=0.0, value=val_inicial, step=25.0, format="%.2f")
        st.session_state.salario_bruto_anual = sem_input * 52
    elif tipo_insercao == "Mensal (€/mês)":
        val_inicial = float(st.session_state.salario_bruto_anual / 12)
        mes_input = st.number_input("Salário Bruto Mensal (€)", min_value=0.0, value=val_inicial, step=100.0, format="%.2f")
        st.session_state.salario_bruto_anual = mes_input * 12
    else:
        val_inicial = float(st.session_state.salario_bruto_anual)
        ano_input = st.number_input("Salário Bruto Anual (€)", min_value=0.0, value=val_inicial, step=1000.0, format="%.2f")
        st.session_state.salario_bruto_anual = ano_input

    with st.expander("⏱️ Calculadora de Horas & Turnos (Hourly & Overtime)"):
        col_h1, col_h2 = st.columns(2)
        taxa_h = col_h1.number_input("Taxa por hora (€/h)", min_value=5.0, value=14.50, step=0.50)
        horas_norm = col_h2.number_input("Horas normais", min_value=0.0, value=39.0, step=1.0)
        
        col_h3, col_h4 = st.columns(2)
        horas_ot = col_h3.number_input("Horas extra (Overtime 1.5x)", min_value=0.0, value=0.0, step=1.0)
        horas_dom = col_h4.number_input("Horas Domingo (1.3x)", min_value=0.0, value=0.0, step=1.0)
        
        total_horas_semanal = (taxa_h * horas_norm) + (taxa_h * 1.5 * horas_ot) + (taxa_h * 1.3 * horas_dom)
        st.info(f"Total bruto estimado por horas: **€{total_horas_semanal:,.2f} / semana**")
        
        if st.button("Aplicar valor de horas como Salário Semanal Base", key="btn_apply_hours"):
            st.session_state.salario_bruto_anual = total_horas_semanal * 52
            st.rerun()

    calc = calcular_impostos_irlanda_2026(st.session_state.salario_bruto_anual, st.session_state.tem_rent_credit)

    vis_freq = st.radio("Frequência de visualização:", ["Por Semana", "Por Mês"], horizontal=True)
    if vis_freq == "Por Semana":
        st.markdown(f"""
        <div class="metric-card-highlight">
            <div class="label">Salário Líquido Semanal Real</div>
            <div class="value">€{calc['liquido_semanal']:,.2f}</div>
            <div class="sub">Equivalente mensal: <strong>€{calc['liquido_mensal']:,.2f}</strong></div>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Bruto / Semana", f"€{calc['bruto_semanal']:,.2f}")
        c2.metric("Deduções / Sem.", f"-€{calc['deducoes_semanal']:,.2f}")
        taxa = (calc['deducoes_semanal'] / calc['bruto_semanal'] * 100) if calc['bruto_semanal'] > 0 else 0
        c3.metric("Taxa Efetiva", f"{taxa:.1f}%")
    else:
        st.markdown(f"""
        <div class="metric-card-highlight">
            <div class="label">Salário Líquido Mensal Real</div>
            <div class="value">€{calc['liquido_mensal']:,.2f}</div>
            <div class="sub">Total líquido anual: <strong>€{calc['liquido_anual']:,.2f}</strong></div>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Bruto / Mês", f"€{calc['bruto_mensal']:,.2f}")
        c2.metric("Deduções / Mês", f"-€{calc['deducoes_mensal']:,.2f}")
        taxa = (calc['deducoes_mensal'] / calc['bruto_mensal'] * 100) if calc['bruto_mensal'] > 0 else 0
        c3.metric("Taxa Efetiva", f"{taxa:.1f}%")

    st.write("---")

    st.markdown("### 📥 Registar Pagamentos Semanais")
    with st.form("form_pagamento_semanal", clear_on_submit=True):
        nome_sem = st.text_input("Identificação da semana", value=f"Semana {len(st.session_state.pagamentos_semanais) + 1}")
        col_v, col_d = st.columns([1, 1])
        with col_v:
            valor_ganho = st.number_input("Valor ganho esta semana (€)", min_value=0.01, step=20.0, format="%.2f")
        with col_d:
            data_pag = st.date_input("Data do Pagamento", value=datetime.today())
        
        eh_liquido = st.checkbox("Já é o valor líquido recebido na conta bancária?", value=False)
        btn_salvar_sem = st.form_submit_button("Guardar Ganho Semanal", use_container_width=True)
        
        if btn_salvar_sem:
            if eh_liquido:
                net_val = float(valor_ganho)
                gross_val = net_val * 1.25
            else:
                gross_val = float(valor_ganho)
                net_val = calcular_liquido_semanal_pelo_bruto(gross_val, st.session_state.tem_rent_credit)
            
            st.session_state.pagamentos_semanais.append({
                "descricao": nome_sem.strip(),
                "valor_bruto": gross_val,
                "valor_liquido": net_val,
                "data": data_pag.strftime('%Y-%m-%d')
            })
            st.success(f"Ganhos da '{nome_sem}' registados! Líquido: €{net_val:.2f}")
            st.rerun()

    if len(st.session_state.pagamentos_semanais) > 0:
        total_liq_semanas = sum(s["valor_liquido"] for s in st.session_state.pagamentos_semanais)
        media_sem = total_liq_semanas / len(st.session_state.pagamentos_semanais)

        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Total Líquido Acumulado", f"€{total_liq_semanas:,.2f}", f"{len(st.session_state.pagamentos_semanais)} semanas")
        col_m2.metric("Média por Semana", f"€{media_sem:,.2f}")

        df_sem = pd.DataFrame(st.session_state.pagamentos_semanais)
        df_sem_mostrar = df_sem.copy()
        df_sem_mostrar["Bruto (€)"] = df_sem_mostrar["valor_bruto"].apply(lambda x: f"€{x:,.2f}")
        df_sem_mostrar["Líquido Recebido (€)"] = df_sem_mostrar["valor_liquido"].apply(lambda x: f"€{x:,.2f}")
        st.dataframe(
            df_sem_mostrar[["descricao", "data", "Bruto (€)", "Líquido Recebido (€)"]].rename(columns={
                "descricao": "Semana", "data": "Data"
            }),
            use_container_width=True,
            hide_index=True
        )

        if st.button("Limpar Histórico de Semanas", type="secondary"):
            st.session_state.pagamentos_semanais = []
            st.rerun()

with aba2:
    calc = calcular_impostos_irlanda_2026(st.session_state.salario_bruto_anual, st.session_state.tem_rent_credit)
    total_liq_semanas = sum(s["valor_liquido"] for s in st.session_state.pagamentos_semanais)
    tem_semanas = len(st.session_state.pagamentos_semanais) > 0

    st.subheader("Controlo de Gastos & Poupança")

    if tem_semanas:
        base_escolhida = st.radio(
            "Base de rendimento para a poupança:",
            [f"Total das Semanas Registadas (€{total_liq_semanas:,.2f})", f"Salário Mensal Estimado (€{calc['liquido_mensal']:,.2f})"],
            horizontal=True
        )
        if "Semanas" in base_escolhida:
            salario_base = total_liq_semanas
        else:
            salario_base = calc["liquido_mensal"]
    else:
        salario_base = calc["liquido_mensal"]

    total_gasto = sum(item["valor"] for item in st.session_state.gastos)
    saldo_poupanca = salario_base - total_gasto

    if total_gasto > 0:
        st.markdown("#### 📊 Distribuição por Categoria")
        df_gastos = pd.DataFrame(st.session_state.gastos)
        cat_group = df_gastos.groupby("categoria")["valor"].sum().reset_index()
        cat_group["% do Gasto"] = (cat_group["valor"] / total_gasto * 100).round(1)
        cat_group["Valor (€)"] = cat_group["valor"].apply(lambda x: f"€{x:,.2f}")
        
        st.dataframe(cat_group[["categoria", "Valor (€)", "% do Gasto"]].rename(columns={"categoria": "Categoria"}), use_container_width=True, hide_index=True)

        renda_val = df_gastos[df_gastos["categoria"] == "Renda"]["valor"].sum()
        if renda_val > 0 and salario_base > 0:
            pct_renda = (renda_val / salario_base) * 100
            if pct_renda > 40:
                st.warning(f"⚠️ A renda consome **{pct_renda:.1f}%** do teu rendimento (€{renda_val:,.2f}). O ideal recomendado na Irlanda é abaixo de 35-40%.")

    cor_saldo = "#16a34a" if saldo_poupanca >= 0 else "#dc2626"
    st.markdown(f"""
    <div style="background-color: #f8fafc; border-radius: 12px; padding: 1.1rem; margin-bottom: 1rem; border: 1px solid #e2e8f0; border-left: 6px solid {cor_saldo};">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
            <span style="color: #64748b; font-size: 0.85rem;">Rendimento Base:</span>
            <strong style="color: #0f172a;">€{salario_base:,.2f}</strong>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.6rem;">
            <span style="color: #64748b; font-size: 0.85rem;">Total Gasto:</span>
            <strong style="color: #dc2626;">-€{total_gasto:,.2f}</strong>
        </div>
        <div style="height: 1px; background-color: #e2e8f0; margin: 0.5rem 0;"></div>
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <strong style="color: #0f172a; font-size: 0.95rem;">Saldo / Poupança:</strong>
            <span style="font-size: 1.4rem; font-weight: 800; font-family: monospace; color: {cor_saldo};">€{saldo_poupanca:,.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("form_novo_gasto", clear_on_submit=True):
        st.markdown("**Adicionar Nova Despesa**")
        desc = st.text_input("Descrição", placeholder="Ex: Renda quarto Dublin, Tesco, Leap Card...")
        col_v, col_c = st.columns([1, 1])
        with col_v:
            val = st.number_input("Valor (€)", min_value=0.01, step=5.0, format="%.2f")
        with col_c:
            cat = st.selectbox("Categoria", ["Renda", "Supermercado", "Transportes", "Lazer", "Outros"])
        
        if st.form_submit_button("Adicionar Gasto", use_container_width=True):
            if not desc.strip():
                st.warning("Por favor, introduz uma descrição para o gasto.")
            else:
                st.session_state.gastos.append({
                    "descricao": desc.strip(),
                    "valor": float(val),
                    "categoria": cat,
                    "data": datetime.today().strftime('%Y-%m-%d')
                })
                st.success(f"Gasto '{desc}' (€{val:.2f}) adicionado!")
                st.rerun()

    st.markdown("#### Lista de Gastos Registados")
    if len(st.session_state.gastos) == 0:
        st.info("Ainda não tens nenhum gasto registado.")
    else:
        df_mostrar = pd.DataFrame(st.session_state.gastos)
        df_mostrar["Valor (€)"] = df_mostrar["valor"].apply(lambda x: f"€{x:,.2f}")
        st.dataframe(
            df_mostrar[["descricao", "categoria", "Valor (€)", "data"]].rename(columns={
                "descricao": "Descrição", "categoria": "Categoria", "data": "Data"
            }),
            use_container_width=True,
            hide_index=True
        )

        csv_data = pd.DataFrame(st.session_state.gastos).to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descarregar Extrato de Gastos (CSV)",
            data=csv_data,
            file_name="gastos_irlanda_2026.csv",
            mime="text/csv",
        )

        if st.button("Limpar Todos os Gastos", type="secondary"):
            st.session_state.gastos = []
            st.rerun()

st.caption("Segurança & Privacidade: Dados guardados localmente na sessão.")
