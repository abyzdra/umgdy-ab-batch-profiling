#-------------------------------------------------------------------------------
# Name:        umgdy-ab-batch-profiling, part 2: 2-txtToPlots
# Author:      Alicja Byzdra
# Created:     13-02-2017
# Copyright:   (c) Alicja Byzdra 2017
# Institution:     UMGDY, University of Gdansk
#-------------------------------------------------------------------------------

#-*- coding: utf-8 -*-


import arcpy
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.path import Path
import matplotlib.patches as patches
from datetime import datetime
import os

################## PARAMETERS ####################################################################
dir = arcpy.GetParameterAsText(0)
Name_PDF = arcpy.GetParameterAsText(1)

Output_folder = arcpy.GetParameterAsText(2)
if Output_folder is None:
    Output_folder = dir

try:
    userMinX=int(arcpy.GetParameterAsText(3))
except:
    userMinX="#"

try:
    userMaxX=int(arcpy.GetParameterAsText(4))
except:
    userMaxX="#"

try:
    userMinY=int(arcpy.GetParameterAsText(5))
except:
    userMinY="#"

try:
    userMaxY=int(arcpy.GetParameterAsText(6))
except:
    userMaxY="#"

pdfTitle=arcpy.GetParameterAsText(7)

userColormap=arcpy.GetParameterAsText(8)

lineWidth=1.5
patchColor="#C2DFFF"        #blue patch
userXLabel="miara biezaca [m]"
userYLabel="h [m]"

#COLORMAPS NAMES ARE DESCRIBED ON THE FOLLOWING WEBSITE:
#https://matplotlib.org/examples/color/colormaps_reference.html


################## CURRENT DATE ##################################################################
currentDate = str(datetime.now())
currentDate = currentDate[:10]


################## CREATE MULTIPAGE PDF ##########################################################
pdf = PdfPages(Output_folder + "\\" + Name_PDF + ".pdf")


################## COLLECT PTXT FILES PATHS ######################################################
dirs = [x[0] for x in os.walk(dir)]
filesPtxt = [x[2] for x in os.walk(dir)]
filesPaths = []
for d in range(len(dirs)):
    if filesPtxt[d]:
        for fil in filesPtxt[d]:
            filesPaths.append(dirs[d] + "\\" + fil)


################## COLLECT LINE_IDs, ALLHEIGHTS, ALLDISTANCES ####################################
allHeights=[]
allDistances=[]
allLineIds=[]

for f in filesPaths:
    with open(f) as txtFile:
        for line in txtFile:
            if line[0]=="#":
                line=line.split(":")
                if line[0]=="#Line_id":
                    line=line[1]
                    if line[0]==" ":
                        line=line[1:-1]
                    allLineIds.append(line)
            else:
                line=line.split()
                allHeights.append(float(line[1]))
                allDistances.append(float(line[2]))
    txtFile.close()
allLineIds=sorted(list(set(allLineIds)))


################## COLLECT LINE_IDs, ALLHEIGHTS, ALLDISTANCES ####################################
for ID in allLineIds:
    fig=plt.figure(figsize=(15,10))
    fig.suptitle(pdfTitle, fontsize=14, verticalalignment="top", fontweight='bold')

    plt.figtext(0.855, 0.04, 'Data wydruku: '+currentDate, fontsize=10, color="grey")
    plt.figtext(0.610, 0.025, u'Wydruk z programu umgdy-ab-batch-profiling, bedacego praca dyplomowa Alicji Byzdra', fontsize=9, color="grey")
    plt.figtext(0.558, 0.01, u'Studia podyplomowe "GIS - System Informacji Geograficznej" (edycja 2016/17), Uniwersytet Gdanski', fontsize=9, color="grey")

    plt.title(ID)
    ax = fig.add_subplot(111)
    cmap = matplotlib.cm.get_cmap(userColormap)

    heightsPlot=[]
    distancesPlot=[]
    datesPlot=[]

    for f in filesPaths:
        with open(f) as txtFile:
            distHeight={}
            for line in txtFile:
                if line[0]=="#":
                    line=line.split(":")
                    if line[0]=="#Date":
                        line=line[1]
                        if line[0]==" ":
                            lDate=line[1:-1]
                        else:
                            lDate=line[:-1]
                    if line[0]=="#Line_id":
                        line=line[1]
                        if line[0]==" ":
                            lID=line[1:-1]
                        else:
                            lID=line[:-1]
                else:
                    if lID==ID:
                        line=line.split()
                        distHeight[float(line[2])]=float(line[1])
        txtFile.close()
        if lID==ID:
            distances=sorted(distHeight.keys())
            heights=[distHeight[d] for d in distances]
            heightsPlot.append(heights)
            distancesPlot.append(distances)
            datesPlot.append(lDate)
    num=len(datesPlot)
    for nr in range(num):
        heights=heightsPlot[nr]
        distances=distancesPlot[nr]
        date=datesPlot[nr]

        if num==1:
            c = cmap(float(nr)/(num))
        else:
            c = cmap(float(nr)/(num-1))
        line, = plt.plot(distances,heights,label=date,linewidth=lineWidth,color=c)
        line.set_label(date)

        belowZeroHeights=[]
        belowZeroDist = []
        for h in range(len(heights)):
            if heights[h]<=0:
                belowZeroHeights.append(heights[h])
                belowZeroDist.append(distances[h])
        if belowZeroHeights:
            verts=[]
            codes=[Path.MOVETO]
            verts.append((belowZeroDist[0],0))
            codes.append(Path.LINETO)
            for v in range(len(belowZeroHeights)):
                verts.append((belowZeroDist[v],belowZeroHeights[v]))
                codes.append(Path.LINETO)
            if userMaxX!="#" and userMinX!="#" and userMaxY!="#" and userMinY!="#":
                verts.append((userMaxX+3,belowZeroHeights[-1]))
                codes.append(Path.LINETO)
                verts.append((userMaxX+3,0))
                verts.append((belowZeroDist[0],0))
                codes.append(Path.CLOSEPOLY)
                path = Path(verts, codes)
            else:
                maxDist=int(max(allDistances))+2
                verts.append((maxDist+3,belowZeroHeights[-1]))
                codes.append(Path.LINETO)
                verts.append((maxDist+3,0))
                verts.append((belowZeroDist[0],0))
                codes.append(Path.CLOSEPOLY)
                path = Path(verts, codes)
            patch = patches.PathPatch(path, facecolor=patchColor, lw=0)
            ax.add_patch(patch)

    plt.legend(loc=1, frameon=True, fontsize=11)
    if userMaxX!="#" and userMinX!="#" and userMaxY!="#" and userMinY!="#":
        maxDist = userMaxX
        minDist = userMinX
        maxHeight = userMaxY
        minHeight = userMinY

        ############### AUTOMATIC STEP - GRID #######################################
        okY=0
        divY=20.0
        while okY!=1:
            if (int(maxHeight)-int(minHeight))%divY==0:
                okY=1
            else:
                divY+=1
        stepY=int((int(maxHeight)-int(minHeight))/divY)


        okX=0
        divX=25.0
        while okX!=1:
            if (int(maxDist)-int(minDist))%divX==0:
                okX=1
            else:
                divX+=1
        stepX=int((int(maxDist)-int(minDist))/divX)

        plt.xlim(minDist, maxDist)
        plt.ylim(minHeight, maxHeight)

        plt.xticks(range(minDist,maxDist,stepX))

        plt.yticks(range(minHeight,maxHeight,stepY))
        ax=plt.gca()
        ax.grid(which='major', axis='x', linewidth=0.75, linestyle='-', color='0.75')
        ax.grid(which='minor', axis='x', linewidth=0.25, linestyle='-', color='0.75')
        ax.grid(which='major', axis='y', linewidth=0.75, linestyle='-', color='0.75')
        ax.grid(which='minor', axis='y', linewidth=0.25, linestyle='-', color='0.75')
        plt.axhline(0, color='0.4', linewidth=1, zorder=20)
        plt.axvline(0, color='0.4', linewidth=1, zorder=20)
        plt.xlabel(userXLabel) #"miara biezaca [m]"
        plt.ylabel(userYLabel) #"h [m]"
        plt.tight_layout()
        plt.subplots_adjust(top=0.93, bottom=0.096)


    else:
        maxDist=int(max(allDistances))
        minDist=int(min(allDistances))
        while (maxDist-minDist)%4.0!=0:
            maxDist+=1
        minHeight=int(min(allHeights))
        maxHeight=int(max(allHeights))
        if (maxHeight-minHeight)%2.0==0:
            maxHeight+=1

        ############### AUTOMATIC STEP - GRID #######################################
        okY=0
        divY=10.0
        while okY!=1:
            if (float(int(maxHeight)-int(minHeight)))%divY==0:
                okY=1
            else:
                divY+=1
        stepY=int(float((int(maxHeight)-int(minHeight)))/divY)


        okX=0
        divX=15.0
        while okX!=1:
            if (float(int(maxDist)-int(minDist)))%divX==0:
                okX=1
            else:
                divX+=1
        stepX=int(float((int(maxDist)-int(minDist)))/divX)


        plt.xlim(minDist-1, maxDist+2)
        plt.ylim(minHeight-1, maxHeight+2)
        plt.xticks(range(minDist,maxDist+2,stepX))

        plt.yticks(range(minHeight-1,maxHeight+2,stepY))
        ax=plt.gca()
        ax.grid(which='major', axis='x', linewidth=0.75, linestyle='-', color='0.75')
        ax.grid(which='minor', axis='x', linewidth=0.25, linestyle='-', color='0.75')
        ax.grid(which='major', axis='y', linewidth=0.75, linestyle='-', color='0.75')
        ax.grid(which='minor', axis='y', linewidth=0.25, linestyle='-', color='0.75')
        plt.axhline(0, color='0.4', linewidth=1, zorder=20)
        plt.axvline(0, color='0.4', linewidth=1, zorder=20)
        plt.xlabel(userXLabel)
        plt.ylabel(userYLabel)
        plt.tight_layout()
        plt.subplots_adjust(top=0.93, bottom=0.096)

    pdf.savefig(fig)
pdf.close()
plt.close('all')

