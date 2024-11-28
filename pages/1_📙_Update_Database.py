import streamlit as st
import pandas as pd
from packages.main import *
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import boto3
import time 

service_name = "dynamodb"
region = "eu-central-1"
table_name = "NeuraBubbleUID_Validator"
client = None
access_id = os.getenv('AWS_ACCESS_ID')
access_key = os.getenv('AWS_ACCESS_KEY')

st.sidebar.page_link('Generate_UID.py', label='🆔 Generate UID')
st.sidebar.page_link('pages/1_📙_Update_Database.py', label='📙 Update Database')
st.sidebar.page_link('pages/2_📈_Visualize_Data.py', label='📈 Visualize Data')

def main():
    """

    :return:
    """
    st.session_state["active_page"] = "page1"
    uid = st.text_input("Enter NeuraBubble UID", value="")
    if validate_uid(uid):
        if not check_uid(uid):
            # add_status = st.radio(f'Do you want to Update NeuraBubble `{uid}` details?', ["Yes", 'No'], index=1)
            # if add_status == "Yes":
            #     st.subheader("NeuraBubble Details")

            #     data_form(uid)

            # if add_status == "Yes":
            #     pass
            return;
        else:
            add_status = st.radio(f'Do you want to Update NeuraBubble `{uid}` details?', ["Yes", 'No'], index=1)
            if add_status == "Yes":
                st.subheader("NeuraBubble Details")
                data_form(uid)

            if add_status == "Yes":
                pass
            return;


# @st.cache_data
def fetch_data():
    """

    :return: table items as a list
    """
    global client

    print("access_id : ", access_id)
    print("access_key : ", access_key)
    client = DynamoDB(access_id, access_key, service_name, region, table_name)

    # connect to DynamoDB
    client.connect()

    # get models table
    table = client.get_table()
    return table["Items"]


def check_uid(uid):
    df = pd.DataFrame(fetch_data(), index=None)
    if uid in list(df.UID):
        # st.success("NeuraBubble UID is Already in the Database")
        uid_df = df[df.UID == uid]
        uid_df.drop("usages", axis=1, inplace=True)
        st.table(uid_df.T)
        st.session_state["uid_df"] = uid_df
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
    st.markdown('<meta http-equiv="refresh" content="0">', unsafe_allow_html=True)

def data_form(uid):
    currentAneurysmType = st.session_state["uid_df"]['ID'].iloc[0].split(' ')[0]
    currentAneurysmSide = st.session_state["uid_df"]['ID'].iloc[0].split(' ')[1]
    currentID = st.session_state["uid_df"]['ID'].iloc[0].split(' ')[2]
    currentModelNumber = st.session_state["uid_df"]['ID'].iloc[0].split(' ')[3]
    currentRuptureStatus = st.session_state["uid_df"]['raptured'].iloc[0]
    currentShippingStatus = st.session_state["uid_df"]['shippedStatus'].iloc[0]
    currentOrderStatus = st.session_state["uid_df"]['orderStatus'].iloc[0]
    currentUsageCount = st.session_state["uid_df"]['usageCount'].iloc[0]
    currentDestination = st.session_state["uid_df"]['destinationShipped'].iloc[0]

    nb_form = st.form("nb_id", clear_on_submit=True)
    options = ["MCA", "ICA", "PCOM", "ACOM", "BA", "TU"]
    default_index = options.index(currentAneurysmType)
    aneurysm_type = nb_form.selectbox("Type of Aneurysm", options, index = default_index)
    aneurysm_side = nb_form.selectbox("Aneurysm Side", ["R", "L"], index=0 if currentAneurysmSide == "R" else 1)
    anonymized_id = nb_form.text_input("Anonymized ID", value=currentID)
    nb_number = nb_form.text_input("NeuraBubble Number", value=currentModelNumber)
    raptured = nb_form.radio("Is the NeuraBubble Ruptured?", ["Yes", "No"], index=0 if currentRuptureStatus else 1)
    shipped = nb_form.radio("Is the NeuraBubble Shipped?", ["Yes", "No"], index=0 if currentShippingStatus else 1)
    status = nb_form.text_input("Order Status", value = currentOrderStatus)

    usage_count = nb_form.number_input("Enter the NeuraBubble Usage Count", value=int(currentUsageCount), min_value=0,
                                       max_value=5)
    shipping_address = nb_form.text_input("Enter Shipping Destination", value = currentDestination)

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
            clear_home_page_state()
        except NoCredentialsError:
            st.error("Credentials not available.")
        except PartialCredentialsError:
            st.error("Incomplete credentials provided.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
        st.success("Details Saved!")
        # print(json_data)
        details, usages = get_tables(json_data)
        # st.table(pd.DataFrame(details, index=["Details"]))
        # if details["usageCount"] != 0:
        #     st.table(pd.DataFrame(usages))

        

def get_tables(json_data):
    json_data_copy = json_data.copy()
    usages = json_data_copy.pop("usages")

    return json_data_copy, usages


if __name__ == "__main__":
    main()
