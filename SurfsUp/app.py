import numpy as np
import re
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.sql import exists  

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the tables
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start (enter as YYYY-MM-DD)<br/>"
        f"/api/v1.0/start/end (enter as YYYY-MM-DD/YYYY-MM-DD)"

    )


@app.route("/api/v1.0/precipitation") #Convert query results to a dictionary using `date` as the key and `tobs` as the value
def precipitation():
    # Create session (link) from Python to the DB
    session = Session(engine)

    # Query Measurement
    results = (session.query(Measurement.date, Measurement.tobs)
                      .order_by(Measurement.date))
    
    # Create a dictionary
    precipitation_date_tobs = []
    for each_row in results:
        dt_dict = {}
        dt_dict["date"] = each_row.date
        dt_dict["tobs"] = each_row.tobs
        precipitation_date_tobs.append(dt_dict)

    return jsonify(precipitation_date_tobs)


@app.route("/api/v1.0/stations") #Return a JSON list of stations from the dataset
def stations():
    # Create session (link) from Python to the DB
    session = Session(engine)

    # Query Stations
    results = session.query(Station.name).all()

    # Convert list of tuples into normal list
    station_details = list(np.ravel(results))

    return jsonify(station_details)


@app.route("/api/v1.0/tobs") # Query the dates and temperature observations of the most active station for the last year of data
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query Measurements for latest date and calculate query_start_date
    latest_date = (session.query(Measurement.date)
                          .order_by(Measurement.date
                          .desc())
                          .first())
    
    latest_date_str = str(latest_date)
    latest_date_str = re.sub("'|,", "",latest_date_str)
    latest_date_obj = dt.datetime.strptime(latest_date_str, '(%Y-%m-%d)')
    query_start_date = dt.date(latest_date_obj.year, latest_date_obj.month, latest_date_obj.day) - dt.timedelta(days=366)
     
    # Query station names and their observation counts sorted descending and select most active station
    q_station_list = (session.query(Measurement.station, func.count(Measurement.station))
                             .group_by(Measurement.station)
                             .order_by(func.count(Measurement.station).desc())
                             .all())
    
    station_hno = q_station_list[0][0]
    print(station_hno)


    # Return a list of tobs for the year before the final date
    results = (session.query(Measurement.station, Measurement.date, Measurement.tobs)
                      .filter(Measurement.date >= query_start_date)
                      .filter(Measurement.station == station_hno)
                      .all())

    # Create JSON results
    tobs_list = []
    for result in results:
        line = {}
        line["Date"] = result[1]
        line["Station"] = result[0]
        line["Temperature"] = int(result[2])
        tobs_list.append(line)

    return jsonify(tobs_list)


@app.route("/api/v1.0/<start>") # Calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date
def start_only(start):

    # Create session (link) from Python to the DB
    session = Session(engine)

    # Date Range (only for help to user in case date gets entered wrong)
    date_range_max = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    date_range_max_str = str(date_range_max)
    date_range_max_str = re.sub("'|,", "",date_range_max_str)
    print (date_range_max_str)

    date_range_min = session.query(Measurement.date).first()
    date_range_min_str = str(date_range_min)
    date_range_min_str = re.sub("'|,", "",date_range_min_str)
    print (date_range_min_str)


    # Check for valid entry of start date
    valid_entry = session.query(exists().where(Measurement.date == start)).scalar()
 
    if valid_entry:

    	results = (session.query(func.min(Measurement.tobs)
    				 ,func.avg(Measurement.tobs)
    				 ,func.max(Measurement.tobs))
    				 	  .filter(Measurement.date >= start).all())

    	tmin =results[0][0]
    	tavg ='{0:.4}'.format(results[0][1])
    	tmax =results[0][2]
    
    	result_printout =( ['Entered Start Date: ' + start,
    						'The lowest Temperature was: '  + str(tmin) + ' F',
    						'The average Temperature was: ' + str(tavg) + ' F',
    						'The highest Temperature was: ' + str(tmax) + ' F'])
    	return jsonify(result_printout)

    return jsonify({"error": f"Input Date {start} not valid. Date Range is {date_range_min_str} to {date_range_max_str}"}), 404
   

@app.route("/api/v1.0/<start>/<end>") # Calculate the `TMIN`, `TAVG`, and `TMAX` for dates between the start and end date inclusive
def start_end(start, end):

    # Create session (link) from Python to the DB
    session = Session(engine)

    # Date Range (only for help to user in case date gets entered wrong)
    date_range_max = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    date_range_max_str = str(date_range_max)
    date_range_max_str = re.sub("'|,", "",date_range_max_str)
    print (date_range_max_str)

    date_range_min = session.query(Measurement.date).first()
    date_range_min_str = str(date_range_min)
    date_range_min_str = re.sub("'|,", "",date_range_min_str)
    print (date_range_min_str)

    # Check for valid entry of start date
    valid_entry_start = session.query(exists().where(Measurement.date == start)).scalar()
 	
 	# Check for valid entry of end date
    valid_entry_end = session.query(exists().where(Measurement.date == end)).scalar()

    if valid_entry_start and valid_entry_end:

    	results = (session.query(func.min(Measurement.tobs)
    				 ,func.avg(Measurement.tobs)
    				 ,func.max(Measurement.tobs))
    					  .filter(Measurement.date >= start)
    				  	  .filter(Measurement.date <= end).all())

    	tmin =results[0][0]
    	tavg ='{0:.4}'.format(results[0][1])
    	tmax =results[0][2]
    
    	result_printout =( ['Entered Start Date: ' + start,
    						'Entered End Date: ' + end,
    						'The lowest Temperature was: '  + str(tmin) + ' F',
    						'The average Temperature was: ' + str(tavg) + ' F',
    						'The highest Temperature was: ' + str(tmax) + ' F'])
    	return jsonify(result_printout)

    if not valid_entry_start and not valid_entry_end:
    	return jsonify({"error": f"Input Start {start} and End Date {end} not valid. Date Range is {date_range_min_str} to {date_range_max_str}"}), 404

    if not valid_entry_start:
    	return jsonify({"error": f"Input Start Date {start} not valid. Date Range is {date_range_min_str} to {date_range_max_str}"}), 404

    if not valid_entry_end:
    	return jsonify({"error": f"Input End Date {end} not valid. Date Range is {date_range_min_str} to {date_range_max_str}"}), 404


if __name__ == '__main__':
    app.run(debug=True)
