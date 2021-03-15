import pymel.core as pm
import maya.cmds as cmds
import shutil
import os

meshes = []
nrOfMeshes = 0
VertexIndicesAdder = 0
UVIndicesAdder = 0
NormalIndicesAdder = 0
shader = ""
winTitle = ""

def Browse():
    path = cmds.fileDialog2(dir=os.getcwd(), fileFilter="*.obj", dialogStyle=2)[0]
    cmds.textField("textField", edit=True, tx=path)
    
def getValues():
    chosenPath = cmds.textField("textField", query=True, text=True)
    triangulateCheck = cmds.checkBox("triangulate", query=True, value=True)
    exportSelectionCheck = cmds.checkBox("exportSelection", query=True, value=True)
    exportMaterialCheck = cmds.checkBox("exportMaterial", query=True, value=True)
    spaceCheck = cmds.radioCollection("space", query=True, sl=True)
    
    directoryPath = (os.path.dirname(chosenPath) + '\\')
    filename = os.path.basename(chosenPath)
    
    if (chosenPath == filename):
        directoryPath = os.getcwd() + '\\'
    
    Export(filename, directoryPath, triangulateCheck, exportSelectionCheck, exportMaterialCheck, spaceCheck)

def buildUI():
    global winTitle
    winTitle = "ExportSettings"
    winWidth = 250
    
    if cmds.window(winTitle, exists=True):
        cmds.deleteUI(winTitle)
    
    cmds.window(winTitle, width=winWidth, title=winTitle)
    
    mainCL = cmds.columnLayout()
    
    tmpRowWidth = [winWidth / 4, winWidth / 2, winWidth / 4]
    cmds.rowLayout(numberOfColumns=3, columnWidth3=tmpRowWidth, height=50)
    cmds.text(label="Filename", width=tmpRowWidth[0])
    cmds.textField("textField", tx="", width=tmpRowWidth[1]-10)
    cmds.button(label="Browse", c="Browse()", width=tmpRowWidth[2]-15)
    cmds.setParent("..")
    
    cmds.rowLayout(numberOfColumns=1, columnWidth1=winWidth, height=30, ct1="left", co1=8)
    cmds.checkBox("triangulate", label="Triangulate")
    cmds.setParent("..")
    
    cmds.rowLayout(numberOfColumns=1, columnWidth1=winWidth, height=30, ct1="left", co1=8)
    cmds.checkBox("exportSelection", label="Export Selection")
    cmds.setParent("..")
    
    cmds.rowLayout(numberOfColumns=1, columnWidth1=winWidth, height=30, ct1="left", co1=8)
    cmds.checkBox("exportMaterial", label="Export Material")
    cmds.setParent("..")
    
    tmpRowWidth = [winWidth / 4, (1.5 * winWidth) / 4,(1.5 * winWidth) / 4]
    cmds.rowLayout(numberOfColumns=3, columnWidth3=tmpRowWidth, height=30, ct3= ("left", "left", "left"), co3=[ 9, 5, 5])
    cmds.text(label="Space:")
    cmds.radioCollection("space")
    cmds.radioButton("world", l="World")
    cmds.radioButton("object", l="Object", sl=True)
    cmds.setParent("..")
    
    cmds.rowLayout(numberOfColumns=1, columnWidth1=winWidth, height=50, cat=(1, "both", winWidth / 2 - 30))
    cmds.button(label="Export", c="getValues()")
    
    cmds.showWindow(winTitle)
    cmds.window(winTitle, e=True, width=winWidth, height=1)

def Material(mesh, path, materialFile):
    global shader

    shader = mesh.listConnections(type=pm.nodetypes.ShadingEngine)[0]
    shader.listConnections()[0]
    material = shader.listConnections(type=pm.nodetypes.Lambert)[0]
    
    #1. Ta reda på texture-path
    texturePath = material.listConnections(type="file")[0].getAttr("fileTextureName")
    #2. Gör en lista med alla element (allt emellan respektive '/')
    file = list(texturePath.split('/'))
    #3. Ta ut det sista elementet (Texturfilen)
    file = file[len(file) - 1]
    
    #Kopiera texturfilen till nya mappen
    shutil.copyfile(texturePath, path + str(file))
    
    diffuse = material.getAttr("diffuse")
    ambient = material.getAmbientColor()
    refIndex = material.getRefractiveIndex()
    specular = material.getAttr("specularColor")
    
    materialFile.write("newmtl " + str(shader))
    materialFile.write("\nillum 4")
    materialFile.write("\nKd " + str(diffuse) + " " + str(diffuse) + " " + str(diffuse))
    materialFile.write("\nKa " + str(ambient[0]) + " " + str(ambient[1]) + " " + str(ambient[2]))
    materialFile.write("\nTf 1.0 1.0 1.0")
    materialFile.write("\nmap_Kd " + file)
    materialFile.write("\nNi " + str(refIndex))
    materialFile.write("\nKs " + str(specular[0]) + " " + str(specular[1]) + " " + str(specular[2]))

def VertexPoses(mesh, space, file):
	pts = mesh.getPoints(space=space)
	for pt in pts:
		file.write("v " + str(pt[0]) + " " + str(pt[1]) + " " + str(pt[2]) + "\n")
	
def UVPoses(mesh, file):
	uvs = mesh.getUVs()
	for i in range(len(uvs[0])):
		file.write("vt " + str(uvs[0][i]) + " " + str(uvs[1][i]) + "\n") 

def Normals(mesh, file):
    normals = mesh.getNormals()
    for normal in normals:
        file.write("vn")
        for n in normal:
            file.write(" " + str(n))
        file.write("\n")

def Faces(mesh, file, VertexIndicesAdder, UVIndicesAdder, NormalIndicesAdder):
	vPerFace = mesh.getVertices()[0]
	vIndices = mesh.getVertices()[1]
	nIndices = mesh.getNormalIds()[1]
	uvIndices = mesh.getAssignedUVs()[1]
	
	counter = 0
	
	for x in range(len(vPerFace)):
		file.write("f")
		for y in range(vPerFace[x]):
			file.write(" " + str(vIndices[counter] + VertexIndicesAdder + 1) + "/" + str(uvIndices[counter] + UVIndicesAdder + 1) + "/" + str(nIndices[counter] + NormalIndicesAdder + 1))
			counter += 1
		file.write("\n")

def Export(filename, path, triangulate, exportSelection, exportMaterial, space):
    global winTitle
    nrOfMeshes = 0
    VertexIndicesAdder = 0
    UVIndicesAdder = 0
    NormalIndicesAdder = 0
    successful = True
    
    if (len(filename) == 0):
        raise RuntimeError("Please select a valid path");
        successful = False;
    
    if (successful):
        if (exportSelection):
            if (triangulate):
                pm.polyTriangulate()
                
            for mesh in pm.ls(sl=True)[0].listRelatives(c=True):
                if not("polySurfaceShape" in str(mesh)):
                    meshes.append(mesh)
                    nrOfMeshes += 1
    
        else:
            if (triangulate):
                pm.select(all=True)
                pm.polyTriangulate()
        
            for mesh in pm.ls(type=pm.nodetypes.Mesh):
                if not("polySurfaceShape" in str(mesh)):
                    meshes.append(mesh)
                    nrOfMeshes += 1
        
        if (nrOfMeshes == 0):
            print "No Objects Found"
    
        if (nrOfMeshes > 0):
            name, extension = os.path.splitext(filename)
           
            print space
            file = open(path + name + ".obj", "w")
            
            if (exportMaterial):
                materialFile = open(path + name + ".mtl", "w")
            
            for mesh in meshes:
                if (exportMaterial):
                    Material(mesh, path, materialFile)
                    file.write("mtllib " + name + ".mtl\n")
                    
                file.write("g default\n")
                VertexPoses(mesh, space, file)
                UVPoses(mesh, file)
                Normals(mesh, file)
                file.write("g " + mesh.firstParent() + "\n")
                
                if (exportMaterial):
                    file.write("usemtl " + shader + "\n")
                    
                Faces(mesh, file, VertexIndicesAdder, UVIndicesAdder, NormalIndicesAdder)
                VertexIndicesAdder += len(mesh.getPoints())
                UVIndicesAdder += len(mesh.getUVs()[0])
                NormalIndicesAdder += len(mesh.getNormals())
            
            file.close()
            
        if (exportMaterial):
            materialFile.close()
            
        if (triangulate):
            pm.undo()
            
        cmds.deleteUI(winTitle, wnd=True)

def main():
    buildUI()
main()