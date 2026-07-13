import sqlite3
conn = sqlite3.connect('db.sqlite3')
conn.execute("DROP TABLE IF EXISTS analysis_skillgap")
conn.execute("DROP TABLE IF EXISTS analysis_userroadmap")
conn.execute("DELETE FROM django_migrations WHERE app='analysis'")
conn.commit()
print('done')