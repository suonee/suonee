import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Function to fetch live data from the website


def fetch_live_data():
    url = "https://www.sharesansar.com/live-trading"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.content, 'html.parser')
    live_data = []

    # Assuming the table data is in a structured format
    table = soup.find('table', {'id': 'headFixed'})
    if table:
        rows = table.find_all('tr')[1:]  # Skip the header row
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:  # Adjust based on the number of columns needed
                symbol = cells[1].text.strip()
                try:
                    ltp = float(cells[2].text.replace(",", "").strip())
                except ValueError:
                    ltp = None

                live_data.append({
                    'Symbol': symbol,
                    'LTP': ltp
                })

    return pd.DataFrame(live_data)


# Set Streamlit app to full-width
st.set_page_config(layout="wide")

# Main application


def main():
    st.title("Nepse Live Tracker")

    # Load the Excel data
    try:
        excel_data = pd.read_excel('data.xlsx')
    except Exception as e:
        st.error(f"Error loading Excel data: {e}")
        return

    # Fetch live data
    live_data_df = fetch_live_data()

    if live_data_df.empty:
        st.warning("No live data fetched. Please check the live data source.")
        return

    # Merge live data with the Excel data
    merged_df = pd.merge(excel_data, live_data_df, on='Symbol', how='inner')

    # Tables for Breakout, Breakdown, and Watchlist
    breakout_data = []
    breakdown_data = []
    watchlist_data = []

    for _, row in merged_df.iterrows():
        symbol = row['Symbol']
        ltp = row['LTP']
        bottom = row['Bottom']
        high = row['High']
        ath = row['ATH']
        atl = row['ATL']

        # Check for Breakout and ATH Breakout
        if ltp > high:
            breakout_data.append({
                'Symbol': symbol,
                'LTP': ltp,
                'High': high,
                'Type': 'Breakout' if ltp <= ath else 'ATH Breakout'
            })
            continue  # Skip further checks for this symbol

        # Check for Breakdown and ATL Breakdown
        if ltp < bottom:
            breakdown_data.append({
                'Symbol': symbol,
                'LTP': ltp,
                'Bottom': bottom,
                'Type': 'Breakdown' if ltp >= atl else 'ATL Breakdown'
            })
            continue  # Skip further checks for this symbol

        # Check for Watchlist (within 1% range of High, Bottom, ATH, ATL)
        if abs(ltp - high) / high <= 0.01:
            watchlist_data.append({
                'Symbol': symbol,
                'LTP': ltp,
                'Bottom': bottom,
                'High': high,
                'Type': 'High'
            })
        elif abs(ltp - bottom) / bottom <= 0.01:
            watchlist_data.append({
                'Symbol': symbol,
                'LTP': ltp,
                'Bottom': bottom,
                'High': high,
                'Type': 'Low'
            })

    # Display Breakout table
    if breakout_data:
        st.subheader("Breakout")
        breakout_df = pd.DataFrame(breakout_data)
        st.dataframe(breakout_df, use_container_width=True)

    # Display Breakdown table
    if breakdown_data:
        st.subheader("Breakdown")
        breakdown_df = pd.DataFrame(breakdown_data)
        st.dataframe(breakdown_df, use_container_width=True)

    # Display Watchlist table
    if watchlist_data:
        st.subheader("Watchlist")
        watchlist_df = pd.DataFrame(watchlist_data)
        st.dataframe(watchlist_df, use_container_width=True)


if __name__ == "__main__":
    main()
