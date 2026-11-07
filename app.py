
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
@st.cache_data
def load_eia_inventories():
    data = pd.read_csv(
        DATA_DIR / "eia_inventories.csv",
        parse_dates=["Date"]
    )
    return data.sort_values("Date").reset_index(drop=True)
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
        "Refining Crack Spreads",
        "Brent Futures Market Structure",
        "Oil Market Fundamentals",
        "European Fuel Markets",
        "Price Forecasting",
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



    
    # BRENT-WTI CRUDE SPREAD ANALYSIS
    st.divider()
    st.subheader("Brent–WTI Crude Oil Spread Analysis")

    st.caption(
        "Historical spot price differential between "
        "Brent and WTI crude oil, in USD per barrel."
    )

    spread_data = pd.read_csv(
        DATA_DIR / "brent_wti_spread.csv",
        parse_dates=["Date"]
    )

    spread_data = spread_data.dropna(
        subset=["Date", "Brent", "WTI", "Brent_WTI_Spread"]
    ).sort_values("Date")

    spread_period = st.selectbox(
        "Spread analysis period",
        ["1 Year", "3 Years", "5 Years", "10 Years"],
        index=2,
        key="brent_wti_period"
    )

    spread_years = int(spread_period.split()[0])

    spread_data = spread_data[
        spread_data["Date"] >= (
            spread_data["Date"].max()
            - pd.DateOffset(years=spread_years)
        )
    ].copy()

    if spread_data.empty:
        st.warning("No Brent–WTI observations available.")

    else:
        spread_data["Spread_MA90"] = (
            spread_data["Brent_WTI_Spread"]
            .rolling(90)
            .mean()
        )

        latest_spread = spread_data["Brent_WTI_Spread"].iloc[-1]
        average_spread = spread_data["Brent_WTI_Spread"].mean()

        recent_date = (
            spread_data["Date"].max()
            - pd.Timedelta(days=28)
        )

        older_data = spread_data[
            spread_data["Date"] <= recent_date
        ]

        four_week_change = (
            latest_spread
            - older_data["Brent_WTI_Spread"].iloc[-1]
            if not older_data.empty
            else float("nan")
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Latest Brent–WTI Spread",
            f"${latest_spread:,.2f}/bbl"
        )

        col2.metric(
            "Period Average Spread",
            f"${average_spread:,.2f}/bbl"
        )

        col3.metric(
            "Approx. 4-Week Change",
            f"{four_week_change:+.2f} USD/bbl"
        )

        fig_spread = go.Figure()

        fig_spread.add_trace(go.Scatter(
            x=spread_data["Date"],
            y=spread_data["Brent_WTI_Spread"],
            mode="lines",
            name="Brent–WTI Spread"
        ))

        fig_spread.add_trace(go.Scatter(
            x=spread_data["Date"],
            y=spread_data["Spread_MA90"],
            mode="lines",
            name="90-Observation Moving Average"
        ))

        fig_spread.add_hline(
            y=0,
            line_dash="dash",
            line_color="gray"
        )

        fig_spread.update_layout(
            title="Historical Brent–WTI Crude Spread",
            xaxis_title="Date",
            yaxis_title="USD per barrel",
            template="plotly_white",
            hovermode="x unified"
        )

        st.plotly_chart(
            fig_spread,
            width="stretch"
        )

        st.caption(
            f"Latest observation: "
            f"{spread_data['Date'].max():%d %b %Y}. "
            "Positive values indicate Brent trading "
            "above WTI. These are spot benchmarks, "
            "not futures calendar spreads."
        )








        # AUTOMATED CRUDE MARKET INSIGHTS
        st.divider()
        st.subheader("Crude Market Insights")

        difference_from_average = (
            latest_spread - average_spread
        )

        if difference_from_average > 0:
            relative_position = "above"
        elif difference_from_average < 0:
            relative_position = "below"
        else:
            relative_position = "equal to"

        if pd.isna(four_week_change):
            spread_direction = "Insufficient history"
        elif four_week_change > 0:
            spread_direction = "Widening"
        elif four_week_change < 0:
            spread_direction = "Narrowing"
        else:
            spread_direction = "Unchanged"

        col1, col2 = st.columns(2)

        col1.metric(
            "Spread vs Period Average",
            f"{difference_from_average:+.2f} USD/bbl"
        )

        col2.metric(
            "Four-Week Spread Direction",
            spread_direction
        )

        st.info(
            f"The Brent–WTI spread is currently "
            f"${latest_spread:.2f}/bbl, "
            f"{abs(difference_from_average):.2f} USD/bbl "
            f"{relative_position} its {spread_period.lower()} "
            f"average of ${average_spread:.2f}/bbl. "
            f"Over approximately four weeks, the "
            f"spread has changed by "
            f"{four_week_change:+.2f} USD/bbl."
        )

        st.caption(
            "Automated descriptive analysis based on "
            "historical spot prices. Spread movements "
            "alone do not establish their causes or "
            "constitute trading recommendations."
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



    
    # DIESEL PRICE DIFFERENTIAL ANALYSIS
    st.divider()
    st.subheader("European Diesel Price Differentials")

    st.caption(
        "Compare national diesel prices excluding taxes. "
        "These are not wholesale trading spreads."
    )

    country_a = st.selectbox(
        "First country",
        ["Netherlands", "Germany", "France", "Belgium"],
        key="country_a"
    )

    country_b = st.selectbox(
        "Second country",
        ["Germany", "France", "Belgium", "Netherlands"],
        key="country_b"
    )

    diesel_data = countries[
        countries["Country"].isin([country_a, country_b])
    ][["Date", "Country", "Diesel"]].copy()

    if country_a == country_b:
        st.warning("Please select two different countries.")

    else:
        diesel_data = diesel_data.pivot_table(
            index="Date",
            columns="Country",
            values="Diesel",
            aggfunc="mean"
        ).sort_index()

        if not all(
            c in diesel_data.columns
            for c in [country_a, country_b]
        ):
            st.warning("Insufficient data for this comparison.")

        else:
            diesel_data = diesel_data[
                [country_a, country_b]
            ].dropna()

            if diesel_data.empty:
                st.warning("No overlapping price observations.")

            else:
                diesel_data["Differential"] = (
                    diesel_data[country_a]
                    - diesel_data[country_b]
                )

                latest = diesel_data["Differential"].iloc[-1]
                average = diesel_data["Differential"].mean()

                col1, col2 = st.columns(2)

                col1.metric(
                    "Latest differential",
                    f"€{latest:,.2f} / 1,000 L"
                )

                col2.metric(
                    "Historical average differential",
                    f"€{average:,.2f} / 1,000 L"
                )

                fig_diff = go.Figure()

                fig_diff.add_trace(go.Scatter(
                    x=diesel_data.index,
                    y=diesel_data["Differential"],
                    mode="lines",
                    name=f"{country_a} minus {country_b}"
                ))

                fig_diff.add_hline(
                    y=0,
                    line_dash="dash",
                    line_color="gray"
                )

                fig_diff.update_layout(
                    title=f"Diesel Differential: {country_a} vs {country_b}",
                    xaxis_title="Date",
                    yaxis_title="EUR per 1,000 litres",
                    template="plotly_white"
                )

                st.plotly_chart(
                    fig_diff,
                    width="stretch"
                )

                st.caption(
                    "A positive differential means diesel is "
                    f"more expensive in {country_a} than {country_b}. "
                    "This is not an executable arbitrage margin."
                )
elif page == "Oil Market Fundamentals":

    st.header("US Oil Market Fundamentals")
    st.caption(
        "EIA weekly commercial crude oil, gasoline and "
        "distillate inventories. Stock levels and weekly "
        "changes are expressed in million barrels."
    )

    inventories = load_eia_inventories()

    product_options = {
        "Crude Oil": "Crude_Stocks",
        "Gasoline": "Gasoline_Stocks",
        "Distillates": "Distillate_Stocks"
    }

    product = st.selectbox(
        "Select petroleum product",
        list(product_options.keys())
    )

    period = st.selectbox(
        "Historical period",
        ["1 Year", "3 Years", "5 Years", "10 Years", "All Data"],
        index=1
    )

    column = product_options[product]
    latest = inventories.iloc[-1]

    stock_level = latest[column]
    weekly_change = latest[column + "_Change"]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Latest Inventory",
        f"{stock_level:,.2f} million bbl"
    )

    col2.metric(
        "Weekly Stock Change",
        f"{weekly_change:+,.3f} million bbl"
    )

    col3.metric(
        "Market Movement",
        "Build" if weekly_change > 0
        else "Draw" if weekly_change < 0
        else "Unchanged"
    )

    st.caption(
        f"Latest EIA observation: "
        f"{latest['Date']:%d %B %Y}"
    )

    data = inventories.copy()

    if period != "All Data":
        years = int(period.split()[0])
        cutoff = data["Date"].max() - pd.DateOffset(
            years=years
        )
        data = data[data["Date"] >= cutoff]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data[column],
        mode="lines",
        name=f"{product} Inventories"
    ))

    fig.update_layout(
        title=f"US {product} Inventory History",
        xaxis_title="Date",
        yaxis_title="Million barrels",
        template="plotly_white",
        hovermode="x unified"
    )

    st.plotly_chart(fig, width="stretch")

    st.subheader("Weekly Inventory Builds and Draws")

    fig_change = go.Figure()

    fig_change.add_trace(go.Bar(
        x=data["Date"],
        y=data[column + "_Change"],
        name="Weekly Change"
    ))

    fig_change.add_hline(y=0, line_dash="dash")

    fig_change.update_layout(
        title=f"Weekly {product} Stock Changes",
        xaxis_title="Date",
        yaxis_title="Million barrels",
        template="plotly_white"
    )

    st.plotly_chart(fig_change, width="stretch")

    st.subheader("Inventory Market Insights")

    if weekly_change > 0:
        interpretation = (
            f"US {product.lower()} inventories increased "
            f"by {weekly_change:.3f} million barrels "
            f"in the latest reporting week."
        )
    elif weekly_change < 0:
        interpretation = (
            f"US {product.lower()} inventories decreased "
            f"by {abs(weekly_change):.3f} million barrels "
            f"in the latest reporting week."
        )
    else:
        interpretation = (
            f"US {product.lower()} inventories were "
            f"unchanged in the latest reporting week."
        )

    st.info(interpretation)

    st.caption(
        "Source: US Energy Information Administration "
        "(EIA), Weekly Petroleum Status Report. "
        "Inventory changes alone do not establish "
        "the cause of a market move or predict prices."
    )




    # =====================================================
    # FIVE-YEAR INVENTORY SEASONAL COMPARISON
    # =====================================================

    st.divider()
    st.subheader("Inventories vs Five-Year Seasonal Average")

    seasonal_file = DATA_DIR / "eia_inventory_seasonality.csv"

    if seasonal_file.exists():

        seasonal = pd.read_csv(
            seasonal_file,
            parse_dates=["Date"]
        )

        product_choice = st.selectbox(
            "Select inventory product",
            ["Crude Oil", "Gasoline", "Distillates"],
            key="seasonal_inventory_product"
        )

        seasonal_data = seasonal[
            seasonal["Product"] == product_choice
        ].sort_values("Date").copy()

        if seasonal_data.empty:
            st.warning(
                "No seasonal inventory data available "
                "for this product."
            )

        else:
            latest_seasonal = seasonal_data.iloc[-1]

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Actual Inventories",
                f"{latest_seasonal['Actual_MMbbl']:,.2f} million bbl"
            )

            c2.metric(
                "Five-Year Seasonal Average",
                f"{latest_seasonal['Five_Year_Avg_MMbbl']:,.2f} million bbl"
            )

            c3.metric(
                "Deviation from Seasonal Average",
                f"{latest_seasonal['Difference_Pct']:+.2f}%"
            )

            fig_seasonal = go.Figure()

            fig_seasonal.add_trace(
                go.Scatter(
                    x=seasonal_data["Date"],
                    y=seasonal_data["Actual_MMbbl"],
                    mode="lines",
                    name="Actual Inventories"
                )
            )

            fig_seasonal.add_trace(
                go.Scatter(
                    x=seasonal_data["Date"],
                    y=seasonal_data["Five_Year_Avg_MMbbl"],
                    mode="lines",
                    name="Five-Year Seasonal Average",
                    line=dict(dash="dash")
                )
            )

            fig_seasonal.update_layout(
                title=f"{product_choice}: Actual vs Seasonal Inventories",
                xaxis_title="Date",
                yaxis_title="Million barrels",
                template="plotly_white",
                hovermode="x unified"
            )

            st.plotly_chart(
                fig_seasonal,
                use_container_width=True
            )

            deviation = float(
                latest_seasonal["Difference_Pct"]
            )

            if deviation < 0:
                interpretation = (
                    f"{product_choice} inventories are "
                    f"{abs(deviation):.2f}% below their "
                    "five-year seasonal average."
                )
            elif deviation > 0:
                interpretation = (
                    f"{product_choice} inventories are "
                    f"{deviation:.2f}% above their "
                    "five-year seasonal average."
                )
            else:
                interpretation = (
                    f"{product_choice} inventories are "
                    "in line with their seasonal average."
                )

            st.info(interpretation)

            st.caption(
                f"Latest observation: "
                f"{latest_seasonal['Date']:%d %B %Y} | "
                f"Reference years: "
                f"{latest_seasonal['Reference_Years']} | "
                "Source: US EIA historical weekly inventories. "
                "Seasonal average calculated from the "
                "same ISO calendar week over the preceding "
                "five years."
            )

    else:
        st.warning(
            "Seasonal inventory CSV not found. "
            "Upload eia_inventory_seasonality.csv "
            "to energy_dashboard_data."
        )
elif page == "Brent Futures Market Structure":

    st.header("Brent Futures Market Structure")

    st.caption(
        "ICE Brent crude futures | 6 November 2026 "
        "| Delayed last-trade price snapshot"
    )

    # Load futures curve
    futures = pd.read_csv(
        DATA_DIR / "brent_futures_curve.csv",
        parse_dates=["Delivery_Month", "Observation_Date"]
    )

    futures = futures.sort_values(
        "Delivery_Month"
    ).reset_index(drop=True)

    prices = futures["Price_USD_bbl"]

    # Calculate calendar spreads
    m1 = prices.iloc[0]
    m2 = prices.iloc[1]
    m6 = prices.iloc[5]

    m1_m2 = m1 - m2
    m1_m6 = m1 - m6

    if m1_m2 > 0:
        structure = "Backwardation"
    elif m1_m2 < 0:
        structure = "Contango"
    else:
        structure = "Flat"

    # Market metrics
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "M1-M2 Spread",
        f"${m1_m2:+.2f}/bbl"
    )

    col2.metric(
        "M1-M6 Spread",
        f"${m1_m6:+.2f}/bbl"
    )

    col3.metric(
        "Front-End Structure",
        structure
    )

    # Interactive futures curve
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=futures["Delivery_Month"],
        y=futures["Price_USD_bbl"],
        mode="lines+markers",
        name="ICE Brent Futures",
        line=dict(width=3),
        marker=dict(size=8),
        hovertemplate=(
            "%{x|%b %Y}<br>"
            "$%{y:.2f}/bbl"
            "<extra></extra>"
        )
    ))

    fig.update_layout(
        title="Brent Futures Forward Curve",
        xaxis_title="Delivery Month",
        yaxis_title="USD per barrel",
        template="plotly_white",
        hovermode="x unified"
    )

    st.plotly_chart(fig, width="stretch")

    # Monthly calendar spreads
    st.subheader("Adjacent-Month Calendar Spreads")

    futures["Calendar_Spread"] = (
        futures["Price_USD_bbl"]
        - futures["Price_USD_bbl"].shift(-1)
    )

    spread_data = futures.iloc[:-1].copy()

    fig_spread = go.Figure()

    fig_spread.add_trace(go.Bar(
        x=spread_data["Delivery_Month"],
        y=spread_data["Calendar_Spread"],
        name="Monthly Calendar Spread"
    ))

    fig_spread.add_hline(
        y=0,
        line_dash="dash"
    )

    fig_spread.update_layout(
        title="Brent Adjacent-Month Futures Spreads",
        xaxis_title="Nearer Delivery Month",
        yaxis_title="USD per barrel",
        template="plotly_white"
    )

    st.plotly_chart(fig_spread, width="stretch")

    # Automated market commentary
    st.subheader("Market Structure Insights")

    if structure == "Backwardation":
        commentary = (
            f"The front of the Brent futures curve "
            f"is in backwardation. The first contract "
            f"trades ${m1_m2:.2f}/bbl above the second "
            f"contract and ${m1_m6:.2f}/bbl above "
            f"the sixth contract. This structure "
            f"can be consistent with stronger "
            f"near-term crude valuations."
        )

    elif structure == "Contango":
        commentary = (
            f"The front of the Brent futures curve "
            f"is in contango. The second contract "
            f"trades ${abs(m1_m2):.2f}/bbl above "
            f"the first contract. Contango can "
            f"support storage economics when "
            f"the spread covers carrying costs."
        )

    else:
        commentary = (
            "The first two Brent futures contracts "
            "are trading at approximately the same price."
        )

    st.info(commentary)

    st.caption(
        "Source: ICE Futures Europe, Brent Crude Futures. "
        "Snapshot dated 6 November 2026. "
        "Prices are delayed last-trade observations, "
        "not official settlement prices. "
        "Calendar spreads are calculated as "
        "nearer-month minus later-month prices. "
        "This is a static historical snapshot."
    )

    with st.expander("View futures contract data"):
        st.dataframe(
            futures[
                ["Contract", "Price_USD_bbl",
                 "Calendar_Spread"]
            ],
            width="stretch",
            hide_index=True
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

    st.subheader("Historical Dataset Coverage")
    st.caption(
        "The following dates come from the CSV files saved in this "
        "GitHub repository. They are not live market data. "
        "Forecast target dates are not counted as historical observations."
    )

    coverage_files = {
        "Brent spot": ("brent_prices.csv", "Date"),
        "Brent–WTI spread": ("brent_wti_spread.csv", "Date"),
        "US EIA inventories": ("eia_inventories.csv", "Date"),
        "EU fuel averages": ("eu_fuel_prices.csv", "Date"),
        "European country fuel prices": ("country_fuel_prices.csv", "Date"),
        "Indicative refining crack spreads": (
            "refining_crack_spreads.csv", "Date"
        ),
        "Historical prices used for forecasting": (
            "forecast_price_history.csv", "Date"
        ),
        "Brent futures snapshot": (
            "brent_futures_curve.csv", "Observation_Date"
        ),
    }
    coverage_rows = []
    for label, (filename, date_column) in coverage_files.items():
        filepath = DATA_DIR / filename
        if not filepath.exists():
            continue
        try:
            dates = pd.to_datetime(
                pd.read_csv(filepath, usecols=[date_column])[date_column],
                errors="coerce"
            ).dropna()
            if not dates.empty:
                coverage_rows.append({
                    "Dataset": label,
                    "First observation": dates.min().strftime("%d %b %Y"),
                    "Last observation": dates.max().strftime("%d %b %Y"),
                })
        except (ValueError, OSError):
            continue

    if coverage_rows:
        st.dataframe(
            pd.DataFrame(coverage_rows),
            use_container_width=True,
            hide_index=True
        )

    technical_file = DATA_DIR / "technical_forecasts_v2.csv"
    if technical_file.exists():
        try:
            technical_dates_df = pd.read_csv(technical_file)
            for date_column in ("Last_Date", "Last_Actual_Date", "Date"):
                if date_column in technical_dates_df.columns:
                    dates = pd.to_datetime(
                        technical_dates_df[date_column], errors="coerce"
                    ).dropna()
                    if not dates.empty:
                        st.caption(
                            "Technical forecasting input through "
                            f"{dates.max():%d %B %Y}."
                        )
                    break
        except (ValueError, OSError):
            pass


# REFINING CRACK SPREAD ANALYSIS
if page == "Refining Crack Spreads":

    st.header("Diesel & Gasoline Crack Spread Analysis")

    st.caption(
        "Brent crude versus New York Harbor wholesale "
        "diesel and gasoline spot benchmarks"
    )

    crack_file = DATA_DIR / "refining_crack_spreads.csv"

    if not crack_file.exists():
        st.error("Upload refining_crack_spreads.csv to GitHub.")
        st.stop()

    @st.cache_data
    def load_cracks():
        df = pd.read_csv(crack_file, parse_dates=["Date"])
        return df.sort_values("Date")

    cracks = load_cracks()

    period = st.selectbox(
        "Historical period",
        ["1 Year", "3 Years", "5 Years", "10 Years", "All Data"],
        index=1,
        key="crack_period"
    )

    data = cracks.copy()

    if period != "All Data":
        years = int(period.split()[0])
        cutoff = data["Date"].max() - pd.DateOffset(years=years)
        data = data[data["Date"] >= cutoff].copy()

    if data.empty:
        st.warning("No data for this period.")
        st.stop()

    latest = data.iloc[-1]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Diesel Crack",
        f"${latest['Diesel_Crack']:.2f}/bbl"
    )

    c2.metric(
        "Gasoline Crack",
        f"${latest['Gasoline_Crack']:.2f}/bbl"
    )

    c3.metric(
        "Illustrative 3:2:1 Crack",
        f"${latest['Crack_321']:.2f}/bbl"
    )

    st.caption(
        f"Latest matched observation: "
        f"{latest['Date']:%d %B %Y}"
    )

    # HISTORICAL CRACK SPREAD CHART
    st.subheader("Historical Product Crack Spreads")

    fig = go.Figure()

    for column, label in [
        ("Diesel_Crack", "Diesel Crack"),
        ("Gasoline_Crack", "Gasoline Crack"),
        ("Crack_321", "3:2:1 Crack")
    ]:
        fig.add_trace(go.Scatter(
            x=data["Date"],
            y=data[column],
            mode="lines",
            name=label
        ))

    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="USD per barrel",
        hovermode="x unified",
        template="plotly_white"
    )

    st.plotly_chart(fig, width="stretch")

    # HISTORICAL COMPARISON
    st.subheader("Crack Spread Market Insights")

    diesel_average = data["Diesel_Crack"].mean()
    gasoline_average = data["Gasoline_Crack"].mean()

    c1, c2 = st.columns(2)

    c1.metric(
        "Period Average Diesel Crack",
        f"${diesel_average:.2f}/bbl"
    )

    c2.metric(
        "Period Average Gasoline Crack",
        f"${gasoline_average:.2f}/bbl"
    )

    diesel_difference = (
        latest["Diesel_Crack"] - diesel_average
    )

    if diesel_difference > 0:
        direction = "above"
    elif diesel_difference < 0:
        direction = "below"
    else:
        direction = "equal to"

    st.info(
        f"The latest diesel crack is "
        f"${abs(diesel_difference):.2f}/bbl "
        f"{direction} its selected-period average. "
        "This describes relative benchmark pricing, "
        "not a refinery's realised profit."
    )

    # REFINING MARGIN SENSITIVITY
    st.subheader("Refining Margin Sensitivity")

    st.write(
        "Illustrative 3:2:1 margin sensitivity "
        "to changes in crude and product prices."
    )

    crude_change = st.slider(
        "Brent price change (USD/bbl)",
        -30.0, 30.0, 0.0, 1.0,
        key="crack_crude_change"
    )

    diesel_change = st.slider(
        "Diesel price change (USD/bbl)",
        -30.0, 30.0, 0.0, 1.0,
        key="crack_diesel_change"
    )

    gasoline_change = st.slider(
        "Gasoline price change (USD/bbl)",
        -30.0, 30.0, 0.0, 1.0,
        key="crack_gasoline_change"
    )

    revised_margin = (
        2 * (
            latest["Gasoline_USD_bbl"]
            + gasoline_change
        )
        + (
            latest["Diesel_USD_bbl"]
            + diesel_change
        )
        - 3 * (
            latest["Brent"] + crude_change
        )
    ) / 3

    st.metric(
        "Scenario 3:2:1 Crack",
        f"${revised_margin:.2f}/bbl",
        delta=(
            f"${revised_margin - latest['Crack_321']:+.2f}/bbl"
        )
    )

    st.divider()

    st.caption(
        "Source: EIA spot price series via FRED. "
        "Diesel: New York Harbor ultra-low-sulfur diesel. "
        "Gasoline: New York Harbor conventional regular. "
        "Crude: Brent spot. "
        "Product prices converted using 42 US gallons "
        "per barrel. The 3:2:1 crack assumes two barrels "
        "of gasoline and one barrel of diesel per three "
        "barrels of crude. These are indicative "
        "cross-market benchmark spreads, not European "
        "ARA crack spreads or realised refinery margins. "
        "Excludes yields, freight, operating costs, "
        "quality differences and other adjustments."
    )

# Forecasting is intentionally isolated to its own sidebar page.
if page == "Price Forecasting":
    st.header("Price Forecasting")
    st.caption(
        "Historical research snapshot — not live prices or trading advice. "
        "Each forecast uses the observation date stored in its source CSV."
    )
    st.info(
        "This portfolio uses fixed historical datasets. "
        "Forecasts and backtest results are not refreshed automatically."
    )

    # ============================================================
    # CRUDE & REFINED PRODUCTS PRICE FORECASTING
    # ============================================================

    st.divider()
    st.subheader("Crude & Refined Products Price Forecasting")

    st.caption(
        "Statistical forecasts using historical spot benchmark prices. "
        "For research and scenario analysis, not trading recommendations."
    )

    forecast_file = DATA_DIR / "energy_price_forecasts.csv"
    accuracy_file = DATA_DIR / "forecast_accuracy.csv"

    if forecast_file.exists() and accuracy_file.exists():

        forecasts = pd.read_csv(
            forecast_file, parse_dates=["Date", "Last_Actual_Date"]
        )

        if not forecasts.empty:
            observed_dates = pd.to_datetime(
                forecasts["Last_Actual_Date"], errors="coerce"
            ).dropna()
            if not observed_dates.empty:
                st.caption(
                    "Statistical forecast input: latest historical observation "
                    f"{observed_dates.max():%d %B %Y}. "
                    "The forecast dates beyond this are projections."
                )

        accuracy = pd.read_csv(accuracy_file)

        commodity = st.selectbox(
            "Select commodity",
            ["Brent", "WTI", "Diesel", "Gasoline"],
            key="price_forecast_commodity"
        )

        horizon = st.selectbox(
            "Forecast horizon",
            [30, 60, 90],
            format_func=lambda x: f"{x} Days",
            key="price_forecast_horizon"
        )

        selected = (
            forecasts[forecasts["Commodity"] == commodity]
            .sort_values("Date")
            .copy()
        )

        if not selected.empty:

            latest_date = selected["Last_Actual_Date"].iloc[0]

            end_date = latest_date + pd.Timedelta(
                days=horizon
            )

            selected = selected[
                selected["Date"] <= end_date
            ]

            if not selected.empty:

                latest = selected.iloc[-1]
                start_price = float(latest["Last_Actual"])
                forecast_price = float(latest["Forecast"])

                change_pct = (
                    (forecast_price / start_price - 1) * 100
                    if start_price != 0 else 0
                )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Latest Historical Price",
                    f"${start_price:,.2f}/bbl"
                )

                col2.metric(
                    "Forecast Price",
                    f"${forecast_price:,.2f}/bbl",
                    delta=f"{change_pct:+.2f}%"
                )

                col3.metric(
                    "Approximate 80% Range",
                    (
                        f"${latest['Lower_80']:,.2f}"
                        f" – ${latest['Upper_80']:,.2f}"
                    )
                )


                # IMPROVED FORECAST CHART
                history_file = DATA_DIR / "forecast_price_history.csv"

                fig = go.Figure()

                if history_file.exists():
                    price_history = pd.read_csv(
                        history_file, parse_dates=["Date"]
                    )

                    historical = (
                        price_history[
                            price_history["Commodity"] == commodity
                        ]
                        .sort_values("Date")
                    )

                    fig.add_trace(go.Scatter(
                        x=historical["Date"],
                        y=historical["Price"],
                        mode="lines",
                        line=dict(color="#2563eb", width=2.5),
                        name="Actual Historical Price"
                    ))

                # Connect the forecast to the last actual price
                forecast_dates = [latest_date] + selected["Date"].tolist()
                forecast_values = (
                    [start_price] + selected["Forecast"].tolist()
                )

                fig.add_trace(go.Scatter(
                    x=forecast_dates,
                    y=forecast_values,
                    mode="lines",
                    line=dict(
                        color="#ea580c",
                        width=3,
                        dash="dash"
                    ),
                    name="Forecast"
                ))

                # Light uncertainty band
                fig.add_trace(go.Scatter(
                    x=selected["Date"],
                    y=selected["Upper_80"],
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo="skip"
                ))

                fig.add_trace(go.Scatter(
                    x=selected["Date"],
                    y=selected["Lower_80"],
                    mode="lines",
                    line=dict(width=0),
                    fill="tonexty",
                    fillcolor="rgba(234,88,12,0.10)",
                    name="Approximate 80% Range"
                ))

                # Mark where historical data ends
                fig.add_vline(
                    x=latest_date.timestamp() * 1000,
                    line_dash="dot",
                    line_color="gray",
                    annotation_text="Forecast begins",
                    annotation_position="top right"
                )

                # Highlight the final forecast price
                fig.add_trace(go.Scatter(
                    x=[latest["Date"]],
                    y=[forecast_price],
                    mode="markers",
                    marker=dict(
                        color="#ea580c",
                        size=10
                    ),
                    name="Forecast End"
                ))

                fig.update_layout(
                    title=f"{commodity}: Historical Prices & Forecast",
                    xaxis_title="Date",
                    yaxis_title="USD per barrel",
                    hovermode="x unified",
                    height=500,
                    legend=dict(orientation="h", y=1.12),
                    margin=dict(t=100)
                )

                st.plotly_chart(
                    fig, use_container_width=True
                )

                st.subheader("Forecast Model Performance")

                result = accuracy[
                    accuracy["Commodity"] == commodity
                ]

                if not result.empty:

                    result = result.iloc[0]

                    c1, c2 = st.columns(2)

                    c1.metric(
                        "ARIMA Mean Absolute Error",
                        f"${result['Model_MAE']:.2f}/bbl"
                    )

                    c2.metric(
                        "No-Change Benchmark Error",
                        f"${result['Naive_MAE']:.2f}/bbl"
                    )

                    if result["Model_MAE"] < result["Naive_MAE"]:
                        st.success(
                            "ARIMA outperformed the no-change "
                            "benchmark in the historical test."
                        )
                    else:
                        st.warning(
                            "ARIMA did not outperform the no-change "
                            "benchmark in the historical test."
                        )

                st.info(
                    f"Latest historical observation: "
                    f"{latest_date:%d %B %Y}. "
                    "Forecasts are generated from historical price "
                    "changes. These projections are uncertain and "
                    "should not be interpreted as market futures prices."
                )

    else:
        st.warning(
            "Forecast files are missing. Upload "
            "energy_price_forecasts.csv and forecast_accuracy.csv "
            "to the energy_dashboard_data folder."
        )

    # ============================================================
    # TECHNICAL FORECASTING & MODEL COMPARISON
    # ============================================================

    import pandas as pd
    import plotly.graph_objects as go
    import streamlit as st
    from pathlib import Path

    DATA_DIR_V2 = Path("energy_dashboard_data")

    @st.cache_data
    def load_technical_data_v2():
        forecasts = pd.read_csv(
            DATA_DIR_V2 / "technical_forecasts_v2.csv"
        )
        accuracy = pd.read_csv(
            DATA_DIR_V2 / "technical_accuracy_v2.csv"
        )
        signals = pd.read_csv(
            DATA_DIR_V2 / "technical_signals_v2.csv"
        )

        forecasts.columns = forecasts.columns.str.strip()
        accuracy.columns = accuracy.columns.str.strip()
        signals.columns = signals.columns.str.strip()

        return forecasts, accuracy, signals


    with st.expander(
        "📈 Technical Forecasting & Model Comparison",
        expanded=False
    ):
        st.subheader("Crude Oil Technical Price Forecasts")
        st.caption(
            "Brent and WTI | Statistical models, technical indicators "
            "and historical out-of-sample model comparison"
        )

        try:
            tf, ta, ts = load_technical_data_v2()

            for date_column in ("Last_Date", "Last_Actual_Date", "Date"):
                if date_column in tf.columns:
                    technical_dates = pd.to_datetime(
                        tf[date_column], errors="coerce"
                    ).dropna()
                    if not technical_dates.empty:
                        st.caption(
                            "Technical forecast input: latest historical "
                            f"observation {technical_dates.max():%d %B %Y}."
                        )
                    break

            required_forecast = {
                "Market", "Horizon_Days", "Model",
                "Last_Price", "Forecast_Price"
            }
            required_accuracy = {
                "Market", "Horizon_Days",
                "Flat_MAE", "Ridge_MAE", "ML_MAE"
            }

            if not required_forecast.issubset(tf.columns):
                st.error(
                    "Technical forecast CSV columns do not match. "
                    f"Available columns: {list(tf.columns)}"
                )
                st.stop()

            if not required_accuracy.issubset(ta.columns):
                st.error(
                    "Technical accuracy CSV columns do not match. "
                    f"Available columns: {list(ta.columns)}"
                )
                st.stop()

            c1, c2 = st.columns(2)

            with c1:
                market_v2 = st.selectbox(
                    "Select crude benchmark",
                    sorted(tf["Market"].dropna().unique()),
                    key="technical_market_v2"
                )

            with c2:
                horizons_v2 = sorted(
                    tf.loc[
                        tf["Market"] == market_v2,
                        "Horizon_Days"
                    ].dropna().astype(int).unique()
                )

                horizon_v2 = st.selectbox(
                    "Forecast horizon",
                    horizons_v2,
                    format_func=lambda x: f"{x} days",
                    key="technical_horizon_v2"
                )

            selected = tf[
                (tf["Market"] == market_v2)
                & (tf["Horizon_Days"] == horizon_v2)
            ].copy()

            selected["Forecast_Price"] = pd.to_numeric(
                selected["Forecast_Price"], errors="coerce"
            )
            selected["Last_Price"] = pd.to_numeric(
                selected["Last_Price"], errors="coerce"
            )
            selected = selected.dropna(
                subset=["Forecast_Price", "Last_Price"]
            )

            if selected.empty:
                st.warning("No forecasts for this selection.")
            else:
                latest_price = float(
                    selected["Last_Price"].iloc[0]
                )

                model_order = [
                    "Flat", "Ridge", "Machine Learning"
                ]

                model_prices = {
                    str(row["Model"]): float(row["Forecast_Price"])
                    for _, row in selected.iterrows()
                }

                st.markdown("#### Model price targets")

                metric_cols = st.columns(3)

                for col, model in zip(metric_cols, model_order):
                    price = model_prices.get(model)

                    with col:
                        if price is not None:
                            pct = (
                                (price / latest_price - 1) * 100
                                if latest_price != 0 else 0
                            )
                            st.metric(
                                model,
                                f"${price:,.2f}/bbl",
                                f"{pct:+.2f}%"
                            )
                        else:
                            st.metric(model, "N/A")

                st.caption(
                    f"Last observed {market_v2} price: "
                    f"${latest_price:,.2f}/bbl. "
                    "Model targets are indicative, not guaranteed outcomes."
                )

                fig = go.Figure()

                fig.add_hline(
                    y=latest_price,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text="Last actual price"
                )

                colors = {
                    "Flat": "#64748b",
                    "Ridge": "#2563eb",
                    "Machine Learning": "#ea580c"
                }

                for model in model_order:
                    if model in model_prices:
                        fig.add_trace(
                            go.Bar(
                                x=[model],
                                y=[model_prices[model]],
                                name=model,
                                marker_color=colors[model],
                                text=[
                                    f"${model_prices[model]:.2f}"
                                ],
                                textposition="outside"
                            )
                        )

                fig.update_layout(
                    title=(
                        f"{market_v2}: {horizon_v2}-Day "
                        "Model Forecast Comparison"
                    ),
                    yaxis_title="USD per barrel",
                    xaxis_title="Forecast model",
                    height=450,
                    showlegend=False,
                    margin=dict(t=70)
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="technical_model_chart_v2"
                )

            # ------------------------------------------
            # HISTORICAL FORECAST ACCURACY
            # ------------------------------------------

            st.markdown("#### Historical Model Accuracy")

            accuracy_row = ta[
                (ta["Market"] == market_v2)
                & (ta["Horizon_Days"] == horizon_v2)
            ]

            if not accuracy_row.empty:
                a = accuracy_row.iloc[0]

                mae_values = {
                    "Flat": float(a["Flat_MAE"]),
                    "Ridge": float(a["Ridge_MAE"]),
                    "Machine Learning": float(a["ML_MAE"])
                }

                best_model = min(
                    mae_values, key=mae_values.get
                )

                st.success(
                    f"Best historical model: {best_model} "
                    f"| MAE: ${mae_values[best_model]:.2f}/bbl"
                )

                accuracy_chart = go.Figure()

                accuracy_chart.add_trace(
                    go.Bar(
                        x=list(mae_values.keys()),
                        y=list(mae_values.values()),
                        marker_color=[
                            "#16a34a" if m == best_model
                            else "#94a3b8"
                            for m in mae_values
                        ],
                        text=[
                            f"${v:.2f}"
                            for v in mae_values.values()
                        ],
                        textposition="outside"
                    )
                )

                accuracy_chart.update_layout(
                    title="Backtested Mean Absolute Error",
                    yaxis_title="MAE (USD per barrel)",
                    xaxis_title="Model",
                    height=380
                )

                st.plotly_chart(
                    accuracy_chart,
                    use_container_width=True,
                    key="technical_accuracy_chart_v2"
                )

                st.caption(
                    "Lower MAE is better. These results measure "
                    "historical out-of-sample forecast error, "
                    "not certainty about future prices."
                )

            # ------------------------------------------
            # TECHNICAL SIGNALS
            # ------------------------------------------

            st.markdown("#### Technical Market Signals")

            signal_row = ts[ts["Market"] == market_v2]

            if not signal_row.empty:
                s = signal_row.iloc[0]

                signal_cols = st.columns(3)

                with signal_cols[0]:
                    if "RSI_14" in ts.columns:
                        st.metric(
                            "14-Day RSI",
                            f"{float(s['RSI_14']):.1f}"
                        )

                with signal_cols[1]:
                    if "MACD_Signal_Gap" in ts.columns:
                        st.metric(
                            "MACD Signal Gap",
                            f"{float(s['MACD_Signal_Gap']):+.4f}"
                        )

                with signal_cols[2]:
                    if "Trend" in ts.columns:
                        st.metric(
                            "Technical Trend",
                            str(s["Trend"])
                        )

                if "RSI_14" in ts.columns:
                    rsi = float(s["RSI_14"])

                    if rsi >= 70:
                        st.info(
                            "RSI is above 70: traditionally "
                            "interpreted as overbought."
                        )
                    elif rsi <= 30:
                        st.info(
                            "RSI is below 30: traditionally "
                            "interpreted as oversold."
                        )
                    else:
                        st.info(
                            "RSI is between 30 and 70: "
                            "neither conventional extreme is triggered."
                        )

            # ------------------------------------------
            # DATA & METHODOLOGY
            # ------------------------------------------

            with st.expander("Forecast methodology and raw data"):
                st.write(
                    "Flat is a no-change price baseline. "
                    "Ridge is regularised linear regression. "
                    "Machine Learning is the fitted nonlinear "
                    "model from the Colab analysis."
                )

                st.write(
                    "Forecasts are model scenarios, not "
                    "market-implied forward prices. "
                    "Historical accuracy should be evaluated "
                    "using time-ordered, out-of-sample observations. "
                    "Technical indicators are descriptive and "
                    "do not establish causation."
                )

                st.dataframe(selected, use_container_width=True)
                st.dataframe(ta, use_container_width=True)
                st.dataframe(ts, use_container_width=True)

                st.caption(
                    "Source: project historical price datasets "
                    "and Python model calculations. "
                    "Forecast dates and last-observation dates "
                    "are determined by the exported CSV snapshot."
                )

        except FileNotFoundError as error:
            st.error(
                f"Missing data file: {error}. "
                "Check the energy_dashboard_data folder on GitHub."
            )
        except Exception as error:
            st.error(
                f"Technical forecasting section could not load: {error}"
            )
