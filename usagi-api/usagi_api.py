import json
import subprocess
from flask import jsonify, Blueprint, request
from peewee import DataError
from config import APP_PREFIX, PORT, VERSION
from main import app
from model.usagi.code_mapping import ScoredConceptEncoder
from model.user.user import token_required
from service.search_service import search_usagi
from service.solr_cole_service import run_solr_command
from service.usagi_service import get_saved_code_mapping, create_concept_mapping, get_vocabulary_list_for_user, \
    load_mapped_concepts_by_vocabulary_name, delete_vocabulary, get_vocabulary_data, get_filters, load_codes_to_server, \
    save_codes
from service.web_socket_service import socket
from util.async_directive import cancel_concept_mapping_task, cancel_load_vocabulary_task
from util.constants import USAGI_IMPORT_STATUS, QUERY_SEARCH_MODE
from util.exception import InvalidUsage
from util.usagi_db import usagi_pg_db
from util.user_db import user_db
from util.vocabulary_db import vocabulary_pg_db

usagi = Blueprint('usagi', __name__, url_prefix=APP_PREFIX)


@app.before_request
def before_request():
    if usagi_pg_db.is_closed():
        usagi_pg_db.connect()

    if user_db.is_closed():
        user_db.connect()

    if vocabulary_pg_db.is_closed():
        vocabulary_pg_db.connect()


@app.after_request
def after_request(response):
    if not usagi_pg_db.is_closed():
        usagi_pg_db.close()

    if user_db.is_closed():
        user_db.connect()

    if vocabulary_pg_db.is_closed():
        vocabulary_pg_db.connect()

    return response


@usagi.route('/api/info', methods=['GET'])
def app_version():
    app.logger.info("REST request to GET app info")
    return jsonify({'name': 'Usagi', 'version': VERSION})


@usagi.route('/api/import_source_codes', methods=['POST'])
@token_required
def create_codes(current_user):
    app.logger.info("REST request to start creating concept mapping process")
    try:
        params = request.json['params']
        source_code_column = params['sourceCode']
        source_name_column = params['sourceName']
        source_frequency_column = params['sourceFrequency']
        auto_concept_id_column = params['autoConceptId']
        additional_info_columns = params['additionalInfo']
        concept_ids_or_atc = params['columnType']
        codes = request.json['codes']
        filters = request.json['filters']
        create_concept_mapping(current_user, codes, filters, source_code_column, source_name_column, source_frequency_column, auto_concept_id_column, concept_ids_or_atc, additional_info_columns)
    except InvalidUsage as error:
        raise error
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return jsonify('OK')


@usagi.route('/api/get_import_source_codes_results', methods=['GET'])
@token_required
def get_import_source_codes_results_call(current_user):
    app.logger.info("REST request GET concept mapping")
    try:
        import_source_codes_results = get_saved_code_mapping(current_user)
    except InvalidUsage as error:
        raise error
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return import_source_codes_results


@usagi.route('/api/load_codes_to_server', methods=['POST'])
@token_required
def load_codes_call(current_user):
    app.logger.info("REST request extract codes from CSV")
    """save schema to server and load it from server in the same request"""
    try:
        file = request.files['file']
        delimiter = request.form['delimiter']
        codes_file = load_codes_to_server(file, delimiter, current_user)
    except InvalidUsage as error:
        raise error
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return jsonify(codes_file)


@usagi.route('/api/get_term_search_results', methods=['POST'])
@token_required
def get_term_search_results_call(current_user):
    app.logger.info("REST request to GET term search result")
    try:
        filters = request.json['filters']
        term = filters['searchString'] if filters['searchMode'] == QUERY_SEARCH_MODE else request.json['term']
        source_auto_assigned_concept_ids = request.json['sourceAutoAssignedConceptIds']
        search_result = search_usagi(filters, term, source_auto_assigned_concept_ids)
    except InvalidUsage as error:
        raise error
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return json.dumps(search_result, indent=4, cls=ScoredConceptEncoder)


@usagi.route('/api/save_mapped_codes', methods=['POST'])
@token_required
def save_mapped_codes_call(current_user):
    app.logger.info("REST request to save mapped codes")
    try:
        codes = request.json['codes']
        mapped_codes = request.json['codeMappings']
        vocabulary_name = request.json['name']
        mapping_params = request.json['mappingParams']
        filters = request.json['filters']
        result = save_codes(current_user, codes, mapping_params, mapped_codes, filters, vocabulary_name)
    except DataError as error:
        raise InvalidUsage(error.__str__(), 400)
    except InvalidUsage as error:
        raise error
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return json.dumps(result)


@usagi.route('/api/get_vocabulary_list', methods=['GET'])
@token_required
def get_vocabulary_list_call(current_user):
    app.logger.info("REST request to GET vocabulary list")
    try:
        result = get_vocabulary_list_for_user(current_user)
    except InvalidUsage as error:
        raise error
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return jsonify(result)


@usagi.route('/api/get_vocabulary', methods=['GET'])
@token_required
def load_mapped_concepts_call(current_user):
    app.logger.info("REST request to GET vocabulary")
    try:
        vocabulary_name = request.args['name']
        load_mapped_concepts_by_vocabulary_name(vocabulary_name, current_user)
    except InvalidUsage as error:
        raise error
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return jsonify('OK')


@usagi.route('/api/delete_vocabulary', methods=['GET'])
@token_required
def delete_vocabulary_call(current_user):
    app.logger.info("REST request to DELETE vocabulary")
    try:
        vocabulary_name = request.args['name']
        delete_vocabulary(vocabulary_name, current_user)
    except InvalidUsage as error:
        raise error
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return jsonify('OK')


@usagi.route('/api/get_vocabulary_data', methods=['GET'])
@token_required
def get_vocabulary_data_call(current_user):
    app.logger.info("REST request to GET vocabulary data")
    try:
        result = get_vocabulary_data(current_user)
    except InvalidUsage as error:
        raise error
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return jsonify(result)


@usagi.route('/api/get_filters', methods=['GET'])
@token_required
def get_filters_call(current_user):
    app.logger.info("REST request to GET filters")
    try:
        result = get_filters(current_user)
    except InvalidUsage as error:
        raise error
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return jsonify(result)


@usagi.route('/api/cancel_concept_mapping_task', methods=['GET'])
@token_required
def cancel_concept_mapping_task_call(current_user):
    app.logger.info("REST request to GET filters")
    try:
        cancel_concept_mapping_task(current_user)
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return jsonify('OK')


@usagi.route('/api/cancel_load_vocabulary_task', methods=['GET'])
@token_required
def cancel_load_vocabulary_task_call(current_user):
    app.logger.info("REST request to cancel mapping codes process")
    try:
        cancel_load_vocabulary_task(current_user)
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return jsonify('OK')


@usagi.route('/api/solr_import_status', methods=['GET'])
def solr_import_status_call():
    app.logger.info("REST request to GET Solr import status")
    try:
        response = run_solr_command(USAGI_IMPORT_STATUS)
    except InvalidUsage as error:
        raise error
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return response


@usagi.route('/api/start_solr', methods=['GET'])
def start_solr_call():
    app.logger.info("REST request to start Solr import process")
    try:
        p = subprocess.Popen([f"solr", "start"], stdout =subprocess.PIPE, stderr =subprocess.PIPE, shell=True)
        output, error = p.communicate()
        if p.returncode != 0:
            print("failed %d %s %s" % (p.returncode, output, error))
    except InvalidUsage as error:
        raise error
    except Exception as error:
        raise InvalidUsage(error.__str__(), 500)
    return jsonify(output)


app.register_blueprint(usagi)

if __name__ == '__main__':
    socket.run(app, port=PORT, host='0.0.0.0')