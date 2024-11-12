# IMAP Mails Checker




## 💻 Requirements

- Python >= 3.11
- Internet connection
- Valid proxies

---

## 🛠️ Setup

1. Clone the repository:
   ```bash
   git clone [repository URL]
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   cd venv/Scripts
   activate
   cd ../..
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration

### settings.yaml

This file contains general settings for the bot:

```yaml
threads: 5 # Number of threads for simultaneous account operations
retry_limit: 3 # Number of retries for failed operations

imap_settings: # IMAP settings for email providers
  gmail.com: imap.gmail.com
  outlook.com: imap-mail.outlook.com
  # Add more email providers as needed
```

### Other Configuration Files

#### 📁 accounts.txt
Contains accounts for check.
```
Format:
email:password
email:password
...
```


#### 📁 proxies.txt
Contains proxy information.
```
Format:
http://user:pass@ip:port
http://ip:port:user:pass
http://ip:port@user:pass
http://user:pass:ip:port
...
```

---

## 🚀 Usage

1. Ensure all configuration files are set up correctly.
2. Run the bot:
   ```bash
   python run.py
   ```

---
