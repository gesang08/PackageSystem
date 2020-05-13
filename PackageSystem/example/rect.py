from rectpack import newPacker

# rectangles = [[100, 30], [40, 60], [30, 30],[70, 70], [100, 50], [30, 30]]
rectangles = [[100, 30,'r1'], [40, 60,'r2'], [30, 30,'r3'],[70, 70,'r4'], [100, 50,'r5'], [30, 30,'r6']]
bins = [[300, 450, 1, 'b1'], [80, 40, 1,'b2'], [200, 150, 1, 'b3']]

packer = newPacker()

# Add the rectangles to packing queue
for r in rectangles:
	packer.add_rect(*r)

# Add the bins where the rectangles will be placed
for b in bins:
	packer.add_bin(b[0],b[1],b[2],bid=b[3])

# Start packing
packer.pack()


# Full rectangle list
all_rects = packer.rect_list()
for rect in all_rects:
    print(rect)
    b, x, y, w, h, rid = rect
    # b - Bin index
    # x - Rectangle bottom-left corner x coordinate
    # y - Rectangle bottom-left corner y coordinate
    # w - Rectangle width
    # h - Rectangle height
    # rid - User asigned rectangle id or None

for abin in packer:
  print(abin.bid) # Bin id if it has one
  for rect in abin:
    print(rect)