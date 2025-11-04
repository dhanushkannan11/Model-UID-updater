# import streamlit as st
# import pandas as pd
# from packages.main import *
# from botocore.exceptions import NoCredentialsError, PartialCredentialsError
# import boto3
# import time 
# from dotenv import load_dotenv
# load_dotenv()

# service_name = "dynamodb"
# region = os.getenv('AWS_REGION')
# table_name = os.getenv('AWS_TABLE_NAME')
# client = None
# access_id = os.getenv('AWS_ACCESS_ID')
# access_key = os.getenv('AWS_ACCESS_KEY')

# st.sidebar.page_link('Generate_UID.py', label='🆔 Generate UID')
# st.sidebar.page_link('pages/1_📙_Update_Database.py', label='📙 Update Database')
# st.sidebar.page_link('pages/2_📈_Visualize_Data.py', label='📈 Visualize Data')
# st.sidebar.page_link('pages/3_📃_Generate_UID_List.py', label='📃 Generate UID List')

import streamlit as st
import pandas as pd
from packages.main import *
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import boto3
import string
import random
import time
import os
from dotenv import load_dotenv
from io import BytesIO

load_dotenv()

service_name = "dynamodb"
region = os.getenv('AWS_REGION')
table_name = os.getenv('AWS_TABLE_NAME')
client = None
access_id = os.getenv('AWS_ACCESS_ID')
access_key = os.getenv('AWS_ACCESS_KEY')

st.sidebar.page_link('Generate_UID.py', label='🆔 Generate UID')
st.sidebar.page_link('pages/1_📙_Update_Database.py', label='📙 Update Database')
st.sidebar.page_link('pages/2_📈_Visualize_Data.py', label='📈 Visualize Data')
st.sidebar.page_link('pages/3_📃_Generate_UID_List.py', label='📃 Generate UID List')


@st.cache_data
def fetch_data():
    """
    Fetch all items from DynamoDB table
    :return: table items as a list
    """
    global client
    client = DynamoDB(access_id, access_key, service_name, region, table_name)
    
    # connect to DynamoDB
    client.connect()
    
    # get models table
    table = client.get_table()
    return table["Items"]


def generate_uid(existing_uids):
    """
    Generate a unique 6-character UID
    :param existing_uids: list of existing UIDs to avoid duplicates
    :return: unique UID string
    """
    characters = string.ascii_letters + string.digits
    uid = ''.join(random.choices(characters, k=6))
    
    while uid in existing_uids:
        uid = ''.join(random.choices(characters, k=6))
        
    return uid


def upload_data(item, table_name, region, access_id, access_key):
    """
    Uploads a new record to DynamoDB table.
    :param item: a dictionary representing the new record
    :return: response from DynamoDB put_item method
    """
    try:
        client = boto3.client('dynamodb', 
                            aws_access_key_id=access_id, 
                            aws_secret_access_key=access_key, 
                            region_name=region)
        
        response = client.put_item(TableName=table_name, Item=item)
        return response
        
    except NoCredentialsError:
        raise Exception("Credentials not available.")
    except PartialCredentialsError:
        raise Exception("Incomplete credentials provided.")
    except Exception as e:
        raise Exception(f"An error occurred: {e}")


def add_details(uid, nb_id, raptured, shipped, destination, usage_count, usages, status):
    """
    Format details into DynamoDB item structure
    """
    formatted_usages = [
        {
            'M': {
                'systemID': {'S': usage.get('systemID', '')},
                'location': {'S': usage.get('location', '')},
                'userEmailID': {'S': usage.get('userEmailID', '')},
                'timestamp': {'N': str(usage.get('timestamp', 0))}
            }
        } for usage in usages
    ]
    
    details_dict = {
        'UID': {'S': uid},
        'destinationShipped': {'S': destination},
        'ID': {'S': nb_id},
        'raptured': {'BOOL': raptured},
        'shippedStatus': {'BOOL': shipped},
        'orderStatus': {'S': status},
        'usageCount': {'N': str(usage_count)},
        'usages': {'L': formatted_usages}
    }
    return details_dict


def validate_nb_number(nb_num):
    """
    Validate and format NeuraBubble number to 3 digits
    :param nb_num: input number
    :return: formatted 3-digit string or None if invalid
    """
    try:
        num = int(nb_num)
        if num < 0 or num > 999:
            return None
        return str(num).zfill(3)
    except ValueError:
        return None


def create_excel_download(data_list):
    """
    Create Excel file from list of records
    :param data_list: list of dictionaries containing UID and NeuraBubble details
    :return: BytesIO object containing Excel file
    """
    df = pd.DataFrame(data_list)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Generated UIDs')
    output.seek(0)
    return output


def clear_page_state():
    """Clear session state and rerun"""
    time.sleep(2)
    # Clear only the form-related states, not the active_page
    keys_to_clear = [k for k in st.session_state.keys() if k != 'active_page']
    for key in keys_to_clear:
        del st.session_state[key]
    st.rerun()


def main():
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "generate_list"
    
    st.session_state["active_page"] = "generate_list"
    
    st.title("Generate UID List")
    st.subheader("NeuraBubble Details")
    
    # Create form
    with st.form("bulk_uid_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            aneurysm_type = st.selectbox("Type of Aneurysm", 
                                        ["MCA", "ICA", "PCOM", "ACOM", "BA", "TU"])
            aneurysm_side = st.selectbox("Aneurysm Side", ["R", "L"])
            anonymized_id = st.text_input("Anonymized ID", value="T04", 
                                         help="(T04, T13, T23)")
        
        with col2:
            raptured = st.radio("Is the NeuraBubble Ruptured?", ["Yes", "No"], index=1)
            shipped = st.radio("Is the NeuraBubble Shipped?", ["Yes", "No"], index=1)
            status = st.text_input("Order Status", value="Yet to ship", 
                                  help="Received/in transit/Yet to ship")
        
        st.markdown("#### NeuraBubble Number Range")
        col3, col4 = st.columns(2)
        
        with col3:
            nb_number_start = st.text_input("Start Number", value="001", 
                                           help="Enter 3-digit number (e.g., 001)")
        with col4:
            nb_number_end = st.text_input("End Number", value="005", 
                                         help="Enter 3-digit number (e.g., 005)")
        
        usage_count = st.number_input("Enter the NeuraBubble Usage Count", 
                                     value=0, min_value=0, max_value=5)
        
        shipping_address = st.text_input("Enter Shipping Destination")
        
        st.warning("⚠️ Confirm the Accuracy of the Details before Clicking Generate!")
        
        submit_button = st.form_submit_button("Generate", use_container_width=True)
    
    # Process form submission
    if submit_button:
        # Validate NeuraBubble numbers
        start_num_formatted = validate_nb_number(nb_number_start)
        end_num_formatted = validate_nb_number(nb_number_end)
        
        if start_num_formatted is None:
            st.error("❌ Invalid Start Number! Please enter a valid number (0-999).")
            return
        
        if end_num_formatted is None:
            st.error("❌ Invalid End Number! Please enter a valid number (0-999).")
            return
        
        start_num = int(start_num_formatted)
        end_num = int(end_num_formatted)
        
        if start_num > end_num:
            st.error("❌ Start Number must be less than or equal to End Number!")
            return
        
        # if not shipping_address.strip():
        #     st.error("❌ Please enter a shipping destination!")
        #     return
        
        # Calculate number of records to generate
        num_records = end_num - start_num + 1
        
        if num_records > 100:
            st.error("❌ Cannot generate more than 100 UIDs at once. Please reduce the range.")
            return
        
        # Fetch existing UIDs
        with st.spinner("Fetching existing UIDs from database..."):
            try:
                df = pd.DataFrame(fetch_data(), index=None)
                existing_uids = df.UID.to_list() if not df.empty else []
            except Exception as e:
                st.error(f"❌ Error fetching data: {e}")
                return
        
        # Generate records
        generated_records = []
        usages = [{
            'systemID': '',
            'location': '',
            'userEmailID': '',
            'timestamp': 0
        }]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        raptured_bool = (raptured == 'Yes')
        shipped_bool = (shipped == 'Yes')
        
        for i, nb_num in enumerate(range(start_num, end_num + 1)):
            # Generate unique UID
            uid = generate_uid(existing_uids)
            existing_uids.append(uid)  # Add to list to avoid duplicates in current batch
            
            # Format NeuraBubble ID
            nb_number_str = str(nb_num).zfill(3)
            nb_id = f"{aneurysm_type} {aneurysm_side} {anonymized_id} {nb_number_str}"
            
            # Create DynamoDB item
            item = add_details(uid, nb_id, raptured_bool, shipped_bool, 
                             shipping_address, usage_count, usages, status)
            
            # Upload to DynamoDB
            try:
                status_text.text(f"Uploading record {i+1}/{num_records}: {nb_id}")
                upload_data(item, table_name, region, access_id, access_key)
                
                # Store for Excel export
                generated_records.append({
                    'UID': uid,
                    'NeuraBubble_ID': nb_id,
                    'Aneurysm_Type': aneurysm_type,
                    'Aneurysm_Side': aneurysm_side,
                    'Anonymized_ID': anonymized_id,
                    'NeuraBubble_Number': nb_number_str,
                    'Ruptured': raptured,
                    'Shipped': shipped,
                    'Order_Status': status,
                    'Shipping_Destination': shipping_address,
                    'Usage_Count': usage_count
                })
                
                progress_bar.progress((i + 1) / num_records)
                
            except Exception as e:
                st.error(f"❌ Error uploading record {nb_id}: {e}")
                progress_bar.empty()
                status_text.empty()
                return
        
        progress_bar.empty()
        status_text.empty()
        
        # Show success message
        st.success(f"✅ Successfully generated and uploaded {num_records} records!")
        
        # Display generated records
        st.subheader("Generated Records")
        display_df = pd.DataFrame(generated_records)
        st.dataframe(display_df, use_container_width=True)
        
        # Create Excel file for download
        excel_file = create_excel_download(generated_records)
        
        # Generate filename
        filename = f"UIDs_{aneurysm_type}_{aneurysm_side}_{anonymized_id}_{start_num_formatted}-{end_num_formatted}.xlsx"
        
        st.download_button(
            label="📥 Download Excel File",
            data=excel_file,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.info("💡 You can now download the generated UIDs as an Excel file using the button above.")


if __name__ == "__main__":
    main()