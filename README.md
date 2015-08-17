# DrawLAMMPSwithTikz
Python program that takes a LAMMPS output file and creates a tex document with a tikz figure of the snapshot. Optionally, one can externalize the snapshot as pdf and png.

Example Usage:
 ./MainDraw.py lammps.dump drawing.tex
 ./MainDraw.py lammps.dump drawing.tex projection=isometric orientation=zxy width=10 height=10 png_export

The colors still have to be changed manually in the resulting tex file