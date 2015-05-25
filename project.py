from flask import Flask, render_template, request, redirect,jsonify, url_for,\
    session as login_session, make_response, flash
# sudo pip install Flask-Session
from flask.ext.session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fullstack_nanodegree.item_catalog.database_setup import Base, Category, Item
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from functools import wraps
import httplib2
import json
import requests

app = Flask(__name__)
app.secret_key = 'wat'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
LAST_ITEMS_NUM = 10
# http://flask.pocoo.org/docs/0.10/blueprints/

def request_wants_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


@app.route('/')
def main_page():
    last_items = session.query(Item).order_by('id desc').limit(LAST_ITEMS_NUM).all()
    last_items = [(i, _get_category(i)) for i in last_items]
    all_categories = session.query(Category).order_by('name').all()
    return render_template('main.html',
                           last_items=last_items,
                           all_categories=all_categories,
                           session=login_session
    )


@app.route('/login')
def show_login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


def login_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if login_session.get('logged_in'):
            return func(*args, **kwargs)
        else:
            return redirect(url_for('show_login'))
    return inner

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['logged_in'] = True

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % credentials
    h = httplib2.Http()
    header, _ = h.request(url, 'GET')

    if header['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        login_session['logged_in'] = False

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/category/', methods=['POST'])
@login_required
def add_category():
    _validate_new_category(request.form)
    new_cat = Category(name=request.form['name'])
    session.add(new_cat)
    session.commit()
    return jsonify(
        type_added='category',
        href=url_for('get_category', category_id=new_cat.id),
        name=new_cat.name
    )


@app.route('/category/<int:category_id>', methods=['GET'])
def get_category(category_id):
    return render_template('category.html',
                           category_id=category_id,
                           category=session.query(Category).filter_by(
                                                                id=category_id
                                                                      ).one(),
                           all_categories=session.query(
                                                        Category
                                                        ).order_by('name').all(),
                           items=_get_items_per_category(category_id),
                           session=login_session
    )


@login_required
@app.route('/category/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    category_obj = session.query(Category).filter_by(id=category_id).one()
    session.delete(category_obj)
    _delete_all_category_items(category_id)
    session.commit()
    return jsonify(redirect=url_for('main_page'))


def _delete_all_category_items(category_id):
    for item in _get_items_per_category(category_id):
        _do_delete_item(item.id)


@login_required
@app.route('/item/', methods=['POST'])
def add_item():
    _validate_new_item(request.form)
    category_id = session.query(Category).filter_by(
                                            id=request.form['category']
                                                    ).one().id
    new_item = Item(name=request.form['name'],
                    description=request.form['description'],
                    category_id=category_id
                )
    session.add(new_item)
    session.commit()
    return jsonify(
        type_added='item',
        href=url_for('get_item', item_id=new_item.id),
        name=new_item.name
    )


@app.route('/item/<int:item_id>', methods=['GET'])
def get_item(item_id):
    return render_template('item.html',
                           item_id=item_id,
                           item=session.query(Item).filter_by(id=item_id).one(),
                           session=login_session
    )


@login_required
@app.route('/item/<int:item_id>', methods=['PUT'])
def edit_item(item_id):
    item_obj = session.query(Item).filter_by(id=item_id).one()
    if request.form.get('name'):
        item_obj.name = request.form['name']
    if request.form.get('description'):
        item_obj.description = request.form['description']
    session.add(item_obj)
    session.commit()
    return jsonify(item_id=item_obj.id,
                   item_name=item_obj.name,
                   item_desc=item_obj.description)


@login_required
@app.route('/item/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    _do_delete_item(item_id)
    return jsonify(redirect=url_for('main_page'))


def _do_delete_item(item_id):
    item_obj = session.query(Item).filter_by(id=item_id).one()
    session.delete(item_obj)
    session.commit()


def _validate_new_category(cat_dict):
    for required_attr in ['name']:
        if not cat_dict.get(required_attr):
            raise Exception("{0} not found in form to add an item".format(
                                                                required_attr
                                                                          )
                  )

def _validate_new_item(item_dict):
    for required_attr in ['category', 'name', 'description']:
        if not item_dict.get(required_attr):
            raise Exception("{0} not found in form to add an item".format(
                                                                required_attr
                                                                          )
                  )


def _get_category(item):
    # picks the category item related to item
    return session.query(Category).join(Item.category).filter_by(
                                                            id=item.category_id
                                                                 ).one()


def _get_items_per_category(category_id):
    return session.query(Item).filter_by(category_id=category_id).all()


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
