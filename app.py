import streamlit as st
import pandas as pd
from io import BytesIO

st.title("BOM Explosion & Cost Consolidation Tool")

file = st.file_uploader("Upload BOM file", type=["csv", "xlsx"])

if file:
    # =========================
    # LOAD FILE
    # =========================
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    st.write("### Raw Data Preview")
    st.dataframe(df)

    # =========================
    # CLEAN & RENAME COLUMNS
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
    # TYPE CONVERSION
    # =========================
    df["PartNo"] = df["PartNo"].astype(str).str.strip()
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["ApproxCost"] = pd.to_numeric(df["ApproxCost"], errors="coerce")
    df["SubCost"] = pd.to_numeric(df["SubCost"], errors="coerce")

    # =========================
    # COMBINE COST
    # =========================
    df["UnitPrice"] = df["ApproxCost"].fillna(df["SubCost"]).fillna(0)

    # Remove empty rows
    df = df[df["PartNo"] != ""]
    df = df[df["PartNo"].notna()]

    # =========================
    # SORT BY STRUCTURE
    # =========================
    df = df.sort_values("PartNo")

    # =========================
    # BUILD QUANTITY LOOKUP
    # =========================
    qty_dict = dict(zip(df["PartNo"], df["Quantity"]))

    # =========================
    # BOM EXPLOSION (MULTIPLY LEVELS)
    # =========================
    def get_total_qty(part):
        parts = part.split(".")
        total = 1
        for i in range(len(parts)):
            parent = ".".join(parts[:i+1])
            if parent in qty_dict:
                total *= qty_dict[parent]
        return total

    df["FinalQty"] = df["PartNo"].apply(get_total_qty)

    # =========================
    # DETECT PARENT / CHILD
    # =========================
    all_parts = df["PartNo"].tolist()

    def has_children(part):
        prefix = part + "."
        return any(p.startswith(prefix) for p in all_parts)

    df["IsParent"] = df["PartNo"].apply(has_children)

    # =========================
    # REMOVE PARENTS (KEEP LEAF ONLY)
    # =========================
    df = df[df["IsParent"] == False]

    # =========================
    # CALCULATE COST
    # =========================
    df["TotalCost"] = df["FinalQty"] * df["UnitPrice"]

    st.write("### After BOM Explosion (Leaf Parts Only)")
    st.dataframe(df[["PartNo", "Description", "FinalQty", "UnitPrice", "TotalCost"]])

    # =========================
    # CONSOLIDATE
    # =========================
    summary = df.groupby(["PartNo", "Description"]).agg({
        "FinalQty": "sum",
        "UnitPrice": "max",
        "TotalCost": "sum"
    }).reset_index()

    summary = summary.rename(columns={"FinalQty": "Quantity"})

    st.write("### ✅ Final Consolidated BOM")
    st.dataframe(summary)

    # =========================
    # DOWNLOAD FILE (SAFE METHOD)
    # =========================
    output = BytesIO()
    summary.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    st.download_button(
        label="Download Consolidated Excel",
        data=output,
        file_name="Consolidated_BOM.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
