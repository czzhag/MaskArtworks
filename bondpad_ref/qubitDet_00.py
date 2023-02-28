#!/usr/bin/env python3

import gdspy
import math

#########################
# set up file and layers
#########################

# The GDSII file is called a library, which contains multiple cells.
lib = gdspy.GdsLibrary()

# Geometry must be placed in cells.
chipCell = lib.new_cell('chip')

# Layers
helper = {"layer": 0, "datatype": 0}
metal1 = {"layer": 1, "datatype": 0}
metal2 = {"layer": 2, "datatype": 0}
metal3 = {"layer": 3, "datatype": 0}
metal4 = {"layer": 4, "datatype": 0}

#########################
# define params
# all sizes in um
#########################

# chip
chip_x = 10000
chip_y = 10000
offset = 10 # min distance from any object to edge of chip
bend_r = 70 # fillet radius
bend_r_small = 2 # fillet radius for small features

# rf launch positions
l1 = (3000,offset)
l2 = (3000,chip_y-offset)
l3 = (chip_x-3000,offset)
l4 = (chip_x-3000,chip_y-offset)

# launch sizes
pad_gnd_thickness = 200
pad_gap_thickness = 90
taper_l = 400

pad_w_in = 200
pad_l_in = 200

pad_w_gap = pad_w_in + 2*pad_gap_thickness
pad_l_gap = pad_l_in + pad_gap_thickness

pad_w_gnd = pad_w_gap + 2*pad_gnd_thickness
pad_l_gnd = pad_l_gap + pad_gnd_thickness

# CPW
cpw_s = 20 # width of central conductor
cpw_w = 9 # width of gaps
cpw_gnd = 100 # width of ground lines
line_l = l2[1] - l1[1] - 2*pad_gnd_thickness - 2*pad_gap_thickness - 2*pad_l_in - 2*taper_l # feedline length between launchpads

# CPW second ground line
gnd2_y_offset = 0.5*cpw_gnd # space from launch pad to gnd line split

# qubits
couplingGap = 30 # gap between qubit pad and feedline
qpad_x = 100 # qubit pad width
qpad_y = 600 # qubit pad height
qpad_gap = 70 # gap between two qubit pads
qpad_gap_shift = 10 # change in qpad gap to shift qubit frequency

jpad_overlap = 15 # overlap between junction pad and qubit big pad
jpad_x = 20 # junction pad width
jpad_y = 20 # junction pad height

jline_x1 = 26
jline_x2 = 30
jline_y = 2
jline_offset = 2*jline_y

jxn_w = 0.12 # junction width
jxn_l = 5 # junction narrow line length

undercut_x = 0.6
undercut_y = undercut_x 

# qubit positions
n_qubits = 3
qspacing = line_l / (n_qubits+1)
start_y = l1[1] + pad_gnd_thickness + pad_gap_thickness + pad_l_in + taper_l + qspacing # first qubit center y coord
line_xoffset = cpw_s/2 + cpw_w + cpw_gnd + couplingGap # offset of qubit pad from line center

# charge line launch positions
cl1 = (offset, start_y)
cl2 = (offset, start_y + qspacing)
cl3 = (offset, start_y + 2*qspacing)
cl4 = (chip_y - offset, start_y)
cl5 = (chip_y - offset, start_y + qspacing)
cl6 = (chip_y - offset, start_y + 2*qspacing)

# dc charge lines
cline_coupling = 100 # coupling gap from charge line to ground next to qubit pad
cline_end = l1[0] - line_xoffset - 2*qpad_x - qpad_gap - couplingGap - cpw_gnd - cline_coupling # x position of end of charge line (1)
cline_endtaper_l = 30 # length of charge line coupling taper
cline_endtaper_w = 2.5 # final width of charge line inner conductor coupling taper

#########################
# create geometry
#########################

# Chip outline for reference only
chipRect = gdspy.Rectangle((0, 0), (chip_x, chip_y),**helper)
chipCell.add(chipRect)

### RF feedlines ########

## standard CPW
lineCell = lib.new_cell('line')

# inner conductor
pad_in = gdspy.Path(pad_w_in, (l1[0], l1[1]+pad_gnd_thickness+pad_gap_thickness))
pad_in.segment(pad_l_in, "+y")
pad_in.segment(taper_l, "+y", final_width=cpw_s)
pad_in.segment(line_l, "+y")
pad_in.segment(taper_l, "+y", final_width=pad_w_in)
pad_in.segment(pad_l_in, "+y")

pad_in_join = gdspy.boolean(pad_in, None, 'or', **metal1)#, max_points=0)
pad_in_join.fillet(bend_r)
lineCell.add(pad_in_join)

# gap
pad_gap = gdspy.Path(pad_w_gap, (l1[0], l1[1]+pad_gnd_thickness))
pad_gap.segment(pad_l_gap, "+y")
pad_gap.segment(taper_l, "+y", final_width = cpw_s + 2*cpw_w)
pad_gap.segment(line_l, "+y")
pad_gap.segment(taper_l, "+y", final_width=pad_w_gap)
pad_gap.segment(pad_l_gap, "+y")

pad_gap_join = gdspy.boolean(pad_gap, None, 'or', **metal1)#, max_points=0)
pad_gap_join.fillet(bend_r)

# outer conductor ground
pad_gnd = gdspy.Path(pad_w_gnd, (l1[0], l1[1]))
pad_gnd.segment(pad_l_gnd, "+y")
pad_gnd.segment(taper_l, "+y", final_width = cpw_s + 2*cpw_w + 2*cpw_gnd)
pad_gnd.segment(line_l, "+y")
pad_gnd.segment(taper_l, "+y", final_width=pad_w_gnd)
pad_gnd.segment(pad_l_gnd, "+y")

pad_gnd_join0 = gdspy.boolean(pad_gnd, None, 'or', **metal1)#, max_points=0)
pad_gnd_join0.fillet(bend_r)

pad_gnd_join = gdspy.boolean(pad_gnd_join0, pad_gap_join, 'not', **metal1)#, max_points=0)
lineCell.add(pad_gnd_join)

# copy for second feedline
lineCell2 = lineCell.copy('line2',translation=(l3[0]-l1[0],l3[1]-l1[1]))
chipCell.add(lineCell)
chipCell.add(lineCell2)

## outside qubit ground line
outlineCell = lib.new_cell('outline')

outline_xoffset = cpw_s/2 + cpw_w + cpw_gnd + couplingGap # offset of outer gnd line start from line center

gnd2 = gdspy.Path(cpw_gnd, (l1[0]-cpw_s/2-cpw_w-cpw_gnd, l1[1]+pad_l_gnd+taper_l+gnd2_y_offset+cpw_gnd/2.))
gnd2.segment(2*qpad_x + qpad_gap + 2*couplingGap - cpw_gnd/2, "-x")
gnd2.turn(cpw_gnd, 'r')
gnd2.segment(line_l - 2*gnd2_y_offset - 2*cpw_gnd - cpw_gnd, "+y")
gnd2.turn(cpw_gnd, 'r')
gnd2.segment(2*qpad_x + qpad_gap + 2*couplingGap - cpw_gnd/2, "+x")
gnd2_join = gdspy.boolean(gnd2, None, 'or', **metal1)

outlineCell.add(gnd2_join)
outlineCell2 = outlineCell.copy('outline2', rotation=math.pi, x_reflection=True, translation=((2*outline_xoffset + l3[0] - l1[0]) + 2*(l1[0] - outline_xoffset), 0))

chipCell.add(outlineCell)
chipCell.add(outlineCell2)

### Qubits ########

## single qubit loop

qubitRowCell = lib.new_cell('qubitRow')

for q in range(n_qubits):

    # pads
    qpad1 = gdspy.Rectangle(
            (l1[0]-line_xoffset, start_y-qpad_y/2),
            (l1[0]-line_xoffset-qpad_x, start_y+qpad_y/2),
            **metal2)
    qpad1.fillet(bend_r)
    qubitRowCell.add(qpad1)
    
    qpad2 = gdspy.Rectangle(
            (l1[0]-line_xoffset-qpad_x-qpad_gap, start_y-qpad_y/2),
            (l1[0]-line_xoffset-2*qpad_x-qpad_gap, start_y+qpad_y/2),
            **metal2)
    qpad2.fillet(bend_r)
    qubitRowCell.add(qpad2)
    
    # junction
    # TO DO: add funny junction pad squiggles
    
    jpad1 = gdspy.Rectangle(
            (l1[0]-line_xoffset-qpad_x+jpad_overlap, start_y-jpad_y/2),
            (l1[0]-line_xoffset-qpad_x+jpad_overlap-jpad_x, start_y+jpad_y/2),
            **metal3)
    jpad1.fillet(bend_r_small)
    qubitRowCell.add(jpad1)
    
    jpad2 = gdspy.copy(jpad1, dx = -jpad_overlap - qpad_gap + jpad_x - jpad_overlap)
    qubitRowCell.add(jpad2)
    
    jline1 = gdspy.Rectangle(
            (l1[0]-line_xoffset-qpad_x-jpad_x+jpad_overlap, start_y-jline_y/2),
            (l1[0]-line_xoffset-qpad_x-jpad_x+jpad_overlap-jline_x1, start_y+jline_y/2),
            **metal3)
    qubitRowCell.add(jline1)
    
    jline2 = gdspy.Rectangle(
            (l1[0]-line_xoffset-qpad_x-qpad_gap+jpad_x-jpad_overlap, start_y-jline_y/2-jline_offset-jline_y),
            (l1[0]-line_xoffset-qpad_x-qpad_gap+jpad_x-jpad_overlap+jline_x2, start_y-jline_y/2-jline_offset),
            **metal3)
    qubitRowCell.add(jline2)
    
    jxn1 = gdspy.Rectangle(
            (l1[0]-line_xoffset-qpad_x-jpad_x+jpad_overlap-jline_x1, start_y-jline_y/2),
            (l1[0]-line_xoffset-qpad_x-jpad_x+jpad_overlap-jline_x1-jxn_l, start_y-jline_y/2+jxn_w),
            **metal3)
    qubitRowCell.add(jxn1)
    
    jxn2 = gdspy.Rectangle(
            (l1[0]-line_xoffset-qpad_x-qpad_gap+jpad_x-jpad_overlap+jline_x2, start_y-jline_y/2-jline_offset),
            (l1[0]-line_xoffset-qpad_x-qpad_gap+jpad_x-jpad_overlap+jline_x2-jxn_w, start_y-jline_y/2-jline_offset+jxn_l),
            **metal3)
    qubitRowCell.add(jxn2)
    
    # junction undercut
    
    upad1 = gdspy.Rectangle(
            (l1[0]-line_xoffset-qpad_x+jpad_overlap, start_y-jpad_y/2),
            (l1[0]-line_xoffset-qpad_x+jpad_overlap-jpad_x-undercut_x, start_y+jpad_y/2+undercut_y),
            **metal4)
    upad1.fillet(bend_r_small)
    upad2 = gdspy.copy(upad1, dx = -jpad_overlap - qpad_gap + jpad_x - jpad_overlap)
    upads = gdspy.boolean([upad1,upad2], [jpad1,jpad2,jline1,jline2], 'not', **metal4)
    qubitRowCell.add(upads)
    
    # TO DO: check if line undercut actually is not supposed to have corner
    uline1 = gdspy.Rectangle(
            (l1[0]-line_xoffset-qpad_x-jpad_x+jpad_overlap, start_y-jline_y/2),
            (l1[0]-line_xoffset-qpad_x-jpad_x+jpad_overlap-jline_x1-undercut_x, start_y+jline_y/2+undercut_x),
            **metal4)
    uline2 = gdspy.copy(jline2, dy = undercut_y)
    ulines = gdspy.boolean([uline1,uline2], [jline1,jline2,jxn1,jxn2], 'not', **metal4)
    qubitRowCell.add(ulines)
    
    ujxn1 = gdspy.Rectangle(
            (l1[0]-line_xoffset-qpad_x-jpad_x+jpad_overlap-jline_x1-jxn_l, start_y-jline_y/2-jxn_w),
            (l1[0]-line_xoffset-qpad_x-jpad_x+jpad_overlap-jline_x1-jxn_l-undercut_x, start_y-jline_y/2+jxn_w*2),
            **metal4)
    qubitRowCell.add(ujxn1)
    ujxn2 = gdspy.Rectangle(
            (l1[0]-line_xoffset-qpad_x-qpad_gap+jpad_x-jpad_overlap+jline_x2+jxn_w, start_y-jline_y/2-jline_offset+jxn_l),
            (l1[0]-line_xoffset-qpad_x-qpad_gap+jpad_x-jpad_overlap+jline_x2-2*jxn_w, start_y-jline_y/2-jline_offset+jxn_l+undercut_y),
            **metal4)
    qubitRowCell.add(ujxn2)
    
    # adjust params for next qubit
    qpad_gap -= qpad_gap_shift
    qpad_x += qpad_gap_shift/2
    start_y += qspacing

chipCell.add(qubitRowCell)

### DC feedlines ########

### standard CPW
clineCell = lib.new_cell('cline')
cline_l = cline_end - offset - pad_l_gnd - taper_l - cline_endtaper_l

# inner conductor
dc_in = gdspy.Path(pad_w_in, (cl1[0]+pad_gnd_thickness+pad_gap_thickness, cl1[1]))
dc_in.segment(pad_l_in, "+x")
dc_in.segment(taper_l, "+x", final_width=cpw_s)
dc_in.segment(cline_l, "+x")
dc_in.segment(cline_endtaper_l, "+x", final_width=cline_endtaper_w)

dc_in_join = gdspy.boolean(dc_in, None, 'or', **metal1)#, max_points=0)
dc_in_join.fillet(bend_r)
clineCell.add(dc_in_join)

# gap
dc_gap = gdspy.Path(pad_w_gap, (cl1[0]+pad_gnd_thickness, cl1[1]))
dc_gap.segment(pad_l_gap, "+x")
dc_gap.segment(taper_l, "+x", final_width = cpw_s + 2*cpw_w)
dc_gap.segment(cline_l + cline_endtaper_l + cline_coupling, "+x")

dc_gap_join = gdspy.boolean(dc_gap, None, 'or', **metal1)#, max_points=0)
dc_gap_join.fillet([bend_r, bend_r, bend_r, bend_r, 0, 0, bend_r, bend_r])

# outer conductor ground
dc_gnd = gdspy.Path(pad_w_gnd, (cl1[0], cl1[1]))
dc_gnd.segment(pad_l_gnd, "+x")
dc_gnd.segment(taper_l, "+x", final_width = cpw_s + 2*cpw_w + 2*cpw_gnd)
dc_gnd.segment(cline_l + cline_endtaper_l + cline_coupling, "+x")

dc_gnd_join0 = gdspy.boolean(dc_gnd, None, 'or', **metal1)#, max_points=0)
dc_gnd_join0.fillet([bend_r, bend_r, bend_r, bend_r, 0, 0, bend_r, bend_r])

dc_gnd_join = gdspy.boolean(dc_gnd_join0, dc_gap_join, 'not', **metal1)#, max_points=0)
clineCell.add(dc_gnd_join)


### tile dc lines along feedline

clineRowCell = lib.new_cell('clineRow')
clineRowCell.add(gdspy.CellArray(clineCell, 1, 3, (0, qspacing)).get_polygonsets())

chipCell.add(clineRowCell)

### Copy row of qubits/charge lines to other feedline(s) ###########

qubitRowCell2 = lib.new_cell('qubitRow2')
clineRowCell2 = lib.new_cell('clineRow2')

qubitRowCell2 = qubitRowCell.copy('qubitPads2', rotation=math.pi, x_reflection=True, translation=((2*line_xoffset + l3[0] - l1[0]) + 2*(l1[0] - line_xoffset), 0))
clineRowCell2 = clineRowCell.copy('cline2', rotation=math.pi, x_reflection=True, translation=((2*line_xoffset + l3[0] - l1[0]) + 2*(l1[0] - line_xoffset), 0))

chipCell.add(qubitRowCell2)
chipCell.add(clineRowCell2)

#########################
# save file
#########################

# Save the library in a file
lib.write_gds('GDS/qubitDetChip.gds')

