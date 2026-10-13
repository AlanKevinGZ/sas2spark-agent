from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("smoke").getOrCreate()


df = (
    spark.read.option("header", "true")  
    .option("inferSchema", "true")  
    .csv("cases/01_data_step_basic/input/transactions.csv")
)

df.printSchema()
df.show(5)

spark.stop()