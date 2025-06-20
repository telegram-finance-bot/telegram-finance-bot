services:
  - type: web
    name: telegram-finance-bot
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    
    envVars:
      - key: PORT
        value: '10000'
      - key: WEBHOOK_URL
        valueFrom:
          secretKeyRef:
            name: telegram-secrets
            key: WEBHOOK_URL
      - key: BOT_TOKEN
        valueFrom:
          secretKeyRef:
            name: telegram-secrets
            key: BOT_TOKEN
      - key: SHEET_ID
        valueFrom:
          secretKeyRef:
            name: telegram-secrets
            key: SHEET_ID
      - key: CREDS_FILE
        value: /etc/secrets/gspread_key.json

    secretFiles:
      - name: telegram-secrets
        mountPath: /etc/secrets
        files:
          - name: gspread_key.json
            path: gspread_key.json
