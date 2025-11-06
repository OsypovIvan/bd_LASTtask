import os
from configparser import ConfigParser
import psycopg2
from flask import Flask, request, render_template, g, current_app

app = Flask(__name__)

def read_config(filename='database.ini', section='PostgreSQL'):
    parser = ConfigParser()
    parser.read(filename)
    return {param[0]: param[1] for param in parser.items(section)}

def connect_db():
    config = read_config()
    return psycopg2.connect(**config)

def get_db():
    if "db" not in g:
        g.db = connect_db()
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@app.route('/')
def homepage():
    return render_template('home.html')

@app.route('/browse')
def browse():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM events ORDER BY event_date')
    rows = cur.fetchall()
    return render_template('browse.html', events=rows)

@app.route('/buy', methods=['GET', 'POST'])
def buy():
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'GET':
        cur.execute('SELECT id, title, available_tickets FROM events WHERE available_tickets > 0')
        events = cur.fetchall()
        return render_template('buy.html', events=events)

    elif request.method == 'POST':
        event_id = request.form['event_id']
        name = request.form['buyer_name']

        try:
            cur.execute('INSERT INTO tickets (event_id, buyer_name) VALUES (%s, %s)', [event_id, name])
            conn.commit()
            return render_template('buy.html', success=True)

        except psycopg2.Error as e:
            conn.rollback()  # отменяем транзакцию
            if "already bought" in str(e):
                return render_template('buy.html', error="You have already purchased a ticket for this event!")
            else:
                return render_template('buy.html', error="An error occurred while purchasing your ticket.")


@app.cli.command("init")
def init_db():
    conn = get_db()
    cur = conn.cursor()
    with current_app.open_resource("schema.sql") as f:
        cur.execute(f.read())
    conn.commit()
    print("DB initialized")

@app.cli.command("populate")
def populate_db():
    conn = get_db()
    cur = conn.cursor()
    with current_app.open_resource("populate.sql") as f:
        cur.execute(f.read())
    conn.commit()
    print("DB populated")

if __name__ == "__main__":
    app.run(debug=True, port=8080)
