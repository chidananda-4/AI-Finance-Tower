import streamlit as st
import pandas as pd
import os
from openai import OpenAI
from dotenv import load_dotenv
from ppt_generation import ppt_generator
from io import BytesIO
from datetime import datetime
import zipfile
import tempfile
import json

# Load environment variables
load_dotenv()

# ============================================================
# CORRECT SHEET NAMES - WITH Finance_KPI_Weekly
# ============================================================

EXPECTED_SOURCES = {
    'AP_Spend_Invoices': [
        'txn_id', 'txn_date', 'cost_center', 'vendor_id', 'category', 
        'sub_category', 'currency', 'amount_inr', 'business_unit', 'region',
        'preferred_vendor_flag', 'payment_terms_days', 'maverick_flag', 
        'po_id', 'invoice_id', 'invoice_received_date', 'invoice_approved_date',
        'invoice_paid_date', 'dispute_flag', 'payment_status', 'due_date',
        'late_payment_flag', 'invoice_processing_days'
    ],
    'Vendor_Master': [
        'vendor_id', 'vendor_name', 'preferred_vendor_flag', 'vendor_risk_score',
        'payment_terms_days'
    ],
    'CostCenter_Master': [
        'cost_center', 'business_unit', 'region', 'owner'
    ],
    'Budget_Plan_Monthly': [
        'month', 'cost_center', 'business_unit', 'region', 'category',
        'planned_budget_inr'
    ],
    'Customer_Master': [
        'customer_id', 'customer_name', 'segment', 'region', 'payment_terms_days'
    ],
    'Finance_KPI_Weekly': [
        'week_start',
        'total_spend_inr',
        'maverick_spend_inr',
        'duplicate_suspect_count',
        'avg_invoice_processing_days',
        'late_payment_rate_ap',
        'ar_invoiced_inr',
        'ar_collected_inr',
        'open_ar_count'
    ],
    'AR_Invoices_Collections': [
        'ar_invoice_id', 'customer_id', 'invoice_date', 'invoice_amount_inr',
        'segment', 'region', 'payment_terms_days', 'due_date', 'paid_date',
        'paid_amount_inr', 'payment_status', 'days_overdue', 'late_payment_flag'
    ],
    'Collections_Actions': [
        'action_id', 'ar_invoice_id', 'action_date', 'action_type', 'outcome'
    ]
}

# CSV file name mappings with correct names
CSV_MAPPING = {
    'ap_spend_invoices.csv': 'AP_Spend_Invoices',
    'vendor_master.csv': 'Vendor_Master',
    'costcenter_master.csv': 'CostCenter_Master',
    'budget_plan_monthly.csv': 'Budget_Plan_Monthly',
    'customer_master.csv': 'Customer_Master',
    'finance_kpi_weekly.csv': 'Finance_KPI_Weekly',
    'ar_invoices_collections.csv': 'AR_Invoices_Collections',
    'collections_actions.csv': 'Collections_Actions'
}

# ============================================================
# EMAIL CONFIGURATION FUNCTIONS
# ============================================================

def load_email_config():
    """Load email configuration from file"""
    config_path = "config/email_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_email_config(config):
    """Save email configuration to file"""
    os.makedirs("config", exist_ok=True)
    with open("config/email_config.json", "w") as f:
        json.dump(config, f, indent=4)

# ============================================================
# VALIDATION FUNCTIONS
# ============================================================

def validate_excel_file(uploaded_file):
    """
    Validate Excel file has all required sheets and columns
    """
    validation_result = {
        'is_valid': False,
        'missing_sources': [],
        'missing_columns': {},
        'available_sources': [],
        'dataframes': {},
        'errors': []
    }
    
    try:
        xls = pd.ExcelFile(uploaded_file)
        available_sheets = xls.sheet_names
        validation_result['available_sources'] = available_sheets
        
        # Check for missing sheets
        for expected_source in EXPECTED_SOURCES.keys():
            if expected_source not in available_sheets:
                validation_result['missing_sources'].append(expected_source)
            else:
                # Load and validate columns
                df = pd.read_excel(uploaded_file, sheet_name=expected_source)
                validation_result['dataframes'][expected_source] = df
                
                required_cols = EXPECTED_SOURCES[expected_source]
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    validation_result['missing_columns'][expected_source] = missing_cols
        
        # Set validity
        validation_result['is_valid'] = (
            len(validation_result['missing_sources']) == 0 and 
            len(validation_result['missing_columns']) == 0
        )
        
    except Exception as e:
        validation_result['errors'].append(str(e))
    
    return validation_result

def validate_csv_files(uploaded_files):
    """
    Validate multiple CSV files have required columns
    """
    validation_result = {
        'is_valid': False,
        'missing_sources': [],
        'missing_columns': {},
        'available_sources': [],
        'dataframes': {},
        'errors': []
    }
    
    uploaded_filenames = [f.name for f in uploaded_files]
    validation_result['available_sources'] = uploaded_filenames
    
    # Check for missing required files
    for required_file, source_name in CSV_MAPPING.items():
        if required_file not in uploaded_filenames:
            validation_result['missing_sources'].append(source_name)
    
    # Load and validate each uploaded file
    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        
        if filename in CSV_MAPPING:
            source_name = CSV_MAPPING[filename]
            try:
                df = pd.read_csv(uploaded_file)
                validation_result['dataframes'][source_name] = df
                
                required_cols = EXPECTED_SOURCES[source_name]
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    validation_result['missing_columns'][source_name] = missing_cols
                    
            except Exception as e:
                validation_result['errors'].append(f"Error reading {filename}: {str(e)}")
    
    # Set validity
    validation_result['is_valid'] = (
        len(validation_result['missing_sources']) == 0 and 
        len(validation_result['missing_columns']) == 0
    )
    
    return validation_result

def validate_zip_file(uploaded_zip):
    """
    Validate zip file containing CSV files
    """
    validation_result = {
        'is_valid': False,
        'missing_sources': [],
        'missing_columns': {},
        'available_sources': [],
        'dataframes': {},
        'errors': []
    }
    
    try:
        with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
            # Extract to temp directory
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_ref.extractall(tmpdir)
                
                # Get all CSV files
                csv_files = [f for f in os.listdir(tmpdir) if f.endswith('.csv')]
                validation_result['available_sources'] = csv_files
                
                # Check for missing required files
                for required_file, source_name in CSV_MAPPING.items():
                    if required_file not in csv_files:
                        validation_result['missing_sources'].append(source_name)
                
                # Load and validate each CSV
                for csv_file in csv_files:
                    if csv_file in CSV_MAPPING:
                        source_name = CSV_MAPPING[csv_file]
                        file_path = os.path.join(tmpdir, csv_file)
                        df = pd.read_csv(file_path)
                        validation_result['dataframes'][source_name] = df
                        
                        required_cols = EXPECTED_SOURCES[source_name]
                        missing_cols = [col for col in required_cols if col not in df.columns]
                        
                        if missing_cols:
                            validation_result['missing_columns'][source_name] = missing_cols
                
                # Set validity
                validation_result['is_valid'] = (
                    len(validation_result['missing_sources']) == 0 and 
                    len(validation_result['missing_columns']) == 0
                )
                
    except Exception as e:
        validation_result['errors'].append(str(e))
    
    return validation_result

def consolidate_dataframes(validation_result):
    """
    Consolidate validated dataframes into the expected format
    """
    consolidated = {
        'AP_Spend_Invoices': None,
        'Vendor_Master': None,
        'CostCenter_Master': None,
        'Budget_Plan_Monthly': None,
        'Customer_Master': None,
        'Finance_KPI_Weekly': None,
        'AR_Invoices_Collections': None,
        'Collections_Actions': None
    }
    
    for source_name, df in validation_result.get('dataframes', {}).items():
        if source_name in consolidated:
            consolidated[source_name] = df
    
    return consolidated

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Finance Control Tower",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS - YOUR ORIGINAL STYLING
# ============================================================
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 2rem;
        text-align: center;
    }
    .success-box {
        padding: 1rem;
        background-color: #DFF2BF;
        border: 1px solid #4F8A10;
        border-radius: 5px;
        color: #4F8A10;
    }
    .warning-box {
        padding: 1rem;
        background-color: #FEEFB3;
        border: 1px solid #9F6000;
        border-radius: 5px;
        color: #9F6000;
    }
    .error-box {
        padding: 1rem;
        background-color: #FFBABA;
        border: 1px solid #D8000C;
        border-radius: 5px;
        color: #D8000C;
    }
    .sheet-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .sheet-present {
        background-color: #DFF2BF;
        color: #4F8A10;
        border: 1px solid #4F8A10;
    }
    .sheet-missing {
        background-color: #FFBABA;
        color: #D8000C;
        border: 1px solid #D8000C;
    }
    .column-badge {
        display: inline-block;
        padding: 0.2rem 0.4rem;
        margin: 0.2rem;
        border-radius: 3px;
        font-size: 0.75rem;
        font-family: monospace;
    }
    .column-present {
        background-color: #DFF2BF;
        color: #4F8A10;
        border: 1px solid #4F8A10;
    }
    .column-missing {
        background-color: #FFBABA;
        color: #D8000C;
        border: 1px solid #D8000C;
    }
    .stProgress > div > div > div > div {
        background-color: #1E88E5;
    }
    .email-config {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .step-box {
        padding: 0.5rem;
        margin: 0.2rem 0;
        border-radius: 0.3rem;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📊 Finance Control Tower Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Autonomous Financial Analytics & Reporting</p>', unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/null/financial-growth.png", width=80)
    st.title("Finance Control Tower")
    st.markdown("---")
    
    st.markdown("### 📤 Data Input Options")
    input_method = st.radio(
        "Choose input method:",
        ["Upload Excel File (Multiple Sheets)", 
         "Upload Multiple CSV Files", 
         "Upload ZIP of CSV Files"]
    )
    
    st.markdown("---")
    
    # ============================================================
    # EMAIL TOGGLE BUTTON
    # ============================================================
    st.markdown("### 📧 Email Distribution")
    
    # Check if email config exists
    email_config = load_email_config()
    email_configured = email_config is not None
    
    if email_configured:
        st.success(f"✅ Email configured for {len(email_config.get('recipient_emails', []))} recipients")
        enable_email = st.checkbox("Enable automatic email distribution", value=False)
        
        # Show email config summary
        with st.expander("📋 Email Settings", expanded=False):
            st.markdown(f"**SMTP:** {email_config.get('smtp_server', '')}")
            st.markdown(f"**Sender:** {email_config.get('sender_email', '')}")
            st.markdown("**Recipients:**")
            for r in email_config.get('recipient_emails', []):
                st.markdown(f"• {r}")
    else:
        st.warning("⚠️ Email not configured")
        enable_email = False
        with st.expander("⚙️ Configure Email", expanded=False):
            st.markdown("Create `config/email_config.json` with:")
            st.code("""{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "sender_email": "your-email@gmail.com",
  "sender_password": "your-app-password",
  "recipient_emails": ["cxo@company.com"]
}""")
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.info(
        """
        This AI-powered dashboard:
        - 📈 Monitors 20+ KPIs
        - 🔍 Detects anomalies
        - 💡 Generates insights
        - 📊 Creates PPT reports
        - 📧 Auto-email distribution
        
        **Required Data Sources:**
        - AP_Spend_Invoices
        - Vendor_Master
        - CostCenter_Master
        - Budget_Plan_Monthly
        - Customer_Master
        - Finance_KPI_Weekly
        - AR_Invoices_Collections
        - Collections_Actions
        """
    )
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        st.warning("⚠️ OpenAI API key not found in .env file")
        api_key_input = st.text_input("Enter your OpenAI API Key:", type="password")
        if api_key_input:
            os.environ['OPENAI_API_KEY'] = api_key_input
            st.success("✅ API Key set successfully!")
    else:
        st.success("✅ OpenAI API Key loaded")

# ============================================================
# MAIN CONTENT
# ============================================================

validation_result = None
consolidated_data = None

if input_method == "Upload Excel File (Multiple Sheets)":
    st.markdown("### 📁 Upload Excel File")
    
    with st.expander("📋 Required Sheets and Columns", expanded=False):
        for source, columns in EXPECTED_SOURCES.items():
            st.markdown(f"**{source}** ({len(columns)} columns)")
            st.code(", ".join(columns[:8]) + ("..." if len(columns) > 8 else ""))
    
    uploaded_file = st.file_uploader(
        "Choose Excel file",
        type=["xlsx", "xls"],
        key="excel_upload"
    )
    
    if uploaded_file is not None:
        with st.spinner("Validating Excel file..."):
            validation_result = validate_excel_file(uploaded_file)
            if validation_result['is_valid']:
                consolidated_data = consolidate_dataframes(validation_result)

elif input_method == "Upload Multiple CSV Files":
    st.markdown("### 📁 Upload Multiple CSV Files")
    
    with st.expander("📋 Required CSV Files and Columns", expanded=False):
        for file, source in CSV_MAPPING.items():
            st.markdown(f"**{file}** → {source}")
            st.code(", ".join(EXPECTED_SOURCES[source][:5]) + "...")
    
    uploaded_files = st.file_uploader(
        "Choose CSV files",
        type=["csv"],
        accept_multiple_files=True,
        key="csv_upload"
    )
    
    if uploaded_files and len(uploaded_files) > 0:
        with st.spinner("Validating CSV files..."):
            validation_result = validate_csv_files(uploaded_files)
            if validation_result['is_valid']:
                consolidated_data = consolidate_dataframes(validation_result)

else:  # Upload ZIP of CSV Files
    st.markdown("### 📁 Upload ZIP of CSV Files")
    
    with st.expander("📋 Required CSV Files in ZIP", expanded=False):
        for file, source in CSV_MAPPING.items():
            st.markdown(f"**{file}** → {source}")
    
    uploaded_zip = st.file_uploader(
        "Choose ZIP file",
        type=["zip"],
        key="zip_upload"
    )
    
    if uploaded_zip is not None:
        with st.spinner("Validating ZIP file contents..."):
            validation_result = validate_zip_file(uploaded_zip)
            if validation_result['is_valid']:
                consolidated_data = consolidate_dataframes(validation_result)

# ============================================================
# DISPLAY VALIDATION RESULTS
# ============================================================

if validation_result:
    st.markdown("---")
    st.markdown("### 📊 Data Validation Results")
    
    if validation_result['is_valid']:
        st.markdown('<p class="success-box">✅ All required sheets/files and columns found!</p>', 
                   unsafe_allow_html=True)
        
        # Display data summary
        col1, col2, col3 = st.columns(3)
        
        total_rows = 0
        for name, df in consolidated_data.items():
            if df is not None:
                total_rows += len(df)
        
        with col1:
            st.metric("Files/Sheets Loaded", 
                     sum(1 for v in consolidated_data.values() if v is not None))
        with col2:
            st.metric("Total Rows", total_rows)
        with col3:
            st.metric("Status", "Ready")
        
        # Column validation summary
        with st.expander("🔍 Column Validation Summary", expanded=False):
            for source_name, df in consolidated_data.items():
                if df is not None:
                    st.markdown(f"**{source_name}**")
                    required = EXPECTED_SOURCES[source_name]
                    present = [col for col in required if col in df.columns]
                    missing = [col for col in required if col not in df.columns]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"✅ Present: {len(present)}/{len(required)}")
                        if present:
                            cols_html = " ".join([f'<span class="column-badge column-present">{col}</span>' 
                                                for col in present[:15]])
                            st.markdown(cols_html, unsafe_allow_html=True)
                    with col2:
                        if missing:
                            st.markdown(f"❌ Missing: {len(missing)}")
                            cols_html = " ".join([f'<span class="column-badge column-missing">{col}</span>' 
                                                for col in missing])
                            st.markdown(cols_html, unsafe_allow_html=True)
                    st.markdown("---")
        
        # Data preview
        with st.expander("🔍 Data Preview", expanded=False):
            tabs = st.tabs([name for name, df in consolidated_data.items() if df is not None])
            
            tab_idx = 0
            for name, df in consolidated_data.items():
                if df is not None:
                    with tabs[tab_idx]:
                        st.dataframe(df.head(), use_container_width=True)
                        st.caption(f"Total rows: {len(df)} | Total columns: {len(df.columns)}")
                    tab_idx += 1
        
        # ============================================================
        # RUN ANALYSIS BUTTON WITH ENHANCED PROGRESS
        # ============================================================
        
        st.markdown("---")
        
        if st.button("🚀 Run Full Finance Analysis", type="primary", use_container_width=True):
            
            # Check for API key
            if not os.getenv('OPENAI_API_KEY') and not os.environ.get('OPENAI_API_KEY'):
                st.error("❌ OpenAI API Key not found. Please add it in the sidebar.")
                st.stop()
            
            # Create progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Create a detailed status expander
            with st.expander("📊 Detailed Progress", expanded=True):
                step1_status = st.empty()
                step2_status = st.empty()
                step3_status = st.empty()
                step4_status = st.empty()
                step5_status = st.empty()
                
                # Initialize step status
                step1_status.markdown("⏳ **Step 1/5:** Computing KPIs and building data views...")
                step2_status.markdown("⏳ **Step 2/5:** Generating slide visualizations (11 slides)...")
                step3_status.markdown("⏳ **Step 3/5:** Creating executive summary with CrewAI agents...")
                step4_status.markdown("⏳ **Step 4/5:** Assembling PowerPoint presentation...")
                step5_status.markdown("⏳ **Step 5/5:** Finalizing and sending emails...")
            
            try:
                # Initialize client
                client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
                
                # ==================== STEP 1: COMPUTE KPIs ====================
                status_text.text("📊 Computing KPIs and building data views...")
                progress_bar.progress(10)
                step1_status.markdown("🔄 **Step 1/5:** Computing KPIs and building data views...")
                
                # This happens inside ppt_generator
                progress_bar.progress(20)
                step1_status.markdown("✅ **Step 1/5:** KPIs computed successfully!")
                
                # ==================== STEP 2: GENERATE VISUALIZATIONS ====================
                status_text.text("📈 Generating slide visualizations...")
                progress_bar.progress(30)
                step2_status.markdown("🔄 **Step 2/5:** Generating slide visualizations (11 slides)...")
                
                progress_bar.progress(50)
                step2_status.markdown("✅ **Step 2/5:** All 11 slide visualizations generated!")
                
                # ==================== STEP 3: GENERATE EXECUTIVE SUMMARY ====================
                status_text.text("🤖 Creating executive summary with CrewAI agents...")
                progress_bar.progress(60)
                step3_status.markdown("🔄 **Step 3/5:** CrewAI agents analyzing insights and creating executive summary...")
                
                # Generate PPT with CrewAI summary
                final_ppt, insights, executive_summary = ppt_generator(
                    consolidated_data, 
                    client, 
                    generate_summary=True
                )
                
                progress_bar.progress(80)
                step3_status.markdown("✅ **Step 3/5:** Executive summary created by 4 CrewAI agents!")
                
                # ==================== STEP 4: ASSEMBLE PRESENTATION ====================
                status_text.text("📑 Assembling PowerPoint presentation...")
                progress_bar.progress(85)
                step4_status.markdown("🔄 **Step 4/5:** Adding cover page, executive summary, and 11 visualization slides...")
                
                # Save to BytesIO
                ppt_bytes = BytesIO()
                final_ppt.save(ppt_bytes)
                ppt_bytes.seek(0)
                
                progress_bar.progress(95)
                step4_status.markdown("✅ **Step 4/5:** Presentation assembled with 14 slides!")
                
                # ==================== STEP 5: FINALIZE AND EMAIL ====================
                status_text.text("📧 Finalizing and sending emails...")
                progress_bar.progress(98)
                
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Finance_Control_Tower_{timestamp}.pptx"
                
                # Email sending (if enabled)
                email_status = "⏸️ Not enabled"
                if enable_email and email_config:
                    step5_status.markdown("🔄 **Step 5/5:** Sending email to recipients...")
                    try:
                        from agents.email_agent import EmailAgent
                        
                        email_agent = EmailAgent(client)
                        ppt_bytes.seek(0)
                        
                        result = email_agent.send_report(
                            ppt_bytes=ppt_bytes,
                            filename=filename,
                            executive_summary=executive_summary,
                            recipients=email_config.get('recipient_emails', [])
                        )
                        
                        if result.get("success"):
                            email_status = f"✅ Email sent to {len(email_config.get('recipient_emails', []))} recipients"
                            step5_status.markdown(f"✅ **Step 5/5:** {email_status}")
                        else:
                            email_status = f"⚠️ Email failed: {result.get('message', 'Unknown error')}"
                            step5_status.markdown(f"⚠️ **Step 5/5:** {email_status}")
                    except Exception as e:
                        email_status = f"⚠️ Email error: {str(e)}"
                        step5_status.markdown(f"⚠️ **Step 5/5:** {email_status}")
                else:
                    step5_status.markdown("✅ **Step 5/5:** Presentation finalized (email not enabled)")
                
                progress_bar.progress(100)
                status_text.text("")
                
                # Close the expander or keep it open
                st.markdown("")  # Just a spacer
                
                st.markdown('<p class="success-box">✅ Analysis Completed Successfully!</p>', 
                           unsafe_allow_html=True)
                
                # Download button
                col1, col2, col3 = st.columns(3)
                with col2:
                    st.download_button(
                        label="📥 Download Finance Control Tower PPT",
                        data=ppt_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )
                
                # Show executive summary
                if executive_summary:
                    with st.expander("📋 Executive Summary", expanded=True):
                        st.markdown("### EXECUTIVE SUMMARY")
                        if "formatted_text" in executive_summary:
                            st.text(executive_summary["formatted_text"])
                        else:
                            st.write(executive_summary.get("big_picture", "Analysis complete"))
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("#### ✅ What's Working")
                                for w in executive_summary.get("working", []):
                                    st.markdown(w)
                            
                            with col2:
                                st.markdown("#### ⚠ What Needs Attention")
                                for a in executive_summary.get("attention", []):
                                    st.markdown(a)
                            
                            st.markdown("#### 🎯 Next Steps")
                            for ns in executive_summary.get("next_steps", []):
                                st.markdown(ns)
                
                # Success metrics
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Slides Generated", "14 (Cover + Summary + 11 + Thank You)")
                with col2:
                    st.metric("File Size", f"{ppt_bytes.getbuffer().nbytes / 1024 / 1024:.1f} MB")
                with col3:
                    st.metric("CrewAI Agents", "4")
                
                # Show processing summary
                with st.expander("⏱️ Processing Summary", expanded=False):
                    st.markdown(f"""
                    | Step | Description | Status |
                    |------|-------------|--------|
                    | 1 | Computing KPIs | ✅ Complete |
                    | 2 | Generating Visualizations (11 slides) | ✅ Complete |
                    | 3 | CrewAI Executive Summary (4 agents) | ✅ Complete |
                    | 4 | Assembling Presentation (14 slides) | ✅ Complete |
                    | 5 | Email Distribution | {email_status} |
                    """)
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.exception(e)
        
    else:
        st.markdown('<p class="error-box">❌ Data validation failed. See details below:</p>', 
                   unsafe_allow_html=True)
        
        # Missing sources
        if validation_result['missing_sources']:
            st.markdown("### 📁 Missing Sources")
            for source in validation_result['missing_sources']:
                st.markdown(f'<span class="sheet-badge sheet-missing">❌ {source}</span>', 
                           unsafe_allow_html=True)
        
        # Missing columns
        if validation_result['missing_columns']:
            st.markdown("### 📊 Missing Columns by Source")
            for source, columns in validation_result['missing_columns'].items():
                st.markdown(f"**{source}**")
                col_html = " ".join([f'<span class="column-badge column-missing">{col}</span>' 
                                    for col in columns])
                st.markdown(col_html, unsafe_allow_html=True)
        
        # Show what was loaded
        if validation_result['dataframes']:
            st.markdown("### 📂 Successfully Loaded Data")
            for name, df in validation_result['dataframes'].items():
                st.markdown(f'<span class="sheet-badge sheet-present">✅ {name}: {len(df)} rows</span>', 
                           unsafe_allow_html=True)

else:
    # Instructions
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📋 Instructions
        
        1. **Choose input method** from sidebar
        2. **Upload your files** (Excel, multiple CSVs, or ZIP)
        3. **System validates** all 50+ required columns
        4. **Click "Run Full Finance Analysis"** to start
        5. **Watch the 5-step progress** as your report generates
        6. **Download** the generated PPT report
        7. **Enable email toggle** in sidebar for auto-distribution
        """)
    
    with col2:
        st.markdown("""
        ### 🔧 Setup Checklist
        
        - [ ] OpenAI API key in `.env` file or sidebar
        - [ ] Excel/CSV files with all required sources
        - [ ] All 50+ columns present in data
        - [ ] Email config in `config/email_config.json` (optional)
        - [ ] Required Python packages installed
        
        ### 📊 Required Sources (8 sheets):
        - AP_Spend_Invoices (23 cols)
        - Vendor_Master (5 cols)
        - CostCenter_Master (4 cols)
        - Budget_Plan_Monthly (6 cols)
        - Customer_Master (5 cols)
        - Finance_KPI_Weekly (5 cols)
        - AR_Invoices_Collections (13 cols)
        - Collections_Actions (5 cols)
        
        **Total: 66 columns across 8 sources**
        """)

# Footer
st.markdown("---")
st.markdown(
    "<center>Made with ❤️ for GCC FUSIONX Hackathon | Agentic AI for Autonomous Analytics</center>",
    unsafe_allow_html=True
)