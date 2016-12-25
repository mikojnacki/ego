"""
Python console app:
- searches people in KRS API
- gets JSON data of chosen person
- creates graph of chosen person
- dumps JSON graph data of chosen person
- runs Flask server with graph visualization
"""

import os
import sys
import networkx as nx
from networkx.readwrite import json_graph
import requests
import json
import flask


def search_people():
    """
    GET request from KRS API
    search people with given name nad last name
    return list of dicts of people to choose
    """
    query = input('Proszę podać imię i nazwisko wyszukiwanej osoby: ')

    r = requests.get('https://api-v3.mojepanstwo.pl/dane/krs_osoby.json?conditions[q]='+query)
    j = r.json()

    people = []
    count = 1
    for person in j['Dataobject']:
        people.append({'no':count,'id':person['id'], 'name':person['data']['krs_osoby.imiona']+' '+person['data']['krs_osoby.nazwisko'],
                       'date_of_birth':person['data']['krs_osoby.data_urodzenia']})
        count = count + 1

    print('Wyszukane osoby: ')
    for person in people:
        print(str(person['no']) + '\t' + person['name'] + ' ' + person['date_of_birth'] + '\n')

    return people


def choose_person(people):
    """
    Choose person from a list of found people
    Return krd_osoby.id of chosen person
    """
    chosen_no = int(input('Proszę podać numer wybranej osoby: '))  # add handling ValueError exceptions
    chosen_id = people[chosen_no - 1]['id']

    return chosen_id


def get_person(chosen_id):
    """
    GET request from KRS API
    return json object with person's graph
    """
    r = requests.get('https://api-v3.mojepanstwo.pl/dane/krs_osoby/' + chosen_id + '.json?layers[]=graph')
    person_json = r.json()
    return person_json


def create_graph(person_json):
    """
    Create NetworkX Graph from person's JSON data
    Dumps JSON graph data into ~/webpage/ subfolder
    """
    G = nx.Graph()
    # create nodes
    for node in person_json['layers']['graph']['nodes']:
        # person node
        if 'osoba' in node['id']:
            # ego person node
            if person_json['id'] in node['id']:
                G.add_node(node['id'], name=node['data']['imiona'] + ' ' + node['data']['nazwisko'],
                           group='ego', attributes=node['data'])
            # other person node
            else:
                G.add_node(node['id'], name=node['data']['imiona'] + ' ' + node['data']['nazwisko'],
                           group='osoba', attributes=node['data'])
        # institution node
        elif 'podmiot' in node['id']:
            G.add_node(node['id'], name=node['data']['nazwa'], attributes=node['data'],
                       group='podmiot')

    # create edges
    for edge in person_json['layers']['graph']['relationships']:
        G.add_edge(edge['start'], edge['end'], relation=edge['type'])

    # dump G graph to JSON file
    d = json_graph.node_link_data(G)
    json.dump(d, open(os.getcwd()+'/webpage/ego.json', 'w'))


def run_server():
    """
    Run a Flask locsl server with d3.js graph visualization
    ego.html file in a ~/webpage/ subfolder
    """
    app = flask.Flask(__name__, static_folder=os.getcwd()+'/webpage/')

    @app.route('/<path:path>')
    def static_proxy(path):
        return app.send_static_file(path)

    print('\nGraf ego wybranej osoby:  http://127.0.0.1:8000/ego.html \n')
    app.run(port=8000)


def main():
    """Main function"""

if __name__ == '__main__':
    try:
        people = search_people()
        chosen_id = choose_person(people)
        person_json = get_person(chosen_id)
        create_graph(person_json)
        run_server()

    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
