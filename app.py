import streamlit as st
import pandas as pd

st.title("BOM Cost Tool")

file = st.file_uploader("Upload BOM file", type=["csv","xlsx"])

if file:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    df.columns = df.columns.str.strip()

    # Rename (edit if needed)
    df = df.rename(columns={
        "Part Number": "PartNo",
        "Description": "Description",
        "Qty": "Quantity",
        "Unit Cost": "UnitPrice"
    })

    if all(col in df.columns for col in ["PartNo","Description","Quantity","UnitPrice"]):
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
        df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce").fillna(0)

        df["TotalCost"] = df["Quantity"] * df["UnitPrice"]

        summary = df.groupby(["PartNo","Description"]).agg({
            "Quantity":"sum",
            "UnitPrice":"max",
            "TotalCost":"sum"
        }).reset_index()

        st.write("### Result")
        st.dataframe(summary)

        summary.to_excel("result.xlsx", index=False)

        with open("result.xlsx","rb") as f:
            st.download_button("Download Excel", f, "result.xlsx")
    else:
        st.error("Column names not matching")
