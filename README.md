# WDMSIM.py - Routing and Spectrum Assignment simulation for WDM networks

Author: Antonio Forster <aforster@gmail.com>
License: GPL v2 


# Introduction

This project has been developed as part of my Master in Science Degree in Network Management at the Electrical Engineering School at the [Pontifical Catholic University in Campinas, Brazil](https://www.puc-campinas.edu.br)

It is distributed AS-IS, without any support, as contribution to the academic community.  

As defined in GPLv2, you can use this software at any time, as long as you keep its source and authoring information, and as Long as any future work devised should inherit GPLv2 license as well. For further information about GNU Public License v2, please refer to [GPL v2 Documentation](https://opensource.org/licenses/gpl-2.0.php) or the attached file named "GPLv2.txt".

Some basic information about the software, its development and its usage is available below. If further information is needed, please refer to my dissertation on PUC Virtual Library. You can find the full dissertation PDF file at [Thesis and Dissertations - Electrical Engineering](
https://www.puc-campinas.edu.br/pos-graduacao/programa-de-pos-graduacao-em-engenharia-eletrica-mestrado/#teses)


# Dependencies

Python 3 and basic libraries



# SMP Support

Since Python does not implement threads with multiprocessing support, this software has been created using OS forks; it is not the best solution for performance as it has its known overhead, but it was the best solution considering we didn't want to use any custom Python libraries and there was the need to maximize resource utilisation in a multi-core hardware system. 



# Usage and Options

'''aforster@wdmsim: $ ./WDMsim.py --help
WDMsim.py version 1.0
Author: Antonio Forster <aforster@gmail.com>
Usage:
-h		Print this help information
-n	<FILE>	Connectivity Matrix of the network to be simulated. Default is matrix.txt.
-v		Verbose output during execution
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

aforster@wdmsim: $
'''


# Available RSA Algorithms

FirstFit: Standard FirstFit RSA algorithm
AltFirstFit: FistFit using alternate Slot sequencing
BestFrag: Experimental Fragmentation-aware algorithm that uses External Fragmentation Metrics as key criteron for allocation definition.
AltBestFrag: Experimental Fragmentation-aware algorithm that uses External Fragmentation Metrics as key criteron for allocation definition and alternate slot sequencing. 


# ASC - in-Advance Slot Checking

Auxiliary Algorithm used to expedite the spetrum allocation procedure in fragmentation-aware algorithms by creating in advance a list of eligible slots that could provide optimum solutions by skipping test of slots that do not have adjacency with other allocated slots or spectrum border. 
This algorithm was detailed explained in a article submitted to [Elsevier's Optical Fiber Technology Journal](https://www.journals.elsevier.com/optical-fiber-technology/) It is still under review and evaluation at this time, so please search for the author's name on that Journal for more information. 

# Network Topology

A file containing the connectivity matrix of NSFNet has been included in this package with the cost for each link. 
If the user wants to use a different network architecture, it can be documented following the same format. 


# Example

./WDMsim.py -r 10000 -s 240 -k 3 -i 50 -l 300 -a BestFrag -v -p 10 -c 7 -m 10 --asc -n nsfnet.txt -e -o newasc-bestfrag.csv > newasc-bestfrag.stats

# Doubts

If you have any doubts, please send an email to aforster@gmail.com and I'll try to respond. 
Thank you for your interest in this project. 


