import MySQLdb

def connection():
	conn = MySQLdb.connect(host="localhost",
							user = "web_a",
							passwd = "123456",
							db = "Record")
	c = conn.cursor()

	return c, conn 