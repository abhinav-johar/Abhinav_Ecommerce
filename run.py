from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], port=int(app.config.get('PORT', 5000)))
    