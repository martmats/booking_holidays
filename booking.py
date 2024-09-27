import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import date, datetime, timedelta
import calendar
from datetime import timedelta, date
import holidays
import json

# Load Google credentials from Streamlit secrets
creds = st.secrets["GOOGLE_CREDS"]

# Initialize the gspread client using the credentials loaded from secrets
client = gspread.service_account_from_dict(creds)

# Access the specific Google Sheet
sheet = client.open("HOLIDAYS BOOKING SYSTEM APP").sheet1

# Define total holidays (excluding bank holidays)
total_holidays = 28

# Dynamically calculate UK bank holidays using the `holidays` package
def get_bank_holidays(year):
    uk_holidays = holidays.UK(years=year)
    bank_holidays = [date for date in uk_holidays if 'Bank Holiday' in uk_holidays.get(date)]
    return bank_holidays

# Function to get all bookings from Google Sheets
def get_bookings():
    records = sheet.get_all_records()
    bookings = []
    for record in records:
        try:
            bookings.append({
                'name': record['Name'].lower(),
                'start_date': datetime.strptime(record['Start Date'], '%d/%m/%Y').date(),
                'end_date': datetime.strptime(record['End Date'], '%d/%m/%Y').date(),
                'year': int(record['Year'])
            })
        except ValueError:
            st.error("Date format error in Google Sheets. Please ensure dates are in the format 'dd/mm/yyyy'.")
    return bookings

# Function to append a new booking to Google Sheets
def add_booking(name, start_date, end_date, year):
    sheet.append_row([name.lower(), start_date.strftime('%d/%m/%Y'), end_date.strftime('%d/%m/%Y'), year])

# Function to calculate remaining holidays and bank holidays for a person
def calculate_remaining_holidays(bookings, name):
    booked_days = set()
    current_year = datetime.now().year
    bank_holidays = get_bank_holidays(current_year)

    # Gather booked days for the person
    for booking in bookings:
        if booking['name'] == name.lower():
            current_date = booking['start_date']
            while current_date <= booking['end_date']:
                booked_days.add(current_date)
                current_date += timedelta(days=1)

    # Count only personal holiday days (not bank holidays)
    personal_holiday_days = len([day for day in booked_days if day not in bank_holidays])
    remaining_holidays = total_holidays - personal_holiday_days

    # Calculate remaining bank holidays for the current year
    remaining_bank_holidays = len([bh for bh in bank_holidays if bh not in booked_days])

    # Debugging statements
    st.write(f"Total bank holidays this year: {len(bank_holidays)}")
    st.write(f"Bank holidays not yet taken: {remaining_bank_holidays}")
    
    return remaining_holidays, remaining_bank_holidays

# Function to check if a person can book holidays
def can_book_holiday(bookings, name, start_date, end_date):
    remaining_holidays, _ = calculate_remaining_holidays(bookings, name)
    days_requested = (end_date - start_date).days + 1
    booked_days = set()
    
    # Gather already booked dates
    for booking in bookings:
        if booking['name'] == name.lower():
            current_date = booking['start_date']
            while current_date <= booking['end_date']:
                booked_days.add(current_date)
                current_date += timedelta(days=1)
    
    # Include bank holidays in the booked days for accurate checking
    bank_holidays = get_bank_holidays(datetime.now().year)
    booked_days.update(bank_holidays)
    
    # Calculate the number of new unique days to be added
    new_unique_days = 0
    current_date = start_date
    while current_date <= end_date:
        if current_date not in booked_days and current_date not in bank_holidays:  # Don't count bank holidays
            new_unique_days += 1
        current_date += timedelta(days=1)
    
    return remaining_holidays >= new_unique_days

# Function to display holidays in a calendar format
def show_holidays_calendar(name, bookings, year, start_date, end_date):
    bank_holidays = get_bank_holidays(year)

    holidays_taken = set()
    for booking in bookings:
        if booking['name'] == name.lower():
            current_date = booking['start_date']
            while current_date <= booking['end_date']:
                holidays_taken.add(current_date)
                current_date += timedelta(days=1)

    earliest_booking = min((booking['start_date'] for booking in bookings if booking['name'] == name.lower()), default=start_date)
    latest_booking = max((booking['end_date'] for booking in bookings if booking['name'] == name.lower()), default=end_date)

    current_date = earliest_booking

    while current_date <= latest_booking:
        st.write(f"### {calendar.month_name[current_date.month]} {current_date.year}")

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(current_date.year, current_date.month)

        month_display = []
        for week in month_days:
            week_display = []
            for day in week:
                if day == 0:
                    week_display.append(" ")
                else:
                    date_to_check = date(current_date.year, current_date.month, day)
                    if date_to_check in holidays_taken:
                        week_display.append(f'<span class="holiday">{day}</span>')  # Regular holiday styling
                    elif date_to_check in bank_holidays:
                        week_display.append(f'<span class="bank-holiday">{day}</span>')  # Yellow for bank holidays
                    else:
                        week_display.append(str(day))
            month_display.append(week_display)

        html = "<table><tr><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th><th>Sun</th></tr>"
        for week in month_display:
            html += "<tr>"
            for day in week:
                html += f"<td style='text-align: center;'>{day}</td>"
            html += "</tr>"
        html += "</table>"

        st.markdown(html, unsafe_allow_html=True)

        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, 1)
        else:
            current_date = date(current_date.year, current_date.month + 1, 1)

# Styling with custom CSS to match a modern, cleaner design
st.markdown("""
    <style>
    /* Customise the sidebar */
    .sidebar-content {
        background-color: #f7f9fc; /* Light background */
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.05);
    }

    /* Customise input fields */
    .stTextInput, .stDateInput {
        background-color: #ffffff; /* White background */
        border-radius: 8px;
        border: 1px solid #ddd;
        margin-bottom: 20px;
        box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.05);
    }

    /* Customise buttons */
    .stButton button {
        background: linear-gradient(135deg, #3498db, #2980b9); /* Blue gradient */
        color: white;
        border: none;
        border-radius: 20px;
        padding: 10px 20px;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
        transition: 0.3s;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #2980b9, #3498db); /* Hover effect */
        box-shadow: 0px 6px 12px rgba(0, 0, 0, 0.3);
    }

    /* Customise calendar table */
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }
    th, td {
        padding: 10px;
        text-align: center;
        border: 1px solid #ddd;
    }
    th {
        background-color: #3498db; /* Blue for headers */
        color: white;
    }
    td {
        background-color: #ffffff; /* White for calendar cells */
        border-radius: 8px;
    }
    .holiday {
        background-color: #ff7675; /* Highlight holidays */
        color: white;
    }
    .bank-holiday {
        background-color: #ffd700; /* Yellow for bank holidays */
        color: black;
    }

    </style>
""", unsafe_allow_html=True)

# Title
st.title("Holiday Booking System")

# Sidebar for booking holidays
st.sidebar.header("Book Your Holiday")

# Input fields for holiday booking with modern UI design
st.sidebar.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
name = st.sidebar.text_input("👤 Your Name", placeholder="Enter your name...", key="name_input")
start_date = st.sidebar.date_input("📅 Start Date", key="start_date_input")
end_date = st.sidebar.date_input("📅 End Date", key="end_date_input")
year = start_date.year

# Show remaining holidays and booked days for the user
if st.sidebar.button("Check Remaining Holidays"):
    bookings = get_bookings()
    remaining_holidays, remaining_bank_holidays = calculate_remaining_holidays(bookings, name)
    
    if remaining_holidays >= 0:
        st.sidebar.success(f"{name.capitalize()} has {remaining_holidays} holiday days left. {remaining_bank_holidays} bank holidays remaining.")
        show_holidays_calendar(name, bookings, year, start_date, end_date)
    else:
        st.sidebar.error("No holidays remaining.")

# Book holiday button
if st.sidebar.button("Book Holiday"):
    bookings = get_bookings()
    if start_date <= end_date:
        if can_book_holiday(bookings, name, start_date, end_date):
            add_booking(name, start_date, end_date, year)
            st.sidebar.success(f"Holiday booked successfully! {start_date} to {end_date}.")
        else:
            st.sidebar.error("You do not have enough holiday days left to book this period.")
    else:
        st.sidebar.error("Invalid date range!")

st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Calendar format of booked days for the user
st.header("Holiday Calendar")
if st.button("Show Holidays"):
    bookings = get_bookings()
    show_holidays_calendar(name, bookings, year, start_date, end_date)
