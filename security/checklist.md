# Security Checklist

| Category | Item | Status | Notes |
|----------|------|--------|-------|
| **Secrets** | Hardcoded Secrets | PASS | Checked app.py, database.py, ai_uzman.py. |
| **Secrets** | .env Committed | PASS | Excluded via .gitignore. |
| **Secrets** | Secret files (txt) Committed | PASS | Excluded via .gitignore. |
| **Auth** | Password Hashing | PASS | Using werkzeug.security. |
| **Auth** | Brute-force Protection | PASS | flask-limiter and lockout mechanism. |
| **API** | SQL Injection | PASS | Parameterized queries used. |
| **API** | CSRF Protection | PASS | flask-wtf integrated. |
| **Session** | Secure Cookies | PASS | Secure and HttpOnly flags set. |
| **Session** | Session Expiry | PASS | 1800s set in app.py. |
| **Dependency**| Vulnerable Packages | PENDING| pip-audit running. |
| **AI** | Prompt Injection | PASS | Delimiters and isolation instructions added. |
| **Infra** | Server Info Leak | PASS | guncelle.bat removed from Git tracking. |
| **Infra** | Error Exposure | PASS | Custom error responses used. |
| **Audit** | Logging | PASS | Auth attempts logged. |
