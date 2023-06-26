import streamlit as st
import easyocr
import mysql.connector
import io
from PIL import Image
import re
import numpy as np
from PIL import UnidentifiedImageError



# Connect to the MySQL database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Ajith568.',
    database='business_card_details'
)
c = conn.cursor()

# Create a table to store business card data
c.execute('''CREATE TABLE IF NOT EXISTS business_cards
             (id INT AUTO_INCREMENT PRIMARY KEY,
              image MEDIUMBLOB,
              company_name VARCHAR(255),
              card_holder_name VARCHAR(255),
              designation VARCHAR(255),
              mobile_number VARCHAR(255),
              email VARCHAR(255),
              website_url VARCHAR(255),
              area VARCHAR(255),
              city VARCHAR(255),
              state VARCHAR(255),
              pin_code VARCHAR(255))''')

# Load the OCR reader
reader = easyocr.Reader(['en'])

# Global variable for storing fetched data
data = []
company_names = []

# Streamlit application code
def main():
    st.title("Business Card Information Extraction")

    # Upload image
    uploaded_image = st.file_uploader("Upload Business Card Image", type=["jpg", "jpeg", "png"])

    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        image_data = uploaded_image.read()

        # Display the uploaded image
        st.image(image, caption="Uploaded Image", use_column_width=True)

        # Extract information using OCR
        result = extract_information(image)

        # Display extracted information
        display_information(result)

        # Save extracted information to the database
        save_to_database(image_data, result)
    selected_entry_company = st.selectbox("Select Entry to Delete", company_names, key="delete_selectbox")
    selected_entry_id = data[company_names.index(selected_entry_company)][0]
    if st.button("Delete Entry"):
        delete_entry(selected_entry_id)
        st.success("Entry deleted successfully!")

def extract_information(image):
    # Convert the PIL image to bytes
    with io.BytesIO() as output:
        image.save(output, format='PNG')
        image_bytes = output.getvalue()

    # Convert the image bytes to a NumPy array
    np_image = np.array(Image.open(io.BytesIO(image_bytes)))

    # Perform OCR on the image
    result = reader.readtext(np_image)
    # Define regular expressions for pattern matching
    regex_patterns = {
        'name': r'([A-Za-z\s]+)',
        'designation': r'([A-Za-z\s&]+)',
        'mobile': r'(\+\d{3}-\d{3}-\d{4})',
        'email': r'([\w\.-]+@[\w\.-]+)',
        'website': r'(www\.[A-Za-z0-9]+\.[A-Za-z]{2,})',
        'address': r'(\d+ [A-Za-z\s,.]+)',
        'city': r'([A-Za-z]+\s?[A-Za-z]*)',
        'state': r'([A-Za-z]+\s?[A-Za-z]*)',
        'pin': r'(\d{6})'
    }

    # Process the OCR result and extract relevant information
    extracted_info = {}
    for box, text, _ in result:
        for key, pattern in regex_patterns.items():
            match = re.search(pattern, text)
            if match:
                extracted_info[key] = match.group(0)

    return extracted_info


def display_information(result):
    # Display the extracted information in a clean and organized manner
    for key, value in result.items():
        st.write(f"**{key.replace('_', ' ').title()}**: {value}")

def save_to_database(image_data, result):
    try:
        # Prepare the SQL query and parameters
        sql = '''
            INSERT INTO business_cards (image, company_name, card_holder_name, designation,
            mobile_number, email, website_url, area, city, state, pin_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        params = (image_data, result.get('company_name'), result.get('card_holder_name'),
                  result.get('designation'), result.get('mobile_number'), result.get('email'),
                  result.get('website_url'), result.get('area'), result.get('city'),
                  result.get('state'), result.get('pin_code'))

        # Execute the SQL query
        c.execute(sql, params)

        # Commit the changes to the database
        conn.commit()

        st.write("Data saved successfully!")

    except mysql.connector.Error as error:
        st.write("Error while saving data to MySQL:", error)

def display_existing_data():
    global data, company_names  # Declare data and company_names as global variables
    # Retrieve existing data from the database
    c.execute("SELECT * FROM business_cards")
    data = c.fetchall()
    # Populate the company names list
    company_names = [entry[2] for entry in data]

    # Display the existing data
    for row in data:
        image_data = io.BytesIO(row[1])
        try:
            image = Image.open(image_data)
            st.image(image, caption="Business Card Image", use_column_width=True)
        except UnidentifiedImageError as e:
            st.write("")
        else:
            st.write(f"**Company Name**: {row[2]}")
            st.write(f"**Card Holder Name**: {row[3]}")
            st.write(f"**Designation**: {row[4]}")
            st.write(f"**Mobile Number**: {row[5]}")
            st.write(f"**Email**: {row[6]}")
            st.write(f"**Website URL**: {row[7]}")
            st.write(f"**Area**: {row[8]}")
            st.write(f"**City**: {row[9]}")
            st.write(f"**State**: {row[10]}")
            st.write(f"**Pin Code**: {row[11]}")
            st.write("---")

def delete_entry(entry_id):
    try:
        # Delete the selected entry from the database
        c.execute("DELETE FROM business_cards WHERE id=%s", (entry_id,))

        # Commit the changes to the database
        conn.commit()
    except mysql.connector.Error as error:
        st.write("Error while deleting entry from MySQL:", error)

if __name__ == '__main__':
    main()
    display_existing_data()
