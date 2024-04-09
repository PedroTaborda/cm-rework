### Deprecated

This project is deprecated. The API used by the Carris Metropolitana website has changed and better tools have been developed for end users. The data is now also available in popular apps like Google Maps. The hosted version of the web app no longer works but the code is still available for reference and the frontend can still be accessed.

# Python API for Carris Metropolitana Bus Lines

This is a Python API for Carris Metropolitana Bus Lines. It uses the API used by the [Carris Metropolitana website](https://www.carrismetropolitana.pt/horarios/). This project is not affiliated with Carris Metropolitana.

The largest benefit of this API is the ability to get the next bus times for a given bus stop, for all bus lines that pass through it. This is not possible with the Carris Metropolitana website, which only shows the next bus times for a given bus line and bus stop.


## Dependencies

- [Requests](https://pypi.org/project/requests/): HTTP requests

# Flask web app

This project also includes a Flask web app that uses the API. It is a simple web app that allows you to search for a bus stop and see the next bus times for all bus lines that pass through it going to some destination.

Under [horarios.pedrotaborda.me](http://horarios.pedrotaborda.me/), you can find a hosted version of the web app. 

## Dependencies

- [Flask](https://pypi.org/project/Flask/): Web framework
