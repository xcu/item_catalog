from flask import Flask, render_template, request, redirect, jsonify, url_for, \
    session as login_session, make_response, flash
# sudo pip install Flask-Session
from flask.ext.session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from database_setup import Base, Category, Item
from oauth_connector import OauthConnector
from xml.dom.minidom import Document
import random
import string
from functools import wraps
import json
import bleach


app = Flask(__name__)
app.secret_key = 'wat'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

LAST_ITEMS_NUM = 10
ENDPOINT_TYPES = {'text/html': 'html',
                  'application/json': 'json',
                  'application/xml': 'xml'}
DEFAULT_ENDPOINT = 'application/json'


def requested_endpoint_type():
    # returns the mimetype specified in the header, or the default one if
    # the requested one is not available
    key = request.accept_mimetypes.best_match(ENDPOINT_TYPES.keys())
    return ENDPOINT_TYPES.get(key, DEFAULT_ENDPOINT)


def return_from_mimetype(mimetype_dictionary):
    # calls the appropriate function for each supported mimetype with the
    # right arguments
    mimetype = requested_endpoint_type()
    if mimetype == 'json':
        _, kwargs = mimetype_dictionary[mimetype]
        return jsonify(**kwargs)
    elif mimetype == 'html':
        template_name, kwargs = mimetype_dictionary[mimetype]
        return render_template(template_name, **kwargs)
    elif mimetype == 'xml':
        f, args = mimetype_dictionary[mimetype]
        return f(*args)
    raise NotImplementedError('wat')


def login_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if login_session.get('logged_in'):
            return func(*args, **kwargs)
        return redirect(url_for('show_login'))

    return inner


def csrf_protected(func):
    @wraps(func)
    def inner(*args, **kwargs):
        csrf_token = request.form.get('token', '')
        if csrf_token == login_session.get('state') and bool(csrf_token):
            return func(*args, **kwargs)
        # csrf detected
        response = make_response(
            json.dumps('Your request could not be processed'),
            401
        )
        response.headers['Content-Type'] = 'application/json'
        return response

    return inner


def _validate_new_category(cat_dict):
    for required_attr in ['name']:
        if not cat_dict.get(required_attr):
            raise Exception("{0} not found in form to add an item".format(
                required_attr)
            )
    if not session.query(Category).filter_by(name=cat_dict['name']).all():
        return
    response = make_response(
        json.dumps('This name exists, please pick another one'),
        404
    )
    response.headers['Content-Type'] = 'application/json'
    return response


def _validate_new_item(item_dict):
    for required_attr in ['category', 'name', 'description']:
        if not item_dict.get(required_attr):
            raise Exception("{0} not found in form to add an item".format(
                required_attr)
            )


def _get_category(item):
    # picks the category item related to item
    return session.query(Category).join(Item.category).filter_by(
        id=item.category_id
    ).one()


def _get_items_per_category(category_id):
    return session.query(Item).filter_by(category_id=category_id).all()


@app.route('/')
def main_page():
    last_items = session.query(Item). \
        order_by('id desc').limit(LAST_ITEMS_NUM).all()
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
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    return OauthConnector().connect()


@app.route('/gdisconnect')
def gdisconnect():
    return OauthConnector().disconnect()


def category_xml(category):
    # xml representation of a category
    doc = Document()
    base = doc.createElement('category')
    doc.appendChild(base)
    desc = doc.createElement('description')
    desc_text = doc.createTextNode(category.name)
    desc.appendChild(desc_text)
    base.appendChild(desc)
    return doc.toxml(encoding='utf-8')


def item_xml(item, category):
    # xml representation of an item
    doc = Document()
    base = doc.createElement('item')
    doc.appendChild(base)
    for (name, val) in [('href', url_for('get_item', item_id=item.id)),
                        ('name', item.name),
                        ('description', item.description),
                        ('image', item.image),
                        ('category_name', category.name),
                        ('category_url', url_for('get_category',
                                          category_id=category.id))]:
        desc = doc.createElement(name)
        desc_text = doc.createTextNode(val)
        desc.appendChild(desc_text)
        base.appendChild(desc)
    return doc.toxml(encoding='utf-8')


@app.route('/category', methods=['POST'])
@csrf_protected
@login_required
def add_category():
    error = _validate_new_category(request.form)
    if error:
        return error
    new_cat = Category(name=bleach.clean(request.form['name']))
    session.add(new_cat)
    session.commit()
    json_args = ((),
                 {'type_added': 'category',
                  'href': url_for('get_category', category_id=new_cat.id),
                  'name': new_cat.name
                  })
    html_args = ('one_category.html',
                 {'category': new_cat})
    xml_args = (category_xml, (new_cat,))
    return return_from_mimetype({'json': json_args,
                                 'html': html_args,
                                 'xml': xml_args})


@app.route('/category/<int:category_id>', methods=['GET'])
def get_category(category_id):
    try:
        category = session.query(Category).filter_by(id=category_id).one()
        all_categories = session.query(Category).order_by('name').all()
    except NoResultFound:
        return make_response('Element not found', 404)
    json_args = ((), {'id': category_id, 'name': category.name})
    html_args = ('category.html',
                 {'category_id': category_id,
                  'category': category,
                  'all_categories': all_categories,
                  'items': _get_items_per_category(category_id),
                  'session': login_session
                  })
    xml_args = (category_xml, (category,))
    return return_from_mimetype({'json': json_args,
                                 'html': html_args,
                                 'xml': xml_args})



@app.route('/category/<int:category_id>', methods=['DELETE'])
@csrf_protected
@login_required
def delete_category(category_id):
    category_obj = session.query(Category).filter_by(id=category_id).one()
    session.delete(category_obj)
    _delete_all_category_items(category_id)
    session.commit()
    json_args = ((), {'redirect': url_for('main_page')})
    return return_from_mimetype({'json': json_args})


def _delete_all_category_items(category_id):
    for item in _get_items_per_category(category_id):
        _do_delete_item(item.id)


@app.route('/item', methods=['POST'])
@csrf_protected
@login_required
def add_item():
    _validate_new_item(request.form)
    category = session.query(Category).filter_by(
        id=request.form['category']
    ).one()
    new_item = Item(bleach.clean(name=request.form['name']),
                    bleach.clean(description=request.form['description']),
                    bleach.clean(image=request.form.get('url', '')),
                    category_id=category.id
                    )
    session.add(new_item)
    session.commit()
    json_args = ((),
                 {'type_added': 'item',
                  'href': url_for('get_item', item_id=new_item.id),
                  'name': new_item.name,
                  'image': new_item.image,
                  'category_name': category.name,
                  'category_url': url_for('get_category',
                                          category_id=category.id)
                  })
    html_args = ('one_item_thumb.html',
                 {'item': new_item, 'category': category})
    xml_args = (item_xml, (new_item, category))
    return return_from_mimetype({'json': json_args,
                                 'html': html_args,
                                 'xml': xml_args})



@app.route('/item/<int:item_id>', methods=['GET'])
def get_item(item_id):
    try:
        item = session.query(Item).filter_by(id=item_id).one()
        category = _get_category(item)
    except NoResultFound:
        return make_response('Element not found', 404)
    json_args = ((),
                 {'name': item.name,
                  'image': item.image,
                  'id': item.id
                  })
    html_args = ('item.html',
                 {'item_id': item_id,
                  'item': item,
                  'session': login_session
                  })
    xml_args = (item_xml, (item, category))
    return return_from_mimetype({'json': json_args,
                                 'html': html_args,
                                 'xml': xml_args})



@app.route('/item/<int:item_id>', methods=['PUT'])
@csrf_protected
@login_required
def edit_item(item_id):
    try:
        item = session.query(Item).filter_by(id=item_id).one()
        category = _get_category(item)
    except NoResultFound:
        return make_response('Element not found', 404)
    if request.form.get('name'):
        item.name = bleach.clean(request.form['name'])
    if request.form.get('description'):
        item.description = bleach.clean(request.form['description'])
    if request.form.get('url'):
        item.image = bleach.clean(request.form['url'])
    session.add(item)
    session.commit()
    json_args = ((),
                 {'item_name': item.name,
                  'item_image': item.image,
                  'item_id': item.id,
                  'item_desc': item.description
                  })
    html_args = ('one_item_thumb.html',
                 {'item': item, 'category': category})
    xml_args = (item_xml, (item, category))
    return return_from_mimetype({'json': json_args,
                                 'html': html_args,
                                 'xml': xml_args})


@app.route('/item/<int:item_id>', methods=['DELETE'])
@csrf_protected
@login_required
def delete_item(item_id):
    _do_delete_item(item_id)
    return jsonify(redirect=url_for('main_page'))


def _do_delete_item(item_id):
    item_obj = session.query(Item).filter_by(id=item_id).one()
    session.delete(item_obj)
    session.commit()


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
