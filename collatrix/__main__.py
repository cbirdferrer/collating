#---------------------------------------------------------------
#__main__.py
#this script collates measurements from individual csv outputs of
#the morphometriX GUI
#the csvs can be saved either all in one folder or within each individual
#animals folder.
#this version includes a safety net that recalculates the measurement using
#accurate altitude and focal lengths that the user must provie in csvs.
# this version uses PyQt5 instead of easygui (used in v2.0)
#created by: Clara Bird (clara.birdferrer#gmail.com), March 2020
#----------------------------------------------------------------

#import modules
import pandas as pd
import numpy as np
import os, sys
import math
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog, QMessageBox, QLabel, QVBoxLayout
from PyQt5.QtGui import QIcon

#define functions
##duplicate check function
def anydup(l): #we'll use this function later to check for duplicates
    seen = set()
    for x in l:
        if x in seen: return True
        seen.add(x)
    return False
## function that reads in csv as one column, then splits
def readfile(f):
    temp=pd.read_csv(f,sep='^',header=None,prefix='X',engine = 'python') #read in csv as one column
    df00=temp.X0.str.split(',',expand=True) #split rows into columns by delimeter
    df00 = df00.replace("",np.nan)
    df0 = df00.dropna(how='all',axis = 'rows').reset_index(drop=True)
    df0 = df0.fillna('') #replace nans by blank space
    return df0
## function that resets header
def fheader(df):
    head = df.iloc[0] #make list out of names in first row
    df = df[1:] #take the data less the header row
    df.columns = head #set the header row as the df header
    return(df)
##this is the function that does the collating
#set up list of constants
constants = ['Image ID', 'Image Path', 'Focal Length', 'Altitude', 'Pixel Dimension']
def collate(csvs,measurements,nonPercMeas,df_L,safety,anFold):
    for f in csvs:
        print(f)
        df0 = readfile(f)
        idx = df0.loc[df0[0] == 'Object'].index #find index (row) values of 'Object'
        df = df0.truncate(before=idx[0]) #take subset of df starting at first row containing Object
        df = fheader(df)

        #make list of Length measurements
        l = df['Object'].tolist() #make list of Object columns aka. names of measurements made
        l = [x for x in l if pd.isna(x) == False] #eliminate all empty cells
        l = [x for x in l if x not in constants and x != 'Object'] #elimate all other instances of Object
        l = [x for x in l if x] #make sure no blank elements in list

        measurements = measurements + l #add the measurement names to the master list
        nonPercMeas = nonPercMeas + l #copy of the master list that does not include widths

        #make list of Width measurements
        iwx = df.loc[df['Widths (%)'].str.contains("Width")].index.tolist()

        for ix,iw in enumerate(iwx):
            if ix +1 < len(iwx):
                iw1 = iwx[ix+1]-1
            else:
                iw1 = len(df0)
            dfw = df.truncate(before=iw,after=iw1)
            head = dfw.iloc[0] #make list out of names in first row
            dfw = dfw[1:] #take the data less the header row
            dfw.columns = head #set the header row as the df header

            dfw = dfw.set_index(dfw.iloc[:,0]) #set Object column as the index
            dfw = dfw.replace(r'^\s*$', np.nan, regex=True) #replace blank space with nan

            widths = dfw.columns.tolist()
            widths = [x for x in widths if x != ""]

            if anydup(l) == True: #check for any duplicate measurement names, if exists, exit code, print error msg
                print("please check file {0} for duplicate Objects and remove duplicates".format(f))
                sys.exit("remove duplicate and run script again")
            elif anydup(l) == False:
                for i in l: #loop through list of measurement types
                    if i in dfw.index:
                        for w in (w for w in widths if w[0].isdigit()): #loop through the widths
                            x = dfw.loc[i,w] #extract cell value of width of measurement type
                            if pd.isna(x) == False: #if the cell isn't empty
                                ww = i + "-" + w #combine the names
                                measurements += [ww] #add this combined name to the master list

    #now we're going to set up a dictionary to fill in with all the measurements
    #that we will eventually turn into a dataframe where the keys are the columns
    rawM = measurements
    measurements += ['Image','Animal_ID','Altitude','Focal Length','PixD','Notes']
    names = ['Image','Animal_ID','Altitude','Focal Length','PixD','Notes']
    mDict = dict.fromkeys(measurements)
    keys = list(mDict.keys())

    df_all = pd.DataFrame(columns = keys) #make an empty dataframe with the headers being the measurement types/info to pull

    rawMM = set(rawM) #get unique list of measurements

    for f in csvs:
        df0 = readfile(f)
        idx = df0.loc[df0[0]=='Object'].index #set object column to index
        df = df0.truncate(after=idx[0]) #subset df to be only top info section

        if anFold == 'yes':
            aID = os.path.split(os.path.split(f)[0])[1] #extract animal ID
        elif anFold == 'no':
            aID = df[df[0] == 'Image ID'].loc[:,[1]].values[0] #pull animal id
            aID = aID[0]
        mDict['Animal_ID'] = aID

        image = os.path.split(df[df[0] == 'Image Path'].loc[:,1].values[0])[1] #extract image
        print(image)
        mDict['Image'] = image

        alt = float((df[df[0] == 'Altitude'].loc[:,[1]].values[0])[0]) #extract entered altitude
        mDict['Altitude'] = alt

        focl = float((df[df[0] == 'Focal Length'].loc[:,[1]].values[0])[0]) #extract entered focal length
        mDict['Focal Length'] = focl

        pixd = float((df[df[0] == 'Pixel Dimension'].loc[:,[1]].values[0])[0]) #extract entered pixel dimension
        mDict['PixD'] = pixd

        notes = df[df[0] == 'Notes'].loc[:,[1]].values[0] #extract entered notes
        mDict['Notes'] = notes[0]

        if safety == 'yes': #pull the altitude, focal length, and pix d from the safety csv by image name
            alt_act = float(df_L[df_L.Image == image].loc[:,'Altitude'].values[0]) #this says: find row where image = image and pull altitude
            foc_act = float(df_L[df_L.Image == image].loc[:,'Focal_Length'].values[0])
            pixd_act = float(df_L[df_L.Image == image].loc[:,'Pixel_Dimension'].values[0])
        else:
            pass

        dfg = df0.truncate(before=idx[0]) #look at part of dataframe that contains measurment data
        dfg = fheader(dfg) #reset the header
        iwx = dfg.loc[dfg['Widths (%)'].str.contains("Width")].index.tolist() #find all rows containing the names of the widths measured
        if len(iwx) == 0: iwx = [0] #if no widths were measured, make index list just 0
        else: iwx = iwx
        dfgg = dfg.set_index(dfg.iloc[:,0]) #make the index the Object column

        for ix,iw in enumerate(iwx): #loop through and make a dataframe for each section of measured widths
            if ix +1 < len(iwx): #if there's an index following the current one
                iw1 = iwx[ix+1]-1 #make the bottom cutoff the next row
            else: #if there is no next width rows
                iw1 = len(df0) #make the bottom cutoff the bottom of the dataframe
            dfw = dfg.truncate(before=iw,after=iw1) #truncate the dataframe to contain just a set of wdiths
            dfGUI = dfw.set_index(dfw.iloc[:,0]) #set Object column as the index
            dfGUI = dfGUI.replace(r'^\s*$', np.nan, regex=True) #replace blank space with nan

            for key in keys: #loop through the keys aka future column headers
                #for the non-width measurements, use full dataframe
                if key in nonPercMeas: #if that key is in the list of measurement types (not widths)
                    if key in dfgg.index: #if the key is in the index of the full dataframe
                        x = float(dfgg.loc[key,'Length (m)']) #extract the measurement value using location
                        if safety == 'yes': # now is the time to do the back calculations
                            pixc = (x/pixd)*(focl/alt) #back calculate the pixel count
                            xx = ((alt_act/foc_act)*pixd_act)*pixc #recalculate using the accurate focal length and altitude
                        elif safety == 'no':
                            xx = x
                    elif key not in dfgg.index: #if this key is not in the csv
                        xx = np.nan
                    mDict[key] = xx #add the value to the respective key
                #for the width measurements, use the truncated dataframes
                elif "%" in key:
                    if key.split("-")[0] in dfGUI.index: #if the key is a width
                        head = dfGUI.iloc[0] #make list out of names in first row
                        dfG = dfGUI[1:] #take the data less the header row
                        dfG.columns = head #set the header row as the df header
                        row = key.split("-")[0] #split the name of the measurement
                        col = key.split("-")[1] #to get the row and column indices
                        y = float(dfG.loc[row,col]) #to extract the measurement value
                        if safety == 'yes': #back calculate and recalculate
                            pixc = (y/pixd)*(focl/alt) #back calculate the pixel count
                            yy = ((alt_act/foc_act)*pixd_act)*pixc #recalculate using the accurate focal length and altitude
                        elif safety == 'no':
                            yy = y
                    elif key.split("-")[0] not in dfGUI.index:
                        yy = np.nan
                    mDict[key] = yy

        df_op = pd.DataFrame(data = mDict,index=[1]) #make dictionary (now filled with the measurements from this one csv) into dataframe
        #display(df_op)
        df_all = pd.concat([df_all,df_op],sort = True) # add this dataframe to the empty one with all the measurements as headers

    df_allx = df_all.drop(columns = ['Altitude','Focal Length','PixD']).replace(np.nan,0) #drop non-measurement cols
    return df_allx

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'close box to end script'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.show()

        #add message box with link to github documentation
        msgBox = QMessageBox()
        msgBox.setWindowTitle("For detailed input info click link below")
        msgBox.setTextFormat(QtCore.Qt.RichText)
        msgBox.setText('<a href = "https://github.com/cbirdferrer/collatrix#inputs">CLICK HERE</a> for detailed input instructions, \n then click on OK button to continue')
        x = msgBox.exec_()

        #do you want the Animal ID to be assigned based on the name of the folder
        items = ('yes', 'no')
        anFold, okPressed = QInputDialog.getItem(self,"Input #1", "Do you want the Animal ID to be assigned based on the name of the folder? \n yes or no",items,0,False)
        if okPressed and anFold:
            print("{0} Animal ID in folder name".format(anFold))

        #ask if they want safey net
        items = ('yes', 'no')
        safety, okPressed = QInputDialog.getItem(self,"Input #2", "Do you want to use the safety? \n Yes or No?",items,0,False)
        if okPressed and safety:
            print("{0} safety".format(safety))
        #if safety yes, ask for file
        if safety == 'yes':
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            safe_csv, _ = QFileDialog.getOpenFileName(self,"2.1 Safety File: Image list with altitudes and other information.", "","All Files (*);;csv files (*.csv)", options=options)
            print("safety csv = {0}".format(safe_csv))
        elif safety == 'no':
            pass

        #animal id list?
        items = ('no','yes')
        idchoice, okPressed = QInputDialog.getItem(self, "Input #3", "Do you want output to only contain certain individuals? \n Yes or No?",items,0,False)
        if idchoice and okPressed:
            print("{0} subset list".format(idchoice))
        if idchoice == 'yes':
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            idsCSV, _ = QFileDialog.getOpenFileName(self,"3.1 File containing ID list", "","All Files (*);;csv files (*.csv)", options=options)
            if idsCSV:
                print("ID list file = {0}".format(idsCSV))
        elif idchoice == 'no':
            pass

        #ask for name of output
        outname, okPressed = QInputDialog.getText(self, "Input #4", "Prefix for output file",QLineEdit.Normal,"")

        #import safety csv if safety selected
        if safety == 'yes':
            dfList = pd.read_csv(safe_csv, sep = ",")
            dfList = dfList.dropna(how="all",axis='rows').reset_index()
            df_L = dfList.groupby('Image').first().reset_index()
            df_L['Image'] = [x.strip() for x in df_L['Image']]
        elif safety == 'no':
            df_L = "no safety"

        #get folders
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        GUIfold = QFileDialog.getExistingDirectory(None, "Input 5. Folder containing MorphoMetriX outputs",options=options)
        saveFold = QFileDialog.getExistingDirectory(None,"Input 6. Folder where output should be saved",options = options)
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog


        #make lists
        #for csvs
        csvs_all = []
        csvs = []
        not_mmx = []
        #for measurements
        measurements = []
        nonPercMeas = []

        #walk through all folders in GUI folder and collect all csvs
        for root,dirs,files in os.walk(GUIfold):
            csvs_all += [os.path.join(root,f) for f in files if f.endswith('.csv')]
        #make sure the csvs are morphometrix outputs by checking first row
        csvs += [c for c in csvs_all if 'Image ID' in pd.read_csv(c,nrows=1,header=None)[0].tolist()]
        #make list of all csvs that were not morphometrix csvs to tell user
        not_mmx += [x for x in csvs if x not in csvs_all]
        print("these csvs were not morphometrix outputs: {0}".format(not_mmx))

        #run the collate function, get collated csv
        df_allx = collate(csvs,measurements,nonPercMeas,df_L,safety,anFold) #run collating function

        #now we group by ID and image just incase multiple images were measured for the same animal
        #this would combine those measurements (it's why I replaced nans with 0)
        df_all_cols = df_allx.columns.tolist() #make list of column names
        gby = ['Animal_ID','Image','Notes'] #list of non-numeric columns
        togroup = [x for x in df_all_cols if x not in gby] #setting up list of columns to be grouped

        df_all = df_allx.groupby(['Animal_ID','Image'])[togroup].apply(lambda x: x.astype(float).sum()).reset_index()
        df_notes = df_allx.groupby(['Animal_ID','Image'])['Notes'].first().reset_index()
        df_all =df_all.merge(df_notes,on=['Animal_ID','Image'])

        #sort cols
        cols = list(df_all)
        a = "AaIiTtEeJjRrBbFfWwCcDdGgHhKkLlMmNnOoPpQqSsUuVvXxYyZz" #make your own ordered alphabet
        col = sorted(cols, key=lambda word:[a.index(c) for c in word[0]]) #sort headers based on this alphabet
        df_all1 = df_all.loc[:,col] #sort columns based on sorted list of column header
        df_all1 = df_all1.replace(0,np.nan) #replace the 0s with nans

        outcsv = os.path.join(saveFold,"{0}_allIDs.csv".format(outname))
        df_all1.to_csv(outcsv,sep = ',',index_label = 'IX')

        if idchoice == 'yes':
            df_ids = pd.read_csv(idsCSV,sep = ',') #read in id csv
            idList = df_ids['Animal_ID'].tolist() #make list of IDs
            df_allID = df_all1[df_all1['Animal_ID'].isin(idList)] #subset full dataframe to just those IDs

            outidcsv = os.path.join(saveFold,"{0}_IDS.csv".format(outname))
            df_allID.to_csv(outidcsv,sep = ',',index_label = 'IX')
        elif idchoice == 'no':
            pass
        print(df_all1)
        print("done, close GUI window to end script")
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
