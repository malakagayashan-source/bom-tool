import streamlit as st
import pandas as pd
from io import BytesIO

st.title("BOM Explosion & Cost Tool")

file = st.file_uploader("Upload BOM file", type=["csv","xlsx"])

if file:
    # Load file
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    st.write("### Raw Data")
    st.dataframe(df)

    # Clean columns
    df.columns = df.columns.str.strip()

    # Rename (based on your file)
    df = df.rename(columns={
        "Part No.": "PartNo",
        "Part description": "Description",
        "Quantity": "Quantity",
        "Approximate cost": "ApproxCost",
        "Sub-assembly cost": "SubCost"
    })

    # Convert types
    df["PartNo"] = df["PartNo"].astype(str)
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["ApproxCost"] = pd.to_numeric(df["ApproxCost"], errors="coerce")
    df["SubCost"] = pd.to_numeric(df["SubCost"], errors="coerce")

    # Combine cost columns
    df["UnitPrice"] = df["ApproxCost"].fillna(df["SubCost"]).fillna(0)

    # Sort by hierarchy
    df = df.sort_values("PartNo")

    # Create lookup for quantities
    qty_dict = dict(zip(df["PartNo"], df["Quantity"]))

    # Function to calculate exploded quantity
    def get_total_qty(part):
        levels = part.split(".")
        total = 1
        for i in range(len(levels)):
            parent = ".".join(levels[:i+1])
            if parent in qty_dict:
                total *= qty_dict[parent]
        return total

    # Apply explosion
    df["FinalQty"] = df["PartNo"].apply(get_total_qty)

    # Detect parent rows
    all_parts = df["PartNo"].tolist()

    def is_parent(part):
        prefix = part + "."
        return any(p.startswith(prefix) for p in all_parts if p != part)

    df["IsParent"] = df["PartNo"].apply(is_parent)

    # Remove parents → keep only leaf parts
    df = df[df["IsParent"] == False]

    # Calculate total cost using exploded qty
    df["TotalCost"] = df["FinalQty"] * df["UnitPrice"]

    st.write("### After BOM Explosion")
    st.dataframe(df[["PartNo","Description","FinalQty","UnitPrice","TotalCost"]])

    # Consolidate
    summary = df.groupby(["PartNo","Description"]).agg({
        "FinalQty":"sum",
        "UnitPrice":"max",
        "TotalCost":"sum"
    }).reset_index()

    summary = summary.rename(columns={"FinalQty":"Quantity"})

    st.write("### ✅ Final Consolidated BOM")
    st.dataframe(summary)

    # Download (safe method)
    output = BytesIO()
    summary.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label="Download Excel",
        data=output,
        file_name="Consolidated_BOM.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
