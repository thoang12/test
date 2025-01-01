from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
# from .forms import RegistrationForm, LoginForm
# from .models import User
from flask_login import login_user, logout_user, login_required, current_user 
from config import config_db     
from mysql.connector import pooling    
import datetime, os, logging, re

main = Blueprint('main', __name__)
sql =config_db
dbconfig = {
    "user": sql.user,
    "password": sql.password,
    "host": sql.host,
    "database": sql.database_name
}
log_file_path = "./logs/app.log"

os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Application has started.")
main.secret_key = sql.secret_key
table_name = sql.table_name
valid_username = sql.valid_username
valid_password = sql.valid_password
cnxpool = pooling.MySQLConnectionPool(pool_name="mypool",pool_size=5,**dbconfig)
def get_db_connection():
    return cnxpool.get_connection()
@main.route('/duplicate_uuids', methods=['GET'])
def find_uuid_duplicate():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Câu lệnh SQL đã được sửa
    cursor.execute(f'SELECT uuid, COUNT(*) FROM {table_name} GROUP BY uuid HAVING COUNT(*) > 1')
    duplicate_uuids = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("duplicate_uuid.html", duplicate_uuids=duplicate_uuids)

@main.route('/duplicate_users', methods=['GET'])
def find_users_duplicate():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Câu lệnh SQL đã được sửa
    cursor.execute(f'''
        SELECT username, uuid 
        FROM {table_name} 
        WHERE uuid IN (
            SELECT uuid 
            FROM {table_name} 
            GROUP BY uuid 
            HAVING COUNT(*) > 1
        )
    ''')
    duplicate_uuids = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("duplicate_users.html", duplicate_uuids=duplicate_uuids)

@main.route('/search/suggestions', methods=['GET'])
def get_user_suggestions():
    query = request.args.get('q', '')  # Get query parameter

    conn = get_db_connection()
    try:
        # cursor = conn.cursor(dictionary=True)
        cursor = conn.cursor()
        cursor.execute(f"SELECT username FROM {table_name} WHERE username LIKE %s", (f'%{query}%',))
        suggestions = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Failed to get user suggestions: {e}")
    cursor.close()
    conn.close()
    return jsonify(suggestions)

@main.route('/search_results', methods=['POST'])
def search_users():
    query = request.form['search_query']  # Get the search query from the form
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name} WHERE username LIKE %s", (f'%{query}%',))
        users = cursor.fetchall()
    except Exception as e:
        print(f"Failed to search users: {e}")
    cursor.close()
    conn.close() 
    return render_template('search_results.html', users=users)

@main.route('/admin_login', methods=['GET', 'POST'])
def handle_login_admin():
    if request.method == 'POST':
        entered_username = request.form.get('username')
        entered_password = request.form.get('password')

        if entered_username == valid_username and entered_password == valid_password:
            session['username'] = entered_username
            return redirect(url_for('main.list_users_accounts', page=1))
        else:
            return render_template('login_admin.html', error="Invalid username or password")
    return render_template('login_admin.html')

@main.route('/', methods=['GET', 'POST'])
@main.route('/login', methods=['GET', 'POST'])
def handle_login():
    if request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({'status': 'fail', 'msg': 'Missing JSON data'})
        username = data.get('username')
        password = data.get('password')
        uuid = data.get('uuid')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f'SELECT * FROM {table_name} WHERE username = %s AND password = %s AND uuid = %s', (username, password, uuid))
        customer = cursor.fetchone()
        cursor.close()
        conn.close()
        if customer:
            session['loggedin'] = True
            session['id'] = customer['id']
            session['username'] = customer['username']
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            logging.info(f"User {username} logged in successfully. Date: {current_date}")
            return jsonify({'status': 'success', 'msg': f'Logged in successfully/{current_date}/{customer["expdate"]}'})
        else:
            return jsonify({'status': 'fail', 'msg': 'Invalid username or password'})
    return jsonify({'status': 'fail', 'msg': 'Use POST method to log in'})

@main.route('/register', methods=['POST'])
def handle_registration():
    if request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({'status': 'fail', 'msg': 'Missing JSON data'})
        username = data.get('username')
        password = data.get('password')
        phone = data.get('phone')
        address = data.get('address')
        uuid = data.get('uuid')
        inforuser = data.get('inforuser')
        if not username or not password or not uuid:
            return jsonify({'status': 'fail', 'msg': 'Missing required fields: username, password, uuid'})
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f'SELECT username FROM {table_name} WHERE username = %s', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            msg = 'Username already exists!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        else:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d')
            cursor.execute(f'INSERT INTO {table_name} (username, password, phone ,address, expdate, uuid, inforuser) VALUES (%s, %s, %s, %s, %s, %s, %s)', (username, password, phone, address, current_time, uuid, inforuser))
            conn.commit()
            msg = 'You have successfully registered!'
            logging.info(f"User {username} registered successfully. Date: {current_time}")
        cursor.close()
        conn.close()
        return jsonify({'status': 'success', 'msg': msg})
    return jsonify({'status': 'fail', 'msg': 'Use POST method to register'})

@main.route('/users_accounts/<int:page>', methods=['GET', 'POST'])
def list_users_accounts(page=1):
    if 'username' in session:
        per_page = 100  # Số lượng bản ghi mỗi trang
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(f"SELECT COUNT(*) AS total FROM {table_name}")
            total = cursor.fetchone()['total']
            offset = (page - 1) * per_page
            cursor.execute(f"SELECT * FROM {table_name} LIMIT %s OFFSET %s", (per_page, offset))
            customers = cursor.fetchall()
        except Exception as e:
            print(f"Failed to fetch customers: {e}")
        # print(customers)
        cursor.close()
        conn.close()
        # total_pages = (total - 1) // per_page + 1
        total_pages = (total + per_page - 1) // per_page
        return render_template('users_accounts.html', customers=customers, page=page,  total_pages=total_pages)
    return redirect(url_for('main.handle_login_admin'))

@main.route('/update_customer', methods=['POST'])
def handle_update_customer():
    customer_id = request.form['id']
    username = request.form['username']
    password = request.form['password']
    phone = request.form['phone']
    address = request.form['address']
    expdate = request.form['expdate']
    uuid = request.form['uuid']
    inforuser = request.form['inforuser']
    timesapproval = request.form['timesapproval']
    notes = request.form['notes']

    update_query = """
    UPDATE customers SET 
        username = %s, 
        password = %s, 
        phone = %s, 
        address = %s, 
        expdate = %s, 
        uuid = %s, 
        inforuser = %s, 
        timesapproval = %s, 
        notes = %s 
    WHERE id = %s
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(update_query, (username, password, phone, address, expdate, uuid, inforuser, timesapproval, notes, customer_id))
        conn.commit()
    except Exception as e:
        print(f"Failed to update customer: {e}")
    cursor.close()
    conn.close()    

    return jsonify({'status': 'success'})

@main.route('/delete_customer', methods=['POST'])
def handle_delete_customer():
    customer_id = request.form['id']
    delete_query = "DELETE FROM customers WHERE id = %s"
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(delete_query, (customer_id,))
        conn.commit()
    except Exception as e:
        print(f"Failed to delete customer: {e}")
    cursor.close()
    conn.close()
    return jsonify({'status': 'success'})

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.handle_login'))


from flask import Flask
app = Flask(__name__)
app.secret_key = sql.secret_key
app.register_blueprint(main)
if __name__ == '__main__':
    app.run(debug=True)