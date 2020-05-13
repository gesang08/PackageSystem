import sys, random
import svgwrite
from svgwrite import cm,mm

"""
bottom-left-fill algorithm for rectangle packing problem
"""

args = sys.argv

# num_blocks = int(args[1])
num_blocks = 10
# rec = []

mu = 5
sigma = 2
# for i in range(num_blocks):
#     bl_size_x = int(random.normalvariate(mu, sigma))
#     if bl_size_x < 0:
#         bl_size_x = -bl_size_x
#     if bl_size_x == 0:
#         bl_size_x = 1
#     bl_size_y = int(random.normalvariate(mu, sigma))
#     if bl_size_y < 0:
#         bl_size_y = -bl_size_y
#     if bl_size_y == 0:
#         bl_size_y = 1
#     rec.append([bl_size_x,bl_size_y])
#
# rec[0] = [7,3]
# rec[1] = [3,2]
# rec[2] = [5,4]
rec = [[40,16],[5,20],[7,6],[24,24],[4,20],[7,6],[7,8],[5,4],[7,4],[4,4]]
# width = int(args[2])
width = 40
temp = 0
xtemp = 0
ytemp = 0
upoint = 0
rpoint = 0
count = 0
# [x_axis,y_axis,x_enable,y_enable]
corner = [[0,0,width,0]]
newcorner = []
ctemp = []
delete = []
umap = []
rmap = []
for i in range(len(rec)):
    newcorner = []
    for j in range(len(corner)):
        if(rec[i][0] <= corner[j][2] and (rec[i][1] <= corner[j][3] or corner[j][3] == 0)):
            upoint = 0
            ctemp = []
            for l in range(len(umap)):
                if(corner[j][1]+rec[i][1] > umap[l][1]):
                    if(upoint == 0):
                        upoint = l+1
                    if(corner[j][0]+rec[i][0] >= umap[l][0]-umap[l][2] and corner[j][0]+rec[i][0] < umap[l][0]):
                        for k in range(len(rmap)):
                            if(corner[j][0]+rec[i][0] < rmap[k][0]):
                                if(rmap[k][1] > umap[l][1] and rmap[k][1] < corner[j][1]+rec[i][1]):
                                    for m in range(k+1,len(rmap)):
                                        if(corner[j][0]+rec[i][0] < rmap[m][0] and rmap[m][1] > rmap[k][1]):
                                            break
                                        if(corner[j][0]+rec[i][0] >= rmap[m][0] or m == len(rmap)-1):
                                            ctemp.append(rmap[k][1])
                                            break
                            else:
                                break
                        ctemp.append(umap[l][1])
                        ctemp = ctemp[::-1]
                        ytemp = 0
                        for k in range(len(umap)):
                            if(umap[l][1] < umap[k][1]):
                                if(corner[j][0]+rec[i][0] >= umap[k][0]-umap[k][2] and corner[j][0]+rec[i][0] < umap[k][0]):
                                    if(ytemp == 0 or ytemp > umap[k][1] - umap[k][3]):
                                        ytemp = umap[k][1] - umap[k][3]
                            else:
                                break
                        for k in range(len(ctemp)):
                            xtemp = width - corner[j][0] - rec[i][0]
                            for m in range(len(rmap)):
                                if(corner[j][0] + rec[i][0] < rmap[m][0]):
                                    if(ctemp[k] >= rmap[m][1] - rmap[m][3] and ctemp[k] < rmap[m][1]):
                                        if(xtemp > rmap[m][0] - rmap[m][2] - corner[j][0] - rec[i][0]):
                                            xtemp = rmap[m][0] - rmap[m][2] - corner[j][0] - rec[i][0]
                                else:
                                    break
                            if(xtemp != 0):
                                if(ytemp == 0):
                                    newcorner.append([corner[j][0]+rec[i][0],ctemp[k],xtemp,ytemp])
                                else:
                                    newcorner.append([corner[j][0]+rec[i][0],ctemp[k],xtemp,ytemp-ctemp[k]])
                        break
            else:
                xtemp = width-corner[j][0]-rec[i][0]
                for k in range(len(rmap)):
                    if(corner[j][0] + rec[i][0] < rmap[k][0]):
                        if(0 == rmap[k][1] - rmap[k][3]):
                            if(xtemp > rmap[k][0] - rmap[k][2] - corner[j][0] - rec[i][0]):
                                xtemp = rmap[k][0] - rmap[k][2] - corner[j][0] - rec[i][0]
                    else:
                        break
                ytemp = 0
                for k in range(len(umap)):
                    if(corner[j][1] + rec[i][1] < umap[k][1]):
                        if(corner[j][0]+rec[i][0] >= umap[k][0]-umap[k][2] and corner[j][0]+rec[i][0] < umap[k][0]):
                            if(ytemp == 0 or ytemp > umap[k][1] - umap[k][3]):
                                ytemp = umap[k][1] - umap[k][3]
                    else:
                        break
                if(xtemp != 0):
                    newcorner.append([corner[j][0]+rec[i][0],0,xtemp,ytemp])
            rpoint = 0
            ctemp = []
            for l in range(len(rmap)):
                if(corner[j][0]+rec[i][0] > rmap[l][0]):
                    if(rpoint == 0):
                        rpoint = l+1
                    if(corner[j][1]+rec[i][1] >= rmap[l][1]-rmap[l][3] and corner[j][1]+rec[i][1] < rmap[l][1]):
                        for k in range(len(umap)):
                            if(corner[j][1]+rec[i][1] < umap[k][1]):
                                if(umap[k][0] > rmap[l][0] and umap[k][0] < corner[j][0]+rec[i][0]):
                                    for m in range(k+1,len(umap)):
                                        if(corner[j][1]+rec[i][1] < umap[m][1] and umap[m][0] > umap[k][0]):
                                            break
                                        if(corner[j][1]+rec[i][1] >= umap[m][1] or m == len(umap)-1):
                                            ctemp.append(umap[k][0])
                                            break
                            else:
                                break
                        ctemp.append(rmap[l][0])
                        ctemp = ctemp[::-1]
                        xtemp = width
                        for k in range(len(rmap)):
                            if(rmap[l][0] < rmap[k][0]):
                                if(corner[j][1]+rec[i][1] >= rmap[k][1] - rmap[k][3] and corner[j][1]+rec[i][1] < rmap[k][1]):
                                    if(xtemp > rmap[k][0] - rmap[k][2]):
                                        xtemp = rmap[k][0] - rmap[k][2]
                            else:
                                break
                        for k in range(len(ctemp)):
                            ytemp = 0
                            for m in range(len(umap)):
                                if(corner[j][1] + rec[i][1] < umap[m][1]):
                                    if(ctemp[k] >= umap[m][0]-umap[m][2] and ctemp[k] < umap[m][0]):
                                        if(ytemp == 0 or ytemp > umap[m][1] - umap[m][3] - corner[j][1] - rec[i][1]):
                                            ytemp = umap[m][1] - umap[m][3] - corner[j][1] - rec[i][1]
                                else:
                                    break
                            if(xtemp - ctemp[k] != 0):
                                newcorner.append([ctemp[k],corner[j][1]+rec[i][1],xtemp-ctemp[k],ytemp])
                        break
            else:
                xtemp = width
                for k in range(len(rmap)):
                    if(0 < rmap[k][0]):
                        if(corner[j][1]+rec[i][1] >= rmap[k][1] - rmap[k][3] and corner[j][1]+rec[i][1] < rmap[k][1]):
                            if(xtemp > rmap[k][0] - rmap[k][2]):
                                xtemp = rmap[k][0] - rmap[k][2]
                    else:
                        break
                ytemp = 0
                for k in range(len(umap)):
                    if(corner[j][1] + rec[i][1] < umap[k][1]):
                        if(0 == umap[k][0]-umap[k][2]):
                            if(ytemp == 0 or ytemp > umap[k][1] - umap[k][3] - corner[j][1] - rec[i][1]):
                                ytemp = umap[k][1] - umap[k][3] - corner[j][1] - rec[i][1]
                    else:
                        break
                if(xtemp != 0):
                    newcorner.append([0,corner[j][1]+rec[i][1],xtemp,ytemp])
            if(upoint == 0):
                umap.append([corner[j][0]+rec[i][0],corner[j][1]+rec[i][1],rec[i][0],rec[i][1]])
            else:
                umap.insert(upoint-1,[corner[j][0]+rec[i][0],corner[j][1]+rec[i][1],rec[i][0],rec[i][1]])
            if(rpoint == 0):
                rmap.append([corner[j][0]+rec[i][0],corner[j][1]+rec[i][1],rec[i][0],rec[i][1]])
            else:
                rmap.insert(rpoint-1,[corner[j][0]+rec[i][0],corner[j][1]+rec[i][1],rec[i][0],rec[i][1]])
            delete = []
            for l in range(len(corner)):
                if(corner[l][0] >= corner[j][0] and corner[l][0] < corner[j][0]+rec[i][0]):
                    if(corner[l][1] >= corner[j][1] and corner[l][1] < corner[j][1]+rec[i][1]):
                        delete.append(l)
                        continue
                if(corner[l][0] < corner[j][0]+rec[i][0] and corner[l][0]+corner[l][2] > corner[j][0]):
                    if(corner[l][1] < corner[j][1]+rec[i][1] and (corner[l][3] == 0 or corner[l][1]+corner[l][3] > corner[j][1])):
                        if(corner[l][1] >= corner[j][1]):
                            corner[l][2] = corner[j][0]-corner[l][0]
                        elif(corner[l][0] >= corner[j][0]):
                            corner[l][3] = corner[j][1]-corner[l][1]
                        else:
                            for k in range(l+1,len(corner)):
                                if(corner[l][1] == corner[k][1]):
                                    if(corner[k][0] > corner[l][0] and corner[k][0] < corner[l][0]+corner[l][2]):
                                        delete.append(k)
                                if(corner[l][0] == corner[k][0]):
                                    if(corner[k][1] > corner[l][1] and corner[k][1] < corner[l][1]+corner[l][3]):
                                        delete.append(k)
                                        break
                            newcorner.append([corner[l][0],corner[l][1],corner[j][0]-corner[l][0],corner[l][3]])
                            corner[l][3] = corner[j][1]-corner[l][1]


            for l,num in enumerate(delete):
                del(corner[num - l])
            temp = 0
            for l in range(len(newcorner)):
                if(newcorner[l][0] == width):
                    continue
                for k in range(temp,len(corner)):
                    if(corner[k] == newcorner[l]):
                        break
                    if((corner[k][1] == newcorner[l][1] and corner[k][0] > newcorner[l][0]) or corner[k][1] > newcorner[l][1]):
                        corner.insert(k,newcorner[l])
                        temp = k+1
                        break
                else:
                    corner.append(newcorner[l])
                    temp = len(corner)
            break

leftup = umap[0][1] + 2
dwg = svgwrite.Drawing(filename="result.svg")
for i in range(len(umap)):
    dwg.add(dwg.rect(insert=((umap[i][0]-umap[i][2])*(100/leftup)*mm,(leftup-umap[i][1])*(100/leftup)*mm),size=(umap[i][2]*(100/leftup)*mm,umap[i][3]*(100/leftup)*mm),fill='black',fill_opacity=0.4,stroke='black'))
for i in range(len(corner)):
    if(corner[i][3] == 0):
        corner[i][3] = umap[0][1] + 2 - corner[i][1]
    dwg.add(dwg.rect(insert=(corner[i][0]*(100/leftup)*mm,(leftup-corner[i][1]-corner[i][3])*(100/leftup)*mm),size=(corner[i][2]*(100/leftup)*mm,corner[i][3]*(100/leftup)*mm),fill='red',fill_opacity=0.2,stroke='red'))
dwg.save()