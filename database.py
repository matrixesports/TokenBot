import sqlite3

connection = sqlite3.connect("/data/discord-commerce.db")
cursor = connection.cursor()
create_table = """CREATE TABLE IF NOT EXISTS balances (
	username INTEGER PRIMARY KEY
);"""
cursor.execute(create_table)
connection.commit()
def add_token(token_name):
    token_name=token_name.lower()
    if token_name in get_token_list():
        return False
    else:
        cursor.execute(
            "ALTER TABLE balances ADD " + token_name + " NOT NULL DEFAULT 0;")


def remove_token(token_name):
    cursor.execute(
        "ALTER TABLE balances ADD ? NOT NULL DEFAULT 0;", (token_name, ))


def user_exists(unique_id):
    return bool(cursor.execute("SELECT EXISTS(select * from balances where username=?)",(unique_id,)).fetchone()[0])


def add_user(unique_id):
    cursor.execute("""INSERT into balances (username) VALUES(?)""", (unique_id,))
    connection.commit()


def set_balance(unique_id, token_name, balance):
    token_name=token_name.lower()
    if user_exists(unique_id) == False:
        add_user(unique_id)
    if token_name in get_token_list():
        cursor.execute("update balances set "  + token_name.lower() + " = ? where username = ?",(balance, unique_id))
        connection.commit()


def get_balance(user, token_name):
    token_name=token_name.lower()
    if token_name in get_token_list():
        if user_exists(user) == False:
            add_user(user)
        balance=cursor.execute("select " + token_name + " from balances where username=?",(user,)).fetchone()[0]
        return int(balance)
    else:
        return None
  


def get_token_list():
    token_list = cursor.execute("PRAGMA table_info(balances)").fetchall()
    token_names = []
    for token in token_list:
        token_names.append(token[1])
    token_names.pop(0)
    return token_names


def get_balances(user):
    if user_exists(user) == False:
        add_user(user)
    balances = list(cursor.execute("select * from balances where username=?", (user,)).fetchone())
    token_names = get_token_list()
    balances.pop(0)
    return dict(zip(token_names, balances))