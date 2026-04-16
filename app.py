import streamlit as st
import pandas as pd

st.title("BOM Cost Consolidation Tool")

file = st.file_uploader("Upload BOM file", type=["csv","xlsx"])

if file:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    st.write("### Raw Data")
    st.dataframe(df)

    # Clean columns
    df.columns = df.columns.str.strip()

    # Rename based on YOUR file
    df = df.rename(columns={
        "Part No.": "PartNo",
        "Part description": "Description",
        "Quantity": "Quantity",
        "Approximate cost": "ApproxCost",
        "Sub-assembly cost": "SubCost"
    })

    # Convert numbers
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["ApproxCost"] = pd.to_numeric(df["ApproxCost"], errors="coerce")
    df["SubCost"] = pd.to_numeric(df["SubCost"], errors="coerce")

    # ✅ Combine costs correctly
    df["UnitPrice"] = df["ApproxCost"].fillna(df["SubCost"]).fillna(0)

    # Calculate total
    df["TotalCost"] = df["Quantity"] * df["UnitPrice"]

    # Remove empty parts
    df = df[df["PartNo"].notna()]

    # Consolidate
    summary = df.groupby(["PartNo","Description"]).agg({
        "Quantity":"sum",
        "UnitPrice":"max",
        "TotalCost":"sum"
    }).reset_index()

    st.write("### ✅ Consolidated BOM")
    st.dataframe(summary)

    # Download
    summary.to_excel("Consolidated_BOM.xlsx", index=False)

    with open("Consolidated_BOM.xlsx","rb") as f:
        st.download_button("Download Excel", f, "Consolidated_BOM.xlsx")
