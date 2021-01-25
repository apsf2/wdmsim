#!/usr/local/bin/python3

""" Faz leitura de arquivo contendo array bidimencional e popula lista em memoria """

from copy import deepcopy
import re
import time
import random
from collections import defaultdict
import getopt, sys
import sys
import os
import multiprocessing
from multiprocessing import Process
import numpy as np
import tinyarray as ta

###
###
### Get command line options, print Usage information
###
###

def getArgs():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hver:k:s:l:a:m:p:i:c:o:n:", ["help", "variable","asc","requests=","routes=","slots=","load=","algorithm=","average=","step=","init=","maxcores=","report=","matrix="])
	except getopt.GetoptError as err:
		print(err)
		printUsage()
		sys.exit(1)

	advancedcount = False
	output = None
	routes = 5
	variable = False
	maxslots = 352
	maxreqs = None
	maxload = None
	algo = None
	ave = 1
	step = 1
	init = None
	maxcores=0
	csvreport="report.csv"
	matrix="matrix.txt"

	for o,a in opts:
		if o in ("-h", "--help"):
			printUsage()
			sys.exit()

		elif o in ("-v","--variable"):
			variable = True

		elif o in ("-e","--asc"):
			advancedcount = True

		elif o in ("-r", "--requests"):
			maxreqs = a

		elif o in ("-k", "--routes"):
			routes = int(a)

		elif o in ("-s", "--slots"):
			maxslots= a

		elif o in ("-l","--load"):
			maxload = a

		elif o in ("-a","--algorithm"):
			algo = a

		elif o in ("-m","--average"):
			ave = a

		elif o in ("-p","--step"):
			step = a

		elif o in ("-i","--init"):
			init = a

		elif o in ("-c","--maxcores"):
			maxcores = a

		elif o in ("-o","--report"):
			csvreport = a

		elif o in ("-n","--matrix"):
			matrix = a

		else:
			print("Error: Invalid Option.")
			printUsage()
			sys.exit(1)

	if init == None:
		init = maxload

	if algo == None:
		algo = "FirstFit"

	if maxreqs == None or maxslots == None or maxload == None:
		print ("Error: Missing mandatory argument.")
		printUsage()
		sys.exit(1)

	return maxreqs,maxslots,maxload,routes,algo,variable,ave,step,init,advancedcount,maxcores,csvreport,matrix


def printUsage():
	print ("""WDMsim.py version 1.0
Author: Antonio Forster <aforster@gmail.com>
Usage:
-h		Print this help information
-n	<FILE>	Connectivity Matrix of the network to be simulated. Default is matrix.txt.
-v		Verbose output during execution
-b		Bidirecional links (default: false)
-r		Number of Requests in the simulation (mandatory)
-k		Number of alternate routes
-s		Number of FSUs (mandatory)
-e		Advanced Slot Count (--asc)
-a		Algorithm to be used (Default: FirstFit)
-m		Rounds of cycles
-p		Step of load variation
-i		Initial Load
-l		Load of the system in Erlangs - Max load in case of variation (mandatory)
-c		Number of processes to be executed. Maximum is #cores - 1. Default is 1
-o	<FILE>	Excel CSV file with simulation data. Default is report.csv.
""")


###
###
### Create structures
###
###


def initArray(index):
	return [[0]*index for i in range(index)]


def printArray(array):
	dimensao = len(array[0])
	print ("        ",end="")
	for index in range(0,dimensao):
		print ("{0:8}".format(index),end="")
		'''
		if index == 0:
			#print("   " + str(index) + " ", end=' ')
		else:

			print(str(index) + " ", end=' ')
		'''

	print()
	count = 0
	for line in array:
		print ("{0:8}".format(count),end="")
		for value in line:
			print ("{0:8}".format(value),end="")
		#print(str(count) + " " + str(line))
		count+=1
		print ()


def printTable(table):
	for line in table:
		print("Origem: " + str(line[0]) + " Destino: " + str(line[1]))
		line[2].sort(key=returnCost)
		for path in line[2]:
			print("Custo: " + str(path[0]) + " Rota: ", end=' ')
			print(path[1])
		print()


def loadMatrix(filename):
	f = open(filename,"r")
	row=0
	for linha in f:
		col=0
		#linha.replace(" ","")
		line=linha.split(",");
		if row == 0:
			dimensao = len(line)
			matriz=initArray(dimensao)
			#print "Criando array com " + str(dimensao) + " elementos"
		for c in line:
			#print("adicionando em %d e %d ") % (row,col)
			c.strip()
			if row == col:
				c = 0
			matriz[row][col]=int(c)
			col+=1
		row+=1
	f.close()
	return matriz

def create_slots(matriz,max):
	slots={}
	for src in range(0,len(matriz)):
		for dst in range(0,len(matriz[src])):
			cost = matriz[src][dst]
			if cost != 0:
				try:
					destinations = len(slots[src])
				except:
					slots[src]={}
			#	try:
			#		alllambs= len(slots[src][dst])
			#	except:
				slots[src][dst]=[0] * max
	return slots



###
###
### Graph discovery
###
###

def findPath(cost,path,src,dst,visited,matriz,validpaths):
	cost = deepcopy(cost)
	path = deepcopy(path)
	visited = deepcopy(visited)
	src=deepcopy(src)
	dst=deepcopy(dst)
	for hop in range(0,len(matriz[src])):
		if (matriz[src][hop] == 0):
			continue

		if hop == src:
			continue

		if hop in visited:
			continue

		if hop == dst:
			#visited[hop]=1
			newpath=deepcopy(path)
			newpath.append(dst)
			newcost=cost+matriz[src][hop]
			element=[newcost,newpath]
			validpaths.append(element)
			continue

		newpath=deepcopy(path)
		newpath.append(hop)
		visited[hop]=1
		newcost=cost+matriz[src][hop]
		findPath(newcost,newpath,hop,dst,visited,matriz,validpaths)
		del(visited[hop])
	return


def listPaths(src,dst,matriz):
	global validpaths
	validpaths=[]
	if (src == dst):
		return [src]
	visited={}
	visited[src]=1
	path=[]
	path.append(src)
	findPath(0,path,src,dst,visited,matriz,validpaths)
	return validpaths


###
###
### Sort routes
###
###

def returnCost(path):
	return (path[0],len(path[1]))


def returnLength(path):
	return (len(path[1]),path[0])


###
###
### Print possible routes and exit - To be used for debugging purposes
###
###

def calc_routes():
	matrix=loadMatrix("matrix.txt")
	print("Connectivity Matrix: ")
	printArray(matrix)
	print()

	dimensao = len(matrix[0])

	for src in range (0,dimensao):
		for dst in range (0,dimensao):
			if src == dst:
				continue
			start=getUptime()
			validpaths=listPaths(src,dst,matrix)
			final=getUptime()
			delta = final - start
			print("Tempo: " + str(delta))
			print()
			print("Caminhos entre " + str(src) + " e " + str(dst) + " ordenados por numero de hops: ")
			validpaths.sort(key=returnLength)
			print(validpaths)
			print()
			print("Caminhos entre " + str(src) + " e " + str(dst) + " ordenados por custo: ")
			validpaths.sort(key=returnCost)
			print(validpaths)


###
###
### Implement Fist Fit Wavelenght Assigment algorithm
###
###

def checkFreeSlots_vector(slots,fiberpath):
	### ASC implementation
    ### check all fibers in path and return list of slots that are available in the entire path

	final=[]
	#inter=[]
    
	#print ("tamanho de path é" + str(len(fiberpath)))
	for fiber in fiberpath:
		fiber_s=fiber[0]
		fiber_d=fiber[1]
		#print ("Caminho a ser somado {} -> {}".format(fiber_s,fiber_d))
		#print ("tamanho de inter é" + str(len(inter)))
		if (len(final)==0):
			final = deepcopy(slots[fiber_s][fiber_d])
			#inter = final
			continue
		#print ("Somando " + str(slots[fiber_s][fiber_d]))
		final = ta.add(ta.absolute(slots[fiber_s][fiber_d]),final)
		#inter = deepcopy(final)
	return final

def checkFreeSlots(slots,fiberpath):
	### ASC implementation

	sum = int('0',2)
	#msb = int('1',2)
    
	#calculate msb 
	#for slot in range(0,maxslots):
		#msb = msb << 1

	#print ("tamanho de path é" + str(len(fiberpath)))
	for fiber in fiberpath:
		current = int('1',2)
		fiber_s=fiber[0]
		fiber_d=fiber[1]
		#print ("Caminho a ser somado {} -> {}".format(fiber_s,fiber_d))
		#print ("tamanho de inter é" + str(len(inter)))
		for slot in slots[fiber_s][fiber_d]:
			current = current << 1
			if slot!=0:
				current = current | 1

		sum = sum | current

	#mask = ~msb
	#sum = sum & mask	
	
	final = [(sum >> bit) & 1 for bit in range(maxslots - 1, -1, -1)]

	return final



def firstfit(req,src,dst,qtd,allroutes,slots,max,routes):
	# qtd = number of lambdas for the request
	# max = number of lambdas per fiber
	# routes = number of considered routes (k-routes)

	validpaths=allroutes[src][dst]
	lamb=0
	count=0
	for route in validpaths:
		if count > routes:
			break;
		count=count + 1
		cost=route[0]
		path=route[1]
		fibers=[]
		s=""
		d=""
		for hop in path:
			if s == "":
				s = hop
				continue
			if d == "":
				d = hop
				fibers.append((s,d))
				s = d
				d = ""

		sumslots=[]
		if advancedcount:
			sumslots = checkFreeSlots(slots,fibers)
			#print (str(sumslots))
		
		for slot in range(0,max-qtd+1):
			if advancedcount:
				#print ("Calculando soma de slot "+str(slot))
				if sumslots[slot]!=0:
					#print ("Soma para slot "+str(slot)+" deu "+ str(sumslots[slot]))
					#print ("Descartou")
					continue
			for fiber in fibers:
				lamb=slot
				fiber_s=fiber[0]
				fiber_d=fiber[1]
				for templamb in range(lamb,lamb+qtd):
					if (slots[fiber_s][fiber_d][templamb] != 0):
						lamb=""
						break
				if lamb=="":
					break

			if lamb!="":
				for fiber in fibers:
					fiber_s=fiber[0]
					fiber_d=fiber[1]
					for templamb in range(lamb,lamb+qtd):
						slots[fiber_s][fiber_d][templamb]=req
				return (lamb,fibers)
	#print("Req " + req + " Bloqueado - Path:",end="")
	#print (path)
	return ("BLOCK",[])

###
###
### Implement Alternate Fist Fit Wavelenght Assigment algorithm
###
###

def altfirstfit(req,src,dst,qtd,allroutes,slots,max,routes):
	# qtd = number of lambdas for the request
	# max = number of lambdas per fiber
	# routes = number of considered routes (k-routes)

	validpaths=allroutes[src][dst]
	lamb=0
	count=0
	for route in validpaths:
		#print ("Loop com lamb = " + str(slot) + " qtd = " + str(qtd) + " para src = " + str(src) + " dst =  " + str(dst) + " via " + str(route) )
		if count >= routes:
			count = 1
			break
		count=count + 1
		cost=route[0]
		path=route[1]
		fibers=[]
		s=""
		d=""

		for hop in path:
			if s == "":
				s = hop
				continue
			if d == "":
				d = hop
				fibers.append((s,d))
				s = d
				d = ""

		for s_count in range(0,max):
			exp = s_count % 2 ### Varia entre 0 e 1 (resto da divisao por 2
			sentido = (-1)**exp  ### Sentido vai variar entre -1 e 1
			slot = (max-1) * exp + sentido * int(s_count/2)

			## O calculo acima gerara uma sequencia de slots "um do comeco, um do fim"
			## Caso s_count seja par, seleciona do inicio, caso seja impar, do final iniciando pelo lambda maximo
			## 0,352,1,351,2,350,3,349,4,348......177,176
			for fiber in fibers:
				lamb=slot
				channel=[]
				fiber_s=fiber[0]
				fiber_d=fiber[1]
				if sentido == 1:
					channel = range(lamb, lamb+qtd)
				else:
					channel = range(lamb, lamb-qtd, -1)

				for templamb in channel:
					if (slots[fiber_s][fiber_d][templamb] != 0):
						lamb=""
						break
				if lamb=="":
					break

			if lamb!="":

				for fiber in fibers:
					fiber_s=fiber[0]
					fiber_d=fiber[1]
					if sentido == 1:
						channel = range(lamb, lamb+qtd)
					else:
						channel = range(lamb, lamb-qtd, -1)

					for templamb in channel:
						slots[fiber_s][fiber_d][templamb]=req

				if sentido == 1:
					return(lamb,fibers)
				else:
					return(lamb+1-qtd,fibers)



	#print("Req " + req + " Bloqueado - Path:",end="")
	#print (path)
	return ("BLOCK",[])

#


###
###
### Implement Best Fit Wavelenght Assigment algorithm
### Fragmentation and utilization aware allocation algorithm
###
###

def lock_reverse(req,path,lamb,qtd,slots):

	#print ("Caminho a ser bloqueado (reverso): ",end="")
	#print (path)
	d = ""
	s = ""

	for dst,src in path:
		channel = range(lamb, lamb+qtd)
		for templamb in channel:
			if (slots[src][dst][templamb] != 0):
				lamb=""
				print ("src {} dst {} lamb {} deveria estar livre, mas nao esta: {}".format(src,dst,templamb,slots[src][dst][templamb]))
				raise RuntimeError ("deveria estar livre, mas nao esta")
			else:
				slots[src][dst][templamb]=req
				#print ("blocking fibra {} para {} lamb {} para req {}".format(src,dst,templamb,req))


def bestfrag(req,src,dst,qtd,allroutes,slots,max,routes,frag_info):
	# qtd = number of lambdas for the request
	# max = number of lambdas per fiber
	# routes = number of considered routes (k-routes)

	validpaths=allroutes[src][dst]
	foundpaths=[]
	lamb=0
	count=0
	candidatePath=[]
	candidateLamb=None
	testedLamb=None
	testedPath=[]
	candidateDelta = None
	limit = 80
	linearLimit = 20
	init = getUptime()
	attempt = 0
	pulou = 0
	trocou = 0

	#print ("Valid Routes de {} para {}:".format(src,dst),end="")
	#print (validpaths)

	for route in validpaths:
		iteraction=0
		sequence = 0
		#print ("-----------------Loop de nova rota ordem {}: {}".format(count,route))
		if count >= routes:
		#	print ("Limite de k-rotas atingido: rota {}  para limite {}".format(count,routes))
			#count = 1
			break
		count=count + 1
		#print ("Testando rota {} para src = {} dst = {}".format(count,src,dst))
		cost=route[0]
		path=route[1]
		fibers=[]
		s=""
		d=""
		for hop in path:
			if s == "":
				s = hop
				continue
			if d == "":
				d = hop
				fibers.append((s,d))
				s = d
				d = ""

		sumslots=[]
		if advancedcount:
			#sumslots = checkFreeSlots_vector(slots,fibers)
			#print ("SUMSLOTS (old):" + str(sumslots))
			sumslots = checkFreeSlots(slots,fibers)
			#print ("SUMSLOTS:" + str(sumslots))

		for slot in range(0,max-qtd+1):
			if advancedcount:

				#print ("Slot atual ("+ str(slot)+"): " + str(sumslots[slot]) + "  -   Anterior:  "+str(sumslots[slot-1]) +  " -  Posterior:  " + str(sumslots[slot+1]))

				if sumslots[slot] != 0:
					continue

				#print ('checking adjacency for slot {}'.format(slot))
				if len(candidatePath) > 0 and slot > 0  and sumslots[slot-1] == 0 and sumslots[slot+1] == 0:
				# check adjacency
					continue

			#print ("Entrou")
			attempt = attempt + 1
			sentido = 1
			#tdelta = getUptime() - init; print ("Time Mark: " + str(tdelta))
			#print ("Loop com lamb = " + str(slot) + " qtd = " + str(qtd) + " para src = " + str(src) + " dst =  " + str(dst) + " via " + str(route) )
			if (iteraction >= limit) and (len(candidatePath) > 0):
				print ("Limite de loops {}.. pegando o melhor ate o momento: {} {}".format(iteraction,candidatePath,candidateDelta))
				break

			## O calculo acima gerara uma sequencia de slots "um do comeco, um do fim"
			## Caso s_count seja par, seleciona do inicio, caso seja impar, do final iniciando pelo lambda maximo
			## 0,352,1,351,2,350,3,349,4,348......177,176

			#print ("------------------------Novo Lambda: " + str(slot))

			channel=[]
			lamb=slot
			adj_sup = ""
			adj_ant = ""

			if not advancedcount:
				if sentido == 1:
					channel = range(lamb, lamb+qtd)
					adj_ant_ind = lamb - 1
					adj_sup_ind = lamb + qtd
				else:
					channel = range(lamb, lamb-qtd, -1)
					adj_ant_ind = lamb + 1
					adj_sup_ind = lamb - qtd

				adj_sup = 0
				adj_ant = 0
			else:
				channel = range(lamb, lamb+qtd)

			for fiber in fibers:
				fiber_s=fiber[0]
				fiber_d=fiber[1]

				if not advancedcount:
					if (0 <= adj_sup_ind <= (max -1)):
						if slots[fiber_s][fiber_d][adj_sup_ind] != 0:
							adj_sup = "used"
					else:
						adj_sup = "border"

					if (0 <= adj_ant_ind <= (max -1)):
						if slots[fiber_s][fiber_d][adj_ant_ind] != 0:
							adj_ant = "used"
					else:
						adj_ant = "border"

				for templamb in channel:
					#print ("Testando {} em {} para {}".format(templamb,fiber_s,fiber_d))
					if (slots[fiber_s][fiber_d][templamb] != 0):
						#print ("Nao tem lambda {} neste caminho {}".format(slot,fibers))
						lamb=""
						break

				if lamb == "":
					break

			if adj_sup == 0 and adj_ant == 0:
				pulou+=1
				lamb = ""
				#print ("Unused borders")
				continue
	
			if lamb!="":
				#print ("ACHOU!")
				iteraction = iteraction + 1

				propLamb = lamb
				propPath = fibers

				#print ("Testando caminho valido:  " + str(propLamb) + " qtd = "+ str(qtd) + " e " + str(propPath) + "candidate ja eh "+ str(candidatePath))
				#print ("Iteracao: " + str(iteraction))


				#tdelta = getUptime() - init; print ("Time Mark: " + str(tdelta))
				origFrag,finalFrag=testFragmentation(propLamb,propPath,sentido,qtd,slots,frag_info);
				#tdelta = getUptime() - init; print ("Time Mark after testFrag: " + str(tdelta))

				testedDelta = (origFrag - finalFrag) / cost
				#testedDelta = origFrag - finalFrag

				testedLamb = propLamb
				testedPath = propPath


				if candidatePath == []:
					#print ("=======>candidatePath estava vazio... candidatePath definido")
					#print ("=======> novo candidatePath definido: Novo candidateDelta = {}".format(testedDelta))
					candidatePath = propPath
					candidateLamb = propLamb
					candidateSent = sentido
					candidateDelta = testedDelta
					#print ("=======> novo path e lambda:  {} slot {}".format(candidatePath,candidateLamb))
					sequence = 0
					#continue

				if (finalFrag == 1 or (testedDelta == 0 and candidateDelta != None and candidatePath != [])):
					candidateSent = sentido
					candidateLamb = propLamb
					candidatePath = propPath

					for fiber in candidatePath:
						channel=[]
						fiber_s=fiber[0]
						fiber_d=fiber[1]
						if sentido == 1:
							channel = range(candidateLamb, candidateLamb+qtd)
						else:
							channel = range(candidateLamb, candidateLamb-qtd, -1)

						for templamb in channel:
							slots[fiber_s][fiber_d][templamb]=req

					#print (">>>>>>>>>>Fechou em  " + str(candidateLamb) + " + "+ str(qtd) + " e " + str(candidatePath) + "k = "+str(count) + " Attempt = " + str(attempt) + " Pulou " + str(pulou) + " Trocou " + str(trocou))
					try:
						del(frag_info[src][dst])
					except:
						pass

					if candidateSent == 1:
						return(candidateLamb,candidatePath)
					else:
						return(candidateLamb+1-qtd,candidatePath)


				elif (testedDelta >= candidateDelta):
					#print ("Descartando... testedDelta {}  >  candidateDelta {} candidatePath {}".format(testedDelta,candidateDelta,candidatePath))
					sequence+=1

					if (sequence == linearLimit):
						iteraction = limit
						#print ("===============>Break Sequence!!!")
						break

					continue


				elif testedDelta < candidateDelta:
					sequence = 0
					#print ("=======> novo candidatePath definido: antigo candidateDelta = {} Novo candidateDelta = {}".format(candidateDelta,testedDelta))
					candidateSent = sentido
					candidateLamb = propLamb
					candidatePath = propPath
					candidateDelta = testedDelta
					trocou += 1
					#print ("=======> novo path e lambda:  {} slot {}".format(candidatePath,candidateLamb))
					try:
						del(frag_info[src][dst])
					except:
						pass

					origFrag = finalFrag
					continue

				else:
					continue
					#raise RuntimeError('ELSE QUE NAO DEVERIA') from error

	if len(candidatePath) > 0:
		#print ("Candidate eh " + str(candidatePath))
		for fiber in candidatePath:
			fiber_s=fiber[0]
			fiber_d=fiber[1]
			if candidateSent == 1:
				channel = range(candidateLamb, candidateLamb+qtd)
			else:
				channel = range(candidateLamb, candidateLamb-qtd, -1)


			for templamb in channel:
				#print ("Testando erro:  templamb = " + str(templamb))
				#print ("lamb = {} qtd = {}".format(str(candidateLamb),str(qtd)))
				slots[fiber_s][fiber_d][templamb]=req

		#print (">>>>>>>>>> Last: Fechou em  " + str(candidateLamb) + " + "+ str(qtd) + " e " + str(candidatePath) + "k = "+str(count) + " Attempt = " + str(attempt) + " Pulou " + str(pulou) + " Trocou " + str(trocou))
		try:
			del(frag_info[src][dst])
		except:
			pass

		if candidateSent == 1:
			return(candidateLamb,candidatePath)
		else:
			return(candidateLamb+1-qtd,candidatePath)
	else:
		#print("Req " + req + " Bloqueado - Path:",end="")
		#print (path)
		return ("BLOCK",[])


def altbestfrag(req,src,dst,qtd,allroutes,slots,max,routes,frag_info):
	# qtd = number of lambdas for the request
	# max = number of lambdas per fiber
	# routes = number of considered routes (k-routes)

	validpaths=allroutes[src][dst]
	foundpaths=[]
	lamb=0
	count=0
	candidatePath=[]
	candidateLamb=None
	testedLamb=None
	testedPath=[]
	candidateDelta = None
	limit = 80
	linearLimit = 20
	init = getUptime()
	attempt = 0
	pulou = 0
	trocou = 0

	#print ("Valid Routes de {} para {}:".format(src,dst),end="")
	#print (validpaths)

	for route in validpaths:
		iteraction=0
		sequence = 0
		#print ("-----------------Loop de nova rota ordem {}: {}".format(count,route))
		if count >= routes:
		#	print ("Limite de k-rotas atingido: rota {}  para limite {}".format(count,routes))
			#count = 1
			break
		count=count + 1
		#print ("Testando rota {} para src = {} dst = {}".format(count,src,dst))
		cost=route[0]
		path=route[1]
		fibers=[]
		s=""
		d=""
		for hop in path:
			if s == "":
				s = hop
				continue
			if d == "":
				d = hop
				fibers.append((s,d))
				s = d
				d = ""

		sumslots=[]
		if advancedcount:
			sumslots = checkFreeSlots(slots,fibers)

		for s_count in range(0,max):
			#tdelta = getUptime() - init; print ("Time Mark: " + str(tdelta))
			exp = s_count % 2
			sentido = (-1)**exp
			slot = (max-1) * exp + sentido * int(s_count/2)
			#sentido = 1
			#slot = s_count
			#print ("Loop com lamb = " + str(slot) + " qtd = " + str(qtd) + " para src = " + str(src) + " dst =  " + str(dst) + " via " + str(route) )

			if advancedcount:
				if sumslots[slot] != 0:
					continue

				if slot > 0 and slot < (max - 1):
					if len(candidatePath) > 0 and sumslots[slot-1] == 0 and sumslots[slot+1] == 0:
						continue

			attempt = attempt + 1

			if (iteraction >= limit) and (len(candidatePath) > 0):
				print ("Limite de loops {}.. pegando o melhor ate o momento: {} {}".format(iteraction,candidatePath,candidateDelta))
				break

			## O calculo acima gerara uma sequencia de slots "um do comeco, um do fim"
			## Caso s_count seja par, seleciona do inicio, caso seja impar, do final iniciando pelo lambda maximo
			## 0,352,1,351,2,350,3,349,4,348......177,176

			#print ("------------------------Novo Lambda: " + str(slot))

			channel=[]
			lamb=slot
			adj_sup = ""
			adp_ant = ""

			if sentido == 1:
				channel = range(lamb, lamb+qtd)
				adj_ant_ind = lamb - 1
				adj_sup_ind = lamb + qtd
			else:
				channel = range(lamb, lamb-qtd, -1)
				adj_ant_ind = lamb + 1
				adj_sup_ind = lamb - qtd

			adj_sup = 0
			adj_ant = 0

			for fiber in fibers:
				fiber_s=fiber[0]
				fiber_d=fiber[1]

				if not advancedcount:
					if (0 <= adj_sup_ind <= (max -1)):
						if slots[fiber_s][fiber_d][adj_sup_ind] != 0:
							adj_sup = "used"
					else:
						adj_sup = "border"

					if (0 <= adj_ant_ind <= (max -1)):
						if slots[fiber_s][fiber_d][adj_ant_ind] != 0:
							adj_ant = "used"
					else:
						adj_ant = "border"

				for templamb in channel:
					#print ("Testando {} em {} para {}".format(templamb,fiber_s,fiber_d))
					if (slots[fiber_s][fiber_d][templamb] != 0):
						#print ("Nao tem lambda {} neste caminho {}".format(slot,fibers))
						lamb=""
						break

				if lamb == "":
					break

			#print ("Bordas sao {} {} com status {} {}".format(adj_ant_ind,adj_sup_ind,adj_ant,adj_sup))

			if adj_sup == 0 and adj_ant == 0 and not advancedcount:
				pulou+=1
				lamb = ""
				#print ("Unused borders")
				continue

			if lamb!="":
				#print ("ACHOU!")
				iteraction = iteraction + 1

				propLamb = lamb
				propPath = fibers

				#print ("Testando caminho valido:  " + str(propLamb) + " qtd = "+ str(qtd) + " e " + str(propPath) + "candidate ja eh "+ str(candidatePath))
				#print ("Iteracao: " + str(iteraction))


				#tdelta = getUptime() - init; print ("Time Mark: " + str(tdelta))
				origFrag,finalFrag=testFragmentation(propLamb,propPath,sentido,qtd,slots,frag_info);
				#tdelta = getUptime() - init; print ("Time Mark after testFrag: " + str(tdelta))

				testedDelta = (origFrag - finalFrag) / cost
				#testedDelta = origFrag - finalFrag

				testedLamb = propLamb
				testedPath = propPath


				if candidatePath == []:
					#print ("=======>candidatePath estava vazio... candidatePath definido")
					#print ("=======> novo candidatePath definido: Novo candidateDelta = {}".format(testedDelta))
					candidatePath = propPath
					candidateLamb = propLamb
					candidateSent = sentido
					candidateDelta = testedDelta
					#print ("=======> novo path e lambda:  {} slot {}".format(candidatePath,candidateLamb))
					sequence = 0
					#continue

				if (finalFrag == 1 or (testedDelta == 0 and candidateDelta != None and candidatePath != [])):
					candidateSent = sentido
					candidateLamb = propLamb
					candidatePath = propPath

					for fiber in candidatePath:
						channel=[]
						fiber_s=fiber[0]
						fiber_d=fiber[1]
						if sentido == 1:
							channel = range(candidateLamb, candidateLamb+qtd)
						else:
							channel = range(candidateLamb, candidateLamb-qtd, -1)

						for templamb in channel:
							slots[fiber_s][fiber_d][templamb]=req

					#print (">>>>>>>>>>Fechou em  " + str(candidateLamb) + " + "+ str(qtd) + " e " + str(candidatePath) + "k = "+str(count) + " Attempt = " + str(attempt) + " Pulou " + str(pulou) + " Trocou " + str(trocou))
					try:
						del(frag_info[src][dst])
					except:
						pass

					if candidateSent == 1:
						return(candidateLamb,candidatePath)
					else:
						return(candidateLamb+1-qtd,candidatePath)


				elif (testedDelta >= candidateDelta):
					#print ("Descartando... testedDelta {}  >  candidateDelta {} candidatePath {}".format(testedDelta,candidateDelta,candidatePath))
					sequence+=1

					if (sequence == linearLimit):
						iteraction = limit
						#print ("===============>Break Sequence!!!")
						break

					continue


				elif testedDelta < candidateDelta:
					sequence = 0
					#print ("=======> novo candidatePath definido: antigo candidateDelta = {} Novo candidateDelta = {}".format(candidateDelta,testedDelta))
					candidateSent = sentido
					candidateLamb = propLamb
					candidatePath = propPath
					candidateDelta = testedDelta
					trocou += 1
					#print ("=======> novo path e lambda:  {} slot {}".format(candidatePath,candidateLamb))
					try:
						del(frag_info[src][dst])
					except:
						pass

					origFrag = finalFrag
					continue

				else:
					continue
					#raise RuntimeError('ELSE QUE NAO DEVERIA') from error

	if len(candidatePath) > 0:
		#print ("Candidate eh " + str(candidatePath))
		for fiber in candidatePath:
			fiber_s=fiber[0]
			fiber_d=fiber[1]
			if candidateSent == 1:
				channel = range(candidateLamb, candidateLamb+qtd)
			else:
				channel = range(candidateLamb, candidateLamb-qtd, -1)


			for templamb in channel:
				#print ("Testando erro:  templamb = " + str(templamb))
				#print ("lamb = {} qtd = {}".format(str(candidateLamb),str(qtd)))
				slots[fiber_s][fiber_d][templamb]=req

		#print (">>>>>>>>>> Last: Fechou em  " + str(candidateLamb) + " + "+ str(qtd) + " e " + str(candidatePath) + "k = "+str(count) + " Attempt = " + str(attempt) + " Pulou " + str(pulou) + " Trocou " + str(trocou))
		try:
			del(frag_info[src][dst])
		except:
			pass

		if candidateSent == 1:
			return(candidateLamb,candidatePath)
		else:
			return(candidateLamb+1-qtd,candidatePath)
	else:
		#print("Req " + req + " Bloqueado - Path:",end="")
		#print (path)
		return ("BLOCK",[])


def testFragmentation(lamb,path,sentido,qtd,oldslots,frag_info):
	slots=deepcopy(oldslots)
	totalfrag = 0
	for src,dst in path:
		used = 0
		free = 0
		maxContFree = 0
		contFree = 0
		frag=0
		try:
			segFrag = frag_info[src][dst]
		except:
			for slot in slots[src][dst]:
				if slot == 0:
					free += 1
					contFree += 1
					if maxContFree < contFree:
						maxContFree = contFree
				else:
					used += 1
					contFree = 0
			try:
				frag=maxContFree/free
			except:
				#print ("entrou no except")
				frag=0

			frag_info[src][dst]=frag


		totalfrag += frag

	origFrag= totalfrag/len(path)

	for fiber in path:
		channel=[]
		fiber_s=fiber[0]
		fiber_d=fiber[1]
		if sentido == 1:
			channel = range(lamb, lamb+qtd)
		else:
			channel = range(lamb, lamb-qtd, -1)

		for templamb in channel:
			#print ("Channel = " + str(channel))

			slots[fiber_s][fiber_d][templamb]='new'


	totalfrag = 0
	for src,dst in path:
		used = 0
		free = 0
		maxContFree = 0
		contFree = 0
		frag=0
		for slot in slots[src][dst]:
			if slot == 0:
				free += 1
				contFree += 1
				if maxContFree < contFree:
					maxContFree = contFree
			else:
				used += 1
				contFree = 0
		try:
			frag=maxContFree/free
		except:
			frag=0

		totalfrag += frag

	finalFrag=  totalfrag/len(path)

	return origFrag,finalFrag



###
###
### Delete link from list
###
###

def link_delete(linkname,reqs,slots):
	if linkname in (reqs.keys()):
		request=reqs[linkname]
		path=request[2]
		lambd=request[3]
		qtd=request[4]
		for fiber in path:
			src=fiber[0]
			dst=fiber[1]
			for fsu in range(0,qtd):
				temp=lambd+fsu
				slots[src][dst][temp]=0
		del(reqs[linkname])

		other=linkname * (-1)

	if other in (reqs.keys()):
		request=reqs[other]
		path=request[2]
		lambd=request[3]
		qtd=request[4]
		for fiber in path:
			dst=fiber[0]
			src=fiber[1]
			for fsu in range(0,qtd):
				temp=lambd+fsu
				slots[src][dst][temp]=0
		del(reqs[other])
###
###
### Calculate usage ratio on fiber
###
###

def getNetworkStats(slots,maxslots):
	linkUsage=defaultdict(dict)
	linkFrag=defaultdict(dict)
	networkFrag=0
	networkUsage=0
	sumFrag=0
	sumUsage=0
	links=0
	minFrag=0
	maxUsage=0
	maxFrag=1
	minUsage=1
	usageval=[]
	fragval=[]

	for src in slots:
		for dst in slots[src]:
			links+=1
			used = 0
			free = 0
			maxContFree = 0
			contFree = 0
			frag=0
			usage=0
			for slot in slots[src][dst]:
				if slot == 0:
					free += 1
					contFree += 1
					if maxContFree < contFree:
						maxContFree = contFree
				else:
					used += 1
					contFree = 0
			try:
				frag=maxContFree/free
			except:
				frag=0

			linkFrag[src][dst]=frag
			if frag > minFrag:
				minFrag = frag

			if frag < maxFrag:
				maxFrag = frag
			fragval.append(frag)
			usage=used/maxslots
			linkUsage[src][dst]=usage
			if usage > maxUsage:
				maxUsage = usage
			if usage < minUsage:
				minUsage=usage
			usageval.append(usage)
			try:
				sumFrag+=(maxContFree/free)
			except:
				pass

			sumUsage+=(used/maxslots)

	networkUsage=sumUsage/links
	networkFrag=1-(sumFrag/links)
	fragval.sort()
	usageval.sort()
	index=len(fragval)
	mediumfrag=1-(fragval[int(index/2)])
	mediumusage=usageval[int(index/2)]
	minFrag=1-minFrag
	maxFrag=1-maxFrag

	return (networkUsage,mediumusage,maxUsage,minUsage,networkFrag,mediumfrag,minFrag,maxFrag,linkFrag,linkUsage)


def printAlloc (slots):
	for src in slots:
		for dst in slots[src]:
			print("Fibra " + str(src) + " - " + str(dst), end=' ')
			print(slots[src][dst])



def run_round(load,rounds,csvQueue,start_time):
	#print ("Init thread for " + str(load))
	#sys.stdout.flush()
	frag_info=defaultdict(dict)
	allblocks=0
	allusage=0
	allmaxusage=0
	allfrag=0
	allmaxfrag=0
	allLinkCount=0
	allmediumU=0
	allminU=0
	allminF=0
	allmediumF=0
	bandwidths=[2,4,4,6,12]
	linkCount = 0
	maxLinkCount = 0
	allDuration = 0

	for round in range (1,rounds+1):
		round_start = getUptime()
		deleted=0
		added = 0
		blocks=0
		slots=create_slots(matrix,maxslots)
		requests=defaultdict(dict)
		for link in range(1,maxreqs+1):
			src=random.randrange(0,dimensao)
			dst=random.randrange(0,dimensao)
			while src == dst:
				src=random.randrange(0,dimensao)
				dst=random.randrange(0,dimensao)
			linkname=link
			path=""

			qtd=bandwidths[random.randrange(0,5)]
			

			if algorithm == "FirstFit":
				newpath=firstfit(linkname,src,dst,qtd,allroutes,slots,maxslots,maxroutes)
			elif algorithm == "AltBestFrag":
				#print ("Iniciando altbestfrag para Req {} src {} dst {} k-routes {}".format(link,src,dst,maxroutes))
				newpath=altbestfrag(linkname,src,dst,qtd,allroutes,slots,maxslots,maxroutes,frag_info)
				timestamp = getUptime() - start_time
				#print ("Mark: " + str(timestamp))
			elif algorithm == "BestFrag":
				#print ("Iniciando bestfrag para Req {} src {} dst {} k-routes {}".format(link,src,dst,maxroutes))
				newpath=bestfrag(linkname,src,dst,qtd,allroutes,slots,maxslots,maxroutes,frag_info)
				timestamp = getUptime() - start_time
				#print ("Mark: " + str(timestamp))
			elif algorithm == "AltFirstFit":
				newpath=altfirstfit(linkname,src,dst,qtd,allroutes,slots,maxslots,maxroutes)


			lambd=newpath[0]
			path=newpath[1]

			if lambd == "BLOCK":
				blocks+=1
				#print ("Allocation when BLOCKED: from " + str(src) + " to " + str(dst))
				#printAlloc(slots)
			else:
				requests[linkname]=(src,dst,path,lambd,qtd)
				added = added + 1
				#print ("Adicionou {} counter {} deleted {} src {} dst {} path {} lambda {} qtd {} load {}".format(linkname,added,deleted,str(src),str(dst),str(path),str(lambd),str(qtd),load))

				Rlinkname=linkname*(-1)
				requests[Rlinkname]=(dst,src,path,lambd,qtd)
				lock_reverse(Rlinkname,path,lambd,qtd,slots)

			#if link%100 == 0:
				#netstats=getNetworkStats(slots,maxslots)
				#### networkUsage,mediumusage,maxUsage,minUsage,networkFrag,mediumfrag,minFrag,maxFrag,linkFrag,linkUsage
				#networkUsage=netstats[0]
				#maxUsage=netstats[2]
				#networkFrag=netstats[4]
				#minFrag=netstats[6]
				#print("Stat: %d %d %d %1.4f %1.4f %1.4f %1.4f" % (link,load,blocks,networkUsage,maxUsage,networkFrag,minFrag))


			#print ("Numero de links: {} Load:  {}".format(str(len(list(requests.keys()))),str(load)))


			if (linkCount >= load):
				#print ("Deletando...")
				linknames=list(requests.keys())
				link_delete(random.choice(linknames),requests,slots)
				deleted = deleted + 1

			linkCount = added - deleted
			maxLinkCount = linkCount if (linkCount > maxLinkCount) else maxLinkCount

			sys.stdout.flush()

        ####### 
		### Print Results
		#print ("Final Allocation")
		#print ("================")
		#printAlloc(slots)
		#print ("total de links: ")
		#print (len(list(requests.keys())))
		#for link in requests:
		#	print(str(link) + ": ", end=' ')
		#	print(requests[link])
		#
		#print("Quantidade de Blocks: " + str(blocks))

        ######

		netstats=getNetworkStats(slots,maxslots)
		### Returns: (networkUsage,mediumusage,maxUsage,minUsage,networkFrag,mediumfrag,minFrag,maxFrag,linkFrag,linkUsage)
		networkUsage=netstats[0]
		mediumU=netstats[1]
		maxUsage=netstats[2]
		minUsage=netstats[3]
		networkFrag=netstats[4]
		mediumF=netstats[5]
		minFrag=netstats[6]
		maxFrag=netstats[7]



		allblocks+=blocks
		allusage+=networkUsage
		allmediumU+=mediumU
		allminU+=minUsage
		allmaxusage+=maxUsage
		allfrag+=networkFrag
		allmaxfrag+=minFrag
		allminF+=maxFrag
		allmediumF+=mediumF
		allLinkCount+=maxLinkCount

		now = getUptime()
		timestamp = now - start_time
		duration = now - round_start
		allDuration+=duration

		if (rounds > 1):
			print("Round Stat: {0:8.0f}  {1:8.0f}  {2:8.0f}   {3:8.0f}   {4:8.5f}   {5:8.5f}   {6:8.5f}   {7:8.5f}   {8:8.5f}   {9:8.5f}   {10:8.5f}   {11:8.5f} {12:8.1f} {13:8.1f}".format(maxreqs,maxLinkCount,load,blocks,networkUsage,mediumU,maxUsage,minUsage,networkFrag,mediumF,minFrag,maxFrag,timestamp,duration))

		sys.stdout.flush()

	blocks=allblocks/rounds
	networkUsage=allusage/rounds
	mediumU=allmediumU/rounds
	maxUsage=allmaxusage/rounds
	minUsage=allminU/rounds
	networkFrag=allfrag/rounds
	mediumF=allmediumF/rounds
	minFrag=allmaxfrag/rounds
	maxFrag=allminF/rounds
	avgMaxLinkCount=allLinkCount/rounds
	avgDuration = allDuration/rounds

	timestamp = getUptime() - start_time
	print("Last Stat: {0:8.0f}   {1:8.0f}   {2:8.0f}   {3:8.0f}   {4:8.5f}   {5:8.5f}   {6:8.5f}   {7:8.5f}   {8:8.5f}   {9:8.5f}   {10:8.5f}   {11:8.5f} {12:8.1f} {13:8.1f}".format(maxreqs,maxLinkCount,load,blocks,networkUsage,mediumU,maxUsage,minUsage,networkFrag,mediumF,minFrag,maxFrag,timestamp,avgDuration))
	message=("{0:8.0f},{1:8.0f},{2:8.0f},{3:8.0f},{4:8.5f},{5:8.5f},{6:8.5f},{7:8.5f},{8:8.5f},{9:8.5f},{10:8.5f},{11:8.5f},{12:8.1f},{13:8.1f}".format(maxreqs,maxLinkCount,load,blocks,networkUsage,mediumU,maxUsage,minUsage,networkFrag,mediumF,minFrag,maxFrag,timestamp,avgDuration))
	csvQueue.put(message)


def listener(csvreport,queue):
	'''listens for messages on the CSV queue writes to file. '''
	with open(csvreport, 'w') as f:
		while 1:
			line = queue.get()
			if line == 'kill':
				f.close()
				break
			else:
				f.write(line + '\n')
				f.flush()

def getUptime():
	with open('/proc/uptime', 'r') as f:
	    return float(f.readline().split()[0])


def main():
	start_time = getUptime()
	# Global variables must be used so forked process will have access to them
	global maxslots,maxreqs,dimensao,algorithm,allroutes,maxroutes,advancedcount,matrix

	reqs,lambdas,sysload,maxroutes,algorithm,variable,ave,passo,inicio,advancedcount,maxcores,csvreport,matrixfile=getArgs()
	maxreqs=int(reqs)
	maxslots=int(lambdas)
	maxload=int(sysload)
	initload=maxload
	rounds=int(ave)
	step=int(passo)
	init=int(inicio)
	cores = os.cpu_count()

	if int(maxcores) > (cores -1):
		proclimit = cores -1
		#proclimit = cores
	elif int(maxcores) == 0:
		proclimit = cores
		maxcores = cores
	else:
		proclimit = int(maxcores)

	print ("Number of cores: " + str(cores))
	print ("Max Processes: " + str(proclimit))
	print ("Running simulation for: ")
	print ("Algorithm = " + algorithm)
	print ("Requests = " + str(maxreqs))
	#print ("Lambdas = " + str(maxslots))
	print ("FSUs = " + str(maxslots))
	print ("Max Routes = " + str(maxroutes))
	print ("Advanced Slot Check " + str(advancedcount))
	if (variable == True):
		print ("Initial System Load = " + str(init) + " Erlangs")
		print ("Maximum System Load = " + str(maxload) + " Erlangs")
		initload=init
	else:
		print ("System Load = " + str(maxload) + " Erlangs")
	print ("Rounds = " + str(rounds))
	print ("Connectivity Matrix file = " + matrixfile)

	matrix=loadMatrix(matrixfile)
	print("Connectivity Matrix: ")
	printArray(matrix)
	print()


	dimensao = len(matrix[0])

	### Calculate and Load possible routes in route table
	allroutes=defaultdict(dict)
	for src in range (0,dimensao):
		for dst in range (0,dimensao):
			if src == dst:
				continue
			validpaths=listPaths(src,dst,matrix)
			#validpaths.sort(key=returnLength)
			validpaths.sort(key=returnCost)
			allroutes[src][dst]=validpaths


	manager = multiprocessing.Manager()
	csvQueue = manager.Queue()

	logwriter = Process(target=listener,args=(csvreport,csvQueue))
	logwriter.start()

	### Generate requests

	columns = "reqs maxCount load blocks netUsage medUsage maxUsage minUsage netFrag medFrag minFrag maxFrag timestamp avgDuration".split()

	print("Cols Stat: {0:>8}   {1:>8}   {2:>8}   {3:>8}   {4:>8}   {5:>8}   {6:>8}   {7:>8}   {8:>8}   {9:>8}   {10:>8}   {11:>8}   {12:>8}  {13:>8}".format(*columns))
	message=("{0:>8},{1:>8},{2:>8},{3:>8},{4:>8},{5:>8},{6:>8},{7:>8},{8:>8},{9:>8},{10:>8},{11:>8},{12:>8},{13:>8}".format(*columns))
	csvQueue.put(message)

	prockeys={}
	processes = {}
	for load in range (initload,maxload+1,step):
		p = Process(target=run_round,args=(load,rounds,csvQueue,start_time))
		p.name = "Process_"+str(load)
		print ("Starting Process {}".format(p.name))

		processes[load]=p
		p.start()

		while len(processes.keys()) >= proclimit:
			time.sleep(1)
			prockeys = list(processes.keys())
			#import pdb; pdb.set_trace()
			for number in prockeys:
				process = processes[number]
				if not process.is_alive():
					del processes[number]

	prockeys = list(processes.keys())
	while len(prockeys) > 0:
		for number in prockeys:
				try:
					process = processes[number]
					if not process.is_alive():
						del processes[number]
				except:
					pass
		time.sleep(1)
		prockeys = list(processes.keys())

	duration = getUptime() - start_time
	csvQueue.put("Duration: " + str(duration))
	csvQueue.put("Command Line: " + " ".join(sys.argv))
	csvQueue.put('kill')

# exit

"""
	for s in allroutes:
		for d in allroutes[s]:
			print ("Origem: " + str(s) + " Destino: " + str(d) + " :"),
			print allroutes[s][d]

"""

if __name__ == "__main__":
	#calc_routes()
	main()
