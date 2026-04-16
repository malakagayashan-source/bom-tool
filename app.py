import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.title("BOM Explosion & Cost Tool (Fixed Version)")

file = st.file_uploader("Upload BOM file", type=["csv", "xlsx"])

if file:
    # =========================
    # LOAD FILE
    # =========================
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    st.write("### Raw Data")
    st.dataframe(df)

    # =========================
    # CLEAN COLUMNS
    # =========================
    df.columns = df.columns.str.strip()

    df = df.rename(columns={
        "Part No.": "PartNo",
        "Part description": "Description",
        "Quantity": "Quantity",
        "Approximate cost": "ApproxCost",
        "Sub-assembly cost": "SubCost"
    })

    # =========================
    # CLEAN DATA (CRITICAL FIX)
    # =========================
    df["PartNo"] = df["PartNo"].astype(str).str.strip()

    # Remove invalid rows
    df = df[df["PartNo"].notna()]
    df = df[df["PartNo"] != ""]
    df = df[df["PartNo"] != "nan"]

    # Keep only valid hierarchical numbers (like 1, 1.1, 1.1.1)
    df = df[df["PartNo"].str.match(r'^\d+(\.\d+)*$')]

    # Convert numbers
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(1)
    df["ApproxCost"] = pd.to_numeric(df["ApproxCost"], errors="coerce")
    df["SubCost"] = pd.to_numeric(df["SubCost"], errors="coerce")

    # =========================
    # COMBINE COST
    # =========================
    df["UnitPrice"] = df["ApproxCost"].fillna(df["SubCost"]).fillna(0)

    # =========================
    # SORT
    # =========================
    df = df.sort_values("PartNo")

    # =========================
    # BUILD LOOKUP
    # =========================
    qty_dict = dict(zip(df["PartNo"], df["Quantity"]))

    # =========================
    # BOM EXPLOSION (FIXED)
    # =========================
    def explode_qty(part):
        levels = part.split(".")
        total = 1
        path = []

        for i in range(len(levels)):
            node = ".".join(levels[:i+1])
            if node in qty_dict:
                total *= qty_dict[node]

        return total

    df["FinalQty"] = df["PartNo"].apply(explode_qty)

    # =========================
    # STRONG PARENT DETECTION
    # =========================
    part_set = set(df["PartNo"])

    def is_parent(part):
        prefix = part + "."
        for p in part_set:
            if p.startswith(prefix):
                return True
        return False

    df["IsParent"] = df["PartNo"].apply(is_parent)

    # =========================
    # KEEP ONLY LEAF NODES
    # =========================
    leaf_df = df[df["IsParent"] == False].copy()

    # =========================
    # COST CALCULATION
    # =========================
    leaf_df["TotalCost"] = leaf_df["FinalQty"] * leaf_df["UnitPrice"]

    st.write("### Leaf Parts Only (Correct)")
    st.dataframe(leaf_df[["PartNo","Description","FinalQty","UnitPrice","TotalCost"]])

    # =========================
    # CONSOLIDATION
    # =========================
    summary = leaf_df.groupby(["PartNo","Description"]).agg({
        "FinalQty":"sum",
        "UnitPrice":"max",
        "TotalCost":"sum"
    }).reset_index()

    summary = summary.rename(columns={"FinalQty":"Quantity"})

    st.write("### ✅ Final Consolidated BOM")
    st.dataframe(summary)

    # =========================
    # DOWNLOAD
    # =========================
    output = BytesIO()
    summary.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    st.download_button(
        "Download Excel",
        data=output,
        file_name="Consolidated_BOM.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
