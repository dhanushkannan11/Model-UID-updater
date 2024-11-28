import streamlit as st
import pandas as pd
from packages.main import *
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import boto3
import string
import random
import time
import os

service_name = "dynamodb"
region = os.getenv('AWS_REGION')
table_name = os.getenv('AWS_TABLE_NAME')
client = None
access_id = os.getenv('AWS_ACCESS_ID')
access_key = os.getenv('AWS_ACCESS_KEY')

st.sidebar.page_link('Generate_UID.py', label='🆔 Generate UID')
st.sidebar.page_link('pages/1_📙_Update_Database.py', label='📙 Update Database')
st.sidebar.page_link('pages/2_📈_Visualize_Data.py', label='📈 Visualize Data')


# @st.cache_data
def fetch_data():
    """

    :return: table items as a list
    """
    global client
    client = DynamoDB(access_id, access_key, service_name, region, table_name)

    # connect to DynamoDB
    client.connect()

    # get models table
    table = client.get_table()
    return table["Items"]


def check_uid(uid):
    df = pd.DataFrame(fetch_data(), index=None)
    if uid in list(df.UID):
        st.success("NeuraBubble UID is Already in the Database")
        uid_df = df[df.UID == uid]
        uid_df.drop("usages", axis=1, inplace=True)
        st.table(uid_df.T)

        return True
    else:
        st.warning("NeuraBubble UID Does Not Exist in the Database!")
        return False


@st.cache_data
def validate_uid(uid):
    try:
        assert len(uid) == 6
        return True

    except AssertionError:
        if len(uid) == 0:
            st.warning("Enter UID!")
        else:
            st.warning("UID Should Contain 6 Characters!")

def upload_data(item, table_name, region, access_id, access_key):
    """
    Uploads a new record to DynamoDB table.
    :param item: a dictionary representing the new record
    :return: response from DynamoDB put_item method
    """
    # global client
    # access_id, access_key = load_token()
    # client = DynamoDB(access_id, access_key, service_name, region, table_name)
    # # connect to DynamoDB
    # client.connect()
    # # upload item
    # response = client.put_item(item)
    # return response
    try:
        # Create a DynamoDB client
        client = boto3.client('dynamodb', aws_access_key_id=access_id, aws_secret_access_key=access_key, region_name=region)

        # Upload the item to the DynamoDB table
        response = client.put_item(TableName=table_name, Item=item)
        return response

    except NoCredentialsError:
        print("Credentials not available.")
    except PartialCredentialsError:
        print("Incomplete credentials provided.")
    except Exception as e:
        print(f"An error occurred: {e}")


def add_details(uid, nb_id, raptured, shipped, destination, usage_count, usages, status):
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
        'raptured': {'BOOL': raptured == 'Yes'},
        'shippedStatus': {'BOOL': shipped == 'Yes'},
        'orderStatus' : {'S': status},
        'usageCount': {'N': str(usage_count)},
        'usages': {'L': formatted_usages}
    }
    return details_dict

def clear_home_page_state():
    time.sleep(2)
    st.session_state.clear()
    st.rerun()

def data_form(uid):
    nb_form = st.form("nb_id", clear_on_submit=True)
    aneurysm_type = nb_form.selectbox("Type of Aneurysm", ["MCA", "ICA", "PCOM", "ACOM", "BA", "TU"])
    aneurysm_side = nb_form.selectbox("Aneurysm Side", ["R", "L"])
    anonymized_id = nb_form.text_input("Anonymized ID", value="T04", help="(T04, T13, T23)")
    nb_number = nb_form.text_input("NeuraBubble Number", value="001", help="(001, 010)")
    raptured = nb_form.radio("Is the NeuraBubble Ruptured?", ["Yes", "No"], index=1)
    shipped = nb_form.radio("Is the NeuraBubble Shipped?", ["Yes", "No"], index=1)
    status = nb_form.text_input("Order Status", help = "Received/in transit")

    usage_count = nb_form.number_input("Enter the NeuraBubble Usage Count", value=0, min_value=0,
                                       max_value=5)

    shipping_address = nb_form.text_input("Enter Shipping Destination")
    nb_id = f"{aneurysm_type} {aneurysm_side} {anonymized_id} {nb_number}"
    usages = [
        {
            'systemID': '',
            'location': '',
            'userEmailID': '',
            'timestamp': 0
        }
    ]
    nb_form.warning("Confirm the Accuracy of the Details before Clicking Submit!")
    nb_id_status = nb_form.form_submit_button("Submit")

    
    json_data = add_details(uid, nb_id, raptured, shipped, shipping_address, usage_count, usages, status)
   
    if nb_id_status:
        try:
            response = upload_data(json_data, table_name, region, access_id, access_key)
            # print(response)
            st.success("Record uploaded successfully!")
        except NoCredentialsError:
            st.error("Credentials not available.")
        except PartialCredentialsError:
            st.error("Incomplete credentials provided.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
        st.success("Details Saved!")
        clear_home_page_state()
        # print(json_data)
        details, usages = get_tables(json_data)
        # st.table(pd.DataFrame(details, index=["Details"]))
        # if details["usageCount"] != 0:
        #     st.table(pd.DataFrame(usages))


def get_tables(json_data):
    json_data_copy = json_data.copy()
    usages = json_data_copy.pop("usages")

    return json_data_copy, usages

def generate_uid():
    df = pd.DataFrame(fetch_data(), index=None)
    uid_list = df.UID.to_list()

    # Define the character set (A-Z, a-z, 0-9)
    characters = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    # Generate a random 6-character UID
    uid = ''.join(random.choices(characters, k=6))

    while(uid in uid_list):
        characters = string.ascii_letters + string.digits
        uid = ''.join(random.choices(characters, k=6))

    return uid


def main():
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "home"  # Default active page

    # If the active page is changed, clear home page state
    if st.session_state["active_page"] != "home":
        clear_home_page_state()

    # Mark current page as active
    st.session_state["active_page"] = "home"

    st.title("UID Generator")

    # print(st.session_state.keys())
    # print(st.session_state["current_uid"])
    # st.session_state.clear()
    # st.session_state["show_form"] = ""
    # st.session_state["current_uid"] = ""

    # Initialize session state for UID and form display
    if "current_uid" not in st.session_state:
        st.session_state["current_uid"] = None
    if "show_form" not in st.session_state:
        st.session_state["show_form"] = False

    # Generate UID and display options
    if st.button("Generate UID", key="generate_uid_button"):
        uid = generate_uid()  # Call the UID generation function
        st.session_state["current_uid"] = uid  # Save UID in session state
        st.session_state["show_form"] = False  # Reset form visibility
        st.success(f"Generated UID: {uid}")
        if validate_uid(uid) and not check_uid(uid):
            # print(st.session_state["current_uid"])
            # st.warning(f"NeuraBubble UID Does Not Exist in the Database!")
            st.session_state["show_form"] = True  # Allow form display

    # Check if a UID has been generated
    if st.session_state["current_uid"]:
        # st.success(f"Generated UID: {st.session_state['current_uid']}")

        # Display the radio button to decide whether to show the form
        if st.session_state["show_form"]:            
            add_status = st.radio(
                f'Do you want to update the Model `{st.session_state["current_uid"]}` details?',
                ["Yes", "No"],
                index=1,
            )
            if add_status == "Yes":
                # Display the form
                st.success(f"Generated UID: {st.session_state['current_uid']}")
                st.subheader("NeuraBubble Details")
                data_form(st.session_state["current_uid"])
            elif add_status == "No":
                # st.info("You chose not to update the details.")
                return;

    else:
        st.info("Click the button to generate a UID.")


if __name__ == "__main__":
    # add_icons_to_menu()
    main()
    generate_uid()

    # df = pd.DataFrame(fetch_data(), index=None)
    # uid_list = df.UID.to_list()
    # # print(uid_list)

    # unique_id = generate_uid()
    # while(unique_id in uid_list):
    #     print("1st Generated UID:", unique_id)
    #     unique_id = generate_uid()

    # print("Generated UID:", unique_id)