import psycopg2
import json
from contextlib import contextmanager

def load_credentials(path):
    with open(path, 'r') as file:
        return json.load(file)

@contextmanager
def db_connection(credentials):
    conn = None
    try:
        conn = psycopg2.connect(
            host=credentials['host'],
            port=credentials['port'],
            database=credentials['database'],
            user=credentials['user'],
            password=credentials['password']
        )
        yield conn
    except psycopg2.DatabaseError as e:
        print(f'Error connecting to the database: {e}')
        raise e
    finally:
        if conn:
            conn.close()

class Database:
    def __init__(self, credentials_path='modules/credentials.json'):
        self.credentials = load_credentials(credentials_path)

    def signup_user(self, **kwargs):
        kwarg_fields = ['name', 'username', 'age', 'faculty', 'matnum', 'password', 'face_img']
        if not all(field in kwargs for field in kwarg_fields):
            return {'success': False, 'error': 'Missing required fields', 'status_code': 400}

        with db_connection(self.credentials) as conn:
            try:
                cur = conn.cursor()
                query = """
                    INSERT INTO users (name, username, age, faculty, matnum, password, face_img)
                    VALUES (%(name)s, %(username)s, %(age)s, %(faculty)s, %(matnum)s, %(hashed_password)s, %(face_img)s)
                """
                kwargs['hashed_password'] = kwargs.pop('password')

                cur.execute(query, kwargs)
                conn.commit()
                cur.close()
                return {'success': True, 'error': None, 'status_code': 201}

            except psycopg2.Error as e:
                error_code = e.pgcode
                error_message = e.pgerror
                print(f'Error registering user: {error_message}')
                return {'success': False, 'error': error_message, 'status_code': 500, 'error_code': error_code}

    def get_user_by_matnum(self, matnum):
        with db_connection(self.credentials) as conn:
            try:
                cur = conn.cursor()
                query = """
                    SELECT password, face_img FROM users WHERE matnum = %s
                """
                cur.execute(query, (matnum,))
                result = cur.fetchone()
                cur.close()

                if result:
                    return {
                        'password': result[0],
                        'face_img': result[1]
                    }
                else:
                    return None

            except Exception as e:
                print(f'Error searching user: {e}')
                return None
