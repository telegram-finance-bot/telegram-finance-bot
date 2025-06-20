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
    
    secretFiles:
      - name: telegram-secrets
        mountPath: /etc/secrets
        files:
          - name: gspread_key.json
            path: gspread_key.json
          - name: BOT_TOKEN
            path: BOT_TOKEN
          - name: SHEET_ID
            path: SHEET_ID
