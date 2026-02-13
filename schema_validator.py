import pandas as pd

REQUIRED_SHEETS = [
    "Finance_KPI_Weekly",
    "AP_Spend_Invoices",
    "Vendor_Master",
    "Budget_Plan_Monthly",
    "AR_Invoices_Collections",
    "Customer_Master",
    "Collections_Actions"
]

def validate_schema(file_path):
    try:
        xls = pd.ExcelFile(file_path)
        sheets = xls.sheet_names

        for sheet in REQUIRED_SHEETS:
            if sheet not in sheets:
                return False, f"Missing sheet: {sheet}"

        return True, "All required sheets present."

    except Exception as e:
        return False, str(e)
