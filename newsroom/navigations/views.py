import re
import flask
import json
from bson import ObjectId
from flask import jsonify, current_app as app
from flask_babel import gettext
from superdesk import get_resource_service

from newsroom.auth.decorator import admin_only
from newsroom.navigations import blueprint
from newsroom.products.products import get_products_by_navigation
from newsroom.utils import get_json_or_400, get_entity_or_404, get_file, query_resource


def get_settings_data():
    return {
        'products': list(query_resource('products')),
        'navigations': list(query_resource('navigations')),
        'sections': app.sections,
    }


@blueprint.route('/navigations', methods=['GET'])
def index():
    navigations = list(query_resource('navigations', lookup=None))
    return jsonify(navigations), 200


@blueprint.route('/navigations/search', methods=['GET'])
@admin_only
def search():
    lookup = None
    if flask.request.args.get('q'):
        regex = re.compile('.*{}.*'.format(flask.request.args.get('q')), re.IGNORECASE)
        lookup = {'name': regex}
    products = list(query_resource('navigations', lookup=lookup))
    return jsonify(products), 200


@blueprint.route('/navigations/new', methods=['POST'])
@admin_only
def create():
    data = json.loads(flask.request.form['navigation'])
    nav_data = _get_navigation_data(data)

    ids = get_resource_service('navigations').post([nav_data])
    return jsonify({'success': True, '_id': ids[0]}), 201


def _get_navigation_data(data):
    if not data.get('name'):
        return jsonify(gettext('Name not found')), 400

    navigation_data = {
        'name': data.get('name'),
        'description': data.get('description'),
        'is_enabled': data.get('is_enabled'),
        'product_type': data.get('product_type'),
        'tile_images': data.get('tile_images')
    }

    for index, tile in enumerate(navigation_data['tile_images'] or []):
        file_url = get_file('file{}'.format(index))
        if file_url:
            tile['file_url'] = file_url

    return navigation_data


@blueprint.route('/navigations/<_id>', methods=['POST'])
@admin_only
def edit(_id):
    get_entity_or_404(_id, 'navigations')

    data = json.loads(flask.request.form['navigation'])
    nav_data = _get_navigation_data(data)

    get_resource_service('navigations').patch(id=ObjectId(_id), updates=nav_data)
    return jsonify({'success': True}), 200


@blueprint.route('/navigations/<_id>', methods=['DELETE'])
@admin_only
def delete(_id):
    """ Deletes the navigations by given id """
    get_entity_or_404(_id, 'navigations')

    # remove all references from products
    db = app.data.get_mongo_collection('products')
    products = get_products_by_navigation(_id)
    for product in products:
        db.update_one({'_id': product['_id']}, {'$pull': {'navigations': _id}})

    get_resource_service('navigations').delete({'_id': ObjectId(_id)})
    return jsonify({'success': True}), 200


@blueprint.route('/navigations/<_id>/products', methods=['POST'])
@admin_only
def save_navigation_products(_id):
    get_entity_or_404(_id, 'navigations')
    data = get_json_or_400()
    products = list(query_resource('products'))

    db = app.data.get_mongo_collection('products')
    for product in products:
        if str(product['_id']) in data.get('products', []):
            db.update_one({'_id': product['_id']}, {'$addToSet': {'navigations': _id}})
        else:
            db.update_one({'_id': product['_id']}, {'$pull': {'navigations': _id}})

    return jsonify(), 200
