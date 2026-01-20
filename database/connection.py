import mysql.connector as SQLC

#login to database
database_config = SQLC.connect(
                        host='localhost',
                        user='root',
                        password='tiger',
                        database = 'notes_management3234' #mysql workbench password
                    )

#creating cursor object

cursor = database_config.cursor()
#print(database_config)
#print(cursor)

#creating database
#create_database_query = "CREATE DATABASE IF NOT EXISTS ANIMALS;"

#3.execute() function is used to execute the sql queries
#cursor.execute(create_database_query)
#print("Database created successfully")

# selecting database
#cursor.execute("USE ANIMALS;")

# creating table
# animal_table_query = """
#                CREATE TABLE ANIMAL(
 #               NAME VARCHAR(30),
  #              AGE INT
   #             );"""
#cursor.execute(animal_table_query)
#print(cursor)
#print("Table created successfully")
