#!/usr/bin/env python3
# Minimal Flask test

from flask import Flask

app = Flask(__name__)

@app.route('/test')
def test():
    return {'status': 'ok', 'message': 'Minimal Flask çalışıyor'}

if __name__ == '__main__':
    print("Minimal Flask başlatılıyor...")
    app.run(debug=False, host='127.0.0.1', port=5001)