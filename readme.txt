1. create a config/ folder 
2. create a file name it email_config.json

json format

{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "ABC@gmail.com",
    "sender_password": "XYZ",
    "recipient_emails": ["123@gmail.com","456@gmail.com"]
}

3. Create a .env file for OPENAI_API_KEY = "******************"
4. streamlit run output.py