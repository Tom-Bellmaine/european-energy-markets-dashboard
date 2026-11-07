import streamlit as st
st.title("Dashboard connection test")
st.stop()
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# PAGE SETTINGS
st.set_page_config(
    page_title="European Energy Markets Monitor",
    page_icon="📈",
    layout="wide"
)

DATA_DIR = Path("energy_dashboard_data")

# LOAD MARKET DATA
@st.cache_data
def load_data():
    brent = pd.read_csv(
        DATA_DIR / "brent_prices.csv",
        parse_dates=["Date"]
    )

    eu = pd.read_csv(
        DATA_DIR / "eu_fuel_prices.csv",
        parse_dates=["Date"]
    )

    countries = pd.read_csv(
        DATA_DIR / "country_fuel_prices.csv",
        parse_dates=["Date"]
    )

    return brent, eu, countries


st.title("European Energy Markets Monitor")

st.caption(
    "Brent crude oil and European downstream "
    "fuel-market analytics"
)

try:
    brent, eu, countries = load_data()
except (FileNotFoundError, ValueError) as error:
    st.warning(
        "The dashboard is ready, but the CSV "
        "datasets must be uploaded to GitHub."
    )
    st.code(str(error))
    st.stop()

# NAVIGATION
page = st.sidebar.radio(
    "Dashboard",
    [
        "Market Overview",
        "Brent Analytics",
        "European Fuel Markets",
        "Commercial Scenarios",
        "Data & Methodology"
    ]
)

if page == "Market Overview":

    st.header("Market Overview")

    latest_brent = brent.sort_values("Date").iloc[-1]
    latest_eu = eu.sort_values("Date").iloc[-1]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Brent Spot (USD/bbl)",
        f"${latest_brent['Brent']:,.2f}"
    )

    col2.metric(
        "EU Petrol Ex-Tax (EUR/1,000 L)",
        f"€{latest_eu['Petrol_EUR_1000L']:,.2f}"
    )

    col3.metric(
        "EU Diesel Ex-Tax (EUR/1,000 L)",
        f"€{latest_eu['Diesel_EUR_1000L']:,.2f}"
    )

    st.caption(
        f"Brent observation: "
        f"{latest_brent['Date']:%d %b %Y} | "
        f"EU fuel observation: "
        f"{latest_eu['Date']:%d %b %Y}"
    )

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=brent["Date"],
        y=brent["Brent"],
        mode="lines",
        name="Brent Spot"
    ))

    fig.update_layout(
        title="Historical Brent Crude Prices",
        xaxis_title="Date",
        yaxis_title="USD per barrel",
        template="plotly_white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

elif page == "Brent Analytics":

    st.header("Brent Crude Analytics")

    period = st.selectbox(
        "Historical period",
        ["1 Year", "3 Years", "5 Years", "10 Years"]
    )

    years = {
        "1 Year": 1,
        "3 Years": 3,
        "5 Years": 5,
        "10 Years": 10
    }[period]

    data = brent[
        brent["Date"] >= (
            brent["Date"].max()
            - pd.DateOffset(years=years)
        )
    ].copy()

    data["MA20"] = data["Brent"].rolling(20).mean()
    data["MA50"] = data["Brent"].rolling(50).mean()

    fig = go.Figure()

    for column, label in [
        ("Brent", "Brent Spot"),
        ("MA20", "20-Day Moving Average"),
        ("MA50", "50-Day Moving Average")
    ]:
        fig.add_trace(go.Scatter(
            x=data["Date"],
            y=data[column],
            name=label
        ))

    fig.update_layout(
        title="Brent Price Trends",
        yaxis_title="USD/bbl",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    returns = data["Brent"].pct_change()

    volatility = returns.std() * (252 ** 0.5) * 100

    st.metric(
        "Annualised Historical Volatility",
        f"{volatility:.1f}%"
    )

elif page == "European Fuel Markets":

    st.header("Northwest European Fuel Markets")

    fuel = st.selectbox(
        "Fuel product",
        ["Diesel", "Petrol"]
    )

    selected = st.multiselect(
        "Countries",
        ["Germany", "France", "Netherlands", "Belgium"],
        default=[
            "Germany",
            "France",
            "Netherlands",
            "Belgium"
        ]
    )

    period = st.selectbox(
        "Historical period",
        ["1 Year", "3 Years", "5 Years", "All Data"],
        index=1
    )

    data = countries.copy()

    if period != "All Data":
        years = int(period.split()[0])
        data = data[
            data["Date"] >= (
                data["Date"].max()
                - pd.DateOffset(years=years)
            )
        ]

    fig = go.Figure()

    for country in selected:
        subset = data[
            data["Country"] == country
        ].sort_values("Date")

        fig.add_trace(go.Scatter(
            x=subset["Date"],
            y=subset[fuel],
            name=country
        ))

    fig.update_layout(
        title=f"European {fuel} Price Comparison",
        xaxis_title="Date",
        yaxis_title="EUR per 1,000 litres",
        hovermode="x unified",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "Prices are consumer-market observations "
        "excluding taxes, not wholesale ARA "
        "product assessments."
    )

elif page == "Commercial Scenarios":

    st.header("Crude Purchase Cost Sensitivity")

    st.write(
        "Estimate the gross cost of purchasing "
        "a specified volume of crude oil."
    )

    crude_price = st.number_input(
        "Crude price (USD/bbl)",
        min_value=0.0,
        value=80.0,
        step=1.0
    )

    volume = st.number_input(
        "Crude volume (barrels)",
        min_value=1,
        value=100000,
        step=10000
    )

    price_change = st.slider(
        "Price movement (USD/bbl)",
        min_value=-30,
        max_value=30,
        value=5
    )

    base_cost = crude_price * volume

    revised_cost = (
        crude_price + price_change
    ) * volume

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Base Purchase Cost",
        f"${base_cost:,.0f}"
    )

    col2.metric(
        "Scenario Purchase Cost",
        f"${revised_cost:,.0f}"
    )

    col3.metric(
        "Cost Difference",
        f"${revised_cost - base_cost:+,.0f}"
    )

    st.caption(
        "Illustrative scenario only. Excludes "
        "freight, quality adjustments, hedging, "
        "financing and other commercial costs."
    )

elif page == "Data & Methodology":

    st.header("Data Sources & Methodology")

    st.markdown(
        """
        **Brent crude:** EIA/FRED daily Brent spot
        prices, expressed in USD per barrel.

        **European fuels:** European Commission
        Oil Bulletin petrol and diesel consumer
        prices excluding taxes, expressed in
        EUR per 1,000 litres.

        **Geographic scope:** Germany, France,
        Netherlands and Belgium.

        **Volatility:** Standard deviation of
        daily percentage returns, annualised
        using 252 trading days.

        **Important limitation:** National
        consumer fuel prices are not equivalent
        to wholesale ARA gasoline or diesel
        prices and cannot directly be used to
        calculate refinery crack spreads.
        """
    )

    st.subheader("Dataset Coverage")

    st.write(
        "Brent:",
        brent["Date"].min().date(),
        "to",
        brent["Date"].max().date()
    )

    st.write(
        "European fuels:",
        eu["Date"].min().date(),
        "to",
        eu["Date"].max().date()
    )

    st.write(
        "Country observations:",
        len(countries)
    )
