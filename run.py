from app import create_app, db

app = create_app()

if __name__ == '__main__':
    # Ensure the database tables are created before starting the server
    with app.app_context():
        db.create_all()

    app.run(debug=True)
