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
TOTAL_HOLIDAYS = 28

def get_bank_holidays(year):
    """Retrieve UK bank holidays for a given year."""
    uk_holidays = holidays.UnitedKingdom(years=year)
    return {str(date): name for date, name in uk_holidays.items()}

def fetch_bookings():
    """Fetch all bookings from the Google Sheet and return as a DataFrame."""
    records = sheet.get_all_records()
    return pd.DataFrame(records)

def validate_date_format(date_str):
    """Validate date format (dd/mm/yyyy)."""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        return None

def calculate_remaining_holidays(user_name, bookings_df, bank_holidays):
    """Calculate the remaining holidays for a given user."""
    user_bookings = bookings_df[bookings_df['Name'].str.lower() == user_name.lower()]
    user_holiday_days = sum(
        (validate_date_format(row['End Date']) - validate_date_format(row['Start Date'])).days + 1
        for _, row in user_bookings.iterrows()
        if validate_date_format(row['Start Date']) and validate_date_format(row['End Date'])
    )
    return TOTAL_HOLIDAYS - user_holiday_days

def can_book_holiday(user_name, start_date, end_date, bookings_df, bank_holidays):
    """Check if the user can book the specified holiday dates."""
    if not start_date or not end_date or start_date > end_date:
        return False, "Invalid date range."
    
    remaining_days = calculate_remaining_holidays(user_name, bookings_df, bank_holidays)
    booking_days = (end_date - start_date).days + 1
    
    if booking_days > remaining_days:
        return False, "Insufficient remaining holidays."
    
    return True, None

def add_booking(user_name, start_date, end_date):
    """Add a new booking to the Google Sheet."""
    new_booking = [user_name, start_date.strftime("%d/%m/%Y"), end_date.strftime("%d/%m/%Y")]
    sheet.append_row(new_booking)

def show_holiday_calendar(bookings_df, bank_holidays):
    """Display the calendar of holidays using Streamlit."""
    # Simplified for demonstration. Customize as needed.
    st.write("Holiday Calendar")

def main():
    # Sidebar Input
    st.sidebar.title("Holiday Booking System")
    user_name = st.sidebar.text_input("Enter your name")
    start_date_str = st.sidebar.text_input("Start Date (dd/mm/yyyy)")
    end_date_str = st.sidebar.text_input("End Date (dd/mm/yyyy)")

    start_date = validate_date_format(start_date_str)
    end_date = validate_date_format(end_date_str)

    bank_holidays = get_bank_holidays(datetime.now().year)
    bookings_df = fetch_bookings()

    # Check Remaining Holidays
    if st.sidebar.button("Check Remaining Holidays"):
        remaining_days = calculate_remaining_holidays(user_name, bookings_df, bank_holidays)
        st.sidebar.write(f"Remaining Personal Holidays: {remaining_days}")
    
    # Book Holiday
    if st.sidebar.button("Book Holiday"):
        can_book, error_message = can_book_holiday(user_name, start_date, end_date, bookings_df, bank_holidays)
        if can_book:
            add_booking(user_name, start_date, end_date)
            st.sidebar.success("Holiday booked successfully!")
        else:
            st.sidebar.error(error_message)
    
    # Show Holiday Calendar
    if st.sidebar.button("Show Holidays"):
        show_holiday_calendar(bookings_df, bank_holidays)

if __name__ == "__main__":
    main()
