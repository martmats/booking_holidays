import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import holidays
import json

# Initialize Google Sheet client and constants
creds = st.secrets["GOOGLE_CREDS"]
client = gspread.service_account_from_dict(creds)
sheet = client.open("HOLIDAYS BOOKING SYSTEM APP").sheet1
def fetch_bookings():
    """Fetch all bookings from the Google Sheet and return as a DataFrame."""
    try:
        records = sheet.get_all_records()
        return pd.DataFrame(records)
    except Exception as e:
        st.error(f"Error fetching bookings: {e}")
        return pd.DataFrame()  # Return an empty DataFrame if there is an issue

def get_user_holidays(user_name, bookings_df):
    """Generate a dictionary of holiday dates for a user, including booked and bank holidays."""
    user_holidays = {}
    
    # Get user-specific bookings
    user_bookings = bookings_df[bookings_df['Name'].str.lower() == user_name.lower()]

    # Process each booking to extract dates
    for _, row in user_bookings.iterrows():
        start_date = pd.to_datetime(row['Start Date'], format='%d/%m/%Y', errors='coerce')
        end_date = pd.to_datetime(row['End Date'], format='%d/%m/%Y', errors='coerce')
        
        if pd.notna(start_date) and pd.notna(end_date):
            current_date = start_date
            while current_date <= end_date:
                user_holidays[current_date.strftime('%Y-%m-%d')] = 'personal'
                current_date += timedelta(days=1)

    # Add bank holidays
    current_year = datetime.now().year
    uk_holidays = holidays.UnitedKingdom(years=current_year)
    for date, name in uk_holidays.items():
        user_holidays[str(date)] = 'bank'

    return user_holidays

def generate_calendar(year, month, holidays):
    """Generate an HTML calendar for a specific month and year, highlighting holidays."""
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)

    # CSS for styling the calendar
    st.markdown(
        """
        <style>
        .calendar-table {
            width: 100%;
            border-collapse: collapse;
        }
        .calendar-table th {
            background-color: #007bff;
            color: white;
            padding: 10px;
        }
        .calendar-table td {
            border: 1px solid #ddd;
            text-align: center;
            padding: 10px;
        }
        .holiday {
            background-color: #ffcccc;
            color: #d9534f;
        }
        .bank-holiday {
            background-color: #ffffcc;
            color: #f0ad4e;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Build HTML table for the calendar
    html = '<table class="calendar-table">'
    html += '<tr>' + ''.join(f'<th>{day}</th>' for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']) + '</tr>'

    for week in month_days:
        html += '<tr>'
        for day in week:
            if day == 0:
                html += '<td></td>'
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                if date_str in holidays:
                    # Apply holiday class if date is in holidays
                    css_class = "holiday" if holidays[date_str] == "personal" else "bank-holiday"
                    html += f'<td class="{css_class}">{day}</td>'
                else:
                    html += f'<td>{day}</td>'
        html += '</tr>'
    
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

def main():
    st.title("Holiday Booking System")

    # Sidebar Input
    user_name = st.sidebar.text_input("Enter your name")
    
    # Fetch bookings data
    bookings_df = fetch_bookings()

    if user_name:
        # Generate user-specific holidays dictionary
        user_holidays = get_user_holidays(user_name, bookings_df)

        # Display calendars for the next two months
        current_year = datetime.now().year
        current_month = datetime.now().month

        # Display the calendar for the current month
        generate_calendar(current_year, current_month, user_holidays)

        # Display the calendar for the next month
        next_month = current_month + 1 if current_month < 12 else 1
        next_year = current_year if current_month < 12 else current_year + 1
        generate_calendar(next_year, next_month, user_holidays)

if __name__ == "__main__":
    main()
