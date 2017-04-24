from flask import Flask, render_template, redirect, request, jsonify
from squad.demo_prepro import prepro
from basic.demo_cli import Demo
from qapipeline import QAPipeline
import json

app = Flask(__name__)
shared = json.load(open("data/squad/shared_test.json", "r"))
contextss = [""]
context_questions = [""]
for i in range(len(shared['contextss'])):
    j = 1 if i==0 else 0
    contextss.append(shared["contextss"][i][j])
    context_questions.append(shared['context_questions'][i][j])
titles = ["Write own paragraph"]+shared["titles"]

demo = Demo()

def getTitle(ai):
    return titles[ai]

def getPara(rxi):
    return contextss[rxi[0]][rxi[1]]

def fixParagraph(paragraph):
    '''Adds a period to the paragraph in case it doesn't have a punctuation mark, 
    improves performance of model'''
    if len(paragraph) < 1 or paragraph is None:
        return paragraph
    if paragraph[-1] not in ['.', '!', '?', ':', ';', '-']:
        paragraph += u"."

    return paragraph

def getAnswer(paragraph, question):
    #paragraph = fixParagraph(paragraph)
    pq_prepro = prepro(paragraph, question)
    if len(pq_prepro['x'])>1000:
        return "[Error] Sorry, the number of words in paragraph cannot be more than 1000." 
    if len(pq_prepro['q'])>100:
        return "[Error] Sorry, the number of words in question cannot be more than 100."
    return demo.run(pq_prepro)

config = json.load(open('qaconfig.json'))
qap = QAPipeline(config['qclf_path'], config['index_url'], config['bidaf_url'], get_answer=getAnswer)

@app.route('/')
def main():
    return 'BiDAF query is located at path /submit, the fields are "paragraph" and "question"'
    #return render_template('index.html')

@app.route('/select', methods=['GET', 'POST'])
def select():
    #paragraph_id = request.args.get('paragraph_id', type=int)
    #rxi = [paragraph_id, 0]
    #paragraph = getPara(rxi)
    #return jsonify(result=paragraph)
    return jsonify(result={"titles" : titles, "contextss" : contextss, "context_questions" : context_questions})

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    paragraph = request.args.get('paragraph')
    question = request.args.get('question')
    if paragraph is None or question is None:
        req_data = request.get_json() 
        question = req_data['question']
        paragraph = req_data['paragraph']
    
    answer = getAnswer(paragraph, question)
    return jsonify(result=answer)

@app.route('/ask', methods=['GET', 'POST'])
def ask():
    userid = request.args.get('userid')
    question = request.args.get('question')
    if (userid is None and question is None):
        print('Wrong request')
        data = json.loads(request.form['data'])
        print(data)
        userid = data['userid']
        question = data['userid']
        print(userid, question)

    res = qap.answer_user_question(userid, question)
    return jsonify(res)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="1995", threaded=True )
