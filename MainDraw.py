#!/usr/bin/env python3
# reads a LAMMPS dump file and writes a tex file containing a tikz picture of the first snapshot in the dump

import sys
import math
import operator

#TODO scaling of picture

class NumberOfArgumentsError(Exception):
    pass

class LammpsFileCorrupt(Exception):
    pass

class UnknownArgument(Exception):
    pass

class UnknownProjectionMode(Exception):
    pass

class UnknownOrientation(Exception):
    pass

class InvalidHeight(Exception):
    pass

class InvalidWidth(Exception):
    pass

if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise NumberOfArgumentsError("\n ERROR: Wrong number of arguments.\n Usage: ./MainDraw.py lammps_file outputfile.tex arguments\n arguments are optional and can be:\n projection=[cabinet|isometric|dimetric]\n orientation=[xyz|zxy|yzx]\n png_export\n width=10\n height=10\n width and heigt have a default value of 10. the program keeps the aspect ratio, i.e. not both values are enforced but the more rigorous constraint determines the geometry of the output.")
    lammpsfile = open(sys.argv[1], 'r')
    outfile = open(sys.argv[2], 'w')

    # default values of arguments
    # used projection
    projection = "cabinet" # "cabinet", "isometric", "dimetric"
    # used orientation
    orientation = "xyz" # "xyz", "zxy", "yzx"
    # whether additionally a png shall be exported
    pngexport = False
    # geometry
    target_width = 10
    target_height = 10
    for i in range(3,len(sys.argv)):
        arg = sys.argv[i].split("=")
        if arg[0] == "projection":
            if arg[1] == "cabinet":
                projection = arg[1]
            elif arg[1] == "isometric":
                projection = arg[1]
            elif arg[1] == "dimetric":
                projection = arg[1]
            else:
                raise UnknownProjection("\n ERROR: " + arg[1] + " is not an valid projection. Only use 'cabinet', 'isometric', or 'dimetric'")
        elif arg[0] == "orientation":
            if arg[1] == "xyz":
                orientation = arg[1]
            elif arg[1] == "zxy":
                orientation = arg[1]
            elif arg[1] == "yzx":
                orientation = arg[1]
            else:
                raise UnknownOrientation("\n ERROR: " + arg[1] + " is not an valid orientation. Only use 'xyz', 'zxy', or 'yzx'")
        elif arg[0] == "png_export":
            pngexport = True
        elif arg[0] == "height":
            try:
                target_height = float(arg[1])
            except:
                raise InvalidHeight("\n ERROR: " + arg[1] + " is not an valid heigth.")
            if target_height <= 0:
                raise InvalidHeight( "\n ERROR: " + arg[1] + " is not an valid heigth.")
        elif arg[0] == "width":
            try:
                target_width = float(arg[1])
            except:
                raise InvalidWidth("\n ERROR: " + arg[1] + " is not an valid width.")
            if target_width <= 0:
                raise InvalidWidth("\n ERROR: " + arg[1] + " is not an valid width.")
        else:
            raise UnknownArgument("\n ERROR: " + arg[0] + " is not an valid argument.")

    print("Reading LAMMPS dump file ...")
    # read time step; not used anywhere
    lammpsfile.readline()
    lammpsfile.readline()
    # read number of particles to draw
    tmp = lammpsfile.readline()
    if tmp != 'ITEM: NUMBER OF ATOMS\n':
        raise LammpsFileCorrupt("\n   ERROR: Number of atoms not in fourth line of LAMMPS dump file")
    number_atoms = int(lammpsfile.readline())
    print("Reading " +  str(number_atoms) + " atoms")
    # read simulation box
    tmp = lammpsfile.readline()
    if tmp.startswith("ITEM: BOX BOUNDS") != True:
        raise LammpsFileCorrupt("\n   ERROR: Cannot handle simulation domain LAMMPS file")
    tmp = lammpsfile.readline().split()
    xmin = float(tmp[0]) 
    xmax = float(tmp[1])
    tmp = lammpsfile.readline().split()
    ymin = float(tmp[0])
    ymax = float(tmp[1])
    tmp = lammpsfile.readline().split()
    zmin = float(tmp[0])
    zmax = float(tmp[1])
    # read header of position section find where are the positions
    header = lammpsfile.readline()
    if header.startswith("ITEM: ATOMS") != True:
        raise LammpsFileCorrupt("\n   ERROR: Header of list of atoms not in expected position")
    split_header = header.split()
    x_coord_mode = -1
    y_coord_mode = -1
    z_coord_mode = -1
    try:
        x_index = split_header.index('xs') - 2 # subtract 2 to correct ITEM: ATOMS in header
        x_coord_mode = 0
    except:
        pass
    try:
        x_index = split_header.index('x') - 2
        x_coord_mode = 1
    except:
        pass
    try:
        y_index = split_header.index('ys') - 2
        y_coord_mode = 0
    except:
        pass
    try:
        y_index = split_header.index('y') - 2
        y_coord_mode = 1
    except:
        pass
    try:
        z_index = split_header.index('zs') - 2
        z_coord_mode = 0
    except:
        pass
    try:
        z_index = split_header.index('z') - 2
        z_coord_mode = 1
    except:
        pass
    if x_coord_mode == -1:
        raise LammpsFileCorrupt("\n   ERROR: Could not find x position in file")
    if y_coord_mode == -1:
        raise LammpsFileCorrupt("\n   ERROR: Could not find y position in file")
    if z_coord_mode == -1:
        raise LammpsFileCorrupt("\n   ERROR: Could not find z position in file")

    try:
        type_index = split_header.index('type') - 2
    except:
        raise LammpsFileCorrupt("\n   ERROR: Could not find type of atom in file")
    
    # read atom positions and type
    list_of_atoms = [];
    for i in range(number_atoms):
        tmp = lammpsfile.readline().split()
        list_of_atoms.append( [int(tmp[type_index]), float(tmp[x_index]), float(tmp[y_index]), float(tmp[z_index])] )
    lammpsfile.close()

    # correct coordinates if scaled coordinates are used in lammps file
    if x_coord_mode == 0:
        xdim = (xmax - xmin)
        for i in range(number_atoms):
            list_of_atoms[i][1] =  xdim * list_of_atoms[i][1] + xmin
    if y_coord_mode == 0:
        ydim = (ymax - ymin)
        for i in range(number_atoms):
            list_of_atoms[i][2] =  ydim * list_of_atoms[i][2] + ymin
    if z_coord_mode == 0:
        zdim = (zmax - zmin)
        for i in range(number_atoms):
            list_of_atoms[i][3] =  zdim * list_of_atoms[i][3] + zmin

    # scale picture
    if projection == "cabinet": 
        if orientation == "xyz":
            # x={(1cm,0cm)}, y={(0cm,1cm)}, z={(3.536mm,-3.536mm)}]\n')
            current_width = (xmax - xmin) + .3536 * (zmax - zmin)
            current_height =  (ymax - ymin) + .3536 * (zmax - zmin)
        elif orientation == "zxy":
            current_width = (zmax - zmin) + .3536 * (ymax - ymin)
            current_height =  (xmax - xmin) + .3536 * (ymax - ymin)
        elif orientation == "yzx":
            current_width = (ymax - ymin) + .3536 * (xmax - xmin)
            current_height =  (zmax - zmin) + .3536 * (xmax - xmin)
    elif projection == "isometric":
        if orientation == "xyz":
            current_width = .866 * (xmax - xmin) + .866 * (ymax - ymin)
            current_height =  .5 * (xmax - xmin) + .5 * (ymax - ymin) + (zmax - zmin)
        elif orientation == "zxy":
            current_width = .866 * (xmax - xmin) + .866 * (ymax - ymin)
            current_height =  .5 * (xmax - xmin) + .5 * (ymax - ymin) + (zmax - zmin)
        elif orientation == "yzx":
            current_width = .866 * (xmax - xmin) + .866 * (ymax - ymin)
            current_height =  .5 * (xmax - xmin) + .5 * (ymax - ymin) + (zmax - zmin)
    elif projection == "dimetric":
        if orientation == "xyz":
            current_width = .3712 * (xmax - xmin) + .9925 * (ymax - ymin)
            current_height =  .3346 * (xmax - xmin) + .1219 * (ymax - ymin) + (zmax - zmin)
        elif orientation == "zxy":
            current_width = .3712 * (zmax - zmin) + .9925 * (xmax - xmin)
            current_height =  .3346 * (zmax - zmin) + .1219 * (xmax - xmin) + (ymax - ymin)
        elif orientation == "yzx":
            current_width = .3712 * (ymax - ymin) + .9925 * (zmax - zmin)
            current_height =  .3346 * (ymax - ymin) + .1219 * (zmax - zmin) + (xmax - xmin)
    scale = min(target_width / current_width, target_height / current_height)
    xmin *= scale
    xmax *= scale
    ymin *= scale
    ymax *= scale
    zmin *= scale
    zmax *= scale
    for i in range(number_atoms):
        list_of_atoms[i][1] *= scale
        list_of_atoms[i][2] *= scale
        list_of_atoms[i][3] *= scale
    radius = .8 * scale
                
    # sort list of atoms 
    if projection == "cabinet": 
        if orientation == "xyz":
            # list_of_atoms.sort(key=operator.itemgetter(3,2,1)) # sort first x, then y, then z (maybe only z is enough)
            list_of_atoms.sort(key=operator.itemgetter(3)) # sort in z
        elif orientation == "zxy":
            list_of_atoms.sort(key=operator.itemgetter(2)) # sort in y
        elif orientation == "yzx":
            list_of_atoms.sort(key=operator.itemgetter(1)) # sort in x
    elif projection == "isometric":
        if orientation == "xyz":
            # list_of_atoms.sort(key=operator.itemgetter(3,2,1)) # sort first x, then y, then z (maybe only z is enough)
            list_of_atoms.sort(key=lambda x: -x[1]+x[2])
        elif orientation == "zxy":
            list_of_atoms.sort(key=lambda x: -x[3]+x[1])
        elif orientation == "yzx":
            list_of_atoms.sort(key=lambda x: -x[2]+x[3])
    elif projection == "dimetric":
        if orientation == "xyz":
            list_of_atoms.sort(key=lambda x: -x[1]+.182*x[2]) # maybe not completely correct
        elif orientation == "zxy":
            list_of_atoms.sort(key=lambda x: -x[3]+.182*x[1]) # maybe not completely correct
        elif orientation == "yzx":
            list_of_atoms.sort(key=lambda x: -x[2]+.182*x[3]) # maybe not completely correct

    types = next(zip(*list_of_atoms)) # extract all types from list of atoms
    num_of_types = len(set(types)) # set determines the unique elements of types and len is then number of different types
    # output atoms
    outfile.write('\documentclass[a4paper]{article}\n')
    outfile.write('\n')
    outfile.write('\\usepackage{amsmath}\n')
    outfile.write('\\usepackage{natbib}\n')
    outfile.write('\\usepackage[T1]{fontenc}\n')
    outfile.write('\\usepackage[latin1]{inputenc}\n')
    outfile.write('\\usepackage{color,graphicx}\n')
    outfile.write('\\usepackage{array}\n')
    outfile.write('\\usepackage{tabularx}\n')
    outfile.write('\\usepackage{pgfplots}\n')
    outfile.write('\pgfplotsset{compat=newest}\n')
    outfile.write('\\usepackage{tikz}\n')
    outfile.write('\\usepgfplotslibrary{external}\n')
    outfile.write('%\\tikzset{external/force remake}\n')
    outfile.write('\\usetikzlibrary{shapes,arrows,shadows,backgrounds,patterns,chains,fadings}\n')
    outfile.write('\n')
    outfile.write('\\usepackage{hyperref}\n')
    outfile.write('\n')
    # TODO: different colors
    for i in range(num_of_types):
        outfile.write('\definecolor{color%d}{RGB}{77,230,230}\n' % (i+1))
    outfile.write('\n')
    outfile.write('\\tikzset{\n')
    outfile.write('    mylargerpadding/.style={\n')
    outfile.write('        show background rectangle,\n')
    outfile.write('        inner frame sep=#1,\n')
    outfile.write('        background rectangle/.style={\n')
    outfile.write('            draw=none\n')
    outfile.write('        }\n')
    outfile.write('    },\n')
    outfile.write('    mylargerpadding/.default=15pt\n')
    outfile.write('}\n')
    outfile.write('\n')
    outfile.write('\\tikzset{\n')
    outfile.write('    png export/.style={\n')
    outfile.write('        external/system call={\n')
    outfile.write('            pdflatex \\tikzexternalcheckshellescape -halt-on-error -interaction=batchmode -jobname "\image" "\\texsource";\n')
    outfile.write('            convert -density 300 -transparent white "\image.pdf" "\image.png"\n')
    outfile.write('        }\n')
    outfile.write('    }\n')
    outfile.write('}\n')
    outfile.write('\\tikzexternalize\n')
    if pngexport == True:
        outfile.write('\\tikzset{png export}\n')
    outfile.write('\n')
    outfile.write('\everymath{\displaystyle}\n')
    outfile.write('\\begin{document}\n')
    outfile.write('\\tiny\n')
    outfile.write('\\tikzset{external/force remake}\n')
    outfile.write('\pgfplotsset{every axis plot/.append style={line width=1pt}}\n')
    outfile.write('\n')
    #outfile.write('\\begin{tikzpicture}[mylargerpadding, x={(3.85mm,-3.85mm)}, z={(1cm,0cm)}]\n')
    if orientation == "xyz":
        if projection == "cabinet":
            outfile.write('\\begin{tikzpicture}[mylargerpadding, x={(1cm,0cm)}, y={(0cm,1cm)}, z={(3.536mm,-3.536mm)}]\n')
        elif projection == "isometric":
            outfile.write('\\begin{tikzpicture}[mylargerpadding, x={(8.66mm,5mm)}, y={(8.66mm,-5mm)}, z={(0cm,1cm)}]\n')
        elif projection == "dimetric":
            outfile.write('\\begin{tikzpicture}[mylargerpadding, x={(3.712mm,3.346mm)}, y={(9.925mm,-1.219mm)}, z={(0cm,1cm)}]\n')
        outfile.write('  \draw [dashed, semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmin, xmax, ymin, zmin))
        outfile.write('  \draw [dashed, semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmax, ymin, zmin, xmax, ymin, zmax))
        outfile.write('  \draw [dashed, semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmax, ymin, zmin, xmax, ymax, zmin))
        for i in range(number_atoms):
            outfile.write('  \shade[ball color=color%d] (xyz cs:x=%f, y=%f, z=%f) circle[x={(1cm,0cm)},y={(0cm,1cm)},x radius=%f,y radius=%f];\n' % (list_of_atoms[i][0], list_of_atoms[i][1], list_of_atoms[i][2], list_of_atoms[i][3], radius, radius))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmin, xmin, ymin, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmin, xmin, ymax, zmin))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmax, xmin, ymax, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmax, xmax, ymin, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymax, zmin, xmin, ymax, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymax, zmin, xmax, ymax, zmin))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymax, zmax, xmax, ymax, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmax, ymin, zmax, xmax, ymax, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmax, ymax, zmin, xmax, ymax, zmax))
    elif orientation == "zxy":
        if projection == "cabinet":
            outfile.write('\\begin{tikzpicture}[mylargerpadding, z={(1cm,0cm)}, x={(0cm,1cm)}, y={(3.536mm,-3.536mm)}]\n')
        elif projection == "isometric":
            outfile.write('\\begin{tikzpicture}[mylargerpadding, z={(8.66mm,5mm)}, x={(8.66mm,-5mm)}, y={(0cm,1cm)}]\n')
        elif projection == "dimetric":
            outfile.write('\\begin{tikzpicture}[mylargerpadding, z={(3.712mm,3.346mm)}, x={(9.925mm,-1.219mm)}, y={(0cm,1cm)}]\n')
        outfile.write('  \draw [dashed, semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmin, xmin, ymin, zmax))
        outfile.write('  \draw [dashed, semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmax, xmin, ymax, zmax))
        outfile.write('  \draw [dashed, semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmax, xmax, ymin, zmax))
        for i in range(number_atoms):
            outfile.write('  \shade[ball color=color%d] (xyz cs:x=%f, y=%f, z=%f) circle[x={(1cm,0cm)},y={(0cm,1cm)},x radius=%f,y radius=%f];\n' % (list_of_atoms[i][0], list_of_atoms[i][1], list_of_atoms[i][2], list_of_atoms[i][3], radius, radius))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmin, xmin, ymax, zmin))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmin, xmax, ymin, zmin))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymax, zmin, xmin, ymax, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymax, zmin, xmax, ymax, zmin))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymax, zmax, xmax, ymax, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmax, ymin, zmin, xmax, ymin, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmax, ymin, zmin, xmax, ymax, zmin))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmax, ymin, zmax, xmax, ymax, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmax, ymax, zmin, xmax, ymax, zmax))
    elif orientation == "yzx":
        if projection == "cabinet":
            outfile.write('\\begin{tikzpicture}[mylargerpadding, y={(1cm,0cm)}, z={(0cm,1cm)}, x={(3.536mm,-3.536mm)}]\n')
        elif projection == "isometric":
            outfile.write('\\begin{tikzpicture}[mylargerpadding, y={(8.66mm,5mm)}, z={(8.66mm,-5mm)}, x={(0cm,1cm)}]\n')
        elif projection == "dimetric":
            outfile.write('\\begin{tikzpicture}[mylargerpadding, y={(3.712mm,3.346mm)}, z={(9.925mm,-1.219mm)}, x={(0cm,1cm)}]\n')
        outfile.write('  \draw [dashed, semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmin, xmin, ymax, zmin))
        outfile.write('  \draw [dashed, semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymax, zmin, xmin, ymax, zmax))
        outfile.write('  \draw [dashed, semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymax, zmin, xmax, ymax, zmin))
        for i in range(number_atoms):
            outfile.write('  \shade[ball color=color%d] (xyz cs:x=%f, y=%f, z=%f) circle[x={(1cm,0cm)},y={(0cm,1cm)},x radius=%f,y radius=%f];\n' % (list_of_atoms[i][0], list_of_atoms[i][1], list_of_atoms[i][2], list_of_atoms[i][3], radius, radius))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmin, xmin, ymin, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmin, xmax, ymin, zmin))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmax, xmin, ymax, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymin, zmax, xmax, ymin, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmin, ymax, zmax, xmax, ymax, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmax, ymin, zmin, xmax, ymin, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmax, ymin, zmin, xmax, ymax, zmin))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmax, ymin, zmax, xmax, ymax, zmax))
        outfile.write('  \draw [semithick, darkgray] (xyz cs:x=%s,y=%s,z=%s) -- (xyz cs:x=%s,y=%s,z=%s);\n' % (xmax, ymax, zmin, xmax, ymax, zmax))

    outfile.write('\end{tikzpicture}\n')
    outfile.write('\n')
    outfile.write('\n')
    outfile.write('\end{document}\n')
    outfile.close()
