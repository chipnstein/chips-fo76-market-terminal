import sys
from pathlib import Path

# Ensure the project root is on sys.path when launched via `streamlit run dashboard/app.py`
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st
from database.db_manager import DatabaseManager

st.set_page_config(
    page_title="FO76 Market Terminal",
    layout="wide",
)

st.title("Fallout 76 Market Terminal (`r/Market76`)")
st.caption("Live supply vs. demand and price tracking across PC, PlayStation, and Xbox.")

db = DatabaseManager()


def render_platform_tab(platform_code: str, label: str) -> None:
    trades = db.get_trades_by_platform(platform_code, limit=2000)

    if not trades:
        st.info(f"No {label} trades recorded in the database yet.")
        return

    df = pd.DataFrame(trades)
    df["created_utc"] = pd.to_datetime(df["created_utc"], utc=True)

    # --- Filters ---
    col_search, col_curr = st.columns([3, 1])
    with col_search:
        search_query = st.text_input(
            "Filter by item name",
            placeholder="e.g. Clean Pitman Mask, Weenie Wagon, Pin-Pointers...",
            key=f"search_{platform_code}",
        )
    with col_curr:
        currency_filter = st.selectbox(
            "Currency",
            options=["All", "L", "c", "OFFER"],
            key=f"curr_{platform_code}",
        )

    filtered = df.copy()
    if search_query:
        filtered = filtered[
            filtered["item_name"].str.contains(search_query, case=False, na=False)
        ]
    if currency_filter != "All":
        filtered = filtered[filtered["currency"] == currency_filter]

    if filtered.empty:
        st.warning("No trades match your current filter.")
        return

    # --- Top KPIs ---
    total_trades = len(filtered)
    buy_count = int((filtered["direction"] == "BUY").sum())
    sell_count = int((filtered["direction"] == "SELL").sum())
    ratio_str = f"{buy_count / sell_count:.2f}" if sell_count > 0 else "∞"

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Listings", total_trades)
    k2.metric("Buy Demand (W:)", buy_count)
    k3.metric("Sell Supply (H:)", sell_count)
    k4.metric("Buy / Sell Ratio", ratio_str)

    st.divider()

    # --- Item Summary Table (Supply vs. Demand & Spread) ---
    st.subheader("Market Summary by Item")
    summary_rows = []
    for (item, curr), group in filtered.groupby(["item_name", "currency"]):
        buys = group[group["direction"] == "BUY"]
        sells = group[group["direction"] == "SELL"]
        summary_rows.append({
            "Item": item,
            "Currency": curr,
            "Buy Count (W:)": len(buys),
            "Sell Count (H:)": len(sells),
            "Median Buy": buys["price"].median() if not buys["price"].dropna().empty else None,
            "Median Sell": sells["price"].median() if not sells["price"].dropna().empty else None,
            "Mentions": len(group),
        })

    summary_df = pd.DataFrame(summary_rows).sort_values("Mentions", ascending=False)
    st.dataframe(summary_df, width="stretch", hide_index=True)

    # --- Price Trend Chart (for priced listings) ---
    priced = filtered.dropna(subset=["price"]).sort_values("created_utc")
    if len(priced) >= 2:
        st.subheader("Price Activity Over Time")
        chart_df = priced.pivot_table(
            index="created_utc",
            columns="direction",
            values="price",
            aggfunc="mean",
        )
        st.line_chart(chart_df)

    # --- Raw Trade Feed ---
    st.subheader("Recent Listings")
    display_cols = ["created_utc", "direction", "item_name", "price", "currency", "raw_title"]
    st.dataframe(
        filtered[display_cols],
        width="stretch",
        hide_index=True,
    )


tab_pc, tab_ps, tab_xb = st.tabs(["PC", "PlayStation (PS)", "Xbox (XB)"])

with tab_pc:
    render_platform_tab("PC", "PC")

with tab_ps:
    render_platform_tab("PS", "PlayStation")

with tab_xb:
    render_platform_tab("XB", "Xbox")