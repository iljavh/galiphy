
import os
from flask import Blueprint, Flask, render_template, send_file, request, url_for, redirect, Response, make_response
from werkzeug import secure_filename
import pandas as pd
import logging
from tool11 import tool11
import re
import yaml



_log = logging.getLogger(__name__)
app = Flask(__name__)

from middleware import ReverseProxied
app.wsgi_app = ReverseProxied(app.wsgi_app)

def openfile(file):
    with open(file, 'r') as readfile:
        for line in readfile:
            line = line.replace('\n','')
            return line


def countgenes():
    """
    This function reads the file that only contains a number, 
    i.e. the number of genes in the latest HPO version. 
    This (int) number is returned.
    """
    directory = openfile('db_directory.txt')
    no_genes_file = directory+'GENES_IN_HPO.txt'
    GENES_IN_HPO = openfile(no_genes_file)
    #GENES_IN_HPO = openfile(numbergenes_file)
    return int(GENES_IN_HPO)

def config_yaml():
    config = yaml.load(open("config.yaml").read())
    return config["HPOdatabase"],config["output_path"]



@app.route('/')
def index():
   return render_template('upload.html', genes_in_HPO=countgenes())

@app.route('/help')
def help():
   return render_template('help.html', genes_in_HPO=countgenes())

@app.route('/reference')
def reference():
   return render_template('reference.html')

@app.route('/contact')
def contact():
   return render_template('contact.html')

@app.route('/uploader', methods = ['GET', 'POST'])
def uploader():
    """
    Input from client is edited so it can be send to tool. 
    """
    if request.method == 'POST':
        # from the upload page, the clients input is called from the text-area of the form. 
        clientinput_unic = request.form['list_genes']
        #print "raw input client:\n", clientinput_unic
        clientinput_unic = re.sub('[^a-zA-Z0-9 \n\r]', '', clientinput_unic) # all symbols are removed from unicode
        clientinput_genelist = clientinput_unic.replace('\r','').split('\n') # a list is created
        clientinput_genelist = [x.encode('UTF8') for x in clientinput_genelist] # removing the Unicode from the list
        # Input send to tool of the latest version. Current = version 1.1
        HPOdatabase, output_path = config_yaml()
        phen_df, genescores_df, numbers, outfile_phen, outfile_genes, outfile_phenpergenes, accepted_df, dropped_df, Q, missing, dupli = tool11(clientinput_genelist, HPOdatabase, output_path)
        print "missing:", missing, len(missing), "dupli:", len(dupli), "dropped:", len(dropped_df), "accepted:", len(accepted_df)
        # information about the variables are also send to the html pages, as the result page has different sections shown dependent on the clients input.
        number_dropped = len(dropped_df)
        number_accepted = len(accepted_df)
        # if dataframes are not empty, an html table is made from them.
        try:
        	accepted = accepted_df.to_html()
        except:
        	accepted = accepted_df
        try:
        	dropped = dropped_df.to_html()
        except:
        	dropped = dropped_df

        return render_template('result.html', genes_in_HPO=countgenes(),output_phen=outfile_phen,output_genes=outfile_genes, output_phenpergenes=outfile_phenpergenes, accepted=accepted, dropped=dropped, Q=Q, missing=missing, dupli=dupli, number_accepted=number_accepted, number_dropped=number_dropped)


@app.route('/download/<filename>')
def download(filename):
    print filename
    # A download function is called from the result page. Downloaded from output folder.
    file = os.path.join(os.getcwd(), 'output', filename)
    return send_file(file, as_attachment=True)


if __name__ == '__main__':
    
    #print HPOdatabase
    #print output_path
    app.run(host='0.0.0.0', port=5001, debug = True)

