import sqlite3

"""db_adapter.py: Manages access to sqlite database """

__author__ = "Daniel Skyrme, Joe Lovell"
__licence__ = "GNU General Public License v3.0"
__email__ = "danielskyrme@hotmail.com"
__credits__ = ["Joe Lovell"]


class DataBaseAdapter:
    DB_FILE_NAME = "res/space_clones.db"
    HIGH_SCORE_DB_NAME = "highscores"
    COLUMN_SCORE = "score"

    def create_connection(self):
        try:
            return sqlite3.connect(DataBaseAdapter.DB_FILE_NAME, timeout=10)
        except sqlite3.Error as e:
            print(e)
        return None

    def get_high_score(self):
        connection = self.create_connection()
        cursor = connection.cursor()
        query = "select {cn} from {tn};".format(tn=DataBaseAdapter.HIGH_SCORE_DB_NAME, cn=DataBaseAdapter.COLUMN_SCORE)
        print(query)
        cursor.execute(query)
        rows = cursor.fetchall()
        if len(rows) == 0:
            self.set_high_score(0)
            return 0
        connection.close()
        return rows[0][0]

    def set_high_score(self, value):
        connection = self.create_connection()
        cursor = connection.cursor()
        q1 = "delete from {tn};".format(tn=DataBaseAdapter.HIGH_SCORE_DB_NAME)
        q2 = "insert into {tn} ({cn}) VALUES({val});".format(tn=DataBaseAdapter.HIGH_SCORE_DB_NAME,
                                                             cn=DataBaseAdapter.COLUMN_SCORE,
                                                             val=value)
        script = q1 + ";\n" + q2
        print(script)
        cursor.executescript(script)
        connection.commit()
        connection.close()
