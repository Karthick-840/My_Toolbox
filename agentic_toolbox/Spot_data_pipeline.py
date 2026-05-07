import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Script generated for node Artist
Artist_node1731220987999 = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://project-test-spot-data-with-date/staging/spotify_artist_data_2023.csv"], "recurse": True}, transformation_ctx="Artist_node1731220987999")

# Script generated for node Tracks
Tracks_node1731220988157 = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://project-test-spot-data-with-date/staging/spotify_tracks_data_2023.csv"], "recurse": True}, transformation_ctx="Tracks_node1731220988157")

# Script generated for node Album
Album_node1731220987664 = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://project-test-spot-data-with-date/staging/spotify-albums_data_2023.csv"], "recurse": True}, transformation_ctx="Album_node1731220987664")

job.commit()