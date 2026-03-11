name: Philly Permits — Daily Scan

on:
  schedule:
    - cron: "0 11 * * *"
  workflow_dispatch:
    inputs:
      initial_permits:
        description: 'Run initial permit load (90 days)?'
        required: false
        default: 'false'

jobs:
  scan:
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install requests

      - name: Run permit pipeline
        env:
          AIRTABLE_API_KEY: ${{ secrets.AIRTABLE_API_KEY }}
          AIRTABLE_BASE_ID: ${{ secrets.AIRTABLE_BASE_ID }}
          GMAIL_USER: ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
        run: |
          if [ "${{ github.event.inputs.initial_permits }}" = "true" ]; then
            python permit_main.py --initial
          else
            python permit_main.py
          fi

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: latest-permits-${{ github.run_number }}
          path: latest_permits.json
          retention-days: 7
