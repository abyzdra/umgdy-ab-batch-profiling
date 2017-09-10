#-------------------------------------------------------------------------------
# Name:        umgdy-ab-batch-profiling, part 1: 1-rasterToTxt
# Author:      Alicja Byzdra
# Created:     13-02-2017
# Copyright:   (c) Alicja Byzdra 2017
# Institution:     UMGDY, University of Gdansk
#-------------------------------------------------------------------------------

#-*- coding: utf-8 -*-

try:

    import arcpy
    from arcpy import *
    from arcpy.sa import *
    import os
    import numpy as np
    import math

    ################## PARAMETERS ####################################################################
    line_feature = arcpy.GetParameterAsText(0)
    DEM_layer = arcpy.GetParameterAsText(1)
    DEM_date = arcpy.GetParameterAsText(2)
    Output_folder = arcpy.GetParameterAsText(3)


    arcpy.CheckOutExtension("spatial")
    arcpy.env.workspace=r"in_memory"

    ################## READ LINE_FEATURE #############################################################
    Idd=[]
    lengthLines=int(arcpy.GetCount_management(line_feature).getOutput(0))
    linesTab=np.zeros((lengthLines,5)).astype(object)
    linesTab[:,0]=linesTab[:,0].astype(str)
    i=0
    with arcpy.da.SearchCursor(line_feature, ["line_id","SHAPE@"]) as cursor:
        for row in cursor:
            Idd.append(row[0])
            linesTab[i,0]=row[0]                        #line_id
            linesTab[i,1]=round(row[1].firstPoint.X,3)  #firstPoint.X
            linesTab[i,2]=round(row[1].firstPoint.Y,3)  #firstPoint.Y
            linesTab[i,3]=round(row[1].lastPoint.X,3)   #lastPoint.X
            linesTab[i,4]=round(row[1].lastPoint.Y,3)   #lastPoint.Y
            i+=1
    del row
    del cursor


    ################## GET CELLSIZE, SPATIAL REFERENCE ###############################################
    desc = arcpy.Describe(DEM_layer)
    cellSize = desc.children[0].meanCellHeight

    desc2 = arcpy.Describe(line_feature)
    spatialRef = desc2.spatialReference


    ################## DISTANCE FUNCTION #############################################################
    #DISTANCE FUNCTION
    def distance(x1,y1,x2,y2):
        dist=math.sqrt((x1-x2)**2 + (y1-y2)**2)
        return dist


    ################## CREATE POINTS ALONG LINES LAYER ###############################################
    arcpy.CreateFeatureclass_management(r"in_memory","linePoints","POINT",spatial_reference=spatialRef)
    arcpy.AddField_management("linePoints","line_id","TEXT")
    arcpy.AddField_management("linePoints","distance","DOUBLE")
    arcpy.env.workspace = r"in_memory"

    with arcpy.da.InsertCursor("linePoints", ["SHAPE@XY","line_id","distance"]) as cursor:
        i=0
        for j in range(len(linesTab)):
            angle = math.atan2(linesTab[j,4]-linesTab[j,2], linesTab[j,3]-linesTab[j,1])
            d = distance(linesTab[j,3],linesTab[j,4],linesTab[j,1],linesTab[j,2])
            dx = cellSize*math.cos(angle)
            dy = cellSize*math.sin(angle)
            d2=0.0                          #distance along line
            xp=linesTab[j,1]                #x
            yp=linesTab[j,2]                #y
            xy=(xp,yp)
            cursor.insertRow([xy,linesTab[j,0],round(d2,3)])
            i+=1
            while d2 < d:
                xp+=dx
                yp+=dy
                d2+=cellSize
                xy=(xp,yp)
                cursor.insertRow([xy,linesTab[j,0],round(d2,3)])
                i+=1
    del cursor


    ################## EXTRACT HEIGHTS FROM RASTER ###################################################
    arcpy.sa.ExtractValuesToPoints("linePoints",DEM_layer,"linePoints_null")
    arcpy.Select_analysis("linePoints_null", "linePoints_DEM", '"RASTERVALU" IS NOT NULL')


    ################## READ HEIGHTS AND DISTANCES FROM POINT LAYER ###################################
    lengthPoints=int(arcpy.GetCount_management("linePoints_DEM").getOutput(0))
    pointsTab=np.zeros((lengthPoints,5)).astype(object)
    pointsTab[:,0]=pointsTab[:,0].astype(str)
    i=0
    with arcpy.da.SearchCursor("linePoints_DEM", ["line_id","RASTERVALU","distance"]) as cursor:
        for row in cursor:
            pointsTab[i,0]=row[0]           #line_id
            pointsTab[i,1]=round(row[1],3)  #height
            pointsTab[i,2]=row[2]           #distance
            i+=1
    del row
    del cursor


    ################## CREATE FOLDERS WITH LINE_ID NAMES #############################################
    foldersNames = list(set(list(pointsTab[:,0])))

    for fold in foldersNames:
        newpath = Output_folder + "\\" + fold
        if not os.path.exists(newpath):
            os.makedirs(newpath)
            arcpy.AddMessage("New folder created: " + fold)
        ################## CREATE NEW .PTXT FILES ####################################################
        if os.path.isfile(newpath + "\\" + fold + "-" + DEM_date + ".ptxt"):
            j=1
            while os.path.isfile(newpath + "\\" + fold + "-" + DEM_date + "-" + str(j) + ".ptxt"):
                j+=1
            txtFile = open(newpath + "\\" + fold + "-" + DEM_date + "-" + str(j) + ".ptxt", "w")
        else:
            txtFile = open(newpath + "\\" + fold + "-" + DEM_date + ".ptxt", "w")
        ################## HEADER ####################################################################
        txtFile.write("#Date: " + DEM_date + "\n")
        txtFile.write("#Source: DEM\n")
        txtFile.write("#Line_id: " + fold + "\n")
        txtFile.write("#pt_id	height	distance\n")
        ################## PT_IDs, HEIGHTS, DISTANCES ################################################
        i=1
        for pnt in range(len(pointsTab)):
            if pointsTab[pnt,0]==fold:
                txtFile.write(str(i) + "\t" + str(pointsTab[pnt,1]) + "\t" + str(pointsTab[pnt,2]) + "\n")
                i+=1
        txtFile.close()
    del pointsTab


    ################## DELETE LAYERS STORED IN_MEMORY ################################################
    arcpy.Delete_management(in_data="in_memory", data_type="Workspace")
    arcpy.CheckInExtension("spatial")


except:
    arcpy.AddError("Error occurred")
    arcpy.AddMessage(arcpy.GetMessages())