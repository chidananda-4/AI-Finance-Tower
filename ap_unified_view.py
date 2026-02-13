import pandas as pd

def build_ap_view(file_path):
    ap = pd.read_excel(file_path, sheet_name="AP_Spend_Invoices")
    vendor = pd.read_excel(file_path, sheet_name="Vendor_Master")
    costcenter = pd.read_excel(file_path, sheet_name="CostCenter_Master")
    budget = pd.read_excel(file_path, sheet_name="Budget_Plan_Monthly")

    ap['yyyy-mm'] = ap['txn_date'].dt.strftime('%Y-%m')
    budget['yyyy-mm'] = budget['month'].dt.strftime('%Y-%m')
    ap = pd.merge(ap,budget,on=['cost_center','yyyy-mm','business_unit','region','category'],how='left')
    ap = pd.merge(ap,vendor[['vendor_id','vendor_risk_score','vendor_name']],on='vendor_id',how='left')
    ap = pd.merge(ap,costcenter[['cost_center','owner']],on='cost_center',how='left')


    

    return ap
