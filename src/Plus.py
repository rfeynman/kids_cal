'''
Created on May 28, 2016

@author: wange
'''
from __future__ import print_function

import numpy as np
from docx import Document 
from docx.shared import Pt
from docx.text import parfmt
from random import shuffle

from sys import argv

from reportlab.pdfgen import canvas

point = 1
inch = 72

def plus(mini,limited, Neqns):
    eqn_ele=[]
    for i in range(0,Neqns):
        a=np.random.randint(mini,limited)
        b=np.random.randint(mini,limited)
        #a=np.random.randint(1,10)
        #b=np.random.randint(1,10)
        i+=1
        eqn_ele.append('%d+%d=        '%(a,b))
        #eqn_ele.append('\n')
    #print(eqn_ele)
    return eqn_ele

def minus(mini,limited, Neqns):
    eqn_ele=[]
    for i in range(0,Neqns):
        a=np.random.randint(mini,limited)
        b=np.random.randint(5,a)
        i+=1
        eqn_ele.append('%d-%d=         '%(a,b))
        #eqn_ele.append('\n')
    #print(eqn_ele)
    return eqn_ele

def times(mini,limited, Neqns):
    eqn_ele=[]
    for i in range(0,Neqns):
        a=np.random.randint(mini,limited)
        b=np.random.randint(mini,limited)
        i+=1
        eqn_ele.append('%dx%d=         '%(a,b))
    return eqn_ele
        
def divide(mini,limited, Neqns):
    eqn_ele=[]
    for i in range(0,Neqns):
        
        b=np.random.randint(mini,limited)
        c=np.random.randint(1,mini)
        a=b*c
        i+=1
        eqn_ele.append('%d'%(a)+u"\u00F7"+'%d=         '%(c))
        #eqn_ele.append('\n')
    #print(eqn_ele)
    return eqn_ele


def comb(mini,limited,Nplus,Nminus,Ntimes,Ndivide):
    
    comb=plus(mini,limited*8,Nplus)
    comb.extend(minus(mini,limited*8,Nminus))
    comb.extend(times(mini,limited,Ntimes))
    comb.extend(divide(mini,limited,Ndivide))

    shuffle(comb)
    strcomb='\t'.join(str(x)+' ' for x in comb)
    return strcomb

'''
def genepdf(filename, calc_list):
    title = filename
    pdfbound=10
    c = canvas.Canvas(filename, pagesize=(8.5 * inch, 11 * inch))
    c.setStrokeColorRGB(0,0,0)
    c.setFillColorRGB(0,0,0)
    t=c.beginText()
    t.setFont("Helvetica", 20 * point)
    t.setTextOrigin(inch, 10*inch)
    t.textLine( "Name____________")
    t.textLine( "Time____________")
    c.line(0.5*inch,(pdfbound-1)*inch,5*inch,(pdfbound-1)*inch)
    t.textLine(calc_list)
    c.drawText(t)
    c.showPage()
    c.save() 
    
    
    
'''
def genedoc(days,minical,limitedcal,pluscal,minuscal,timescal,dividecal):
    d=Document()
    
    #font.font.name='Calibri'
    for day in range(1,days):
        calc_list=comb(minical,limitedcal,pluscal,minuscal,timescal,dividecal)
        d.add_heading('The %d day; Using__________mins'%(day))
        d.add_paragraph(calc_list)
        d.add_page_break()
        day+=1
    style=d.styles['Normal']
    style.font.size=Pt(24)    
    d.save('../Practise_mix.docx')



if __name__ == '__main__':
    totalcal=34
    pluscal=8
    minuscal=8
    timescal=10
    dividecal=totalcal-pluscal-minuscal-timescal
    minical=12
    limitedcal=100
    days=13
    #dailycal=comb(minical,limitedcal,pluscal,minuscal,timescal)
    #print(dailycal)
    #genepdf("day1.pdf", dailycal)
    genedoc(days,minical,limitedcal,pluscal,minuscal,timescal,timescal)
