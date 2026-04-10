import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# ================= CONFIG =================
st.set_page_config(
    page_title="Oraculus AI",
    page_icon="🔮",
    layout="wide"
)

# ================= CACHE =================
@st.cache_data
def carregar_dados(arquivo):
    dados = pd.read_csv(arquivo)
    dados.columns = dados.columns.str.lower()
    return dados

@st.cache_data
def processar_dados(dados):

    mapa_colunas = {
        "quantity": "vendas",
        "description": "produto",
        "unitprice": "preco",
        "invoicedate": "data",
        "date": "data"
    }

    dados = dados.rename(columns=mapa_colunas)
    # ================= VALIDAÇÃO DE COLUNAS =================

    colunas_obrigatorias = ["vendas", "produto"]

    faltando = [col for col in colunas_obrigatorias if col not in dados.columns]

    if faltando:
        return f"Faltando colunas obrigatórias: {', '.join(faltando)}"

    # 🔥 corrigir preço (string → float)
    if "preco" in dados.columns:
        dados["preco"] = (
            dados["preco"]
            .astype(str)
            .str.replace(",", ".", regex=False)
        )
        dados["preco"] = pd.to_numeric(dados["preco"], errors="coerce")
        dados = dados.dropna(subset=["preco"])
    if "vendas" not in dados.columns or "produto" not in dados.columns:
        return None

    dados["vendas"] = pd.to_numeric(dados["vendas"], errors="coerce")
    dados = dados.dropna(subset=["vendas"])
    dados = dados[dados["vendas"] > 0]

    if len(dados) > 100000:
        dados = dados.sample(100000)

    limite = dados["vendas"].quantile(0.99)
    dados = dados[dados["vendas"] <= limite]

    if "data" in dados.columns:
        dados["data"] = pd.to_datetime(dados["data"], errors="coerce")
        dados = dados.dropna(subset=["data"])
        vendas_tempo = dados.groupby("data")["vendas"].sum().sort_index()
    else:
        vendas_tempo = None

    vendas_produto = dados.groupby("produto")["vendas"].sum().sort_values(ascending=False)

    return dados, vendas_tempo, vendas_produto


# ================= UI =================
st.markdown("""
<style>
.big-title {font-size: 42px; font-weight: bold;}
.subtitle {font-size: 18px; color: #AAAAAA;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-title">🔮 ORACULUS AI</p>', unsafe_allow_html=True)

st.markdown("""
<p class="subtitle">
Descubra exatamente onde investir para ganhar mais dinheiro.
</p>
""", unsafe_allow_html=True)

st.info("""
🧠 Oraculus AI não mostra dados.

Ele te diz exatamente:

→ Onde investir  
→ Quanto investir  
→ O que fazer agora  

Como um consultor de negócios automático.
""")

# ================= UPLOAD =================
arquivo = st.file_uploader("Envie seu CSV de vendas")

if arquivo:

    dados_brutos = carregar_dados(arquivo)
    resultado = processar_dados(dados_brutos)

    if isinstance(resultado, str):
        st.error(resultado)
        st.info("Seu CSV precisa ter pelo menos: Quantity e Description")
        liberado = False

        query_params = st.query_params
        if query_params.get("liberado") == "1":
            liberado = True

        if not liberado:
            st.stop()

    dados, vendas_tempo, vendas_produto = resultado

    total_vendas = dados["vendas"].sum()
    top_produto = vendas_produto.index[0]
    valor_top = vendas_produto.iloc[0]
    participacao = (valor_top / vendas_produto.sum()) * 100

    # ================= KPI =================
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total vendido", f"{int(total_vendas):,}")
    col2.metric("🏆 Produto líder", top_produto)
    col3.metric("📊 Dominância", f"{participacao:.1f}%")


    # 👇 AQUI
    if vendas_tempo is not None:
        st.markdown("## 📈 Suas vendas ao longo do tempo")
        st.line_chart(vendas_tempo)

    # ================= BLOQUEIO =================

    # ================= BLOQUEIO CORRETO =================

    query_params = st.query_params
    liberado = query_params.get("liberado") == "1"

    if not liberado:
        st.error("🚫 Análise completa bloqueada")

        st.markdown("""
        ## 💰 Você está perdendo dinheiro e nem percebeu

        Libere a análise completa para ver:
        - Ranking inteligente
        - Previsões
        - Plano de ação
        """)

        st.link_button(
            "🔥 DESBLOQUEAR AGORA",
            "https://www.mercadopago.com.br/subscriptions/checkout?preapproval_plan_id=634f1224b6ec4839b9c735fdb556ffdd"
        )

        st.stop()

    # ================= CRESCIMENTO GERAL =================
    if vendas_tempo is not None and len(vendas_tempo) > 5:
        n = int(len(vendas_tempo) * 0.3)
        inicio = vendas_tempo.head(n).mean()
        fim = vendas_tempo.tail(n).mean()
        crescimento = ((fim - inicio) / inicio) * 100 if inicio > 0 else 0
    else:
        crescimento = 0

    
    # ================= SCORE INTELIGENTE =================

    vendas_total = dados.groupby("produto")["vendas"].sum()

    crescimento_produtos = {}

    for produto in vendas_total.index:

        d = dados[dados["produto"] == produto]
        crescimento_val = 0  # 🔥 define padrão
        crescimento_real = 0

        if "data" in d.columns and len(d) > 5:
            serie = d.groupby("data")["vendas"].sum().sort_index()
            # 🔮 PREVISÃO SIMPLES
            if len(serie) > 5:
                X = np.arange(len(serie)).reshape(-1, 1)
                y = serie.values

                model = LinearRegression()
                model.fit(X, y)

                previsao = model.predict([[len(serie) + 7]])[0]
            else:
                previsao = 0
            n = int(len(serie) * 0.3)
            inicio = serie.head(n).mean()
            fim = serie.tail(n).mean()

            if inicio > 5 and d["vendas"].sum() > 50:
                # Crescimento Real (para mostrar)
                crescimento_real = ((fim - inicio) / (inicio + 10)) * 100

                # 🔥 penalizar crescimento absurdo (instável)
                if crescimento_real > 80:
                    crescimento_real *= 0.6
                elif crescimento_real > 50:
                    crescimento_real *= 0.8

                # Crescimento Ajustado (para ranking)
                crescimento_val = np.log1p(max(crescimento_real, 0))

            # penalizar volume
            volume = d["vendas"].sum()
            if volume < 50:
                crescimento_val *= 0.3
            elif volume < 100:
                crescimento_val *= 0.5
            else:
                crescimento_val *= 1 

            crescimento_val = round(crescimento_val, 1)

        crescimento_produtos[produto] = crescimento_real

    crescimento_series = pd.Series(crescimento_produtos)

    q1 = crescimento_series.quantile(0.25)
    q2 = crescimento_series.quantile(0.50)
    q3 = crescimento_series.quantile(0.75)    


    # ================= FILTRO INTELIGENTE =================

    # remover produtos fracos
    vendas_min = vendas_total.quantile(0.25)
    validos = (crescimento_series > 0) & (vendas_total > vendas_min)

    # ================= SCORE PROFISSIONAL (CORRETO E LIMPO) =================

    crescimento_series = pd.Series(crescimento_produtos)

    vendas_min = vendas_total.quantile(0.25)
    validos = (crescimento_series > 0) & (vendas_total > vendas_min)

    if validos.sum() > 0:

        vendas_filtrado = vendas_total[validos]
        crescimento_filtrado = np.log1p(crescimento_series[validos].clip(lower=0))

        vendas_norm = vendas_filtrado / vendas_filtrado.max()

        if crescimento_filtrado.max() != crescimento_filtrado.min():
            crescimento_norm = (crescimento_filtrado - crescimento_filtrado.min()) / (
                crescimento_filtrado.max() - crescimento_filtrado.min()
            )
        else:
            crescimento_norm = crescimento_filtrado * 0

        score = (vendas_norm * 0.6) + (crescimento_norm * 0.4)

        ranking = score.sort_values(ascending=False)

    else:
        ranking = vendas_total.sort_values(ascending=False)

    top3 = ranking.head(3)
    melhor_produto = top3.index[0]
    st.markdown("## 🚀 Onde investir seu dinheiro AGORA")

    st.warning("💡 Com base nos seus dados, você pode estar investindo errado.")

    investimento_total = st.number_input(
        "Quanto você quer investir agora? (R$)",
        min_value=100.0,
        step=100.0
    )

    if investimento_total > 0:

        top_scores = score[top3.index]

        proporcao = top_scores / top_scores.sum()
        distribuicao = proporcao * investimento_total

        for produto in top3.index:

            valor = distribuicao[produto]
            crescimento_p = crescimento_series[produto]

            if crescimento_p > 30:
                acao = "🔥 Escalar forte"
            elif crescimento_p > 10:
                acao = "📈 Crescimento saudável"
            else:
                acao = "⚖️ Testar com cautela"

            st.success(f"""
            📦 {produto}

            💰 Investir: R$ {valor:,.2f}  
            📈 Crescimento: {crescimento_p:.1f}%

            👉 Estratégia: {acao}
            """)
    crescimento_melhor = crescimento_series[melhor_produto]

    st.info(f"""
    🔥 Melhor oportunidade agora: {melhor_produto}

    📈 Crescimento esperado: {crescimento_melhor:.1f}%

    👉 Esse é o produto com maior potencial baseado nos seus dados
    """)

    # ================= DIAGNÓSTICO =================
    
    st.markdown("## 🏆 Melhores oportunidades de investimento")

    for i, produto in enumerate(top3.index, start=1):
        
        crescimento_p = crescimento_series[produto]
        vendas_p = vendas_total[produto]

        # 🔥 1. ganho primeiro
        ganho_estimado = vendas_p * (crescimento_p / 100)

        # 🔥 2. preço
        preco_medio = dados[dados["produto"] == produto]["preco"].mean()

        # 🔥 3. faturamento (com proteção)
        if pd.isna(preco_medio) or preco_medio == 0:
            faturamento_formatado = "Indisponível"
        else:
            faturamento_estimado = ganho_estimado * preco_medio
            faturamento_formatado = f"R$ {faturamento_estimado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        # 🔥 4. score e confiança
        score_oportunidade = (crescimento_p * 0.6) + (vendas_p * 0.0001)
        confianca = min(100, crescimento_p * 2)

        d = dados[dados["produto"] == produto]

        if "data" in d.columns and len(d) > 5:
            serie = d.groupby("data")["vendas"].sum().sort_index()

            periodo_dias = (serie.index.max() - serie.index.min()).days

            if periodo_dias == 0:
                periodo_dias = 1            

            X = np.arange(len(serie)).reshape(-1, 1)
            y = serie.values

            model = LinearRegression()
            model.fit(X, y)

            previsao = model.predict([[len(serie) + 7]])[0]
        else:
            previsao = 0
            periodo_dias = 7
        
        

        st.success(f"""
        🥇 #{i} — {produto}

        📊 Vendas: {int(vendas_p):,}  
        📈 Crescimento: {crescimento_p:.1f}%  
        💰 Faturamento potencial: +{faturamento_formatado} em {periodo_dias} dias 
        
        🔮 Previsão (7 dias): {int(previsao)} unidades vendidas

        🔥 Score: {score_oportunidade:.1f}/100  
        🤖 Confiança: {confianca:.0f}%

        💡 Motivo:
        - {"Alta demanda" if vendas_p > vendas_total.median() else "Boa oportunidade"}
        - {"Crescimento acelerado" if crescimento_p > 20 else "Crescimento consistente"}
        """)

        if crescimento_p > 30:
            st.warning("🔥 Produto em alta — oportunidade imediata")

        elif crescimento_p < 0:
            st.error("⚠️ Produto em queda — risco de prejuízo")

    st.info(f"""
📈 Crescimento geral: {crescimento:.1f}%  
🏆 Produto líder: {top_produto}  
💰 Melhor oportunidade: {melhor_produto}

👉 DECISÃO:
Invista em **{melhor_produto}**
""")

    # ================= GRÁFICO =================
    if vendas_tempo is not None:
        st.markdown("## 📈 Evolução das vendas")
        st.line_chart(vendas_tempo)

    # ================= PRODUTOS =================
    st.markdown("## 📦 Produtos")
    st.bar_chart(vendas_produto.head(20))

    # ================= ASSISTENTE =================
    #st.divider()
    #st.subheader("🤖 Assistente ORACULUS")

    #col1, col2, col3, col4 = st.columns(4)

    #if col1.button("💰 Onde investir?"):
        #st.session_state.pergunta = "investir"

    #if col2.button("🏆 Produto líder"):
       #st.session_state.pergunta = "lider"

    #if col3.button("📈 Crescimento"):
        #st.session_state.pergunta = "crescimento"

    #if col4.button("🚀 Melhorar vendas"):
        #st.session_state.pergunta = "melhorar"

    #st.caption("💡 Clique nos botões para obter recomendações inteligentes")


    #pergunta = st.session_state.get("pergunta", "")
   

    #if pergunta:

        #if "invest" in pergunta:

            #st.success(f"""
        #💰 Melhor escolha: {top3.index[0]}

        #🏆 Top 3 investimentos:

        #1. {top3.index[0]} (crescimento: {crescimento_series[top3.index[0]]:.1f}%)
        #2. {top3.index[1]} (crescimento: {crescimento_series[top3.index[1]]:.1f}%)
        #3. {top3.index[2]} (crescimento: {crescimento_series[top3.index[2]]:.1f}%)

        #📊 Motivo:
        #- Alto volume + crescimento positivo
        #- Evita produtos em queda

        #🚀 Estratégia:
        #- Comece pelo primeiro
        #- Teste os outros
        #""")

        #elif "lider" in pergunta:

            #st.success(f"""
#🏆 Produto líder: {top_produto}

#📊 Dominância: {participacao:.1f}%
#""")

        #elif "cres" in pergunta:

            #st.success(f"""
            #📈 Análise de crescimento: {crescimento:.1f}%

            #📊 O que isso significa:

            #{"🚀 Forte crescimento — demanda acelerando" if crescimento > 10 else ""}
            #{"📈 Crescimento moderado — mercado saudável" if 3 < crescimento <= 10 else ""}
            #{"⚖️ Estável — sem tendência clara" if -3 <= crescimento <= 3 else ""}
            #{"📉 Queda — demanda enfraquecendo" if crescimento < -3 else ""}

            #💡 Implicação prática:

            #{"🔥 Momento ideal para escalar investimento" if crescimento > 5 else ""}
            #{"🧪 Testar campanhas antes de escalar" if 0 < crescimento <= 5 else ""}
            #{"⚠️ Revisar estratégia urgente" if crescimento <= 0 else ""}
            #""")

        #elif "melhor" in pergunta:
            #crescimento_prod = crescimento_series[top3.index[0]]

            # 🔥 CLASSIFICAÇÃO
            #if crescimento_prod > q3:
                #nivel = "🔥 Crescimento muito alto"
            #elif crescimento_prod > q2:
                #nivel = "🚀 Crescimento forte"
            #elif crescimento_prod > q1:
               # nivel = "📈 Crescimento saudável"
            #elif crescimento_prod > 0:
               # nivel = "⚖️ Crescimento leve"
            #else:
               # nivel = "📉 Queda"
            # 📦 REGRA DE ESTOQUE
           # if crescimento_prod <= 0:
              #  estoque_recomendado = "não aumentar estoque"
           # else:
                #estoque_base = min(max(crescimento_prod * 0.8, 10), 60)
               # estoque_recomendado = f"{int(estoque_base * 0.5)}% a {int(estoque_base)}%"    
            
           # st.success(f"""
           # 🚀 Plano para aumentar suas vendas

            #🎯 Produto foco: {top3.index[0]}

           # 📊 Por que esse produto:
           # - Alto volume de vendas
            #- Crescimento: {crescimento_prod:.1f}%
           # - Classificação: {nivel}

            #💡 Estratégia prática:

            #📦 Estoque:
            #- Aumentar estoque em {estoque_recomendado}

           # 📢 Tráfego:
            #- Aumentar investimento em anúncios proporcional ao crescimento

           # 💰 Conversão:
            #- Testar aumento de preço entre 5% e 10%
            #- Criar oferta com urgência (combo/desconto)

            #🚀 Insight:
            #Produto com tendência de crescimento — escalar com controle
            #""")

        #else:
            #st.warning("Pergunta não reconhecida")
