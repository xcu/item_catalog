# item_catalog
Third project for Udacity Full Stack dev Nanodegree

# How to run the application
Apart from cloning the repository you will need to provide a file named 'client_secrets.json' with your app details. You can download the one for your app by entering in https://console.developers.google.com and Select Download JSON in the Credentials submenu.
The code has been tested with the following versions:
- Flask (0.10.1)
- Flask-OAuth2-Login (0.0.9)
- Flask-Session (0.1.1)
- oauth (1.0.1)
- oauth2client (1.4.11)
- oauthlib (0.7.2)
- SQLAlchemy (0.8.4)
- requests (2.2.1)
- requests-oauthlib (0.4.2)
- bleach (1.4.1)
Most of them are included in the vagrant VM provided for the course. I only had to install Flask-Session (and only because I wanted to try other types of sessions, the default ones would serve just the same).
Once the repo is cloned and the dependencies are installed you just need to run python project.py
After that open your browser and check http://localhost:5000

# Features
- Implemented a REST compliant API for two basic endpoints: categories and items. They both support POST, PUT, GET and DELETE requests. Most of them support several endpoint types, such as HTTP, JSON and XML (for example, DELETE requests don't send back HTML responses since browsers don't use them unless you explicitely ask for it using Javascript or a handcrafted request. In any case you probably don't want HTML).
- To know in which mimetype the user wants the response the request headers are inspected.
- Items support adding an additional image field. The image is displayed when the item details are requested.
- CSRF protection: all the requests that could alter the database information are protected using a token sent from the server side.
- Authentication: all the requests to add, edit or delete information require prior authentication using a Google id.
- It was my first contact with Javascript after quite a while, so I tried to focus on that side a little bit to refresh my memory. I know there are several improvements that could still be done, both there and on the server side, but at some point you have to step the development and move on to the next project!
