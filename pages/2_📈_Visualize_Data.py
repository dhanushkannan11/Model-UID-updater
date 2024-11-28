import streamlit as st
import pandas as pd
from packages.main import *
import plotly.express as px
import plotly.graph_objects as go

service_name = "dynamodb"
region = "eu-central-1"
table_name = "NeuraBubbleUID_Validator"
access_id = os.getenv('AWS_ACCESS_ID')
access_key = os.getenv('AWS_ACCESS_KEY')

st.sidebar.page_link('Generate_UID.py', label='🆔 Generate UID')
st.sidebar.page_link('pages/1_📙_Update_Database.py', label='📙 Update Database')
st.sidebar.page_link('pages/2_📈_Visualize_Data.py', label='📈 Visualize Data')

def main():
    st.session_state["active_page"] = "page2"
    st.title('NeuraBubbles Data')
    side_bar()


# @st.cache_data
def fetch_data():
    client = DynamoDB(access_id, access_key, service_name, region, table_name)

    # connect to DynamoDB
    client.connect()

    # get models table
    table = client.get_table()
    return table["Items"]


def side_bar():
    data = fetch_data()

    clean_df, usages_df = pre_process_data(data)
    clean_df['usageCount'] = pd.to_numeric(clean_df['usageCount'], errors='coerce').fillna(0).astype(int)

    st.sidebar.header("Filters")
    anon_id = st.sidebar.button("Anonymized ID")
    side = st.sidebar.button("Aneurysm Side")
    aneurysm_type = st.sidebar.button("Types of Aneurysm")
    ruptured = st.sidebar.button("Ruptured")
    shipped = st.sidebar.button("Shipped Status")
    shipped_location = st.sidebar.button("Shipped Location")
    usage_count = st.sidebar.button("Usage Count")

    st.sidebar.button("No Filters")

    if ruptured:
        st.subheader("Ruptured NeuraBubbles")
        st.bar_chart(clean_df["raptured"].value_counts())
    elif shipped:
        st.subheader("NeuraBubbles Shipping Status")
        st.bar_chart(clean_df["shippedStatus"].value_counts())
    elif usage_count:
        st.subheader("NeuraBubbles Usage Count")
        st.bar_chart(clean_df["usageCount"].value_counts())
    elif aneurysm_type:
        st.subheader("NeuraBubbles Aneurysm Type")
        st.bar_chart(clean_df["Aneurysm_Type"].value_counts())
    elif side:
        st.subheader("Aneurysm Side of the Head")
        fig = go.Figure(data=[go.Pie(labels=clean_df["Aneurysm_Side"].unique(), values=clean_df["Aneurysm_Side"].value_counts())])
        st.plotly_chart(fig)
    elif anon_id:
        st.subheader("Patient Anonymized ID")
        st.bar_chart(clean_df["Anonymized_ID"].value_counts())
    elif shipped_location:
        st.subheader("Shipping Destination")
        shipped_df = clean_df["destinationShipped"].value_counts()
        fig = go.Figure(
            data=[go.Pie(values=shipped_df.values, labels=list(shipped_df.index))])
        st.plotly_chart(fig)
        st.bar_chart(clean_df["destinationShipped"].value_counts())

    else:
        st.dataframe(clean_df)


@st.cache_data
def pre_process_data(json_data):
    df = pd.DataFrame(json_data)

    df[["Aneurysm_Type", "Aneurysm_Side", "Anonymized_ID", "NeuraBubble_ID"]] = df["ID"].str.split(" ", expand=True)

    usages_df = df[["usages", "UID"]]

    df.drop(["ID", "usages"], inplace=True, axis=1)

    return df, usages_df


# TODO: Complete plot function
def plot(df, group_by):
    features = df.columns.pop()

    st.bar_chart(df.groupby(group_by)["Anonymized_ID"])


if __name__ == "__main__":
    main()
