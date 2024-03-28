import sqlite3

class MyDatabase:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS my_table (
                guild_id INTEGER PRIMARY KEY,
                default_name TEXT DEFAULT '名無しさん＠お腹いっぱい。',
                count INTEGER DEFAULT 1
            )
        ''')
        self.conn.commit()

    def insert_data(self, guild_id, default_name=None, count=None):
        if default_name is None:
            default_name = '名無しさん＠お腹いっぱい。'
        if count is None:
            count = 1
        self.cursor.execute('''
            INSERT INTO my_table (guild_id, default_name, count)
            VALUES (?, ?, ?)
        ''', (guild_id, default_name, count))
        self.conn.commit()

    # guild_id, default_nameを引数にとり、default_nameを更新する
    def update_name(self, guild_id, default_name):
        self.cursor.execute('''
            UPDATE my_table SET default_name=? WHERE guild_id=?
        ''', (default_name, guild_id))
        self.conn.commit()

    # guild_idを引数にとり、countに1を足す
    def update_count(self, guild_id):
        self.cursor.execute('''
            UPDATE my_table SET count=count+1 WHERE guild_id=?
        ''', (guild_id,))
        self.conn.commit()

    # guild_idを引数にとり、default_nameを返す
    def select_name(self, guild_id):
        self.cursor.execute('''
            SELECT default_name FROM my_table WHERE guild_id=?
        ''', (guild_id,))
        return self.cursor.fetchone()
    
    # guild_idを引数にとり、countを返す。登録がない場合はNoneを返す
    def select_count(self, guild_id):
        self.cursor.execute('''
            SELECT count FROM my_table WHERE guild_id=?
        ''', (guild_id,))
        return self.cursor.fetchone()

    def delete_data(self, guild_id):
        self.cursor.execute('''
            DELETE FROM my_table WHERE guild_id=?
        ''', (guild_id,))
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()