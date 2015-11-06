from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask import flash, make_response, session as login_session
from flask import send_from_directory
from werkzeug import secure_filename
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from nocache import nocache
from database_setup import Base, Category, Item, User
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import os, random, string, httplib2, json, requests


# Set global variables
app = Flask(__name__)
APPLICATION_NAME = "Item Catalog"
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'bmp'])
DEV_MODE = False


# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------

# User Helper Functions

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Picture Helper Functions

def uploadFile(item):
    # Check if file was specified
    file = request.files['image']
    filename = file.filename
    # Check file for correct extension
    if not '.' in filename:
        flash('Warning: Item image ''%s'' was not attached because the file \
            name is not in the standard format of <filename>.<extension>. \
            You may still add an image by editing the item.' % (filename))
        return ''
    file_ext = filename.rsplit('.', 1)[1]
    if not file_ext in ALLOWED_EXTENSIONS:
        flash('Warning: Item image ''%s'' was not attached because it is not \
            a known image format. You may still add an image by \
            editing the item.' % (filename))
        return ''
    # Check file size is below 8 MB
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    if file_size > 8*1024*1024:
        flash('Warning: Item image ''%s'' was not attached because it \
            exceeded the maximum file size of 16 MB. You may still add an \
            image by editing the item.' % (filename))
        return ''
    file.seek(0, os.SEEK_SET)
    # Set save path
    filename =  item.category.name + '_' + item.name + '.' + file_ext
    try:
        file.save(os.path.join(UPLOAD_FOLDER, filename))
    except:
        flash('Warning: Item image ''%s'' was not attached because there was \
            an error during upload. You may still add an image by \
            editing the item.' % (filename))
    return filename


def deleteFile(item):
    if item.picture:
        try:
            os.remove(UPLOAD_FOLDER + item.picture)
        except:
            flash('Warning: The file ''%s'' was not deleted because there \
            was an error during delete.' % (item.picture))
        item.picture = ''
    return


# -----------------------------------------------------------------------------
# Picture Route
# -----------------------------------------------------------------------------

@app.route('/uploads/<path:filename>')
def showFile(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
@app.route('/test/')


# -----------------------------------------------------------------------------
# JSON APIs
# -----------------------------------------------------------------------------

# Entire Catalog
@app.route('/catalog.json')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[r.serialize for r in categories])


# Individual Category
@app.route('/catalog/<string:category_name>.json')
def catalogJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    return jsonify(listItems=[i.serialize for i in category.items])


# -----------------------------------------------------------------------------
# Category Routes
# -----------------------------------------------------------------------------


# Show all categories
@app.route('/')
def showRoot():
    return redirect(url_for('showCategories'))


@app.route('/catalog/')
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('catalog.html', categories=categories)


# View category details
@app.route('/catalog/<string:category_name>/')
def showCategory(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    return render_template('category.html', category=category)


# Create a new category
@app.route('/catalog/new', methods=['GET', 'POST'])
def newCategory():
    # Verify authentication
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'], user_id=login_session['user_id'])
        # Make sure the category name isn't used
        oldCategory = session.query(Category).\
            filter_by(name=newCategory.name).first()
        if oldCategory != None:
            flash('Danger: New category %s was not created. There is already \
                a category by that name.' % (newCategory.name))
            return render_template('categoryNew.html')
        # Create the new category
        session.add(newCategory)
        flash('Success: Created New Category %s' % (newCategory.name))
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('categoryNew.html')


# Edit a category
@app.route('/catalog/<string:category_name>/edit', methods=['GET', 'POST'])
def editCategory(category_name):
    editedCategory = session.query(
        Category).filter_by(name=category_name).one()
    # Verify authentication
    if 'username' not in login_session:
        return redirect('/catalog/login')
    #Verify authorization
    if editedCategory.user_id != login_session['user_id']:
        flash('Danger: You are not authorized to edit this category. Please \
            create your own category in order to edit.')
        return redirect(url_for('showCategory', category_name=category_name))
    if request.method == 'POST':
        # Make sure the category name isn't used
        oldCategory = session.query(Category).\
            filter_by(name=editedCategory.name).first()
        if oldCategory != None and oldCategory != editedCategory:
            flash('Danger: Category %s was not edited. There is already \
                a category by that name.' % (editedCategory.name))
            return render_template('categoryEdit.html', \
                category=editedCategory)
        # Update the category
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Success: Edited Category %s' % (editedCategory.name))
            session.commit()
            return redirect(url_for('showCategory', \
                category_name=editedCategory.name))
    else:
        return render_template('categoryEdit.html', category=editedCategory)


# Delete a category
@app.route('/catalog/<string:category_name>/delete', methods=['GET', 'POST'])
def deleteCategory(category_name):
    deletedCategory = session.query(
        Category).filter_by(name=category_name).one()
    # Verify authentication
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    #Verify authorization
    if deletedCategory.user_id != login_session['user_id']:
        flash('Danger: You are not authorized to delete this category. \
            Please create your own category in order to delete.')
        return redirect(url_for('showCategory', category_name=category_name))
    if request.method == 'POST':
        # Delete category items
        for item in deletedCategory.items:
            deleteFile(item)
            session.delete(item)
        # Delete the category
        session.delete(deletedCategory)
        flash('Success: Deleted Category %s' % (category_name))
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('categoryDelete.html', \
            category=deletedCategory)


# -----------------------------------------------------------------------------
# Item Routes
# -----------------------------------------------------------------------------

# View item details
@app.route('/catalog/<string:category_name>/<string:item_name>/')
@nocache
def showItem(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name).one()
    return render_template('item.html', item=item)


# Create a new item
@app.route('/catalog/<string:category_name>/new', methods=['GET', 'POST'])
def newItem(category_name):
    # Verify authentication
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    category = session.query(Category).filter_by(name=category_name).one()
    #Verify authorization
    if login_session['user_id'] != category.user_id:
        flash('Danger: You are not authorized to add items to this category. \
            Please create your own category in order to add items.')
        return redirect(url_for('showCategory', category_name=category_name))
    if request.method == 'POST':
        newItem = Item(name = request.form['name'], \
            description = request.form['description'], \
            category_id = category.id)
        # Make sure the item name isn't used
        oldItem = session.query(Item). \
            filter_by(category_id=category.id). \
            filter_by(name=newItem.name).first()
        if oldItem != None:
            flash('Danger: New item %s was not created. There is already \
                an item by that name.' % (newItem.name))
            return render_template('itemNew.html')
        # Create the new item
        session.add(newItem)
        session.flush()
        if request.files['image']:
            filename = uploadFile(newItem)
            newItem.picture = filename
        session.commit()
        flash('Success: Created New Item %s' % (newItem.name))
        return redirect(url_for('showCategory', category_name=category_name))
    else:
        return render_template('itemNew.html')


# Edit an item
@app.route('/catalog/<string:category_name>/<string:item_name>/edit', 
    methods=['GET', 'POST'])
def editItem(category_name, item_name):
    # Verify authentication
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    category = session.query(Category).filter_by(name=category_name).one()
    editedItem = session.query(Item).filter_by(name=item_name).one()
    #Verify authorization
    if login_session['user_id'] != category.user_id:
        flash('Danger: You are not authorized to edit items in this category. \
            Please create your own category in order to edit items.')
        return redirect(url_for('showItem', category_name=category_name, \
            item_name=item_name))
    if request.method == 'POST':
        # Make sure the item name isn't used
        oldItem = session.query(Item). \
            filter_by(category_id=category.id). \
            filter_by(name=editedItem.name).first()
        if oldItem != None and oldItem != editedItem:
            flash('Danger: Item %s was not edited. There is already \
                an item by that name.' % (editedItem.name))
            return render_template('itemEdit.html', item=editedItem)
        # Update the item
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form.get('deletebox', False):
            deleteFile(editedItem)
        if request.files['image']:
            deleteFile(editedItem)
            filename = uploadFile(editedItem)
            editedItem.picture = filename
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash('Success: Edited Item %s' % (editedItem.name))
        return redirect(url_for('showItem', category_name=category_name, \
            item_name=editedItem.name))
    else:
        return render_template('itemEdit.html', item=editedItem)


# Delete an item
@app.route('/catalog/<string:category_name>/<string:item_name>/delete', 
    methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    # Verify authentication
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    category = session.query(Category).filter_by(name=category_name).one()
    deletedItem = session.query(Item).filter_by(name=item_name).one()
    #Verify authorization
    if login_session['user_id'] != category.user_id:
        flash('Danger: You are not authorized to delete items from this \
            category. Please create your own category in order to delete \
            items.')
        return redirect(url_for('showItem', category_name=category_name, \
            item_name=item_name))
    if request.method == 'POST':
        # Delete the item
        deleteFile(deletedItem)
        session.delete(deletedItem)
        session.commit()
        flash('Success: Deleted Item %s' % (item_name))
        return redirect(url_for('showCategory', category_name=category_name))
    else:
        return render_template('itemDelete.html', item=deletedItem)


# -----------------------------------------------------------------------------
# Authentication Routes
# -----------------------------------------------------------------------------

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    google_id = json.loads(open(
        'client_secrets_google.json', 'r').read())['web']['client_id']
    facebook_id = json.loads(open(
        'client_secrets_facebook.json', 'r').read())['web']['app_id']
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # developer mode to fake login
    if DEV_MODE:
        login_session['username'] = 'Foobar'
        login_session['email'] = 'foobar@foobar.com'
        login_session['user_id'] = getUserID(login_session['email'])
        flash("Success: You are now logged in as %s" % (
            login_session['username']))
        return redirect(url_for('showCategories'))
    return render_template('login.html', STATE=state, google_id=google_id, \
        facebook_id=facebook_id)


# Facebook authentication connection
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    app_id = json.loads(open('client_secrets_facebook.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('client_secrets_facebook.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]
    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % (token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # Store token in session for proper logout
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % (token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Success: You are now logged in as %s" % (login_session['username']))
    return output


# Facebook disconnect
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


# Google authentication connect
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
        oauth_flow = flow_from_clientsecrets('client_secrets_google.json', scope='')
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
           % (access_token))
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
    client_id = json.loads(open(
        'client_secrets_google.json', 'r').read())['web']['client_id']
    if result['issued_to'] != client_id:
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
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("Success: You are now logged in as %s" % (login_session['username']))
    return output


# Google disconnect
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % (access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Generic disconnect points to provider
@app.route('/disconnect')
def disconnect():
    if DEV_MODE:
        del login_session['username']
        del login_session['email']
        del login_session['user_id']
        flash("Success: You have been logged out.")
        return redirect(url_for('showCategories'))
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("Success: You have been logged out.")
        return redirect(url_for('showCategories'))
    else:
        flash("Warning: You were not logged in.")
        return redirect(url_for('showCategories'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
